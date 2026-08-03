"""listing image thumbnails + query indexes + trigram search

Revision ID: 0004
Revises: 0003
Create Date: 2026-08-03

"""
from alembic import op
import sqlalchemy as sa

revision = "0004"
down_revision = "0003"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("listing_images", sa.Column("thumb_url", sa.String(), nullable=True))

    # Everything the hot queries filter or order by.
    op.create_index("ix_listings_owner_id", "listings", ["owner_id"])
    op.create_index("ix_listings_category", "listings", ["category"])
    op.create_index("ix_listings_status", "listings", ["status"])
    op.create_index("ix_listings_created_at", "listings", ["created_at"])
    op.create_index("ix_listings_lat_lng", "listings", ["latitude", "longitude"])
    op.create_index("ix_reservations_listing_id", "reservations", ["listing_id"])
    op.create_index("ix_reservations_requester_id", "reservations", ["requester_id"])
    op.create_index("ix_chat_messages_chat_created", "chat_messages", ["chat_id", "created_at"])
    op.create_index("ix_reviews_reviewee_id", "reviews", ["reviewee_id"])

    # Search runs ILIKE '%term%', which btree cannot help with; trigram GIN
    # indexes serve exactly that pattern. The extension ships with Postgres.
    op.execute("CREATE EXTENSION IF NOT EXISTS pg_trgm")
    op.execute("CREATE INDEX ix_listings_title_trgm ON listings USING gin (title gin_trgm_ops)")
    op.execute("CREATE INDEX ix_listings_description_trgm ON listings USING gin (description gin_trgm_ops)")


def downgrade() -> None:
    op.execute("DROP INDEX IF EXISTS ix_listings_description_trgm")
    op.execute("DROP INDEX IF EXISTS ix_listings_title_trgm")
    op.drop_index("ix_reviews_reviewee_id", table_name="reviews")
    op.drop_index("ix_chat_messages_chat_created", table_name="chat_messages")
    op.drop_index("ix_reservations_requester_id", table_name="reservations")
    op.drop_index("ix_reservations_listing_id", table_name="reservations")
    op.drop_index("ix_listings_lat_lng", table_name="listings")
    op.drop_index("ix_listings_created_at", table_name="listings")
    op.drop_index("ix_listings_status", table_name="listings")
    op.drop_index("ix_listings_category", table_name="listings")
    op.drop_index("ix_listings_owner_id", table_name="listings")
    op.drop_column("listing_images", "thumb_url")
