import uuid
from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict

from app.models.notification import NotificationType


class NotificationOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    type: NotificationType
    actor_name: Optional[str] = None
    entity_title: Optional[str] = None
    link: Optional[str] = None
    is_read: bool
    created_at: datetime


class UnreadCount(BaseModel):
    count: int
