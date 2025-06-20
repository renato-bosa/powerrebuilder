# DataWindow Extraction Fix Report

## Issue Summary
DataWindow extraction was failing with "All extraction strategies failed" errors despite the data being present in PBD files.

## Root Cause Analysis
Investigation revealed:
1. DataWindow SQL data was present in UTF-16 LE format in the PBD files
2. The extraction logic was not properly detecting and extracting this UTF-16 encoded data
3. The DataWindow extractor was expecting different data formats than what was provided

## Fixes Implemented

### 1. Direct UTF-16 Detection
Added direct detection of PBSELECT patterns in UTF-16 LE format:
```python
pbselect_utf16 = b'P\x00B\x00S\x00E\x00L\x00E\x00C\x00T\x00'
utf16_pos = binary_data.find(pbselect_utf16)
```

### 2. UTF-16 Extraction Logic
Implemented proper UTF-16 LE decoding that handles the PowerBuilder format:
```python
def _extract_utf16_syntax(data: bytes, start_pos: int) -> str | None:
    # Decode UTF-16 LE character by character
    # Handle only printable ASCII and whitespace
```

### 3. Dual Extraction Attempts
Modified extraction to try both with and without DAT headers:
- First attempt: With DAT headers intact
- Second attempt: Raw data without DAT headers

### 4. Enhanced Logging
Added detailed logging to track extraction progress and identify issues.

## Test Results

From the test run, we observed successful extraction:

```
Successfully extracted 625 characters of DataWindow syntax for d_remove_outsourced_job_ds.dwo
Successfully extracted 442 characters of DataWindow syntax for d_remove_outsourced_link_ds.dwo  
Successfully extracted 547 characters of DataWindow syntax for d_paragon_member_detail_ds.dwo
```

DataWindow files are now being properly extracted and saved as:
- `.srd` files (DataWindow source definition)
- `.sql` files (Extracted SQL statements)

## Files Modified

1. `/Users/michael/Projects/sime-finch/extract/pbd/io/file_operations.py`
   - Added `_extract_utf16_syntax()` function
   - Modified `_extract_datawindow_syntax()` to include direct UTF-16 detection
   - Enhanced `_process_datawindow()` with dual extraction attempts

## Impact

This fix resolves the DataWindow extraction failures and enables proper extraction of DataWindow SQL and definitions from PowerBuilder PBD files. The extraction success rate should improve from near 0% to a significant percentage (exact rate depends on how many DataWindows are in compiled PDW format vs source format).

## Next Steps

1. Run full extraction on all PBD files to verify the fix works across the entire codebase
2. Monitor for any edge cases or DataWindows that still fail extraction
3. Consider adding support for additional DataWindow formats if needed