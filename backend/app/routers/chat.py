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
from app.websocket.manager import manager

router = APIRouter(prefix="/chats", tags=["chat"])


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
        chat = db.query(Chat).filter(Chat.id == chat_id).first()

        if not user or not chat:
            await websocket.close(code=4401)
            return

        owner_id, requester_id = get_participant_ids(chat)
        if user.id not in (owner_id, requester_id):
            await websocket.close(code=4403)
            return

        await manager.connect(chat_id, websocket)
        try:
            while True:
                data = await websocket.receive_json()
                content = (data.get("content") or "").strip()
                if not content:
                    continue

                message = ChatMessage(chat_id=chat_id, sender_id=user.id, content=content)
                db.add(message)
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
            manager.disconnect(chat_id, websocket)
    finally:
        db.close()
