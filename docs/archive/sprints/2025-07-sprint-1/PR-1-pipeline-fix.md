# PR #1: Fix Pipeline File Handle Type Error

## Summary
- Fix type error in `retrieve_bytes_from_file` that's blocking the main pipeline
- Update `_process_entry` to properly handle different file content types
- Ensure extraction pipeline can process all 1374 entries

## Problem
The `_process_entry` function in `src/extract/pbd/extractors/base.py` (line 165) uses undefined `file_handle` variable when it should use `file_content`.

## Solution
1. Replace `file_handle` with `file_content`
2. Add proper type handling for file_content (str/Path/bytes/BinaryIO)
3. Ensure conversion to file handle when needed

## Implementation Details

### Fix 1: Simple variable correction
```python
# Line 165 in _process_entry
data, is_partial = extract_data_from_entry(
    file_content, entry_def_obj, header.is_unicode, block_size, file_size
)
```

### Fix 2: Add type handling
```python
# Convert file_content to proper file handle
if isinstance(file_content, (str, Path)):
    with open(file_content, 'rb') as f:
        data, is_partial = extract_data_from_entry(
            f, entry_def_obj, header.is_unicode, block_size, file_size
        )
elif isinstance(file_content, bytes):
    import io
    with io.BytesIO(file_content) as f:
        data, is_partial = extract_data_from_entry(
            f, entry_def_obj, header.is_unicode, block_size, file_size
        )
else:
    # Already a file handle
    data, is_partial = extract_data_from_entry(
        file_content, entry_def_obj, header.is_unicode, block_size, file_size
    )
```

## Test Plan
- [ ] Run test extraction script: `python test_extraction_stages.py`
- [ ] Verify extraction completes without type errors
- [ ] Confirm all 1374 entries are processed
- [ ] Run full pipeline: `python main.py all input output`

## Estimated Time: 1 hour

## Branch: `fix/pipeline-file-handle-issue`