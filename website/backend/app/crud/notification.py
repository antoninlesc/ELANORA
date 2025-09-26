"""Notification CRUD operations - Pure database access layer."""

from sqlalchemy import desc, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.model.notification import Notification
from app.model.notification_preference import NotificationPreference
from app.schema.requests.notification import (
    NotificationCreateRequest,
    NotificationPreferenceUpdateRequest,
)
from app.utils.database import DatabaseUtils


async def get_notifications_by_user_id(
    db: AsyncSession, user_id: int, skip: int = 0, limit: int = 100
) -> list[Notification]:
    """Retrieve notifications for a specific user with pagination."""
    filters = {"user_id": user_id}
    order_by = [desc(Notification.created_at)]
    return await DatabaseUtils.get_by_filter(
        db, Notification, filters, order_by=order_by, offset=skip, limit=limit
    )


async def get_unread_notifications_by_user_id(
    db: AsyncSession, user_id: int, skip: int = 0, limit: int = 100
) -> list[Notification]:
    """Retrieve unread notifications for a specific user with pagination."""
    conditions = [
        Notification.user_id == user_id,
        Notification.is_read.is_(False),
    ]
    order_by = [desc(Notification.created_at)]
    return await DatabaseUtils.get_by_conditions(
        db,
        Notification,
        conditions=conditions,
        order_by=order_by,
        offset=skip,
        limit=limit,
    )


async def get_notification_by_id(
    db: AsyncSession, notification_id: int
) -> Notification | None:
    """Retrieve a notification by its ID."""
    return await DatabaseUtils.get_by_id(
        db, Notification, "notification_id", notification_id
    )


async def create_notification(
    db: AsyncSession, notification_data: NotificationCreateRequest
) -> Notification:
    """Create a new notification."""
    notification = Notification(
        user_id=notification_data.user_id,
        title=notification_data.title,
        message=notification_data.message,
        action_url=notification_data.action_url,
    )
    db.add(notification)
    await db.flush()
    await db.refresh(notification)
    return notification


async def mark_notification_as_read(db: AsyncSession, notification_id: int) -> bool:
    """Mark a notification as read. Returns True if updated."""
    filters = {"notification_id": notification_id}
    update_fields = {"is_read": True}
    updated_count = await DatabaseUtils.update_by_filter(
        db, Notification, filters, update_fields
    )
    return updated_count > 0


async def mark_all_notifications_as_read(db: AsyncSession, user_id: int) -> int:
    """Mark all notifications for a user as read. Returns the number of updated notifications."""
    conditions = [
        Notification.user_id == user_id,
        Notification.is_read.is_(False),
    ]
    update_fields = {"is_read": True}
    # Use the enhanced update method for bulk updates with conditions
    from sqlalchemy import update

    stmt = (
        update(Notification)
        .where(Notification.user_id == user_id, Notification.is_read.is_(False))
        .values(is_read=True)
    )
    result = await db.execute(stmt)
    return result.rowcount


async def delete_notification(db: AsyncSession, notification_id: int) -> bool:
    """Delete a notification by its ID."""
    deleted_count = await DatabaseUtils.delete_by_filter(
        db, Notification, notification_id=notification_id
    )
    return deleted_count > 0


async def get_notification_stats(db: AsyncSession, user_id: int) -> dict[str, int]:
    """Get notification statistics for a user."""
    # Get total count
    total_stmt = (
        select(func.count())
        .select_from(Notification)
        .where(Notification.user_id == user_id)
    )
    total_result = await db.execute(total_stmt)
    total_count = total_result.scalar() or 0

    # Get unread count
    unread_stmt = (
        select(func.count())
        .select_from(Notification)
        .where(Notification.user_id == user_id, ~Notification.is_read)
    )
    unread_result = await db.execute(unread_stmt)
    unread_count = unread_result.scalar() or 0

    return {
        "total_notifications": total_count,
        "unread_notifications": unread_count,
        "read_notifications": total_count - unread_count,
    }


# Notification Preference CRUD operations


async def get_notification_preference_by_user_id(
    db: AsyncSession, user_id: int
) -> NotificationPreference | None:
    """Retrieve notification preferences for a specific user."""
    filters = {"user_id": user_id}
    return await DatabaseUtils.get_one_or_none(
        db, NotificationPreference, filters=filters
    )


async def create_notification_preference(
    db: AsyncSession, user_id: int, email_enabled: bool = True
) -> NotificationPreference:
    """Create notification preferences for a user."""
    preference = NotificationPreference(
        user_id=user_id,
        email_enabled=email_enabled,
    )
    db.add(preference)
    await db.flush()
    await db.refresh(preference)
    return preference


async def update_notification_preference(
    db: AsyncSession, user_id: int, preference_data: NotificationPreferenceUpdateRequest
) -> NotificationPreference | None:
    """Update notification preferences for a user."""
    preference = await get_notification_preference_by_user_id(db, user_id)
    if preference:
        preference.email_enabled = preference_data.email_enabled
        return preference

    # Create preference if it doesn't exist
    return await create_notification_preference(
        db, user_id, preference_data.email_enabled
    )


async def get_or_create_notification_preference(
    db: AsyncSession, user_id: int
) -> NotificationPreference:
    """Get or create notification preferences for a user."""
    preference = await get_notification_preference_by_user_id(db, user_id)
    if not preference:
        preference = await create_notification_preference(db, user_id)
    return preference
