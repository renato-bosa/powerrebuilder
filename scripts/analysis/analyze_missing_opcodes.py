#!/usr/bin/env python3
"""Analyze which opcodes are truly missing from our implementation."""

import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

# Read the unified opcode table directly
unified_path = (
    Path(__file__).parent.parent / "decompile" / "opcode_tables" / "unified.py"
)
with open(unified_path) as f:
    content = f.read()

# Extract OPCODE_MAP_UNIFIED by evaluating the relevant part
import re

match = re.search(r"OPCODE_MAP_UNIFIED = \{(.*?)\}", content, re.DOTALL)
if match:
    opcode_dict_str = "{" + match.group(1) + "}"
    OPCODE_MAP_UNIFIED = eval(opcode_dict_str)
else:
    sys.exit(1)

# List of opcodes reported as unknown in decompilation
reported_unknown = [
    "jumpfalse",
    "assign_uint",
    "store_return_val",
    "le_dec",
    "assign_int",
    "ge_double",
    "cnv_long_to_uint",
    "eq_float",
    "le_long",
    "cnv_string_to_char",
    "assign_time",
    "ne_double",
    "dbstop",
    "dbclose",
    "index",
    "ge_datetime",
    "gt_datetime",
    "gt_ulong",
    "cnv_char_to_string",
    "gt_uint",
    "eq_ulong",
    "push_const_dec",
    "ne_obinst",
    "cnv_string_to_chararray",
    "assign_long",
    "assign_obinst",
    "le_float",
    "ne_binary",
    "jumptrue",
    "cnv_float_to_long",
    "ne_long",
    "ge_char",
    "ne_char",
    "assign_string",
]

# Get all mnemonics from unified opcode map
known_mnemonics = set()
for mnemonic, _, _ in OPCODE_MAP_UNIFIED.values():
    known_mnemonics.add(mnemonic.lower())

# Check which opcodes are defined

found_opcodes = []
for opcode_name in reported_unknown:
    if opcode_name.lower() in known_mnemonics:
        found_opcodes.append(opcode_name)
        # Find the hex value
        for mnem, _, _ in OPCODE_MAP_UNIFIED.values():
            if mnem.lower() == opcode_name.lower():
                break


missing_opcodes = []
for opcode_name in reported_unknown:
    if opcode_name.lower() not in known_mnemonics:
        missing_opcodes.append(opcode_name)


# Check for similar opcodes
for missing in missing_opcodes:
    similar = []
    for mnem in known_mnemonics:
        # Check if the missing opcode is a substring or vice versa
        if (
            missing in mnem
            or mnem in missing
            or (missing.startswith("assign_") and mnem.startswith("store_"))
            or (missing.startswith("ne_") and mnem.startswith("ne_"))
            or (missing.startswith("ge_") and mnem.startswith("ge_"))
            or (missing.startswith("gt_") and mnem.startswith("gt_"))
            or (missing.startswith("eq_") and mnem.startswith("eq_"))
        ):
            similar.append(mnem)

    if similar:
        for _s in similar:
            pass

# Look for patterns in opcode ranges
comparison_opcodes = ["le_", "ge_", "gt_", "eq_", "ne_"]
conversion_opcodes = ["cnv_"]
assignment_opcodes = ["assign_", "store_"]

for prefix in comparison_opcodes:
    opcodes = [m for m in known_mnemonics if m.startswith(prefix)]
    if opcodes:
        pass

for prefix in conversion_opcodes:
    opcodes = [m for m in known_mnemonics if m.startswith(prefix)]
    if opcodes:
        pass

for prefix in assignment_opcodes:
    opcodes = [m for m in known_mnemonics if m.startswith(prefix)]
    if opcodes:
        pass
