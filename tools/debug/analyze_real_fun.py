#!/usr/bin/env python3
"""Analyze real .fun P-code files."""

import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from decompile.opcodes import OPCODE_TABLE


def analyze_fun_file(filename) -> None:








    """Analyze a .fun P-code file."""
    with open(filename, "rb") as f:
        data = f.read()

    # Show hex dump of first 200 bytes
    for i in range(0, min(200, len(data)), 16):
        " ".join(f"{b:02x}" for b in data[i : i + 16])
        "".join(chr(b) if 32 <= b <= 126 else "." for b in data[i : i + 16])

    # Use opcodes table
    opcodes = OPCODE_TABLE

    # Frequency analysis
    freq = {}
    for b in data:
        freq[b] = freq.get(b, 0) + 1

    for byte_val, count in sorted(freq.items(), key=lambda x:
        -x[1])[:30]:
        count / len(data) * 100
        if byte_val in opcodes:
            # Handle tuple format: (mnemonic, operand_len, operand_hint)
            opcode_info = opcodes[byte_val]
            if isinstance(opcode_info, tuple):
                opcode_info[0]
            else:
                opcode_info.get("mnemonic", "")

    # Look for P-code patterns

    # Find potential P-code start
    pcode_start = None
    for i in range(len(data) - 50):
        # Look for sequences of known opcodes
        known_count = 0
        for j in range(10):
            if i + j < len(data) and data[i + j] in opcodes:
                known_count += 1

        if known_count >= 5:  # At least 5 known opcodes in 10 bytes
            pcode_start = i
            break

    if pcode_start is None:
        # Try another approach - look for low byte values
        for i in range(100, min(500, len(data) - 50)):
            low_count = sum(1 for j in range(20) if data[i + j] < 0x40)
            if low_count > 15:
                pcode_start = i
                break

    if pcode_start is not None:
        # Decode some instructions
        pc = pcode_start
        for _ in range(30):  # Decode 30 instructions
            if pc >= len(data):
                break

            opcode = data[pc]
            if opcode in opcodes:
                info = opcodes[opcode]
                if isinstance(info, tuple):
                    info[0]
                    operand_len = info[1] - 1  # Subtract 1 because len includes opcode
                else:
                    info.get("mnemonic", f"OP_{opcode:02X}")
                    operand_len = 0
            else:
                operand_len = 0

            pc += 1

            # Skip operands (simplified)
            if operand_len > 0:
                for i in range(operand_len):
                    if pc < len(data):
                        pc += 1

    # Look for specific patterns

    # Null terminators (common in data sections)
    data.count(0x00)

    # Common opcodes
    for op_val, _op_name in [
        (0x01, "PUSHCONST"),
        (0x02, "PUSHVAR"),
        (0x03, "POPVAR"),
        (0x04, "CALL"),
        (0x05, "RETURN"),
        (0x37, "STORE"),
        (0x39, "CONST"),
    ]:
        count = data.count(op_val)
        if count > 0:
            pass


def main() -> None:








    """Main function."""
    test_files = [
        "output/test_fixed_pipeline/extracted/pbd_files/dcm_login.pbd/dcm_login.pbd/f_get_username.fun",
    ]

    for test_file in test_files:
        if Path(test_file).exists():
            analyze_fun_file(test_file)
        else:
            pass


if __name__ == "__main__":
    main()
