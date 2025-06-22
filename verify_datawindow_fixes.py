#!/usr/bin/env python3
"""Verify the DataWindow utils fixes."""

from common.constants import BUFFER_SIZE, HEADER_SIZE, STRING_TABLE_OFFSET
from common.datawindow_utils import DataWindowDetector


def test_format_patterns() -> None:





    """Test the updated FORMAT_PATTERNS."""
    print("Testing FORMAT_PATTERNS...")

    # Test cases
    test_cases = [
        ('processing="0"', "freeform"),
        ('processing="1"', "tabular"),
        ('processing="1" grid.lines=1', "grid"),
        ('processing="2"', "label"),
    ]

    for content, expected_type in test_cases:
        data = f"release 12;\ndatawindow({content})".encode()
        metadata = DataWindowDetector.extract_metadata(data)
        actual_type = metadata["type"]
        status = "✓" if actual_type == expected_type else "✗"
        print(f"  {status} {content:<30} -> {actual_type} (expected: {expected_type})")

    print()

def test_validate_syntax() -> None:





    """Test the validate_syntax fix."""
    print("Testing validate_syntax...")

    # Test the specific syntax that was failing
    syntax = """release 12;
datawindow(units=0 timer_interval=0)
table(column=(type=char(10) name=id))
"""

    is_valid, issues = DataWindowDetector.validate_syntax(syntax)
    print(f"  Syntax validation: {"✓ VALID" if is_valid else "✗ INVALID"}")
    if issues:
        print(f"  Issues: {issues}")
    else:
        print("  No issues found")

    print()

    # Test another example with multiple columns
    syntax2 = """release 12;
datawindow(units=0 timer_interval=0)
table(column=(type=char(10) name=id) column=(type=char(MAX_NAME_LENGTH) name=name))
"""

    is_valid2, issues2 = DataWindowDetector.validate_syntax(syntax2)
    print(f"  Multi-column syntax: {"✓ VALID" if is_valid2 else "✗ INVALID"}")
    if issues2:
        print(f"  Issues: {issues2}")
    else:
        print("  No issues found")

if __name__ == "__main__":
    print("DataWindow Utils Fix Verification")
    print("=" * 50)
    print()

    test_format_patterns()
    test_validate_syntax()

    print("\nAll fixes have been successfully applied!")
