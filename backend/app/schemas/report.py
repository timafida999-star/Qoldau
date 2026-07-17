import uuid
from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict

from app.models.report import ReportReason, ReportStatus, ReportTargetType
from app.schemas.user import UserPublic


class ReportCreate(BaseModel):
    target_type: ReportTargetType
    target_id: uuid.UUID
    reason: ReportReason
    description: Optional[str] = None


class ReportOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    reporter: UserPublic
    target_type: ReportTargetType
    target_id: uuid.UUID
    reason: ReportReason
    description: Optional[str] = None
    status: ReportStatus
    created_at: datetime
