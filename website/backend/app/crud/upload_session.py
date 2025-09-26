from sqlalchemy.ext.asyncio import AsyncSession

from app.core.centralized_logging import get_logger
from app.model.upload_session import UploadSession
from app.utils.database import DatabaseUtils

logger = get_logger()


async def create_upload_session(
    db: AsyncSession,
    session_id: str,
    project_id: int,
    status: str = "processing",
    description: str | None = None,
) -> UploadSession:
    """Create a new upload session."""
    session = UploadSession(
        session_id=session_id,
        project_id=project_id,
        status=status,
        description=description,
    )
    await DatabaseUtils.create(db, session)
    await db.flush()
    return session


async def get_upload_session_by_id(
    db: AsyncSession, session_id: str
) -> UploadSession | None:
    """Get an upload session by ID."""
    return await DatabaseUtils.get_by_id(db, UploadSession, "session_id", session_id)


async def get_upload_sessions_by_conditions(
    db: AsyncSession, conditions: list
) -> list[UploadSession]:
    """Get upload sessions by conditions."""
    return await DatabaseUtils.get_by_conditions(db, UploadSession, conditions)


async def update_upload_session(
    db: AsyncSession, session_id: str, updates: dict
) -> bool:
    """Update an upload session."""
    count = await DatabaseUtils.update_by_filter(
        db, UploadSession, {"session_id": session_id}, updates
    )
    return count > 0


async def delete_upload_session(db: AsyncSession, session_id: str) -> bool:
    """Delete an upload session."""
    count = await DatabaseUtils.delete_by_filter(
        db, UploadSession, session_id=session_id
    )
    return count > 0
