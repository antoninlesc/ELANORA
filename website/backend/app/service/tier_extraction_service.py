"""
tier_extraction_service.py

Service for extracting tiers from uploaded ELAN files.
"""

import tempfile
import os
from typing import List, Dict, Any
from fastapi import UploadFile

from app.core.centralized_logging import get_logger
from app.utils.tier_extraction_utils import TierExtractor

logger = get_logger()


async def extract_tiers_from_files(
    files: List[UploadFile],
    project_id: int,
    session_id: str,
    db=None,  # Database session for creating staged entries
) -> List[Dict[str, Any]]:
    """
    Extract tiers from uploaded ELAN files and create staged database entries.

    Args:
        files: List of uploaded files
        project_id: Project ID
        db: Database session (required for creating staged entries)
        session_id: Upload session ID

    Returns:
        List of extracted tier information
    """
    if db is None:
        raise ValueError("Database session is required for tier extraction")

    extracted_tiers = []

    for file in files:
        try:
            # Save file temporarily
            with tempfile.NamedTemporaryFile(delete=False, suffix=".eaf") as temp_file:
                content = await file.read()
                temp_file.write(content)
                temp_file_path = temp_file.name

            try:
                # Extract tiers using the reusable utility
                tiers = TierExtractor.extract_tiers_from_elan_file(temp_file_path)

                # Create staged database entries
                for tier_data in tiers:
                    # Create or get tier (staged)
                    from app.crud.tier import get_tier_by_name, create_tier_in_db

                    existing_tier = await get_tier_by_name(
                        db, tier_data["tier_name"], include_staged=True
                    )
                    if not existing_tier:
                        # Create new staged tier
                        tier = await create_tier_in_db(
                            db,
                            tier_name=tier_data["tier_name"],
                            parent_tier_id=None,  # Will be set later in assignment step
                            is_staged=True,
                            session_id=session_id,
                        )
                    else:
                        tier = existing_tier

                    # Format for our response
                    extracted_tiers.append(
                        {
                            "tier_id": tier.tier_id,
                            "tier_name": tier_data["tier_name"],
                            "parent_tier_name": tier_data.get("parent_tier_name"),
                            "file_name": file.filename,
                            "session_id": session_id,
                        }
                    )

            finally:
                # Clean up temp file
                os.unlink(temp_file_path)

        except Exception as e:
            logger.error(f"Error processing file {file.filename}: {str(e)}")
            continue

    return extracted_tiers
