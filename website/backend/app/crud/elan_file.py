"""ELAN File CRUD operations - Simplified using utilities."""

from sqlalchemy.ext.asyncio import AsyncSession

from app.model.elan_file import ElanFile
from app.utils.database import DatabaseUtils
from app.utils.validation import ValidationUtils
from app.core.centralized_logging import get_logger
from app.model.associations import ElanFileToProject, ElanFileToTier
from app.model.elan_file import ElanFile

logger = get_logger()


async def get_elan_files_by_project(
    db: AsyncSession, project_id: int
) -> list[ElanFile]:
    logger.info(f"Fetching ELAN files for project_id={project_id}")
    filters = {"project_id": project_id}
    links = await DatabaseUtils.get_by_filter(db, ElanFileToProject, filters)
    logger.info(
        f"Found {len(links)} ElanFileToProject links for project_id={project_id}"
    )
    elan_ids = [link.elan_id for link in links]
    files = []
    missing_ids = []
    for elan_id in elan_ids:
        ef = await DatabaseUtils.get_by_id(db, ElanFile, "elan_id", elan_id)
        if ef:
            files.append(ef)
        else:
            missing_ids.append(elan_id)
    logger.info(f"Found {len(files)} ELAN files for project_id={project_id}")
    if missing_ids:
        logger.warning(f"Missing ELAN files for elan_ids={missing_ids}")
    return files


async def delete_elan_file_associations(db: AsyncSession, elan_id: int):
    logger.info(f"Attempting to delete ELAN file associations for elan_id={elan_id}")
    try:
        await DatabaseUtils.bulk_delete(
            db, ElanFileToTier, ElanFileToTier.elan_id == elan_id
        )
        await DatabaseUtils.bulk_delete(
            db, ElanFileToProject, ElanFileToProject.elan_id == elan_id
        )
        logger.info(f"Deleted ELAN file associations for elan_id={elan_id}")
    except Exception as e:
        logger.error(
            f"Failed to delete ELAN file associations for elan_id={elan_id}: {e}"
        )


async def delete_elan_file(db: AsyncSession, elan_file):
    logger.info(
        f"Deleting ELAN file and all related data for elan_id={elan_file.elan_id}"
    )
    try:
        await delete_elan_file_associations(db, elan_file.elan_id)
        logger.info(
            f"Attempting to delete ELAN file row for elan_id={elan_file.elan_id}"
        )
        await db.delete(elan_file)
        logger.info(f"Deleted ELAN file elan_id={elan_file.elan_id}")
    except Exception as e:
        logger.error(f"Failed to delete ELAN file elan_id={elan_file.elan_id}: {e}")


async def get_elan_file_by_id(db: AsyncSession, elan_id: int) -> ElanFile | None:
    """Retrieve an ELAN file by ID."""
    return await DatabaseUtils.get_by_id(db, ElanFile, "elan_id", elan_id)


async def get_elan_file_by_filename(db: AsyncSession, filename: str) -> ElanFile | None:
    """Retrieve an ELAN file by filename."""
    return await DatabaseUtils.get_by_id(db, ElanFile, "filename", filename)


async def get_elan_files_by_user(db: AsyncSession, user_id: int) -> list[ElanFile]:
    """Get all ELAN files for a specific user."""
    filters = {"user_id": user_id}
    return await DatabaseUtils.get_by_filter(db, ElanFile, filters)


async def check_elan_file_exists_by_filename(db: AsyncSession, filename: str) -> bool:
    """Check if an ELAN file with the given filename exists."""
    return await DatabaseUtils.exists(db, ElanFile, "filename", filename)


async def create_elan_file_in_db(
    db: AsyncSession,
    filename: str,
    file_path: str,
    file_size: int,
    user_id: int,
    project_id: int,
) -> ElanFile:
    """Create a new ELAN file record in the database."""
    ValidationUtils.validate_user_id(user_id)
    sanitized_filename = ValidationUtils.sanitize_filename(filename)

    elan_file = ElanFile(
        filename=sanitized_filename,
        file_path=file_path,
        file_size=file_size,
        user_id=user_id,
    )

    elan_file = await DatabaseUtils.create_and_commit(db, elan_file)
    await add_elan_file_to_project(db, elan_file.elan_id, project_id)
    return elan_file


