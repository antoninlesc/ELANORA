from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.model.project_naming_standard import ProjectNamingStandard
from app.model.naming_component import NamingComponent
from app.utils.database import DatabaseUtils

# --- ProjectNamingStandard CRUD ---


async def get_standards_by_project(
    db: AsyncSession, project_id: int
) -> list[ProjectNamingStandard]:
    return await DatabaseUtils.get_by_filter(
        db, ProjectNamingStandard, {"project_id": project_id}
    )


async def get_standard_by_id(
    db: AsyncSession, standard_id: int
) -> ProjectNamingStandard | None:
    return await DatabaseUtils.get_by_id(db, ProjectNamingStandard, "id", standard_id)


async def create_standard(
    db: AsyncSession,
    project_id: int,
    name: str,
    file_type_id: int,
    pattern: str,
    description: str | None,
):
    from app.model.project_naming_standard import ProjectNamingStandard

    standard = ProjectNamingStandard(
        project_id=project_id,
        name=name,
        file_type_id=file_type_id,
        pattern=pattern,
        description=description,
    )
    db.add(standard)
    await db.flush()
    return standard


async def update_standard(
    db: AsyncSession, standard_id: int, update_fields: dict
) -> int:
    return await DatabaseUtils.update_by_filter(
        db, ProjectNamingStandard, {"id": standard_id}, update_fields
    )


async def delete_standard(db: AsyncSession, standard_id: int) -> int:
    return await DatabaseUtils.delete_by_filter(
        db, ProjectNamingStandard, id=standard_id
    )
