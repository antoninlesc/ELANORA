"""Modular ELAN file extractors for specific components.

This module provides a set of specialized extractors that can be used independently
or in combination to process different aspects of ELAN files. Each extractor follows
a consistent interface and can be tested in isolation.
"""

from abc import ABC, abstractmethod
from decimal import Decimal
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

from lxml import etree
from app.core.centralized_logging import get_logger
from app.utils.file_processing import ElanFileProcessor, XmlAttributeExtractor

logger = get_logger()


class BaseElanExtractor(ABC):
    """Base class for ELAN component extractors."""

    def __init__(self, root: Any, file_path: Path):
        self.root = root
        self.file_path = file_path
        logger.debug(f"Initialized {self.__class__.__name__} for {file_path}")

    @abstractmethod
    def extract(self) -> Any:
        """Extract specific component data from ELAN XML."""
        pass


class MediaExtractor(BaseElanExtractor):
    """Extract media descriptor information from ELAN files."""

    def extract(self) -> List[Dict[str, str]]:
        """Extract all media descriptors from ELAN file.

        Returns:
            List of media descriptor dictionaries with keys:
            - media_url: URL/path to media file
            - mime_type: MIME type of media
            - relative_media_url: Relative path to media
            - time_origin: Time origin (optional)
            - extracted_from: Source information (optional)
        """
        logger.info(f"Extracting media descriptors from {self.file_path}")

        media_descriptors = []
        for media_elem in self.root.findall(".//MEDIA_DESCRIPTOR", namespaces=None):
            media_url = media_elem.get("MEDIA_URL")

            # Skip media descriptors without media_url (database constraint requires it)
            if media_url is None:
                logger.debug("Skipping media descriptor without MEDIA_URL")
                continue

            media_info = {
                "media_url": media_url,
                "mime_type": media_elem.get("MIME_TYPE"),
                "relative_media_url": media_elem.get("RELATIVE_MEDIA_URL"),
            }
            media_descriptors.append(media_info)

        logger.info(f"Extracted {len(media_descriptors)} media descriptors")
        return media_descriptors


class TimeSlotExtractor(BaseElanExtractor):
    """Extract time slot information from ELAN files."""

    def extract(self) -> Dict[str, int]:
        """Extract all time slots from ELAN file.

        Returns:
            Dictionary mapping time slot IDs to time values (in milliseconds)
        """
        logger.info(f"Extracting time slots from {self.file_path}")
        return ElanFileProcessor.extract_time_slots(self.root)


