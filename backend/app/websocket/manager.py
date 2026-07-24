import uuid
from typing import Dict, List

from fastapi import WebSocket


class ChatConnectionManager:
    def __init__(self) -> None:
        self.active_connections: Dict[uuid.UUID, List[WebSocket]] = {}

    async def connect(self, chat_id: uuid.UUID, websocket: WebSocket) -> None:
        await websocket.accept()
        self.active_connections.setdefault(chat_id, []).append(websocket)

    def disconnect(self, chat_id: uuid.UUID, websocket: WebSocket) -> None:
        connections = self.active_connections.get(chat_id)
        if not connections:
            return
        if websocket in connections:
            connections.remove(websocket)
        if not connections:
            self.active_connections.pop(chat_id, None)

    async def broadcast(self, chat_id: uuid.UUID, message: dict) -> None:
        """Send to every live socket in the room, dropping the ones that fail.
        """
        dead: List[WebSocket] = []
        for connection in list(self.active_connections.get(chat_id, [])):
            try:
                await connection.send_json(message)
            except Exception:  # noqa: BLE001 - one bad socket must not break the room
                dead.append(connection)

        for connection in dead:
            self.disconnect(chat_id, connection)


manager = ChatConnectionManager()
