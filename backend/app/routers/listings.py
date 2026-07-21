import uuid
from typing import List, Optional

from fastapi import APIRouter, Depends, File, HTTPException, Query, UploadFile, status
from sqlalchemy.orm import Session

from app.auth.dependencies import get_current_user
from app.database.session import get_db
from app.models.listing import Category, Condition, Listing, ListingImage, ListingStatus
from app.models.user import User
from app.schemas.listing import ListingCreate, ListingImageOut, ListingOut, ListingPage, ListingSummary, ListingUpdate
from app.utils.files import save_upload

router = APIRouter(prefix="/listings", tags=["listings"])

ALLOWED_IMAGE_TYPES = {"image/jpeg", "image/png", "image/webp"}


def get_listing_or_404(listing_id: uuid.UUID, db: Session) -> Listing:
    listing = db.query(Listing).filter(Listing.id == listing_id).first()
    if not listing:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Listing not found")
    return listing


def ensure_owner(listing: Listing, user: User) -> None:
    if listing.owner_id != user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not the listing owner")


@router.get("", response_model=ListingPage)
def list_listings(
    category: Optional[Category] = None,
    status_filter: Optional[ListingStatus] = Query(default=None, alias="status"),
    search: Optional[str] = None,
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=12, ge=1, le=48),
    min_lat: Optional[float] = None,
    max_lat: Optional[float] = None,
    min_lng: Optional[float] = None,
    max_lng: Optional[float] = None,
    db: Session = Depends(get_db),
):
    query = db.query(Listing)

    if category:
        query = query.filter(Listing.category == category)
    if status_filter:
        query = query.filter(Listing.status == status_filter)
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

    total = query.count()
    items = (
        query.order_by(Listing.created_at.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
        .all()
    )
    return ListingPage(
        items=items,
        total=total,
        page=page,
        page_size=page_size,
        has_more=page * page_size < total,
    )


@router.post("", response_model=ListingOut, status_code=status.HTTP_201_CREATED)
def create_listing(
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
def get_listing(listing_id: uuid.UUID, db: Session = Depends(get_db)):
    return get_listing_or_404(listing_id, db)


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
def upload_listing_images(
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
