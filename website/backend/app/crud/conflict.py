from sqlalchemy.ext.asyncio import AsyncSession

from app.core.centralized_logging import get_logger
from sqlalchemy.future import select
from sqlalchemy.sql import func
from app.model.conflict import Conflict
from app.model.elan_file import ElanFile
from app.model.association import ConflictOfElanFile, ElanFileToProject
from app.model.enums import ConflictType, ConflictSeverity, ConflictStatus
from typing import List, Optional
from app.utils.database import DatabaseUtils

logger = get_logger()


async def delete_project_conflicts(db: AsyncSession, project_id: int):
    logger.info(f"Deleting conflicts for project_id={project_id}")
    try:
        count = (
            await db.execute(
                Conflict.__table__.count().where(Conflict.project_id == project_id)
            )
        ).scalar_one()
        logger.info(f"Found {count} conflicts to delete for project_id={project_id}")
        await DatabaseUtils.delete_by_filter(db, Conflict, project_id=project_id)
        logger.info("Conflicts deleted successfully")
    except Exception as e:
        logger.error(f"Failed to delete conflicts for project_id={project_id}: {e}")


async def delete_conflict_of_elan_file(db: AsyncSession, elan_id: int):
    logger.info(f"Deleting ConflictOfElanFile for elan_id={elan_id}")
    try:
        count = (
            await db.execute(
                ConflictOfElanFile.__table__.count().where(
                    ConflictOfElanFile.elan_id == elan_id
                )
            )
        ).scalar_one()
        logger.info(
            f"Found {count} ConflictOfElanFile rows to delete for elan_id={elan_id}"
        )
        await DatabaseUtils.delete_by_filter(db, ConflictOfElanFile, elan_id=elan_id)
        logger.info("ConflictOfElanFile deleted successfully")
    except Exception as e:
        logger.error(f"Failed to delete ConflictOfElanFile for elan_id={elan_id}: {e}")


async def save_git_conflicts(
    db: AsyncSession, project_id: int, branch_name: str, conflicts: List[dict]
) -> None:
    """Save git conflicts using association with ELAN files."""
    for conflict_data in conflicts:
        logger.info(
            f"Processing conflict for project_id={project_id}, branch_name={branch_name}, "
            f"filename={conflict_data['filename']}"
        )
        filename = conflict_data["filename"]
        if filename.startswith("elan_files/"):
            filename = filename[len("elan_files/") :]

        # Find the ELAN file by filename and project through association
        elan_file_stmt = (
            select(ElanFile)
            .join(ElanFileToProject, ElanFile.elan_id == ElanFileToProject.elan_id)
            .where(
                ElanFileToProject.project_id == project_id,
                ElanFile.filename == filename,
            )
        )
        elan_file_result = await db.execute(elan_file_stmt)
        elan_file = elan_file_result.scalar_one_or_none()
        logger.info(f"Found ELAN file: {elan_file.filename if elan_file else 'None'}")

        if not elan_file:
            # Log or handle missing ELAN file
            continue

        # Check if conflict already exists through association
        existing_conflict_stmt = (
            select(Conflict)
            .join(
                ConflictOfElanFile,
                Conflict.conflict_id == ConflictOfElanFile.conflict_id,
            )
            .where(
                ConflictOfElanFile.elan_id == elan_file.elan_id,
                Conflict.branch_name == branch_name,
                Conflict.status.in_(
                    [ConflictStatus.DETECTED, ConflictStatus.IN_PROGRESS]
                ),
                Conflict.conflict_type.in_(
                    [
                        ConflictType.GIT_MERGE_CONFLICT,
                        ConflictType.GIT_CONTENT_CONFLICT,
                        ConflictType.GIT_FILE_CONFLICT,
                    ]
                ),
            )
        )
        existing_result = await db.execute(existing_conflict_stmt)
        existing_conflict = existing_result.scalar_one_or_none()

        if existing_conflict:
            # Update existing conflict
            existing_conflict.conflict_description = build_conflict_description(
                conflict_data
            )
            existing_conflict.git_details = conflict_data
            existing_conflict.detected_at = func.now()
            existing_conflict.status = ConflictStatus.DETECTED
        else:
            # Map conflict type
            git_conflict_type = ConflictType.GIT_MERGE_CONFLICT
            if conflict_data["type"] == "content_conflict":
                git_conflict_type = ConflictType.GIT_CONTENT_CONFLICT
            elif conflict_data["type"] == "file_conflict":
                git_conflict_type = ConflictType.GIT_FILE_CONFLICT

            # Create new conflict
            new_conflict = Conflict(
                branch_name=branch_name,
                conflict_type=git_conflict_type,
                conflict_description=build_conflict_description(conflict_data),
                severity=ConflictSeverity.MEDIUM,
                status=ConflictStatus.DETECTED,
                detected_at=func.now(),
                git_details=conflict_data,
                project_id=project_id,
            )
            logger.info(f"Creating new conflict: {new_conflict}")
            db.add(new_conflict)
            await db.flush()  # Get the auto-generated ID

            # Create association with ELAN file
            conflict_association = ConflictOfElanFile(
                conflict_id=new_conflict.conflict_id,  # Auto-generated ID
                elan_id=elan_file.elan_id,
            )
            db.add(conflict_association)

    await db.commit()


