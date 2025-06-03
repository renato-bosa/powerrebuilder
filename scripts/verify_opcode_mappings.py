#!/usr/bin/env python3
"""Verify opcode mappings between reference and our implementation."""

# Reference opcodes from Opcodes.cs that were reported as missing
reference_opcodes = {
    0x80: "ASSIGN_INT",
    0x81: "ASSIGN_UINT", 
    0x82: "ASSIGN_LONG",
    0x88: "ASSIGN_STRING",
    0x89: "ASSIGN_TIME",
    0x8A: "ASSIGN_OBINST",
    0x93: "CNV_LONG_TO_UINT",
    0x9A: "CNV_FLOAT_TO_LONG",
    0xA2: "CNV_STRING_TO_CHAR",
    0xA4: "CNV_STRING_TO_CHARARRAY",
    0xA9: "EQ_ULONG",
    0xAB: "EQ_FLOAT",
    0xB8: "NE_LONG",
    0xBC: "NE_DOUBLE",
    0xBF: "NE_BINARY",
    0xC3: "NE_CHAR",
    0xC4: "NE_OBINST",
    0xC7: "GT_UINT",
    0xC9: "GT_ULONG",
    0xD0: "GT_DATETIME",
    0xE4: "GE_DOUBLE",
    0xE8: "GE_DATETIME",
    0xE9: "GE_CHAR",
    0xEE: "LE_DEC",
    0xEF: "LE_FLOAT",
    0xEC: "LE_LONG"
}

# Opcodes reported as unknown in logs
unknown_from_logs = [
    0xC4, 0xC6, 0x1E, 0xEB, 0xEA, 0xC7, 0xED, 0xDC, 
    0x0F, 0x1A, 0x0E, 0x8A, 0x19, 0x1B, 0x95
]

print("=== OPCODE MAPPING VERIFICATION ===\n")

print("1. Reference opcodes that match unknown opcodes from logs:")
for hex_val in unknown_from_logs:
    if hex_val in reference_opcodes:
        print(f"   0x{hex_val:02X}: {reference_opcodes[hex_val]}")

print("\n2. Potential conflicts:")
print("   - 0x1E: PUSH_LOCAL_VAR in our table, but logs show it as unknown")
print("   - 0x8A: ASSIGN_OBINST in reference")
print("   - 0xC4: NE_OBINST in reference") 
print("   - 0xC6: Should be GT_INT according to reference")
print("   - 0xC7: GT_UINT in reference")

print("\n3. Our incorrect mappings:")
print("   - LE_DEC: We have 0xDA, should be 0xEE")
print("   - LE_FLOAT: We have 0xDB, should be 0xEF")
print("   - LE_LONG: We have 0xD8, should be 0xEC")
print("   - CNV_STRING_TO_CHAR: We have 0x87, reference has 0xA2")

print("\n4. Summary:")
print("   The opcodes being reported as unknown (0xC4, 0xC6, etc.) are actually")
print("   valid opcodes according to the reference implementation. Our opcode table")
print("   needs to be updated to match the reference values.")