# P-code Extraction Debug Report

## Issue Summary

P-code files (`.fun` files) are not being created during the extraction process because of a flawed detection logic in `extract/pbd_core/core.py`.

## Root Cause

The P-code detection logic (lines 35-37 in `core.py`) checks if:
```python
is_potential_pcode: bool = (entry.objectname.lower().endswith(tuple(SOURCE_EXTENSIONS)) and
                     ("function" in entry.version.lower() or "event" in entry.version.lower())) or \
                     entry.objectname.lower().endswith((".srf", ".srj"))
```

However:
- The `entry.version` field contains the PowerBuilder version number (e.g., "0.6.0.0")
- It does NOT contain object type descriptions like "function" or "event"
- Therefore, regular source files (.sru, .srw, etc.) are never detected as P-code
- Only .srf and .srj files are detected as P-code due to the fallback condition

## Evidence

From analyzing the `dcm_email.pbd` file:
- All entries have version = "0.6.0.0" (PowerBuilder 6.0)
- Object names include: n_cst_mailsession.udo, n_cst_pdfwriter.udo, n_cst_email.udo, w_mail_test.win
- None of these would be detected as P-code

## Impact

1. No `.fun` files are created for source code objects
2. P-code content is not extracted separately
3. Decompilation tools expecting `.fun` files will not work

## Potential Solutions

### Option 1: Fix Detection Logic (Recommended)
Remove the version string check and assume all source files contain P-code:
```python
is_potential_pcode: bool = entry.objectname.lower().endswith(tuple(SOURCE_EXTENSIONS))
```

### Option 2: Use Object Type Information
If object type information is available elsewhere in the entry data, use that instead of the version field.

### Option 3: Heuristic Detection
Check the actual content of the extracted data to determine if it contains P-code.

## Test Script Results

The test script confirmed that:
- Source files with PB version strings: NOT detected as P-code ❌
- Source files with "function"/"event" in version: Detected as P-code ✓
- .srf/.srj files: Always detected as P-code ✓

## Recommendation

The detection logic should be updated to treat all source code files as potentially containing P-code, regardless of the version string content.