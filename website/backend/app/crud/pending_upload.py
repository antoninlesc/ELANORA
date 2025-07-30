from sqlalchemy.ext.asyncio import AsyncSession

from app.core.centralized_logging import get_logger
from sqlalchemy.future import select
from sqlalchemy.sql import func
from app.model.association import ConflictOfElanFile
from app.model.pending_upload import PendingUpload
from app.model.elan_file import ElanFile
from app.model.association import ConflictOfElanFile, ElanFileToProject
from app.model.enums import Type, Severity, Status
from typing import List, Optional
from app.utils.database import DatabaseUtils

logger = get_logger()


async def save_pending_upload(
    db: AsyncSession, project_id: int, branch_name: str, upload_data: dict
) -> None:
    """Save pending upload info - no conflicts stored."""
    # Create pending upload record
    pending_upload = PendingUpload(
        branch_name=branch_name,
        upload_type=Type.PENDING_UPLOAD,  # New enum value
        upload_description=build_pending_description(upload_data),
        severity=Severity.LOW,  # Informational only
        status=Status.PENDING_ADMIN_APPROVAL,  # New enum value
        detected_at=func.now(),
        git_details=upload_data,
        project_id=project_id,
    )
    db.add(pending_upload)
    await db.commit()
    logger.info(f"Saved pending upload for branch: {branch_name}")


async def get_pending_uploads(db: AsyncSession, project_id: int) -> list[dict]:
    """Get all pending uploads for admin dashboard."""
    filter = {"project_id": project_id}
    return await DatabaseUtils.get_by_filter(db, PendingUpload, filter)


def build_pending_description(upload_data: dict) -> str:
    """Build description for pending upload."""
    new_count = len(upload_data.get("new_files", []))
    modified_count = len(upload_data.get("modified_files", []))
    deleted_count = len(upload_data.get("deleted_files", []))

    parts = []
    if new_count > 0:
        parts.append(f"{new_count} new")
    if modified_count > 0:
        parts.append(f"{modified_count} modified")
    if deleted_count > 0:
        parts.append(f"{deleted_count} deleted")

    files_desc = ", ".join(parts) if parts else "no changes"
    return f"Pending upload: {files_desc} files"


async def mark_upload_processed(db: AsyncSession, branch_name: str) -> None:
    """Mark upload as processed after merge."""
    stmt = select(PendingUpload).where(
        PendingUpload.branch_name == branch_name,
        PendingUpload.status == Status.PENDING_ADMIN_APPROVAL,
    )
    result = await db.execute(stmt)
    upload_record = result.scalar_one_or_none()

    if upload_record:
        upload_record.status = Status.RESOLVED
        upload_record.resolved_at = func.now()
        await db.commit()
