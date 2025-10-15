"""Clean, focused unit tests for ELAN merge functionality.

These tests validate each component step by step:
1. Basic merge service functionality
2. XML generation from merged data
3. File processing capabilities
4. End-to-end workflow validation
5. Real file inspection (when available)
"""

import pytest
import tempfile
from pathlib import Path

from app.service.elan_merge import ElanMergeService
from app.service.elan_generator import ElanXmlGenerator


class TestMergeServiceBasics:
    """Test core merge functionality with simple mock data."""

    @pytest.fixture
    def simple_contributor_data(self):
        """Minimal contributor data for testing."""
        return {
            "tiers": [
                {"tier_name": "contributor_tier", "annotations": []},
                {"tier_name": "common_tier", "annotations": []},
            ],
            "time_slots": {"ts1": 1000, "ts2": 2000},
            "metadata": {"author": "contributor"},
        }

    @pytest.fixture
    def simple_master_data(self):
        """Minimal master data for testing."""
        return {
            "tiers": [
                {"tier_name": "master_tier", "annotations": []},
                {"tier_name": "common_tier", "annotations": []},
            ],
            "time_slots": {"ts1": 1000, "ts3": 3000},
            "metadata": {"author": "master"},
        }

    @pytest.mark.asyncio
    async def test_merge_detects_tier_conflicts(
        self, simple_contributor_data, simple_master_data
    ):
        """Test basic conflict detection."""
        merge_service = ElanMergeService()
        tier_assignments = {"contributor_tier": 1, "common_tier": 1}

        result = await merge_service.perform_preliminary_merge(
            contributor_data=simple_contributor_data,
            master_data=simple_master_data,
            contributor_username="test_user",
            tier_section_assignments=tier_assignments,
        )

        # Should detect conflict on common_tier
        conflicts = result["conflicts"]
        conflict_names = [c["tier_name"] for c in conflicts]
        assert "common_tier" in conflict_names

    @pytest.mark.asyncio
    async def test_merge_preserves_master_tiers(
        self, simple_contributor_data, simple_master_data
    ):
        """Test that master-only tiers are preserved."""
        merge_service = ElanMergeService()
        tier_assignments = {"contributor_tier": 1, "common_tier": 1}

        result = await merge_service.perform_preliminary_merge(
            contributor_data=simple_contributor_data,
            master_data=simple_master_data,
            contributor_username="test_user",
            tier_section_assignments=tier_assignments,
        )

        merged_tiers = result["merged_data"]["tiers"]
        tier_names = [t["tier_name"] for t in merged_tiers]
        assert "master_tier" in tier_names

    @pytest.mark.asyncio
    async def test_merge_adds_contributor_tiers(
        self, simple_contributor_data, simple_master_data
    ):
        """Test that new contributor tiers are added."""
        merge_service = ElanMergeService()
        tier_assignments = {"contributor_tier": 1, "common_tier": 1}

        result = await merge_service.perform_preliminary_merge(
            contributor_data=simple_contributor_data,
            master_data=simple_master_data,
            contributor_username="test_user",
            tier_section_assignments=tier_assignments,
        )

        merged_tiers = result["merged_data"]["tiers"]
        tier_names = [t["tier_name"] for t in merged_tiers]
        assert "contributor_tier" in tier_names

    @pytest.mark.asyncio
    async def test_merge_returns_statistics(
        self, simple_contributor_data, simple_master_data
    ):
        """Test that merge returns proper statistics."""
        merge_service = ElanMergeService()
        tier_assignments = {"contributor_tier": 1, "common_tier": 1}

        result = await merge_service.perform_preliminary_merge(
            contributor_data=simple_contributor_data,
            master_data=simple_master_data,
            contributor_username="test_user",
            tier_section_assignments=tier_assignments,
        )

        assert "statistics" in result
        stats = result["statistics"]
        assert "contributor_tier_count" in stats
        assert "master_tier_count" in stats
        assert "merged_tier_count" in stats
        assert "conflicts_detected" in stats
        assert "tiers_added" in stats
        assert "tiers_preserved" in stats
        assert "merge_timestamp" in stats