class TierExtractor(BaseElanExtractor):
    """Extract tier information and structure from ELAN files."""

    def __init__(
        self, root: Any, file_path: Path, time_slots: Optional[Dict[str, int]] = None
    ):
        super().__init__(root, file_path)
        self.time_slots = time_slots or {}

    def extract(self) -> List[Dict[str, Any]]:
        """Extract all tiers with their annotations and metadata.

        Returns:
            List of tier dictionaries containing:
            - tier_name: Name/ID of the tier
            - parent_tier_name: Parent tier name (if any)
            - linguistic_type: Linguistic type reference
            - participant: Participant name
            - annotator: Annotator name
            - annotations: List of annotations for this tier
        """
        logger.info(f"Extracting tiers from {self.file_path}")

        # Ensure we have time slots
        if not self.time_slots:
            time_extractor = TimeSlotExtractor(self.root, self.file_path)
            self.time_slots = time_extractor.extract()

        tiers_data = []

        for tier_element in self.root.findall(".//TIER", namespaces=None):
            tier_info = self._extract_single_tier(tier_element)
            if tier_info:
                tiers_data.append(tier_info)

        logger.info(f"Extracted {len(tiers_data)} tiers from {self.file_path}")
        return tiers_data

    def _extract_single_tier(self, tier_element: Any) -> Optional[Dict[str, Any]]:
        """Extract data from a single tier element."""
        tier_name = tier_element.get("TIER_ID")

        if not tier_name:
            logger.warning("Skipping tier with no name")
            return None

        # Extract tier metadata
        tier_info = {
            "tier_name": tier_name,
            "parent_tier_name": tier_element.get("PARENT_REF"),
            "linguistic_type": tier_element.get("LINGUISTIC_TYPE_REF"),
            "participant": tier_element.get("PARTICIPANT"),
            "annotator": tier_element.get("ANNOTATOR"),
            "default_locale": tier_element.get("DEFAULT_LOCALE"),
            "annotations": self._extract_tier_annotations(tier_element),
        }

        # Remove None values for cleaner output
        tier_info = {
            k: v for k, v in tier_info.items() if v is not None or k == "annotations"
        }

        return tier_info

    def _extract_tier_annotations(self, tier_element: Any) -> List[Dict[str, Any]]:
        """Extract all annotations for a tier."""
        annotations = []

        # Extract alignable annotations
        for annotation in tier_element.findall(
            ".//ALIGNABLE_ANNOTATION", namespaces=None
        ):
            ann_data = XmlAttributeExtractor.get_alignable_annotation_attributes(
                annotation, self.time_slots
            )
            if ann_data:
                annotations.append(ann_data)

        # Extract reference annotations
        for annotation in tier_element.findall(".//REF_ANNOTATION", namespaces=None):
            ann_data = XmlAttributeExtractor.get_ref_annotation_attributes(annotation)
            if ann_data:
                annotations.append(ann_data)

        logger.debug(f"Extracted {len(annotations)} annotations from tier")
        return annotations


class AnnotationExtractor(BaseElanExtractor):
    """Extract annotation information across all tiers."""

    def __init__(
        self, root: Any, file_path: Path, time_slots: Optional[Dict[str, int]] = None
    ):
        super().__init__(root, file_path)
        self.time_slots = time_slots or {}

    def extract(self) -> Dict[str, List[Dict[str, Any]]]:
        """Extract all annotations grouped by tier.

        Returns:
            Dictionary mapping tier names to lists of annotations
        """
        logger.info(f"Extracting annotations from {self.file_path}")

        # Ensure we have time slots
        if not self.time_slots:
            time_extractor = TimeSlotExtractor(self.root, self.file_path)
            self.time_slots = time_extractor.extract()

        annotations_by_tier = {}

        for tier_element in self.root.findall(".//TIER", namespaces=None):
            tier_name = tier_element.get("TIER_ID")
            if not tier_name:
                continue

            annotations = self._extract_annotations_for_tier(tier_element)
            if annotations:
                annotations_by_tier[tier_name] = annotations

        total_annotations = sum(len(anns) for anns in annotations_by_tier.values())
        logger.info(
            f"Extracted {total_annotations} annotations across {len(annotations_by_tier)} tiers"
        )
        return annotations_by_tier

    def _extract_annotations_for_tier(self, tier_element: Any) -> List[Dict[str, Any]]:
        """Extract annotations for a specific tier element."""
        annotations = []

        # Process alignable annotations
        for annotation in tier_element.findall(
            ".//ALIGNABLE_ANNOTATION", namespaces=None
        ):
            ann_data = XmlAttributeExtractor.get_alignable_annotation_attributes(
                annotation, self.time_slots
            )
            if ann_data:
                annotations.append(ann_data)

        # Process reference annotations
        for annotation in tier_element.findall(".//REF_ANNOTATION", namespaces=None):
            ann_data = XmlAttributeExtractor.get_ref_annotation_attributes(annotation)
            if ann_data:
                annotations.append(ann_data)

        return annotations


