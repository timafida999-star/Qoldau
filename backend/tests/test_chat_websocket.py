"""Regression tests for the chat WebSocket room.

A single malformed frame used to kill a room permanently: ``receive_json()``
raised, the only handler was ``except WebSocketDisconnect``, so
``manager.disconnect()`` never ran and the dead socket stayed in
``active_connections`` forever. ``broadcast()`` then raised on that socket and
aborted before reaching the live clients, so nobody in the room could send or
receive again until the process restarted.
"""
import asyncio
import uuid
from datetime import datetime, timedelta, timezone

import pytest
from jose import jwt
from starlette.websockets import WebSocketDisconnect

from app.config import settings
from app.routers import chat as chat_router
from app.websocket.manager import ChatConnectionManager


# --- broadcast: one dead socket must not starve the rest of the room ---------


class _FakeSocket:
    """Minimal stand-in for a Starlette WebSocket."""

    def __init__(self, fail: bool = False):
        self.fail = fail
        self.sent: list[dict] = []

    async def send_json(self, message: dict) -> None:
        if self.fail:
            raise RuntimeError("socket is dead")
        self.sent.append(message)


def test_broadcast_reaches_live_sockets_past_a_dead_one():
    manager = ChatConnectionManager()
    chat_id = uuid.uuid4()
    dead, live = _FakeSocket(fail=True), _FakeSocket()
    # Dead one first: the old implementation aborted here and never reached live.
    manager.active_connections[chat_id] = [dead, live]

    asyncio.run(manager.broadcast(chat_id, {"content": "hello"}))

    assert live.sent == [{"content": "hello"}]


def test_broadcast_prunes_failed_sockets():
    manager = ChatConnectionManager()
    chat_id = uuid.uuid4()
    dead, live = _FakeSocket(fail=True), _FakeSocket()
    manager.active_connections[chat_id] = [dead, live]

    asyncio.run(manager.broadcast(chat_id, {"content": "hello"}))

    assert manager.active_connections[chat_id] == [live]


def test_broadcast_drops_the_room_when_every_socket_is_dead():
    manager = ChatConnectionManager()
    chat_id = uuid.uuid4()
    manager.active_connections[chat_id] = [_FakeSocket(fail=True), _FakeSocket(fail=True)]

    asyncio.run(manager.broadcast(chat_id, {"content": "hello"}))

    assert chat_id not in manager.active_connections


# --- end-to-end: a malformed frame must not break the room ------------------


@pytest.fixture
def ws_session(db, monkeypatch):
    """Point the WS handler's ``SessionLocal()`` at the test's session.

    The handler opens its own session rather than going through ``get_db``, so
    without this it would run on a separate connection and never see the
    fixtures' uncommitted rows. ``close()`` is neutered because the handler
    closes its session on exit and the fixture still needs it afterwards.
    """
    class _NoCloseSession:
        def __getattr__(self, name):
            return getattr(db, name)

        def close(self):
            pass

    monkeypatch.setattr(chat_router, "SessionLocal", _NoCloseSession)
    return db


@pytest.fixture
def chat_room(client, make_user, make_listing):
    """An accepted reservation, which is what creates a chat. Returns both
    participants and the chat id."""
    owner, requester = make_user(), make_user()
    listing = make_listing(owner)

    reservation = client.post(
        f"/listings/{listing['id']}/reservations", headers=requester["headers"]
    ).json()
    accepted = client.patch(
        f"/reservations/{reservation['id']}",
        headers=owner["headers"],
        json={"action": "accept"},
    ).json()

    return {"owner": owner, "requester": requester, "chat_id": accepted["chat_id"]}


def _connect(client, chat_room, participant):
    return client.websocket_connect(
        f"/ws/chats/{chat_room['chat_id']}?token={chat_room[participant]['token']}"
    )


