# Grammar Usage Summary

## Active Grammar Files and Their Usage

### 1. powerbuilder.lark
- **Used by**: PowerBuilderParser (parse_coordinator.py, line 67)
- **File types**: .sra, .srw, .sru, .srf, .srm, .srs, .srq
- **Status**: Main production grammar
- **Imports**: From common (CNAME, INT, WS_INLINE, NEWLINE, WS)

### 2. datawindow.lark  
- **Used by**: PowerBuilderDataWindowParser (parse_coordinator.py, line 185)
- **File types**: .srd
- **Status**: Production, but using hardcoded path
- **Imports**: From common AND from powerbuilder.lark
- **Issue**: Mixed imports create coupling

### 3. sql.lark
- **Used by**: SQLParser (sql_parser.py via load_grammar)
- **File types**: .srq and embedded SQL
- **Status**: Production
- **Imports**: None currently

### 4. pseudocode.lark
- **Used by**: Tests only (test_pseudocode.py)
- **Status**: Test/development
- **Imports**: From common

### 5. common_grammar.lark
- **Status**: Created but NOT imported by any grammar
- **Contains**: Token definitions and operators
- **Issue**: Duplicates imports from Lark's common

## Experimental/Unused Grammars
- powerbuilder_fixed.lark - Used by test_fixed_grammar.py
- powerbuilder_fixed_v2.lark - Used by test_fixed_grammar.py
- powerbuilder_simple.lark - Used by test_simple_parser.py
- powerbuilder_core.lark - Referenced in tests but commented out
- powerbuilder_js.lark - Used by test_pb_js_transformer.py

## Key Issues

### 1. Hardcoded Paths
```python
# In PowerBuilderDataWindowParser.__init__
with open(self.base_path / "parse/datawindow.lark", encoding="utf-8") as f:

# In PowerBuilderQueryParser.__init__  
with open(self.base_path / "parse/sql.lark", encoding="utf-8") as f:
```

### 2. GrammarManager Not Used
- GrammarManager exists in grammar.py but parse_coordinator.py doesn't use it
- Direct file loading instead of centralized management

### 3. Common Grammar Not Integrated
- common_grammar.lark was created but no grammar imports from it
- All grammars import directly from Lark's common module

### 4. Duplicate Token/Rule Definitions
Most common duplicates across grammars:
- Operators: EQUALS (8x), DOT (8x), COMMA (8x), etc.
- Keywords: TYPE (6x), RETURN (6x), END (6x), etc.
- Rules: string_value (4x), argument (4x), value_list (3x), etc.

## Recommended Actions

### Immediate (Quick Fixes)
1. **Fix hardcoded paths** in parse_coordinator.py
2. **Create experimental/ directory** and move unused grammars
3. **Update root test files** to use moved grammars or main grammars

### Short-term (Consolidation)
1. **Remove common_grammar.lark** - it's not providing value over Lark's common
2. **Standardize imports** - all grammars should import from Lark's common
3. **Extract shared PowerBuilder rules** into a pb_common.lark file
4. **Fix datawindow.lark** to not import from powerbuilder.lark

### Long-term (Refactoring)
1. **Use GrammarManager** throughout the codebase
2. **Modularize powerbuilder.lark** into smaller focused files
3. **Create proper test grammars** separate from experimental ones
4. **Document grammar architecture** and dependencies