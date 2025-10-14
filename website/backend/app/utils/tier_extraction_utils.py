"""tier_extraction_utils.py

Reusable utilities for extracting tier information from ELAN files.
"""

from pathlib import Path

from lxml import etree

from app.core.centralized_logging import get_logger

logger = get_logger()


class TierExtractor:
    """Reusable class for extracting tier information from ELAN XML."""

    @staticmethod
    def extract_tiers_from_elan_file(file_path: str) -> list[dict]:
        """Extract all tiers from an ELAN file.

        Args:
            file_path: Path to the ELAN file

        Returns:
            List of tier dictionaries with tier information

        """
        file_path_obj = Path(file_path)
        if not file_path_obj.exists() or file_path_obj.suffix.lower() != ".eaf":
            raise ValueError(f"Invalid ELAN file: {file_path}")

        try:
            # Parse XML
            parser = etree.XMLParser(
                resolve_entities=False, no_network=True, recover=False
            )
            tree = etree.parse(str(file_path_obj), parser=parser)
            root = tree.getroot()

            tiers = []
            for tier_elem in root.findall(".//TIER", namespaces=None):
                tier_info = {
                    "tier_name": tier_elem.get("TIER_ID"),
                    "parent_tier_name": tier_elem.get("PARENT_REF"),
                    "linguistic_type": tier_elem.get("LINGUISTIC_TYPE_REF"),
                    "participant": tier_elem.get("PARTICIPANT"),
                    "annotator": tier_elem.get("ANNOTATOR"),
                    "default_locale": tier_elem.get("DEFAULT_LOCALE"),
                }
                # Remove None values
                tier_info = {k: v for k, v in tier_info.items() if v is not None}
                tiers.append(tier_info)

            logger.info(f"Extracted {len(tiers)} tiers from {file_path}")
            return tiers

        except Exception as e:
            logger.error(f"Error parsing ELAN file {file_path}: {e!s}")
            raise

    @staticmethod
    def extract_time_slots(root: etree._Element) -> dict[str, int]:
        """Extract time slots from ELAN file.

        Args:
            root: XML root element

        Returns:
            Dictionary mapping time slot IDs to time values

        """
        time_slots = {}
        for time_slot in root.findall(".//TIME_SLOT", namespaces=None):
            slot_id = time_slot.get("TIME_SLOT_ID")
            time_value = time_slot.get("TIME_VALUE")
            if slot_id and time_value is not None:
                time_slots[slot_id] = int(time_value)

        logger.debug(f"Extracted {len(time_slots)} time slots")
        return time_slots

    @staticmethod
    def extract_media_descriptors(root: etree._Element) -> list[dict]:
        """Extract media descriptors from ELAN file.

        Args:
            root: XML root element

        Returns:
            List of media descriptor dictionaries

        """
        media_descriptors = []
        for media in root.findall(".//MEDIA_DESCRIPTOR", namespaces=None):
            media_info = {
                "media_url": media.get("MEDIA_URL"),
                "mime_type": media.get("MIME_TYPE"),
                "relative_media_url": media.get("RELATIVE_MEDIA_URL"),
                "time_origin": media.get("TIME_ORIGIN"),
                "extracted_from": media.get("EXTRACTED_FROM"),
            }
            # Remove None values
            media_info = {k: v for k, v in media_info.items() if v is not None}
            media_descriptors.append(media_info)

        logger.debug(f"Extracted {len(media_descriptors)} media descriptors")
        return media_descriptors

    @staticmethod
    def extract_linguistic_types(root: etree._Element) -> list[dict]:
        """Extract linguistic types from ELAN file.

        Args:
            root: XML root element

        Returns:
            List of linguistic type dictionaries

        """
        linguistic_types = []
        for ling_type in root.findall(".//LINGUISTIC_TYPE", namespaces=None):
            type_info = {
                "linguistic_type_id": ling_type.get("LINGUISTIC_TYPE_ID"),
                "time_alignable": ling_type.get("TIME_ALIGNABLE") == "true",
                "constraints": ling_type.get("CONSTRAINTS"),
                "graphic_references": ling_type.get("GRAPHIC_REFERENCES") == "true",
                "controlled_vocabulary": ling_type.get("CONTROLLED_VOCABULARY"),
                "controlled_vocabulary_url": ling_type.get("CONTROLLED_VOCABULARY_URL"),
            }
            # Remove None values
            type_info = {
                k: v for k, v in type_info.items() if k in type_info and v is not None
            }
            linguistic_types.append(type_info)

        logger.debug(f"Extracted {len(linguistic_types)} linguistic types")
        return linguistic_types
