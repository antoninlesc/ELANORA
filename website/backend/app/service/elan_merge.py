"""ELAN Merge Service - Core merge logic for collaborative contributions."""

from datetime import datetime
from typing import Any

from app.core.centralized_logging import get_logger

logger = get_logger()


class ElanMergeService:
    """Service for merging ELAN file contributions with master data."""

    async def perform_preliminary_merge(
        self,
        contributor_data: dict[str, Any],
        master_data: dict[str, Any],
        contributor_username: str,
        tier_section_assignments: dict[str, int],
    ) -> dict[str, Any]:
        """Perform preliminary merge of contributor and master ELAN data.

        Args:
            contributor_data: Complete ELAN data from contributor file
            master_data: Complete ELAN data from master database
            contributor_username: Username of contributor
            tier_section_assignments: Mapping of tier_name -> section_id

        Returns:
            Dict containing merged data, conflicts, and merge statistics

        """
        logger.info(
            f"Starting preliminary merge for contributor: {contributor_username}"
        )

        merge_result: dict[str, Any] = {
            "merged_data": {},
            "conflicts": [],
            "tiers_added": [],
            "tiers_preserved": [],
            "statistics": {},
        }

        try:
            # Initialize merged data structure
            merged_data = self._initialize_merged_data(contributor_username)

            # Step 1: Reconcile time slots (resolve ID conflicts)
            time_slot_mapping = self._reconcile_time_slots(
                contributor_data.get("time_slots", {}),
                master_data.get("time_slots", {}),
            )
            merged_data["time_slots"] = time_slot_mapping["merged_slots"]

            # Step 2: Merge media descriptors (into header)
            merged_data["header"]["media"] = self._merge_media_descriptors(
                contributor_data.get("media", []), master_data.get("media", [])
            )

            # Step 3: Merge linguistic types
            merged_data["linguistic_types"] = self._merge_linguistic_types(
                contributor_data.get("linguistic_types", []),
                master_data.get("linguistic_types", []),
            )

            # Step 4: Merge file properties (into header)
            merged_data["header"]["properties"] = self._merge_file_properties(
                contributor_data.get("properties", []),
                master_data.get("properties", []),
            )

            # Step 5: Merge linked file descriptors (into header)
            merged_data["header"]["linked_files"] = self._merge_linked_file_descriptors(
                contributor_data.get("linked_file_descriptors", []),
                master_data.get("linked_file_descriptors", []),
            )

            # Step 6: Merge controlled vocabularies
            merged_cvs, ext_refs_to_remove = self._merge_controlled_vocabularies(
                contributor_data.get("controlled_vocabularies", []),
                master_data.get("controlled_vocabularies", []),
            )
            merged_data["controlled_vocabularies"] = merged_cvs

            # Step 7: Merge languages
            merged_data["languages"] = self._merge_languages(
                contributor_data.get("languages", []), master_data.get("languages", [])
            )

            # Step 8: Merge external references (filtering out those no longer needed)
            merged_data["external_refs"] = self._merge_external_refs(
                contributor_data.get("external_refs", []),
                master_data.get("external_refs", []),
                ext_refs_to_remove,
            )

            # Step 9: Merge locales
            merged_data["locales"] = self._merge_locales(
                contributor_data.get("locales", []), master_data.get("locales", [])
            )

            # Step 10: Merge constraints
            merged_data["constraints"] = self._merge_constraints(
                contributor_data.get("constraints", []),
                master_data.get("constraints", []),
            )

            # Step 11: Core tier merge logic with conflict detection
            tier_merge_result = self._merge_tiers_with_conflict_detection(
                contributor_data.get("tiers", []),
                master_data.get("tiers", []),
                time_slot_mapping["id_remapping"],
                tier_section_assignments,
            )

            merged_data["tiers"] = tier_merge_result["merged_tiers"]
            merge_result["conflicts"] = tier_merge_result["conflicts"]
            merge_result["tiers_added"] = tier_merge_result["tiers_added"]
            merge_result["tiers_preserved"] = tier_merge_result["tiers_preserved"]
            merge_result["merged_data"] = merged_data

            # Step 10: Generate merge statistics
            merge_result["statistics"] = self._generate_merge_statistics(
                contributor_data, master_data, merge_result
            )

            logger.info(
                f"Preliminary merge completed: {len(merge_result['tiers_added'])} added, "
                f"{len(merge_result['conflicts'])} conflicts, "
                f"{len(merge_result['tiers_preserved'])} preserved"
            )

            return merge_result

        except Exception as e:
            logger.error(f"Preliminary merge failed: {e}")
            raise

    def _initialize_merged_data(self, contributor_username: str) -> dict[str, Any]:
        """Initialize the merged data structure with proper metadata.

        Structure matches what ElanXmlGenerator expects:
        - Top-level metadata attributes (author, date, etc.)
        - header dict containing media, linked_files, properties
        - time_slots, tiers, linguistic_types, etc. at top level
        """
        return {
            # Top-level document attributes
            "author": contributor_username,
            "date": datetime.now().isoformat(),
            "format": "3.0",
            "version": "3.0",
            # Header structure for ELAN generator
            "header": {
                "media_file": "",  # Deprecated but kept for compatibility
                "time_units": "milliseconds",
                "media": [],  # MEDIA_DESCRIPTOR elements
                "linked_files": [],  # LINKED_FILE_DESCRIPTOR elements
                "properties": [],  # PROPERTY elements
            },
            # Document structure
            "time_slots": {},
            "tiers": [],
            "linguistic_types": [],
            "controlled_vocabularies": [],
            "constraints": [],
            "languages": [],
            "locales": [],
            "external_refs": [],
        }

    def _reconcile_time_slots(
        self, contributor_slots: dict[str, int], master_slots: dict[str, int]
    ) -> dict[str, Any]:
        """Reconcile time slot conflicts and generate ID remapping.

        Returns:
            Dict with merged slots and ID remapping for contributor annotations

        """
        merged_slots = master_slots.copy()  # Start with master slots
        id_remapping = {}  # Maps old contributor IDs to new IDs
        next_id = 1

        # Find highest existing time slot ID number
        for slot_id in master_slots:
            if slot_id.startswith("ts"):
                try:
                    slot_num = int(slot_id[2:])
                    next_id = max(next_id, slot_num + 1)
                except ValueError:
                    continue

        # Process contributor time slots
        for contrib_slot_id, contrib_time_value in contributor_slots.items():
            if contrib_slot_id in master_slots:
                # Conflict: same ID exists in master
                if master_slots[contrib_slot_id] == contrib_time_value:
                    # Same time value - no remapping needed
                    id_remapping[contrib_slot_id] = contrib_slot_id
                else:
                    # Different time value - need new ID
                    new_slot_id = f"ts{next_id}"
                    merged_slots[new_slot_id] = contrib_time_value
                    id_remapping[contrib_slot_id] = new_slot_id
                    next_id += 1
            else:
                # No conflict - keep original ID
                merged_slots[contrib_slot_id] = contrib_time_value
                id_remapping[contrib_slot_id] = contrib_slot_id

        logger.debug(f"Time slot reconciliation: {len(id_remapping)} mappings created")

        return {"merged_slots": merged_slots, "id_remapping": id_remapping}

    def _merge_media_descriptors(
        self, contributor_media: list[dict], master_media: list[dict]
    ) -> list[dict]:
        """Merge media descriptors, preferring master for conflicts."""
        # For simplicity, preserve master media and add any new contributor media
        master_media_urls = {media.get("media_url", "") for media in master_media}
        merged_media = master_media.copy()

        for contrib_media in contributor_media:
            contrib_url = contrib_media.get("media_url", "")
            if contrib_url and contrib_url not in master_media_urls:
                merged_media.append(contrib_media)

        return merged_media

    def _merge_linguistic_types(
        self, contributor_types: list[dict], master_types: list[dict]
    ) -> list[dict]:
        """Merge linguistic types, preferring master for conflicts."""
        master_type_ids = {lt.get("linguistic_type_id", "") for lt in master_types}
        merged_types = master_types.copy()

        for contrib_type in contributor_types:
            type_id = contrib_type.get("linguistic_type_id", "")
            if type_id and type_id not in master_type_ids:
                merged_types.append(contrib_type)

        return merged_types

    def _merge_file_properties(
        self, contributor_props: list[dict], master_props: list[dict]
    ) -> list[dict]:
        """Merge file properties, preferring master for conflicts."""
        master_prop_names = {prop.get("name", "") for prop in master_props}
        merged_props = master_props.copy()

        for contrib_prop in contributor_props:
            prop_name = contrib_prop.get("name", "")
            if prop_name and prop_name not in master_prop_names:
                merged_props.append(contrib_prop)

        return merged_props

    def _merge_linked_file_descriptors(
        self, contributor_linked: list[dict], master_linked: list[dict]
    ) -> list[dict]:
        """Merge linked file descriptors, preferring master for conflicts."""
        master_link_urls = {link.get("link_url", "") for link in master_linked}
        merged_linked = master_linked.copy()

        for contrib_link in contributor_linked:
            link_url = contrib_link.get("link_url", "")
            if link_url and link_url not in master_link_urls:
                merged_linked.append(contrib_link)

        return merged_linked

    def _merge_controlled_vocabularies(
        self, contributor_cvs: list[dict], master_cvs: list[dict]
    ) -> tuple[list[dict], set[str]]:
        """Merge controlled vocabularies, keeping external CVs as external.

        Returns:
            Tuple of (merged_cvs, ext_refs_to_remove)

        """
        merged_cvs = []
        ext_refs_to_remove = set()

        # Process contributor CVs first to prefer their external refs
        contrib_cv_ids = {cv.get("cv_id", "") for cv in contributor_cvs}
        for contrib_cv in contributor_cvs:
            merged_cvs.append(contrib_cv.copy())

        # Then master CVs if not already added
        for master_cv in master_cvs:
            cv_id = master_cv.get("cv_id", "")
            if cv_id not in contrib_cv_ids:
                merged_cvs.append(master_cv.copy())

        return merged_cvs, ext_refs_to_remove

    def _merge_languages(
        self, contributor_langs: list[dict], master_langs: list[dict]
    ) -> list[dict]:
        """Merge languages, preferring master for conflicts."""
        master_lang_ids = {lang.get("lang_id", "") for lang in master_langs}
        merged_langs = master_langs.copy()

        for contrib_lang in contributor_langs:
            lang_id = contrib_lang.get("lang_id", "")
            if lang_id and lang_id not in master_lang_ids:
                merged_langs.append(contrib_lang)

        return merged_langs

    def _merge_external_refs(
        self,
        contributor_refs: list[dict],
        master_refs: list[dict],
        ext_refs_to_remove: set[str],
    ) -> list[dict]:
        """Merge external references, creating unique IDs for different URLs and filtering out unused ones."""
        merged_refs = []

        # Process master refs, filtering out those that are no longer needed
        for master_ref in master_refs:
            ref_id = master_ref.get("ext_ref_id", "")
            if ref_id not in ext_refs_to_remove:
                merged_refs.append(master_ref)

        # Process contributor refs
        master_values = {ref.get("value", "") for ref in merged_refs}
        master_ids = {ref.get("ext_ref_id", "") for ref in merged_refs}

        for contrib_ref in contributor_refs:
            contrib_value = contrib_ref.get("value", "")
            contrib_id = contrib_ref.get("ext_ref_id", "")

            # Skip if this ref was marked for removal
            if contrib_id in ext_refs_to_remove:
                continue

            # Only add if the URL/value is different from existing references
            if contrib_value and contrib_value not in master_values:
                # Create unique ID if same ID exists but different value
                ref_to_add = contrib_ref.copy()
                if contrib_id in master_ids:
                    # Generate unique ID by appending counter
                    counter = 2
                    new_id = f"{contrib_id}_{counter}"
                    while new_id in master_ids:
                        counter += 1
                        new_id = f"{contrib_id}_{counter}"
                    ref_to_add["ext_ref_id"] = new_id

                merged_refs.append(ref_to_add)
                master_values.add(contrib_value)
                master_ids.add(ref_to_add.get("ext_ref_id", ""))

        return merged_refs

    def _merge_locales(
        self, contributor_locales: list[dict], master_locales: list[dict]
    ) -> list[dict]:
        """Merge locales, preferring master for conflicts."""
        # Use combination of COUNTRY_CODE and LANGUAGE_CODE as unique identifier
        master_locale_keys = {
            (locale.get("country_code", ""), locale.get("language_code", ""))
            for locale in master_locales
        }
        merged_locales = master_locales.copy()

        for contrib_locale in contributor_locales:
            locale_key = (
                contrib_locale.get("country_code", ""),
                contrib_locale.get("language_code", ""),
            )
            if locale_key not in master_locale_keys:
                merged_locales.append(contrib_locale)

        return merged_locales

    def _merge_constraints(
        self, contributor_constraints: list[dict], master_constraints: list[dict]
    ) -> list[dict]:
        """Merge constraints, preferring master for conflicts."""
        # Use STEREOTYPE as unique identifier for constraints
        master_stereotypes = {
            constraint.get("stereotype", "") for constraint in master_constraints
        }
        merged_constraints = master_constraints.copy()

        for contrib_constraint in contributor_constraints:
            stereotype = contrib_constraint.get("stereotype", "")
            if stereotype and stereotype not in master_stereotypes:
                merged_constraints.append(contrib_constraint)

        return merged_constraints

    def _merge_tiers_with_conflict_detection(
        self,
        contributor_tiers: list[dict[str, Any]],
        master_tiers: list[dict[str, Any]],
        time_slot_remapping: dict[str, str],
        tier_section_assignments: dict[str, int],
    ) -> dict[str, Any]:
        """Core tier merge logic with conflict detection."""
        merged_tiers = []
        conflicts = []
        tiers_added = []
        tiers_preserved = []

        # Create lookup sets for efficient comparison
        master_tier_names = {tier["tier_name"] for tier in master_tiers}
        contributor_tier_names = {tier["tier_name"] for tier in contributor_tiers}

        # Process master tiers
        for master_tier in master_tiers:
            tier_name = master_tier["tier_name"]

            if tier_name not in contributor_tier_names:
                # Preserve master tier (contributor didn't touch it)
                merged_tiers.append(master_tier)
                tiers_preserved.append(tier_name)
            # If tier exists in both, we'll handle the conflict below

        # Process contributor tiers
        for contributor_tier in contributor_tiers:
            tier_name = contributor_tier["tier_name"]

            # Apply time slot remapping to annotations
            contributor_tier_remapped = self._remap_tier_time_slots(
                contributor_tier, time_slot_remapping
            )

            # Add section assignment information
            if tier_name in tier_section_assignments:
                contributor_tier_remapped["section_id"] = tier_section_assignments[
                    tier_name
                ]

            if tier_name in master_tier_names:
                # CONFLICT: Tier exists in both master and contributor
                master_tier = next(
                    t for t in master_tiers if t["tier_name"] == tier_name
                )

                conflict = {
                    "type": "tier_collision",
                    "tier_name": tier_name,
                    "master_tier": master_tier,
                    "contributor_tier": contributor_tier_remapped,
                    "conflict_details": self._analyze_tier_conflict(
                        master_tier, contributor_tier_remapped
                    ),
                }
                conflicts.append(conflict)

                # For preliminary merge, add contributor version with conflict marker
                contributor_tier_remapped["_has_conflict"] = True
                contributor_tier_remapped["_conflict_id"] = len(conflicts) - 1
                merged_tiers.append(contributor_tier_remapped)

                logger.warning(f"Tier conflict detected: {tier_name}")

            else:
                # No conflict - add contributor tier
                merged_tiers.append(contributor_tier_remapped)
                tiers_added.append(tier_name)

        return {
            "merged_tiers": merged_tiers,
            "conflicts": conflicts,
            "tiers_added": tiers_added,
            "tiers_preserved": tiers_preserved,
        }

    def _remap_tier_time_slots(
        self, tier: dict[str, Any], time_slot_remapping: dict[str, str]
    ) -> dict[str, Any]:
        """Apply time slot ID remapping to a tier's annotations."""
        tier_copy = tier.copy()
        tier_copy["annotations"] = []

        for annotation in tier.get("annotations", []):
            annotation_copy = annotation.copy()

            # Remap time slot references
            if (
                "time_slot_ref1" in annotation_copy
                and annotation_copy["time_slot_ref1"] in time_slot_remapping
            ):
                annotation_copy["time_slot_ref1"] = time_slot_remapping[
                    annotation_copy["time_slot_ref1"]
                ]

            if (
                "time_slot_ref2" in annotation_copy
                and annotation_copy["time_slot_ref2"] in time_slot_remapping
            ):
                annotation_copy["time_slot_ref2"] = time_slot_remapping[
                    annotation_copy["time_slot_ref2"]
                ]

            tier_copy["annotations"].append(annotation_copy)

        return tier_copy

    def _analyze_tier_conflict(
        self, master_tier: dict[str, Any], contributor_tier: dict[str, Any]
    ) -> dict[str, Any]:
        """Analyze the nature of tier conflicts."""
        master_annotations = master_tier.get("annotations", [])
        contrib_annotations = contributor_tier.get("annotations", [])

        return {
            "master_annotation_count": len(master_annotations),
            "contributor_annotation_count": len(contrib_annotations),
            "requires_manual_review": True,
            "suggested_resolution": "admin_review",
        }

    def _generate_merge_statistics(
        self,
        contributor_data: dict[str, Any],
        master_data: dict[str, Any],
        merge_result: dict[str, Any],
    ) -> dict[str, Any]:
        """Generate comprehensive merge statistics."""
        return {
            "contributor_tier_count": len(contributor_data.get("tiers", [])),
            "master_tier_count": len(master_data.get("tiers", [])),
            "merged_tier_count": len(merge_result["merged_data"]["tiers"]),
            "conflicts_detected": len(merge_result["conflicts"]),
            "tiers_added": len(merge_result["tiers_added"]),
            "tiers_preserved": len(merge_result["tiers_preserved"]),
            "merge_timestamp": datetime.now().isoformat(),
        }
