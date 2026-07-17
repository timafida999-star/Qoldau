import uuid
from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, ConfigDict, Field

from app.models.listing import Category, Condition, ListingStatus
from app.schemas.user import UserPublic


class ListingImageOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    image_url: str
    position: int


class ListingCreate(BaseModel):
    title: str = Field(min_length=3, max_length=120)
    description: str = Field(min_length=10)
    category: Category
    condition: Condition
    latitude: float
    longitude: float
    address_text: Optional[str] = None


class ListingUpdate(BaseModel):
    title: Optional[str] = Field(default=None, min_length=3, max_length=120)
    description: Optional[str] = Field(default=None, min_length=10)
    category: Optional[Category] = None
    condition: Optional[Condition] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    address_text: Optional[str] = None


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
    images: List[ListingImageOut] = []
    created_at: datetime
