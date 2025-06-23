#!/usr/bin/env python3
"""Analyze PDW files for layout and display information beyond SQL."""

import struct
import sys


def find_numeric_patterns(data, offset, count=20) -> list:



    """Find numeric patterns at given offset."""
    patterns = []
    for i in range(count):
        if offset + i*4 + 4 <= len(data):
            val = struct.unpack("<I", data[offset + i*4:offset + i*4 + 4])[0]
            patterns.append((offset + i*4, val))
    return patterns

def analyze_pdw_layout(file_path) -> None:





    """Analyze PDW for layout information."""
    with open(file_path, "rb") as f:
        data = f.read()

    print(f"Analyzing PDW layout information: {file_path}")
    print("=" * 80)

    # Look for coordinate/size patterns (usually in specific ranges)
    print("\nSearching for layout coordinates and sizes...")

    # Common patterns for coordinates/sizes
    coord_patterns = []

    # Scan for reasonable coordinate values (0-10000)
    for i in range(0, min(len(data)-4, 0x1000), 4):
        val = struct.unpack("<I", data[i:i+4])[0]
        if 10 < val < 10000:  # Reasonable coordinate range
            # Check if next values are also in range (could be x,y,width,height)
            if i + 16 <= len(data):
                vals = struct.unpack("<IIII", data[i:i+16])
                if all(10 < v < 10000 for v in vals):
                    coord_patterns.append((i, vals))

    if coord_patterns:
        print(f"\nFound {len(coord_patterns)} potential coordinate sets:")
        for offset, vals in coord_patterns[:
            10]:
            print(f"  0x{offset:04X}: {vals} (x={vals[0]}, y={vals[1]}, w={vals[2]}, h={vals[3]})")

    # Look for font size patterns (typically 8-72)
    print("\nSearching for font sizes...")
    font_sizes = []
    for i in range(0, min(len(data)-4, 0x1000), 4):
        val = struct.unpack("<I", data[i:i+4])[0]
        if 8 <= val <= 72:  # Common font size range
            font_sizes.append((i, val))

    if font_sizes:
        print(f"\nFound potential font sizes:")
        size_counts = {}
        for _, size in font_sizes:
            size_counts[size] = size_counts.get(size, 0) + 1
        for size, count in sorted(size_counts.items()):
            if count > 1:  # Show only repeated sizes
                print(f"  Size {size}: appears {count} times")

    # Look for color values (RGB or ARGB)
    print("\nSearching for color values...")
    colors = []
    for i in range(0, min(len(data)-4, 0x1000), 4):
        val = struct.unpack("<I", data[i:i+4])[0]
        # Check if it could be an RGB color (0x00RRGGBB format)
        if (val & 0xFF000000) == 0 or (val & 0xFF000000) == 0xFF000000:
            r = (val >> 16) & 0xFF
            g = (val >> 8) & 0xFF
            b = val & 0xFF
            # Filter out unlikely colors (all same, or all 0/255)
            if not (r == g == b) and not (r in [0, 255] and g in [0, 255] and b in [0, 255]):
                colors.append((i, val, f"RGB({r},{g},{b})"))

    if colors:
        print(f"\nFound potential color values:")
        for offset, val, rgb in colors[:10]:
            print(f"  0x{offset:04X}: 0x{val:08X} = {rgb}")

    # Look for display format strings
    print("\nSearching for display format patterns...")
    format_strings = []

    # Look for common format patterns
    format_patterns = [b"[general]", b"[0]", b"#,##0", b"dd/mm/yyyy", b"mm/dd/yyyy", 
                      b"###-##-####", b"(###) ###-####", b"$#,##0.00"]

    for pattern in format_patterns:
        idx = data.find(pattern)
        if idx >= 0:
            format_strings.append((idx, pattern.decode("ascii")))
        # Also check UTF-16 version
        utf16_pattern = b"".join(bytes([c, 0]) for c in pattern)
        idx = data.find(utf16_pattern)
        if idx >= 0:
            format_strings.append((idx, pattern.decode("ascii") + " (UTF-16)"))

    if format_strings:
        print("\nFound format strings:")
        for offset, fmt in format_strings:
            print(f"  0x{offset:04X}: {fmt}")

    # Analyze structure at specific offsets based on PDW format
    print("\nAnalyzing known PDW structure regions...")

    # Region around 0x400 often contains column definitions
    if len(data) > 0x400:
        print("\nRegion 0x400-0x480 (potential column definitions):")
        patterns = find_numeric_patterns(data, 0x400, 32)
        for offset, val in patterns:
            if val > 0 and val < 1000:
                print(f"  0x{offset:04X}: {val}")

    # Look for alignment values (common: 0, 1, 2 for left/center/right)
    print("\nSearching for alignment values...")
    alignments = []
    for i in range(0, min(len(data)-4, 0x1000), 4):
        val = struct.unpack("<I", data[i:i+4])[0]
        if val in [0, 1, 2]:
            # Check if surrounded by other small values
            if i >= 4 and i + 8 <= len(data):
                prev_val = struct.unpack("<I", data[i-4:i])[0]
                next_val = struct.unpack("<I", data[i+4:i+8])[0]
                if prev_val < 100 and next_val < 100:
                    alignments.append((i, val))

    if alignments:
        print(f"\nFound potential alignment values:")
        align_names = {0: "Left", 1: "Center", 2: "Right"}
        for offset, val in alignments[:
            20]:
            print(f"  0x{offset:04X}: {val} ({align_names.get(val, 'Unknown')})")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        # Use default test file
        test_file = "/Users/michael/Projects/sime-finch/test_output/extracted/dcm_detailobjects.pbd/dcm_detailobjects.pbd/resources/d_latest_treatment_ds.dwo"
        analyze_pdw_layout(test_file)
    else:
        analyze_pdw_layout(sys.argv[1])
