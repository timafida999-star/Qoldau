import uuid
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, Response, status
from sqlalchemy.orm import Session

from app.auth.dependencies import get_current_user
from app.database.session import get_db
from app.models.exchange import Exchange, ExchangeStatus
from app.models.listing import ListingStatus
from app.models.notification import NotificationType
from app.models.user import User
from app.schemas.exchange import ExchangeOut, ExchangeVerifyRequest
from app.utils.notifications import notify
from app.utils.qr import generate_qr_png

router = APIRouter(prefix="/exchanges", tags=["exchanges"])


def get_exchange_or_404(exchange_id: uuid.UUID, db: Session) -> Exchange:
    exchange = db.query(Exchange).filter(Exchange.id == exchange_id).first()
    if not exchange:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Exchange not found")
    return exchange


def to_exchange_out(exchange: Exchange, viewer: User) -> ExchangeOut:
    listing = exchange.reservation.listing
    role = "owner" if listing.owner_id == viewer.id else "requester"
    return ExchangeOut(
        id=exchange.id,
        reservation_id=exchange.reservation_id,
        status=exchange.status,
        completed_at=exchange.completed_at,
        created_at=exchange.created_at,
        listing_id=listing.id,
        listing_title=listing.title,
        owner_id=listing.owner_id,
        requester_id=exchange.reservation.requester_id,
        role=role,
    )


def ensure_participant(exchange: Exchange, user_id: uuid.UUID) -> None:
    listing = exchange.reservation.listing
    if user_id not in (listing.owner_id, exchange.reservation.requester_id):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not a participant of this exchange")


@router.get("/{exchange_id}", response_model=ExchangeOut)
def get_exchange(exchange_id: uuid.UUID, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    exchange = get_exchange_or_404(exchange_id, db)
    ensure_participant(exchange, current_user.id)
    return to_exchange_out(exchange, current_user)


@router.get("/{exchange_id}/qr")
def get_exchange_qr(exchange_id: uuid.UUID, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    exchange = get_exchange_or_404(exchange_id, db)
    listing = exchange.reservation.listing

    if listing.owner_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Only the listing owner can view this QR code")

    if exchange.status == ExchangeStatus.COMPLETED:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Exchange already completed")

    png_bytes = generate_qr_png(str(exchange.qr_uuid))
    return Response(content=png_bytes, media_type="image/png")


@router.post("/verify", response_model=ExchangeOut)
def verify_exchange(
    payload: ExchangeVerifyRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    exchange = db.query(Exchange).filter(Exchange.qr_uuid == payload.qr_uuid).first()
    if not exchange:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Invalid code")

    if exchange.reservation.requester_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Only the recipient can confirm this exchange")

    if exchange.status == ExchangeStatus.COMPLETED:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Exchange already completed")

    exchange.status = ExchangeStatus.COMPLETED
    exchange.completed_at = datetime.now(timezone.utc)
    listing = exchange.reservation.listing
    listing.status = ListingStatus.COMPLETED

    notify(
        db,
        user_id=listing.owner_id,
        type=NotificationType.EXCHANGE_COMPLETED,
        actor_name=current_user.full_name,
        entity_title=listing.title,
        link=f"/reviews/new/{exchange.id}",
    )

    db.commit()
    db.refresh(exchange)
    return to_exchange_out(exchange, current_user)
