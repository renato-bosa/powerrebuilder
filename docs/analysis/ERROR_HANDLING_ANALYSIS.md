# PowerRebuilder Error Handling and Circular Dependencies Analysis

## 1. Current Error/Exception Classes Overview

The codebase has multiple error hierarchies that create confusion and potential conflicts:

### Main Error Hierarchies

1. **src/common/exceptions.py** (Primary - 358 lines)
   - Base: `SimeFinchError` (with alias `Error`)
   - Comprehensive hierarchy covering all modules
   - Well-structured with context support
   - Includes backward compatibility aliases

2. **src/common/pipeline/exceptions.py** (Duplicate - 31 lines)
   - Base: `PipelineError`
   - Duplicates: `ExtractError`, `ParseError`, `DecompileError`, `GenerateError`, `ValidationError`
   - Conflicts with main hierarchy

3. **src/common/types/errors.py** (Dataclass - 77 lines)
   - `ParseError` as a dataclass (not an exception!)
   - `ErrorCollector` utility class
   - Conflicts with exception-based ParseError

4. **Module-specific re-exports**:
   - `src/model/utils/errors.py` - Re-exports from common.exceptions
   - `src/extract/pbd/exceptions.py` - Re-exports PBD-specific exceptions
   - `src/parse/exceptions.py` - Re-exports parser-specific exceptions
   - `src/parse/utils/exceptions.py` - Contains only `GrammarLoadError`

## 2. Inconsistent Error Handling Patterns

### Coordinator Error Handling

1. **Extract Coordinator** (src/extract/coordinator.py):
   ```python
   from src.extract.pbd.exceptions import PbdError
   
   # Catches specific PbdError
   except PbdError as pbd_e:
       # Specific handling
   except Exception as e:
       # Generic fallback
   ```

2. **Parse Coordinator** (src/parse/coordinator.py):
   ```python
   from src.common.types.errors import ErrorCollector, ParseError
   from .exceptions import GrammarParseError, SyntaxError
   
   # Uses ErrorCollector pattern
   # Mixes dataclass ParseError with exception-based errors
   ```

3. **Model Coordinator** (src/model/coordinator.py):
   ```python
   from src.model.utils.errors import ValidationError
   
   # Uses re-exported ValidationError
   ```

4. **Generate Coordinator** (src/generate/coordinator.py):
   - No explicit error imports found
   - Likely using generic exception handling

5. **Pipeline Coordinator** (src/common/pipeline/pipeline_coordinator.py):
   ```python
   from .exceptions import DecompileError, ExtractError, GenerateError, ParseError
   
   # Uses duplicate pipeline-specific exceptions
   ```

### Error Handling Anti-patterns

1. **Bare except clauses**: Many files use `except Exception as e:`
2. **Silent failures**: Some errors are logged but not re-raised
3. **Mixed error types**: Dataclass errors mixed with exception errors
4. **Duplicate error classes**: Same error names in different modules

## 3. Circular Import Dependencies

### Direct Circular Imports Found

While no direct circular imports were detected in the automated scan, there are several risky patterns:

1. **Common → Module → Common**:
   - `src/common/utils/error_recovery.py` imports from `src/common.exceptions`
   - Module-specific error files re-export from `src/common.exceptions`

2. **Type System Dependencies**:
   - `src/model/types/validation.py` imports from `.errors` (ValidationError)
   - `src/common/types/errors.py` defines ParseError as dataclass
   - Potential conflict with exception-based ParseError

3. **Coordinator Dependencies**:
   - Coordinators import from various error modules
   - No direct circular imports between coordinators found

## 4. Naming Conflicts

1. **ParseError**:
   - Exception in `src/common/exceptions.py`
   - Dataclass in `src/common/types/errors.py`
   - Re-exported in multiple places

2. **ValidationError**:
   - In `src/common/exceptions.py`
   - In `src/common/pipeline/exceptions.py`
   - Referenced differently across modules

## 5. Recommendations for Standardized Error Hierarchy

### Immediate Actions

1. **Remove Duplicate Error Hierarchies**:
   ```python
   # DELETE: src/common/pipeline/exceptions.py
   # UPDATE: pipeline_coordinator.py to use src.common.exceptions
   ```

2. **Rename Dataclass ParseError**:
   ```python
   # In src/common/types/errors.py
   @dataclass
   class ParseErrorInfo:  # Renamed from ParseError
       line: int
       column: int
       message: str
       # ...
   ```

3. **Standardize Coordinator Error Handling**:
   ```python
   # Standard pattern for all coordinators
   from src.common.exceptions import (
       ExtractError,
       ParseError,
       DecompileError,
       ModelError,
       GenerateError
   )
   
   try:
       # operation
   except SpecificError as e:
       logger.error("Operation failed: %s", e)
       raise  # Re-raise, don't swallow
   ```

### Proposed Error Hierarchy

```python
# src/common/exceptions.py - Single source of truth

SimeFinchError (base)
├── PowerBuilderError
│   ├── TransactionError
│   └── PBSpecificErrors...
├── ParseError (with position info)
│   ├── GrammarError
│   │   ├── GrammarLoadError
│   │   ├── GrammarParseError
│   │   └── GrammarNotFoundError
│   ├── PowerBuilderSyntaxError
│   └── PreprocessorError
├── ExtractError
│   └── PbdError
│       ├── HeaderError
│       ├── NodeError
│       ├── EntryError
│       └── DatError
├── DecompileError
├── ModelError
│   ├── ModelGenerationError
│   └── TypeValidationError
├── GenerateError
├── ValidationError
└── ConfigurationError
```

### Migration Strategy

1. **Phase 1**: Update imports
   - Replace all `from pipeline.exceptions import` with `from common.exceptions import`
   - Update ErrorCollector to use ParseErrorInfo instead of ParseError

2. **Phase 2**: Remove duplicates
   - Delete `src/common/pipeline/exceptions.py`
   - Update re-export modules to add deprecation warnings

3. **Phase 3**: Standardize handling
   - Implement consistent error handling in all coordinators
   - Add error context (file, line, column) where applicable
   - Ensure all errors are properly logged and re-raised

### Best Practices

1. **Always include context**:
   ```python
   raise ParseError(
       message="Unexpected token",
       filename=self.current_file,
       line=token.line,
       column=token.column
   )
   ```

2. **Use specific exceptions**:
   ```python
   # Good
   except GrammarLoadError:
   
   # Bad
   except Exception:
   ```

3. **Log and re-raise**:
   ```python
   except SpecificError as e:
       logger.error("Context: %s", e, exc_info=True)
       raise  # Preserve stack trace
   ```

4. **Avoid circular imports**:
   - Keep error definitions in `src/common/exceptions.py`
   - Import errors at module level, not function level
   - Use TYPE_CHECKING for type hints if needed

This standardization will improve code maintainability, debugging, and error handling consistency across the entire PowerRebuilder project.