# Opcode Analysis Summary

## Executive Summary

The opcodes you listed (jumpfalse, assign_uint, etc.) are NOT actually missing from our implementation. The real issue is that our opcode table has incorrect mappings and is missing many opcodes that exist in the PowerBuilder specification.

## Key Findings

### 1. Correctly Mapped Opcodes
These opcodes are already in our unified table with the correct values:
- `jumpfalse` → 0x03 (JUMPFALSE) ✓
- `jumptrue` → 0x02 (JUMPTRUE) ✓
- `store_return_val` → 0x01 (STORE_RETURN_VAL) ✓
- `dbstop` → 0x08 (DBSTOP) ✓
- `dbclose` → 0x09 (DBCLOSE) ✓
- `index` → 0x28 (INDEX) ✓
- `push_const_dec` → 0x36 (PUSH_CONST_DEC) ✓

### 2. Incorrectly Mapped Opcodes
These opcodes exist in our table but with wrong hex values:
- `le_dec`: We have 0xDA, should be 0xEE
- `le_float`: We have 0xDB, should be 0xEF
- `le_long`: We have 0xD8, should be 0xEC
- `cnv_string_to_char`: We have 0x87, should be 0xA2

### 3. Missing Opcodes
These opcodes are not in our unified table at all:
- `assign_int` → 0x80
- `assign_uint` → 0x81
- `assign_long` → 0x82
- `assign_string` → 0x88
- `assign_time` → 0x89
- `assign_obinst` → 0x8A
- `cnv_long_to_uint` → 0x93
- `cnv_float_to_long` → 0x9A
- `cnv_string_to_chararray` → 0xA4
- `eq_float` → 0xAB
- `eq_ulong` → 0xA9
- `ne_double` → 0xBC
- `ne_long` → 0xB8
- `ne_char` → 0xC3
- `ne_obinst` → 0xC4
- `ne_binary` → 0xBF
- `gt_uint` → 0xC7
- `gt_ulong` → 0xC9
- `gt_datetime` → 0xD0
- `ge_double` → 0xE4
- `ge_datetime` → 0xE8
- `ge_char` → 0xE9

### 4. The Unknown Opcodes in Logs
The hex values being reported as unknown in `logs/unknown_opcodes.log` (0xC4, 0xC6, 0xC7, etc.) are actually valid opcodes:
- 0xC4 = NE_OBINST (not equal object instance)
- 0xC6 = GT_INT (greater than integer)
- 0xC7 = GT_UINT (greater than unsigned integer)
- 0x8A = ASSIGN_OBINST (assign object instance)

## Root Cause

The decompiler is correctly identifying that these opcodes are unknown **to our implementation**, not that they're invalid opcodes. Our unified opcode table is incomplete and has some incorrect mappings.

## Recommended Actions

1. **Update the unified opcode table** (`decompile/opcode_tables/unified.py`) to include all missing opcodes from the reference implementation

2. **Fix incorrect opcode values** for LE_DEC, LE_FLOAT, LE_LONG, and CNV_STRING_TO_CHAR

3. **Implement opcode handlers** in the stack simulator for the newly added opcodes

4. **Update the missing_opcodes.yaml** to remove entries that are now properly mapped

The opcodes are well-documented in the reference implementation at `reference/implementations/Opcodes.cs`, which should be used as the authoritative source for opcode definitions.