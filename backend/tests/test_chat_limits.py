"""Size and rate limits on the chat socket.

``ChatMessage.content`` is ``Text`` and the slowapi limits only decorate HTTP
routes, so before these guards a single socket could store a message of any
size, as fast as it could send frames.

Reuses the WebSocket fixtures from ``test_chat_websocket`` (``ws_session``
redirects the handler's own ``SessionLocal()`` at the test transaction).
"""
import time

import pytest

from app.routers import chat as chat_router
from app.websocket.limits import MAX_MESSAGE_CHARS, SlidingWindowLimiter

from tests.test_chat_websocket import _connect, chat_room, ws_session  # noqa: F401


@pytest.fixture(autouse=True)
def _clean_limiter():
    """The limiter is a module singleton; don't let tests leak into each other."""
    chat_router.message_limiter.reset()
    yield
    chat_router.message_limiter.reset()


def _messages(client, chat_room, participant="owner"):
    return client.get(
        f"/chats/{chat_room['chat_id']}/messages",
        headers=chat_room[participant]["headers"],
    ).json()


# --- the limiter itself ------------------------------------------------------


def test_limiter_allows_up_to_the_cap():
    limiter = SlidingWindowLimiter(max_events=3, window_seconds=60)
    assert [limiter.allow("user") for _ in range(3)] == [True, True, True]


def test_limiter_blocks_past_the_cap():
    limiter = SlidingWindowLimiter(max_events=3, window_seconds=60)
    for _ in range(3):
        limiter.allow("user")
    assert limiter.allow("user") is False


def test_limiter_buckets_are_per_key():
    limiter = SlidingWindowLimiter(max_events=1, window_seconds=60)
    assert limiter.allow("a") is True
    assert limiter.allow("a") is False
    assert limiter.allow("b") is True


def test_limiter_recovers_after_the_window_passes():
    limiter = SlidingWindowLimiter(max_events=2, window_seconds=0.05)
    assert limiter.allow("user") is True
    assert limiter.allow("user") is True
    assert limiter.allow("user") is False

    time.sleep(0.06)
    assert limiter.allow("user") is True


def test_limiter_sweeps_keys_that_have_gone_quiet():
    """A stream of one-off senders must not leak buckets forever."""
    limiter = SlidingWindowLimiter(max_events=5, window_seconds=0.01, sweep_every=4)
    for i in range(100):
        limiter.allow(f"user-{i}")

    time.sleep(0.02)  # every bucket is now older than the window

    # The sweep is amortised, so it takes a few calls to come around.
    for _ in range(limiter.sweep_every):
        limiter.allow("chatty")

    assert set(limiter._events) == {"chatty"}


def test_sweeping_does_not_forgive_an_active_flooder():
    """The sweep must not hand a still-sending client a fresh budget."""
    limiter = SlidingWindowLimiter(max_events=2, window_seconds=60, sweep_every=2)
    assert limiter.allow("flooder") is True
    assert limiter.allow("flooder") is True
    for _ in range(10):
        assert limiter.allow("flooder") is False


# --- wired into the socket ---------------------------------------------------


def test_oversized_message_is_dropped(client, chat_room, ws_session):  # noqa: F811
    with _connect(client, chat_room, "owner") as owner_ws:
        owner_ws.send_json({"content": "x" * (MAX_MESSAGE_CHARS + 1)})

        # Same connection, processed in order: if the huge one had been stored,
        # it would arrive here first.
        owner_ws.send_json({"content": "normal"})
        assert owner_ws.receive_json()["content"] == "normal"

    stored = _messages(client, chat_room)
    assert [m["content"] for m in stored] == ["normal"]


def test_message_at_exactly_the_cap_is_accepted(client, chat_room, ws_session):  # noqa: F811
    content = "x" * MAX_MESSAGE_CHARS
    with _connect(client, chat_room, "owner") as owner_ws:
        owner_ws.send_json({"content": content})
        assert owner_ws.receive_json()["content"] == content

    assert len(_messages(client, chat_room)) == 1


def test_oversize_is_measured_after_stripping(client, chat_room, ws_session):  # noqa: F811
    """Padding with whitespace must not push a legal message over the cap."""
    content = "x" * MAX_MESSAGE_CHARS
    with _connect(client, chat_room, "owner") as owner_ws:
        owner_ws.send_json({"content": f"   {content}   "})
        assert owner_ws.receive_json()["content"] == content


def test_flood_is_throttled(client, chat_room, ws_session, monkeypatch):  # noqa: F811
    """A socket cannot keep writing rows once it is over its budget."""
    cap = 3
    monkeypatch.setattr(
        chat_router, "message_limiter", SlidingWindowLimiter(max_events=cap, window_seconds=60)
    )

    with _connect(client, chat_room, "owner") as owner_ws:
        for i in range(cap + 5):
            owner_ws.send_json({"content": f"msg{i}"})

        for i in range(cap):
            assert owner_ws.receive_json()["content"] == f"msg{i}"

        time.sleep(0.5)

    assert len(_messages(client, chat_room)) == cap


def test_throttled_sender_does_not_block_the_other_participant(
    client, chat_room, ws_session, monkeypatch  # noqa: F811
):
    """Buckets are per user, so one flooder cannot mute the room."""
    monkeypatch.setattr(
        chat_router, "message_limiter", SlidingWindowLimiter(max_events=1, window_seconds=60)
    )

    with _connect(client, chat_room, "owner") as owner_ws, \
            _connect(client, chat_room, "requester") as requester_ws:
        owner_ws.send_json({"content": "owner uses their budget"})
        assert owner_ws.receive_json()["content"] == "owner uses their budget"
        assert requester_ws.receive_json()["content"] == "owner uses their budget"

        owner_ws.send_json({"content": "over budget, dropped"})

        requester_ws.send_json({"content": "requester still works"})
        assert requester_ws.receive_json()["content"] == "requester still works"
        assert owner_ws.receive_json()["content"] == "requester still works"
