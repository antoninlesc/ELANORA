"""upload_session_service.py

Service layer for upload session operations.
"""

import json
import uuid
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.centralized_logging import get_logger
from app.crud.tier import get_tier_id_by_name
from app.crud.tier_group import create_tier_group
from app.crud.tier_section import create_tier_section
from app.crud.upload_session import (
    create_upload_session,
    delete_upload_session,
    get_upload_session_by_id,
    update_upload_session,
)
from app.service.tier_extraction_service import extract_tiers_from_files

logger = get_logger()


async def create_upload_session_service(
    db: AsyncSession, project_id: int, description: str | None = None
) -> str:
    """Create a new upload session and return the session ID."""
    session_id = str(uuid.uuid4())
    await create_upload_session(
        db, session_id=session_id, project_id=project_id, description=description
    )
    await db.commit()
    return session_id


async def process_upload_files_service(
    db: AsyncSession, files: list, project_id: int
) -> dict[str, Any]:
    """Process uploaded files for tier extraction."""
    session_id = await create_upload_session_service(db, project_id)

    # Extract tiers from files (creates staged DB entries)
    extracted_tiers = await extract_tiers_from_files(files, project_id, session_id, db)

    # Update session status to completed
    await update_upload_session(db, session_id, {"status": "completed"})
    await db.commit()

    return {"session_id": session_id, "extracted_tiers": extracted_tiers}


async def confirm_upload_service(
    db: AsyncSession,
    session_id: str,
    tier_assignments: list[dict],
    new_section_names: list[str],
    description: str,
) -> dict[str, str]:
    """Confirm and finalize the upload."""
    upload_session = await get_upload_session_by_id(db, session_id)
    if not upload_session:
        raise ValueError("Upload session not found")
    if upload_session.status != "completed":
        raise ValueError("Upload session is not in completed status")

    # Create new sections if specified
    section_mapping = {}  # section_name -> tier_section_id
    for section_name in new_section_names:
        tier_section = await create_tier_section(
            db,
            upload_session.project_id,
            section_name,
            is_staged=True,
            session_id=session_id,
        )
        section_mapping[section_name] = tier_section.tier_section_id

    # Create tier groups based on assignments
    for assignment in tier_assignments:
        tier_name = assignment["tier_name"]
        section_name = assignment.get("section_name")

        # Get tier_id from tier_name
        tier_id = await get_tier_id_by_name(db, tier_name, include_staged=True)
        if not tier_id:
            raise ValueError(f"Tier '{tier_name}' not found")

        # Get section_id from mapping, or None if not assigned to a section
        section_id = section_mapping.get(section_name) if section_name else None

        # Create tier group (staged)
        await create_tier_group(
            db,
            section_id=section_id,
            project_id=upload_session.project_id,
            tier_id=tier_id,
            tier_name=tier_name,
            is_staged=True,
            session_id=session_id,
        )

    # Update session
    await update_upload_session(
        db, session_id, {"status": "pending_approval", "description": description}
    )
    await db.commit()

    return {
        "message": "Upload confirmed successfully and is now pending administrator approval"
    }


async def cancel_upload_service(db: AsyncSession, session_id: str) -> dict[str, str]:
    """Cancel an upload session and clean up staged data."""
    upload_session = await get_upload_session_by_id(db, session_id)
    if not upload_session:
        raise ValueError("Upload session not found")

    # Delete staged data (using existing cleanup functions)
    from app.crud.tier import delete_tiers_for_session
    from app.crud.tier_group import delete_tier_groups_for_session
    from app.crud.tier_section import delete_tier_sections_for_session

    await delete_tiers_for_session(db, session_id)
    await delete_tier_groups_for_session(db, session_id)
    await delete_tier_sections_for_session(db, session_id)

    # Delete the session
    await delete_upload_session(db, session_id)
    await db.commit()

    return {"message": "Upload cancelled and cleaned up successfully"}
