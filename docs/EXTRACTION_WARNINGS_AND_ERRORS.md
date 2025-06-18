# PowerBuilder Extraction Warnings and Errors

## Overview

This document systematically catalogs all warnings and errors encountered during the PowerBuilder extraction phase. The extraction process is experiencing significant issues, particularly with DataWindow objects and SQL extraction.

## Summary Statistics

- **Total Warnings**: 6,670
- **Total Errors**: 188
- **DataWindow Extraction Failures**: 1,772
- **Partial/Truncated Extractions**: 2,405

## Major Warning Categories

### 1. DataWindow Extraction Failures

**Pattern**: DataWindow objects failing to extract and being saved as binary files instead of parsed SQL/SRD content.

**Root Cause**: Corrupted or misinterpreted data length fields showing a consistent value of `1146094070` bytes across many different files.

**Example**:
```
WARNING: DAT block for 'd_remove_outsourced_job_ds.dwo' at offset 4608: 
Declared data length 1146094070 extends beyond file size 3493888 (ends at 1146098690). 
Reading up to EOF. Marking as partial.
```

**Affected Files** (Top 5 by warning count):
1. `dcms_reports.pbd` - 206 warnings
2. `dcm_hicaps.pbd` - 128 warnings  
3. `dcm_detailobjects.pbd` - 110 warnings
4. `dcm_treatmentplan.pbd` - 107 warnings
5. `dcm_patient.pbd` - 105 warnings

### 2. SQL Corruption Patterns

**Location**: `/Users/michael/Projects/sime-finch/extract/pbd/structures/data_corruption_fix.py`

**Common Corruption Types**:
1. **Asterisk Insertion**: Words split by asterisks
   - `"add * ess_id"` → `"address_id"`
   - `"COL *L MN"` → `"COLUMN"`
   - `"table.*column"` → `"table.column"`

2. **Truncated SQL**: SQL files containing only partial content
   ```sql
   -- SQL from DataWindow: d_direct_debit_lines_2arg_bw.dwo
   PBSELECT(VERSION(400)
   ```

3. **Missing SQL Content**: DataWindows extracted without their SQL definitions

### 3. Byte-Level Recovery Warnings

**Pattern**: All PBD files show placeholder warnings for byte-level recovery attempts

**Example**:
```
WARNING: Attempt 4: Byte-level recovery for dcm_patient.pbd (enable_byte_recovery=True) 
is currently a placeholder.
```

### 4. Unknown Opcode Errors

**Issue**: Over 100 instances of unrecognized PowerBuilder opcodes during extraction

**Common Unknown Opcodes**:
- `0xC4`, `0xC6`, `0x1E`, `0xEB`, `0xEA`, `0xC7`, `0xED`, `0xDC`

**Example Log Entry**:
```
2025-06-03 14:44:07,456 - Opcode: 0xC4 - Pos: 7590 - Obj: unknown - Context: c4 84 56 c4 8f 2a c7
```

### 5. Directory Access Errors

**Count**: 80+ occurrences

**Pattern**: Extraction attempting to read directories as files

**Example**:
```
ERROR: [Errno 21] Is a directory: '/Users/michael/Projects/sime-finch/output/extracted/proxy.pbd/proxy.pbd'
```

### 6. Function Call Errors

**Issue**: Missing required arguments in extraction functions

**Example**:
```
ERROR: Failed to extract dcm_detailobjects.pbd due to an unexpected error: 
extract_nods() missing 1 required positional argument: 'block_size'
TypeError: extract_nods() missing 1 required positional argument: 'block_size'
```

## Root Causes Analysis

### 1. Critical DAT Block Format Bug
**CRITICAL ISSUE FOUND**: There's a data structure mismatch in the DAT block handling:
- `data_block.py` line 25 defines data length as 2 bytes: `DAT_DATA_LEN_FIELD_LEN = 2`
- `get_binary_with_dat_headers()` line 233 writes it as 4 bytes: `struct.pack("<I", block.data_length_in_block)`
- This mismatch corrupts the DAT block format when reconstructing headers

### 2. Corrupted Data Length Field
The consistent appearance of `1146094070` (0x445001F6) as a data length:
- In little-endian: `F6 01 50 44` which ends with "PD" (possibly PowerBuilder Data marker)
- This appears to be data being misinterpreted as a length field due to incorrect offset calculations
- The 2-byte vs 4-byte mismatch above likely causes reading at wrong offsets

### 3. Missing DataWindow Extractor Modules
**CRITICAL**: The following modules are referenced but don't exist:
- `decompile.analysis.enhanced_datawindow_integration`
- `decompile.analysis.datawindow_extractor`
- Without these modules, ALL DataWindow objects default to binary export
- This explains why 1,772 DataWindow objects failed to extract

