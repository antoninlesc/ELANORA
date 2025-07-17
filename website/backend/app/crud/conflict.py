from sqlalchemy.ext.asyncio import AsyncSession

from app.core.centralized_logging import get_logger
from app.model.association import ConflictOfElanFile
from app.model.conflict import Conflict
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
