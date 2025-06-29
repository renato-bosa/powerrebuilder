# SQL Parameter Placeholder Decoder Fix Summary

## Issue Identified
DataWindow SQL files were being extracted with corrupted parameter placeholders. The character `Ā` (U+0100, UTF-8 bytes: 0xC4 0x80) was appearing where SQL parameter placeholders (`?`) should be.

Example of corrupted SQL:
```sql
SELECT bill_payment.bill_id 
FROM bill_payment 
WHERE ( bill_payment.bill_id = Ā ) 
AND ( bill_payment.payment_type = Ā )
```

## Root Cause
The extraction process was using PowerBuilderDecoderV3 instead of PowerBuilderDecoderV4, which has specific fixes for SQL parameter placeholder corruption.

## Files Modified

### 1. `/extract/pbd/structures/data_block.py`
Changed the import statement in the `get_text_from_data` function:
- **Before**: `from extract.pbd.utils.powerbuilder_decoder_v3 import decode_powerbuilder_text`
- **After**: `from extract.pbd.utils.powerbuilder_decoder_v4 import decode_powerbuilder_text`

### 2. `/extract/pbd/utils/powerbuilder_decoder_v4.py`
Fixed a regex pattern that was incorrectly removing the UNION keyword:
- **Before**: `(re.compile(r'Ā(?:\s*\)|,|\s+AND|\s+OR|\s+UNION)', re.IGNORECASE), '?')`
- **After**: `(re.compile(r'Ā(\s*(?:\)|,|\s+AND|\s+OR|\s+UNION))', re.IGNORECASE), r'?\1')`

## How the Fix Works

PowerBuilderDecoderV4 specifically handles SQL parameter placeholders by:

1. Detecting if text appears to be SQL (checks for SQL keywords)
2. Applying specific pattern replacements for common SQL contexts:
   - WHERE clauses
   - VALUES clauses
   - Equals comparisons
   - UNION queries
3. Replacing remaining `Ā` characters with `?` only in SQL contexts
4. Preserving `Ā` characters in non-SQL text

## Verification
A test script (`test_sql_parameter_fix.py`) was created to verify:
- All SQL parameter patterns are correctly fixed
- Non-SQL text with `Ā` characters is preserved
- The UNION keyword is not accidentally removed

All tests pass successfully.

## Next Steps
To fix existing SQL files, the extraction process needs to be re-run. The decoder will now correctly replace `Ā` with `?` during extraction.

Example of corrected SQL:
```sql
SELECT bill_payment.bill_id 
FROM bill_payment 
WHERE ( bill_payment.bill_id = ? ) 
AND ( bill_payment.payment_type = ? )
```