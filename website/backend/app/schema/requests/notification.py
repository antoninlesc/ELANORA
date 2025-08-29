"""Request schemas for notification-related endpoints."""

from pydantic import BaseModel, Field


class NotificationCreateRequest(BaseModel):
    """Schema for creating a new notification."""

    user_id: int = Field(
        ..., description="The ID of the user receiving the notification"
    )
    title: str = Field(..., max_length=200, description="The title of the notification")
    message: str = Field(..., description="The message content of the notification")
    action_url: str | None = Field(
        None, max_length=500, description="Optional URL for the notification action"
    )


class NotificationUpdateRequest(BaseModel):
    """Schema for updating a notification."""

    is_read: bool = Field(..., description="Whether the notification has been read")


class NotificationPreferenceUpdateRequest(BaseModel):
    """Schema for updating notification preferences."""

    email_enabled: bool = Field(
        ..., description="Whether email notifications are enabled"
    )
