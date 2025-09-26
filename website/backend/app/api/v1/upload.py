"""upload.py

API endpoints for file upload processing.
"""

from fastapi import APIRouter, File, Form, HTTPException, UploadFile
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.centralized_logging import get_logger
from app.dependency.database import get_db_dep
from app.schema.requests.upload import CancelUploadRequest, ConfirmUploadRequest
from app.schema.responses.upload import (
    CancelUploadResponse,
    CleanupExpiredResponse,
    ConfirmUploadResponse,
    ProcessUploadResponse,
)
from app.service.upload_session import (
    cancel_upload_service,
    confirm_upload_service,
    process_upload_files_service,
)

logger = get_logger()

router = APIRouter()


@router.post("/process", response_model=ProcessUploadResponse)
async def process_upload_files(
    files: list[UploadFile] = File(...),
    project_id: int = Form(...),
    db: AsyncSession = get_db_dep,
) -> ProcessUploadResponse:
    """Process uploaded files for tier extraction.
    Creates staged database entries and returns extracted tiers.
    """
    try:
        result = await process_upload_files_service(db, files, project_id)
        return ProcessUploadResponse(**result)
    except Exception as e:
        logger.error(f"Error processing upload files: {e!s}")
        raise HTTPException(status_code=500, detail=f"Error processing files: {e!s}")


@router.post("/confirm", response_model=ConfirmUploadResponse)
async def confirm_upload(
    request: ConfirmUploadRequest,
    db: AsyncSession = get_db_dep,
) -> ConfirmUploadResponse:
    """Confirm and finalize the upload by marking it as pending approval."""
    try:
        result = await confirm_upload_service(
            db,
            request.session_id,
            request.tier_assignments,
            request.new_section_names,
            request.description,
        )
        return ConfirmUploadResponse(**result)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error confirming upload: {e!s}")
        raise HTTPException(status_code=500, detail=f"Error confirming upload: {e!s}")


@router.post("/cancel", response_model=CancelUploadResponse)
async def cancel_upload(
    request: CancelUploadRequest,
    db: AsyncSession = get_db_dep,
) -> CancelUploadResponse:
    """Cancel an upload session and clean up all staged data."""
    try:
        result = await cancel_upload_service(db, request.session_id)
        return CancelUploadResponse(**result)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error cancelling upload: {e!s}")
        raise HTTPException(status_code=500, detail=f"Error cancelling upload: {e!s}")


@router.delete("/cleanup-expired", response_model=CleanupExpiredResponse)
async def cleanup_expired_sessions(
    db: AsyncSession = get_db_dep,
) -> CleanupExpiredResponse:
    """Clean up expired upload sessions and their associated staged data and temp files.
    This endpoint can be called periodically to remove abandoned uploads.
    """
    from app.service.upload_service import cleanup_expired_upload_sessions

    result = await cleanup_expired_upload_sessions(db)
    return CleanupExpiredResponse(**result)
