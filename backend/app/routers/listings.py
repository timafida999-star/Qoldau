import hashlib
import math
import uuid
from typing import List, Optional

from fastapi import APIRouter, Depends, File, HTTPException, Query, Request, UploadFile, status
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.auth.dependencies import get_current_user, get_current_user_optional
from app.config import settings
from app.database.session import get_db
from app.rate_limit import limiter
from app.models.listing import Category, Condition, Listing, ListingImage, ListingStatus
from app.models.reservation import Reservation, ReservationStatus
from app.models.user import User
from app.schemas.listing import ListingCreate, ListingImageOut, ListingOut, ListingPage, ListingSummary, ListingUpdate
from app.utils.files import save_upload
from app.utils.geo import EARTH_RADIUS_KM, approximate_location, haversine_km

router = APIRouter(prefix="/listings", tags=["listings"])

ALLOWED_IMAGE_TYPES = {"image/jpeg", "image/png", "image/webp"}

DEFAULT_NEAR_RADIUS_KM = 10

# Domain-separated key for the coordinate blur, so the JWT secret itself is
# never used as an HMAC key for anything else.
_LOCATION_BLUR_KEY = hashlib.sha256(f"location-blur:{settings.jwt_secret_key}".encode()).hexdigest()


def _distance_km_expr(near_lat: float, near_lng: float):
    """Haversine distance from (near_lat, near_lng) as a SQL expression."""
    lat_radians = func.radians(Listing.latitude)
    dlat_half = func.radians(Listing.latitude - near_lat) / 2
    dlng_half = func.radians(Listing.longitude - near_lng) / 2
    a = (
        func.pow(func.sin(dlat_half), 2)
        + math.cos(math.radians(near_lat)) * func.cos(lat_radians) * func.pow(func.sin(dlng_half), 2)
    )
    return 2 * EARTH_RADIUS_KM * func.asin(func.sqrt(a))


def _blurred(listing: Listing) -> tuple[float, float]:
    return approximate_location(listing.id, listing.latitude, listing.longitude, _LOCATION_BLUR_KEY)


def _sees_exact_location(listing: Listing, viewer: Optional[User], db: Session) -> bool:
    """Exact meeting point is for the owner, admins, and an accepted requester."""
    if viewer is None:
        return False
    if viewer.id == listing.owner_id or viewer.is_admin:
        return True
    return (
        db.query(Reservation.id)
        .filter(
            Reservation.listing_id == listing.id,
            Reservation.requester_id == viewer.id,
            Reservation.status == ReservationStatus.ACCEPTED,
        )
        .first()
        is not None
    )


def get_listing_or_404(listing_id: uuid.UUID, db: Session) -> Listing:
    listing = db.query(Listing).filter(Listing.id == listing_id).first()
    if not listing:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Listing not found")
    return listing


def ensure_owner(listing: Listing, user: User) -> None:
    if listing.owner_id != user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not the listing owner")


def _listings_with_exact_location(items: List[Listing], viewer: Optional[User], db: Session) -> set:
    """IDs from `items` whose true coordinates this viewer may see.

    One batched query for the viewer's accepted reservations instead of a
    per-listing lookup.
    """
    if viewer is None:
        return set()
    if viewer.is_admin:
        return {listing.id for listing in items}

    exact_ids = {listing.id for listing in items if listing.owner_id == viewer.id}
    other_ids = [listing.id for listing in items if listing.id not in exact_ids]
    if other_ids:
        accepted = (
            db.query(Reservation.listing_id)
            .filter(
                Reservation.requester_id == viewer.id,
                Reservation.status == ReservationStatus.ACCEPTED,
                Reservation.listing_id.in_(other_ids),
            )
            .all()
        )
        exact_ids.update(row[0] for row in accepted)
    return exact_ids


