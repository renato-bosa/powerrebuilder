#!/usr/bin/env python3
"""
Real tests for binary detection issues.

This module tests and demonstrates the actual problems with binary detection
in DataWindow files.
"""

import struct

# Add project root to path
import sys
from pathlib import Path

project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from common.object_type_detector import MagicNumbers, ObjectTypeDetector


def test_real_binary_detection():






    """Test actual binary detection with real DataWindow patterns."""

    print("Testing Binary Detection Issues")
    print("=" * 60)

    # Test Case 1: DataWindow with magic number 0x444F4D76
    print("\n1. DataWindow with magic number 0x444F4D76:")
    magic_data = struct.pack("<I", MagicNumbers.DATAWINDOW_HEADER) + b"\x00" * 100
    is_binary = ObjectTypeDetector.is_binary_content(magic_data)
    magic_detected = ObjectTypeDetector.detect_magic_number(magic_data)
    print(f"   Data starts with: {magic_data[:8].hex()}")
    print(f"   Is binary detected: {is_binary}")
    print(f"   Magic number detected: {hex(magic_detected) if magic_detected else 'None'}")
    print(f"   Is corrupted size: {ObjectTypeDetector.is_corrupted_size(MagicNumbers.DATAWINDOW_HEADER)}")

    # Test Case 2: DataWindow with high null content
    print("\n2. DataWindow with 70% null bytes:")
    null_data = b"release 12.5;\n" + b"\x00" * 70 + b"datawindow()" + b"\x00" * 20
    analysis = ObjectTypeDetector.analyze_file_content(null_data, "test.dwo")
    print(f"   Null percentage: {analysis['null_percentage']:.1f}%")
    print(f"   Is binary: {analysis['is_binary']}")
    print(f"   Has DataWindow markers: {analysis['has_datawindow_markers']}")

    # Test Case 3: Mixed binary/text DataWindow
    print("\n3. Mixed binary/text DataWindow:")
    mixed_data = b"release 12.5;\x00\x00\x00\x00datawindow(\x00\x00processing=1\x00\x00)"
    is_binary = ObjectTypeDetector.is_binary_content(mixed_data)
    analysis = ObjectTypeDetector.analyze_file_content(mixed_data, "d_test_sql.dwo")
    print(f"   Is binary: {is_binary}")
    print(f"   Has DataWindow markers: {analysis['has_datawindow_markers']}")
    print(f"   DataWindow subtype: {analysis.get('datawindow_subtype')}")

    # Test Case 4: Corrupted extraction with asterisks
    print("\n4. Corrupted extraction pattern:")
    corrupted = b'COLUMN(NAME="address.add * ess_id")\nCOL *L MN(NAME="test")'
    print(f"   Sample corrupted data: {corrupted.decode('utf-8', errors='ignore')}")
    print(f"   Contains corruption markers: {'*' in corrupted.decode('utf-8', errors='ignore')}")

    # Test Case 5: Binary detection threshold
    print("\n5. Binary detection threshold testing:")
    for null_pct in [10, 20, 30, 40, 50, 60, 70]:
        test_size = 100
        null_count = int(test_size * null_pct / 100)
        test_data = b"A" * (test_size - null_count) + b"\x00" * null_count
        is_binary = ObjectTypeDetector.is_binary_content(test_data)
        print(f"   {null_pct}% nulls: binary = {is_binary}")

    # Test Case 6: Validation for extraction
    print("\n6. Extraction validation:")
    test_files = [
        ("d_test_sql.dwo", b"\x44\x4F\x4D\x76" + b"\x00" * 100),
        ("d_test_ds.dwo", b"release 12.5;\n" + b"\x00" * 200),
        ("d_test_ex.dwo", b"HA$PBExportHeader$\n" + b"datawindow()"),
    ]

    for filename, data in test_files:
        should_extract, method = ObjectTypeDetector.validate_extraction_target(data, filename)
        print(f"   {filename}: extract={should_extract}, method={method}")

    print("\n" + "=" * 60)
    print("Summary of Issues Found:")
    print("1. Binary detection threshold (30%) may be too high for some DataWindows")
    print("2. Magic number 0x444F4D76 is correctly detected as corrupt size")
    print("3. Mixed binary/text content is challenging to handle")
    print("4. No validation for corruption markers (*) in extracted content")
    print("5. Different DataWindow subtypes need different handling")


def test_extraction_corruption():






    """Test for the extraction corruption issue with asterisks."""

    print("\n\nTesting Extraction Corruption")
    print("=" * 60)

    # Simulate the corrupted extraction pattern we saw
    original_data = b'COLUMN(NAME="address.address_id")\nCOLUMN(NAME="person.name")'

    # Simulate corruption that inserts asterisks
    # This might happen due to encoding issues or binary data interpretation
    corrupted_positions = [20, 35]  # Random positions where corruption occurs

    corrupted_data = bytearray(original_data)
    for pos in corrupted_positions:
        if pos < len(corrupted_data):
            # Insert asterisk and space
            corrupted_data[pos:pos] = b"* "

    print("Original:", original_data.decode("utf-8"))
    print("Corrupted:", bytes(corrupted_data).decode("utf-8", errors="ignore"))

    # Test if we can detect this corruption
    corruption_markers = ["* ", "*L ", '* "', "COL *"]
    text = bytes(corrupted_data).decode("utf-8", errors="ignore")

    has_corruption = any(marker in text for marker in corruption_markers)
    print(f"\nCorruption detected: {has_corruption}")

    if has_corruption:
        print("Corruption patterns found:")
        for marker in corruption_markers:
            if marker in text:
                print(f"  - '{marker}'")


if __name__ == "__main__":
    test_real_binary_detection()
    test_extraction_corruption()