### 4. DAT Block Header Recognition Issues
Many DataWindow objects lack proper DAT* headers, preventing proper extraction:
- Files default to binary export when headers aren't recognized
- Chain reading stops prematurely to prevent cascading errors

### 5. Incomplete Extraction Logic
The extraction process appears to:
- Successfully identify DataWindow objects
- Fail to properly parse their internal structure
- Fall back to binary export rather than parsing SQL/SRD content

## Fixes Applied (2025-06-18)

### 1. ✓ FIXED: DAT Block Data Length Field Size (data_block.py:233)
**Commit**: 5178540b
```python
# WAS (WRONG):
header += struct.pack("<I", block.data_length_in_block)  # 4 bytes

# NOW (CORRECT):
header += struct.pack("<H", block.data_length_in_block)  # 2 bytes (unsigned short)
```

### 2. ✓ FIXED: DataWindow Extractors - DAT Header Check Issue
**Commit**: cb3f1d5f
- Modified `datawindow_extractor.py` and `enhanced_datawindow_integration.py`
- Removed early return when DAT headers are missing
- Added header logging for debugging
- Added detection for compiled PDW format DataWindows
- Extractors now attempt extraction regardless of header presence

### 3. ✓ FIXED: Missing block_size Parameter
**Commit**: d27534af
- Fixed `test_pbd_fixtures.py` - added missing BLOCK_SIZE import and parameter
- Note: The error log referencing `extract/pbd_core/core.py` was from an old version (May 30)


## Remaining Issues to Address

### 1. Verify Magic Number Resolution
The 1146094070 (0x445001F6) issue should be resolved by the DAT block fix, but needs verification:
- Run extraction on affected files
- Confirm the magic number no longer appears
- Verify DataWindow extraction success rate improves

### 2. Handle Compiled PDW Format DataWindows
Some DataWindows are in compiled binary format (PDW1000) that cannot be decompiled:
- Implement detection and proper logging for these files
- Consider reverse engineering the PDW format if source is needed
- Document which DataWindows are affected

### 3. Complete SQL Extraction
Many DataWindows show truncated SQL (only "PBSELECT(VERSION(400)"):
- Investigate why SQL extraction is incomplete
- Fix the extraction logic to get full SQL content
- Validate extracted SQL for completeness

### 4. Implement Byte-Level Recovery
Current byte-level recovery is just a placeholder:
- Implement actual recovery strategies for corrupted blocks
- Add checksum validation where possible
- Handle partial block recovery

### 5. Handle Unknown Opcodes
Over 100 instances of unrecognized opcodes:
- Document opcodes: 0xC4, 0xC6, 0x1E, 0xEB, 0xEA, 0xC7, 0xED, 0xDC
- Research their purpose in PowerBuilder bytecode
- Implement handlers or graceful degradation

## Impact on Flutter/Dart Migration

The DataWindow extraction failures significantly impact the ability to:
1. Generate proper data models from SQL definitions
2. Understand data relationships and constraints
3. Create appropriate Flutter widgets for data display
4. Migrate business logic embedded in DataWindows

These issues must be resolved before accurate PowerBuilder to Flutter mapping can occur.

## Summary of Current State (Updated 2025-06-18)

### Critical Issues Fixed:

1. **✓ DAT Block Format Bug**: Fixed 2-byte vs 4-byte mismatch in data length field
2. **✓ DAT Header Requirement Bug**: Extractors now attempt extraction without DAT* headers
3. **✓ Missing Block Size Parameter**: Fixed missing parameter in test file

### Expected Improvements After Fixes:

The three critical fixes should resolve:
- The 1146094070 magic number issue (caused by DAT block misalignment)
- DataWindow objects being rejected due to missing DAT headers
- Test failures due to missing parameters

### Remaining Issues:

1. **Compiled PDW Format**: Some DataWindows are in binary format that cannot be decompiled
2. **Truncated SQL**: SQL extraction often incomplete (needs investigation)
3. **Unknown Opcodes**: Over 100 unrecognized opcodes in decompilation
4. **Byte-Level Recovery**: Still using placeholder implementation

### Next Steps:

1. **Re-run extraction** with the fixes to verify improvements
2. **Measure success rate** - expect significant improvement in DataWindow extraction
3. **Investigate remaining failures** - likely compiled PDW format files
4. **Fix SQL truncation** issue for complete extraction

## Verification Steps

1. **Immediate**: Re-run extraction pipeline on affected PBD files
2. **Verify**: Check that 1146094070 magic number no longer appears
3. **Measure**: Count successful DataWindow extractions vs binary saves
4. **Test**: Run unit tests to ensure no regression
5. **Document**: Update this file with extraction results after fixes