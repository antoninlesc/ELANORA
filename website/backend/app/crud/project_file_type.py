from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.centralized_logging import get_logger
from app.model.project_file_type import ProjectFileType
from app.utils.database import DatabaseUtils

logger = get_logger()


async def remove_file_type_from_project(
    db: AsyncSession, project_id: int, file_type_id: int
) -> None:
    """Remove a file type from a project."""
    await DatabaseUtils.delete_by_filter(
        db, ProjectFileType, project_id=project_id, file_type_id=file_type_id
    )


async def add_project_file_type(
    db: AsyncSession,
    project_id: int,
    name: str,
    file_type_id: int,
) -> ProjectFileType:
    """Add a project file type association, returning existing or new instance."""
    filters = {"project_id": project_id, "name": name}
    exists = await DatabaseUtils.get_one_or_none(db, ProjectFileType, filters)
    if not exists:
        assoc = ProjectFileType(
            project_id=project_id,
            name=name,
            file_type_id=file_type_id,
        )
        await DatabaseUtils.create(db, assoc)
        await db.flush()
        return assoc
    return exists


async def get_project_file_types(db: AsyncSession, project_id: int):
    return await DatabaseUtils.get_by_filter(
        db,
        ProjectFileType,
        {"project_id": project_id},
        options=[selectinload(ProjectFileType.file_type)],
    )


async def delete_project_file_type(
    db: AsyncSession, project_file_type_id: int, project_id: int
):
    # Delete the association between the project and the project file type
    await DatabaseUtils.delete_by_filter(
        db, ProjectFileType, project_id=project_id, id=project_file_type_id
    )


async def update_project_file_type(
    db: AsyncSession, project_file_type_id: int, update_fields: dict
):
    # Only update name or file_type_id (not extension here)
    allowed = {}
    if "name" in update_fields:
        allowed["name"] = update_fields["name"]
    if "file_type_id" in update_fields:
        allowed["file_type_id"] = update_fields["file_type_id"]
    if allowed:
        await DatabaseUtils.update_by_filter(
            db, ProjectFileType, {"id": project_file_type_id}, allowed
        )


async def get_project_file_type_by_id(
    db: AsyncSession, project_file_type_id: int
) -> ProjectFileType | None:
    """Get a project file type by ID with file type relationship loaded."""
    return await DatabaseUtils.get_one_or_none(
        db,
        ProjectFileType,
        {"id": project_file_type_id},
        options=[selectinload(ProjectFileType.file_type)],
    )


async def count_project_file_types_by_file_type_id(
    db: AsyncSession, file_type_id: int
) -> int:
    """Count project file types using a specific file type ID."""
    return await DatabaseUtils.count_records(
        db, ProjectFileType, {"file_type_id": file_type_id}
    )


async def update_project_file_type_name(
    db: AsyncSession, project_file_type_id: int, name: str
):
    return await DatabaseUtils.update_by_filter(
        db, ProjectFileType, {"id": project_file_type_id}, {"name": name}
    )


async def update_project_file_type_file_type_id(
    db: AsyncSession, project_file_type_id: int, new_file_type_id: int
):
    return await DatabaseUtils.update_by_filter(
        db,
        ProjectFileType,
        {"id": project_file_type_id},
        {"file_type_id": new_file_type_id},
    )


async def get_project_file_type_by_project_and_file_type(
    db: AsyncSession, project_id: int, file_type_id: int
) -> ProjectFileType | None:
    """Get the ProjectFileType for a given project and file_type_id."""
    filters = {"project_id": project_id, "file_type_id": file_type_id}
    return await DatabaseUtils.get_one_or_none(db, ProjectFileType, filters)


async def get_project_file_type_with_file_type(
    db: AsyncSession, project_file_type_id: int
) -> ProjectFileType | None:
    """Get a project file type with file type relationship loaded."""
    return await DatabaseUtils.get_one_or_none(
        db,
        ProjectFileType,
        {"id": project_file_type_id},
        options=[selectinload(ProjectFileType.file_type)],
    )


async def delete_project_file_types_for_project(db: AsyncSession, project_id: int):
    """Delete all project file type associations for a specific project."""
    conditions = [ProjectFileType.project_id == project_id]
    await DatabaseUtils.delete_by_conditions(db, ProjectFileType, conditions=conditions)
