"""Coordinated ELAN file processing with modular extractors.

This module provides a unified interface for processing ELAN files using the
modular extractor components. It supports both complete processing and selective
component extraction for performance optimization.
"""

import time
from pathlib import Path
from typing import Dict, Any, List, Optional, Union

from lxml import etree
from app.core.centralized_logging import get_logger
from app.utils.elan_extractors import (
    MediaExtractor,
    TimeSlotExtractor,
    TierExtractor,
    AnnotationExtractor,
    MetadataExtractor,
    LinguisticTypeExtractor,
)
from app.utils.file_processing import ElanFileProcessor as BaseElanFileProcessor

logger = get_logger()


class ElanFileCoordinator:
    """Coordinated processor for complete ELAN file extraction.

    This class provides both complete and selective processing capabilities,
    allowing clients to extract only the components they need for better performance.
    """

    def __init__(self, file_path: Union[str, Path]):
        """Initialize processor with ELAN file path.

        Args:
            file_path: Path to the ELAN file to process

        Raises:
            FileNotFoundError: If file doesn't exist
            ValueError: If file is not a valid ELAN file
        """
        self.file_path_obj = BaseElanFileProcessor.validate_elan_file(str(file_path))
        self.root: Optional[Any] = None
        self.time_slots: Dict[str, int] = {}
        self._parsed = False

        logger.info(f"Initialized ElanFileProcessor for {self.file_path_obj}")

    def process_complete(self) -> Dict[str, Any]:
        """Process entire ELAN file and return all extracted data.

        Returns:
            Dictionary containing:
            - file_info: Basic file information
            - metadata: File metadata and document info
            - time_slots: Time slot mappings
            - media: Media descriptor information
            - tiers: Tier information with annotations
            - annotations: Annotations grouped by tier
            - linguistic_types: Linguistic type definitions
        """
        logger.info(f"Starting complete processing of {self.file_path_obj}")
        start_time = time.perf_counter()

        # Parse XML if not already done
        self._ensure_parsed()

        # Extract all components
        result = {
            "file_info": self._extract_file_info(),
            "metadata": self._extract_metadata(),
            "time_slots": self._extract_time_slots(),
            "media": self._extract_media(),
            "tiers": self._extract_tiers(),
            "annotations": self._extract_annotations(),
            "linguistic_types": self._extract_linguistic_types(),
        }

        processing_time = time.perf_counter() - start_time
        logger.info(
            f"Completed processing of {self.file_path_obj} in {processing_time:.3f}s"
        )
        return result

    def process_selective(self, components: List[str]) -> Dict[str, Any]:
        """Process only specified components for better performance.

        Args:
            components: List of component names to extract. Valid values:
                       'file_info', 'metadata', 'time_slots', 'media',
                       'tiers', 'annotations', 'linguistic_types'

        Returns:
            Dictionary containing only the requested components
        """
        logger.info(
            f"Processing selective components {components} from {self.file_path_obj}"
        )
        start_time = time.perf_counter()

        # Parse XML if needed
        if any(
            comp in components
            for comp in [
                "metadata",
                "time_slots",
                "media",
                "tiers",
                "annotations",
                "linguistic_types",
            ]
        ):
            self._ensure_parsed()

        result = {}

        # Process components in dependency order
        if "file_info" in components:
            result["file_info"] = self._extract_file_info()

        if "time_slots" in components:
            result["time_slots"] = self._extract_time_slots()

        if "metadata" in components:
            result["metadata"] = self._extract_metadata()

        if "media" in components:
            result["media"] = self._extract_media()

        if "linguistic_types" in components:
            result["linguistic_types"] = self._extract_linguistic_types()

        # These components depend on time_slots
        if "tiers" in components or "annotations" in components:
            if not self.time_slots:
                self._extract_time_slots()

        if "tiers" in components:
            result["tiers"] = self._extract_tiers()

        if "annotations" in components:
            result["annotations"] = self._extract_annotations()

        processing_time = time.perf_counter() - start_time
        logger.info(f"Completed selective processing in {processing_time:.3f}s")
        return result

    def _ensure_parsed(self) -> None:
        """Ensure the XML file has been parsed."""
        if not self._parsed:
            logger.debug(f"Parsing XML from {self.file_path_obj}")
            parse_start = time.perf_counter()

            # Parse XML
            tree = etree.parse(str(self.file_path_obj))
            self.root = tree.getroot()
            self._parsed = True

            parse_time = time.perf_counter() - parse_start
            logger.debug(f"XML parsing took {parse_time:.3f}s")

    def _extract_file_info(self) -> Dict[str, Any]:
        """Extract basic file information."""
        return BaseElanFileProcessor.get_file_info(self.file_path_obj)

    def _extract_time_slots(self) -> Dict[str, int]:
        """Extract and cache time slots."""
        if not self.time_slots:
            extractor = TimeSlotExtractor(self.root, self.file_path_obj)
            self.time_slots = extractor.extract()
        return self.time_slots

    def _extract_metadata(self) -> Dict[str, Any]:
        """Extract metadata."""
        extractor = MetadataExtractor(self.root, self.file_path_obj)
        return extractor.extract()

    def _extract_media(self) -> List[Dict[str, str]]:
        """Extract media descriptors."""
        extractor = MediaExtractor(self.root, self.file_path_obj)
        return extractor.extract()

    def _extract_tiers(self) -> List[Dict[str, Any]]:
        """Extract tiers with annotations."""
        self._extract_time_slots()  # Ensure time slots are loaded
        extractor = TierExtractor(self.root, self.file_path_obj, self.time_slots)
        return extractor.extract()

    def _extract_annotations(self) -> Dict[str, List[Dict[str, Any]]]:
        """Extract annotations grouped by tier."""
        self._extract_time_slots()  # Ensure time slots are loaded
        extractor = AnnotationExtractor(self.root, self.file_path_obj, self.time_slots)
        return extractor.extract()

    def _extract_linguistic_types(self) -> List[Dict[str, Any]]:
        """Extract linguistic types."""
        extractor = LinguisticTypeExtractor(self.root, self.file_path_obj)
        return extractor.extract()
