"""tier_extraction_service.py

Enhanced service for extracting tiers from uploaded ELAN files using modular extractors.
"""

import os
import tempfile
from typing import Any

from fastapi import UploadFile

from app.core.centralized_logging import get_logger
from app.utils.elan_processor import ElanFileCoordinator

logger = get_logger()


async def extract_tiers_from_files(
    files: list[UploadFile],
    project_id: int,
    session_id: str,
    db=None,  # Database session for creating staged entries
) -> list[dict[str, Any]]:
    """Extract tiers from uploaded ELAN files and create staged database entries.

    Args:
        files: List of uploaded files
        project_id: Project ID
        db: Database session (required for creating staged entries)
        session_id: Upload session ID

    Returns:
        List of extracted tier information with enhanced metadata

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
                # Extract tiers using the new modular processor - only get tiers for efficiency
                processor = ElanFileCoordinator(temp_file_path)
                result = processor.process_selective(["tiers", "metadata"])
                tiers = result.get("tiers", [])
                metadata = result.get("metadata", {})

                # Create staged database entries
                for tier_data in tiers:
                    # Create or get tier (staged)
                    from app.crud.tier import create_tier_in_db, get_tier_by_name

                    tier_name = tier_data["tier_name"]
                    if not tier_name:
                        continue

                    existing_tier = await get_tier_by_name(
                        db, tier_name, include_staged=True
                    )
                    if not existing_tier:
                        # Create new staged tier
                        tier = await create_tier_in_db(
                            db,
                            tier_name=tier_name,
                            parent_tier_id=None,  # Will be set later in assignment step
                            is_staged=True,
                            session_id=session_id,
                        )
                    else:
                        tier = existing_tier

                    # Format for our response with enhanced metadata
                    extracted_tiers.append(
                        {
                            "tier_id": tier.tier_id,
                            "tier_name": tier_name,
                            "parent_tier_name": tier_data.get("parent_tier_name"),
                            "linguistic_type": tier_data.get("linguistic_type"),
                            "participant": tier_data.get("participant"),
                            "annotator": tier_data.get("annotator"),
                            "annotation_count": len(tier_data.get("annotations", [])),
                            "file_name": file.filename,
                            "session_id": session_id,
                            "file_statistics": metadata.get("statistics", {}),
                        }
                    )

                logger.info(f"Extracted {len(tiers)} tiers from {file.filename}")

            finally:
                # Clean up temp file
                os.unlink(temp_file_path)

        except Exception as e:
            logger.error(f"Error processing file {file.filename}: {e!s}")
            continue

    logger.info(
        f"Total extracted tiers: {len(extracted_tiers)} from {len(files)} files"
    )
    return extracted_tiers