def test_malformed_frame_does_not_kill_the_room(client, chat_room, ws_session):
    with _connect(client, chat_room, "owner") as owner_ws, \
            _connect(client, chat_room, "requester") as requester_ws:
        # A) baseline: the room is healthy
        owner_ws.send_json({"content": "msg1"})
        assert owner_ws.receive_json()["content"] == "msg1"
        assert requester_ws.receive_json()["content"] == "msg1"

        # B) one client sends a frame that is not JSON
        requester_ws.send_text("}{ not json")

        # C) the same room still works, for both participants
        owner_ws.send_json({"content": "msg2"})
        assert owner_ws.receive_json()["content"] == "msg2"
        assert requester_ws.receive_json()["content"] == "msg2"

        # ...and the client that sent the bad frame is still usable itself
        requester_ws.send_json({"content": "msg3"})
        assert owner_ws.receive_json()["content"] == "msg3"
        assert requester_ws.receive_json()["content"] == "msg3"


@pytest.mark.parametrize("payload", ['"just a string"', "42", "[1, 2, 3]", "null"])
def test_valid_json_of_the_wrong_shape_does_not_kill_the_room(
    client, chat_room, ws_session, payload
):
    """``data.get(...)`` would raise AttributeError on anything but an object."""
    with _connect(client, chat_room, "owner") as owner_ws:
        owner_ws.send_text(payload)

        owner_ws.send_json({"content": "still alive"})
        assert owner_ws.receive_json()["content"] == "still alive"


def test_disconnect_removes_the_socket_from_the_room(client, chat_room, ws_session):
    chat_id = uuid.UUID(chat_room["chat_id"])

    with _connect(client, chat_room, "owner"):
        assert len(chat_router.manager.active_connections.get(chat_id, [])) == 1

    assert chat_id not in chat_router.manager.active_connections


# --- rejected handshakes: the close code must reach the client --------------
#
# Closing before ``accept()`` makes uvicorn answer the handshake with a bare
# HTTP 403, so a browser only ever sees close code 1006 and cannot tell an
# expired session from a network failure. Each rejection must therefore be an
# accepted socket that is then closed with an application code.


def _assert_closed_after_accept(client, url: str, expected_code: int) -> None:
    with client.websocket_connect(url) as ws:
        with pytest.raises(WebSocketDisconnect) as closed:
            ws.receive_json()
    assert closed.value.code == expected_code


def _token(sub: str, expires_in: timedelta) -> str:
    payload = {"sub": sub, "exp": datetime.now(timezone.utc) + expires_in}
    return jwt.encode(payload, settings.jwt_secret_key, algorithm=settings.jwt_algorithm)


def test_garbage_token_is_closed_with_4401(client, chat_room, ws_session):
    _assert_closed_after_accept(
        client, f"/ws/chats/{chat_room['chat_id']}?token=not-a-jwt", chat_router.WS_CLOSE_UNAUTHORIZED
    )


def test_expired_token_is_closed_with_4401(client, chat_room, ws_session):
    expired = _token(chat_room["owner"]["id"], timedelta(minutes=-1))
    _assert_closed_after_accept(
        client, f"/ws/chats/{chat_room['chat_id']}?token={expired}", chat_router.WS_CLOSE_UNAUTHORIZED
    )


def test_token_of_unknown_user_is_closed_with_4401(client, chat_room, ws_session):
    ghost = _token(str(uuid.uuid4()), timedelta(minutes=5))
    _assert_closed_after_accept(
        client, f"/ws/chats/{chat_room['chat_id']}?token={ghost}", chat_router.WS_CLOSE_UNAUTHORIZED
    )


def test_non_participant_is_closed_with_4403(client, chat_room, make_user, ws_session):
    stranger = make_user()
    _assert_closed_after_accept(
        client, f"/ws/chats/{chat_room['chat_id']}?token={stranger['token']}", chat_router.WS_CLOSE_FORBIDDEN
    )


def test_missing_chat_is_closed_with_4404(client, chat_room, ws_session):
    _assert_closed_after_accept(
        client,
        f"/ws/chats/{uuid.uuid4()}?token={chat_room['owner']['token']}",
        chat_router.WS_CLOSE_NOT_FOUND,
    )


def test_rejected_socket_never_joins_the_room(client, chat_room, make_user, ws_session):
    chat_id = uuid.UUID(chat_room["chat_id"])
    stranger = make_user()

    _assert_closed_after_accept(
        client, f"/ws/chats/{chat_id}?token={stranger['token']}", chat_router.WS_CLOSE_FORBIDDEN
    )

    assert chat_id not in chat_router.manager.active_connections
