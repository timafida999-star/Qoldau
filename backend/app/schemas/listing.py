import uuid
from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, ConfigDict

from app.models.listing import Category, Condition, ListingStatus
from app.schemas.fields import (
    AddressText,
    Latitude,
    ListingDescription,
    ListingTitle,
    Longitude,
)
from app.schemas.user import UserPublic


class ListingImageOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    image_url: str
    # Null for images uploaded before thumbnails existed; clients fall back to image_url.
    thumb_url: Optional[str] = None
    position: int


class ListingCreate(BaseModel):
    title: ListingTitle
    description: ListingDescription
    category: Category
    condition: Condition
    latitude: Latitude
    longitude: Longitude
    address_text: Optional[AddressText] = None


class ListingUpdate(BaseModel):
    title: Optional[ListingTitle] = None
    description: Optional[ListingDescription] = None
    category: Optional[Category] = None
    condition: Optional[Condition] = None
    latitude: Optional[Latitude] = None
    longitude: Optional[Longitude] = None
    address_text: Optional[AddressText] = None


class ListingOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    owner_id: uuid.UUID
    owner: UserPublic
    title: str
    description: str
    category: Category
    condition: Condition
    status: ListingStatus
    latitude: float
    longitude: float
    # True when the coordinates above are deliberately blurred (see utils/geo.py):
    # only the owner, an admin, or a requester with an accepted reservation gets
    # the exact meeting point.
    location_is_approximate: bool = False
    address_text: Optional[str] = None
    images: List[ListingImageOut] = []
    created_at: datetime
    updated_at: datetime


class ListingSummary(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    title: str
    category: Category
    condition: Condition
    status: ListingStatus
    latitude: float
    longitude: float
    location_is_approximate: bool = False
    # Filled only when the request filters by proximity (near_lat/near_lng).
    distance_km: Optional[float] = None
    address_text: Optional[str] = None
    images: List[ListingImageOut] = []
    created_at: datetime


class ListingPage(BaseModel):
    items: List[ListingSummary]
    total: int
    page: int
    page_size: int
    has_more: bool
