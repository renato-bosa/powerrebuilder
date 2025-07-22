#!/usr/bin/env python3
"""Analyze P-code extraction results without complex imports."""

from pathlib import Path

from src.decompile.analyzers.parser import ObjectParser


def analyze_pcode_extraction() -> None:








    """Analyze how well we're extracting P-code."""
    output_dir = Path("output")
    fun_files = list(output_dir.glob("**/*.fun"))[:3]

    if not fun_files:
        return

    for fun_file in fun_files:
        with open(fun_file, "rb") as f:
            data = f.read()

        # Use object parser
        pb_object = ObjectParser.parse_object(data, fun_file.stem)

        if not pb_object:
            continue

        if pb_object.pcode_data:
            # Analyze the P-code data

            # Count different byte values
            byte_counts = {}
            for byte in pb_object.pcode_data:
                byte_counts[byte] = byte_counts.get(byte, 0) + 1

            # Show most common bytes
            sorted_bytes = sorted(byte_counts.items(), key=lambda x: x[1], reverse=True)
            for byte, count in sorted_bytes[:
                10]:
                count * 100.0 / len(pb_object.pcode_data)

            # Look for opcode-like patterns

            # Known opcodes that take parameters
            OPCODES_WITH_PARAMS = {
                0x02: ("JUMPTRUE", 2),
                0x03: ("JUMPFALSE", 2),
                0x04: ("JUMP", 2),
                0x29: ("GLOBFUNCCALL", 3),
                0x2C: ("DOTFUNCCALL", 3),
                0x32: ("PUSH_CONST_INT", 3),
            }

            i = 0
            instruction_count = 0
            while i < len(pb_object.pcode_data) - 3:
                byte = pb_object.pcode_data[i]
                if byte in OPCODES_WITH_PARAMS:
                    opcode_name, opcode_len = OPCODES_WITH_PARAMS[byte]
                    if i + opcode_len <= len(pb_object.pcode_data):
                        instruction_count += 1
                        if instruction_count <= 5:  # Show first few
                            param_bytes = pb_object.pcode_data[i + 1 : i + opcode_len]
                            " ".join(f"{b:02x}" for b in param_bytes)
                        i += opcode_len
                        continue
                i += 1

            # Show hex dump of first part
            for offset in range(0, min(128, len(pb_object.pcode_data)), 16):
                " ".join(f"{b:02x}" for b in pb_object.pcode_data[offset : offset + 16])
                "".join(
                    chr(b) if 32 <= b < 127 else "."
                    for b in pb_object.pcode_data[offset : offset + 16]
                )


if __name__ == "__main__":
    analyze_pcode_extraction()
