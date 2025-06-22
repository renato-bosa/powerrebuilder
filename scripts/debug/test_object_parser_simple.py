#!/usr/bin/env python3
"""Simple test of object parsing logic without complex imports."""

import struct
from pathlib import Path


def parse_object_simple(data: bytes, object_name: str) -> None:



    
    


    """Simplified object parser."""
    # Skip export header if present
    offset = 0
    if data.startswith(b"HA$PBExportHeader$"):
        header_end = data.find(b"\n$PBExportComments$\n")
        if header_end >= 0:
            offset = header_end + len(b"\n$PBExportComments$\n")
        else:
            first_nl = data.find(b"\n")
            if first_nl >= 0:
                second_nl = data.find(b"\n", first_nl + 1)
                if second_nl >= 0:
                    offset = second_nl + 1

    # Get actual object data
    obj_data = data[offset:]
    if len(obj_data) < 16:
        return

    # Parse header
    struct.unpack("<H", obj_data[0:2])[0]
    struct.unpack("<H", obj_data[2:4])[0]
    struct.unpack("<I", obj_data[4:8])[0]

    # Show first 256 bytes
    for i in range(0, min(256, len(obj_data)), 16):
        " ".join(f"{b:02x}" for b in obj_data[i : i + 16])
        "".join(chr(b) if 32 <= b < 127 else "." for b in obj_data[i : i + 16])

    # Look for P-code patterns

    # Known opcodes
    opcodes = {
        0x00: "RETURN",
        0x01: "STORE_RETURN_VAL",
        0x02: "JUMPTRUE",
        0x03: "JUMPFALSE",
        0x04: "JUMP",
        0x29: "GLOBFUNCCALL",
        0x2C: "DOTFUNCCALL",
        0x32: "PUSH_CONST_INT",
        0x65: "PUSH_LVALUE_INT",
        0x72: "PUSH_LVALUE_LONG",
    }

    # Scan for high-density opcode regions
    best_score = 0
    best_offset = -1
    window = 50

    for i in range(0, len(obj_data) - window, 10):
        score = sum(1 for j in range(window) if obj_data[i + j] in opcodes)
        if score > best_score:
            best_score = score
            best_offset = i

    if best_offset >= 0:
        # Show that region
        for i in range(best_offset, min(best_offset + 64, len(obj_data)), 16):
            " ".join(f"{b:02x}" for b in obj_data[i : i + 16])
            # Annotate known opcodes
            annotations = []
            for j in range(16):
                if i + j < len(obj_data) and obj_data[i + j] in opcodes:
                    annotations.append(f"{j * 3}:{opcodes[obj_data[i + j]]}")
            if annotations:
                pass


def main() -> None:
    
    


    output_dir = Path("output")
    fun_files = list(output_dir.glob("**/*.fun"))[:3]

    if not fun_files:
        return

    for fun_file in fun_files:
        with open(fun_file, "rb") as f:
            data = f.read()

        parse_object_simple(data, fun_file.stem)


if __name__ == "__main__":
    main()
