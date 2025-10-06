"""tier_extraction_utils.py

DEPRECATED: This module is being phased out in favor of the new modular extractors.
Use app.utils.elan_extractors and app.utils.elan_processor instead.

Legacy utilities for extracting tier information from ELAN files.
"""

import warnings
from pathlib import Path

from app.core.centralized_logging import get_logger
from app.utils.elan_processor import ElanFileCoordinator

logger = get_logger()


class TierExtractor:
    """DEPRECATED: Use app.utils.elan_extractors.TierExtractor instead."""

    @staticmethod
    def extract_tiers_from_elan_file(file_path: str) -> list[dict]:
        """Extract all tiers from an ELAN file.

        DEPRECATED: Use ElanFileCoordinator.process_selective(['tiers']) instead.

        Args:
            file_path: Path to the ELAN file

        Returns:
            List of tier dictionaries with tier information

        """
        warnings.warn(
            "TierExtractor.extract_tiers_from_elan_file is deprecated. "
            "Use app.utils.elan_processor.ElanFileCoordinator instead.",
            DeprecationWarning,
            stacklevel=2,
        )

        # Use the new modular processor
        processor = ElanFileCoordinator(file_path)
        result = processor.process_selective(["tiers"])
        return result.get("tiers", [])

    @staticmethod
    def extract_time_slots(file_path: str) -> dict[str, int]:
        """DEPRECATED: Use ElanFileCoordinator.process_selective(['time_slots']) instead."""
        warnings.warn(
            "TierExtractor.extract_time_slots is deprecated. "
            "Use app.utils.elan_processor.ElanFileCoordinator instead.",
            DeprecationWarning,
            stacklevel=2,
        )

        processor = ElanFileCoordinator(file_path)
        result = processor.process_selective(["time_slots"])
        return result.get("time_slots", {})

    @staticmethod
    def extract_media_descriptors(file_path: str) -> list[dict]:
        """DEPRECATED: Use ElanFileCoordinator.process_selective(['media']) instead."""
        warnings.warn(
            "TierExtractor.extract_media_descriptors is deprecated. "
            "Use app.utils.elan_processor.ElanFileCoordinator instead.",
            DeprecationWarning,
            stacklevel=2,
        )

        processor = ElanFileCoordinator(file_path)
        result = processor.process_selective(["media"])
        return result.get("media", [])

    @staticmethod
    def extract_linguistic_types(file_path: str) -> list[dict]:
        """DEPRECATED: Use ElanFileCoordinator.process_selective(['linguistic_types']) instead."""
        warnings.warn(
            "TierExtractor.extract_linguistic_types is deprecated. "
            "Use app.utils.elan_processor.ElanFileCoordinator instead.",
            DeprecationWarning,
            stacklevel=2,
        )

        processor = ElanFileCoordinator(file_path)
        result = processor.process_selective(["linguistic_types"])
        return result.get("linguistic_types", [])
