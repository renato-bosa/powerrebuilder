# Common Module

## Overview

The Common module provides shared utilities, types, and infrastructure used across all other modules in the SIME Finch project. It ensures consistency and reduces code duplication throughout the pipeline.

## Structure

```
common/
├── __init__.py
├── constants.py              # Global constants
├── exceptions.py             # Custom exceptions
├── logging_config.py         # Logging configuration
├── pipeline/                 # Pipeline infrastructure
│   ├── __init__.py
│   ├── pipeline.py          # Pipeline base classes
│   ├── pipeline_coordinator.py
│   └── progress.py          # Progress tracking
├── types/                    # Type definitions
│   ├── __init__.py
│   └── types.py             # Common type aliases
└── utils/                    # Utility functions
    ├── __init__.py
    ├── datawindow_utils.py  # DataWindow helpers
    ├── error_recovery.py    # Error recovery utilities
    └── object_type_detector.py # File type detection
```

## Key Components

### Pipeline Infrastructure

The pipeline package provides the foundation for the modular architecture:

- **PipelineStage**: Base class for pipeline stages
- **PipelineCoordinator**: Orchestrates pipeline execution
- **ProgressTracker**: Tracks processing progress

```python
from common.pipeline import PipelineStage, PipelineCoordinator

class MyStage(PipelineStage):
    def process(self, input_data):
        # Process data
        return output_data

coordinator = PipelineCoordinator()
coordinator.add_stage(MyStage())
coordinator.run(input_data)
```

### Exceptions

Custom exception hierarchy for better error handling:

```python
from common.exceptions import (
    SimeFinchError,      # Base exception
    ExtractionError,     # Extract module errors
    ParseError,          # Parse module errors
    ModelError,          # Model module errors
    DecompileError,      # Decompile module errors
    GenerateError        # Generate module errors
)
```

### Constants

Global constants used throughout the project:

```python
from common.constants import (
    SUPPORTED_PB_VERSIONS,   # PowerBuilder versions
    MAX_FILE_SIZE,          # File size limits
    ENCODING_DEFAULTS,      # Character encodings
    MAGIC_NUMBERS          # File format signatures
)
```

### Utilities

#### Object Type Detector
Detects PowerBuilder object types from file content:

```python
from common.utils import ObjectTypeDetector

file_type = ObjectTypeDetector.detect_file_type(data, filename)
is_binary = ObjectTypeDetector.is_binary_content(data)
subtype = ObjectTypeDetector.detect_datawindow_subtype(filename)
```

#### DataWindow Utilities
Helper functions for DataWindow processing:

```python
from common.utils import DataWindowUtils

sql = DataWindowUtils.extract_sql(datawindow_content)
columns = DataWindowUtils.parse_columns(datawindow_syntax)
```

#### Error Recovery
Utilities for graceful error handling:

```python
from common.utils import ErrorRecovery

with ErrorRecovery.context("Processing file"):
    # Code that might fail
    result = process_file(filename)
```

### Type Definitions

Common type aliases for type safety:

```python
from common.types import (
    SourcePosition,      # Line/column position
    SourceRange,         # Start/end positions
    NodeId,             # AST node identifier
    SymbolName,         # Symbol table name
    FilePath            # Path type alias
)
```

## Logging Configuration

Centralized logging setup:

```python
from common.logging_config import setup_logging

# Setup logging for the entire application
setup_logging(
    level="INFO",
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    file="sime_finch.log"
)
```

## Progress Tracking

Track long-running operations:

```python
from common.pipeline import ProgressTracker

tracker = ProgressTracker(total_items=100)
for item in items:
    process_item(item)
    tracker.update(1)
    tracker.log_progress()
```

## Error Handling Strategy

The module promotes consistent error handling:

1. **Specific Exceptions**: Use module-specific exceptions
2. **Error Context**: Provide context for errors
3. **Recovery Options**: Enable graceful degradation
4. **Detailed Logging**: Log errors with full context

## Best Practices

### Using Pipeline Infrastructure
- Inherit from `PipelineStage` for new stages
- Implement `validate_input` and `validate_output`
- Use progress tracking for long operations

### Error Handling
- Catch specific exceptions at appropriate levels
- Use `ErrorRecovery` for non-critical operations
- Always log errors with context

### Type Safety
- Use type aliases from `common.types`
- Enable type checking with mypy
- Document expected types in docstrings

## Dependencies

- Python 3.9+
- typing_extensions
- No external runtime dependencies

## Testing

The common module includes comprehensive tests:

```bash
# Run common module tests
pytest tests/test_common/

# Test specific components
pytest tests/test_common/test_pipeline.py
pytest tests/test_common/test_object_type_detector.py
```

## Related Modules

All other modules depend on Common for:
- Shared utilities and helpers
- Consistent error handling
- Type definitions
- Pipeline infrastructure