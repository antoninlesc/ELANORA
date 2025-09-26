from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.centralized_logging import get_logger
from app.model.user_to_project import UserToProject
from app.utils.database import DatabaseUtils

logger = get_logger()


async def add_user_to_project(db: AsyncSession, user_id: int, project_id: int) -> None:
    """Add a user to project association if it doesn't already exist."""
    filters = {"user_id": user_id, "project_id": project_id}
    exists = await DatabaseUtils.get_one_or_none(db, UserToProject, filters)
    if not exists:
        assoc = UserToProject(user_id=user_id, project_id=project_id)
        await DatabaseUtils.create(db, assoc)


async def remove_user_from_project(db: AsyncSession, user_id: int, project_id: int):
    """Remove a user from a project using simple delete by filter."""
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


async def get_project_users(db: AsyncSession, project_id: int) -> list[dict]:
    """Get all users associated with a project with their permissions."""
    # Use DatabaseUtils with relationship loading
    user_to_projects = await DatabaseUtils.get_by_filter(
        db,
        UserToProject,
        {"project_id": project_id},
        options=[selectinload(UserToProject.user)],
    )
    return [
        {
            "user_id": user_to_project.user_id,
            "username": user_to_project.user.username,
            "email": user_to_project.user.email,
            "permission": user_to_project.permission,
        }
        for user_to_project in user_to_projects
    ]


async def delete_project_users_for_project(db: AsyncSession, project_id: int):
    """Delete all user-to-project associations for a specific project."""
    conditions = [UserToProject.project_id == project_id]
    await DatabaseUtils.delete_by_conditions(db, UserToProject, conditions=conditions)
