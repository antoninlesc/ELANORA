"""Request schemas for invitation operations."""

from pydantic import EmailStr

from app.model.user_to_project import ProjectPermission
from app.schema.common.base import CustomBaseModel


class InvitationSendRequest(CustomBaseModel):
    """Schema for sending an invitation by email."""

    receiver_email: EmailStr
    project_name: str
    project_permission: ProjectPermission = ProjectPermission.READ
    expires_in_days: int = 7
    language: str = "en"
    message: str | None = None


class InvitationAcceptRequest(CustomBaseModel):
    """Schema for accepting an invitation during registration."""

    invitation_id: str
