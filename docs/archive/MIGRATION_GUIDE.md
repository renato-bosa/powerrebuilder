# Migration Guide - Code Consolidation Changes

This guide helps developers update their code to work with the consolidated project structure.

## Quick Reference - What Changed

### Import Changes

| Old Import | New Import |
|------------|------------|
| `from model.base.exception import TryCatchStatement` | `from src.model.ast.exception_handling import TryCatchStatement` |
| `from model.utils.type_system import validate_simple_type` | `from src.common.types import validate_simple_type` |
| `from parse.grammar import load_grammar` | `from src.parse.utils.grammar_loader import load_grammar` |
| `from parse.transaction_parser import Parser` | `from src.parse.parsers.transaction import TransactionParser` |
| `from extract.pbd_core.dat import DataClass` | `from src.extract.pbd_core.data_block import DataClass` |

### Function Renames

| Old Function | New Function |
|--------------|--------------|
| `bin2int(data)` | `binary_to_int(data)` |
| `bin2time(data)` | `binary_to_time(data)` |

### Module Relocations

| Old Location | New Location | Notes |
|--------------|--------------|-------|
| `extract/pbd_core/library.py::calculate_content_hash` | `src/extract/pbd_io/utils.py` | Moved to utilities |
| `extract/pbd_core/core.py::save_to_file` | `src/extract/pbd_io/file_operations.py` | Consolidated file ops |
| `extract/pbd_core/library.py::load_pfc_hashes` | `src/extract/pbd_core/pfc_utils.py` | Extracted PFC utilities |

## Step-by-Step Migration

### 1. Update Exception Imports

```python
# Before
from model.base.exception import (
    TryCatchStatement,
    CatchBlock,
    ThrowStatement
)

# After
from src.model.ast.exception_handling import (
    TryCatchStatement,
    CatchBlock,
    ThrowStatement
)
```

### 2. Update Type System Imports

```python
# Before
from model.utils.type_system import (
    validate_simple_type,
    normalize_type_name,
    create_type_from_info
)

# After
from src.common.types import (
    validate_simple_type,
    normalize_type_name,
    create_type_from_info
)
```

### 3. Update Binary Conversion Calls

```python
# Before
value = bin2int(binary_data)
timestamp = bin2time(binary_data)

# After
value = binary_to_int(binary_data)
timestamp = binary_to_time(binary_data)
```

### 4. Update Parser Usage

```python
# Before
from parse.transaction_parser import Parser
parser = Parser()

# After
from src.parse.parsers.transaction import TransactionParser
parser = TransactionParser()
```

### 5. Update Grammar Loading

```python
# Before
from parse.grammar import load_grammar
grammar = load_grammar("sql")

# After
from src.parse.utils.grammar_loader import load_grammar
grammar = load_grammar("sql")
```

### 6. Update DataBlock Usage

```python
# Before
from extract.pbd_core.dat import DataClass

# After
from src.extract.pbd_core.data_block import DataClass
```

## Common Errors and Solutions

### Import Errors

**Error**: `ImportError: cannot import name 'validate_simple_type' from 'model.utils.type_system'`

**Solution**: The type system functions have been moved to `src.common.types`. Update your imports accordingly.

### Function Not Found

**Error**: `NameError: name 'bin2int' is not defined`

**Solution**: The binary conversion functions have been renamed. Use `binary_to_int` instead.

### Module Not Found

**Error**: `ModuleNotFoundError: No module named 'parse.transaction_parser'`

**Solution**: Transaction parser has been moved to the specialized parsers subdirectory. Use `src.parse.parsers.transaction`.

## Notes

1. All consolidated code has been tested to ensure backward compatibility where possible
2. The old modules have been marked as deprecated and will be removed in a future version
3. If you encounter any issues not covered here, check the consolidation logs or raise an issue