import enum
import uuid

from sqlalchemy import Boolean, Column, DateTime, ForeignKey, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.database.base import Base, pg_enum


class NotificationType(str, enum.Enum):
    RESERVATION_REQUESTED = "reservation_requested"
    RESERVATION_ACCEPTED = "reservation_accepted"
    RESERVATION_DECLINED = "reservation_declined"
    RESERVATION_CANCELLED = "reservation_cancelled"
    MESSAGE_RECEIVED = "message_received"
    EXCHANGE_COMPLETED = "exchange_completed"
    REVIEW_RECEIVED = "review_received"


class Notification(Base):
    """A single in-app notification for one recipient.

    Only the event type plus its actors are stored, never a rendered sentence,
    so the frontend can display it in the reader's own language.
    """

    __tablename__ = "notifications"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    type = Column(pg_enum(NotificationType), nullable=False)
    actor_name = Column(String, nullable=True)
    entity_title = Column(String, nullable=True)
    link = Column(String, nullable=True)
    is_read = Column(Boolean, default=False, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    user = relationship("User")
