# P-code Format Analysis and Resolution

## Problem Statement

The PowerBuilder decompiler was failing to decode P-code from extracted .fun files, with errors indicating the data didn't match expected P-code format.

## Root Cause Analysis

Through detailed investigation, we discovered:

1. **Extracted files contain full object data, not just P-code**
   - The .fun files contain complete PowerBuilder object structures
   - P-code is embedded within these structures, not stored separately
   - The initial bytes (03 00 76 40) are object type/version markers, not P-code

2. **Object Structure Format**
   ```
   Header: HA$PBExportHeader$<object_name>\n$PBExportComments$\n
   Object Data:
   - Type marker: 0x0003
   - Object type: 0x4076 (related to 0x4077 base for functions)
   - Version info: 0x00100001
   - Metadata, properties, strings (UTF-16)
   - P-code instructions interleaved throughout
   ```

3. **P-code is not contiguous**
   - Instructions are mixed with data throughout the object
   - Cannot simply extract a "P-code section" and decode it
   - Need to parse the entire object structure first

## Solution Implemented

1. **Created ObjectParser (decompile/analysis/object_parser.py)**
   - Parses PowerBuilder object structure
   - Extracts object type, version, and metadata
   - Identifies regions containing P-code
   - Returns parsed object with P-code data

2. **Updated ExtractedFileDecompiler**
   - Uses ObjectParser before attempting P-code decoding
   - Passes extracted P-code data to decoder
   - Handles cases where no P-code is found

3. **Fixed Python compatibility issues**
   - Resolved dataclass inheritance problems for Python 3.9
   - Fixed field ordering issues in AST nodes

## Current Status

The core architecture is now correct:
1. Extract → produces object files (.fun, .str, etc.)
2. Decompile → parses objects, extracts P-code, decodes instructions
3. Parse → converts decompiled code to AST
4. Generate → produces target language code

However, there are still some issues:
- Import dependencies (missing 'magic' module)
- P-code decoder may need updates to handle the specific format
- Need to implement proper P-code extraction from interleaved data

## Next Steps

1. **Fix import issues**
   - Remove or make optional the 'magic' module dependency
   - Resolve circular imports in the codebase

2. **Enhance P-code extraction**
   - Study reference implementations more closely
   - Implement proper extraction of interleaved P-code
   - Handle different PowerBuilder versions

3. **Add pseudocode output**
   - Implement intermediate representation
   - Output pseudocode for debugging and verification

4. **Complete pipeline testing**
   - Run full pipeline with test data
   - Verify output quality
   - Compare with reference decompiler output

## Code References

- Object parser: decompile/analysis/object_parser.py
- Updated decompiler: decompile/decompile_coordinator.py:66-89
- P-code detector: decompile/analysis/pcode_detector.py:64-91
- Debug scripts: scripts/debug/analyze_fun_structure.py

## Related Issues

- Chinese/garbled characters in output: Caused by treating binary as text
- Parser finding 0 files: Fixed by reordering pipeline
- AttributeError PowerBuilderVersion: Fixed incorrect usage