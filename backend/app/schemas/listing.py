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
    address_text: Optional[str] = None
    images: List[ListingImageOut] = []
    created_at: datetime


class ListingPage(BaseModel):
    items: List[ListingSummary]
    total: int
    page: int
    page_size: int
    has_more: bool
