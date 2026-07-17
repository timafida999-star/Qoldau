import enum
import uuid

from sqlalchemy import Column, DateTime, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.database.base import Base, pg_enum


class ExchangeStatus(str, enum.Enum):
    PENDING = "pending"
    COMPLETED = "completed"


class Exchange(Base):
    __tablename__ = "exchanges"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    reservation_id = Column(UUID(as_uuid=True), ForeignKey("reservations.id", ondelete="CASCADE"), unique=True, nullable=False)
    qr_uuid = Column(UUID(as_uuid=True), unique=True, default=uuid.uuid4, nullable=False)
    status = Column(pg_enum(ExchangeStatus), default=ExchangeStatus.PENDING, nullable=False)
    completed_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    reservation = relationship("Reservation", back_populates="exchange")
    reviews = relationship("Review", back_populates="exchange", cascade="all, delete-orphan")
