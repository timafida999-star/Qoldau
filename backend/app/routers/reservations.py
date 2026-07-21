import uuid
from typing import List

from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.orm import Session

from app.auth.dependencies import get_current_user
from app.database.session import get_db
from app.rate_limit import limiter
from app.models.chat import Chat
from app.models.exchange import Exchange
from app.models.listing import Listing, ListingStatus
from app.models.notification import NotificationType
from app.models.reservation import Reservation, ReservationStatus
from app.models.user import User
from app.schemas.reservation import ListingBrief, ReservationAction, ReservationOut
from app.schemas.user import UserPublic
from app.utils.notifications import notify

router = APIRouter(prefix="/reservations", tags=["reservations"])
listing_reservations_router = APIRouter(prefix="/listings", tags=["reservations"])


def to_reservation_out(reservation: Reservation, viewer: User) -> ReservationOut:
    role = "owner" if reservation.listing.owner_id == viewer.id else "requester"
    return ReservationOut(
        id=reservation.id,
        listing=ListingBrief.model_validate(reservation.listing),
        requester=UserPublic.model_validate(reservation.requester),
        status=reservation.status,
        chat_id=reservation.chat.id if reservation.chat else None,
        exchange_id=reservation.exchange.id if reservation.exchange else None,
        created_at=reservation.created_at,
        updated_at=reservation.updated_at,
        role=role,
    )


@listing_reservations_router.post(
    "/{listing_id}/reservations", response_model=ReservationOut, status_code=status.HTTP_201_CREATED
)
@limiter.limit("20/minute;100/hour")
def create_reservation(
    request: Request,
    listing_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    listing = db.query(Listing).filter(Listing.id == listing_id).first()
    if not listing:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Listing not found")

    if listing.owner_id == current_user.id:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="You cannot reserve your own listing")

    if listing.status != ListingStatus.AVAILABLE:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Listing is not available")

    existing = (
        db.query(Reservation)
        .filter(
            Reservation.listing_id == listing.id,
            Reservation.requester_id == current_user.id,
            Reservation.status == ReservationStatus.PENDING,
        )
        .first()
    )
    if existing:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="You already requested this item")

    reservation = Reservation(listing_id=listing.id, requester_id=current_user.id)
    db.add(reservation)

    notify(
        db,
        user_id=listing.owner_id,
        type=NotificationType.RESERVATION_REQUESTED,
        actor_name=current_user.full_name,
        entity_title=listing.title,
        link="/reservations",
    )

    db.commit()
    db.refresh(reservation)
    return to_reservation_out(reservation, current_user)


@router.get("/mine", response_model=List[ReservationOut])
def list_my_reservations(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    reservations = (
        db.query(Reservation)
        .join(Listing)
        .filter((Reservation.requester_id == current_user.id) | (Listing.owner_id == current_user.id))
        .order_by(Reservation.created_at.desc())
        .all()
    )
    return [to_reservation_out(r, current_user) for r in reservations]


@router.patch("/{reservation_id}", response_model=ReservationOut)
def update_reservation(
    reservation_id: uuid.UUID,
    payload: ReservationAction,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    reservation = db.query(Reservation).filter(Reservation.id == reservation_id).first()
    if not reservation:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Reservation not found")

    listing = reservation.listing
    is_owner = listing.owner_id == current_user.id
    is_requester = reservation.requester_id == current_user.id

    if payload.action in ("accept", "decline"):
        if not is_owner:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Only the listing owner can do this")
        if reservation.status != ReservationStatus.PENDING:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Reservation already resolved")

        if payload.action == "accept":
            reservation.status = ReservationStatus.ACCEPTED
            listing.status = ListingStatus.RESERVED

            chat = Chat(reservation_id=reservation.id)
            db.add(chat)

            exchange = Exchange(reservation_id=reservation.id)
            db.add(exchange)

            other_pending = (
                db.query(Reservation)
                .filter(
                    Reservation.listing_id == listing.id,
                    Reservation.id != reservation.id,
                    Reservation.status == ReservationStatus.PENDING,
                )
                .all()
            )
            for other in other_pending:
                other.status = ReservationStatus.DECLINED
                notify(
                    db,
                    user_id=other.requester_id,
                    type=NotificationType.RESERVATION_DECLINED,
                    actor_name=current_user.full_name,
                    entity_title=listing.title,
                    link="/reservations",
                )

            notify(
                db,
                user_id=reservation.requester_id,
                type=NotificationType.RESERVATION_ACCEPTED,
                actor_name=current_user.full_name,
                entity_title=listing.title,
                link="/reservations",
            )
        else:
            reservation.status = ReservationStatus.DECLINED
            notify(
                db,
                user_id=reservation.requester_id,
                type=NotificationType.RESERVATION_DECLINED,
                actor_name=current_user.full_name,
                entity_title=listing.title,
                link="/reservations",
            )

    elif payload.action == "cancel":
        if not is_requester:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Only the requester can cancel")
        if reservation.status != ReservationStatus.PENDING:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Only pending requests can be cancelled")
        reservation.status = ReservationStatus.CANCELLED
        notify(
            db,
            user_id=listing.owner_id,
            type=NotificationType.RESERVATION_CANCELLED,
            actor_name=current_user.full_name,
            entity_title=listing.title,
            link="/reservations",
        )

    db.commit()
    db.refresh(reservation)
    return to_reservation_out(reservation, current_user)
