import uuid
from datetime import datetime
from typing import Optional

from pydantic import BaseModel, EmailStr, ConfigDict


class UserBase(BaseModel):
    full_name: str
    phone: Optional[str] = None
    bio: Optional[str] = None


class UserCreate(BaseModel):
    email: EmailStr
    password: str
    full_name: str


class UserUpdate(BaseModel):
    full_name: Optional[str] = None
    phone: Optional[str] = None
    bio: Optional[str] = None


class UserPublic(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    full_name: str
    avatar_url: Optional[str] = None
    bio: Optional[str] = None
    rating_avg: float
    rating_count: int
    created_at: datetime


class UserMe(UserPublic):
    email: EmailStr
    phone: Optional[str] = None
    is_admin: bool
