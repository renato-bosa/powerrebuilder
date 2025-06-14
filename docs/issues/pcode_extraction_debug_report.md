# P-code Extraction Debug Report

## Issue Summary

The extracted .fun files contain data that doesn't match the expected P-code format, preventing successful decompilation.

## Problem Description

When examining extracted .fun files, the binary data after the PowerBuilder export header doesn't match the expected function structure format used by reference decompilers.

### Example Hex Dump
```
00000000: 4841 2450 4245 7870 6f72 7448 6561 6465  HA$PBExportHeade
00000010: 7224 665f 6765 745f 7573 6572 6e61 6d65  r$f_get_username
00000020: 2e66 756e 0a24 5042 4578 706f 7274 436f  .fun.$PBExportCo
00000030: 6d6d 656e 7473 240a 0300 6e40 0100 1000  mments$...n@....
00000040: 0000 36e0 eb44 a9c8 134f 0800 0000 1000  ..6..D...O......
```

## Analysis Results

### 1. File Format Structure
The .fun files correctly include the PowerBuilder export header:
- Line 1: `HA$PBExportHeader$<objectname>`
- Line 2: `$PBExportComments$`
- Followed by: Binary data

### 2. Expected P-code Format
Based on analysis of PbdViewer and powerbuilder-decompile reference implementations:
```
[0-1]: P-code size (uint16 LE)
[2-3]: Debug info size (uint16 LE)  
[4-5]: Unknown field (uint16 LE)
[6+]: P-code data
[6+code_len]: Debug data (4 bytes per entry)
```

### 3. Actual Data Analysis
The binary data starting at offset 0x38:
```
03 00 6e 40 01 00 10 00 00 00 36 e0 eb 44 a9 c8 13 4f 08 00 00 00 10 00
```

Interpreted as function structure:
- Code length: 3 bytes (0x0003)
- Debug entries: 16494 (0x406e) - **Unrealistic!**
- Unknown: 1 (0x0001)
- Expected total size: 65,985 bytes
- Actual data size: 24 bytes

**This clearly doesn't match the expected format.**

## Root Causes

### 1. Wrong Data Extraction
The data being saved to .fun files might not be P-code at all, but rather:
- Object metadata
- Compressed/encrypted data
- Different structure type

### 2. Extraction Process Issues
The extraction logic in `save_to_file()` skips bytes based on `entry.commentlen`, which might be removing actual P-code data or including wrong data.

### 3. Format Variations
Different PowerBuilder versions might use different P-code formats that we're not handling correctly.

## Investigation Steps Taken

1. Created multiple analysis scripts to examine binary structure
2. Compared with reference implementations (PbdViewer, powerbuilder-decompile)
3. Fixed P-code detector to properly handle export headers
4. Analyzed raw binary data for patterns and structure

## Recommendations

### Immediate Actions
1. **Verify Data Source**: Add logging to understand exactly what data is being extracted from PBD files
2. **Check Entry Types**: Ensure we're correctly identifying which entries contain P-code vs other data
3. **Test Known Good Files**: Create test cases with known P-code to verify the extraction and decoding pipeline

### Long-term Solutions
1. **Implement Proper P-code Detection**: Use heuristics to detect actual P-code vs metadata
2. **Support Multiple Formats**: Add version-specific P-code format handlers
3. **Add Validation**: Verify extracted data matches expected P-code patterns before saving

## Next Steps

1. Add comprehensive logging to the extraction process
2. Create test PBD files with known P-code content
3. Compare extraction results with reference decompiler outputs
4. Implement format validation before saving .fun files