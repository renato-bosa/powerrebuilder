# Pipeline Restoration Status

## Summary
The PowerRebuilder pipeline was broken due to the file reorganization in commit f2917007. We've made significant progress fixing import errors and missing modules.

## Completed Fixes

### 1. Import Errors Fixed
- ✓ Fixed `Any` type import in `resource_utils.py`
- ✓ Fixed `any` vs `Any` in `database_schema_extractor.py`
- ✓ Fixed attribute name mismatches in test script:
  - `nod_offset` → `address`
  - `entry_count` → `numberofentries`
  - `entry_name` → `objectname`
  - `dat_offset` → `offset`
  - `entry_size` → `objectsize`

### 2. Missing Modules Restored
- ✓ Copied `src/model/transaction` from archive
- ✓ Copied `src/parse/utils` from archive
- ✓ Copied `src/common/types` from archive

### 3. Dependencies
- ✓ Installed all project dependencies including `lark` parser
- ✓ Created virtual environment with `uv`

## Current Status

### Extraction Stage: ✓ WORKING
- Successfully extracts header information
- Extracts 1 node with 1374 entries (only 30 entries fully processed due to warning)
- Sample entries extracted include .men, .apl, .udo, .bin, .win, and .bmp files

### Parsing Stage: ✗ NEEDS FIXES
- Grammar file exists at correct location
- Parser class name mismatch fixed (PowerBuilderParser → EnhancedPowerBuilderParser)
- Still failing with grammar loading issues

### Decompilation Stage: ✓ PARTIALLY WORKING
- Decodes instructions but with unknown opcodes
- Opcode definitions likely need to be restored from .pyc files

### Generation Stage: ✓ WORKING
- Mock generation succeeds for both Flutter and Python

## Remaining Issues

1. **Main Pipeline Error**: Type error in `retrieve_bytes_from_file` - receiving bytes instead of file handle
2. **Missing Opcode Definitions**: All opcodes showing as unknown (0x00, 0x01, etc.)
3. **Grammar Loading**: Parser can't load the grammar file properly
4. **Entry Processing**: Only processing 30 of 1374 entries due to signature validation

## Next Steps

1. Fix the file handle vs bytes issue in the main extraction pipeline
2. Restore opcode definitions from compiled .pyc files
3. Debug grammar loading in the parser
4. Investigate why entry processing stops at 30 entries

## Test Command
```bash
source .venv/bin/activate && python test_extraction_stages.py input/dcm_detailobjects.pbd
```