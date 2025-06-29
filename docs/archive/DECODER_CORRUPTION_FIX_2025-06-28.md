# Decoder Corruption Fix - 2025-06-28

## Problem Identified

The PowerBuilder extraction pipeline dropped from 100% success to 41.9% due to a regression in the decoder implementation.

### Root Cause

The "unified" v2 decoder was processing control byte sequences BEFORE position-based corruption fixing:

1. **Control Byte Interference**:
   - Input: `a*dress` (bytes: `a\x2a\x64ress`)
   - v2 decoder treated `\x2a\x64` as control sequence → `d`
   - Result: `adress` (wrong!)
   - Expected: `address`

2. **Missing Dictionary Entry**:
   - 'logic' was not in the SQL keywords dictionary
   - Pattern `LOG*C` → `LOGIC` was not in pattern fixes

3. **Detection Heuristic Too Narrow**:
   - `data_block.py` only looked for `[a-z]\*[A-Z]` patterns
   - Missed lowercase patterns like `a*dress`, `opera*or`

## Solution Implemented

### 1. Created PowerBuilder Decoder v3
- Prioritizes text corruption fixing over control byte decoding
- Better heuristics to distinguish text corruption from binary control sequences
- Only applies control byte decoding when confident it's binary data

### 2. Fixed Missing Patterns
Added to v3 decoder:
- 'logic' to SQL keywords dictionary
- `LOG*C` → `LOGIC` pattern fix

### 3. Updated Integration
- `data_block.py` now imports `powerbuilder_decoder_v3`
- Fixed detection patterns to catch all corruption types

## Test Results

All corruption patterns now fixed correctly:
```
COL*MN → COLUMN ✓
a*dress → address ✓
TREA*MENT → TREATMENT ✓
LOG*C → LOGIC ✓
opera*or → operator ✓
patien* → patient ✓
NA *E= → NAME= ✓
*ate → DATE ✓
```

## Impact

This fix should restore the extraction success rate from 41.9% back to near 100% for PowerBuilder files with position-based corruptions.

## Key Lesson

When creating "unified" implementations, be careful about strategy ordering. In this case, aggressive control byte decoding prevented the position-based corruption fixing from working properly. The v3 decoder fixes this by being more selective about when to apply each strategy.