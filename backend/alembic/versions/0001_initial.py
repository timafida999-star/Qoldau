"""initial schema

Revision ID: 0001
Revises:
Create Date: 2026-07-16

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "0001"
down_revision = None
branch_labels = None
depends_on = None

category_enum = postgresql.ENUM(
    "electronics", "furniture", "clothes", "books", "kitchen", "kids", "other",
    name="category", create_type=False,
)
condition_enum = postgresql.ENUM(
    "new", "like_new", "good", "fair", "worn", name="condition", create_type=False
)
listing_status_enum = postgresql.ENUM(
    "available", "reserved", "completed", name="listingstatus", create_type=False
)
reservation_status_enum = postgresql.ENUM(
    "pending", "accepted", "declined", "cancelled", name="reservationstatus", create_type=False
)
exchange_status_enum = postgresql.ENUM("pending", "completed", name="exchangestatus", create_type=False)
report_target_type_enum = postgresql.ENUM("listing", "user", name="reporttargettype", create_type=False)
report_reason_enum = postgresql.ENUM(
    "spam", "inappropriate", "fraud", "other", name="reportreason", create_type=False
)
report_status_enum = postgresql.ENUM("open", "resolved", name="reportstatus", create_type=False)


def upgrade() -> None:
    bind = op.get_bind()
    category_enum.create(bind, checkfirst=True)
    condition_enum.create(bind, checkfirst=True)
    listing_status_enum.create(bind, checkfirst=True)
    reservation_status_enum.create(bind, checkfirst=True)
    exchange_status_enum.create(bind, checkfirst=True)
    report_target_type_enum.create(bind, checkfirst=True)
    report_reason_enum.create(bind, checkfirst=True)
    report_status_enum.create(bind, checkfirst=True)

    op.create_table(
        "users",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("email", sa.String(), nullable=False, unique=True, index=True),
        sa.Column("hashed_password", sa.String(), nullable=False),
        sa.Column("full_name", sa.String(), nullable=False),
        sa.Column("phone", sa.String(), nullable=True),
        sa.Column("avatar_url", sa.String(), nullable=True),
        sa.Column("bio", sa.Text(), nullable=True),
        sa.Column("is_admin", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("rating_avg", sa.Float(), nullable=False, server_default="0"),
        sa.Column("rating_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    op.create_table(
        "listings",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("owner_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("title", sa.String(), nullable=False),
        sa.Column("description", sa.Text(), nullable=False),
        sa.Column("category", category_enum, nullable=False),
        sa.Column("condition", condition_enum, nullable=False),
        sa.Column("status", listing_status_enum, nullable=False, server_default="available"),
        sa.Column("latitude", sa.Float(), nullable=False),
        sa.Column("longitude", sa.Float(), nullable=False),
        sa.Column("address_text", sa.String(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    op.create_table(
        "listing_images",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("listing_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("listings.id", ondelete="CASCADE"), nullable=False),
        sa.Column("image_url", sa.String(), nullable=False),
        sa.Column("position", sa.Integer(), nullable=False, server_default="0"),
    )

    op.create_table(
        "reservations",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("listing_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("listings.id", ondelete="CASCADE"), nullable=False),
        sa.Column("requester_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("status", reservation_status_enum, nullable=False, server_default="pending"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    op.create_table(
        "chats",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("reservation_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("reservations.id", ondelete="CASCADE"), nullable=False, unique=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    op.create_table(
        "chat_messages",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("chat_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("chats.id", ondelete="CASCADE"), nullable=False),
        sa.Column("sender_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    op.create_table(
        "exchanges",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("reservation_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("reservations.id", ondelete="CASCADE"), nullable=False, unique=True),
        sa.Column("qr_uuid", postgresql.UUID(as_uuid=True), nullable=False, unique=True),
        sa.Column("status", exchange_status_enum, nullable=False, server_default="pending"),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    op.create_table(
        "reviews",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("exchange_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("exchanges.id", ondelete="CASCADE"), nullable=False),
        sa.Column("reviewer_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("reviewee_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("rating", sa.Integer(), nullable=False),
        sa.Column("comment", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.UniqueConstraint("exchange_id", "reviewer_id", name="uq_review_per_exchange_reviewer"),
    )

    op.create_table(
        "reports",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("reporter_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("target_type", report_target_type_enum, nullable=False),
        sa.Column("target_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("reason", report_reason_enum, nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("status", report_status_enum, nullable=False, server_default="open"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )


def downgrade() -> None:
    op.drop_table("reports")
    op.drop_table("reviews")
    op.drop_table("exchanges")
    op.drop_table("chat_messages")
    op.drop_table("chats")
    op.drop_table("reservations")
    op.drop_table("listing_images")
    op.drop_table("listings")
    op.drop_table("users")

    bind = op.get_bind()
    report_status_enum.drop(bind, checkfirst=True)
    report_reason_enum.drop(bind, checkfirst=True)
    report_target_type_enum.drop(bind, checkfirst=True)
    exchange_status_enum.drop(bind, checkfirst=True)
    reservation_status_enum.drop(bind, checkfirst=True)
    listing_status_enum.drop(bind, checkfirst=True)
    condition_enum.drop(bind, checkfirst=True)
    category_enum.drop(bind, checkfirst=True)
