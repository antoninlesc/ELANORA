"""Request schemas for invitation operations."""

from pydantic import EmailStr, Field

from app.model.enums import ProjectPermission
from app.schema.common.base import CustomBaseModel


class InvitationSendRequest(CustomBaseModel):
    """Schema for sending an invitation."""

    receiver_email: EmailStr | None = None
    project_name: str
    project_permission: ProjectPermission = ProjectPermission.READ
    expires_in_days: int = 7
    language: str = "en"
    message: str | None = None
    send_email: bool = Field(
        default=True, description="Whether to send email or just generate code"
    )


class InvitationAcceptRequest(CustomBaseModel):
    """Schema for accepting an invitation during registration."""

    invitation_id: str
