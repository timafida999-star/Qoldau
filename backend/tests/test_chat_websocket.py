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

import pytest

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