class MetadataExtractor(BaseElanExtractor):
    """Extract ELAN file metadata and properties."""

    def extract(self) -> Dict[str, Any]:
        """Extract metadata from ELAN file header and document.

        Returns:
            Dictionary containing:
            - document: Document-level metadata (author, date, format, version)
            - header: Header information (media file, time units)
            - statistics: Basic counts (tiers, time slots, annotations)
            - linguistic_types: Available linguistic types
        """
        logger.info(f"Extracting metadata from {self.file_path}")

        metadata = {
            "document": self._extract_document_metadata(),
            "header": self._extract_header_info(),
            "statistics": self._calculate_statistics(),
            "linguistic_types": self._extract_linguistic_types(),
        }

        return metadata

    def _extract_document_metadata(self) -> Dict[str, str]:
        """Extract ANNOTATION_DOCUMENT attributes."""
        doc_metadata = {}

        if self.root.tag == "ANNOTATION_DOCUMENT":
            doc_metadata.update(
                {
                    "author": self.root.get("AUTHOR", ""),
                    "date": self.root.get("DATE", ""),
                    "format": self.root.get("FORMAT", ""),
                    "version": self.root.get("VERSION", ""),
                }
            )

        return {k: v for k, v in doc_metadata.items() if v}

    def _extract_header_info(self) -> Dict[str, Any]:
        """Extract HEADER information."""
        header_info = {}

        header = self.root.find(".//HEADER", namespaces=None)
        if header is not None:
            header_info = {
                "media_file": header.get("MEDIA_FILE", ""),
                "time_units": header.get("TIME_UNITS", "milliseconds"),
            }

        return {k: v for k, v in header_info.items() if v}

    def _calculate_statistics(self) -> Dict[str, int]:
        """Calculate basic statistics about the ELAN file."""
        return {
            "tier_count": len(self.root.findall(".//TIER", namespaces=None)),
            "time_slot_count": len(self.root.findall(".//TIME_SLOT", namespaces=None)),
            "alignable_annotation_count": len(
                self.root.findall(".//ALIGNABLE_ANNOTATION", namespaces=None)
            ),
            "ref_annotation_count": len(
                self.root.findall(".//REF_ANNOTATION", namespaces=None)
            ),
        }

    def _extract_linguistic_types(self) -> List[Dict[str, Any]]:
        """Extract linguistic type definitions."""
        linguistic_types = []

        for ling_type in self.root.findall(".//LINGUISTIC_TYPE", namespaces=None):
            type_info = {
                "linguistic_type_id": ling_type.get("LINGUISTIC_TYPE_ID"),
                "time_alignable": ling_type.get("TIME_ALIGNABLE") == "true",
                "constraints": ling_type.get("CONSTRAINTS"),
                "graphic_references": ling_type.get("GRAPHIC_REFERENCES") == "true",
                "controlled_vocabulary": ling_type.get("CONTROLLED_VOCABULARY"),
                "controlled_vocabulary_url": ling_type.get("CONTROLLED_VOCABULARY_URL"),
            }
            # Remove None values
            type_info = {k: v for k, v in type_info.items() if v is not None}
            linguistic_types.append(type_info)

        return linguistic_types


class LinguisticTypeExtractor(BaseElanExtractor):
    """Extract linguistic type information from ELAN files."""

    def extract(self) -> List[Dict[str, Any]]:
        """Extract all linguistic type definitions.

        Returns:
            List of linguistic type dictionaries
        """
        logger.info(f"Extracting linguistic types from {self.file_path}")

        linguistic_types = []
        for ling_type in self.root.findall(".//LINGUISTIC_TYPE", namespaces=None):
            type_info = {
                "linguistic_type_id": ling_type.get("LINGUISTIC_TYPE_ID"),
                "time_alignable": ling_type.get("TIME_ALIGNABLE") == "true",
                "constraints": ling_type.get("CONSTRAINTS"),
                "graphic_references": ling_type.get("GRAPHIC_REFERENCES") == "true",
                "controlled_vocabulary": ling_type.get("CONTROLLED_VOCABULARY"),
                "controlled_vocabulary_url": ling_type.get("CONTROLLED_VOCABULARY_URL"),
            }
            # Remove None values for cleaner output
            type_info = {k: v for k, v in type_info.items() if v is not None}
            linguistic_types.append(type_info)

        logger.info(f"Extracted {len(linguistic_types)} linguistic types")
        return linguistic_types
