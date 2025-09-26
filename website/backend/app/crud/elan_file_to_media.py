from sqlalchemy.ext.asyncio import AsyncSession

from app.core.centralized_logging import get_logger
from app.model.elan_file_to_media import ElanFileToMedia
from app.utils.database import DatabaseUtils

logger = get_logger()


async def add_elan_file_to_media(db: AsyncSession, elan_id: int, media_id: int) -> None:
    """Add an ELAN file to media association if it doesn't already exist."""
    filters = {"elan_id": elan_id, "media_id": media_id}
    exists = await DatabaseUtils.get_one_or_none(db, ElanFileToMedia, filters)
    if not exists:
        assoc = ElanFileToMedia(elan_id=elan_id, media_id=media_id)
        await DatabaseUtils.create(db, assoc)
        await db.flush()


async def remove_elan_file_from_media(db: AsyncSession, elan_id: int, media_id: int):
    await DatabaseUtils.delete_by_filter(
        db, ElanFileToMedia, elan_id=elan_id, media_id=media_id
    )


async def update_elan_file_media(
    db: AsyncSession, elan_id: int, old_media_id: int, new_media_id: int
):
    await DatabaseUtils.update_by_filter(
        db,
        ElanFileToMedia,
        {"elan_id": elan_id, "media_id": old_media_id},
        {"media_id": new_media_id},
    )
