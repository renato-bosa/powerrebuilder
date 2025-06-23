#!/usr/bin/env python3
"""Parse text-format P-code files and extract actual opcodes."""

import logging
import re
import sys
from pathlib import Path

logger = logging.getLogger(__name__)

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))


def parse_text_pcode(filename) -> None:







    """Parse text-format P-code file."""
    with open(filename, encoding="utf-8", errors="replace") as f:
        content = f.read()

    # Look for lines with format "XXXX: OPCODE_NAME args"
    pattern = r"^([0-9A-F]{4}):\s+(\w+)(?:\s+(.*))?$"

    instructions = []
    for line in content.split("\n"):
        match = re.match(pattern, line.strip())
        if match:
            addr = int(match.group(1), 16)
            opcode = match.group(2)
            args = match.group(3) or ""

            instructions.append(
                {
                    "address": addr,
                    "opcode": opcode,
                    "args": args,
                    "line": line.strip(),
                },
            )

    # Show first 30
    for instr in instructions[:30]:
        pass

    # Count opcodes
    opcode_counts = {}
    for instr in instructions:
        opcode = instr["opcode"]
        opcode_counts[opcode] = opcode_counts.get(opcode, 0) + 1

    for opcode, _count in sorted(opcode_counts.items(), key=lambda x:
        -x[1])[:20]:
        pass

    # Analyze patterns

    # Function structure
    sum(1 for i in instructions if i["opcode"] == "FUNCTION_START")
    sum(1 for i in instructions if i["opcode"] == "FUNCTION_END")

    # Control flow
    sum(1 for i in instructions if "JUMP" in i["opcode"])
    sum(1 for i in instructions if i["opcode"] in ["JUMPTRUE", "JUMPFALSE"])

    # Data operations
    sum(1 for i in instructions if "STORE" in i["opcode"])
    sum(1 for i in instructions if "LOAD" in i["opcode"])
    sum(1 for i in instructions if "CONST" in i["opcode"] or i["opcode"] == "STRING")

    # Look for actual opcode values in comments
    hex_pattern = r"0x([0-9A-F]{2})"
    found_opcodes = []
    for instr in instructions:
        if instr.get("args"):
            hex_matches = re.findall(hex_pattern, instr["args"])
            for hex_val in hex_matches:
                found_opcodes.append((instr["opcode"], int(hex_val, 16)))

    if found_opcodes:
        for _name, _value in found_opcodes[:
            20]:
            pass

    return instructions


def create_opcode_mapping(instructions):






    """Try to create opcode mapping from text format."""
    mapping = {}

    # Known mappings from our corrected opcodes
    known = {
        "HALT": 0x00,
        "PUSHCONST": 0x01,
        "PUSHVAR": 0x02,
        "POPVAR": 0x03,
        "CALL": 0x04,
        "RETURN": 0x05,
        "ADD": 0x15,
        "SUB": 0x16,
        "MUL": 0x17,
        "DIV": 0x18,
        "STORE": 0x37,
        "CONST": 0x39,
    }

    # Try to infer from instruction sequence
    for _i, instr in enumerate(instructions):
        opcode_name = instr["opcode"]

        # Check if we have a hex value in args
        if instr["args"] and instr["args"].startswith("0x"):
            try:
                hex_val = int(instr["args"].split()[0], 16)
                if opcode_name not in mapping:
                    mapping[opcode_name] = hex_val
            except Exception as e:
                logger.debug("Exception caught: %s", e)

    # Add known mappings
    mapping.update(known)

    return mapping


def main() -> None:








    """Main function."""
    test_files = [
        "tests/fixtures/pcode_files/test.pcode",
        "tests/fixtures/pcode_files/test_tj_report.pcode",
    ]

    all_instructions = []
    for test_file in test_files:
        if Path(test_file).exists():
            instructions = parse_text_pcode(test_file)
            all_instructions.extend(instructions)

    # Try to create mapping
    mapping = create_opcode_mapping(all_instructions)

    for _name, _value in sorted(mapping.items(), key=lambda x:
        x[1]):
        pass


if __name__ == "__main__":
    main()
