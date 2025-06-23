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
    0xEC: "LE_LONG",
}

# Opcodes reported as unknown in logs
unknown_from_logs = [
    0xC4,
    0xC6,
    0x1E,
    0xEB,
    0xEA,
    0xC7,
    0xED,
    0xDC,
    0x0F,
    0x1A,
    0x0E,
    0x8A,
    0x19,
    0x1B,
    0x95,
]


for hex_val in unknown_from_logs:
    if hex_val in reference_opcodes:
        pass
