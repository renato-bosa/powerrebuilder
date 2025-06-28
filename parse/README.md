# Parse Module

## Overview

The Parse module provides PowerBuilder source code parsing capabilities using Lark grammars. It transforms PowerBuilder source code into Abstract Syntax Trees (AST) that can be analyzed and converted to other languages.

## Structure

```
parse/
├── __init__.py
├── ast_to_model.py         # AST to model conversion
├── constants.py            # PowerBuilder constants
├── debug.py               # Debugging utilities
├── grammar.py             # Grammar management
├── library.py             # Library/import management
├── parse_coordinator.py   # Main parsing orchestrator
├── error_recovery/        # Error recovery mechanisms
│   ├── enhanced_error_recovery.py
│   └── error_recovery.py
├── grammar/               # Lark grammar definitions
│   ├── datawindow.lark
│   ├── powerbuilder.lark
│   ├── pseudocode.lark
│   └── sql.lark
├── parsers/               # Parser implementations
│   ├── base_parser.py
│   ├── enhanced_parser.py
│   ├── pseudocode_parser.py
│   ├── sql_parser.py
│   ├── transaction_parser.py
│   └── type_parser.py
├── transformers/          # AST transformers
│   ├── enhanced_type_transformer.py
│   ├── powerbuilder_transformer.py
│   └── pseudocode_transformer.py
└── visitors/              # AST visitors
    ├── abstract_visitor.py
    ├── position_tracker.py
    └── sql_transformer.py
```

## Key Components

### Grammar Files
- **powerbuilder.lark**: Main PowerBuilder language grammar
- **datawindow.lark**: DataWindow syntax grammar
- **sql.lark**: Embedded SQL grammar
- **pseudocode.lark**: PowerScript pseudocode grammar

### Parsers
- **PowerBuilderBaseParser**: Abstract base parser class
- **EnhancedPowerBuilderParser**: Parser with error recovery
- **SQLParser**: Handles embedded SQL statements
- **TransactionParser**: Parses transaction objects

### Error Recovery
The module includes sophisticated error recovery:
- Continues parsing after syntax errors
- Creates error nodes for unparseable sections
- Provides detailed error reporting
- Supports partial AST generation

## Usage

```python
from parse import parse_file, parse_string

# Parse a file
ast = parse_file("window.srw")

# Parse a string
code = "function integer calculate(integer a, integer b)\n  return a + b\nend function"
ast = parse_string(code)
```

## Grammar Features

### PowerBuilder Grammar
- Complete PowerScript syntax support
- Object-oriented constructs (classes, inheritance)
- Event handling
- DataWindow syntax
- Embedded SQL
- Control structures
- Variable declarations

### SQL Grammar
- SELECT, INSERT, UPDATE, DELETE
- Joins and subqueries
- PowerBuilder-specific SQL extensions
- Cursor declarations
- Dynamic SQL

## Error Handling

The parser provides multiple levels of error handling:
1. **Syntax Error Recovery**: Continues parsing after errors
2. **Error Nodes**: Creates placeholder nodes for invalid syntax
3. **Partial ASTs**: Generates usable ASTs even with errors
4. **Detailed Diagnostics**: Reports error locations and expected tokens

## Transformers

Transformers process the raw parse tree into a more useful AST:
- **PowerBuilderTransformer**: Main AST transformer
- **EnhancedTypeTransformer**: Handles complex type expressions
- **PseudocodeToPython**: Converts pseudocode to Python

## Dependencies

- lark-parser: For grammar-based parsing
- Python 3.9+

## Related Modules

- **Extract**: Provides source files to parse
- **Model**: Receives AST for further processing
- **Generate**: Uses parsed AST for code generation