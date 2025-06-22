#!/usr/bin/env python3
"""Test parsing of extracted .dwo files."""

import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from parse.parse_coordinator import PowerBuilderDataWindowParser


def test_dwo_parsing():




    """Test parsing of .dwo files with reconstructed DataWindow syntax."""

    # Sample DataWindow syntax from our comprehensive extraction
    sample_dw_syntax = """// Decompiled from PDW1000 PDW format
// Note: This is a reconstruction - original source not available
// Extracted: SQL=True, Columns=2, Properties=5

release 1000;

datawindow()
datawindow.color=126

header(height=72 color=536870912)

// SQL Query
table(column=(type=char(1) updatewhereclause=yes name=dummy dbname="dummy" )
 retrieve="SELECT t1.treatment_id FROM treatment t1" )

// Column definitions
column=(band=detail id=1 name="person_id" x="48" y="24" width="37" height="11")

summary(height=0 color=536870912)
footer(height=0 color=536870912)
"""

    print("Testing DataWindow parser with reconstructed .dwo syntax...")
    print("=" * 60)

    parser = PowerBuilderDataWindowParser()

    try:
        # Parse the sample syntax
        tree = parser.parse(sample_dw_syntax)
        print("✓ Successfully parsed DataWindow syntax")
        print(f"  Parse tree type: {type(tree)}")
        print(f"  Root data: {tree.data if hasattr(tree, 'data') else 'N/A'}")

        # Show first few nodes
        if hasattr(tree, "children"):
            print(f"  Children count: {len(tree.children)}")
            for i, child in enumerate(tree.children[:
                3]):
                if hasattr(child, "data"):
                    print(f"    Child {i}: {child.data}")
                else:
                    print(f"    Child {i}: {type(child)}")

    except Exception as e:
        print(f"✗ Failed to parse: {e}")
        print(f"  Error type: {type(e).__name__}")
        if hasattr(e, "line"):
            print(f"  Line: {e.line}")
        if hasattr(e, "column"):
            print(f"  Column: {e.column}")

if __name__ == "__main__":
    test_dwo_parsing()
