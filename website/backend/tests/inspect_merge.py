#!/usr/bin/env python3
"""
Merge Inspection Tool - Create and save merged ELAN files for inspection.

This tool performs the same merge workflow as the integration test but provides
detailed analysis output for manual inspection. Use this to debug merge issues
and verify ELAN compatibility.

Output files:
- merge_inspection_latest.eaf: Latest merged ELAN file (always updated)
- merge_inspection_latest_analysis.json: Detailed merge analysis
- merge_inspection_latest_report.txt: Human-readable merge report
"""

import asyncio
import json
from pathlib import Path
from datetime import datetime

from app.service.elan_merge import ElanMergeService
from app.service.elan_generator import ElanXmlGenerator
from app.utils.elan_processor import ElanFileCoordinator


async def create_merge_output(output_name=None):
    # Input files
    file1 = Path(
        r"c:\Coding\Github_Repository\ELANORA\website\static\lsfb_simplified\CLSFB2912_S060.eaf"
    )
    file2 = Path(
        r"c:\Coding\Github_Repository\ELANORA\website\static\lsfb_simplified\CLSFB2912_S060_original.eaf"
    )

    if not file1.exists() or not file2.exists():
        print(f"ERROR: Input files not found!")
        print(f"   File 1: {file1}")
        print(f"   File 2: {file2}")
        return

    print("=" * 70)
    print("ELAN MERGE INSPECTION TOOL")
    print("=" * 70)

    # Create output directory
    output_dir = Path("tests/merge_outputs")
    output_dir.mkdir(parents=True, exist_ok=True)

    base_name = output_name if output_name else "merge_inspection_latest"

    # Extract data from files
    print("\nProcessing input files...")
    coord1 = ElanFileCoordinator(file1)
    data1 = coord1.process_complete()
    print(f"   Contributor: {len(data1['tiers'])} tiers")

    coord2 = ElanFileCoordinator(file2)
    data2 = coord2.process_complete()
    print(f"   Master: {len(data2['tiers'])} tiers")

    # Analyze differences
    tiers1 = {tier["tier_name"] for tier in data1["tiers"]}
    tiers2 = {tier["tier_name"] for tier in data2["tiers"]}

    common = tiers1 & tiers2
    only_1 = tiers1 - tiers2
    only_2 = tiers2 - tiers1

    print(f"\nTIER ANALYSIS:")
    print(f"   Common (conflicts): {len(common)}")
    print(f"   New from contributor: {len(only_1)}")
    print(f"   Preserved from master: {len(only_2)}")

    # Perform merge
    print("\nPERFORMING MERGE...")
    tier_assignments = {tier: 1 for tier in tiers1}
    merge_service = ElanMergeService()

    result = await merge_service.perform_preliminary_merge(
        contributor_data=data1,
        master_data=data2,
        contributor_username="inspector",
        tier_section_assignments=tier_assignments,
    )

    print(f"   Conflicts detected: {len(result['conflicts'])}")
    print(f"   Merged tiers: {result['statistics']['merged_tier_count']}")

    # Generate XML
    print("\nGENERATING ELAN XML...")
    xml_generator = ElanXmlGenerator()
    xml_content = xml_generator.generate_elan_xml(result["merged_data"])

    # Verify DESCRIPTION elements
    cv_count = xml_content.count("<CONTROLLED_VOCABULARY")
    desc_count = xml_content.count('<DESCRIPTION LANG_REF="und"')
    print(f"   Controlled vocabularies: {cv_count}")
    print(f"   DESCRIPTION elements: {desc_count}")
    if cv_count > 0 and desc_count > 0:
        print("   DESCRIPTION elements present (ELAN compatible)")

    # Save outputs
    print(f"\nSAVING OUTPUTS...")
    merged_file = output_dir / f"{base_name}.eaf"
    merged_file.write_text(xml_content, encoding="utf-8")
    print(f"   Merged file: {merged_file.name}")

    print("\n" + "=" * 70)
    print("INSPECTION COMPLETE")
    print(f"Output: {merged_file.absolute()}")
    print("=" * 70)


if __name__ == "__main__":
    import sys

    custom_name = sys.argv[1] if len(sys.argv) > 1 else None
    asyncio.run(create_merge_output(custom_name))
