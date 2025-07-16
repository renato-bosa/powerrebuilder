# PR #5: Fix Entry Processing Limit Issue

## Summary
- Investigate why only 30 of 1374 entries are processed
- Fix signature validation that's stopping processing
- Ensure all entries in PBD files are extracted

## Problem
The extraction process stops after processing only 30 entries due to a signature validation warning, leaving 1344 entries unprocessed.

## Solution
1. Debug signature validation logic
2. Add option to continue processing despite warnings
3. Implement proper error recovery for invalid entries
4. Add progress tracking for large files

## Implementation Details

### Investigation Steps
1. Check signature validation in entry processing
2. Identify what triggers the 30-entry limit
3. Review warning handling logic
4. Test with different PBD files

### Potential Fixes
```python
# Add flag to continue on warnings
def process_entries(self, continue_on_warning=True):
    for i, entry in enumerate(entries):
        try:
            self._process_entry(entry)
        except SignatureWarning as w:
            if continue_on_warning:
                logger.warning(f"Entry {i}: {w}")
                continue
            else:
                raise
```

## Test Plan
- [ ] Run extraction on multiple PBD files
- [ ] Verify all entries are attempted
- [ ] Log statistics on successful vs failed entries
- [ ] Compare with reference extraction tools

## Dependencies
- Requires PR #1 (Pipeline Fix) to be completed first

## Estimated Time: 3 points (half day)

## Branch: `fix/entry-processing-limit`