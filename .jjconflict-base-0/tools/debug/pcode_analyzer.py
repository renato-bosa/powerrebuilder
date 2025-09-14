#!/usr/bin/env python3
"""Consolidated P-code file analyzer.

This tool combines functionality from:
- analyze_pcode_patterns.py (byte frequency and pattern analysis)
- analyze_pcode_structure.py (.fun file structure analysis)
- extract_pcode_from_fun.py (P-code extraction from .fun files)

Usage:
    python pcode_file_analyzer.py <file.fun> [--patterns] [--structure] [--extract]
    python pcode_file_analyzer.py <file.fun>  # Run all analyses
"""

import argparse
import os
import struct
import sys
from collections import Counter
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from src.decompile.pcode.opcodes.definitions import OPCODES


def read_file(file_path: str) -> bytes:
    """Read file as binary data."""
    with open(file_path, "rb") as f:
        return f.read()


def analyze_patterns(data: bytes) -> None:
    """Analyze byte patterns and frequencies in P-code data."""
    # Byte frequency analysis
    byte_freq = Counter(data)
    for byte_val, count in byte_freq.most_common(20):
        (count / len(data)) * 100
        OPCODES.get(byte_val, "UNKNOWN")

    # Look for known P-code patterns
    known_opcodes = {}
    for byte_val in byte_freq:
        if byte_val in OPCODES:
            known_opcodes[byte_val] = byte_freq[byte_val]

    for _opcode, count in sorted(
        known_opcodes.items(), key=lambda x: x[1], reverse=True
    ):
        pass

    # Pattern detection (sequences of bytes)
    patterns = Counter()
    for i in range(len(data) - 2):
        pattern = tuple(data[i : i + 3])
        patterns[pattern] += 1

    for pattern, count in patterns.most_common(10):
        if count > 10:  # Only show patterns that occur frequently
            " ".join(f"{b:02X}" for b in pattern)


def analyze_structure(data: bytes, file_path: str) -> None:
    """Analyze .fun file structure."""
    # Check for PowerBuilder export header
    if data.startswith(b"$PBExport"):
        header_end = data.find(b"\r\n\r\n")
        if header_end != -1:
            data[:header_end].decode("utf-8", errors="ignore")
            data = data[header_end + 4 :]  # Skip header for P-code analysis

    # Look for string tables
    strings = []
    current_string = bytearray()
    for i, byte in enumerate(data):
        if 32 <= byte <= 126:  # Printable ASCII
            current_string.append(byte)
        else:
            if len(current_string) >= 4:  # Minimum string length
                strings.append(
                    (i - len(current_string), current_string.decode("ascii"))
                )
            current_string = bytearray()

    if strings:
        for offset, _string in strings[:10]:  # Show first 10
            pass

    # Look for P-code markers
    markers = [b"PBFUN", b"PBSCR", b"PCODE", b"FUN*", b"SCR*"]
    for marker in markers:
        offset = data.find(marker)
        if offset != -1:
            pass

    # Analyze sections
    # Look for null-padded sections
    null_runs = []
    in_null_run = False
    start_offset = 0

    for i, byte in enumerate(data):
        if byte == 0:
            if not in_null_run:
                in_null_run = True
                start_offset = i
        else:
            if in_null_run and i - start_offset > 16:  # Significant null section
                null_runs.append((start_offset, i - start_offset))
            in_null_run = False

    if null_runs:
        for offset, _length in null_runs[:5]:
            pass


def extract_pcode(data: bytes, file_path: str) -> None:
    """Extract P-code from .fun file."""
    # Skip PowerBuilder export header if present
    pcode_start = 0
    if data.startswith(b"$PBExport"):
        header_end = data.find(b"\r\n\r\n")
        if header_end != -1:
            pcode_start = header_end + 4

    pcode_data = data[pcode_start:]

    # Try to identify P-code structure

    # Analyze first few bytes
    if len(pcode_data) >= 16:
        " ".join(f"{b:02X}" for b in pcode_data[:16])

        # Try to interpret as instructions
        offset = 0
        for _i in range(10):  # Decode first 10 instructions
            if offset >= len(pcode_data):
                break

            opcode = pcode_data[offset]
            OPCODES.get(opcode, f"UNKNOWN_0x{opcode:02X}")

            # Simple instruction length heuristic
            if opcode in [0x01, 0x02, 0x03]:  # PUSH instructions often have operands
                if offset + 4 < len(pcode_data):
                    struct.unpack("<I", pcode_data[offset + 1 : offset + 5])[0]
                    offset += 5
                else:
                    offset += 1
            else:
                offset += 1

    # Save extracted P-code
    output_path = file_path + ".pcode"
    with open(output_path, "wb") as f:
        f.write(pcode_data)


def main() -> None:
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Analyze P-code files - patterns, structure, and extraction",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )

    parser.add_argument("file", help="Path to .fun file to analyze")

    parser.add_argument(
        "--patterns",
        "-p",
        action="store_true",
        help="Analyze byte patterns and frequencies",
    )

    parser.add_argument(
        "--structure", "-s", action="store_true", help="Analyze file structure"
    )

    parser.add_argument(
        "--extract", "-e", action="store_true", help="Extract P-code section"
    )

    args = parser.parse_args()

    # If no specific analysis requested, do all
    if not (args.patterns or args.structure or args.extract):
        args.patterns = args.structure = args.extract = True

    # Check file exists
    if not os.path.exists(args.file):
        sys.exit(1)

    # Read file
    try:
        data = read_file(args.file)
    except Exception:
        sys.exit(1)

    # Run requested analyses
    if args.patterns:
        analyze_patterns(data)

    if args.structure:
        analyze_structure(data, args.file)

    if args.extract:
        extract_pcode(data, args.file)


if __name__ == "__main__":
    main()
