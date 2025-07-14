"""Invitation API endpoints."""

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.dependency.database import get_db_dep
from app.dependency.user import get_user_dep, get_admin_dep
from app.model.user import User, UserRole
from app.schema.requests.invitation import InvitationSendRequest
from app.schema.responses.invitation import (
    InvitationSendResponse,
    InvitationListResponse,
    InvitationValidationResponse,
)
from app.service.invitation import InvitationService

router = APIRouter()


@router.post("/send", response_model=InvitationSendResponse)
async def send_invitation(
    request: InvitationSendRequest,
    background_tasks: BackgroundTasks,
    user: User = get_user_dep,
    db: AsyncSession = get_db_dep,
) -> InvitationSendResponse:
    """Send an invitation to a specific project (Admin only)."""
    # Check if user is admin
    if user.role != UserRole.ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only administrators can send invitations",
        )

    invitation_service = InvitationService()
    return await invitation_service.send_invitation(
        db=db,
        sender_id=user.user_id,
        request=request,
    )


@router.get("/validate/{invitation_id}", response_model=InvitationValidationResponse)
async def validate_invitation(
    invitation_id: str,
    db: AsyncSession = get_db_dep,
) -> InvitationValidationResponse:
    """Validate an invitation code (Public endpoint for registration)."""
    invitation_service = InvitationService()
    return await invitation_service.validate_invitation(
        db=db,
        invitation_id=invitation_id,
    )


@router.get("/sent", response_model=InvitationListResponse)
async def get_sent_invitations(
    user: User = get_user_dep,
    db: AsyncSession = get_db_dep,
) -> InvitationListResponse:
    """Get invitations sent by the current user (Admin only)."""
    # Check if user is admin
    if user.role != UserRole.ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only administrators can view sent invitations",
        )

    invitation_service = InvitationService()
    return await invitation_service.get_sent_invitations(
        db=db,
        sender_id=user.user_id,
    )


@router.get("/received/{email}", response_model=InvitationListResponse)
async def get_received_invitations(
    email: str,
    user: User = get_user_dep,
    db: AsyncSession = get_db_dep,
) -> InvitationListResponse:
    """Get invitations received by email (Admin only or own email)."""
    # Check if user is admin or requesting their own invitations
    if user.role != UserRole.ADMIN and user.email != email:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You can only view your own invitations",
        )

    invitation_service = InvitationService()
    return await invitation_service.get_user_invitations(
        db=db,
        email=email,
    )
