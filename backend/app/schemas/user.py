import uuid
from datetime import datetime
from typing import Optional

from pydantic import BaseModel, EmailStr, ConfigDict

from app.schemas.fields import Bio, Email, FullName, NewPassword, Phone


class UserBase(BaseModel):
    full_name: FullName
    phone: Optional[Phone] = None
    bio: Optional[Bio] = None


class UserCreate(BaseModel):
    email: Email
    password: NewPassword
    full_name: FullName


class UserUpdate(BaseModel):
    full_name: Optional[FullName] = None
    phone: Optional[Phone] = None
    bio: Optional[Bio] = None


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
