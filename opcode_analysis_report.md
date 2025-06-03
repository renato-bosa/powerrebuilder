# Opcode Analysis Report

## Summary

After analyzing the decompilation output and our opcode implementation, I found that the opcode names you provided (like "jumpfalse", "assign_uint", etc.) are not actually the issue. These names appear to be from a different context or possibly from the higher-level output.

## The Real Issue

The actual unknown opcodes being reported in the logs are hex values with variants:

### Unknown Opcodes from logs/unknown_opcodes.log:
- **0x0E** - Has variants (0x00, 0x02, 0xC2, 0xC3, 0xC4, 0xC5, 0xC6, 0x1D)
- **0x0F** - Has variants (0x00, 0x01, 0x04, 0x2B, 0x3A, 0xC2, 0xC3, 0xC4, 0xC5, 0xC6)
- **0x19** - Has variants (0x00, 0x15, 0xC6, 0xC7, 0xEC)
- **0x1A** - Has variants (0x00, 0xC7, 0xCA, 0xEC)
- **0x1B** - Has variants (0x00, 0xC2, 0xEC)
- **0x1E** - Has variants (0x00, 0xC4, 0xC8, 0xEC)
- **0x8A** - Has variants (multiple)
- **0x95** - Has variants (multiple)
- **0xC4** - Has variants (extensive list)
- **0xC6** - Has variants (extensive list)
- **0xC7** - Has variants (extensive list)
- **0xDC** - Has variants (multiple)
- **0xEA** - Has variants (multiple)
- **0xEB** - Has variants (multiple)
- **0xED** - Has variants (multiple)

## Key Findings

1. **The opcodes you listed ARE defined in our tables:**
   - jumpfalse -> 0x03 (JUMPFALSE)
   - jumptrue -> 0x02 (JUMPTRUE)
   - store_return_val -> 0x01 (STORE_RETURN_VAL)
   - dbstop -> 0x08 (DBSTOP)
   - dbclose -> 0x09 (DBCLOSE)
   - index -> 0x28 (INDEX)
   - push_const_dec -> 0x36 (PUSH_CONST_DEC)
   - le_dec -> 0xDA (LE_DEC)
   - le_long -> 0xD8 (LE_LONG)
   - le_float -> 0xDB (LE_FLOAT)
   - cnv_string_to_char -> 0x87 (CNV_STRING_TO_CHAR)
   - cnv_char_to_string -> 0x6E (CNV_CHAR_TO_STRING)

2. **The opcodes NOT found in our tables are:**
   - assign_uint, assign_int, assign_long, assign_time, assign_string, assign_obinst
   - ge_double, ge_datetime, ge_char
   - gt_datetime, gt_ulong, gt_uint
   - eq_float, eq_ulong
   - ne_double, ne_obinst, ne_binary, ne_long, ne_char
   - cnv_long_to_uint, cnv_string_to_chararray, cnv_float_to_long

3. **These missing opcodes are already captured in missing_opcodes.yaml** as variants of the extended opcodes (0xC4, 0xC5, 0xC6, 0xC7, etc.)

## The Real Problem

Looking at the reference implementation (reference/implementations/Opcodes.cs), I discovered that:

1. The missing opcodes ARE defined, but with values > 0xFF:
   - ASSIGN_INT = 0x80
   - ASSIGN_UINT = 0x81
   - ASSIGN_LONG = 0x82
   - ASSIGN_STRING = 0x88
   - ASSIGN_TIME = 0x89
   - ASSIGN_OBINST = 0x8A
   - CNV_LONG_TO_UINT = 0x93
   - CNV_STRING_TO_CHAR = 0xA2
   - CNV_FLOAT_TO_LONG = 0x9A
   - CNV_STRING_TO_CHARARRAY = 0xA4
   - EQ_FLOAT = 0xAB
   - EQ_ULONG = 0xA9
   - NE_DOUBLE = 0xBC
   - NE_LONG = 0xB8
   - NE_CHAR = 0xC3
   - NE_OBINST = 0xC4
   - NE_BINARY = 0xBF
   - GT_UINT = 0xC7
   - GT_ULONG = 0xC9
   - GT_DATETIME = 0xD0
   - GE_DOUBLE = 0xE4
   - GE_DATETIME = 0xE8
   - GE_CHAR = 0xE9
   - LE_DEC = 0xEE (not 0xDA as in our table)
   - LE_FLOAT = 0xEF (not 0xDB as in our table)
   - LE_LONG = 0xEC (not 0xD8 as in our table)

2. The hex values 0xC4, 0xC6, etc. that appear in our logs are NOT the actual opcodes but are being misidentified as single-byte opcodes when they might be part of multi-byte opcodes or have different meanings.

## Conclusion

The issue is a mismatch between our opcode definitions and the actual PowerBuilder opcode values. Our unified opcode table has incorrect values for many opcodes. We need to:

1. Update the unified opcode table to match the reference implementation
2. Handle opcodes with values > 0xFF properly
3. Fix the incorrect opcode values (e.g., LE_DEC should be 0xEE not 0xDA)

The "Unknown opcode" messages in the logs are showing the correct hex values that need to be mapped to their proper mnemonics according to the reference implementation.