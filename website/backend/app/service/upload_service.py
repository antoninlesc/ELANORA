"""upload_service.py

Service layer for upload-related operations.
"""

import os
import shutil
from datetime import datetime, timedelta
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.centralized_logging import get_logger
from app.crud.tier import delete_tiers_for_session
from app.crud.tier_group import delete_tier_groups_for_session
from app.crud.tier_section import delete_tier_sections_for_session
from app.model.upload_session import UploadSession
from app.utils.database import DatabaseUtils

logger = get_logger()


async def cleanup_expired_upload_sessions(db: AsyncSession) -> dict[str, Any]:
    """Clean up expired upload sessions and their associated staged data and temp files.

    Returns:
        Dict with cleanup results

    """
    try:
        # Define expiration time (e.g., 24 hours)
        expiration_time = datetime.utcnow() - timedelta(hours=24)

        # Find expired sessions
        expired_sessions = await DatabaseUtils.get_by_conditions(
            db,
            UploadSession,
            conditions=[
                UploadSession.created_at < expiration_time,
                UploadSession.status.in_(
                    ["processing", "completed", "pending_approval"]
                ),
            ],
        )

        if not expired_sessions:
            return {"message": "No expired sessions to clean up", "cleaned_count": 0}

        cleaned_count = 0

        for session in expired_sessions:
            session_id = session.session_id

            # Delete temp files for this session
            temp_dir = f"/tmp/uploads/{session_id}"
            if os.path.exists(temp_dir):
                shutil.rmtree(temp_dir)
                logger.info(f"Deleted temp directory: {temp_dir}")

            # Delete staged data for this session using CRUD functions
            await delete_tiers_for_session(db, session_id)
            await delete_tier_groups_for_session(db, session_id)
            await delete_tier_sections_for_session(db, session_id)

            # Delete the session
            await db.delete(session)
            cleaned_count += 1

        await db.commit()

        logger.info(f"Cleaned up {cleaned_count} expired upload sessions")

        return {
            "message": f"Successfully cleaned up {cleaned_count} expired sessions",
            "cleaned_count": cleaned_count,
        }

    except Exception as e:
        logger.error(f"Error cleaning up expired sessions: {e!s}")
        await db.rollback()
        raise


# Placeholder for other upload services if needed
async def process_upload_files_service(db: AsyncSession, files, project_id, session_id):
    # Implement if needed
    pass


async def confirm_upload_service(
    db: AsyncSession, session_id, tier_assignments, new_section_names, description
):
    # Implement if needed
    pass


async def cancel_upload_service(db: AsyncSession, session_id):
    # Implement if needed
    pass
