"""
ELAN XML Generator Service

This service generates ELAN XML files using lxml library, following the official EAF v3.0 specification.
Uses the schema-compliant approach with proper element ordering and attribute handling.
"""

import os
import logging
from datetime import datetime
from typing import Dict, Any, List, Optional
from lxml import etree

logger = logging.getLogger(__name__)


class ElanXmlGenerator:
    """
    Generator for ELAN XML files using lxml for better XML control and schema compliance.
    Follows the official EAF v3.0 XSD specification exactly.
    """

    def __init__(self):
        """Initialize the ELAN generator with schema-aware settings."""
        # EAF v3.0 namespace and schema location
        self.namespace = None  # EAF v3.0 uses no namespace
        self.schema_location = "http://www.mpi.nl/tools/elan/EAFv3.0.xsd"

        # Load EAF v3.0 XSD schema for validation
        schema_path = os.path.join(os.path.dirname(__file__), "..", "..", "EAFv3.0.xsd")
        if os.path.exists(schema_path):
            with open(schema_path, "rb") as f:
                schema_doc = etree.parse(f)
                self.schema = etree.XMLSchema(schema_doc)
                logger.info("EAF v3.0 XSD schema loaded successfully for validation")
        else:
            logger.warning(
                f"EAF v3.0 XSD schema not found at {schema_path}, validation disabled"
            )
            self.schema = None

    def generate_elan_xml(self, merged_data: Dict[str, Any]) -> str:
        """
        Generate ELAN XML from merged data using lxml with EAF v3.0 schema compliance.

        Args:
            merged_data: Dictionary containing merged ELAN data structure

        Returns:
            String containing formatted ELAN XML
        """
        logger.info(
            "Starting ELAN XML generation with lxml and EAF v3.0 schema compliance"
        )

        # Create root element with proper namespace and schema location
        root = etree.Element("ANNOTATION_DOCUMENT")

        # Add root attributes in ELAN's exact order and format
        root.set("AUTHOR", merged_data.get("author", ""))

        # Format date with timezone like working ELAN files
        date_str = merged_data.get("date", datetime.now().isoformat())
        if "+" not in date_str and "Z" not in date_str:
            date_str = (
                date_str.split(".")[0] + "+01:00"
            )  # Remove microseconds and add timezone
        root.set("DATE", date_str)

        root.set("FORMAT", "3.0")
        root.set("VERSION", "3.0")

        # Set XML Schema instance namespace
        root.set(
            "{http://www.w3.org/2001/XMLSchema-instance}noNamespaceSchemaLocation",
            self.schema_location,
        )

        # Build document structure following EAF v3.0 element order:
        # LICENSE?, HEADER, TIME_ORDER, TIER*, LINGUISTIC_TYPE*, LOCALE*, LANGUAGE*,
        # CONSTRAINT*, CONTROLLED_VOCABULARY*, LEXICON_REF*, REF_LINK_SET*, EXTERNAL_REF*

        # 1. LICENSE (optional)
        if merged_data.get("license"):
            license_elem = self._create_license_element(merged_data["license"])
            root.append(license_elem)

        # 2. HEADER (required)
        header = self._create_header_element(merged_data.get("header", {}))
        root.append(header)

        # 3. TIME_ORDER (required)
        time_order = self._create_time_order_element(merged_data.get("time_slots", {}))
        root.append(time_order)

        # 4. TIER* (zero or more)
        for tier_data in merged_data.get("tiers", []):
            tier = self._create_tier_element(tier_data)
            root.append(tier)

        # 5. LINGUISTIC_TYPE* (zero or more)
        for lt_data in merged_data.get("linguistic_types", []):
            lt = self._create_linguistic_type_element(lt_data)
            root.append(lt)

        # 6. LOCALE* (zero or more)
        for locale_data in merged_data.get("locales", []):
            locale = self._create_locale_element(locale_data)
            root.append(locale)

        # 7. LANGUAGE* (zero or more)
        for lang_data in merged_data.get("languages", []):
            language = self._create_language_element(lang_data)
            root.append(language)

        # 8. CONSTRAINT* (zero or more)
        for constraint_data in merged_data.get("constraints", []):
            constraint = self._create_constraint_element(constraint_data)
            root.append(constraint)

        # 9. CONTROLLED_VOCABULARY* (zero or more)
        for cv_data in merged_data.get("controlled_vocabularies", []):
            cv = self._create_controlled_vocabulary_element(cv_data)
            root.append(cv)

        # 10. LEXICON_REF* (zero or more)
        for lexicon_data in merged_data.get("lexicon_refs", []):
            lexicon_ref = self._create_lexicon_ref_element(lexicon_data)
            root.append(lexicon_ref)

        # 11. REF_LINK_SET* (zero or more)
        for ref_link_set_data in merged_data.get("ref_link_sets", []):
            ref_link_set = self._create_ref_link_set_element(ref_link_set_data)
            root.append(ref_link_set)

        # 12. EXTERNAL_REF* (zero or more)
        for ext_ref_data in merged_data.get("external_refs", []):
            ext_ref = self._create_external_ref_element(ext_ref_data)
            root.append(ext_ref)

        # Generate formatted XML with ELAN-specific formatting
        xml_str = self._format_elan_xml_style(root)

        # Validate against EAF v3.0 schema if available
        if self.schema is not None:
            try:
                # Parse the XML string back to element for validation
                xml_element = etree.fromstring(xml_str.encode("utf-8"))
                self.schema.assertValid(xml_element)
                logger.info(
                    "Generated XML successfully validated against EAF v3.0 schema"
                )
            except etree.DocumentInvalid as e:
                logger.error(f"Generated XML failed schema validation: {e}")
                raise ValueError(f"EAF v3.0 schema validation failed: {e}")
        else:
            logger.warning("Schema validation skipped - EAF v3.0 XSD not available")

        logger.info("ELAN XML generation completed successfully")
        return xml_str

    def _create_license_element(self, license_data: Dict[str, Any]) -> etree._Element:
        """Create LICENSE element following EAF v3.0 schema."""
        license_elem = etree.Element("LICENSE")

        if license_data.get("license_url"):
            license_elem.set("LICENSE_URL", license_data["license_url"])

        if license_data.get("license_text"):
            license_elem.text = license_data["license_text"]

        return license_elem

    def _create_header_element(self, header_data: Dict[str, Any]) -> etree._Element:
        """Create HEADER element following EAF v3.0 schema."""
        header = etree.Element("HEADER")

        # Set required attributes with defaults
        header.set("MEDIA_FILE", header_data.get("media_file", ""))
        header.set("TIME_UNITS", header_data.get("time_units", "milliseconds"))

        # Add MEDIA_DESCRIPTOR elements
        for media_item in header_data.get("media", []):
            media_desc = self._create_media_descriptor_element(media_item)
            header.append(media_desc)

        # Add LINKED_FILE_DESCRIPTOR elements
        for linked_file in header_data.get("linked_files", []):
            lfd = self._create_linked_file_descriptor_element(linked_file)
            header.append(lfd)

        # Add required PROPERTY elements (ELAN expects these)
        import uuid

        # Check if URN property exists, if not add it
        existing_props = {
            prop.get("name", ""): prop for prop in header_data.get("properties", [])
        }

        if "URN" not in existing_props:
            urn_prop = etree.SubElement(header, "PROPERTY")
            urn_prop.set("NAME", "URN")
            urn_prop.text = f"urn:nl-mpi-tools-elan-eaf:{uuid.uuid4()}"

        if "lastUsedAnnotationId" not in existing_props:
            id_prop = etree.SubElement(header, "PROPERTY")
            id_prop.set("NAME", "lastUsedAnnotationId")
            id_prop.text = "1000"

        # Add existing properties
        for prop in header_data.get("properties", []):
            property_elem = etree.SubElement(header, "PROPERTY")
            property_elem.set("NAME", prop.get("name", ""))
            if prop.get("value"):
                property_elem.text = prop["value"]

        return header

    def _create_media_descriptor_element(
        self, media_data: Dict[str, Any]
    ) -> etree._Element:
        """Create MEDIA_DESCRIPTOR element following EAF v3.0 schema."""
        media_desc = etree.Element("MEDIA_DESCRIPTOR")

        # Make media URLs more portable by converting absolute paths to relative when possible
        media_url = media_data.get("media_url", "")
        if media_url.startswith("file:///Users/") or media_url.startswith(
            "file:///C:/"
        ):
            # Extract filename and make it relative
            filename = os.path.basename(media_url)
            media_url = f"./{filename}"
            logger.info(f"Converted media path to relative: {filename}")

        media_desc.set("MEDIA_URL", media_url)

        if media_data.get("mime_type"):
            media_desc.set("MIME_TYPE", media_data["mime_type"])
        if media_data.get("time_origin"):
            media_desc.set("TIME_ORIGIN", str(media_data["time_origin"]))
        if media_data.get("extracted_from"):
            media_desc.set("EXTRACTED_FROM", media_data["extracted_from"])

        return media_desc

    def _create_linked_file_descriptor_element(
        self, linked_file_data: Dict[str, Any]
    ) -> etree._Element:
        """Create LINKED_FILE_DESCRIPTOR element following EAF v3.0 schema."""
        lfd = etree.Element("LINKED_FILE_DESCRIPTOR")

        # Make linked file URLs more portable
        link_url = linked_file_data.get("link_url", "")
        if link_url.startswith("file:///Users/") or link_url.startswith("file:///C:/"):
            # Extract filename and make it relative
            filename = os.path.basename(link_url)
            link_url = f"./{filename}"
            logger.info(f"Converted linked file path to relative: {filename}")

        lfd.set("LINK_URL", link_url)

        # Update relative URL too if it exists
        if linked_file_data.get("relative_link_url"):
            relative_url = linked_file_data["relative_link_url"]
            if not relative_url.startswith("./"):
                filename = os.path.basename(relative_url)
                relative_url = f"./{filename}"
            lfd.set("RELATIVE_LINK_URL", relative_url)

        if linked_file_data.get("mime_type"):
            lfd.set("MIME_TYPE", linked_file_data["mime_type"])
        if linked_file_data.get("time_origin"):
            lfd.set("TIME_ORIGIN", str(linked_file_data["time_origin"]))
        if linked_file_data.get("associated_with"):
            lfd.set("ASSOCIATED_WITH", linked_file_data["associated_with"])

        return lfd

    def _create_time_order_element(self, time_slots: Dict[str, int]) -> etree._Element:
        """Create TIME_ORDER element following EAF v3.0 schema."""
        time_order = etree.Element("TIME_ORDER")

        # Sort time slots by ID for consistent output
        sorted_slots = sorted(
            time_slots.items(), key=lambda x: self._extract_time_slot_number(x[0])
        )

        for slot_id, time_value in sorted_slots:
            time_slot = etree.SubElement(time_order, "TIME_SLOT")
            time_slot.set("TIME_SLOT_ID", slot_id)
            time_slot.set("TIME_VALUE", str(time_value))

        return time_order

    def _extract_time_slot_number(self, slot_id: str) -> int:
        """Extract numeric part from time slot ID for sorting."""
        try:
            if slot_id.startswith("ts"):
                return int(slot_id[2:])
            return 0
        except ValueError:
            return 0

    def _create_tier_element(self, tier_data: Dict[str, Any]) -> etree._Element:
        """Create TIER element following EAF v3.0 schema."""
        tier = etree.Element("TIER")

        # Required attribute
        tier.set("TIER_ID", tier_data.get("tier_name", ""))

        # Add LINGUISTIC_TYPE_REF - check both possible field names
        linguistic_type = tier_data.get("linguistic_type_ref") or tier_data.get(
            "linguistic_type"
        )
        if linguistic_type:
            tier.set("LINGUISTIC_TYPE_REF", linguistic_type)
            logger.info(
                f"Added LINGUISTIC_TYPE_REF '{linguistic_type}' to tier '{tier_data.get('tier_name')}'"
            )
        else:
            logger.warning(
                f"Missing linguistic type for tier '{tier_data.get('tier_name')}'"
            )

        # Add PARENT_REF if present - check both possible field names
        parent_ref = tier_data.get("parent_ref") or tier_data.get("parent_tier_name")
        if parent_ref:
            tier.set("PARENT_REF", parent_ref)
            logger.info(
                f"Added PARENT_REF '{parent_ref}' to tier '{tier_data.get('tier_name')}'"
            )

        # Add other optional tier attributes
        if tier_data.get("participant"):
            tier.set("PARTICIPANT", tier_data["participant"])
        if tier_data.get("annotator"):
            tier.set("ANNOTATOR", tier_data["annotator"])
        if tier_data.get("lang_ref"):
            tier.set("LANG_REF", tier_data["lang_ref"])
        if tier_data.get("default_locale"):
            tier.set("DEFAULT_LOCALE", tier_data["default_locale"])

        # Add annotations
        for annotation_data in tier_data.get("annotations", []):
            annotation = self._create_annotation_element(annotation_data)
            tier.append(annotation)

        return tier

    def _create_annotation_element(
        self, annotation_data: Dict[str, Any]
    ) -> etree._Element:
        """Create ANNOTATION element following EAF v3.0 schema."""
        annotation = etree.Element("ANNOTATION")

        # Create alignable or ref annotation based on structure
        if annotation_data.get("time_slot_ref1") and annotation_data.get(
            "time_slot_ref2"
        ):
            # Alignable annotation
            alignable = etree.SubElement(annotation, "ALIGNABLE_ANNOTATION")
            self._add_annotation_attributes(alignable, annotation_data)
            alignable.set("TIME_SLOT_REF1", annotation_data["time_slot_ref1"])
            alignable.set("TIME_SLOT_REF2", annotation_data["time_slot_ref2"])

            # Add annotation value
            annotation_value = etree.SubElement(alignable, "ANNOTATION_VALUE")
            annotation_value.text = annotation_data.get("annotation_value", "")

        elif annotation_data.get("annotation_ref"):
            # Reference annotation
            ref_annotation = etree.SubElement(annotation, "REF_ANNOTATION")
            self._add_annotation_attributes(ref_annotation, annotation_data)
            ref_annotation.set("ANNOTATION_REF", annotation_data["annotation_ref"])

            # Add annotation value
            annotation_value = etree.SubElement(ref_annotation, "ANNOTATION_VALUE")
            annotation_value.text = annotation_data.get("annotation_value", "")

        return annotation

    def _add_annotation_attributes(
        self, element: etree._Element, annotation_data: Dict[str, Any]
    ) -> None:
        """Add common annotation attributes following EAF v3.0 schema."""
        if annotation_data.get("annotation_id"):
            element.set("ANNOTATION_ID", annotation_data["annotation_id"])
        if annotation_data.get("ext_ref"):
            element.set("EXT_REF", annotation_data["ext_ref"])
        if annotation_data.get("lang_ref"):
            element.set("LANG_REF", annotation_data["lang_ref"])
        if annotation_data.get("cve_ref"):
            element.set("CVE_REF", annotation_data["cve_ref"])

    def _create_linguistic_type_element(
        self, lt_data: Dict[str, Any]
    ) -> etree._Element:
        """Create LINGUISTIC_TYPE element following EAF v3.0 schema."""
        lt = etree.Element("LINGUISTIC_TYPE")

        # Required attribute
        lt.set("LINGUISTIC_TYPE_ID", lt_data.get("linguistic_type_id", ""))

        # Optional attributes
        if lt_data.get("time_alignable") is not None:
            lt.set("TIME_ALIGNABLE", "true" if lt_data["time_alignable"] else "false")
        if lt_data.get("constraints"):
            lt.set("CONSTRAINTS", lt_data["constraints"])
        if lt_data.get("graphic_references") is not None:
            lt.set(
                "GRAPHIC_REFERENCES",
                "true" if lt_data["graphic_references"] else "false",
            )
        if lt_data.get("controlled_vocabulary_ref"):
            lt.set("CONTROLLED_VOCABULARY_REF", lt_data["controlled_vocabulary_ref"])
        if lt_data.get("ext_ref"):
            lt.set("EXT_REF", lt_data["ext_ref"])
        if lt_data.get("lexicon_ref"):
            lt.set("LEXICON_REF", lt_data["lexicon_ref"])

        return lt

    def _create_locale_element(self, locale_data: Dict[str, Any]) -> etree._Element:
        """Create LOCALE element following EAF v3.0 schema."""
        locale = etree.Element("LOCALE")

        if locale_data.get("country_code"):
            locale.set("COUNTRY_CODE", locale_data["country_code"])
        if locale_data.get("language_code"):
            locale.set("LANGUAGE_CODE", locale_data["language_code"])

        return locale

    def _create_language_element(self, lang_data: Dict[str, Any]) -> etree._Element:
        """Create LANGUAGE element following EAF v3.0 schema."""
        language = etree.Element("LANGUAGE")

        # Required attribute
        language.set("LANG_ID", lang_data.get("lang_id", ""))

        # Optional attributes
        if lang_data.get("lang_def"):
            language.set("LANG_DEF", lang_data["lang_def"])
        if lang_data.get("lang_label"):
            language.set("LANG_LABEL", lang_data["lang_label"])

        return language

    def _create_constraint_element(
        self, constraint_data: Dict[str, Any]
    ) -> etree._Element:
        """Create CONSTRAINT element following EAF v3.0 schema."""
        constraint = etree.Element("CONSTRAINT")

        # Add DESCRIPTION attribute if provided (as seen in working ELAN files)
        if constraint_data.get("description"):
            constraint.set("DESCRIPTION", constraint_data["description"])

        # Required attribute
        constraint.set("STEREOTYPE", constraint_data.get("stereotype", ""))

        # Note: CONSTRAINT elements should be empty according to ELAN schema
        return constraint

    def _create_controlled_vocabulary_element(
        self, cv_data: Dict[str, Any]
    ) -> etree._Element:
        """Create CONTROLLED_VOCABULARY element following EAF v3.0 schema.

        According to EAF v3.0 XSD specification (line 1040), CONTROLLED_VOCABULARY
        must have DESCRIPTION elements BEFORE CV_ENTRY_ML elements, even if empty.
        This is critical for ELAN compatibility.
        """
        cv = etree.Element("CONTROLLED_VOCABULARY")

        # Required attribute
        cv.set("CV_ID", cv_data.get("cv_id", ""))

        # Optional external reference attribute
        if cv_data.get("ext_ref"):
            cv.set("EXT_REF", cv_data["ext_ref"])

        # CRITICAL: Always add DESCRIPTION element, even if empty
        # This is required by EAF v3.0 schema and ELAN will fail without it
        desc = etree.SubElement(cv, "DESCRIPTION")
        desc.set("LANG_REF", cv_data.get("description_lang", "und"))
        # Only set text if description is not empty
        if cv_data.get("description"):
            desc.text = cv_data["description"]

        # Add CV entries (must come AFTER DESCRIPTION per schema)
        for entry in cv_data.get("entries", []):
            cv_entry_ml = etree.SubElement(cv, "CV_ENTRY_ML")
            cv_entry_ml.set("CVE_ID", entry.get("cve_id", ""))

            # Add CV values
            for value in entry.get("values", []):
                cv_value = etree.SubElement(cv_entry_ml, "CVE_VALUE")
                cv_value.set("LANG_REF", value.get("lang_ref", "und"))
                if value.get("description"):
                    cv_value.set("DESCRIPTION", value["description"])
                cv_value.text = value.get("value", "")

        return cv

    def _create_lexicon_ref_element(
        self, lexicon_data: Dict[str, Any]
    ) -> etree._Element:
        """Create LEXICON_REF element following EAF v3.0 schema."""
        lexicon_ref = etree.Element("LEXICON_REF")

        # Add attributes
        for key, value in lexicon_data.items():
            if key != "ref_links":  # Skip nested elements
                lexicon_ref.set(key.upper(), str(value))

        # Add REF_LINK elements
        for ref_link_data in lexicon_data.get("ref_links", []):
            ref_link = etree.SubElement(lexicon_ref, "REF_LINK")
            self._add_ref_link_attributes(ref_link, ref_link_data)

        return lexicon_ref

    def _add_ref_link_attributes(
        self, element: etree._Element, link_data: Dict[str, Any]
    ) -> None:
        """Add REF_LINK attributes following EAF v3.0 schema."""
        if link_data.get("ref_link_id"):
            element.set("REF_LINK_ID", link_data["ref_link_id"])
        if link_data.get("lang_ref"):
            element.set("LANG_REF", link_data["lang_ref"])
        if link_data.get("cve_ref"):
            element.set("CVE_REF", link_data["cve_ref"])
        if link_data.get("content"):
            element.text = link_data["content"]

    def _create_ref_link_set_element(
        self, ref_link_set_data: Dict[str, Any]
    ) -> etree._Element:
        """Create REF_LINK_SET element following EAF v3.0 schema."""
        ref_link_set = etree.Element("REF_LINK_SET")

        # Add attributes
        if ref_link_set_data.get("ref_link_set_id"):
            ref_link_set.set("REF_LINK_SET_ID", ref_link_set_data["ref_link_set_id"])
        if ref_link_set_data.get("lang_ref"):
            ref_link_set.set("LANG_REF", ref_link_set_data["lang_ref"])
        if ref_link_set_data.get("cve_ref"):
            ref_link_set.set("CVE_REF", ref_link_set_data["cve_ref"])
        if ref_link_set_data.get("ext_ref"):
            ref_link_set.set("EXT_REF", ref_link_set_data["ext_ref"])

        # Add CROSS_REF_LINK elements
        for cross_ref_data in ref_link_set_data.get("cross_ref_links", []):
            cross_ref = self._create_cross_ref_link_element(cross_ref_data)
            ref_link_set.append(cross_ref)

        # Add GROUP_REF_LINK elements
        for group_ref_data in ref_link_set_data.get("group_ref_links", []):
            group_ref = self._create_group_ref_link_element(group_ref_data)
            ref_link_set.append(group_ref)

        return ref_link_set

    def _create_cross_ref_link_element(
        self, cross_ref_data: Dict[str, Any]
    ) -> etree._Element:
        """Create CROSS_REF_LINK element following EAF v3.0 schema."""
        cross_ref = etree.Element("CROSS_REF_LINK")

        if cross_ref_data.get("ref1"):
            cross_ref.set("REF1", cross_ref_data["ref1"])
        if cross_ref_data.get("ref2"):
            cross_ref.set("REF2", cross_ref_data["ref2"])
        if cross_ref_data.get("dir_info"):
            cross_ref.set("DIR_INFO", cross_ref_data["dir_info"])
        if cross_ref_data.get("lang_ref"):
            cross_ref.set("LANG_REF", cross_ref_data["lang_ref"])
        if cross_ref_data.get("cve_ref"):
            cross_ref.set("CVE_REF", cross_ref_data["cve_ref"])

        return cross_ref

    def _create_group_ref_link_element(
        self, group_ref_data: Dict[str, Any]
    ) -> etree._Element:
        """Create GROUP_REF_LINK element following EAF v3.0 schema."""
        group_ref = etree.Element("GROUP_REF_LINK")

        if group_ref_data.get("refs"):
            group_ref.set("REFS", group_ref_data["refs"])
        if group_ref_data.get("lang_ref"):
            group_ref.set("LANG_REF", group_ref_data["lang_ref"])
        if group_ref_data.get("cve_ref"):
            group_ref.set("CVE_REF", group_ref_data["cve_ref"])

        return group_ref

    def _create_external_ref_element(
        self, ext_ref_data: Dict[str, Any]
    ) -> etree._Element:
        """Create EXTERNAL_REF element following EAF v3.0 schema."""
        ext_ref = etree.Element("EXTERNAL_REF")

        # Required attributes
        ext_ref.set("EXT_REF_ID", ext_ref_data.get("ext_ref_id", ""))
        ext_ref.set("TYPE", ext_ref_data.get("type", ""))
        ext_ref.set("VALUE", ext_ref_data.get("value", ""))

        return ext_ref

    def _format_elan_xml_style(self, root: etree._Element) -> str:
        """Format XML to match ELAN's exact formatting style."""
        # Convert to string first with lxml pretty printing
        xml_str = etree.tostring(root, encoding="unicode", pretty_print=True)

        # Apply ELAN-specific formatting (safer approach)
        lines = xml_str.split("\n")
        formatted_lines = []

        # Add XML declaration
        formatted_lines.append('<?xml version="1.0" encoding="UTF-8"?>')

        for line in lines:
            stripped = line.strip()
            if not stripped:
                continue

            # Special formatting for root element (multi-line attributes like working file)
            if stripped.startswith("<ANNOTATION_DOCUMENT"):
                # Extract attributes
                attrs = root.attrib
                formatted_lines.append(
                    '<ANNOTATION_DOCUMENT AUTHOR="{}" DATE="{}"'.format(
                        attrs.get("AUTHOR", ""), attrs.get("DATE", "")
                    )
                )
                formatted_lines.append(
                    '    FORMAT="{}" VERSION="{}"'.format(
                        attrs.get("FORMAT", ""), attrs.get("VERSION", "")
                    )
                )
                schema_location = attrs.get(
                    "{http://www.w3.org/2001/XMLSchema-instance}noNamespaceSchemaLocation",
                    "",
                )
                formatted_lines.append(
                    '    xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xsi:noNamespaceSchemaLocation="{}"'.format(
                        schema_location
                    )
                    + ">"
                )
                continue

            # Keep all other lines as-is to avoid breaking XML structure
            formatted_lines.append(line)

        return "\n".join(formatted_lines)
