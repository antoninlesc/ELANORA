"""Invitation service layer - Business logic for invitation management."""

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.centralized_logging import get_logger
from app.crud.invitation import (
    create_invitation,
    get_invitation_by_code,
    get_invitation_by_id,
    get_invitations_by_email,
    get_invitations_by_sender,
    get_pending_invitations_by_email,
    update_invitation_status,
)
from app.crud.project import add_user_to_project, get_project_by_name, get_project_by_id
from app.crud.user import get_user_by_id
from app.model.enums import InvitationStatus
from app.model.invitation import Invitation
from app.schema.requests.invitation import InvitationSendRequest
from app.schema.responses.invitation import (
    InvitationListResponse,
    InvitationResponse,
    InvitationSendResponse,
    InvitationValidationResponse,
)
from app.service.email_service import EmailService

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
            project = await get_project_by_name(db, request.project_name)
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
                project_id=project.project_id,  # Utiliser l'ID du projet trouvé
                project_permission=request.project_permission,
                expires_in_days=request.expires_in_days,
            )

            language = request.language or "en"  # Default to English if not provided

            # Send invitation email
            email_sent = await self.email_service.send_invitation_email(
                email=str(request.receiver_email),
                invitation_code=raw_code,  # Now the parameter name is clear
                sender_name=f"{sender.first_name} {sender.last_name}",
                project_name=project_name,
                custom_message=request.message,
                language=language,
            )

            if email_sent:
                logger.info(
                    "Invitation sent successfully",
                    extra={
                        "sender_id": sender_id,
                        "receiver_email": str(request.receiver_email),
                        "invitation_id": invitation.invitation_id,
                        "project_id": project.project_id,  # Utiliser l'ID du projet trouvé
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
        invitation_code: str,
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
        """Mark an invitation as accepted and add user to project."""
        try:
            # Get invitation details first
            invitation = await get_invitation_by_id(db, invitation_id)
            if not invitation:
                logger.warning(
                    "Invitation not found",
                    extra={"invitation_id": invitation_id},
                )
                return False

            # Update invitation status
            success = await update_invitation_status(
                db=db,
                invitation_id=invitation_id,
                status=InvitationStatus.ACCEPTED,
                receiver_id=user_id,
            )

            if success:
                # Add user to project with the permission specified in the invitation
                try:
                    await add_user_to_project(
                        db=db,
                        user_id=user_id,
                        project_id=invitation.project_id,
                        permission=invitation.project_permission,
                    )
                    logger.info(
                        "User added to project via invitation",
                        extra={
                            "invitation_id": invitation_id,
                            "user_id": user_id,
                            "project_id": invitation.project_id,
                            "permission": invitation.project_permission,
                        },
                    )
                except Exception as project_error:
                    logger.error(
                        "Failed to add user to project",
                        extra={
                            "invitation_id": invitation_id,
                            "user_id": user_id,
                            "project_id": invitation.project_id,
                            "error": str(project_error),
                        },
                        exc_info=True,
                    )
                    # Note: invitation status is already updated,
                    # but user was not added to project
                    return False

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

        # Ensure project_permission is always lowercase to match the Pydantic enum
        project_permission = invitation.project_permission
        if isinstance(project_permission, str):
            project_permission = project_permission.lower()
        else:
            project_permission = project_permission.value.lower()

        return InvitationResponse(
            invitation_id=invitation.invitation_id,
            receiver_email=invitation.receiver_email,
            project_id=invitation.project_id,
            project_permission=project_permission,
            status=invitation.status,
            created_at=invitation.created_at,
            expires_at=invitation.expires_at,
            responded_at=invitation.responded_at,
            sender_username=sender_username,
            project_name=project_name,
        )
