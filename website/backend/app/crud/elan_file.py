"""ELAN File CRUD operations - Simplified using utilities."""

from typing import List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.model.elan_file import ElanFile
from app.utils.database import DatabaseUtils
from app.utils.validation import ValidationUtils


async def get_elan_file_by_id(db: AsyncSession, elan_id: int) -> Optional[ElanFile]:
    """Retrieve an ELAN file by ID."""
    return await DatabaseUtils.get_by_id(db, ElanFile, "elan_id", elan_id)


async def get_elan_file_by_filename(
    db: AsyncSession, filename: str
) -> Optional[ElanFile]:
    """Retrieve an ELAN file by filename."""
    return await DatabaseUtils.get_by_id(db, ElanFile, "filename", filename)


async def get_elan_files_by_user(db: AsyncSession, user_id: int) -> List[ElanFile]:
    """Get all ELAN files for a specific user."""
    result = await db.execute(select(ElanFile).filter(ElanFile.user_id == user_id))
    return list(result.scalars().all())


async def check_elan_file_exists_by_filename(db: AsyncSession, filename: str) -> bool:
    """Check if an ELAN file with the given filename exists."""
    return await DatabaseUtils.exists(db, ElanFile, "filename", filename)


async def create_elan_file_in_db(
    db: AsyncSession, filename: str, file_path: str, file_size: int, user_id: int
) -> ElanFile:
    """Create a new ELAN file record in the database."""
    # Validate inputs
    ValidationUtils.validate_user_id(user_id)
    sanitized_filename = ValidationUtils.sanitize_filename(filename)

    elan_file = ElanFile(
        filename=sanitized_filename,
        file_path=file_path,
        file_size=file_size,
        user_id=user_id,
    )

    return await DatabaseUtils.create_and_commit(db, elan_file)


async def delete_elan_file_by_id(db: AsyncSession, elan_id: int) -> bool:
    """Delete an ELAN file by ID."""
    try:
        elan_file = await get_elan_file_by_id(db, elan_id)
        if elan_file:
            await db.delete(elan_file)
            await db.commit()
            return True
        return False
    except Exception:
        await db.rollback()
        return False


async def get_all_elan_files(db: AsyncSession) -> List[ElanFile]:
    """Get all ELAN files."""
    return await DatabaseUtils.get_all(db, ElanFile)
