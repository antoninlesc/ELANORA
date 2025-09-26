"""Notification Preference CRUD operations - Pure database access layer."""

from sqlalchemy.ext.asyncio import AsyncSession

from app.model.notification_preference import NotificationPreference
from app.schema.requests.notification import NotificationPreferenceUpdateRequest
from app.utils.database import DatabaseUtils


async def get_notification_preference_by_user_id(
    db: AsyncSession, user_id: int
) -> NotificationPreference | None:
    """Retrieve notification preferences for a specific user."""
    filters = {"user_id": user_id}
    return await DatabaseUtils.get_one_or_none(
        db, NotificationPreference, filters=filters
    )


async def get_notification_preference_by_id(
    db: AsyncSession, preference_id: int
) -> NotificationPreference | None:
    """Retrieve a notification preference by its ID."""
    return await DatabaseUtils.get_by_id(
        db, NotificationPreference, "preference_id", preference_id
    )


async def create_notification_preference(
    db: AsyncSession, user_id: int, email_enabled: bool = True
) -> NotificationPreference:
    """Create notification preferences for a user."""
    preference = NotificationPreference(
        user_id=user_id,
        email_enabled=email_enabled,
    )
    return await DatabaseUtils.create(db, preference)


async def update_notification_preference(
    db: AsyncSession, user_id: int, preference_data: NotificationPreferenceUpdateRequest
) -> NotificationPreference | None:
    """Update notification preferences for a user."""
    preference = await get_notification_preference_by_user_id(db, user_id)
    if not preference:
        return None

    update_fields = {"email_enabled": preference_data.email_enabled}
    await DatabaseUtils.update_by_filter(
        db, NotificationPreference, {"user_id": user_id}, update_fields
    )

    # Refresh the preference to get updated data
    return await get_notification_preference_by_user_id(db, user_id)


async def delete_notification_preference(db: AsyncSession, user_id: int) -> bool:
    """Delete notification preferences for a user."""
    deleted_count = await DatabaseUtils.delete_by_filter(
        db, NotificationPreference, user_id=user_id
    )
    return deleted_count > 0


async def get_or_create_notification_preference(
    db: AsyncSession, user_id: int
) -> NotificationPreference:
    """Get existing notification preference or create a new one with defaults."""
    preference = await get_notification_preference_by_user_id(db, user_id)
    if preference:
        return preference

    return await create_notification_preference(db, user_id)
