"""Request schemas for invitation operations."""

from typing import Optional
from pydantic import EmailStr
from app.schema.common.base import CustomBaseModel
from app.model.enums import ProjectPermission


class InvitationSendRequest(CustomBaseModel):
    """Schema for sending an invitation."""

    receiver_email: EmailStr
    project_id: int
    project_permission: ProjectPermission = ProjectPermission.READ
    expires_in_days: int = 7
    language: str = "en"
    message: Optional[str] = None


class InvitationAcceptRequest(CustomBaseModel):
    """Schema for accepting an invitation during registration."""

    invitation_id: str
