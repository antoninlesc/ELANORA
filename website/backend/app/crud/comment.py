from sqlalchemy.ext.asyncio import AsyncSession

from app.core.centralized_logging import get_logger
from app.model.association import CommentConflict, CommentProject
from app.utils.database import DatabaseUtils

logger = get_logger()


async def delete_project_comments(db: AsyncSession, project_id: int):
    logger.info(f"Deleting project comments for project_id={project_id}")
    try:
        count = (
            await db.execute(
                CommentProject.__table__.count().where(
                    CommentProject.project_id == project_id
                )
            )
        ).scalar_one()
        logger.info(
            f"Found {count} project comments to delete for project_id={project_id}"
        )
        await DatabaseUtils.delete_by_filter(db, CommentProject, project_id=project_id)
        logger.info("Project comments deleted successfully")
    except Exception as e:
        logger.error(
            f"Failed to delete project comments for project_id={project_id}: {e}"
        )


async def delete_conflict_comments(db: AsyncSession, conflict_id: str):
    logger.info(f"Deleting conflict comments for conflict_id={conflict_id}")
    try:
        count = (
            await db.execute(
                CommentConflict.__table__.count().where(
                    CommentConflict.conflict_id == conflict_id
                )
            )
        ).scalar_one()
        logger.info(
            f"Found {count} conflict comments to delete for conflict_id={conflict_id}"
        )
        await DatabaseUtils.delete_by_filter(
            db, CommentConflict, conflict_id=conflict_id
        )
        logger.info("Conflict comments deleted successfully")
    except Exception as e:
        logger.error(
            f"Failed to delete conflict comments for conflict_id={conflict_id}: {e}"
        )
