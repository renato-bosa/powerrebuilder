# PBD Extraction Fix Summary

## Root Cause Analysis

The PBD extraction was only extracting 4 out of 2780 objects (0.14%) due to overly restrictive limits in the node entry extraction logic.

## Issues Found and Fixed

### 1. Entry Count Limit in `extract_entry_definitions_from_node_block`
**Location**: `src/extract/pbd/structures/node.py`, line 146

**Problem**: 
```python
# OLD CODE
max_entries = min(entry_count, 10000) if entry_count < 10000 else 1000
```
When `entry_count >= 10000`, the code would cap extraction at only 1000 entries.

**Fix**:
```python
# NEW CODE
if entry_count > 100000:
    # This is likely corrupted
    logger.warning("Suspicious entry count %d, capping at 10000", entry_count)
    max_entries = 10000
else:
    # Trust the entry count from the NOD header
    max_entries = entry_count
```

### 2. Conservative Read Size for Node Entries
**Location**: `src/extract/pbd/structures/node.py`, line 434

**Problem**:
```python
# OLD CODE
if entry_count > 1000:
    # This seems like a corrupted entry count
```
The code treated any node with more than 1000 entries as "corrupted" and would use a conservative read approach.

**Fix**:
```python
# NEW CODE
if entry_count > 100000:
    # This seems like a corrupted entry count
```
Raised the threshold to 100,000 entries, as large PBD files commonly have thousands of entries.

## Impact

These fixes should allow the extraction process to handle PBD files with thousands of entries correctly:
- Files with up to 100,000 entries will be processed normally
- The 10MB read buffer is sufficient for most use cases (can hold ~30,000 typical entries)
- Only truly corrupted files with unrealistic entry counts (>100,000) will be capped

## Expected Results

After these fixes:
- Extraction rate should increase from 0.14% to near 100% for valid PBD files
- All 2780 objects should be extracted successfully
- The extraction process will handle large commercial PowerBuilder applications correctly

## Testing

To verify the fix:
```bash
python test_extraction_fix.py <your_pbd_file>
```

This will show:
- Total number of files extracted
- Breakdown by file type
- Success/failure status