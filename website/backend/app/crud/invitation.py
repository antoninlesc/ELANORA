"""Invitation CRUD operations - Pure database access layer."""

import secrets
from datetime import datetime, timedelta

from passlib.context import CryptContext
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.centralized_logging import get_logger
from app.model.invitation import Invitation, InvitationStatus
from app.model.user_to_project import ProjectPermission

# Password context for hashing codes
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

from app.utils.database import DatabaseUtils

logger = get_logger()


async def delete_project_invitations(db: AsyncSession, project_id: int):
    logger.info(f"Deleting invitations for project_id={project_id}")
    try:
        count = await DatabaseUtils.delete_by_conditions(
            db, Invitation, [Invitation.project_id == project_id]
        )
        logger.info(f"Deleted {count} invitations for project_id={project_id}")
    except Exception as e:
        logger.error(f"Failed to delete invitations for project_id={project_id}: {e}")


async def create_invitation(
    db: AsyncSession,
    sender_id: int,
    receiver_email: str,
    project_id: int,
    project_permission: ProjectPermission = ProjectPermission.READ,
    expires_in_days: int = 7,
) -> tuple[Invitation, str]:
    """Create a new invitation in the database.

    Returns:
        Tuple[Invitation, str]: The created invitation and the raw code for email

    """
    expires_at = datetime.now() + timedelta(days=expires_in_days)

    # Generate a secure random code (independent of invitation_id)
    raw_code = secrets.token_urlsafe(32)  # 32 bytes = 256 bits of entropy
    hashed_code = pwd_context.hash(raw_code)

    invitation = Invitation(
        sender=sender_id,
        receiver_email=receiver_email,
        project_id=project_id,
        project_permission=project_permission,
        status=InvitationStatus.PENDING,
        expires_at=expires_at,
        hashed_code=hashed_code,
    )

    db.add(invitation)
    await db.commit()
    await db.refresh(invitation)
    return invitation, raw_code


async def get_invitation_by_id(
    db: AsyncSession, invitation_id: int
) -> Invitation | None:
    """Retrieve an invitation by ID."""
    return await DatabaseUtils.get_by_id(db, Invitation, "invitation_id", invitation_id)


async def get_invitations_by_email(db: AsyncSession, email: str) -> list[Invitation]:
    """Get all invitations for a specific email."""
    filters = {"receiver_email": email}
    return await DatabaseUtils.get_by_filter(db, Invitation, filters)


async def get_pending_invitations_by_email(
    db: AsyncSession, email: str
) -> list[Invitation]:
    """Get pending invitations for a specific email."""
    conditions = [
        Invitation.receiver_email == email,
        Invitation.status == InvitationStatus.PENDING,
        Invitation.expires_at > datetime.now(),
    ]
    return await DatabaseUtils.get_by_conditions(db, Invitation, conditions=conditions)


async def update_invitation_status(
    db: AsyncSession,
    invitation_id: int,
    status: InvitationStatus,
    receiver_id: int | None = None,
) -> bool:
    """Update invitation status and optionally set receiver_id."""
    filters = {"invitation_id": invitation_id}
    update_fields = {
        "status": status,
        "responded_at": datetime.now(),
    }
    if receiver_id:
        update_fields["receiver"] = receiver_id

    updated_count = await DatabaseUtils.update_by_filter(
        db, Invitation, filters, update_fields
    )
    return updated_count > 0


async def check_invitation_exists_and_valid(
    db: AsyncSession, invitation_id: int
) -> bool:
    """Check if invitation exists and is still valid."""
    invitation = await get_invitation_by_id(db, invitation_id)
    return (
        invitation is not None
        and invitation.status == InvitationStatus.PENDING
        and invitation.expires_at > datetime.now()
    )


async def get_invitations_by_sender(
    db: AsyncSession, sender_id: int
) -> list[Invitation]:
    """Get all invitations sent by a specific user."""
    filters = {"sender": sender_id}
    return await DatabaseUtils.get_by_filter(db, Invitation, filters)


async def get_invitations_by_project(
    db: AsyncSession, project_id: int
) -> list[Invitation]:
    """Get all invitations for a specific project."""
    filters = {"project_id": project_id}
    return await DatabaseUtils.get_by_filter(db, Invitation, filters)


async def expire_old_invitations(db: AsyncSession) -> int:
    """Mark expired invitations as expired and return count."""
    from sqlalchemy import update

    stmt = (
        update(Invitation)
        .where(Invitation.status == InvitationStatus.PENDING)
        .where(Invitation.expires_at <= datetime.now())
        .values(status=InvitationStatus.EXPIRED)
    )
    result = await db.execute(stmt)
    return result.rowcount


async def verify_invitation_code(
    db: AsyncSession, invitation_id: int, raw_code: str
) -> bool:
    """Verify if the provided code matches the invitation's hashed code."""
    invitation = await get_invitation_by_id(db, invitation_id)
    if not invitation:
        return False

    return pwd_context.verify(raw_code, invitation.hashed_code)


async def get_invitation_by_code(db: AsyncSession, raw_code: str) -> Invitation | None:
    """Retrieve an invitation by verifying the raw code against hashed codes."""
    # Get all pending invitations using modern SQLAlchemy syntax
    stmt = (
        select(Invitation)
        .where(Invitation.status == InvitationStatus.PENDING)
        .where(Invitation.expires_at > datetime.now())
    )
    result = await db.execute(stmt)
    invitations = list(result.scalars().all())

    # Check each invitation's hashed code against the provided raw code
    for invitation in invitations:
        if pwd_context.verify(raw_code, invitation.hashed_code):
            return invitation

    return None
