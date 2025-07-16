from sqlalchemy.ext.asyncio import AsyncSession

from app.core.centralized_logging import get_logger
from app.model.invitation import Invitation
from app.utils.database import DatabaseUtils

logger = get_logger()


async def delete_project_invitations(db: AsyncSession, project_id: int):
    logger.info(f"Deleting invitations for project_id={project_id}")
    try:
        count = (
            await db.execute(
                Invitation.__table__.count().where(Invitation.project_id == project_id)
            )
        ).scalar_one()
        logger.info(f"Found {count} invitations to delete for project_id={project_id}")
        await DatabaseUtils.delete_by_filter(db, Invitation, project_id=project_id)
        logger.info("Invitations deleted successfully")
    except Exception as e:
        logger.error(f"Failed to delete invitations for project_id={project_id}: {e}")
