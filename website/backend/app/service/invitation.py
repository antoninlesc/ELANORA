"""Invitation service layer - Business logic for invitation management."""

from typing import List, Optional
from app.core.centralized_logging import get_logger
from app.crud.invitation import (
    create_invitation,
    get_invitation_by_id,
    get_invitation_by_code,
    get_invitations_by_email,
    get_pending_invitations_by_email,
    update_invitation_status,
    check_invitation_exists_and_valid,
    get_invitations_by_sender,
)
from app.crud.user import get_user_by_id
from app.crud.project import get_project_by_id
from app.model.invitation import Invitation
from app.model.enums import InvitationStatus, ProjectPermission
from app.service.email_service import EmailService
from app.schema.requests.invitation import InvitationSendRequest
from app.schema.responses.invitation import (
    InvitationResponse,
    InvitationSendResponse,
    InvitationListResponse,
    InvitationValidationResponse,
)
from sqlalchemy.ext.asyncio import AsyncSession

# Get logger for this module
logger = get_logger()


class InvitationService:
    """Service for managing invitations."""

    def __init__(self):
        self.email_service = EmailService()

    async def send_invitation(
        self,
        db: AsyncSession,
        sender_id: int,
        request: InvitationSendRequest,
    ) -> InvitationSendResponse:
        """Send an invitation email to a user."""
        try:
            # Get sender information
            sender = await get_user_by_id(db, sender_id)
            if not sender:
                return InvitationSendResponse(success=False, message="Sender not found")

            # Get project information (now required)
            project = await get_project_by_id(db, request.project_id)
            if not project:
                return InvitationSendResponse(
                    success=False, message="Project not found"
                )
            project_name = project.project_name

            # Check for existing invitations
            existing = await get_pending_invitations_by_email(
                db, str(request.receiver_email)
            )
            if existing:
                return InvitationSendResponse(
                    success=False,
                    message="An active invitation already exists for this email.",
                )

            # Create invitation in database
            invitation, raw_code = await create_invitation(
                db=db,
                sender_id=sender_id,
                receiver_email=str(request.receiver_email),
                project_id=request.project_id,
                project_permission=request.project_permission,
                expires_in_days=request.expires_in_days,
            )

            # Send invitation email
            email_sent = await self.email_service.send_invitation_email(
                email=str(request.receiver_email),
                invitation_code=raw_code,  # Now the parameter name is clear
                sender_name=f"{sender.first_name} {sender.last_name}",
                project_name=project_name,
                custom_message=request.message,
                language="en",  # Default to English for now
            )

            if email_sent:
                logger.info(
                    "Invitation sent successfully",
                    extra={
                        "sender_id": sender_id,
                        "receiver_email": str(request.receiver_email),
                        "invitation_id": invitation.invitation_id,
                        "project_id": request.project_id,
                    },
                )
                return InvitationSendResponse(
                    success=True,
                    message="Invitation sent successfully",
                    invitation_id=invitation.invitation_id,
                )
            else:
                return InvitationSendResponse(
                    success=False, message="Failed to send invitation email"
                )

        except Exception as e:
            logger.error(
                "Failed to send invitation",
                extra={
                    "sender_id": sender_id,
                    "receiver_email": str(request.receiver_email),
                    "error": str(e),
                },
                exc_info=True,
            )
            return InvitationSendResponse(
                success=False, message="Internal server error"
            )

    async def validate_invitation(
        self,
        db: AsyncSession,
        invitation_code: str,  # Now this is the raw code, not invitation_id
    ) -> InvitationValidationResponse:
        """Validate an invitation code."""
        try:
            # Find invitation by code
            invitation = await get_invitation_by_code(db, invitation_code)

            if not invitation:
                return InvitationValidationResponse(
                    valid=False, message="Invalid invitation code"
                )

            # Convert to response format
            invitation_response = await self._convert_to_response(db, invitation)

            return InvitationValidationResponse(
                valid=True,
                invitation=invitation_response,
                message="Invitation is valid",
            )

        except Exception as e:
            logger.error(
                "Failed to validate invitation",
                extra={
                    "invitation_code": invitation_code,
                    "error": str(e),
                },
                exc_info=True,
            )
            return InvitationValidationResponse(
                valid=False, message="Internal server error"
            )

    async def accept_invitation(
        self,
        db: AsyncSession,
        invitation_id: str,
        user_id: int,
    ) -> bool:
        """Mark an invitation as accepted."""
        try:
            success = await update_invitation_status(
                db=db,
                invitation_id=invitation_id,
                status=InvitationStatus.ACCEPTED,
                receiver_id=user_id,
            )

            if success:
                logger.info(
                    "Invitation accepted",
                    extra={
                        "invitation_id": invitation_id,
                        "user_id": user_id,
                    },
                )

            return success

        except Exception as e:
            logger.error(
                "Failed to accept invitation",
                extra={
                    "invitation_id": invitation_id,
                    "user_id": user_id,
                    "error": str(e),
                },
                exc_info=True,
            )
            return False

    async def get_user_invitations(
        self,
        db: AsyncSession,
        email: str,
    ) -> InvitationListResponse:
        """Get all invitations for a user by email."""
        try:
            invitations = await get_invitations_by_email(db, email)
            invitation_responses = []

            for invitation in invitations:
                response = await self._convert_to_response(db, invitation)
                invitation_responses.append(response)

            return InvitationListResponse(
                invitations=invitation_responses, total=len(invitation_responses)
            )

        except Exception as e:
            logger.error(
                "Failed to get user invitations",
                extra={
                    "email": email,
                    "error": str(e),
                },
                exc_info=True,
            )
            return InvitationListResponse(invitations=[], total=0)

    async def get_sent_invitations(
        self,
        db: AsyncSession,
        sender_id: int,
    ) -> InvitationListResponse:
        """Get all invitations sent by a user."""
        try:
            invitations = await get_invitations_by_sender(db, sender_id)
            invitation_responses = []

            for invitation in invitations:
                response = await self._convert_to_response(db, invitation)
                invitation_responses.append(response)

            return InvitationListResponse(
                invitations=invitation_responses, total=len(invitation_responses)
            )

        except Exception as e:
            logger.error(
                "Failed to get sent invitations",
                extra={
                    "sender_id": sender_id,
                    "error": str(e),
                },
                exc_info=True,
            )
            return InvitationListResponse(invitations=[], total=0)

    async def _convert_to_response(
        self,
        db: AsyncSession,
        invitation: Invitation,
    ) -> InvitationResponse:
        """Convert invitation model to response format."""
        # Get sender information
        sender = await get_user_by_id(db, invitation.sender)
        sender_username = sender.username if sender else None

        # Get project information
        project_name = None
        if invitation.project_id:
            project = await get_project_by_id(db, invitation.project_id)
            project_name = project.project_name if project else None

        return InvitationResponse(
            invitation_id=invitation.invitation_id,
            receiver_email=invitation.receiver_email,
            project_id=invitation.project_id,
            project_permission=invitation.project_permission,
            status=invitation.status,
            created_at=invitation.created_at,
            expires_at=invitation.expires_at,
            responded_at=invitation.responded_at,
            sender_username=sender_username,
            project_name=project_name,
        )
