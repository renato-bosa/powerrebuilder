#!/usr/bin/env python3
"""Demonstrate PDW extraction capabilities."""

import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from decompile.pdw.pdw_handler import PDWHandler


def demo_pdw_extraction(file_path) -> None:





    """Demonstrate PDW extraction capabilities."""
    print("PDW Extraction Capabilities Demo")
    print("=" * 80)
    print()

    with open(file_path, "rb") as f:
        data = f.read()

    filename = Path(file_path).name

    # Check if it's a PDW file
    if not PDWHandler.can_handle_file(data):
        print(f"Error: {filename} is not a PDW file")
        return

    print(f"File: {filename}")
    print(f"Size: {len(data)} bytes")
    print()

    # Get summary
    print("Summary:")
    print("-" * 40)
    summary = PDWHandler.get_pdw_summary(data, filename)
    print(summary)
    print()

    # Extract comprehensive information
    print("\nComprehensive Extraction:")
    print("-" * 40)
    result = PDWHandler.process_pdw_file(data, filename, extract_mode="comprehensive")

    if result.get("datawindow"):
        dw = result["datawindow"]

        print(f"✓ Extracted {len(dw.columns)} columns")
        print(f"✓ Found {len(dw.tables)} tables")
        print(f"✓ Detected {len(dw.properties)} properties")

        if dw.window_bounds:
            print(f"✓ Window bounds: {dw.window_bounds}")

        if dw.background_color:
            print(f"✓ Background color: {dw.background_color}")

        print()

        # Show reconstructed source
        print("Reconstructed DataWindow Source:")
        print("-" * 40)
        if result.get("source_approximation"):
            print(result["source_approximation"])
        print()

        # Show what we couldn't extract
        print("\nLimitations:")
        print("-" * 40)
        print("Note: The following could not be extracted from compiled PDW:")
        print("  - Event scripts and code")
        print("  - Computed field expressions")
        print("  - Validation rules")
        print("  - Complex display expressions")
        print("  - Original comments and formatting")
        print()
        print("For complete source code, the original .srd or .dwo file is needed.")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        # Use default test file
        test_file = "/Users/michael/Projects/sime-finch/test_data/output/current/extracted/dcm_detailobjects.pbd/dcm_detailobjects.pbd/resources/d_latest_treatment_ds.dwo"
        if Path(test_file).exists():
            demo_pdw_extraction(test_file)
        else:
            print("Usage: demo_pdw_extraction.py <pdw_file>")
    else:
        demo_pdw_extraction(sys.argv[1])
