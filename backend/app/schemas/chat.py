import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict

from app.schemas.user import UserPublic


class ChatMessageOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    chat_id: uuid.UUID
    sender_id: uuid.UUID
    content: str
    created_at: datetime


class ChatMessageCreate(BaseModel):
    content: str


class ChatOut(BaseModel):
    id: uuid.UUID
    reservation_id: uuid.UUID
    listing_title: str
    other_participant: UserPublic
    created_at: datetime
