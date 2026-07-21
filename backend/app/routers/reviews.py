import uuid
from typing import List

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.auth.dependencies import get_current_user
from app.database.session import get_db
from app.models.exchange import Exchange, ExchangeStatus
from app.models.notification import NotificationType
from app.models.review import Review
from app.models.user import User
from app.schemas.review import ReviewCreate, ReviewOut
from app.schemas.user import UserPublic
from app.utils.notifications import notify

router = APIRouter(tags=["reviews"])


@router.post("/reviews", response_model=ReviewOut, status_code=status.HTTP_201_CREATED)
def create_review(
    payload: ReviewCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    exchange = db.query(Exchange).filter(Exchange.id == payload.exchange_id).first()
    if not exchange:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Exchange not found")

    if exchange.status != ExchangeStatus.COMPLETED:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Exchange is not completed yet")

    owner_id = exchange.reservation.listing.owner_id
    requester_id = exchange.reservation.requester_id

    if current_user.id == owner_id:
        reviewee_id = requester_id
    elif current_user.id == requester_id:
        reviewee_id = owner_id
    else:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not a participant of this exchange")

    existing = (
        db.query(Review)
        .filter(Review.exchange_id == exchange.id, Review.reviewer_id == current_user.id)
        .first()
    )
    if existing:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="You already reviewed this exchange")

    review = Review(
        exchange_id=exchange.id,
        reviewer_id=current_user.id,
        reviewee_id=reviewee_id,
        rating=payload.rating,
        comment=payload.comment,
    )
    db.add(review)

    reviewee = db.query(User).filter(User.id == reviewee_id).first()
    new_count = reviewee.rating_count + 1
    reviewee.rating_avg = round((reviewee.rating_avg * reviewee.rating_count + payload.rating) / new_count, 2)
    reviewee.rating_count = new_count

    notify(
        db,
        user_id=reviewee_id,
        type=NotificationType.REVIEW_RECEIVED,
        actor_name=current_user.full_name,
        entity_title=exchange.reservation.listing.title,
        link=f"/profile/{reviewee_id}",
    )

    db.commit()
    db.refresh(review)

    return ReviewOut(
        id=review.id,
        exchange_id=review.exchange_id,
        reviewer=UserPublic.model_validate(current_user),
        reviewee_id=review.reviewee_id,
        rating=review.rating,
        comment=review.comment,
        created_at=review.created_at,
    )


@router.get("/users/{user_id}/reviews", response_model=List[ReviewOut])
def list_user_reviews(user_id: uuid.UUID, db: Session = Depends(get_db)):
    reviews = (
        db.query(Review)
        .filter(Review.reviewee_id == user_id)
        .order_by(Review.created_at.desc())
        .all()
    )
    return [
        ReviewOut(
            id=r.id,
            exchange_id=r.exchange_id,
            reviewer=UserPublic.model_validate(r.reviewer),
            reviewee_id=r.reviewee_id,
            rating=r.rating,
            comment=r.comment,
            created_at=r.created_at,
        )
        for r in reviews
    ]
