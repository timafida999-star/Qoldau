import uuid
from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field

from app.schemas.user import UserPublic


class ReviewCreate(BaseModel):
    exchange_id: uuid.UUID
    rating: int = Field(ge=1, le=5)
    comment: Optional[str] = None


class ReviewOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    exchange_id: uuid.UUID
    reviewer: UserPublic
    reviewee_id: uuid.UUID
    rating: int
    comment: Optional[str] = None
    created_at: datetime
