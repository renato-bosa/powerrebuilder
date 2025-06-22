#!/usr/bin/env python3
"""Analyze the structure of .fun files to understand their format."""

import struct
from collections import Counter
from pathlib import Path


def analyze_structure(data: bytes, offset: int = 0) -> None:



    
    


    """Analyze structure starting at offset."""
    if len(data) < offset + 16:
        return

    # Try different interpretations
    # 1. As 16-bit values (little-endian)
    values_16 = []
    for i in range(0, min(32, len(data) - offset), 2):
        if offset + i + 1 < len(data):
            val = struct.unpack("<H", data[offset + i : offset + i + 2])[0]
            values_16.append(val)

    # 2. As 32-bit values (little-endian)
    values_32 = []
    for i in range(0, min(32, len(data) - offset), 4):
        if offset + i + 3 < len(data):
            val = struct.unpack("<I", data[offset + i : offset + i + 4])[0]
            values_32.append(val)

    # 3. Look for pointers/offsets
    for i, val in enumerate(values_32[:
        8]):
        if 0 < val < len(data):
            # Show what's at that offset
            if val + 16 < len(data):
                data[val : val + 16].hex(" ")


def find_patterns(data: bytes) -> None:



    
    


    """Find common byte patterns in the data."""
    # Look for 4-byte patterns
    patterns = Counter()
    for i in range(0, len(data) - 3, 1):
        pattern = data[i : i + 4]
        patterns[pattern] += 1

    # Show most common patterns
    for pattern, count in patterns.most_common(10):
        if count > 5:  # Only show patterns that appear multiple times
            pattern.hex(" ")
            # Try to interpret as text if possible
            "".join(chr(b) if 32 <= b < 127 else "." for b in pattern)


def analyze_string_table(data: bytes) -> None:



    
    


    """Look for string table structures."""
    # UTF-16 LE strings often appear in PowerBuilder
    i = 0
    strings_found = []

    while i < len(data) - 4:
        # Look for UTF-16 string pattern (alternating ASCII and 0x00)
        if data[i + 1] == 0 and 32 <= data[i] < 127:
            # Potential UTF-16 string start
            string_start = i
            string_bytes = []

            while i < len(data) - 1:
                if data[i + 1] == 0 and 32 <= data[i] < 127:
                    string_bytes.append(data[i])
                    i += 2
                else:
                    break

            if len(string_bytes) >= 3:  # Minimum string length
                string_text = "".join(chr(b) for b in string_bytes)
                strings_found.append((string_start, string_text))
        else:
            i += 1

    if strings_found:
        for _offset, _text in strings_found[:
            10]:  # First 10
            pass


def main() -> None:
    
    


    # Find a .fun file to analyze
    output_dir = Path("output")
    fun_files = list(output_dir.glob("**/*.fun"))

    if not fun_files:
        return

    # Analyze first file in detail
    fun_file = fun_files[0]

    with open(fun_file, "rb") as f:
        data = f.read()

    # Skip PowerBuilder export header if present
    pcode_start = 0
    if data.startswith(b"HA$PBExportHeader$"):
        first_nl = data.find(b"\n")
        second_nl = data.find(b"\n", first_nl + 1)
        if second_nl > 0:
            pcode_start = second_nl + 1

    # Get the actual data
    actual_data = data[pcode_start:]

    # Analyze the structure
    analyze_structure(actual_data, 0)

    # Look for patterns
    find_patterns(actual_data)

    # Look for strings
    analyze_string_table(actual_data)

    # Check if it might be a known structure

    # The pattern 03 00 76 40 appears frequently
    if actual_data[:4] == b"\x03\x00\x76\x40":
        pass

    # Check if it looks like a serialized object
    if actual_data[4:8] == b"\x01\x00\x10\x00":
        pass

    # Try to find actual P-code

    # Known P-code instruction starts
    pcode_markers = [
        (b"\x00", "RETURN"),
        (b"\x01", "STORE_RETURN_VAL"),
        (b"\x02", "JUMPTRUE"),
        (b"\x03", "JUMPFALSE"),
        (b"\x04", "JUMP"),
        (b"\x29", "GLOBFUNCCALL"),
        (b"\x2c", "DOTFUNCCALL"),
        (b"\x32", "PUSH_CONST_INT"),
    ]

    for marker, _name in pcode_markers:
        count = actual_data.count(marker + b"\x00")
        if count > 0:
            # Find first occurrence
            idx = actual_data.find(marker + b"\x00")
            if idx >= 0:
                pass


if __name__ == "__main__":
    main()
