import uuid
from typing import List

from fastapi import APIRouter, Depends, HTTPException, Query, WebSocket, WebSocketDisconnect, status
from sqlalchemy.orm import Session

from app.auth.dependencies import get_current_user
from app.auth.security import decode_access_token
from app.database.session import SessionLocal, get_db
from app.models.chat import Chat, ChatMessage
from app.models.user import User
from app.schemas.chat import ChatMessageOut, ChatOut
from app.schemas.user import UserPublic
from app.utils.notifications import notify_new_message
from app.websocket.limits import MAX_MESSAGE_CHARS, message_limiter
from app.websocket.manager import manager

router = APIRouter(prefix="/chats", tags=["chat"])

WS_CLOSE_UNAUTHORIZED = 4401
WS_CLOSE_FORBIDDEN = 4403
WS_CLOSE_NOT_FOUND = 4404


def get_chat_or_404(chat_id: uuid.UUID, db: Session) -> Chat:
    chat = db.query(Chat).filter(Chat.id == chat_id).first()
    if not chat:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Chat not found")
    return chat


def get_participant_ids(chat: Chat) -> tuple[uuid.UUID, uuid.UUID]:
    return chat.reservation.listing.owner_id, chat.reservation.requester_id


def ensure_participant(chat: Chat, user_id: uuid.UUID) -> None:
    owner_id, requester_id = get_participant_ids(chat)
    if user_id not in (owner_id, requester_id):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not a participant of this chat")


def get_other_participant(chat: Chat, viewer_id: uuid.UUID) -> User:
    owner = chat.reservation.listing.owner
    requester = chat.reservation.requester
    return requester if viewer_id == owner.id else owner


@router.get("/{chat_id}", response_model=ChatOut)
def get_chat(chat_id: uuid.UUID, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    chat = get_chat_or_404(chat_id, db)
    ensure_participant(chat, current_user.id)

    return ChatOut(
        id=chat.id,
        reservation_id=chat.reservation_id,
        listing_title=chat.reservation.listing.title,
        other_participant=UserPublic.model_validate(get_other_participant(chat, current_user.id)),
        created_at=chat.created_at,
    )


@router.get("/{chat_id}/messages", response_model=List[ChatMessageOut])
def get_messages(chat_id: uuid.UUID, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    chat = get_chat_or_404(chat_id, db)
    ensure_participant(chat, current_user.id)
    return chat.messages


ws_router = APIRouter(tags=["chat"])


async def reject_websocket(websocket: WebSocket, code: int) -> None:
    # Closing before accept() turns into a bare HTTP 403 on the handshake, and
    # the browser then only sees close code 1006. Accept first so the client
    # receives the application close code.
    await websocket.accept()
    await websocket.close(code=code)


@ws_router.websocket("/ws/chats/{chat_id}")
async def chat_websocket(websocket: WebSocket, chat_id: uuid.UUID, token: str = Query(...)):
    db = SessionLocal()
    try:
        raw_user_id = decode_access_token(token)
        user = None
        if raw_user_id:
            try:
                user = db.query(User).filter(User.id == uuid.UUID(raw_user_id)).first()
            except ValueError:
                user = None
        if not user:
            await reject_websocket(websocket, WS_CLOSE_UNAUTHORIZED)
            return

        chat = db.query(Chat).filter(Chat.id == chat_id).first()
        if not chat:
            await reject_websocket(websocket, WS_CLOSE_NOT_FOUND)
            return

        owner_id, requester_id = get_participant_ids(chat)
        if user.id not in (owner_id, requester_id):
            await reject_websocket(websocket, WS_CLOSE_FORBIDDEN)
            return

        await manager.connect(chat_id, websocket)
        try:
            while True:
                try:
                    data = await websocket.receive_json()
                except (ValueError, KeyError):
                    continue

                if not isinstance(data, dict):
                    continue

                content = (data.get("content") or "").strip()
                if not content or len(content) > MAX_MESSAGE_CHARS:
                    continue
                if not message_limiter.allow(user.id):
                    continue

                message = ChatMessage(chat_id=chat_id, sender_id=user.id, content=content)
                db.add(message)

                recipient_id = requester_id if user.id == owner_id else owner_id
                notify_new_message(
                    db,
                    user_id=recipient_id,
                    actor_name=user.full_name,
                    entity_title=chat.reservation.listing.title,
                    link=f"/chats/{chat_id}",
                )

                db.commit()
                db.refresh(message)

                await manager.broadcast(
                    chat_id,
                    {
                        "id": str(message.id),
                        "chat_id": str(message.chat_id),
                        "sender_id": str(message.sender_id),
                        "content": message.content,
                        "created_at": message.created_at.isoformat(),
                    },
                )
        except WebSocketDisconnect:
            pass
        finally:
            manager.disconnect(chat_id, websocket)
    finally:
        db.close()
