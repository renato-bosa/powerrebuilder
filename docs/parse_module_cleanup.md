# Parse Module Cleanup Documentation

## Summary
This document outlines unused or partially integrated components in the parse module that could be cleaned up or properly integrated in future work.

## Integration Issues Fixed (2025-06-14)
1. **DataWindow and Query Parser Grammar Paths**: Fixed incorrect grammar file paths in parse_coordinator.py
2. **Parse Phase Target**: Changed from parsing decompiled files to parsing extracted source files
3. **AST to Model Converter**: Properly integrated to convert parsed AST JSON files to model objects

## Grammar File Issues Discovered
1. **DataWindow Grammar** (`parse/grammar/datawindow.lark`): Contains comments that cause Lark parser initialization to fail
2. **SQL Grammar** (`parse/grammar/sql.lark`): Has reduce/reduce conflicts in select_statement rules

## Unused Parse Components

### 1. Transformers and Visitors
- `parse/visitors/pb_js_transformer.py` - PowerBuilder to JavaScript transformer (not used in pipeline)
- `parse/visitors/sql_transformer.py` - SQL AST transformer (imported but not actively used)
- `parse/pseudocode_transformer.py` - Pseudocode transformer (exists but not integrated)

### 2. Specialized Parsers
- `PowerBuilderQueryParser` - Has grammar conflicts and not used in main pipeline
- `parse/sql_parser.py` - Standalone SQL parser not integrated with main flow

### 3. Grammar Files
- `parse/grammar/powerbuilder_js.lark` - JavaScript-style PowerBuilder grammar (not used)
- `parse/grammar/pseudocode.lark` - Pseudocode grammar (not integrated)
- Multiple experimental grammar files in `parse/grammar/experimental/`

### 4. Library Management
- `parse/library.py` - Library and LibraryManager classes exist but not used in pipeline
- `parse/transaction_parser.py` - Transaction parser imported in __init__ but never used

## Recommendations

### Immediate Actions
1. Fix grammar file issues (remove comments from DataWindow grammar, resolve SQL conflicts)
2. Remove or properly integrate unused transformers and visitors
3. Clean up experimental grammar files or document their purpose

### Future Improvements
1. Integrate specialized parsers (Query, SQL) if needed for specific file types
2. Implement library management for handling PowerBuilder library dependencies
3. Complete AST deserialization to handle pretty-printed AST strings in JSON files
4. Add proper error recovery and reporting for parse failures

## Notes
- The main PowerBuilderParser works correctly for standard PowerBuilder source files
- The AST to Model converter needs enhancement to handle all AST node types
- Consider consolidating grammar files and removing duplicates