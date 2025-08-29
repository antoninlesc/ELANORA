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
    stmt = (
        select(Notification)
        .where(Notification.user_id == user_id)
        .order_by(desc(Notification.created_at))
        .offset(skip)
        .limit(limit)
    )
    result = await db.execute(stmt)
    return list(result.scalars().all())


async def get_unread_notifications_by_user_id(
    db: AsyncSession, user_id: int, skip: int = 0, limit: int = 100
) -> list[Notification]:
    """Retrieve unread notifications for a specific user with pagination."""
    stmt = (
        select(Notification)
        .where(Notification.user_id == user_id, ~Notification.is_read)
        .order_by(desc(Notification.created_at))
        .offset(skip)
        .limit(limit)
    )
    result = await db.execute(stmt)
    return list(result.scalars().all())


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


async def mark_notification_as_read(
    db: AsyncSession, notification_id: int
) -> Notification | None:
    """Mark a notification as read."""
    notification = await get_notification_by_id(db, notification_id)
    if notification:
        notification.is_read = True
        await db.flush()
        await db.refresh(notification)
    return notification


async def mark_all_notifications_as_read(db: AsyncSession, user_id: int) -> int:
    """Mark all notifications for a user as read. Returns the number of updated notifications."""
    stmt = select(Notification).where(
        Notification.user_id == user_id, ~Notification.is_read
    )
    result = await db.execute(stmt)
    notifications = list(result.scalars().all())

    for notification in notifications:
        notification.is_read = True

    await db.flush()
    return len(notifications)


async def delete_notification(db: AsyncSession, notification_id: int) -> bool:
    """Delete a notification by its ID."""
    notification = await get_notification_by_id(db, notification_id)
    if notification:
        await db.delete(notification)
        await db.flush()
        return True
    return False


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
    return await DatabaseUtils.get_one_by_filter(db, NotificationPreference, filters)


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
