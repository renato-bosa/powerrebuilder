# Bug Reference

## Fixed Bugs

### 30-Entry Limit in PBD Extraction (2025-01-10)

**Issue**: The PBD extractor was stopping after processing only 30 entries when it encountered a DAT* block, even though there were many more entries to process (e.g., 1374 entries expected).

**Root Cause**: In `src/extract/pbd/structures/node.py`, the `extract_entry_definitions_from_node_block` function was incorrectly treating DAT* blocks as end-of-data markers instead of skipping over them.

**Solution**: 
1. Modified the function to parse DAT* block headers to determine their size
2. Skip over the entire DAT* block and continue searching for more ENT* entries
3. Added support for both ASCII and Unicode DAT* blocks
4. Added safety checks to prevent infinite loops

**DAT* Block Structure**:
- ASCII DAT*:
  - 4 bytes: signature ("DAT*")
  - 4 bytes: next block offset
  - 2 bytes: data length
  - variable: actual data
  
- Unicode DAT*:
  - 8 bytes: signature ("D\x00A\x00T\x00*\x00")
  - 4 bytes: next block offset
  - 2 bytes: data length
  - variable: actual data

**Testing**: Use `test_30_entry_fix.py` to verify the fix works correctly on PBD files with more than 30 entries.

### P-code Detection Minimum Size Constraint (2025-07-16)

**Issue**: The P-code detector in `src/decompile/pcode/detector.py` was rejecting any P-code section smaller than 10 bytes, which could skip legitimate small functions like simple getters/setters.

**Root Cause**: 
1. The `_calculate_pcode_confidence` method returned 0.0 confidence for any data less than 10 bytes
2. The `find_all_pcode_sections` method required at least 20 bytes for analysis
3. Small sections were filtered out with a hardcoded 10-byte minimum

**Solution**:
1. Modified `_calculate_pcode_confidence` to handle data >= 4 bytes (minimum meaningful P-code)
2. Added `_calculate_small_section_confidence` method specifically for 4-9 byte sections
3. Added special handling in `find_all_pcode_sections` for data < 20 bytes
4. Reduced minimum section size from 10 to 4 bytes
5. Added pattern recognition for common small functions:
   - Getter pattern: PUSH_PROPERTY + RETURN (4-6 bytes)
   - Setter pattern: POP_PROPERTY + RETURN (4-6 bytes)
   - Constant return: PUSH_CONST_* + RETURN (4 bytes)

**Testing**: Added `test_small_pcode_detection` test case to verify detection of small P-code sections works correctly.

### Regex-based AST Parsing (2025-07-16)

**Issue**: The ModelCoordinator was using fragile regex patterns to extract information from string representations of AST trees, causing parsing failures and maintenance issues.

**Root Cause**:
1. AST trees were converted to strings and parsed with regex patterns like `r"Tree\(Token\('RULE', 'event_handler'\).*?Token\('IDENTIFIER', '(\w+)'\)"`
2. String format changes would break the regex patterns
3. Nested structures couldn't be properly handled
4. No type safety or proper error handling

**Solution**: Implemented proper visitor pattern for AST traversal:
1. Created `ASTTreeVisitor` base class that handles multiple AST formats (Lark trees, dictionaries, legacy strings)
2. Implemented `ModelExtractorVisitor` for extracting model information
3. Added `ASTWalker` utility for efficient node searching and pattern matching
4. Created `PatternMatcher` with pre-defined PowerBuilder patterns
5. Updated ModelCoordinator to use visitors with fallback to legacy regex for compatibility

**Benefits**:
- Type-safe traversal of AST structures
- Supports multiple AST formats transparently
- Easy to extend with new node types
- Better error handling and debugging
- No string manipulation or regex compilation overhead

**Files Modified**:
- Created: `src/model/visitors/` package with visitor implementations
- Updated: `src/model/coordinator.py` to use visitors instead of regex
- Added: `tests/unit/model/test_visitors.py` for visitor testing
- Added: `examples/visitor_pattern_demo.py` for usage examples
- Added: `docs/guides/VISITOR_PATTERN.md` for documentation

**Testing**: Run `pytest tests/unit/model/test_visitors.py` to verify visitor implementations work correctly.