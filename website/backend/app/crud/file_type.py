from sqlalchemy.ext.asyncio import AsyncSession

from app.model.file_type import FileType
from app.model.project_file_type import ProjectFileType
from app.utils.database import DatabaseUtils


async def get_file_type_by_id(db: AsyncSession, file_type_id: int) -> FileType | None:
    return await DatabaseUtils.get_by_id(db, FileType, "id", file_type_id)


async def get_file_type_by_name(db: AsyncSession, name: str) -> FileType | None:
    result = await DatabaseUtils.get_by_filter(db, FileType, {"name": name}, limit=1)
    return result[0] if result else None


async def get_file_type_by_extension(db: AsyncSession, extension: str):
    result = await DatabaseUtils.get_by_filter(
        db, FileType, {"extension": extension}, limit=1
    )
    return result[0] if result else None


async def create_file_type(db: AsyncSession, extension: str) -> FileType:
    file_type = FileType(extension=extension)
    await DatabaseUtils.create(db, file_type)
    await db.flush()
    return file_type


async def update_file_type(
    db: AsyncSession, file_type_id: int, update_fields: dict
) -> int:
    return await DatabaseUtils.update_by_filter(
        db, FileType, {"id": file_type_id}, update_fields
    )


async def delete_file_type(db: AsyncSession, file_type_id: int) -> int:
    return await DatabaseUtils.delete_by_filter(db, FileType, id=file_type_id)


async def delete_orphaned_file_types(db: AsyncSession) -> int:
    """Delete FileType records not referenced by any ProjectFileType."""
    # Find orphaned FileType records using NOT EXISTS condition
    orphaned_file_types = await DatabaseUtils.get_with_exists_conditions(
        db,
        FileType,
        not_exists_conditions=[(ProjectFileType, {"file_type_id": "id"})],
    )

    # Delete the orphaned records
    count = 0
    for file_type in orphaned_file_types:
        await db.delete(file_type)
        count += 1

    return count