@router.get("", response_model=ListingPage)
def list_listings(
    category: Optional[Category] = None,
    status_filter: Optional[ListingStatus] = Query(default=None, alias="status"),
    search: Optional[str] = None,
    owner: Optional[uuid.UUID] = None,
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=12, ge=1, le=48),
    min_lat: Optional[float] = None,
    max_lat: Optional[float] = None,
    min_lng: Optional[float] = None,
    max_lng: Optional[float] = None,
    near_lat: Optional[float] = Query(default=None, ge=-90, le=90),
    near_lng: Optional[float] = Query(default=None, ge=-180, le=180),
    radius_km: Optional[float] = Query(default=None, gt=0, le=100),
    viewer: Optional[User] = Depends(get_current_user_optional),
    db: Session = Depends(get_db),
):
    if (near_lat is None) != (near_lng is None):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="near_lat and near_lng must be provided together"
        )
    if radius_km is not None and near_lat is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="radius_km requires near_lat and near_lng"
        )

    query = db.query(Listing)

    if category:
        query = query.filter(Listing.category == category)
    if status_filter:
        query = query.filter(Listing.status == status_filter)
    if owner:
        query = query.filter(Listing.owner_id == owner)
    if search:
        term = f"%{search.strip()}%"
        query = query.filter(Listing.title.ilike(term) | Listing.description.ilike(term))
    if min_lat is not None:
        query = query.filter(Listing.latitude >= min_lat)
    if max_lat is not None:
        query = query.filter(Listing.latitude <= max_lat)
    if min_lng is not None:
        query = query.filter(Listing.longitude >= min_lng)
    if max_lng is not None:
        query = query.filter(Listing.longitude <= max_lng)

    near_active = near_lat is not None and near_lng is not None
    order_by = Listing.created_at.desc()
    if near_active:
        radius = radius_km if radius_km is not None else DEFAULT_NEAR_RADIUS_KM
        distance = _distance_km_expr(near_lat, near_lng)
        query = query.filter(distance <= radius)
        # "Near me" reads as "closest first", not "newest first".
        order_by = distance.asc()

    total = query.count()
    items = (
        query.order_by(order_by)
        .offset((page - 1) * page_size)
        .limit(page_size)
        .all()
    )

    exact_ids = _listings_with_exact_location(items, viewer, db)
    summaries = []
    for listing in items:
        summary = ListingSummary.model_validate(listing)
        updates = {}
        if listing.id not in exact_ids:
            blurred_lat, blurred_lng = _blurred(listing)
            updates = {"latitude": blurred_lat, "longitude": blurred_lng, "location_is_approximate": True}
        if near_active:
            # Distance comes from the true point so the badge agrees with the filter.
            updates["distance_km"] = round(haversine_km(near_lat, near_lng, listing.latitude, listing.longitude), 1)
        if updates:
            summary = summary.model_copy(update=updates)
        summaries.append(summary)

    return ListingPage(
        items=summaries,
        total=total,
        page=page,
        page_size=page_size,
        has_more=page * page_size < total,
    )


@router.post("", response_model=ListingOut, status_code=status.HTTP_201_CREATED)
@limiter.limit("10/minute;40/hour")
def create_listing(
    request: Request,
    payload: ListingCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    listing = Listing(owner_id=current_user.id, **payload.model_dump())
    db.add(listing)
    db.commit()
    db.refresh(listing)
    return listing


@router.get("/{listing_id}", response_model=ListingOut)
def get_listing(
    listing_id: uuid.UUID,
    viewer: Optional[User] = Depends(get_current_user_optional),
    db: Session = Depends(get_db),
):
    listing = get_listing_or_404(listing_id, db)
    out = ListingOut.model_validate(listing)
    if not _sees_exact_location(listing, viewer, db):
        blurred_lat, blurred_lng = _blurred(listing)
        out = out.model_copy(
            update={"latitude": blurred_lat, "longitude": blurred_lng, "location_is_approximate": True}
        )
    return out


@router.patch("/{listing_id}", response_model=ListingOut)
def update_listing(
    listing_id: uuid.UUID,
    payload: ListingUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    listing = get_listing_or_404(listing_id, db)
    ensure_owner(listing, current_user)

    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(listing, field, value)

    db.commit()
    db.refresh(listing)
    return listing


@router.delete("/{listing_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_listing(
    listing_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    listing = get_listing_or_404(listing_id, db)
    ensure_owner(listing, current_user)
    db.delete(listing)
    db.commit()


@router.post("/{listing_id}/images", response_model=List[ListingImageOut], status_code=status.HTTP_201_CREATED)
@limiter.limit("30/minute")
def upload_listing_images(
    request: Request,
    listing_id: uuid.UUID,
    files: List[UploadFile] = File(...),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    listing = get_listing_or_404(listing_id, db)
    ensure_owner(listing, current_user)

    current_max_position = max((img.position for img in listing.images), default=-1)
    created_images = []

    for offset, file in enumerate(files, start=1):
        if file.content_type not in ALLOWED_IMAGE_TYPES:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Unsupported image type: {file.content_type}")
        url = save_upload(file, "listings")
        image = ListingImage(listing_id=listing.id, image_url=url, position=current_max_position + offset)
        db.add(image)
        created_images.append(image)

    db.commit()
    for image in created_images:
        db.refresh(image)
    return created_images


@router.delete("/{listing_id}/images/{image_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_listing_image(
    listing_id: uuid.UUID,
    image_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    listing = get_listing_or_404(listing_id, db)
    ensure_owner(listing, current_user)

    image = db.query(ListingImage).filter(ListingImage.id == image_id, ListingImage.listing_id == listing.id).first()
    if not image:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Image not found")

    db.delete(image)
    db.commit()