async def delete_elan_file_by_id(db: AsyncSession, elan_id: int) -> bool:
    """Delete an ELAN file by ID."""
    try:
        count = await DatabaseUtils.delete_by_filter(db, ElanFile, elan_id=elan_id)
        return count > 0
    except Exception:
        await db.rollback()
        return False


async def get_all_elan_files(db: AsyncSession) -> list[ElanFile]:
    """Get all ELAN files."""
    return await DatabaseUtils.get_all(db, ElanFile)


# --- ELAN_FILE_TO_TIER ASSOCIATION CRUD ---


async def get_tiers_for_elan_file(db: AsyncSession, elan_id: int) -> list[int]:
    """Get all tier_ids associated with an ELAN file."""
    filters = {"elan_id": elan_id}
    associations = await DatabaseUtils.get_by_filter(db, ElanFileToTier, filters)
    return [assoc.tier_id for assoc in associations]


async def add_elan_file_to_tier(db: AsyncSession, elan_id: int, tier_id: int) -> None:
    """Add association between ELAN file and tier if not exists."""
    filters = {"elan_id": elan_id, "tier_id": tier_id}
    exists = await DatabaseUtils.get_one_by_filter(db, ElanFileToTier, filters)
    if not exists:
        assoc = ElanFileToTier(elan_id=elan_id, tier_id=tier_id)
        await DatabaseUtils.create_and_commit(db, assoc)


async def remove_elan_file_to_tier(
    db: AsyncSession, elan_id: int, tier_id: int
) -> None:
    """Remove association between ELAN file and tier."""
    await DatabaseUtils.bulk_delete(
        db,
        ElanFileToTier,
        (ElanFileToTier.elan_id == elan_id) & (ElanFileToTier.tier_id == tier_id),
    )


async def sync_elan_file_to_tiers(
    db: AsyncSession, elan_id: int, new_tier_ids: list[int]
) -> None:
    current_tier_ids = set(await get_tiers_for_elan_file(db, elan_id))
    new_tier_ids_set = set(new_tier_ids)

    # Add new associations
    for tier_id in new_tier_ids_set - current_tier_ids:
        assoc = ElanFileToTier(elan_id=elan_id, tier_id=tier_id)
        await DatabaseUtils.create_and_commit(db, assoc)

    # Remove old associations
    for tier_id in current_tier_ids - new_tier_ids_set:
        await DatabaseUtils.delete_by_filter(
            db, ElanFileToTier, elan_id=elan_id, tier_id=tier_id
        )


# --- ELAN_FILE_TO_PROJECT ASSOCIATION CRUD ---


async def get_projects_for_elan_file(db: AsyncSession, elan_id: int) -> list[int]:
    """Get all project_ids associated with an ELAN file."""
    filters = {"elan_id": elan_id}
    associations = await DatabaseUtils.get_by_filter(db, ElanFileToProject, filters)
    return [assoc.project_id for assoc in associations]


async def add_elan_file_to_project(
    db: AsyncSession, elan_id: int, project_id: int
) -> None:
    """Add association between ELAN file and project if not exists."""
    filters = {"elan_id": elan_id, "project_id": project_id}
    exists = await DatabaseUtils.get_one_by_filter(db, ElanFileToProject, filters)
    if not exists:
        assoc = ElanFileToProject(elan_id=elan_id, project_id=project_id)
        await DatabaseUtils.create_and_commit(db, assoc)


async def remove_elan_file_to_project(
    db: AsyncSession, elan_id: int, project_id: int
) -> None:
    """Remove association between ELAN file and project."""
    await DatabaseUtils.bulk_delete(
        db,
        ElanFileToProject,
        (ElanFileToProject.elan_id == elan_id)
        & (ElanFileToProject.project_id == project_id),
    )


async def sync_elan_file_to_projects(
    db: AsyncSession, elan_id: int, project_id: int
) -> None:
    current_project_ids = set(await get_projects_for_elan_file(db, elan_id))
    new_project_ids_set = {project_id}

    # Add new association if needed
    if project_id not in current_project_ids:
        assoc = ElanFileToProject(elan_id=elan_id, project_id=project_id)
        await DatabaseUtils.create_and_commit(db, assoc)

    # Remove old associations
    for old_project_id in current_project_ids - new_project_ids_set:
        await DatabaseUtils.delete_by_filter(
            db, ElanFileToProject, elan_id=elan_id, project_id=old_project_id
        )
