#!/usr/bin/env python3
"""Debug script to analyze the structure of P-code files and identify the actual P-code start."""

import struct
import sys
from pathlib import Path


def analyze_pcode_file(file_path: Path) -> None:








    """Analyze a .fun file to understand its structure."""
    with open(file_path, "rb") as f:
        data = f.read()

    # Show first 512 bytes in hex/ASCII format

    for offset in range(0, min(512, len(data)), 16):
        " ".join(f"{b:02x}" for b in data[offset : offset + 16])
        "".join(chr(b) if 32 <= b < 127 else "." for b in data[offset : offset + 16])

    # Look for PowerBuilder export headers
    if data.startswith(b"HA$PBExportHeader$"):
        # Find end of first line (object name)
        first_newline = data.find(b"\n")
        if first_newline > 0:
            data[18:first_newline].decode("utf-8", errors="ignore")

            # Find end of second line (comments)
            second_newline = data.find(b"\n", first_newline + 1)
            if second_newline > 0:
                data[first_newline + 1 : second_newline].decode(
                    "utf-8", errors="ignore",
                )

                # The actual P-code starts after the second newline
                pcode_start = second_newline + 1

                # Show the P-code section
                pcode_data = data[pcode_start:]

                for offset in range(0, min(256, len(pcode_data)), 16):
                    pcode_start + offset
                    " ".join(f"{b:02x}" for b in pcode_data[offset : offset + 16])
                    "".join(
                        chr(b) if 32 <= b < 127 else "."
                        for b in pcode_data[offset : offset + 16]
                    )

                # Analyze the P-code structure
                if len(pcode_data) >= 8:
                    # Try to interpret first few bytes

                    # Check for potential patterns
                    if pcode_data[0:2] == b"\x03\x00":
                        pass

                    # Try reading as little-endian 16-bit values
                    if len(pcode_data) >= 4:
                        struct.unpack("<H", pcode_data[0:2])[0]
                        struct.unpack("<H", pcode_data[2:4])[0]

                    # Look for potential opcode sequences
                    for i in range(min(32, len(pcode_data))):
                        pcode_data[i]
                        if (i + 1) % 4 == 0:
                            pass
    else:
        # Still analyze it
        for i in range(min(64, len(data))):
            data[i]
            if (i + 1) % 8 == 0:
                pass


def main() -> None:





    if len(sys.argv) < 2:
        sys.exit(1)

    file_path = Path(sys.argv[1])
    if not file_path.exists():
        sys.exit(1)

    analyze_pcode_file(file_path)


if __name__ == "__main__":
    main()
