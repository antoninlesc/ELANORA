from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from app.model.elan_file_media import ElanFileMedia
from app.model.association import ElanFileToMedia
from app.utils.database import DatabaseUtils


async def get_media_by_url(db: AsyncSession, media_url: str) -> ElanFileMedia | None:
    """Retrieve a media file by its URL."""
    filters = {"media_url": media_url}
    return await DatabaseUtils.get_one_by_filter(db, ElanFileMedia, filters)


async def create_media_in_db(
    db: AsyncSession,
    media_url: str,
    mime_type: str | None = None,
    relative_media_url: str | None = None,
) -> ElanFileMedia:
    """Create a new media file record in the database."""
    media = ElanFileMedia(
        media_url=media_url,
        mime_type=mime_type,
        relative_media_url=relative_media_url,
    )
    await DatabaseUtils.create(db, media)
    await db.flush()
    return media


async def create_or_get_media_in_db(
    db: AsyncSession,
    media_url: str,
    mime_type: str | None = None,
    relative_media_url: str | None = None,
) -> ElanFileMedia:
    """Get or create a media file by URL."""
    media = await get_media_by_url(db, media_url)
    if media:
        return media
    return await create_media_in_db(db, media_url, mime_type, relative_media_url)


async def get_media_by_id(db: AsyncSession, media_id: int) -> ElanFileMedia | None:
    """Retrieve a media file by its ID."""
    return await DatabaseUtils.get_by_id(db, ElanFileMedia, "media_id", media_id)


async def get_all_media(db: AsyncSession) -> list[ElanFileMedia]:
    """Get all media files."""
    return await DatabaseUtils.get_all(db, ElanFileMedia)


async def delete_orphaned_media(db: AsyncSession) -> int:
    """
    Delete all media files that are not referenced in ELAN_FILE_TO_MEDIA.
    Returns the number of deleted rows.
    """
    return await DatabaseUtils.delete_fully_orphaned(
        db, ElanFileMedia, ElanFileToMedia, "media_id", "media_id"
    )
