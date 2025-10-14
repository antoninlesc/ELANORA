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
            # Extract annotation attributes preserving time slot references for XML generation
            annotation_value_elem = annotation.find("ANNOTATION_VALUE", namespaces=None)
            if annotation_value_elem is not None and annotation_value_elem.text:
                ann_data = {
                    "annotation_id": annotation.get("ANNOTATION_ID", ""),
                    "time_slot_ref1": annotation.get("TIME_SLOT_REF1", ""),
                    "time_slot_ref2": annotation.get("TIME_SLOT_REF2", ""),
                    "annotation_value": annotation_value_elem.text.strip(),
                }
                annotations.append(ann_data)

        # Extract reference annotations
        for annotation in tier_element.findall(".//REF_ANNOTATION", namespaces=None):
            annotation_value_elem = annotation.find("ANNOTATION_VALUE", namespaces=None)
            if annotation_value_elem is not None and annotation_value_elem.text:
                ann_data = {
                    "annotation_id": annotation.get("ANNOTATION_ID", ""),
                    "annotation_ref": annotation.get("ANNOTATION_REF", ""),
                    "annotation_value": annotation_value_elem.text.strip(),
                }
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
                "controlled_vocabulary_ref": ling_type.get("CONTROLLED_VOCABULARY_REF"),
                "ext_ref": ling_type.get("EXT_REF"),
                "lexicon_ref": ling_type.get("LEXICON_REF"),
            }
            # Remove None values for cleaner output
            type_info = {k: v for k, v in type_info.items() if v is not None}
            linguistic_types.append(type_info)

        logger.info(f"Extracted {len(linguistic_types)} linguistic types")
        return linguistic_types


class LinkedFileExtractor(BaseElanExtractor):
    """Extract linked file descriptor information from ELAN files."""

    def extract(self) -> List[Dict[str, Any]]:
        """Extract all linked file descriptors from ELAN file header.

        Returns:
            List of linked file descriptor dictionaries with keys:
            - link_url: URL/path to linked file
            - relative_link_url: Relative path to linked file
            - mime_type: MIME type of linked file
            - time_origin: Time origin (optional)
            - associated_with: Associated media (optional)
        """
        logger.info(f"Extracting linked file descriptors from {self.file_path}")

        linked_files = []
        for lfd_elem in self.root.findall(".//LINKED_FILE_DESCRIPTOR", namespaces=None):
            link_url = lfd_elem.get("LINK_URL")

            # Skip if no link URL
            if not link_url:
                logger.debug("Skipping linked file descriptor without LINK_URL")
                continue

            linked_file_info = {
                "link_url": link_url,
                "relative_link_url": lfd_elem.get("RELATIVE_LINK_URL"),
                "mime_type": lfd_elem.get("MIME_TYPE"),
                "time_origin": lfd_elem.get("TIME_ORIGIN"),
                "associated_with": lfd_elem.get("ASSOCIATED_WITH"),
            }
            # Remove None values for cleaner output
            linked_file_info = {
                k: v for k, v in linked_file_info.items() if v is not None
            }
            linked_files.append(linked_file_info)

        logger.info(f"Extracted {len(linked_files)} linked file descriptors")
        return linked_files


class PropertyExtractor(BaseElanExtractor):
    """Extract property information from ELAN files."""

    def extract(self) -> List[Dict[str, str]]:
        """Extract all properties from ELAN file header.

        Returns:
            List of property dictionaries with keys:
            - name: Property name
            - value: Property value (optional)
        """
        logger.info(f"Extracting properties from {self.file_path}")

        properties = []
        for prop_elem in self.root.findall(".//PROPERTY", namespaces=None):
            prop_name = prop_elem.get("NAME")

            # Skip if no property name
            if not prop_name:
                logger.debug("Skipping property without NAME")
                continue

            property_info = {
                "name": prop_name,
                "value": prop_elem.text or prop_elem.get("VALUE", ""),
            }
            properties.append(property_info)

        logger.info(f"Extracted {len(properties)} properties")
        return properties


