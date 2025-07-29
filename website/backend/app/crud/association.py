from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.centralized_logging import get_logger
from app.model.association import (
    ElanFileToProject,
    ElanFileToTier,
    ProjectAnnotStandard,
    UserToProject,
)
from app.model.user import User
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
    """Get all tier IDs associated with an ELAN file."""
    records = await DatabaseUtils.get_by_filter(
        db, ElanFileToTier, {"elan_id": elan_id}
    )
    return [r.tier_id for r in records]


async def get_project_users(db: AsyncSession, project_id: int) -> list[dict]:
    """Get all users associated with a project with their permissions."""
    stmt = (
        select(UserToProject, User)
        .join(User, UserToProject.user_id == User.user_id)
        .where(UserToProject.project_id == project_id)
    )

    result = await db.execute(stmt)
    return [
        {
            "user_id": user_to_project.user_id,
            "username": user.username,
            "email": user.email,
            "permission": user_to_project.permission,
        }
        for user_to_project, user in result.all()
    ]


async def remove_user_from_project(
    db: AsyncSession, user_id: int, project_id: int
) -> bool:
    """Remove a user from a project."""
    try:
        await DatabaseUtils.bulk_delete(
            db,
            UserToProject,
            (UserToProject.user_id == user_id)
            & (UserToProject.project_id == project_id),
        )
        return True
    except Exception as e:
        logger.error(f"Failed to remove user {user_id} from project {project_id}: {e}")
        return False
