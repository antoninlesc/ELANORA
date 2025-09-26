from sqlalchemy.ext.asyncio import AsyncSession

from app.model.file_type import FileType
from app.model.project_file_type import ProjectFileType
from app.utils.database import DatabaseUtils


async def get_file_type_by_id(db: AsyncSession, file_type_id: int) -> FileType | None:
    return await DatabaseUtils.get_by_id(db, FileType, "id", file_type_id)


async def get_file_type_by_name(db: AsyncSession, name: str) -> FileType | None:
    """Get file type by name."""
    filters = {"name": name}
    return await DatabaseUtils.get_one_or_none(db, FileType, filters=filters)


async def get_file_type_by_extension(
    db: AsyncSession, extension: str
) -> FileType | None:
    """Get file type by extension."""
    filters = {"extension": extension}
    return await DatabaseUtils.get_one_or_none(db, FileType, filters=filters)


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
    from sqlalchemy import exists, select

    # Find orphaned FileType records using a more complex query
    # A FileType is orphaned if:
    # 1. It's not referenced by any ProjectFileType AND
    # 2. No ProjectNamingStandard references any ProjectFileType that uses this FileType

    # Custom query to find truly orphaned FileType records
    orphaned_query = select(FileType).where(
        # Not referenced by any ProjectFileType
        ~exists(
            select(ProjectFileType.id).where(
                ProjectFileType.file_type_id == FileType.id
            )
        )
    )

    result = await db.execute(orphaned_query)
    orphaned_file_types = result.scalars().all()

    # Delete the orphaned records
    count = 0
    for file_type in orphaned_file_types:
        await db.delete(file_type)
        count += 1

    return count
