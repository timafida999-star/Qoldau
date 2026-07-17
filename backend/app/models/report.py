import enum
import uuid

from sqlalchemy import Column, DateTime, ForeignKey, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.database.base import Base, pg_enum


class ReportTargetType(str, enum.Enum):
    LISTING = "listing"
    USER = "user"


class ReportReason(str, enum.Enum):
    SPAM = "spam"
    INAPPROPRIATE = "inappropriate"
    FRAUD = "fraud"
    OTHER = "other"


class ReportStatus(str, enum.Enum):
    OPEN = "open"
    RESOLVED = "resolved"


class Report(Base):
    __tablename__ = "reports"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    reporter_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    target_type = Column(pg_enum(ReportTargetType), nullable=False)
    target_id = Column(UUID(as_uuid=True), nullable=False)
    reason = Column(pg_enum(ReportReason), nullable=False)
    description = Column(Text, nullable=True)
    status = Column(pg_enum(ReportStatus), default=ReportStatus.OPEN, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    reporter = relationship("User")
