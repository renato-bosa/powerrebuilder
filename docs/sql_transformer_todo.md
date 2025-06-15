# SQL Transformer TODO

## Completed
- Fixed SQL grammar reduce/reduce conflicts by restructuring select statement rules
- Updated transformer to use concrete literal classes instead of abstract Literal
- Fixed select_statement_core to look for correct dictionary keys

## Remaining Issues
1. Column references coming as strings instead of ColumnReference objects in some cases
2. Assignment transformer expecting ColumnReference but getting string
3. in_op_subquery transformer expecting Expression but getting string  
4. Generic "'list' object has no attribute 'children'" errors suggest some methods expect Tree but get list

## Notes
The SQL grammar itself is now working correctly without conflicts. The issues are in the transformer's handling of various AST node types. The parser successfully parses all test queries but the transformer needs updates to properly convert all parse tree nodes to AST nodes.