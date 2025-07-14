"""File processing utilities for ELAN files."""

from lxml import etree as lxml_etree
from pathlib import Path
from typing import Dict, List, Optional
from decimal import Decimal


class ElanFileProcessor:
    """Utilities for processing ELAN XML files."""

    @staticmethod
    def validate_elan_file(file_path: str) -> Path:
        """Validate and return Path object for ELAN file."""
        file_path_obj = Path(file_path)

        if not file_path_obj.exists():
            raise FileNotFoundError(f"ELAN file not found: {file_path}")

        if file_path_obj.suffix.lower() != ".eaf":
            raise ValueError(f"Not an ELAN file: {file_path}")

        return file_path_obj

    @staticmethod
    def get_file_info(file_path_obj: Path) -> Dict:
        """Extract basic file information."""
        return {
            "filename": file_path_obj.name,
            "file_path": str(file_path_obj.absolute()),
            "file_size": file_path_obj.stat().st_size,
        }

    @staticmethod
    def extract_time_slots(root: lxml_etree._Element) -> Dict[str, int]:
        """Extract time slots from ELAN XML root."""
        time_slots = {}
        for time_slot in root.findall(".//TIME_SLOT", namespaces=None):
            slot_id = time_slot.get("TIME_SLOT_ID", None)
            time_value = int(time_slot.get("TIME_VALUE", 0))
            if slot_id:
                time_slots[slot_id] = time_value
        return time_slots

    @staticmethod
    def safe_get_text(element: Optional[lxml_etree._Element]) -> Optional[str]:
        """Safely get text from XML element."""
        if element is None or not element.text:
            return None
        return element.text.strip()

    @staticmethod
    def convert_time_to_decimal(time_value: int) -> Decimal:
        """Convert milliseconds to decimal seconds."""
        return Decimal(time_value) / 1000

    @staticmethod
    def find_files_in_directory(
        directory_path: str, pattern: str = "**/*.eaf"
    ) -> List[Path]:
        """Find all ELAN files in directory."""
        directory = Path(directory_path)

        if not directory.exists():
            raise FileNotFoundError(f"Directory not found: {directory}")

        return list(directory.glob(pattern))


class XmlAttributeExtractor:
    """Utilities for extracting attributes from XML elements."""

    @staticmethod
    def get_tier_attributes(tier_element: lxml_etree._Element) -> Dict:
        """Extract tier attributes from XML element."""
        return {
            "tier_id": tier_element.get("TIER_ID", None),
            "tier_name": tier_element.get("TIER_ID", None),
            "parent_tier_id": tier_element.get("PARENT_REF", None),
            "linguistic_type": tier_element.get("LINGUISTIC_TYPE_REF", None),
        }

    @staticmethod
    def get_annotation_attributes(annotation: lxml_etree._Element) -> Dict:
        """Extract annotation attributes from XML element."""
        return {
            "annotation_id": annotation.get("ANNOTATION_ID", None),
            "time_slot_ref1": annotation.get("TIME_SLOT_REF1", None),
            "time_slot_ref2": annotation.get("TIME_SLOT_REF2", None),
        }

    @staticmethod
    def get_alignable_annotation_attributes(
        annotation: lxml_etree._Element, time_slots: Dict[str, int]
    ) -> Optional[Dict]:
        """Extract information from an alignable annotation."""
        annotation_value_elem = annotation.find("ANNOTATION_VALUE", namespaces=None)
        if annotation_value_elem is None or not annotation_value_elem.text:
            return None

        start_ref = annotation.get("TIME_SLOT_REF1", None)
        end_ref = annotation.get("TIME_SLOT_REF2", None)

        start_time = time_slots.get(start_ref, 0) if start_ref else 0
        end_time = time_slots.get(end_ref, 0) if end_ref else 0

        return {
            "annotation_id": annotation.get("ANNOTATION_ID", None),
            "annotation_value": annotation_value_elem.text.strip(),
            "start_time": Decimal(start_time) / 1000,
            "end_time": Decimal(end_time) / 1000,
        }

    @staticmethod
    def get_ref_annotation_attributes(
        annotation: lxml_etree._Element,
    ) -> Optional[Dict]:
        """Extract information from a reference annotation."""
        annotation_value_elem = annotation.find("ANNOTATION_VALUE", namespaces=None)
        if annotation_value_elem is None or not annotation_value_elem.text:
            return None

        return {
            "annotation_id": annotation.get("ANNOTATION_ID", None),
            "annotation_value": annotation_value_elem.text.strip(),
            "start_time": Decimal(0),
            "end_time": Decimal(0),
        }
