from sqlalchemy.ext.asyncio import AsyncSession

from app.core.centralized_logging import get_logger
from app.model.association import (
    ElanFileToProject,
    ElanFileToTier,
    ProjectAnnotStandard,
    UserToProject,
)
from app.utils.database import DatabaseUtils

logger = get_logger()


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