class TestXmlGeneration:
    """Test XML generation from merged data."""

    @pytest.fixture
    def minimal_merged_data(self):
        """Minimal data structure for XML generation."""
        return {
            "tiers": [
                {
                    "tier_name": "test_tier",
                    "linguistic_type_ref": "default-lt",
                    "annotations": [],
                }
            ],
            "time_slots": {"ts1": 1000, "ts2": 2000},
            "metadata": {"author": "test"},
            "linguistic_types": [
                {
                    "linguistic_type_id": "default-lt",
                    "time_alignable": "true",
                    "constraints": None,
                    "graphic_references": "false",
                    "controlled_vocabulary_ref": None,
                }
            ],
            "constraints": [],
            "controlled_vocabularies": [],
            "languages": [],
            "external_refs": [],
            "media": [],
            "linked_files": [],
            "properties": [],
        }

    def test_xml_has_valid_structure(self, minimal_merged_data):
        """Test basic XML structure is valid."""
        xml_generator = ElanXmlGenerator()
        xml_content = xml_generator.generate_elan_xml(minimal_merged_data)

        assert xml_content.startswith('<?xml version="1.0" encoding="UTF-8"?>')
        assert "<ANNOTATION_DOCUMENT" in xml_content
        assert "</ANNOTATION_DOCUMENT>" in xml_content

    def test_xml_includes_time_slots(self, minimal_merged_data):
        """Test that time slots are properly included."""
        xml_generator = ElanXmlGenerator()
        xml_content = xml_generator.generate_elan_xml(minimal_merged_data)

        assert "ts1" in xml_content
        assert "ts2" in xml_content
        assert 'TIME_VALUE="1000"' in xml_content

    def test_xml_includes_tiers(self, minimal_merged_data):
        """Test that tiers are properly included."""
        xml_generator = ElanXmlGenerator()
        xml_content = xml_generator.generate_elan_xml(minimal_merged_data)

        assert 'TIER_ID="test_tier"' in xml_content


class TestEndToEndWorkflow:
    """Test complete workflow from merge to XML."""

    @pytest.mark.asyncio
    async def test_complete_workflow(self):
        """Test the complete merge-to-XML workflow."""
        # Simple test data with proper linguistic types
        contributor_data = {
            "tiers": [
                {
                    "tier_name": "new_tier",
                    "linguistic_type_ref": "default-lt",
                    "annotations": [],
                }
            ],
            "time_slots": {"ts1": 1000},
            "metadata": {"author": "contributor"},
            "linguistic_types": [
                {
                    "linguistic_type_id": "default-lt",
                    "time_alignable": "true",
                    "constraints": None,
                    "graphic_references": "false",
                    "controlled_vocabulary_ref": None,
                }
            ],
        }

        master_data = {
            "tiers": [
                {
                    "tier_name": "master_tier",
                    "linguistic_type_ref": "default-lt",
                    "annotations": [],
                }
            ],
            "time_slots": {"ts2": 2000},
            "metadata": {"author": "master"},
            "linguistic_types": [
                {
                    "linguistic_type_id": "default-lt",
                    "time_alignable": "true",
                    "constraints": None,
                    "graphic_references": "false",
                    "controlled_vocabulary_ref": None,
                }
            ],
        }

        # Step 1: Perform merge
        merge_service = ElanMergeService()
        tier_assignments = {"new_tier": 1}

        merge_result = await merge_service.perform_preliminary_merge(
            contributor_data=contributor_data,
            master_data=master_data,
            contributor_username="test_user",
            tier_section_assignments=tier_assignments,
        )

        # Step 2: Generate XML
        xml_generator = ElanXmlGenerator()
        xml_content = xml_generator.generate_elan_xml(merge_result["merged_data"])

        # Validate workflow worked
        assert merge_result is not None
        assert xml_content is not None
        assert "new_tier" in xml_content
        assert "master_tier" in xml_content
        assert len(xml_content) > 100


# Optional tests that run with real files (skipped if files don't exist)
@pytest.mark.skipif(
    not Path(
        r"c:\Coding\Github_Repository\ELANORA\website\static\lsfb_simplified\CLSFB2912_S060.eaf"
    ).exists(),
    reason="Test ELAN files not found",
)
class TestWithRealFiles:
    """Tests that use actual ELAN files when available."""

    def test_can_process_real_elan_file(self):
        """Test basic file processing works."""
        from app.utils.elan_processor import ElanFileCoordinator

        file_path = Path(
            r"c:\Coding\Github_Repository\ELANORA\website\static\lsfb_simplified\CLSFB2912_S060.eaf"
        )
        coordinator = ElanFileCoordinator(file_path)
        data = coordinator.process_complete()

        assert "tiers" in data
        assert "time_slots" in data
        assert len(data["tiers"]) > 0

    @pytest.mark.asyncio
    async def test_real_file_merge_workflow(self):
        """Test complete workflow with real files."""
        from app.utils.elan_processor import ElanFileCoordinator

        file1 = Path(
            r"c:\Coding\Github_Repository\ELANORA\website\static\lsfb_simplified\CLSFB2912_S060.eaf"
        )
        file2 = Path(
            r"c:\Coding\Github_Repository\ELANORA\website\static\lsfb_simplified\CLSFB2912_S060_original.eaf"
        )

        if not file2.exists():
            pytest.skip("Second test file not found")

        # Extract data from both files
        coord1 = ElanFileCoordinator(file1)
        data1 = coord1.process_complete()

        coord2 = ElanFileCoordinator(file2)
        data2 = coord2.process_complete()

        # Create tier assignments
        tier_assignments = {}
        for tier in data1["tiers"]:
            tier_assignments[tier["tier_name"]] = 1

        # Perform merge
        merge_service = ElanMergeService()
        result = await merge_service.perform_preliminary_merge(
            contributor_data=data1,
            master_data=data2,
            contributor_username="test_user",
            tier_section_assignments=tier_assignments,
        )

        # Generate XML
        xml_generator = ElanXmlGenerator()
        xml_content = xml_generator.generate_elan_xml(result["merged_data"])

        # Basic validations
        assert result is not None
        assert "conflicts" in result
        assert xml_content.startswith("<?xml")
        assert len(xml_content) > 1000

        # Optional: Save to temp file for manual inspection
        with tempfile.NamedTemporaryFile(mode="w", suffix=".eaf", delete=False) as f:
            f.write(xml_content)
            print(f"\n📄 Generated merged XML: {f.name}")
            print(f"   Conflicts detected: {len(result['conflicts'])}")
            print(f"   Open this file in ELAN to validate the merge!")


