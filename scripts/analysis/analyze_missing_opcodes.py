#!/usr/bin/env python3
"""Analyze which opcodes are truly missing from our implementation."""

import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

# Read the unified opcode table directly
unified_path = Path(__file__).parent.parent / "decompile" / "opcode_tables" / "unified.py"
with open(unified_path, 'r') as f:
    content = f.read()
    
# Extract OPCODE_MAP_UNIFIED by evaluating the relevant part
import re
match = re.search(r'OPCODE_MAP_UNIFIED = \{(.*?)\}', content, re.DOTALL)
if match:
    opcode_dict_str = "{" + match.group(1) + "}"
    OPCODE_MAP_UNIFIED = eval(opcode_dict_str)
else:
    print("Failed to extract OPCODE_MAP_UNIFIED")
    sys.exit(1)

# List of opcodes reported as unknown in decompilation
reported_unknown = [
    "jumpfalse", "assign_uint", "store_return_val", "le_dec", "assign_int",
    "ge_double", "cnv_long_to_uint", "eq_float", "le_long", "cnv_string_to_char",
    "assign_time", "ne_double", "dbstop", "dbclose", "index", "ge_datetime",
    "gt_datetime", "gt_ulong", "cnv_char_to_string", "gt_uint", "eq_ulong",
    "push_const_dec", "ne_obinst", "cnv_string_to_chararray", "assign_long",
    "assign_obinst", "le_float", "ne_binary", "jumptrue", "cnv_float_to_long",
    "ne_long", "ge_char", "ne_char", "assign_string"
]

# Get all mnemonics from unified opcode map
known_mnemonics = set()
for opcode, (mnemonic, _, _) in OPCODE_MAP_UNIFIED.items():
    known_mnemonics.add(mnemonic.lower())

# Check which opcodes are defined
print("=== OPCODE ANALYSIS REPORT ===\n")

print("1. Opcodes found in unified table:")
found_opcodes = []
for opcode_name in reported_unknown:
    if opcode_name.lower() in known_mnemonics:
        found_opcodes.append(opcode_name)
        # Find the hex value
        for hex_val, (mnem, _, _) in OPCODE_MAP_UNIFIED.items():
            if mnem.lower() == opcode_name.lower():
                print(f"   - {opcode_name} -> 0x{hex_val:02X} ({mnem})")
                break

print(f"\nTotal found: {len(found_opcodes)}")

print("\n2. Opcodes NOT found in unified table:")
missing_opcodes = []
for opcode_name in reported_unknown:
    if opcode_name.lower() not in known_mnemonics:
        missing_opcodes.append(opcode_name)
        print(f"   - {opcode_name}")

print(f"\nTotal missing: {len(missing_opcodes)}")

# Check for similar opcodes
print("\n3. Checking for similar opcodes in unified table:")
for missing in missing_opcodes:
    similar = []
    for mnem in known_mnemonics:
        # Check if the missing opcode is a substring or vice versa
        if missing in mnem or mnem in missing:
            similar.append(mnem)
        # Check specific patterns
        elif missing.startswith("assign_") and mnem.startswith("store_"):
            similar.append(mnem)
        elif missing.startswith("ne_") and mnem.startswith("ne_"):
            similar.append(mnem)
        elif missing.startswith("ge_") and mnem.startswith("ge_"):
            similar.append(mnem)
        elif missing.startswith("gt_") and mnem.startswith("gt_"):
            similar.append(mnem)
        elif missing.startswith("eq_") and mnem.startswith("eq_"):
            similar.append(mnem)
    
    if similar:
        print(f"\n   {missing} might be related to:")
        for s in similar:
            print(f"      - {s}")

# Look for patterns in opcode ranges
print("\n4. Checking opcode ranges for patterns:")
comparison_opcodes = ["le_", "ge_", "gt_", "eq_", "ne_"]
conversion_opcodes = ["cnv_"]
assignment_opcodes = ["assign_", "store_"]

for prefix in comparison_opcodes:
    opcodes = [m for m in known_mnemonics if m.startswith(prefix)]
    if opcodes:
        print(f"\n   {prefix}* opcodes: {', '.join(sorted(opcodes))}")

for prefix in conversion_opcodes:
    opcodes = [m for m in known_mnemonics if m.startswith(prefix)]
    if opcodes:
        print(f"\n   {prefix}* opcodes: {', '.join(sorted(opcodes))}")

for prefix in assignment_opcodes:
    opcodes = [m for m in known_mnemonics if m.startswith(prefix)]
    if opcodes:
        print(f"\n   {prefix}* opcodes: {', '.join(sorted(opcodes))}")