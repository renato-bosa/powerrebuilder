#!/usr/bin/env python3
"""Test opcode loading."""

from decompile.opcode_tables import OpcodeManager
from extract.pbd_core.version_detector import PowerBuilderVersion

# Test loading opcodes
version = PowerBuilderVersion(8, 0, False)
opcodes = OpcodeManager.get_opcode_table(version)

print(f"Total opcodes loaded: {len(opcodes)}")
print(f"Opcode 0xFF present: 0xFF in opcodes = {0xFF in opcodes}")
print(f"Opcode 0xF0 present: 0xF0 in opcodes = {0xF0 in opcodes}")
print(f"Opcode 0xF6 present: 0xF6 in opcodes = {0xF6 in opcodes}")

if 0xFF in opcodes:
    print(f"Opcode 0xFF = {opcodes[0xFF]}")
if 0xF0 in opcodes:
    print(f"Opcode 0xF0 = {opcodes[0xF0]}")
if 0xF6 in opcodes:
    print(f"Opcode 0xF6 = {opcodes[0xF6]}")

# Check what's in the opcode table around 0xF0-0xFF
print("\nOpcodes from 0xF0 to 0xFF:")
for i in range(0xF0, 0x100):
    if i in opcodes:
        print(f"  0x{i:02X}: {opcodes[i]}")
    else:
        print(f"  0x{i:02X}: NOT FOUND")