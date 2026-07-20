import uuid
from typing import Optional

from sqlalchemy.orm import Session
from sqlalchemy.sql import func

from app.models.notification import Notification, NotificationType


def notify(
    db: Session,
    *,
    user_id: uuid.UUID,
    type: NotificationType,
    actor_name: Optional[str] = None,
    entity_title: Optional[str] = None,
    link: Optional[str] = None,
) -> Notification:
    """Queue a notification for a recipient. The caller commits."""
    notification = Notification(
        user_id=user_id,
        type=type,
        actor_name=actor_name,
        entity_title=entity_title,
        link=link,
    )
    db.add(notification)
    return notification


def notify_new_message(
    db: Session,
    *,
    user_id: uuid.UUID,
    actor_name: str,
    entity_title: Optional[str],
    link: str,
) -> None:
    """Notify about a chat message, collapsing bursts into one unread entry.

    A busy conversation should show a single "new message" item rather than one
    per message, so an existing unread entry for the same chat is refreshed.
    """
    existing = (
        db.query(Notification)
        .filter(
            Notification.user_id == user_id,
            Notification.type == NotificationType.MESSAGE_RECEIVED,
            Notification.link == link,
            Notification.is_read.is_(False),
        )
        .first()
    )

    if existing:
        existing.created_at = func.now()
        existing.actor_name = actor_name
        return

    notify(
        db,
        user_id=user_id,
        type=NotificationType.MESSAGE_RECEIVED,
        actor_name=actor_name,
        entity_title=entity_title,
        link=link,
    )
