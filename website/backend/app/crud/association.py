from sqlalchemy.ext.asyncio import AsyncSession

from app.core.centralized_logging import get_logger
from app.model.association import (
    ElanFileToProject,
    ElanFileToTier,
    ElanFileToMedia,
    ProjectAnnotStandard,
    UserToProject,
)
from app.utils.database import DatabaseUtils

logger = get_logger()

# --- ElanFileToMedia ---


async def add_elan_file_to_media(db: AsyncSession, elan_id: int, media_id: int):
    filters = {"elan_id": elan_id, "media_id": media_id}
    exists = await DatabaseUtils.get_one_by_filter(db, ElanFileToMedia, filters)
    if not exists:
        assoc = ElanFileToMedia(elan_id=elan_id, media_id=media_id)
        await DatabaseUtils.create(db, assoc)
        await db.flush()


async def remove_elan_file_from_media(db: AsyncSession, elan_id: int, media_id: int):
    await DatabaseUtils.delete_by_filter(
        db, ElanFileToMedia, elan_id=elan_id, media_id=media_id
    )


async def update_elan_file_media(
    db: AsyncSession, elan_id: int, old_media_id: int, new_media_id: int
):
    await DatabaseUtils.update_by_filter(
        db,
        ElanFileToMedia,
        {"elan_id": elan_id, "media_id": old_media_id},
        {"media_id": new_media_id},
    )


# --- ElanFileToProject ---


async def add_elan_file_to_project(db: AsyncSession, elan_id: int, project_id: int):
    filters = {"elan_id": elan_id, "project_id": project_id}
    exists = await DatabaseUtils.get_one_by_filter(db, ElanFileToProject, filters)
    if not exists:
        assoc = ElanFileToProject(elan_id=elan_id, project_id=project_id)
        await DatabaseUtils.create(db, assoc)
        await db.flush()


async def remove_elan_file_from_project(
    db: AsyncSession, elan_id: int, project_id: int
):
    await DatabaseUtils.delete_by_filter(
        db, ElanFileToProject, elan_id=elan_id, project_id=project_id
    )


async def update_elan_file_project(
    db: AsyncSession, elan_id: int, old_project_id: int, new_project_id: int
):
    await DatabaseUtils.update_by_filter(
        db,
        ElanFileToProject,
        {"elan_id": elan_id, "project_id": old_project_id},
        {"project_id": new_project_id},
    )


# --- ElanFileToTier ---


async def add_elan_file_to_tier(db: AsyncSession, elan_id: int, tier_id: int):
    filters = {"elan_id": elan_id, "tier_id": tier_id}
    exists = await DatabaseUtils.get_one_by_filter(db, ElanFileToTier, filters)
    if not exists:
        assoc = ElanFileToTier(elan_id=elan_id, tier_id=tier_id)
        await DatabaseUtils.create(db, assoc)


async def remove_elan_file_from_tier(db: AsyncSession, elan_id: int, tier_id: int):
    await DatabaseUtils.delete_by_filter(
        db, ElanFileToTier, elan_id=elan_id, tier_id=tier_id
    )


async def update_elan_file_tier(
    db: AsyncSession, elan_id: int, old_tier_id: int, new_tier_id: int
):
    await DatabaseUtils.update_by_filter(
        db,
        ElanFileToTier,
        {"elan_id": elan_id, "tier_id": old_tier_id},
        {"tier_id": new_tier_id},
    )


# --- ProjectAnnotStandard ---


async def add_project_annot_standard(
    db: AsyncSession, project_id: int, annot_standard_id: int
):
    filters = {"project_id": project_id, "annot_standard_id": annot_standard_id}
    exists = await DatabaseUtils.get_one_by_filter(db, ProjectAnnotStandard, filters)
    if not exists:
        assoc = ProjectAnnotStandard(
            project_id=project_id, annot_standard_id=annot_standard_id
        )
        await DatabaseUtils.create(db, assoc)


async def remove_project_annot_standard(
    db: AsyncSession, project_id: int, annot_standard_id: int
):
    await DatabaseUtils.delete_by_filter(
        db,
        ProjectAnnotStandard,
        project_id=project_id,
        annot_standard_id=annot_standard_id,
    )


async def update_project_annot_standard(
    db: AsyncSession,
    project_id: int,
    old_annot_standard_id: int,
    new_annot_standard_id: int,
):
    await DatabaseUtils.update_by_filter(
        db,
        ProjectAnnotStandard,
        {"project_id": project_id, "annot_standard_id": old_annot_standard_id},
        {"annot_standard_id": new_annot_standard_id},
    )


# --- UserToProject ---


async def add_user_to_project(db: AsyncSession, user_id: int, project_id: int):
    filters = {"user_id": user_id, "project_id": project_id}
    exists = await DatabaseUtils.get_one_by_filter(db, UserToProject, filters)
    if not exists:
        assoc = UserToProject(user_id=user_id, project_id=project_id)
        await DatabaseUtils.create(db, assoc)


async def remove_user_from_project(db: AsyncSession, user_id: int, project_id: int):
    await DatabaseUtils.delete_by_filter(
        db, UserToProject, user_id=user_id, project_id=project_id
    )


async def update_user_project(
    db: AsyncSession, user_id: int, old_project_id: int, new_project_id: int
):
    await DatabaseUtils.update_by_filter(
        db,
        UserToProject,
        {"user_id": user_id, "project_id": old_project_id},
        {"project_id": new_project_id},
    )


# --- Bulk delete for project associations (unchanged) ---


async def delete_project_associations(db: AsyncSession, project_id: int):
    logger.info(f"Bulk deleting project associations for project_id={project_id}")
    try:
        await DatabaseUtils.bulk_delete(
            db, ElanFileToProject, ElanFileToProject.project_id == project_id
        )
        await DatabaseUtils.bulk_delete(
            db, ProjectAnnotStandard, ProjectAnnotStandard.project_id == project_id
        )
        await DatabaseUtils.bulk_delete(
            db, UserToProject, UserToProject.project_id == project_id
        )
        logger.info("Bulk deleted project associations successfully")
    except Exception as e:
        logger.error(
            f"Failed to bulk delete project associations for project_id={project_id}: {e}"
        )


# --- Utility fetchers (unchanged) ---


async def get_elan_ids_for_project(db, project_id):
    records = await DatabaseUtils.get_by_filter(
        db, ElanFileToProject, {"project_id": project_id}
    )
    return [r.elan_id for r in records]


async def get_tier_ids_for_elan_file(db, elan_id: int) -> list[int]:
    records = await DatabaseUtils.get_by_filter(
        db, ElanFileToTier, {"elan_id": elan_id}
    )
    return [r.tier_id for r in records]
