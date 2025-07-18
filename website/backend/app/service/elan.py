"""ELAN Service - Simplified using utilities."""

import time
from decimal import Decimal
from pathlib import Path

from lxml import etree as ET
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.centralized_logging import get_logger
from app.crud import annotation, elan_file, tier
from app.crud.annotation import bulk_create_annotations
from app.crud.annotation_value import bulk_get_or_create_annotation_values
from app.crud.project import get_project_by_name
from app.model.tier import Tier
from app.utils.file_processing import ElanFileProcessor, XmlAttributeExtractor
from app.crud.elan_file import store_elan_file_data_in_db

# Get logger for this module
logger = get_logger()


class ElanService:
    """Service for ELAN file operations."""

    def __init__(self, db: AsyncSession):
        self.db = db
        self.file_processor = ElanFileProcessor()
        self.xml_extractor = XmlAttributeExtractor()

    def parse_elan_file(self, file_path: str) -> dict:
        logger.info(f"Starting to parse ELAN file: {file_path}")
        t0 = time.perf_counter()

        # Use utility for validation
        file_path_obj = ElanFileProcessor.validate_elan_file(file_path)

        t_parse_start = time.perf_counter()
        parser = ET.XMLParser(resolve_entities=False, no_network=True, recover=False)
        tree = ET.parse(file_path_obj, parser=parser)
        root = tree.getroot()
        t_parse_end = time.perf_counter()
        logger.info(f"XML parsing took {t_parse_end - t_parse_start:.3f}s")

        t_info_start = time.perf_counter()
        file_info = ElanFileProcessor.get_file_info(file_path_obj)
        file_info.update(
            {
                "tiers": [],
                "time_slots": ElanFileProcessor.extract_time_slots(root),
                "media": ElanFileProcessor.extract_media_descriptors(root),
            }
        )
        t_info_end = time.perf_counter()
        logger.info(f"File info extraction took {t_info_end - t_info_start:.3f}s")

        t_tiers_start = time.perf_counter()
        self._extract_tiers(root, file_info)
        t_tiers_end = time.perf_counter()
        logger.info(
            f"Tier and annotation extraction took {t_tiers_end - t_tiers_start:.3f}s"
        )

        total_time = time.perf_counter() - t0
        logger.info(f"Total parse_elan_file time: {total_time:.3f}s")
        return file_info

    def _extract_tiers(self, root: ET._Element, file_info: dict) -> None:
        """Extract tiers using utility functions."""
        tier_count = 0
        for tier_element in root.findall(".//TIER", namespaces=None):
            tier_info = self.xml_extractor.get_tier_attributes(tier_element)
            tier_info["annotations"] = self._extract_annotations(
                tier_element, file_info["time_slots"]
            )
            file_info["tiers"].append(tier_info)
            tier_count += 1

        logger.debug(f"Extracted {tier_count} tiers with annotations")

    def _extract_annotations(
        self, tier_element: ET._Element, time_slots: dict[str, int]
    ) -> list[dict]:
        """Extract annotations for a tier using utility functions."""
        annotations = []

        # Extract alignable annotations
        for annotation_elem in tier_element.findall(
            ".//ANNOTATION/ALIGNABLE_ANNOTATION",
            namespaces=None,
        ):
            ann_info = self.xml_extractor.get_alignable_annotation_attributes(
                annotation_elem, time_slots
            )
            if ann_info:
                annotations.append(ann_info)

        # Extract reference annotations
        for annotation_elem in tier_element.findall(
            ".//ANNOTATION/REF_ANNOTATION", namespaces=None
        ):
            ann_info = self.xml_extractor.get_ref_annotation_attributes(annotation_elem)
            if ann_info:
                annotations.append(ann_info)

        logger.debug(f"Extracted {len(annotations)} annotations from tier")
        return annotations

    def get_files_in_directory(self, directory_path: str) -> list[Path]:
        """Get all ELAN files in a directory using utility."""
        logger.info(f"Scanning directory for ELAN files: {directory_path}")
        files = ElanFileProcessor.find_files_in_directory(directory_path)
        logger.info(f"Found {len(files)} ELAN files in directory")
        return files

    # ==================== STORAGE METHODS ====================

    async def _store_tiers_and_annotations(
        self, tiers_data: list[dict], elan_id: int
    ) -> None:
        logger.debug(f"Storing {len(tiers_data)} tiers with annotations")
        t0 = time.perf_counter()

        # Bulk get or create all annotation values, get value_map
        t_val_start = time.perf_counter()
        value_map = await bulk_get_or_create_annotation_values(self.db, tiers_data)
        t_val_end = time.perf_counter()
        logger.info(f"AnnotationValue creation took {t_val_end - t_val_start:.3f}s")

        # First pass: create all tiers without parent references
        tier_name_to_id = {}
        t_tier_start = time.perf_counter()
        for tier_data in tiers_data:
            tier_obj = await tier.get_tier_by_name(self.db, tier_data["tier_name"])
            if not tier_obj:
                tier_obj = await tier.create_tier_in_db(
                    db=self.db,
                    tier_name=tier_data["tier_name"],
                    parent_tier_id=None,
                )
                logger.debug(
                    f"Created new tier: {tier_data['tier_name']} (ID: {tier_obj.tier_id})"
                )
            else:
                logger.debug(
                    f"Using existing tier: {tier_data['tier_name']} (ID: {tier_obj.tier_id})"
                )
            tier_data["tier_id"] = tier_obj.tier_id
            tier_name_to_id[tier_data["tier_name"]] = tier_obj.tier_id
        t_tier_end = time.perf_counter()
        logger.info(f"Tier creation took {t_tier_end - t_tier_start:.3f}s")

        # Second pass: update parent_tier_id for child tiers using CRUD
        for tier_data in tiers_data:
            parent_name = tier_data.get("parent_tier_name")
            if parent_name:
                parent_id = tier_name_to_id.get(parent_name)
                if parent_id and tier_data.get("parent_tier_id") != parent_id:
                    await tier.update_parent_tier(
                        self.db, tier_data["tier_id"], parent_id
                    )

        # Bulk create all annotations for all tiers
        t_ann_start = time.perf_counter()
        await bulk_create_annotations(self.db, tiers_data, elan_id, value_map)
        t_ann_end = time.perf_counter()
        logger.info(
            f"Annotation creation (all tiers) took {t_ann_end - t_ann_start:.3f}s"
        )

        logger.info(
            f"Tier/annotation DB operations took {t_ann_end - t_tier_start:.3f}s"
        )
        total_time = time.perf_counter() - t0
        logger.info(f"Total _store_tiers_and_annotations time: {total_time:.3f}s")

    async def _get_or_create_tier(self, tier_data: dict) -> Tier:
        """Get existing tier or create new one using CRUD."""
        tier_obj = await tier.get_tier_by_name(self.db, tier_data["tier_name"])

        if not tier_obj:
            tier_obj = await tier.create_tier_in_db(
                db=self.db,
                tier_name=tier_data["tier_name"],
                parent_tier_id=tier_data.get("parent_tier_id"),
            )
            logger.debug(
                f"Created new tier: {tier_data['tier_name']} (ID: {tier_obj.tier_id})"
            )
        else:
            logger.debug(
                f"Using existing tier: {tier_data['tier_name']} (ID: {tier_data['tier_id']})"
            )

        return tier_obj

    async def store_elan_file_data(
        self, file_info: dict, user_id: int, project_id: int
    ) -> int:
        """Store parsed ELAN file data in the database and sync associations."""
        logger.info(f"Storing ELAN file data: {file_info['filename']}")

        # Store all ELAN file data and associations using CRUD
        elan_id = await store_elan_file_data_in_db(
            self.db, file_info, user_id, project_id
        )

        # Store tiers and annotations (this sets tier["tier_id"])
        await self._store_tiers_and_annotations(file_info["tiers"], elan_id)

        # Now that tiers have IDs, sync associations
        tier_ids = [tier["tier_id"] for tier in file_info["tiers"]]
        await elan_file.sync_elan_file_to_tiers(self.db, elan_id, tier_ids)

        await self.db.commit()
        logger.info(f"Successfully stored: {file_info['filename']} (ID: {elan_id})")
        return elan_id

    async def process_single_file(
        self, file_path: str, user_id: int, project_name: str
    ) -> int:
        """Process and store a single ELAN file for the given project."""
        logger.info(f"Processing single ELAN file: {file_path}")

        # Resolve project name to ID
        project = await get_project_by_name(self.db, project_name)
        if not project:
            raise ValueError(f"Project '{project_name}' not found")

        file_info = self.parse_elan_file(file_path)
        elan_id = await self.store_elan_file_data(
            file_info, user_id, project.project_id
        )
        logger.info(f"Completed processing file: {file_path} (ID: {elan_id})")
        return elan_id

    async def process_directory(
        self, directory_path: str, user_id: int, project_name: str
    ) -> dict[str, int | None]:
        """Process all ELAN files in a directory for the given project."""
        logger.info(f"Starting directory processing: {directory_path}")
        eaf_files = self.get_files_in_directory(directory_path)

        logger.info(f"Found {len(eaf_files)} ELAN files in {directory_path}")

        results = {}
        processed_count = 0
        failed_count = 0

        for eaf_file in eaf_files:
            try:
                logger.info(f"Processing: {eaf_file.name}")
                elan_id = await self.process_single_file(
                    str(eaf_file), user_id, project_name
                )
                results[eaf_file.name] = elan_id
                processed_count += 1
            except Exception as e:
                logger.error(f"Failed to process {eaf_file.name}: {e}")
                results[eaf_file.name] = None
                failed_count += 1

        logger.info(
            f"Directory processing completed. Processed: {processed_count}, Failed: {failed_count}"
        )
        return results

    # ==================== QUERY METHODS ====================

    async def get_all_files_with_tiers(self) -> dict[str, list[str]]:
        """Get all files with their associated tier names."""
        logger.debug("Retrieving all files with their tier names")

        tier_names = await tier.get_all_tier_names_with_annotations(self.db)
        files = await elan_file.get_all_elan_files(self.db)

        logger.debug(
            f"Found {len(files)} files with {len(tier_names)} unique tier types"
        )

        return {f.filename: tier_names for f in files}

    async def get_file_structure(self, filename: str) -> dict | None:
        """Get complete structure for a specific file."""
        logger.debug(f"Retrieving file structure for: {filename}")

        # Get file using CRUD
        elan_file_obj = await elan_file.get_elan_file_by_filename(self.db, filename)

        if not elan_file_obj:
            logger.warning(f"File not found in database: {filename}")
            return None

        # Get all tiers with annotations
        tiers_with_annotations = await self._get_tiers_with_annotations()

        file_structure = {
            "elan_id": elan_file_obj.elan_id,
            "filename": elan_file_obj.filename,
            "file_path": elan_file_obj.file_path,
            "file_size": elan_file_obj.file_size,
            "tiers": [],
        }

        total_annotations = 0
        for tier_obj in tiers_with_annotations:
            # Get annotations using CRUD
            annotations_list = await annotation.get_annotations_by_tier(
                self.db, tier_obj.tier_id
            )
            tier_data = {
                "tier_id": tier_obj.tier_id,
                "tier_name": tier_obj.tier_name,
                "parent_tier_id": tier_obj.parent_tier_id,
                "annotation_count": len(annotations_list),
                "annotations": [
                    {
                        "annotation_id": ann.annotation_id,
                        "annotation_value": ann.annotation_value,
                        "start_time": float(ann.start_time),
                        "end_time": float(ann.end_time),
                    }
                    for ann in annotations_list
                ],
            }
            file_structure["tiers"].append(tier_data)
            total_annotations += len(annotations_list)

        logger.debug(
            f"Retrieved structure for {filename}: {len(file_structure['tiers'])} tiers, {total_annotations} annotations"
        )
        return file_structure

    async def _get_tiers_with_annotations(self) -> list[Tier]:
        """Get all tiers that have at least one annotation."""
        tiers = await tier.get_tiers_with_annotations(self.db)
        logger.debug(f"Found {len(tiers)} tiers with annotations")
        return tiers

    async def get_tier_statistics(self) -> dict:
        """Get statistics about tiers across all files."""
        logger.debug("Generating tier statistics")

        stats_list = await tier.get_tier_statistics(self.db)
        stats = {
            "tier_statistics": [
                {"tier_name": tier_name, "annotation_count": ann_count}
                for tier_name, ann_count in stats_list
            ]
        }

        logger.debug(
            f"Generated statistics for {len(stats['tier_statistics'])} tier types"
        )
        return stats

    async def get_user_files(self, user_id: int) -> list[dict]:
        """Get all ELAN files for a specific user."""
        logger.debug(f"Retrieving files for user ID: {user_id}")

        # Use CRUD function
        files = await elan_file.get_elan_files_by_user(self.db, user_id)

        logger.debug(f"Found {len(files)} files for user {user_id}")

        return [
            {
                "elan_id": f.elan_id,
                "filename": f.filename,
                "file_path": f.file_path,
                "file_size": f.file_size,
            }
            for f in files
        ]

    async def delete_file(self, elan_id: int) -> bool:
        """Delete an ELAN file (delegates to CRUD layer)."""
        logger.info(f"Deleting ELAN file with ID: {elan_id}")
        # Delegate all deletion logic to the CRUD layer
        success = await elan_file.delete_elan_file_full(self.db, elan_id)
        if success:
            logger.info(f"Successfully deleted ELAN file ID: {elan_id}")
        else:
            logger.warning(f"Failed to delete ELAN file ID: {elan_id}")
        return success

    async def get_annotations_in_time_range(
        self, tier_id: int, start_time: Decimal, end_time: Decimal
    ) -> list[dict]:
        """Get annotations within a specific time range for a tier."""
        logger.debug(
            f"Retrieving annotations for tier {tier_id} in time range: {start_time}-{end_time}"
        )

        # Use CRUD function
        annotations_list = await annotation.get_annotations_by_time_range(
            self.db, tier_id, start_time, end_time
        )

        logger.debug(f"Found {len(annotations_list)} annotations in time range")

        return [
            {
                "annotation_id": ann.annotation_id,
                "annotation_value": ann.annotation_value,
                "start_time": float(ann.start_time),
                "end_time": float(ann.end_time),
            }
            for ann in annotations_list
        ]

    async def delete_tier_annotations(self, tier_id: int) -> int:
        """Delete all annotations for a specific tier."""
        logger.info(f"Deleting all annotations for tier ID: {tier_id}")

        # Use CRUD function
        deleted_count = await annotation.delete_annotations_by_tier(self.db, tier_id)

        logger.info(f"Deleted {deleted_count} annotations for tier {tier_id}")
        return deleted_count
