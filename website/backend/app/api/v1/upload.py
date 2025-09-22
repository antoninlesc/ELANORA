"""
upload.py

API endpoints for file upload processing.
"""

from fastapi import APIRouter, UploadFile, File, Form, HTTPException, Depends
from typing import List, Dict, Any
import uuid
from sqlalchemy.ext.asyncio import AsyncSession

from app.service.tier_extraction_service import extract_tiers_from_files
from app.dependency.database import get_db_dep
from app.model.upload_session import UploadSession
from app.model.tier import Tier
from app.model.tier_group import TierGroup
from app.model.tier_section import TierSection
from app.core.centralized_logging import get_logger

logger = get_logger()

router = APIRouter(prefix="/upload", tags=["upload"])


@router.post("/process")
async def process_upload_files(
    files: List[UploadFile] = File(...),
    project_id: str = Form(...),
    db: AsyncSession = Depends(get_db_dep),
):
    """
    Process uploaded files for tier extraction.
    Creates staged database entries and returns extracted tiers.
    """
    try:
        # Generate session ID
        session_id = str(uuid.uuid4())

        # Create upload session record
        upload_session = UploadSession(
            session_id=session_id, project_id=int(project_id), status="processing"
        )
        db.add(upload_session)
        await db.flush()

        # Extract tiers from files (creates staged DB entries)
        extracted_tiers = await extract_tiers_from_files(
            files, int(project_id), session_id, db
        )

        # Update session status to completed
        upload_session.status = "completed"
        await db.commit()

        return {"session_id": session_id, "extracted_tiers": extracted_tiers}

    except Exception as e:
        logger.error(f"Error processing upload files: {str(e)}")
        await db.rollback()
        raise HTTPException(status_code=500, detail=f"Error processing files: {str(e)}")


@router.post("/confirm")
async def confirm_upload(
    session_id: str = Form(...),
    tier_assignments: str = Form(...),  # JSON string
    new_section_names: str = Form(...),  # JSON string
    description: str = Form(...),
    db: AsyncSession = Depends(get_db_dep),
):
    """
    Confirm and finalize the upload by marking it as pending approval.
    """
    try:
        # Get the upload session
        upload_session = await db.get(UploadSession, session_id)
        if not upload_session:
            raise HTTPException(status_code=404, detail="Upload session not found")

        if upload_session.status != "completed":
            raise HTTPException(
                status_code=400, detail="Upload session is not ready for confirmation"
            )

        # Parse the JSON data
        import json

        try:
            parsed_assignments = json.loads(tier_assignments)
            parsed_new_sections = json.loads(new_section_names)
        except json.JSONDecodeError:
            raise HTTPException(
                status_code=400, detail="Invalid JSON data in tier assignments"
            )

        # Create new sections if specified
        from app.crud.tier_section import create_tier_section

        section_mapping = {}  # section_name -> tier_section_id
        for section_name in parsed_new_sections:
            section = await create_tier_section(
                db,
                upload_session.project_id,
                section_name,
                is_staged=True,
                session_id=session_id,
            )
            section_mapping[section_name] = section.tier_section_id

        # Create tier groups based on assignments
        from app.crud.tier_group import create_tier_group

        for assignment in parsed_assignments:
            tier_id = assignment["tier_id"]
            section_name = assignment.get("section_name")

            # Get section_id from mapping, or None if not assigned to a section
            section_id = section_mapping.get(section_name) if section_name else None

            # Create tier group (staged)
            await create_tier_group(
                db,
                section_id=section_id,
                project_id=upload_session.project_id,
                tier_id=tier_id,
                tier_name=assignment["tier_name"],
                is_staged=True,
                session_id=session_id,
            )

        # Update session with confirmation data
        upload_session.status = "pending_approval"
        upload_session.description = description

        await db.commit()

        logger.info(
            f"Upload session {session_id} confirmed and marked as pending approval"
        )

        return {
            "message": "Upload confirmed successfully and is now pending administrator approval"
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error confirming upload: {str(e)}")
        await db.rollback()
        raise HTTPException(
            status_code=500, detail=f"Error confirming upload: {str(e)}"
        )


@router.post("/cancel")
async def cancel_upload(
    session_id: str = Form(...),
    db: AsyncSession = Depends(get_db_dep),
):
    """
    Cancel an upload session and clean up all staged data.
    """
    try:
        # Get the upload session
        upload_session = await db.get(UploadSession, session_id)
        if not upload_session:
            raise HTTPException(status_code=404, detail="Upload session not found")

        # Delete all staged data associated with this session
        from app.utils.database import DatabaseUtils
        from app.model.tier import Tier
        from app.model.tier_group import TierGroup
        from app.model.tier_section import TierSection

        # Delete staged tier groups
        await DatabaseUtils.delete_by_filter(
            db, TierGroup, session_id=session_id, is_staged=True
        )

        # Delete staged tier sections
        await DatabaseUtils.delete_by_filter(
            db, TierSection, session_id=session_id, is_staged=True
        )

        # Delete staged tiers
        await DatabaseUtils.delete_by_filter(
            db, Tier, session_id=session_id, is_staged=True
        )

        # Delete the upload session
        await db.delete(upload_session)

        await db.commit()

        logger.info(f"Upload session {session_id} cancelled and staged data cleaned up")

        return {"message": "Upload cancelled successfully"}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error cancelling upload: {str(e)}")
        await db.rollback()
        raise HTTPException(
            status_code=500, detail=f"Error cancelling upload: {str(e)}"
        )


@router.delete("/cleanup-expired")
async def cleanup_expired_sessions(
    db: AsyncSession = Depends(get_db_dep),
):
    """
    Clean up expired upload sessions and their associated staged data and temp files.
    This endpoint can be called periodically to remove abandoned uploads.
    """
    try:
        import os
        import shutil
        from datetime import datetime, timedelta
        from app.utils.database import DatabaseUtils

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

            # Delete staged data for this session
            await DatabaseUtils.delete_by_filter(
                db, Tier, session_id=session_id, is_staged=True
            )
            await DatabaseUtils.delete_by_filter(
                db, TierGroup, session_id=session_id, is_staged=True
            )
            await DatabaseUtils.delete_by_filter(
                db, TierSection, session_id=session_id, is_staged=True
            )

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
        logger.error(f"Error cleaning up expired sessions: {str(e)}")
        await db.rollback()
        raise HTTPException(
            status_code=500, detail=f"Error cleaning up expired sessions: {str(e)}"
        )
