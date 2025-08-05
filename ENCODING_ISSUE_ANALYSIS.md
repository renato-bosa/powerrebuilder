# PowerRebuilder Encoding Issue Analysis

## Root Cause Identified

The extraction code contains an overly aggressive "corruption repair" mechanism that is **creating** corruption rather than fixing it. The PBD files are NOT corrupted - they contain valid UTF-16LE encoded strings.

## The Problem Chain

### 1. Valid UTF-16LE Data in PBD Files
PowerBuilder PBD files store object names in UTF-16LE encoding:
```
Example: "w_main_window" is stored as:
w\x00_\x00m\x00a\x00i\x00n\x00_\x00w\x00i\x00n\x00d\x00o\x00w\x00\x00\x00
```

### 2. Misguided Byte-Order "Fix"
The function `_fix_utf16_byte_order` in `src/extract/utils/binary.py` (lines 486-513) swaps EVERY byte pair:
```python
def _fix_utf16_byte_order(data: bytes) -> bytes | None:
    # Swap each pair of bytes
    fixed = bytearray()
    for i in range(0, len(data), 2):
        if i + 1 < len(data):
            # Swap the byte pair: AB -> BA
            fixed.append(data[i + 1])
            fixed.append(data[i])
```

### 3. Result of Byte Swapping
After swapping valid UTF-16LE data:
```
Original: w\x00_\x00m\x00a\x00i\x00n\x00...
Swapped:  \x00w\x00_\x00m\x00a\x00i\x00n...
```

### 4. Decoding Failure
When the swapped data is decoded as UTF-16LE:
- First character is NULL (\x00)
- String is truncated at first NULL
- Result: Empty string or single character

## Why This Happens

The `decode_powerbuilder_name` function (line 542) tries multiple decoding strategies:
1. Context-based decoding (UTF-16 or ASCII)
2. Auto-detection based on data patterns
3. ASCII/Latin-1 fallback
4. UTF-8 attempt
5. **Byte-order "corrected" UTF-16** ← This is the problem!

The function scores each result and picks the "best" one. However, the byte-swapped version often scores poorly because it produces garbage, but sometimes a single character slips through.

## Evidence in Extracted Files

This explains ALL the symptoms:
- **Single character names**: `a.fun`, `l.fun`, `_.fun` - first valid character after byte swap
- **Non-ASCII characters**: `à.fun` - mangled byte sequences interpreted as extended ASCII
- **SQL as filename**: Parsing offset corruption after "repair" attempts
- **Empty names**: `.fun` - completely NULL result

## The Solution

The fix is straightforward:

1. **Remove or disable the byte-order swapping** in `_fix_utf16_byte_order`
2. **Trust the file format** - PowerBuilder consistently uses UTF-16LE
3. **Simplify decoding logic** - don't try to "fix" valid data

### Quick Fix Option
Comment out or modify the byte-swap strategy in `decode_powerbuilder_name`:
```python
# Strategy 5: Try byte-order corrected UTF-16
# DISABLED - This was corrupting valid UTF-16LE data
# try:
#     if len(data) >= 2 and len(data) % 2 == 0:
#         fixed_data = _fix_utf16_byte_order(data)
#         ...
```

### Proper Fix Option
1. Detect the PBD file encoding mode (Unicode vs ASCII) from the header
2. Use the appropriate decoder consistently throughout
3. Remove speculative "corruption fixes"
4. Add logging to track which decoding method succeeds

## Impact

Fixing this issue will:
- Restore proper PowerBuilder object names
- Enable successful decompilation (which currently fails due to bad filenames)
- Improve the overall extraction success rate from ~6 files to potentially all 54 files
- Maintain the integrity of the original PowerBuilder project structure