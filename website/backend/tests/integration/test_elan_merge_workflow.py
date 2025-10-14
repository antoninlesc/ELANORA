"""Integration test for ELAN merge workflow.

This test simulates the complete collaborative contribution workflow:
1. Extract data from contributor file
2. Query database for master file data (simulated)
3. Perform preliminary merge with tier assignments
4. Generate ELAN XML
5. Save output to merge_outputs for inspection

This test is reproducible and creates output in tests/merge_outputs/.
"""

import pytest
from pathlib import Path
from datetime import datetime

from app.service.elan_merge import ElanMergeService
from app.service.elan_generator import ElanXmlGenerator
from app.utils.elan_processor import ElanFileCoordinator


class TestElanMergeWorkflow:
    """Test the complete ELAN merge workflow with real files."""

    @pytest.mark.asyncio
    async def test_complete_merge_workflow(self):
        """Test complete merge workflow from extraction to XML generation.

        This test:
        1. Loads two ELAN files (simulating contributor and master)
        2. Extracts complete data from both
        3. Performs preliminary merge
        4. Generates valid ELAN XML
        5. Saves output for manual inspection in ELAN software
        """
        # Setup paths
        base_path = Path(
            r"c:\Coding\Github_Repository\ELANORA\website\static\lsfb_simplified"
        )
        file1 = base_path / "CLSFB2912_S060.eaf"
        file2 = base_path / "CLSFB2912_S060_original.eaf"

        # Skip if files don't exist
        if not file1.exists() or not file2.exists():
            pytest.skip("Test ELAN files not found")

        print("\n" + "=" * 70)
        print("🧪 ELAN MERGE WORKFLOW INTEGRATION TEST")
        print("=" * 70)

        # Step 1: Extract contributor data
        print("\n📄 Step 1: Extracting contributor file data...")
        coord1 = ElanFileCoordinator(file1)
        contributor_data = coord1.process_complete()
        print(f"   ✓ Extracted {len(contributor_data['tiers'])} tiers from contributor")

        # Step 2: Extract master data (simulating database query)
        print("\n📄 Step 2: Extracting master file data (simulating DB query)...")
        coord2 = ElanFileCoordinator(file2)
        master_data = coord2.process_complete()
        print(f"   ✓ Extracted {len(master_data['tiers'])} tiers from master")

        # Step 3: Analyze tier overlap
        contributor_tier_names = {
            tier["tier_name"] for tier in contributor_data["tiers"]
        }
        master_tier_names = {tier["tier_name"] for tier in master_data["tiers"]}

        common_tiers = contributor_tier_names & master_tier_names
        new_tiers = contributor_tier_names - master_tier_names
        preserved_tiers = master_tier_names - contributor_tier_names

        print(f"\n📊 Tier Analysis:")
        print(f"   • Common tiers (conflicts): {len(common_tiers)}")
        print(f"   • New tiers from contributor: {len(new_tiers)}")
        print(f"   • Preserved master tiers: {len(preserved_tiers)}")

        # Step 4: Create tier assignments (assign all contributor tiers to section 1)
        print("\n🔧 Step 4: Creating tier assignments...")
        tier_assignments = {tier: 1 for tier in contributor_tier_names}
        print(f"   ✓ Assigned {len(tier_assignments)} tiers to section 1")

        # Step 5: Perform preliminary merge
        print("\n🔄 Step 5: Performing preliminary merge...")
        merge_service = ElanMergeService()
        merge_result = await merge_service.perform_preliminary_merge(
            contributor_data=contributor_data,
            master_data=master_data,
            contributor_username="test_researcher",
            tier_section_assignments=tier_assignments,
        )

        print(f"   ✓ Merge completed")
        print(f"   • Conflicts detected: {len(merge_result['conflicts'])}")
        print(
            f"   • Merged tier count: {merge_result['statistics']['merged_tier_count']}"
        )

        # Step 6: Generate ELAN XML
        print("\n📝 Step 6: Generating ELAN XML...")
        xml_generator = ElanXmlGenerator()
        xml_content = xml_generator.generate_elan_xml(merge_result["merged_data"])

        print(f"   ✓ Generated XML ({len(xml_content)} characters)")

        # Step 7: Save output for inspection
        print("\n💾 Step 7: Saving output for inspection...")
        output_dir = Path("tests/merge_outputs")
        output_dir.mkdir(parents=True, exist_ok=True)

        # Clean up old test outputs (keep last 5)
        existing_outputs = sorted(output_dir.glob("test_merge_*.eaf"))
        if len(existing_outputs) > 5:
            for old_file in existing_outputs[:-5]:
                old_file.unlink()
                print(f"   • Cleaned up old output: {old_file.name}")

        # Save with reproducible name for testing
        output_file = output_dir / "test_merge_latest.eaf"
        output_file.write_text(xml_content, encoding="utf-8")
        print(f"   ✓ Saved to: {output_file}")

        # Also save timestamped version
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        timestamped_file = output_dir / f"test_merge_{timestamp}.eaf"
        timestamped_file.write_text(xml_content, encoding="utf-8")
        print(f"   ✓ Saved timestamped copy: {timestamped_file.name}")

        # Step 8: Validation
        print("\n✅ Step 8: Validation...")
        assert merge_result is not None
        assert "merged_data" in merge_result
        assert "conflicts" in merge_result
        assert "statistics" in merge_result
        assert xml_content.startswith("<?xml")
        assert "ANNOTATION_DOCUMENT" in xml_content
        assert "CONTROLLED_VOCABULARY" in xml_content

        # Verify DESCRIPTION elements are present in controlled vocabularies
        assert '<DESCRIPTION LANG_REF="und"' in xml_content
        print("   ✓ XML structure validated")
        print("   ✓ DESCRIPTION elements present in controlled vocabularies")

        print("\n" + "=" * 70)
        print("✅ INTEGRATION TEST COMPLETED SUCCESSFULLY")
        print("=" * 70)
        print(f"\n📂 Output files available in: {output_dir.absolute()}")
        print("   • test_merge_latest.eaf (always latest)")
        print(f"   • test_merge_{timestamp}.eaf (timestamped)")
        print("\n💡 Open these files in ELAN to verify compatibility!")
        print("=" * 70)

        return {
            "success": True,
            "output_file": str(output_file),
            "conflicts": len(merge_result["conflicts"]),
            "merged_tiers": merge_result["statistics"]["merged_tier_count"],
        }


if __name__ == "__main__":
    """Allow running test directly without pytest for quick checks."""
    import asyncio

    async def run_test():
        test = TestElanMergeWorkflow()
        result = await test.test_complete_merge_workflow()
        print("\n✅ Test result:", result)

    asyncio.run(run_test())
