# Undefined Names Analysis Report

## Summary

- **Total diagnostics**: 2,334 errors/warnings
- **Primary issue**: ~1,029 undefined names across the codebase
- **Most affected modules**: `generate/`, `decompile/`, `model/`, `parse/`, and `extract/`

## Error Categories

### 1. **Unknown Attributes** (403 occurrences - 17%)
The largest category of errors. Common patterns:
- `append` on non-list types (46 instances)
- `value` on Expression base class instead of Literal subclasses (17 instances)  
- `extend` on non-list types (17 instances)
- Missing AST node attributes (`operator`, `left`, `right`, `fields`, etc.)

### 2. **Missing Type Annotations** (359 occurrences - 15%)
- Missing parameter type annotations in functions
- Missing return type annotations
- Generic decorators without type parameters

### 3. **Type Mismatch Errors** (329 occurrences - 14%)
- Argument type mismatches in function calls
- Path vs str type confusion
- Incorrect types passed to methods

### 4. **Missing Type Arguments** (319 occurrences - 14%)
- Generic types used without type parameters: `List`, `Dict`, `Callable`
- Collections without type specifications

### 5. **Return Type Issues** (137 occurrences - 6%)
- Functions returning wrong types
- Missing return statements
- Incompatible return types

## Top 20 Most Common Undefined Names

1. **`__setitem__`** (56 instances) - Trying to use dict-like assignment on non-dict objects (often BaseException)
2. **`append`** (46 instances) - Calling append on non-list types (int, dict, float)
3. **`__getitem__`** (37 instances) - Trying to use dict-like access on non-dict objects
4. **`value`** (17 instances) - Accessing `value` on Expression base class instead of Literal subclasses
5. **`extend`** (17 instances) - Calling extend on non-list types
6. **`operator`** (16 instances) - Missing attribute on AST nodes
7. **`right`** (14 instances) - Missing attribute on binary expression nodes
8. **`left`** (12 instances) - Missing attribute on binary expression nodes
9. **`fields`** (11 instances) - Missing attribute on dataclass-like objects
10. **`suffix`** (10 instances) - Missing attribute on certain AST nodes

## Most Problematic Files

1. **src/generate/coordinator.py** (104 errors)
2. **src/decompile/analysis/data_flow.py** (101 errors)
3. **src/model/ast/additional_nodes.py** (83 errors)
4. **src/parse/transformer/ast_builder.py** (78 errors)
5. **src/parse/visitors/pb_js_transformer.py** (70 errors)

## Root Causes Analysis

### 1. **BaseException Dictionary Access Pattern**
In `async_coordinators.py`, code is trying to treat exceptions as dictionaries:
```python
result["file"] = str(pbd_file)  # Line 80
```
This happens when `result` is actually an Exception object from `asyncio.gather(return_exceptions=True)`.

### 2. **Expression Class Hierarchy Confusion**
The `Expression` base class doesn't have a `value` attribute - only `Literal` subclasses do. Code is accessing `value` on the base Expression type without checking the subtype.

### 3. **Missing Import Symbols**
- `Progress` class is missing from imports in 3 files
- `PipelineProgress` is missing in main.py
- Various coordinator classes not properly imported

### 4. **Type Confusion in Collections**
Many instances where code assumes a variable is a list but it's actually:
- An int or float
- A dict
- None

### 5. **AST Node Attributes**
Many AST node classes are missing expected attributes like:
- `operator`, `left`, `right` for binary expressions
- `value` for literals
- `fields` for structured nodes

## Recommended Fixes

### 1. **Fix BaseException Dictionary Access**
```python
# Before
if isinstance(result, Exception):
    logger.error(f"Failed: {result}")
else:
    result["file"] = str(pbd_file)  # Only access dict methods on non-exceptions

# After
if isinstance(result, Exception):
    logger.error(f"Failed: {result}")
    result_dict = {"status": "error", "error": str(result), "file": str(pbd_file)}
else:
    result["file"] = str(pbd_file)
```

### 2. **Fix Expression Value Access**
```python
# Before
if expr.value:  # Wrong - Expression doesn't have value

# After
if isinstance(expr, Literal) and expr.value:  # Check type first
```

### 3. **Add Missing Imports**
```python
# In src/common/pipeline/__init__.py
from .progress import Progress, PipelineProgress

# Export them
__all__ = ["Progress", "PipelineProgress", ...]
```

### 4. **Fix Collection Type Confusion**
```python
# Before
results.append(item)  # results might not be a list

# After
if not isinstance(results, list):
    results = []
results.append(item)
```

### 5. **Add Type Annotations**
```python
# Before
def process(args, kwargs):

# After
from typing import Any, Dict
def process(*args: Any, **kwargs: Any) -> Dict[str, Any]:
```

### 6. **Fix Generic Type Usage**
```python
# Before
cache: Dict = {}

# After
cache: Dict[str, Any] = {}
```

## Priority Actions

1. **High Priority** (affects functionality):
   - Fix BaseException dictionary access in async_coordinators.py
   - Fix Expression/Literal type confusion in data flow analysis
   - Add missing imports for Progress and coordinator classes

2. **Medium Priority** (type safety):
   - Add missing type annotations to reduce type confusion
   - Fix generic type specifications
   - Validate collection types before operations

3. **Low Priority** (code quality):
   - Add proper type hints to all function parameters
   - Document expected attributes for all AST node classes
   - Create type stubs for complex types

## Patterns to Prevent Future Issues

1. **Always check types before accessing attributes**
2. **Use isinstance() for type narrowing**
3. **Provide complete type annotations**
4. **Use TypedDict for dictionary structures**
5. **Create proper base classes with all expected attributes**
6. **Use @property decorators for computed attributes**
7. **Validate return types match declarations**