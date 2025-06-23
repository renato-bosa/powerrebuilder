#!/usr/bin/env python3
"""Test the enhanced PDW extractor."""

import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from decompile.analysis.enhanced_pdw_extractor import EnhancedPDWExtractor


def test_pdw_extraction(file_path):




    """Test PDW extraction on a file."""
    with open(file_path, "rb") as f:
        data = f.read()

    print(f"Testing enhanced PDW extraction on: {file_path}")
    print(f"File size: {len(data)} bytes")
    print("=" * 80)

    # Extract structure
    structure = EnhancedPDWExtractor.extract_pdw_structure(data, Path(file_path).name)

    # Print report
    report = EnhancedPDWExtractor.format_structure_report(structure)
    print(report)

    # Additional details
    print("\nAdditional Analysis:")
    print("-" * 40)

    # Show hex dump of interesting regions
    for start, end, desc in structure.binary_regions:
        if "SQL" in desc:
            print(f"\nHex dump of {desc} (first 160 bytes):")
            region_data = data[start:min(start+160, end)]
            for i in range(0, len(region_data), 16):
                hex_part = region_data[i:i+16].hex()
                ascii_part = "".join(chr(b) if 0x20 <= b <= 0x7E else "." for b in region_data[i:i+16])
                print(f"  {start+i:04X}: {hex_part:<32} {ascii_part}")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        # Use default test file
        test_file = "/Users/michael/Projects/sime-finch/test_output/extracted/dcm_detailobjects.pbd/dcm_detailobjects.pbd/resources/d_latest_treatment_ds.dwo"
        test_pdw_extraction(test_file)
    else:
        test_pdw_extraction(sys.argv[1])
