#!/usr/bin/env python3
"""Simple analysis of .fun files without complex imports."""

import struct
from pathlib import Path


def hexdump(data, offset=0, length=None):



    """Create a hex dump of binary data."""
    if length:
        data = data[:length]

    lines = []
    for i in range(0, len(data), 16):
        hex_bytes = " ".join(f"{b:02x}" for b in data[i : i + 16])
        ascii_bytes = "".join(
            chr(b) if 32 <= b < 127 else "." for b in data[i : i + 16]
        )
        lines.append(f"{offset + i:08x}: {hex_bytes:<48} {ascii_bytes}")
    return "\n".join(lines)


def analyze_fun_file(file_path) -> None:








    """Analyze a .fun file structure."""
    with open(file_path, "rb") as f:
        data = f.read()

    # Check for PowerBuilder export header
    has_header = data.startswith(b"HA$PBExportHeader$")

    pcode_start = 0
    if has_header:
        # Find header boundaries
        first_nl = data.find(b"\n")
        comments_end = data.find(b"\n$PBExportComments$\n")

        if comments_end >= 0:
            pcode_start = comments_end + len(b"\n$PBExportComments$\n")
        elif first_nl > 0:
            second_nl = data.find(b"\n", first_nl + 1)
            if second_nl > 0:
                pcode_start = second_nl + 1

        if pcode_start > 0:
            data[:pcode_start].decode("utf-8", errors="ignore")

    # Get the P-code data
    pcode_data = data[pcode_start:]

    if len(pcode_data) > 0:
        # Try to interpret first few values
        if len(pcode_data) >= 4:
            for i in range(0, min(32, len(pcode_data)), 4):
                if i + 4 <= len(pcode_data):
                    struct.unpack("<I", pcode_data[i : i + 4])[0]

        # Look for patterns

        # Check if it's all zeros
        if all(b == 0 for b in pcode_data[: min(100, len(pcode_data))]):
            pass

        # Check for text patterns
        text_chars = sum(
            1 for b in pcode_data[: min(100, len(pcode_data))] if 32 <= b < 127
        )
        if text_chars > 50:
            pass

        # Check for specific byte patterns
        if pcode_data.startswith(b"\x00\x00\x00\x00"):
            pass
        if pcode_data.startswith(b"\x03\x00"):
            pass


def main() -> None:





    # Find some .fun files to analyze
    output_dir = Path("output")
    fun_files = list(output_dir.glob("**/*.fun"))[:5]  # First 5 files

    if not fun_files:
        return

    for fun_file in fun_files:
        analyze_fun_file(fun_file)


if __name__ == "__main__":
    main()
