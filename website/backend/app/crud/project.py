from sqlalchemy.ext.asyncio import AsyncSession
from app.model.project import Project
from sqlalchemy.future import select


async def create_project_db(
    db: AsyncSession,
    project_name: str,
    description: str,
    project_path: str,
    instance_id: int,
) -> Project:
    project = Project(
        project_name=project_name,
        description=description,
        project_path=project_path,
        instance_id=instance_id,
    )
    db.add(project)
    await db.commit()
    await db.refresh(project)
    return project


async def get_project_by_name(db: AsyncSession, project_name: str) -> Project | None:
    result = await db.execute(
        select(Project).where(Project.project_name == project_name)
    )
    return result.scalars().first()


async def get_project_by_id(db: AsyncSession, project_id: int) -> Project | None:
    result = await db.execute(select(Project).where(Project.project_id == project_id))
    return result.scalars().first()


async def delete_project(db: AsyncSession, project_id: int) -> None:
    project = await get_project_by_id(db, project_id)
    if project:
        await db.delete(project)
        await db.commit()
