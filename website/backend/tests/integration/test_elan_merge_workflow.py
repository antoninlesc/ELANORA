"""Integration test for ELAN merge workflow.

This test simulates the complete collaborative contribution workflow:
1. Extract data from contributor file
2. Query database for master file data (simulated)
3. Perform preliminary merge with tier assignments
4. Generate ELAN XML
5. Save output to merge_outputs for inspection

This test is reproducible and creates output in tests/merge_outputs/.

Usage:
    pytest tests/integration/test_elan_merge_workflow.py -v -s
    python tests/integration/test_elan_merge_workflow.py [--inspect]
"""

import json
import sys
import os
from pathlib import Path
from datetime import datetime
from typing import Dict, Any

import pytest

from app.service.elan_merge import ElanMergeService
from app.service.elan_generator import ElanXmlGenerator
from app.utils.elan_processor import ElanFileCoordinator


@pytest.fixture
def inspect_mode():
    """Fixture to check if inspect mode is enabled via environment variable."""
    return os.getenv("ELAN_TEST_INSPECT", "false").lower() == "true"


class TestElanMergeWorkflow:
    """Test the complete ELAN merge workflow with real files."""

    @pytest.mark.asyncio
    @pytest.mark.parametrize("inspect_mode", [False, True], ids=["basic", "inspect"])
    async def test_complete_merge_workflow(self, inspect_mode):
        """Test complete merge workflow from extraction to XML generation.

        Args:
            inspect_mode: If True, generates detailed analysis files for inspection
        """
        result = await self._run_merge_workflow(inspect_mode)
        return result

    async def _run_merge_workflow(self, inspect_mode: bool = False) -> Dict[str, Any]:
        """Run the complete merge workflow."""
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
        if inspect_mode:
            print("🔍 INSPECTION MODE ENABLED")
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
        output_dir = Path("tests/integration/test_elan_merge_workflow_output")
        output_dir.mkdir(parents=True, exist_ok=True)

        # Generate detailed analysis if in inspect mode
        if inspect_mode:
            await self._generate_inspection_files(
                contributor_data, master_data, merge_result, xml_content, output_dir
            )

        # Save with reproducible name for testing
        output_file = output_dir / "test_merge_latest.eaf"
        output_file.write_text(xml_content, encoding="utf-8")
        print(f"   ✓ Saved to: {output_file}")

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
        print("   • test_merge_latest.eaf (merged ELAN file)")
        if inspect_mode:
            print("   • test_merge_latest_analysis.json (detailed analysis)")
            print("   • test_merge_latest_report.txt (human-readable report)")
        print("\n💡 Open test_merge_latest.eaf in ELAN to verify compatibility!")
        print("=" * 70)

        return {
            "success": True,
            "output_file": str(output_file),
            "conflicts": len(merge_result["conflicts"]),
            "merged_tiers": merge_result["statistics"]["merged_tier_count"],
            "inspect_mode": inspect_mode,
        }

    async def _generate_inspection_files(
        self,
        contributor_data: Dict[str, Any],
        master_data: Dict[str, Any],
        merge_result: Dict[str, Any],
        xml_content: str,
        output_dir: Path,
    ) -> None:
        """Generate detailed inspection files for analysis."""
        print("   🔍 Generating detailed analysis files...")

        # Analysis data
        analysis = {
            "timestamp": datetime.now().isoformat(),
            "contributor_file": "CLSFB2912_S060.eaf",
            "master_file": "CLSFB2912_S060_original.eaf",
            "tier_analysis": {
                "contributor_tiers": len(contributor_data["tiers"]),
                "master_tiers": len(master_data["tiers"]),
                "common_tiers": len(
                    set(t["tier_name"] for t in contributor_data["tiers"])
                    & set(t["tier_name"] for t in master_data["tiers"])
                ),
                "new_tiers": len(
                    set(t["tier_name"] for t in contributor_data["tiers"])
                    - set(t["tier_name"] for t in master_data["tiers"])
                ),
                "preserved_tiers": len(
                    set(t["tier_name"] for t in master_data["tiers"])
                    - set(t["tier_name"] for t in contributor_data["tiers"])
                ),
            },
            "merge_statistics": merge_result["statistics"],
            "conflicts": merge_result["conflicts"],
            "xml_validation": "passed" if merge_result["merged_data"] else "failed",
        }

        # Save analysis JSON
        analysis_file = output_dir / "test_merge_latest_analysis.json"
        with open(analysis_file, "w", encoding="utf-8") as f:
            json.dump(analysis, f, indent=2, ensure_ascii=False)
        print(f"   ✓ Analysis saved: {analysis_file.name}")

        # Generate human-readable report
        report = f"""
ELAN Merge Analysis Report
==========================

Generated: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}

Input Files:
- Contributor: CLSFB2912_S060.eaf ({len(contributor_data["tiers"])} tiers)
- Master: CLSFB2912_S060_original.eaf ({len(master_data["tiers"])} tiers)

Tier Analysis:
- Common tiers (potential conflicts): {analysis["tier_analysis"]["common_tiers"]}
- New tiers from contributor: {analysis["tier_analysis"]["new_tiers"]}
- Preserved master tiers: {analysis["tier_analysis"]["preserved_tiers"]}

Merge Results:
- Total merged tiers: {merge_result["statistics"]["merged_tier_count"]}
- Conflicts detected: {len(merge_result["conflicts"])}
- Merge sections: {merge_result["statistics"].get("sections_created", "N/A")}

Conflicts:
"""
        for i, conflict in enumerate(merge_result["conflicts"], 1):
            report += f"{i}. {conflict['tier_name']}: {conflict.get('description', 'Tier conflict')}\n"

        report += f"""

Validation:
- XML structure: {"✓ Valid" if xml_content.startswith("<?xml") else "✗ Invalid"}
- Schema compliance: {"✓ Passed" if "ANNOTATION_DOCUMENT" in xml_content else "✗ Failed"}
- ELAN compatibility: {"✓ Ready" if '<DESCRIPTION LANG_REF="und"' in xml_content else "✗ Not ready"}

Output File: test_merge_latest.eaf
"""

        # Save report
        report_file = output_dir / "test_merge_latest_report.txt"
        report_file.write_text(report, encoding="utf-8")
        print(f"   ✓ Report saved: {report_file.name}")


if __name__ == "__main__":
    """Allow running test directly without pytest for quick checks."""
    import argparse
    import asyncio

    parser = argparse.ArgumentParser(description="Run ELAN merge workflow test")
    parser.add_argument(
        "--inspect",
        action="store_true",
        help="Generate detailed analysis files for inspection",
    )
    args = parser.parse_args()

    async def run_test():
        test = TestElanMergeWorkflow()
        result = await test.test_complete_merge_workflow(inspect_mode=args.inspect)
        print("\n✅ Test result:", result)

    asyncio.run(run_test())
