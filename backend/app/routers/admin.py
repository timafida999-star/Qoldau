import uuid
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.auth.dependencies import get_current_admin
from app.database.session import get_db
from app.models.listing import Listing
from app.models.report import Report, ReportStatus
from app.models.user import User
from app.schemas.report import ReportOut
from app.schemas.user import UserPublic

router = APIRouter(prefix="/admin", tags=["admin"])


@router.get("/reports", response_model=List[ReportOut])
def list_reports(
    status_filter: Optional[ReportStatus] = None,
    _admin: User = Depends(get_current_admin),
    db: Session = Depends(get_db),
):
    query = db.query(Report)
    if status_filter:
        query = query.filter(Report.status == status_filter)
    reports = query.order_by(Report.created_at.desc()).all()

    return [
        ReportOut(
            id=r.id,
            reporter=UserPublic.model_validate(r.reporter),
            target_type=r.target_type,
            target_id=r.target_id,
            reason=r.reason,
            description=r.description,
            status=r.status,
            created_at=r.created_at,
        )
        for r in reports
    ]


@router.patch("/reports/{report_id}", response_model=ReportOut)
def resolve_report(
    report_id: uuid.UUID,
    _admin: User = Depends(get_current_admin),
    db: Session = Depends(get_db),
):
    report = db.query(Report).filter(Report.id == report_id).first()
    if not report:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Report not found")

    report.status = ReportStatus.RESOLVED
    db.commit()
    db.refresh(report)

    return ReportOut(
        id=report.id,
        reporter=UserPublic.model_validate(report.reporter),
        target_type=report.target_type,
        target_id=report.target_id,
        reason=report.reason,
        description=report.description,
        status=report.status,
        created_at=report.created_at,
    )


@router.delete("/listings/{listing_id}", status_code=status.HTTP_204_NO_CONTENT)
def admin_delete_listing(
    listing_id: uuid.UUID,
    _admin: User = Depends(get_current_admin),
    db: Session = Depends(get_db),
):
    listing = db.query(Listing).filter(Listing.id == listing_id).first()
    if not listing:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Listing not found")
    db.delete(listing)
    db.commit()