def build_conflict_description(conflict_data: dict) -> str:
    """Build a descriptive conflict message from conflict data."""
    filename = conflict_data.get("filename", "unknown")
    conflict_type = conflict_data.get("type", "merge_conflict")
    details = conflict_data.get("details", {})

    if conflict_type == "selective_merge_conflict":
        if isinstance(details, dict):
            change_type = details.get("change_type", "modified")
            isolated_branch = details.get("isolated_in_branch")
            description = (
                f"File '{filename}' - {change_type} in branch, isolated for review"
            )
            if isolated_branch:
                description += f" (branch: {isolated_branch})"
            return description

    elif conflict_type == "content_conflict":
        if isinstance(details, dict):
            markers = details.get("conflict_markers_count", 0)
            return f"Content conflict in '{filename}' with {markers} conflict markers"

    elif conflict_type == "merge_conflict":
        if isinstance(details, dict):
            change_type = details.get("change_type", "modified")
            isolated_branch = details.get("isolated_in_branch")
            if isolated_branch:
                return f"Merge conflict in '{filename}' - {change_type}, isolated in branch '{isolated_branch}'"
            else:
                return f"Merge conflict in '{filename}' - {change_type}"

    # Default description
    return f"Conflict in file '{filename}'"


async def get_git_conflicts_for_branch(
    db: AsyncSession,
    project_id: int,
    branch_name: str,
    status: Optional[ConflictStatus] = None,
) -> List[Conflict]:
    """Get git conflicts for a specific branch via ELAN file associations."""
    stmt = (
        select(Conflict)
        .join(
            ConflictOfElanFile, Conflict.conflict_id == ConflictOfElanFile.conflict_id
        )
        .join(ElanFile, ConflictOfElanFile.elan_id == ElanFile.elan_id)
        .join(ElanFileToProject, ElanFile.elan_id == ElanFileToProject.elan_id)
        .where(
            ElanFileToProject.project_id == project_id,
            Conflict.branch_name == branch_name,
            Conflict.conflict_type.in_(
                [
                    ConflictType.GIT_MERGE_CONFLICT,
                    ConflictType.GIT_CONTENT_CONFLICT,
                    ConflictType.GIT_FILE_CONFLICT,
                ]
            ),
        )
    )

    if status:
        stmt = stmt.where(Conflict.status == status)

    result = await db.execute(stmt)
    return result.scalars().all()


async def get_conflicts_with_file_info(
    db: AsyncSession,
    project_id: int,
    branch_name: str,
    status: Optional[ConflictStatus] = None,
) -> List[dict]:
    """Get conflicts with associated ELAN file information via joins."""
    stmt = (
        select(Conflict, ElanFile)
        .join(
            ConflictOfElanFile, Conflict.conflict_id == ConflictOfElanFile.conflict_id
        )
        .join(ElanFile, ConflictOfElanFile.elan_id == ElanFile.elan_id)
        .join(ElanFileToProject, ElanFile.elan_id == ElanFileToProject.elan_id)
        .where(
            ElanFileToProject.project_id == project_id,
            Conflict.branch_name == branch_name,
            Conflict.conflict_type.in_(
                [
                    ConflictType.GIT_MERGE_CONFLICT,
                    ConflictType.GIT_CONTENT_CONFLICT,
                    ConflictType.GIT_FILE_CONFLICT,
                ]
            ),
        )
    )

    if status:
        stmt = stmt.where(Conflict.status == status)

    result = await db.execute(stmt)
    rows = result.all()

    conflicts_info = []
    for conflict, elan_file in rows:
        conflict_info = {
            "conflict_id": conflict.conflict_id,
            "type": conflict.conflict_type.value,
            "description": conflict.conflict_description,
            "severity": conflict.severity.value,
            "status": conflict.status.value,
            "detected_at": conflict.detected_at.isoformat()
            if conflict.detected_at
            else None,
            "branch_name": conflict.branch_name,
            "git_details": conflict.git_details,
            "filename": elan_file.filename,
            "elan_file_id": elan_file.elan_id,
        }
        conflicts_info.append(conflict_info)

    return conflicts_info


async def resolve_git_conflict_by_filename(
    db: AsyncSession,
    project_id: int,
    branch_name: str,
    filename: str,
    resolved_by_user_id: int,
) -> None:
    """Mark a git conflict as resolved by filename."""
    stmt = (
        select(Conflict)
        .join(
            ConflictOfElanFile, Conflict.conflict_id == ConflictOfElanFile.conflict_id
        )
        .join(ElanFile, ConflictOfElanFile.elan_id == ElanFile.elan_id)
        .join(ElanFileToProject, ElanFile.elan_id == ElanFileToProject.elan_id)
        .where(
            ElanFileToProject.project_id == project_id,
            Conflict.branch_name == branch_name,
            ElanFile.filename == filename,
            Conflict.status.in_([ConflictStatus.DETECTED, ConflictStatus.IN_PROGRESS]),
        )
    )
    result = await db.execute(stmt)
    conflict = result.scalar_one_or_none()

    if conflict:
        conflict.status = ConflictStatus.RESOLVED
        conflict.resolved_at = func.now()
        conflict.resolved_by = resolved_by_user_id
        await db.commit()


async def resolve_all_git_conflicts_for_branch(
    db: AsyncSession, project_id: int, branch_name: str, resolved_by_user_id: int
) -> int:
    """Mark all git conflicts for a branch as resolved."""
    conflicts = await get_git_conflicts_for_branch(
        db, project_id, branch_name, status=ConflictStatus.DETECTED
    )

    resolved_count = 0
    for conflict in conflicts:
        conflict.status = ConflictStatus.RESOLVED
        conflict.resolved_at = func.now()
        conflict.resolved_by = resolved_by_user_id
        resolved_count += 1

    await db.commit()
    return resolved_count
