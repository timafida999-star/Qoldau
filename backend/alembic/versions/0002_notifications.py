"""notifications

Revision ID: 0002
Revises: 0001
Create Date: 2026-07-20

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "0002"
down_revision = "0001"
branch_labels = None
depends_on = None

notification_type_enum = postgresql.ENUM(
    "reservation_requested",
    "reservation_accepted",
    "reservation_declined",
    "reservation_cancelled",
    "message_received",
    "exchange_completed",
    "review_received",
    name="notificationtype",
    create_type=False,
)


def upgrade() -> None:
    notification_type_enum.create(op.get_bind(), checkfirst=True)

    op.create_table(
        "notifications",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "user_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("users.id", ondelete="CASCADE"),
            nullable=False,
            index=True,
        ),
        sa.Column("type", notification_type_enum, nullable=False),
        sa.Column("actor_name", sa.String(), nullable=True),
        sa.Column("entity_title", sa.String(), nullable=True),
        sa.Column("link", sa.String(), nullable=True),
        sa.Column("is_read", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )


def downgrade() -> None:
    op.drop_table("notifications")
    notification_type_enum.drop(op.get_bind(), checkfirst=True)
