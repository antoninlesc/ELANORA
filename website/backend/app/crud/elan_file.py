"""ELAN File CRUD operations - Simplified using utilities."""

from typing import List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import delete, select


from app.model.elan_file import ElanFile
from app.model.associations import ElanFileToTier, ElanFileToProject
from app.utils.database import DatabaseUtils
from app.utils.validation import ValidationUtils
from app.core.centralized_logging import get_logger

logger = get_logger()


async def get_elan_file_by_id(db: AsyncSession, elan_id: int) -> Optional[ElanFile]:
    """Retrieve an ELAN file by ID."""
    return await DatabaseUtils.get_by_id(db, ElanFile, "elan_id", elan_id)


async def get_elan_file_by_filename(
    db: AsyncSession, filename: str
) -> Optional[ElanFile]:
    """Retrieve an ELAN file by filename."""
    return await DatabaseUtils.get_by_id(db, ElanFile, "filename", filename)


async def get_elan_files_by_user(db: AsyncSession, user_id: int) -> List[ElanFile]:
    """Get all ELAN files for a specific user."""
    result = await db.execute(select(ElanFile).filter(ElanFile.user_id == user_id))
    return list(result.scalars().all())


async def check_elan_file_exists_by_filename(db: AsyncSession, filename: str) -> bool:
    """Check if an ELAN file with the given filename exists."""
    return await DatabaseUtils.exists(db, ElanFile, "filename", filename)


async def create_elan_file_in_db(
    db: AsyncSession, filename: str, file_path: str, file_size: int, user_id: int
) -> ElanFile:
    """Create a new ELAN file record in the database."""
    # Validate inputs
    ValidationUtils.validate_user_id(user_id)
    sanitized_filename = ValidationUtils.sanitize_filename(filename)

    elan_file = ElanFile(
        filename=sanitized_filename,
        file_path=file_path,
        file_size=file_size,
        user_id=user_id,
    )

    return await DatabaseUtils.create_and_commit(db, elan_file)


async def delete_elan_file_by_id(db: AsyncSession, elan_id: int) -> bool:
    """Delete an ELAN file by ID."""
    try:
        elan_file = await get_elan_file_by_id(db, elan_id)
        if elan_file:
            await db.delete(elan_file)
            await db.commit()
            return True
        return False
    except Exception:
        await db.rollback()
        return False


async def get_all_elan_files(db: AsyncSession) -> List[ElanFile]:
    """Get all ELAN files."""
    return await DatabaseUtils.get_all(db, ElanFile)


# --- ELAN_FILE_TO_TIER ASSOCIATION CRUD ---


async def get_tiers_for_elan_file(db: AsyncSession, elan_id: int) -> list[str]:
    """Get all tier_ids associated with an ELAN file."""
    result = await db.execute(
        select(ElanFileToTier.tier_id).where(ElanFileToTier.elan_id == elan_id)
    )
    return [row[0] for row in result]


async def add_elan_file_to_tier(db: AsyncSession, elan_id: int, tier_id: str) -> None:
    """Add association between ELAN file and tier if not exists."""
    exists = await db.execute(
        select(ElanFileToTier).where(
            ElanFileToTier.elan_id == elan_id,
            ElanFileToTier.tier_id == tier_id,
        )
    )
    if not exists.scalar_one_or_none():
        db.add(ElanFileToTier(elan_id=elan_id, tier_id=tier_id))
        await db.commit()


async def remove_elan_file_to_tier(
    db: AsyncSession, elan_id: int, tier_id: str
) -> None:
    """Remove association between ELAN file and tier."""
    await db.execute(
        delete(ElanFileToTier).where(
            ElanFileToTier.elan_id == elan_id,
            ElanFileToTier.tier_id == tier_id,
        )
    )
    await db.commit()


async def sync_elan_file_to_tiers(
    db: AsyncSession, elan_id: int, new_tier_ids: list[str]
) -> None:
    """Synchronize ELAN_FILE_TO_TIER associations for a file."""
    current_tier_ids = set(await get_tiers_for_elan_file(db, elan_id))
    new_tier_ids_set = set(new_tier_ids)

    # Add new associations
    for tier_id in new_tier_ids_set - current_tier_ids:
        db.add(ElanFileToTier(elan_id=elan_id, tier_id=tier_id))

    # Remove old associations
    for tier_id in current_tier_ids - new_tier_ids_set:
        await db.execute(
            delete(ElanFileToTier).where(
                ElanFileToTier.elan_id == elan_id,
                ElanFileToTier.tier_id == tier_id,
            )
        )
    await db.commit()


# --- ELAN_FILE_TO_PROJECT ASSOCIATION CRUD ---


async def get_projects_for_elan_file(db: AsyncSession, elan_id: int) -> list[int]:
    """Get all project_ids associated with an ELAN file."""
    result = await db.execute(
        select(ElanFileToProject.project_id).where(ElanFileToProject.elan_id == elan_id)
    )
    return [row[0] for row in result]


async def add_elan_file_to_project(
    db: AsyncSession, elan_id: int, project_id: int
) -> None:
    """Add association between ELAN file and project if not exists."""
    exists = await db.execute(
        select(ElanFileToProject).where(
            ElanFileToProject.elan_id == elan_id,
            ElanFileToProject.project_id == project_id,
        )
    )
    if not exists.scalar_one_or_none():
        db.add(ElanFileToProject(elan_id=elan_id, project_id=project_id))
        await db.commit()


async def remove_elan_file_to_project(
    db: AsyncSession, elan_id: int, project_id: int
) -> None:
    """Remove association between ELAN file and project."""
    await db.execute(
        delete(ElanFileToProject).where(
            ElanFileToProject.elan_id == elan_id,
            ElanFileToProject.project_id == project_id,
        )
    )
    await db.commit()


async def sync_elan_file_to_projects(
    db: AsyncSession, elan_id: int, new_project_ids: list[int]
) -> None:
    """Synchronize ELAN_FILE_TO_PROJECT associations for a file."""
    from app.core.centralized_logging import get_logger

    logger = get_logger()
    logger.info(
        f"sync_elan_file_to_projects called for elan_id={elan_id} with new_project_ids={new_project_ids}"
    )
    current_project_ids = set(await get_projects_for_elan_file(db, elan_id))
    new_project_ids_set = set(new_project_ids)

    # Add new associations
    for project_id in new_project_ids_set - current_project_ids:
        logger.info(
            f"Adding ELAN_FILE_TO_PROJECT association: elan_id={elan_id}, project_id={project_id}"
        )
        db.add(ElanFileToProject(elan_id=elan_id, project_id=project_id))

    # Remove old associations
    for project_id in current_project_ids - new_project_ids_set:
        logger.info(
            f"Removing ELAN_FILE_TO_PROJECT association: elan_id={elan_id}, project_id={project_id}"
        )
        await db.execute(
            delete(ElanFileToProject).where(
                ElanFileToProject.elan_id == elan_id,
                ElanFileToProject.project_id == project_id,
            )
        )
    await db.commit()
    logger.info(f"Finished syncing ELAN_FILE_TO_PROJECT for elan_id={elan_id}")
