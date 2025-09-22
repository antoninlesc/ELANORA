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

        # Update session with confirmation data
        upload_session.status = "pending_approval"
        upload_session.description = description

        # TODO: Store tier assignments and new section names
        # For now, we'll store them as JSON in the description or add fields later
        # This data will be used by admins when approving the upload

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
