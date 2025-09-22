"""
upload.py

API endpoints for file upload processing.
"""

from fastapi import APIRouter, UploadFile, File, Form, HTTPException
from typing import List
import uuid

from app.service.tier_extraction_service import extract_tiers_from_files

router = APIRouter(prefix="/upload", tags=["upload"])


@router.post("/process")
async def process_upload_files(
    files: List[UploadFile] = File(...), project_id: str = Form(...)
):
    """
    Process uploaded files for tier extraction.
    Returns extracted tiers without creating database entries yet.
    """
    try:
        # Generate session ID
        session_id = str(uuid.uuid4())

        # Extract tiers from files (no DB storage yet)
        extracted_tiers = await extract_tiers_from_files(
            files, int(project_id), session_id, None
        )

        return {"session_id": session_id, "extracted_tiers": extracted_tiers}

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error processing files: {str(e)}")


@router.post("/confirm")
async def confirm_upload(
    session_id: str = Form(...),
    tier_assignments: dict = Form(...),
    description: str = Form(...),
):
    """
    Confirm and finalize the upload.
    For now, just return success - actual implementation will be added later.
    """
    try:
        # TODO: Implement actual confirmation logic
        # For now, just return success
        return {"message": "Upload confirmed successfully"}

    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Error confirming upload: {str(e)}"
        )
