"""File processing utilities for ELAN files."""

from decimal import Decimal
from pathlib import Path

from lxml import etree as ET

from app.core.centralized_logging import get_logger

logger = get_logger()


class ElanFileProcessor:
    """Utilities for processing ELAN XML files."""

    @staticmethod
    def validate_elan_file(file_path: str) -> Path:
        """Validate and return Path object for ELAN file."""
        file_path_obj = Path(file_path)
        logger.info(f"Validating ELAN file: {file_path}")
        if not file_path_obj.exists():
            logger.error(f"ELAN file not found: {file_path}")
            raise FileNotFoundError(f"ELAN file not found: {file_path}")
        if file_path_obj.suffix.lower() != ".eaf":
            logger.error(f"Not an ELAN file: {file_path}")
            raise ValueError(f"Not an ELAN file: {file_path}")
        logger.debug(f"ELAN file validated: {file_path_obj}")
        return file_path_obj

    @staticmethod
    def get_file_info(file_path_obj: Path) -> dict:
        """Extract basic file information."""
        info = {
            "filename": file_path_obj.name,
            "file_path": str(file_path_obj.absolute()),
            "file_size": file_path_obj.stat().st_size,
        }
        logger.info(f"Extracted file info: {info}")
        return info

    @staticmethod
    def extract_time_slots(root: ET._Element) -> dict[str, int]:
        """Extract time slots from ELAN XML root."""
        time_slots = {}
        for time_slot in root.findall(".//TIME_SLOT", namespaces=None):
            slot_id = time_slot.get("TIME_SLOT_ID", None)
            time_value = int(time_slot.get("TIME_VALUE", 0))
            if slot_id:
                time_slots[slot_id] = time_value
        logger.debug(f"Extracted {len(time_slots)} time slots")
        return time_slots

    @staticmethod
    def safe_get_text(element: ET._Element | None) -> str | None:
        """Safely get text from XML element."""
        if element is None or not element.text:
            logger.warning("safe_get_text: element is None or empty")
            return None
        text = element.text.strip()
        logger.debug(f"safe_get_text: '{text}'")
        return text

    @staticmethod
    def convert_time_to_decimal(time_value: int) -> Decimal:
        """Convert milliseconds to decimal seconds."""
        decimal_time = Decimal(time_value) / 1000
        logger.debug(f"convert_time_to_decimal: {time_value}ms -> {decimal_time}s")
        return decimal_time

    @staticmethod
    def find_files_in_directory(
        directory_path: str, pattern: str = "**/*.eaf"
    ) -> list[Path]:
        """Find all ELAN files in directory."""
        directory = Path(directory_path)
        logger.info(
            f"Searching for ELAN files in directory: {directory_path} with pattern: {pattern}"
        )
        if not directory.exists():
            logger.error(f"Directory not found: {directory_path}")
            raise FileNotFoundError(f"Directory not found: {directory_path}")
        files = list(directory.glob(pattern))
        logger.info(f"Found {len(files)} ELAN files in directory")
        return files

    @staticmethod
    def extract_media_descriptors(root: ET._Element) -> list[dict]:
        """Extract all MEDIA_DESCRIPTOR elements from ELAN XML root."""
        media_descriptors = []
        for media_elem in root.findall(".//MEDIA_DESCRIPTOR", namespaces=None):
            media_info = {
                "media_url": media_elem.get("MEDIA_URL"),
                "mime_type": media_elem.get("MIME_TYPE"),
                "relative_media_url": media_elem.get("RELATIVE_MEDIA_URL"),
            }
            media_descriptors.append(media_info)
        logger.info(f"Extracted {len(media_descriptors)} media descriptors")
        return media_descriptors


class XmlAttributeExtractor:
    """Utilities for extracting attributes from XML elements."""

    @staticmethod
    def get_tier_attributes(tier_element: ET._Element) -> dict:
        """Extract tier attributes from XML element."""
        attrs = {
            "tier_name": tier_element.get("TIER_ID", None),
            "parent_tier_name": tier_element.get("PARENT_REF", None),
        }
        logger.debug(f"Extracted tier attributes: {attrs}")
        return attrs

    @staticmethod
    def get_annotation_attributes(annotation: ET._Element) -> dict:
        """Extract annotation attributes from XML element."""
        attrs = {
            "annotation_id": annotation.get("ANNOTATION_ID", None),
            "time_slot_ref1": annotation.get("TIME_SLOT_REF1", None),
            "time_slot_ref2": annotation.get("TIME_SLOT_REF2", None),
        }
        logger.debug(f"Extracted annotation attributes: {attrs}")
        return attrs

    @staticmethod
    def get_alignable_annotation_attributes(
        annotation: ET._Element, time_slots: dict[str, int]
    ) -> dict | None:
        """Extract information from an alignable annotation."""
        annotation_value_elem = annotation.find("ANNOTATION_VALUE", namespaces=None)
        if annotation_value_elem is None or not annotation_value_elem.text:
            logger.warning(
                "get_alignable_annotation_attributes: missing annotation value"
            )
            return None
        start_ref = annotation.get("TIME_SLOT_REF1", None)
        end_ref = annotation.get("TIME_SLOT_REF2", None)
        start_time = time_slots.get(start_ref, 0) if start_ref else 0
        end_time = time_slots.get(end_ref, 0) if end_ref else 0
        attrs = {
            "annotation_id": annotation.get("ANNOTATION_ID", None),
            "annotation_value": annotation_value_elem.text.strip(),
            "start_time": Decimal(start_time) / 1000,
            "end_time": Decimal(end_time) / 1000,
        }
        logger.debug(f"Extracted alignable annotation: {attrs}")
        return attrs

    @staticmethod
    def get_ref_annotation_attributes(
        annotation: ET._Element,
    ) -> dict | None:
        """Extract information from a reference annotation."""
        annotation_value_elem = annotation.find("ANNOTATION_VALUE", namespaces=None)
        if annotation_value_elem is None or not annotation_value_elem.text:
            logger.warning("get_ref_annotation_attributes: missing annotation value")
            return None
        attrs = {
            "annotation_id": annotation.get("ANNOTATION_ID", None),
            "annotation_value": annotation_value_elem.text.strip(),
            "start_time": Decimal(0),
            "end_time": Decimal(0),
        }
        logger.debug(f"Extracted ref annotation: {attrs}")
        return attrs
