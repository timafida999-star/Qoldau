import enum
import uuid

from sqlalchemy import Column, DateTime, Float, ForeignKey, Index, Integer, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.database.base import Base, pg_enum


class Category(str, enum.Enum):
    ELECTRONICS = "electronics"
    FURNITURE = "furniture"
    CLOTHES = "clothes"
    BOOKS = "books"
    KITCHEN = "kitchen"
    KIDS = "kids"
    OTHER = "other"


class Condition(str, enum.Enum):
    NEW = "new"
    LIKE_NEW = "like_new"
    GOOD = "good"
    FAIR = "fair"
    WORN = "worn"


class ListingStatus(str, enum.Enum):
    AVAILABLE = "available"
    RESERVED = "reserved"
    COMPLETED = "completed"


class Listing(Base):
    __tablename__ = "listings"
    # The home feed filters by category/status/owner and orders by created_at;
    # the near-me filter prefilters on the lat/lng bounding box.
    __table_args__ = (Index("ix_listings_lat_lng", "latitude", "longitude"),)

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    owner_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    title = Column(String, nullable=False)
    description = Column(Text, nullable=False)
    category = Column(pg_enum(Category), nullable=False, index=True)
    condition = Column(pg_enum(Condition), nullable=False)
    status = Column(pg_enum(ListingStatus), default=ListingStatus.AVAILABLE, nullable=False, index=True)
    latitude = Column(Float, nullable=False)
    longitude = Column(Float, nullable=False)
    address_text = Column(String, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), index=True)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    owner = relationship("User", back_populates="listings")
    images = relationship("ListingImage", back_populates="listing", cascade="all, delete-orphan", order_by="ListingImage.position")
    reservations = relationship("Reservation", back_populates="listing", cascade="all, delete-orphan")


class ListingImage(Base):
    __tablename__ = "listing_images"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    listing_id = Column(UUID(as_uuid=True), ForeignKey("listings.id", ondelete="CASCADE"), nullable=False)
    image_url = Column(String, nullable=False)
    # Smaller copy for grid cards; nullable because rows uploaded before the
    # column existed have no thumbnail (the frontend falls back to image_url).
    thumb_url = Column(String, nullable=True)
    position = Column(Integer, default=0, nullable=False)

    listing = relationship("Listing", back_populates="images")
