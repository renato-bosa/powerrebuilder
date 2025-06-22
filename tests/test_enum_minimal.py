#!/usr/bin/env python3
"""Test minimal enum support."""

import sys
from pathlib import Path

# Add project root to path
sys.path.append(str(Path(__file__).parent.parent))

from parse.parse_coordinator import PowerBuilderParser

# Test enumerated type with values
enum_test = """
global type my_status enumerated from powerobject
    active = 1
    inactive = 2
    pending = 3
end type
"""

# Test structure (should still work)
struct_test = """
global type my_struct from structure
    public integer id
    public string name
    private boolean flag
end type
"""

def test_parsing():




    """Test enum and struct parsing."""
    parser = PowerBuilderParser()

    tests = [
        ("Enumerated Type", enum_test),
        ("Structure Type", struct_test),
    ]

    for test_name, source in tests:
        print(f"\n{'='*50}")
        print(f"Testing: {test_name}")
        print(f"{'='*50}")

        try:
            # Parse the source
            tree = parser.parse(source, preprocess=False)

            print(f"✓ Successfully parsed")

            if isinstance(tree, dict):
                print(f"  AST type: {tree.get('type')}")

                # Check for elements
                if "elements" in tree:
                    for elem in tree["elements"]:
                        if hasattr(elem, "__class__"):
                            print(f"  - Found: {elem.__class__.__name__}")
                            if hasattr(elem, "name"):
                                print(f"    Name: {elem.name}")
                            if hasattr(elem, "is_enumerated"):
                                print(f"    Is Enumerated: {getattr(elem, 'is_enumerated', False)}")
                            if hasattr(elem, "values") and elem.__class__.__name__ == "EnumeratedType":
                                print(f"    Enum values: {elem.values}")
                            if hasattr(elem, "fields") and elem.__class__.__name__ == "StructureType":
                                print(f"    Structure fields: {len(elem.fields)} fields")
                                for field in elem.fields:
                                    print(f"      - {field.name}: {field.type}")

        except Exception as e:
            print(f"✗ Failed to parse {test_name}")
            print(f"  Error: {type(e).__name__}: {str(e)}")

            # Show first few lines of error for debugging
            error_lines = str(e).split("\n")[:5]
            for line in error_lines:
                if line.strip():
                    print(f"    {line}")

if __name__ == "__main__":
    test_parsing()