# Detailed inspection test (run with pytest -s to see detailed output)
@pytest.mark.skipif(
    not Path(
        r"c:\Coding\Github_Repository\ELANORA\website\static\lsfb_simplified\CLSFB2912_S060.eaf"
    ).exists(),
    reason="Test ELAN files not found",
)
class TestDetailedInspection:
    """Detailed inspection of merge results."""

    @pytest.mark.asyncio
    async def test_detailed_merge_inspection(self):
        """Perform detailed inspection of merge process."""
        from app.utils.elan_processor import ElanFileCoordinator

        file1 = Path(
            r"c:\Coding\Github_Repository\ELANORA\website\static\lsfb_simplified\CLSFB2912_S060.eaf"
        )
        file2 = Path(
            r"c:\Coding\Github_Repository\ELANORA\website\static\lsfb_simplified\CLSFB2912_S060_original.eaf"
        )

        if not file2.exists():
            pytest.skip("Second test file not found")

        print(f"\n🔍 DETAILED MERGE INSPECTION")
        print("=" * 50)

        # Extract and analyze
        coord1 = ElanFileCoordinator(file1)
        data1 = coord1.process_complete()

        coord2 = ElanFileCoordinator(file2)
        data2 = coord2.process_complete()

        # Compare tiers
        tiers1 = {tier["tier_name"] for tier in data1["tiers"]}
        tiers2 = {tier["tier_name"] for tier in data2["tiers"]}

        common = tiers1 & tiers2
        only_1 = tiers1 - tiers2
        only_2 = tiers2 - tiers1

        print(f"📊 COMPARISON:")
        print(f"   File 1 ({file1.name}): {len(tiers1)} tiers")
        print(f"   File 2 ({file2.name}): {len(tiers2)} tiers")
        print(f"   Common tiers (conflicts): {len(common)}")
        print(f"   Only in file 1 (new): {len(only_1)}")
        print(f"   Only in file 2 (preserved): {len(only_2)}")

        # Show examples
        if only_1:
            print(f"   🆕 New tiers (first 3): {list(only_1)[:3]}")
        if common:
            print(f"   ⚠️  Conflicts (first 3): {list(common)[:3]}")

        # Perform merge
        tier_assignments = {tier: 1 for tier in tiers1}
        merge_service = ElanMergeService()

        result = await merge_service.perform_preliminary_merge(
            contributor_data=data1,
            master_data=data2,
            contributor_username="test_researcher",
            tier_section_assignments=tier_assignments,
        )

        print(f"\n🔄 MERGE RESULTS:")
        print(f"   Conflicts detected: {len(result['conflicts'])}")
        print(
            f"   Total merged tiers: {result['statistics'].get('merged_tier_count', 'N/A')}"
        )
        print(f"   Tiers added: {result['statistics'].get('tiers_added', 'N/A')}")
        print(
            f"   Tiers preserved: {result['statistics'].get('tiers_preserved', 'N/A')}"
        )  # Generate and save XML
        xml_generator = ElanXmlGenerator()
        xml_content = xml_generator.generate_elan_xml(result["merged_data"])

        with tempfile.NamedTemporaryFile(mode="w", suffix=".eaf", delete=False) as f:
            f.write(xml_content)
            temp_path = f.name

        print(f"\n📄 XML GENERATED:")
        print(f"   File: {temp_path}")
        print(f"   Size: {len(xml_content)} characters")
        print(f"   Lines: {len(xml_content.split(chr(10)))}")
        print(f"\n🎯 Next step: Open {temp_path} in ELAN to validate!")

        # Validate results
        assert len(result["conflicts"]) >= len(common)
        assert result["statistics"]["merged_tier_count"] > 0
        assert xml_content.startswith("<?xml")
        assert "<ANNOTATION_DOCUMENT" in xml_content
