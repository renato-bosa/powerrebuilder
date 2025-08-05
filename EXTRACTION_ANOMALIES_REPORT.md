# PowerRebuilder Extraction Anomalies Report

## Summary of Odd Characters and Processing Issues

During the extraction process, several anomalies were detected that indicate potential issues with filename handling and character encoding:

### 1. Single-Character Filenames
Many extracted files have single-character names, suggesting truncation or corruption:
- `_.fun` (underscore)
- `a.fun`, `A.fun`, `l.fun`, `o.fun`, `m.fun`, `w.fun`, `u.fun`, `t.fun`, `s.fun`, `g.fun`, `c.fun`, `e.fun`
- `.fun` (empty name, just extension)
- `1.fun` (numeric)
- `%.fun` (special character)

### 2. Non-ASCII Characters
- `à.fun` - Contains accented character (à = 0xE0 in extended ASCII)
- This suggests the extraction process may not be properly handling character encoding

### 3. Extremely Long SQL-Like Filename
Found in dcms_reports:
```
l,_____client,_____client_address,_____clinic,_____address as address_a,_____address as address_b,_____clinic_logo,_____clinic_address,______client_clinic___ __   WHERE ( billing.fun
```
This appears to be SQL query text incorrectly used as a filename, indicating possible data/metadata confusion during extraction.

### 4. Special Characters in Filenames
- ` .fun` (space character)
- `)` (single parenthesis as filename in dcm_list)
- `_id.fun` (looks like a database field name)

### 5. Empty Files
Several directories contain files with 0 bytes:
- In dcm_dbupgrade: files named `a`, `l`, `T` (no extension)
- In dcm_list: `cms_list_clinic_type_sql.dwo` (0 bytes)

### 6. Decompilation Failures
The decompile stage failed for many files, particularly those with odd filenames. This suggests:
- The P-code structure may be corrupted or non-standard
- Character encoding issues are preventing proper parsing
- Some files may contain data other than executable P-code

### 7. File Size Patterns
Extracted .fun files vary dramatically in size:
- Small: 643KB (_.fun)
- Medium: 1-2MB (several files)
- Large: 5.2MB (A.fun), 8.4MB (à.fun), 9MB (_id.fun, _.fun)

### Root Causes

1. **Character Encoding Issues**: The PBD format may use different character encodings (ANSI, Unicode, etc.) that aren't being handled consistently

2. **Entry Name Extraction**: The code extracting entry names from PBD headers may be:
   - Truncating names at null bytes or special characters
   - Misinterpreting the name length field
   - Not handling Unicode/wide character names properly

3. **Data/Metadata Confusion**: Some extracted "filenames" appear to be data content (SQL queries) rather than actual object names

4. **Legacy Format Variations**: Different versions of PowerBuilder may use slightly different PBD formats

## Recommendations

1. Review the PBD entry name extraction logic in `src/extract/pbd/structures.py`
2. Add character encoding detection and proper Unicode handling
3. Implement validation for extracted filenames before writing to disk
4. Add logging for suspicious filenames during extraction
5. Consider adding a mapping table for single-character names to their full names
6. Implement stricter bounds checking when reading entry headers

## Impact

While extraction succeeded for most files, these anomalies suggest that:
- Some PowerBuilder objects may not be properly identified
- The decompile stage struggles with files that have corrupted metadata
- Full recovery of the original source code structure may be incomplete