class ControlledVocabularyExtractor(BaseElanExtractor):
    """Extract CONTROLLED_VOCABULARY elements from ELAN XML."""

    def extract(self) -> List[Dict[str, Any]]:
        """Extract all CONTROLLED_VOCABULARY elements.

        Returns:
            List of controlled vocabulary dictionaries with keys:
            - cv_id: Controlled vocabulary ID
            - description: Description text (may be empty)
            - description_lang: Language reference for description (defaults to 'und')
            - entries: List of CV entries
            - ext_ref: External reference (optional)
        """
        logger.info(f"Extracting controlled vocabularies from {self.file_path}")

        vocabularies = []
        for cv in self.root.findall(".//CONTROLLED_VOCABULARY", namespaces=None):
            cv_data = {
                "cv_id": cv.get("CV_ID", ""),
                "ext_ref": cv.get("EXT_REF", ""),
                "description": "",
                "description_lang": "und",  # Default to 'und' as per ELAN convention
                "entries": [],
            }

            # Extract description - ALWAYS preserve it even if empty
            # According to EAF v3.0 schema, DESCRIPTION should come before CV_ENTRY_ML
            desc_elem = cv.find("DESCRIPTION")
            if desc_elem is not None:
                cv_data["description"] = desc_elem.text or ""
                cv_data["description_lang"] = desc_elem.get("LANG_REF", "und")

            # Extract CV entries
            for entry in cv.findall("CV_ENTRY_ML"):
                entry_data = {"cve_id": entry.get("CVE_ID", ""), "values": []}

                # Extract CV values
                for value in entry.findall("CVE_VALUE"):
                    value_data = {
                        "lang_ref": value.get("LANG_REF", "und"),  # Default to 'und'
                        "description": value.get("DESCRIPTION", ""),
                        "value": value.text or "",
                    }
                    entry_data["values"].append(value_data)

                cv_data["entries"].append(entry_data)

            vocabularies.append(cv_data)

        logger.info(f"Extracted {len(vocabularies)} controlled vocabularies")
        return vocabularies


class LanguageExtractor(BaseElanExtractor):
    """Extract LANGUAGE elements from ELAN XML."""

    def extract(self) -> List[Dict[str, Any]]:
        """Extract all LANGUAGE elements.

        Returns:
            List of language dictionaries with keys:
            - lang_id: Language ID
            - lang_def: Language definition URL
            - lang_label: Language label
        """
        logger.info(f"Extracting languages from {self.file_path}")

        languages = []
        for lang in self.root.findall(".//LANGUAGE", namespaces=None):
            lang_data = {
                "lang_id": lang.get("LANG_ID", ""),
                "lang_def": lang.get("LANG_DEF", ""),
                "lang_label": lang.get("LANG_LABEL", ""),
            }
            languages.append(lang_data)

        logger.info(f"Extracted {len(languages)} languages")
        return languages


class ExternalRefExtractor(BaseElanExtractor):
    """Extract EXTERNAL_REF elements from ELAN XML."""

    def extract(self) -> List[Dict[str, Any]]:
        """Extract all EXTERNAL_REF elements.

        Returns:
            List of external reference dictionaries with keys:
            - ext_ref_id: External reference ID
            - type: Reference type
            - value: Reference value/URL
        """
        logger.info(f"Extracting external references from {self.file_path}")

        external_refs = []
        for ext_ref in self.root.findall(".//EXTERNAL_REF", namespaces=None):
            ref_data = {
                "ext_ref_id": ext_ref.get("EXT_REF_ID", ""),
                "type": ext_ref.get("TYPE", ""),
                "value": ext_ref.get("VALUE", ""),
            }
            external_refs.append(ref_data)

        logger.info(f"Extracted {len(external_refs)} external references")
        return external_refs


class LocaleExtractor(BaseElanExtractor):
    """Extract LOCALE elements from ELAN XML."""

    def extract(self) -> List[Dict[str, Any]]:
        """Extract all LOCALE elements.

        Returns:
            List of locale dictionaries with keys:
            - country_code: Country code
            - language_code: Language code
        """
        logger.info(f"Extracting locales from {self.file_path}")

        locales = []
        for locale in self.root.findall(".//LOCALE", namespaces=None):
            locale_data = {
                "country_code": locale.get("COUNTRY_CODE", ""),
                "language_code": locale.get("LANGUAGE_CODE", ""),
            }
            locales.append(locale_data)

        logger.info(f"Extracted {len(locales)} locales")
        return locales


class ConstraintExtractor(BaseElanExtractor):
    """Extract CONSTRAINT elements from ELAN XML."""

    def extract(self) -> List[Dict[str, Any]]:
        """Extract all CONSTRAINT elements.

        Returns:
            List of constraint dictionaries with keys:
            - stereotype: Constraint stereotype
            - description: Constraint description
        """
        logger.info(f"Extracting constraints from {self.file_path}")

        constraints = []
        for constraint in self.root.findall(".//CONSTRAINT", namespaces=None):
            constraint_data = {
                "stereotype": constraint.get("STEREOTYPE", ""),
                "description": constraint.get("DESCRIPTION", ""),
            }
            constraints.append(constraint_data)

        logger.info(f"Extracted {len(constraints)} constraints")
        return constraints
