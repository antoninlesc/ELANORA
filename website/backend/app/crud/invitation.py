"""Invitation CRUD operations - Pure database access layer."""

import secrets
import uuid
from datetime import datetime, timedelta

from passlib.context import CryptContext
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.model.enums import InvitationStatus, ProjectPermission
from app.model.invitation import Invitation

# Password context for hashing codes
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


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
    invitation_id = str(uuid.uuid4())
    expires_at = datetime.now() + timedelta(days=expires_in_days)

    # Generate a secure random code (independent of invitation_id)
    raw_code = secrets.token_urlsafe(32)  # 32 bytes = 256 bits of entropy
    hashed_code = pwd_context.hash(raw_code)

    invitation = Invitation(
        invitation_id=invitation_id,
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
    db: AsyncSession, invitation_id: str
) -> Invitation | None:
    """Retrieve an invitation by ID."""
    result = await db.execute(
        select(Invitation).filter(Invitation.invitation_id == invitation_id)
    )
    return result.scalar_one_or_none()


async def get_invitations_by_email(db: AsyncSession, email: str) -> list[Invitation]:
    """Get all invitations for a specific email."""
    result = await db.execute(
        select(Invitation).filter(Invitation.receiver_email == email)
    )
    return list(result.scalars().all())


async def get_pending_invitations_by_email(
    db: AsyncSession, email: str
) -> list[Invitation]:
    """Get pending invitations for a specific email."""
    result = await db.execute(
        select(Invitation)
        .filter(Invitation.receiver_email == email)
        .filter(Invitation.status == InvitationStatus.PENDING)
        .filter(Invitation.expires_at > datetime.now())
    )
    return list(result.scalars().all())


async def update_invitation_status(
    db: AsyncSession,
    invitation_id: str,
    status: InvitationStatus,
    receiver_id: int | None = None,
) -> bool:
    """Update invitation status and optionally set receiver_id."""
    invitation = await get_invitation_by_id(db, invitation_id)
    if not invitation:
        return False

    invitation.status = status
    invitation.responded_at = datetime.now()
    if receiver_id:
        invitation.receiver = receiver_id

    await db.commit()
    return True


async def check_invitation_exists_and_valid(
    db: AsyncSession, invitation_id: str
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
    result = await db.execute(select(Invitation).filter(Invitation.sender == sender_id))
    return list(result.scalars().all())


async def expire_old_invitations(db: AsyncSession) -> int:
    """Mark expired invitations as expired and return count."""
    result = await db.execute(
        select(Invitation)
        .filter(Invitation.status == InvitationStatus.PENDING)
        .filter(Invitation.expires_at <= datetime.now())
    )

    expired_invitations = list(result.scalars().all())
    count = 0

    for invitation in expired_invitations:
        invitation.status = InvitationStatus.EXPIRED
        count += 1

    if count > 0:
        await db.commit()

    return count


async def verify_invitation_code(
    db: AsyncSession, invitation_id: str, raw_code: str
) -> bool:
    """Verify if the provided code matches the invitation's hashed code."""
    invitation = await get_invitation_by_id(db, invitation_id)
    if not invitation:
        return False

    return pwd_context.verify(raw_code, invitation.hashed_code)


async def get_invitation_by_code(db: AsyncSession, raw_code: str) -> Invitation | None:
    """Retrieve an invitation by verifying the raw code against hashed codes."""
    # Get all pending invitations
    result = await db.execute(
        select(Invitation)
        .filter(Invitation.status == InvitationStatus.PENDING)
        .filter(Invitation.expires_at > datetime.now())
    )
    invitations = list(result.scalars().all())

    # Check each invitation's hashed code against the provided raw code
    for invitation in invitations:
        if pwd_context.verify(raw_code, invitation.hashed_code):
            return invitation

    return None
