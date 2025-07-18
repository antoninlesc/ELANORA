"""ELAN File CRUD operations - Simplified using utilities."""

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.centralized_logging import get_logger
from app.model.association import ElanFileToProject, ElanFileToTier
from app.model.elan_file import ElanFile
from app.utils.database import DatabaseUtils
from app.utils.validation import ValidationUtils
from app.crud.elan_file_media import (
    create_or_get_media_in_db,
    delete_orphaned_media,
)
from app.crud.association import add_elan_file_to_media, add_elan_file_to_project
from app.model.tier_group import TierGroup

logger = get_logger()


async def get_orphan_elan_files_by_project(
    db: AsyncSession, project_id: int
) -> list[ElanFile]:
    logger.info(f"Fetching ELAN files for project_id={project_id}")
    filters = {"project_id": project_id}
    links = await DatabaseUtils.get_by_filter(db, ElanFileToProject, filters)
    logger.info(
        f"Found {len(links)} ElanFileToProject links for project_id={project_id}"
    )
    orphaned_elan_files = await DatabaseUtils.get_orphaned_by_association(
        db,
        ElanFile,
        ElanFileToProject,
        "elan_id",
        "elan_id",
        "project_id",
        project_id,
    )
    logger.info(
        f"Found {len(orphaned_elan_files)} ELAN files for project_id={project_id}"
    )
    return orphaned_elan_files


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

    elan_file = await DatabaseUtils.create(db, elan_file)
    await db.flush()
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
        await DatabaseUtils.create(db, assoc)


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
        await DatabaseUtils.create(db, assoc)

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


async def delete_elan_file_full(db: AsyncSession, elan_id: int) -> bool:
    """
    Delete an ELAN file and all related associations, then clean up orphaned media.
    Returns True if the file was deleted, False otherwise.
    """
    logger.info(f"Full deletion for ELAN file ID: {elan_id}")
    try:
        # Get the ELAN file object
        elan_file_obj = await get_elan_file_by_id(db, elan_id)
        if not elan_file_obj:
            logger.warning(f"ELAN file ID {elan_id} not found.")
            return False

        # Delete associations (tiers, projects, etc.)
        await delete_elan_file_associations(db, elan_id)

        # Check if file is still associated with any projects
        remaining_projects = await get_projects_for_elan_file(db, elan_id)
        if not remaining_projects:
            logger.info(f"Deleting ELAN file row for elan_id={elan_id}")
            await db.delete(elan_file_obj)
            logger.info(f"Deleted ELAN file elan_id={elan_id}")
        else:
            logger.info(
                f"ELAN file elan_id={elan_id} still associated with projects {remaining_projects}, not deleting file row."
            )
            return False

        # Clean up orphaned media
        deleted_count = await delete_orphaned_media(db)
        logger.info(f"Deleted {deleted_count} orphaned media files.")

        return True
    except Exception as e:
        logger.error(f"Failed to fully delete ELAN file elan_id={elan_id}: {e}")
        return False


async def store_elan_file_data_in_db(
    db: AsyncSession, file_info: dict, user_id: int, project_id: int
) -> int:
    """
    Store parsed ELAN file data in the database and sync associations.
    Returns the elan_id.
    """
    # Check if file already exists
    if await check_elan_file_exists_by_filename(db, file_info["filename"]):
        existing_file = await get_elan_file_by_filename(db, file_info["filename"])
        if existing_file:
            await add_elan_file_to_project(db, existing_file.elan_id, project_id)
            # Sync media associations for existing file
            for media in file_info.get("media", []):
                media_obj = await create_or_get_media_in_db(
                    db,
                    media_url=media["media_url"],
                    mime_type=media["mime_type"],
                    relative_media_url=media["relative_media_url"],
                )
                await add_elan_file_to_media(
                    db, existing_file.elan_id, media_obj.media_id
                )
            return existing_file.elan_id

    # Create ELAN file record
    elan_file_obj = await create_elan_file_in_db(
        db=db,
        filename=file_info["filename"],
        file_path=file_info["file_path"],
        file_size=file_info["file_size"],
        user_id=user_id,
        project_id=project_id,
    )

    # Always sync ELAN_FILE_TO_PROJECT associations
    await add_elan_file_to_project(db, elan_file_obj.elan_id, project_id)

    # Store media descriptors and associations
    for media in file_info.get("media", []):
        media_obj = await create_or_get_media_in_db(
            db,
            media_url=media["media_url"],
            mime_type=media["mime_type"],
            relative_media_url=media["relative_media_url"],
        )
        await add_elan_file_to_media(db, elan_file_obj.elan_id, media_obj.media_id)

    # Create TierGroup entry for this ELAN file and project
    tier_group = TierGroup(
        project_id=project_id, elan_file_name=file_info["filename"], section_id=None
    )
    await DatabaseUtils.create(db, tier_group)

    return elan_file_obj.elan_id
