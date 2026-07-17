import uuid
from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict

from app.models.exchange import ExchangeStatus


class ExchangeVerifyRequest(BaseModel):
    qr_uuid: uuid.UUID


class ExchangeOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    reservation_id: uuid.UUID
    status: ExchangeStatus
    completed_at: Optional[datetime] = None
    created_at: datetime
    listing_id: uuid.UUID
    listing_title: str
    owner_id: uuid.UUID
    requester_id: uuid.UUID
    role: Optional[str] = None
