from sqlalchemy.ext.asyncio import AsyncSession

from app.core.centralized_logging import get_logger
from app.model.association import (
    ElanFileToProject,
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
