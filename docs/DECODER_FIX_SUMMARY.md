# PowerBuilder Decoder Fix Summary

## Issue Identified

The PowerBuilder decoder v2 was failing to fix position-based corruptions like "a*dress" -> "address". Investigation revealed two key problems:

### 1. Control Byte Decoding Interference
The v2 decoder was trying to decode control byte sequences BEFORE applying position-based corruption fixes. When it saw `b'a*dress'` (where `*` is `\x2a`), it would:
- Find `\x2a\x64` (asterisk followed by 'd') 
- Map this to 'd' according to control_byte_map
- Result: "a" + "d" + "ress" = "adress" (incorrect)

This prevented the dictionary-based fixing from ever running.

### 2. Heuristic Pattern Too Restrictive
In `data_block.py`, the pattern to detect PowerBuilder corruption only looked for uppercase letters after asterisks:
```python
pb_pattern = re.compile(r'[a-zA-Z]\*[A-Z]|[A-Z]\*[A-Z]')
```
This meant lowercase corruptions like "a*dress" wouldn't trigger the decoder at all.

## Solution Implemented

### 1. Created PowerBuilder Decoder v3
- Removed aggressive control byte decoding
- Prioritizes position-based dictionary fixing for text content
- Only applies control sequences when confident it's binary data
- Better heuristics to detect text corruptions vs binary control sequences

### 2. Fixed Integration in data_block.py
- Updated to use decoder v3
- Fixed the heuristic pattern to detect all corruption cases:
```python
pb_pattern = re.compile(r'[a-zA-Z]\*[a-zA-Z]|\b\w*\*\w*\b')
```

## Results

Before fix:
- "a*dress" -> "adress" ❌
- "COL*MN" -> "COLUMN" ✓ (uppercase worked)
- "trea*ment" -> "treament" ❌

After fix:
- "a*dress" -> "address" ✓
- "COL*MN" -> "COLUMN" ✓
- "trea*ment" -> "treatment" ✓
- SQL statements with corruption are properly fixed ✓

## Files Modified

1. **Created**: `/extract/pbd/utils/powerbuilder_decoder_v3.py`
   - New decoder implementation without control byte interference
   - Improved corruption detection logic
   - Better pattern matching for edge cases

2. **Modified**: `/extract/pbd/structures/data_block.py`
   - Changed import from decoder_v2 to decoder_v3
   - Fixed heuristic pattern to catch lowercase corruptions

3. **Created**: `/tests/test_powerbuilder_decoder_v3.py`
   - Comprehensive test suite for the fixed decoder
   - Tests edge cases and SQL corruption scenarios

## Key Insight

The corruption is **position-based** (certain byte positions get corrupted as asterisks), not a character substitution cipher. The fix properly implements the solution described in `POSITION_BASED_CORRUPTION_SOLUTION.md` by:

1. First decoding bytes to text normally
2. Detecting corruption patterns (asterisks within words)
3. Using domain dictionary to find correct replacements
4. Only applying fixes when confident it's text corruption, not binary data

The decoder now correctly handles the medical/dental domain corruptions that were failing before.