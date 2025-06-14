#!/usr/bin/env python3
"""Extract and analyze P-code from .fun files."""

import struct
import sys
from pathlib import Path


def extract_pcode_from_fun(file_path: Path) -> None:
    """Extract P-code from a .fun file."""
    with open(file_path, "rb") as f:
        data = f.read()

    # Skip PowerBuilder export header if present
    pcode_start = 0
    if data.startswith(b"HA$PBExportHeader$"):
        first_newline = data.find(b"\n")
        second_newline = data.find(b"\n", first_newline + 1)
        if second_newline >= 0:
            pcode_start = second_newline + 1
            data[18:first_newline].decode("utf-8", errors="ignore")

    # Get the function data after header
    func_data = data[pcode_start:]

    if len(func_data) < 6:
        return

    # Parse function header
    code_len, line_len, unk_len = struct.unpack("<HHH", func_data[0:6])

    # Validate sizes
    expected_size = 6 + code_len + (line_len * 4)

    if expected_size > len(func_data):
        # Try to interpret the data differently

        # Show the data as potential P-code
        for i in range(min(32, len(func_data))):
            if i < len(func_data):
                func_data[i]
    else:
        # Extract P-code
        pcode = func_data[6 : 6 + code_len]

        # Show hex dump
        for i in range(0, len(pcode), 16):
            " ".join(f"{b:02x}" for b in pcode[i : i + 16])
            "".join(chr(b) if 32 <= b < 127 else "." for b in pcode[i : i + 16])

        # Show as opcodes
        for i in range(len(pcode)):
            pcode[i]

        # Extract debug info if present
        if line_len > 0 and 6 + code_len + (line_len * 4) <= len(func_data):
            debug_start = 6 + code_len
            for i in range(min(10, line_len)):  # Show first 10
                entry = func_data[debug_start + i * 4 : debug_start + (i + 1) * 4]
                if len(entry) == 4:
                    line_no, pcode_offset = struct.unpack("<HH", entry)


if __name__ == "__main__":
    if len(sys.argv) < 2:
        sys.exit(1)

    extract_pcode_from_fun(Path(sys.argv[1]))
