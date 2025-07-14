"""Response schemas for invitation operations."""

from datetime import datetime
from typing import Optional
from app.schema.common.base import CustomBaseModel
from app.model.enums import InvitationStatus, ProjectPermission


class InvitationResponse(CustomBaseModel):
    """Schema for invitation data."""

    invitation_id: str
    receiver_email: str
    project_id: int
    project_permission: ProjectPermission
    status: InvitationStatus
    created_at: datetime
    expires_at: datetime
    responded_at: Optional[datetime] = None
    sender_username: Optional[str] = None
    project_name: Optional[str] = None


class InvitationSendResponse(CustomBaseModel):
    """Schema for invitation send response."""

    success: bool
    message: str
    invitation_id: Optional[str] = None


class InvitationListResponse(CustomBaseModel):
    """Schema for invitation list response."""

    invitations: list[InvitationResponse]
    total: int


class InvitationValidationResponse(CustomBaseModel):
    """Schema for invitation validation response."""

    valid: bool
    invitation: Optional[InvitationResponse] = None
    message: str
