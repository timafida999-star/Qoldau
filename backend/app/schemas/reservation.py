import uuid
from datetime import datetime
from typing import Literal, Optional

from pydantic import BaseModel, ConfigDict

from app.models.reservation import ReservationStatus
from app.schemas.fields import ReservationMessage
from app.schemas.user import UserPublic


class ReservationCreate(BaseModel):
    # A short "why me?" note shown to the owner next to the request.
    message: Optional[ReservationMessage] = None


class ReservationAction(BaseModel):
    action: Literal["accept", "decline", "cancel"]


class ListingBrief(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    title: str
    status: str


class ReservationOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    listing: ListingBrief
    requester: UserPublic
    status: ReservationStatus
    message: Optional[str] = None
    chat_id: Optional[uuid.UUID] = None
    exchange_id: Optional[uuid.UUID] = None
    created_at: datetime
    updated_at: datetime
    role: Optional[Literal["owner", "requester"]] = None
