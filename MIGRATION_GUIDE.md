# Migration Guide - Code Consolidation Changes

This guide helps developers update their code to work with the consolidated project structure.

## Quick Reference - What Changed

### Import Changes

| Old Import | New Import |
|------------|------------|
| `from model.base.exception import TryCatchStatement` | `from model.ast.exception_handling import TryCatchStatement` |
| `from model.utils.type_system import validate_simple_type` | `from common.types import validate_simple_type` |
| `from parse.grammar import load_grammar` | `from parse.utils.grammar_loader import load_grammar` |
| `from parse.transaction_parser import Parser` | `from parse.parsers.transaction import TransactionParser` |
| `from extract.pbd_core.dat import DataClass` | `from extract.pbd_core.data_block import DataClass` |

### Function Renames

| Old Function | New Function |
|--------------|--------------|
| `bin2int(data)` | `binary_to_int(data)` |
| `bin2time(data)` | `binary_to_time(data)` |

### Module Relocations

| Old Location | New Location | Notes |
|--------------|--------------|-------|
| `extract/pbd_core/library.py::calculate_content_hash` | `extract/pbd_io/utils.py` | Moved to utilities |
| `extract/pbd_core/core.py::save_to_file` | `extract/pbd_io/file_operations.py` | Consolidated file ops |
| `extract/pbd_core/library.py::load_pfc_hashes` | `extract/pbd_core/pfc_utils.py` | Extracted PFC utilities |

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
from model.ast.exception_handling import (
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
from common.types import (
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
from parse.parsers.transaction import TransactionParser
parser = TransactionParser()
```

### 5. Update Grammar Loading

```python
# Before
from parse.grammar import load_grammar
grammar = load_grammar("sql")

# After
from parse.utils.grammar_loader import load_grammar
# Now supports more options
grammar = load_grammar(
    "sql",
    parser="lalr",  # Can specify parser type
    cache=True,     # Control caching
    import_paths=["/custom/path"]  # Custom import paths
)
```

### 6. Use New Base Classes

For new coordinator development:

```python
# Before - lots of boilerplate
class MyCoordinator:
    def __init__(self):
        self.logger = logging.getLogger(__name__)
    
    def process_files(self, input_dir, output_dir):
        # Manual directory creation
        # Manual progress tracking
        # Manual error handling
        pass

# After - inherit common functionality
from common.pipeline import PipelineStage

class MyCoordinator(PipelineStage):
    def __init__(self):
        super().__init__("my_stage")
    
    def process_file(self, input_file, output_dir):
        # Just implement file processing
        # Base class handles the rest
        pass
```

### 7. Use Consolidated Utilities

```python
# DataWindow detection
from common.datawindow_utils import DataWindowDetector

# Check if file is a DataWindow
if DataWindowDetector.is_datawindow_file(filename):
    metadata = DataWindowDetector.extract_metadata(data)
    format_type = DataWindowDetector.detect_format(data)

# SQL parsing - use single parser
from parse.parsers.sql import SQLParser
parser = SQLParser()
result = parser.parse(sql_content)
```

## Common Pitfalls

### 1. Importing from Deleted Modules
```python
# This will fail - module deleted
from model.utils.type_system import Type  # ❌

# Use this instead
from common.types import Type  # ✓
```

### 2. Using Old Function Names
```python
# This will fail - function renamed
value = bin2int(data)  # ❌

# Use this instead
value = binary_to_int(data)  # ✓
```

### 3. Wrong Parser Import
```python
# Don't use multiple SQL parsers
from parse.sql_parser import SQLParser  # ❌
from parse.parse_coordinator import PowerBuilderQueryParser  # ❌

# Use the consolidated one
from parse.parsers.sql import SQLParser  # ✓
```

## Testing Your Migration

1. **Run Import Check**:
   ```bash
   python -m py_compile your_module.py
   ```

2. **Run Tests**:
   ```bash
   pytest tests/ -v
   ```

3. **Check for Deprecation Warnings**:
   ```python
   import warnings
   warnings.filterwarnings('error', category=DeprecationWarning)
   ```

## Getting Help

If you encounter issues:
1. Check this migration guide
2. Review CONSOLIDATION_CHANGES_SUMMARY.md for details
3. Search for the old import/function name in the codebase
4. Check the git history for the rename commit

## Future Deprecations

The following may be removed in future versions:
- Re-export modules in parse/exceptions.py
- Re-export modules in extract/pbd_core/exceptions.py
- Old parser classes in parse_coordinator.py

Update your code now to avoid future breakage!