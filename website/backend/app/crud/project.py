from sqlalchemy.ext.asyncio import AsyncSession
from app.crud.annotation import delete_unused_annotation_values
from app.crud.association import delete_project_associations
from app.crud.comment import delete_project_comments
from app.crud.conflict import delete_project_conflicts
from app.crud.elan_file import delete_elan_file, get_orphan_elan_files_by_project
from app.crud.invitation import delete_project_invitations
from app.crud.tier import delete_tiers_for_elan_file
from app.model.association import UserToProject
from app.model.enums import ProjectPermission
from app.model.project import Project
from app.utils.database import DatabaseUtils

from app.core.centralized_logging import get_logger

logger = get_logger()


async def create_project_db(
    db: AsyncSession,
    project_name: str,
    description: str,
    project_path: str,
    instance_id: int,
    creator_user_id: int,
) -> Project:
    project = Project(
        project_name=project_name,
        description=description,
        project_path=project_path,
        instance_id=instance_id,
    )
    await DatabaseUtils.create_and_commit(db, project)
    user_to_project = UserToProject(
        project_id=project.project_id,
        user_id=creator_user_id,
        permission=ProjectPermission.OWNER,
    )
    await DatabaseUtils.create_and_commit(db, user_to_project)
    return project


async def get_project_name_by_id(db: AsyncSession, project_id: int) -> str | None:
    project = await DatabaseUtils.get_by_id(db, Project, "project_id", project_id)
    if project:
        return project.project_name
    return None


async def get_project_by_name(db: AsyncSession, project_name: str) -> Project | None:
    filters = {"project_name": project_name}
    return await DatabaseUtils.get_one_by_filter(db, Project, filters)


async def get_project_by_id(db: AsyncSession, project_id: int) -> Project | None:
    return await DatabaseUtils.get_by_id(db, Project, "project_id", project_id)


async def delete_project_db(db: AsyncSession, project_name: str) -> None:
    project = await get_project_by_name(db, project_name)
    if project:
        # Delete ELAN files and all related tiers/annotations that are associated with the only this project
        orphan_elan_files = await get_orphan_elan_files_by_project(
            db, project.project_id
        )
        for orphan_elan_file in orphan_elan_files:
            await delete_tiers_for_elan_file(db, orphan_elan_file.elan_id)
            await delete_elan_file(db, orphan_elan_file)
        # Now delete project associations (users, standards, file links)
        await delete_project_associations(db, project.project_id)
        await delete_project_invitations(db, project.project_id)
        await delete_project_conflicts(db, project.project_id)
        await delete_project_comments(db, project.project_id)
        # Clean up unused annotation values
        await delete_unused_annotation_values(db)
        # Finally, delete the project itself
        await db.delete(project)
        await db.commit()


async def list_projects_by_instance(
    db: AsyncSession, instance_id: int
) -> list[Project]:
    filters = {"instance_id": instance_id}
    return await DatabaseUtils.get_by_filter(db, Project, filters)


async def project_exists_by_name(db: AsyncSession, project_name: str) -> bool:
    return await DatabaseUtils.exists(db, Project, "project_name", project_name)


async def add_user_to_project(
    db: AsyncSession,
    user_id: int,
    project_id: int,
    permission: ProjectPermission = ProjectPermission.READ,
) -> UserToProject:
    """Add a user to a project with specified permission."""
    user_to_project = UserToProject(
        user_id=user_id,
        project_id=project_id,
        permission=permission,
    )
    db.add(user_to_project)
    await db.commit()
    await db.refresh(user_to_project)
    return user_to_project
