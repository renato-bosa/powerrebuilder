# Circular Dependency Analysis Report for PowerRebuilder

## Executive Summary

The PowerRebuilder codebase contains several circular dependency patterns that should be addressed to improve maintainability and prevent future issues. The analysis identified 5 major circular dependency patterns and several minor ones.

## Major Circular Dependencies Found

### 1. Model ↔ AST Circular Dependency
**Pattern**: `src.model` imports from `src.model.ast`, and `src.model.ast` imports back from `src.model`

**Details**:
- `src/model/ast/nodes/base.py` imports `SourceAnchor` from `src.model.utils.base` (uses TYPE_CHECKING)
- `src/model/ast/nodes/declarations.py` imports `PBNode` from `src.model.utils.base`
- `src/model/ast/additional_nodes.py` imports `PBNode` from `src.model.utils.base`
- `src/model/ast/nodes/sql.py` imports `PBNode` from `src.model.utils.base`
- `src/model/ast/pb_types.py` imports `PBNode` from `src.model.utils.base`
- `src/model/ast/functions.py` imports `PBNode` from `src.model.utils.base`

Meanwhile:
- Multiple files in `src/model` import from `src.model.ast`
- `src/model/utils/base.py` imports `NodeKind` from `src.model.ast.node_kind` (uses TYPE_CHECKING)

**Impact**: High - Core data structures are interdependent

### 2. Common ↔ Other Modules Circular Dependency
**Pattern**: `src.common` imports from various modules, which import back from `src.common`

**Details**:
- `src/common/types/types.py` imports AST types from `src.model.ast`
- `src/common/pipeline/pipeline_coordinator.py` imports all coordinators
- Many modules import from `src.common.utils` and `src.common.types`

**Impact**: Medium - Makes common utilities less reusable

### 3. Parse ↔ Transformer Circular Dependency
**Pattern**: Parser modules import transformers, transformers import parser types

**Details**:
- `src/parse/parser/sql.py` imports `SQLTransformer` from `src.parse.transformer.sql_transformer`
- `src/parse/transformer/type_resolver.py` imports types from `src.parse.parsers.type_parser`
- `src/parse/transformer/enhanced_type_transformer.py` imports from `src.parse.parser.specialized.type_parser`

**Impact**: Medium - Couples parsing and transformation phases

### 4. Coordinator Dependencies
**Pattern**: Pipeline coordinator imports all stage coordinators, creating potential for circular dependencies

**Details**:
- `src/common/pipeline/pipeline_coordinator.py` imports from:
  - `src.extract.coordinator`
  - `src.parse.coordinator`
  - `src.decompile.coordinator`
  - `src.model.coordinator`
  - `src.generate.coordinator`

**Impact**: Low - Currently managed through careful import ordering

### 5. TYPE_CHECKING Guards
**Pattern**: Extensive use of TYPE_CHECKING to avoid runtime circular imports

**Files using TYPE_CHECKING** (19 files):
- Model layer: 8 files
- Parse layer: 4 files
- Extract layer: 3 files
- Others: 4 files

**Impact**: Medium - Indicates underlying design issues

## Minor Circular Dependencies

### 1. Expression Dependencies
- `src/model/expressions/evaluator.py` ↔ `src/model/expressions/ast_expressions.py`
- Both use TYPE_CHECKING to avoid runtime issues

### 2. Transaction Module Dependencies
- Transaction modules import from each other with TYPE_CHECKING guards
- `distributed.py`, `error_handling.py`, and `transaction.py` have interdependencies

## Recommendations

### 1. Extract Common Base Types
Create a new module `src/base/types.py` to hold:
- `SourceAnchor`
- `PBNode`
- `NodeKind`
- Other base types

This would break the Model ↔ AST circular dependency.

### 2. Refactor Common Module
Split `src/common` into:
- `src/common/utilities` - Pure utility functions with no domain dependencies
- `src/common/pipeline` - Pipeline-specific code
- `src/common/types` - Type definitions only

### 3. Use Dependency Injection for Coordinators
Instead of direct imports in pipeline_coordinator.py:
```python
class PipelineCoordinator:
    def __init__(self, coordinators: Dict[str, Any]):
        self.coordinators = coordinators
```

### 4. Separate Parser and Transformer Interfaces
Create interfaces/protocols:
```python
# src/parse/interfaces.py
class IParser(Protocol):
    def parse(self, source: str) -> Any: ...

class ITransformer(Protocol):
    def transform(self, tree: Any) -> Any: ...
```

### 5. Reduce TYPE_CHECKING Usage
Where TYPE_CHECKING is used extensively, consider:
- Moving type definitions to a separate module
- Using string annotations with `from __future__ import annotations`
- Creating protocol classes for type checking

## Priority Actions

1. **High Priority**: Fix Model ↔ AST circular dependency
   - Extract base types to new module
   - Update all imports
   - Remove TYPE_CHECKING guards where possible

2. **Medium Priority**: Refactor Common module
   - Split into focused sub-modules
   - Remove domain-specific imports

3. **Low Priority**: Clean up remaining TYPE_CHECKING usage
   - Evaluate each case individually
   - Replace with better design patterns where appropriate

## Verification Script

To verify circular dependencies are resolved:
```bash
# Check for remaining circular imports
python -m pycycle src/ --verbose

# Check for TYPE_CHECKING usage
grep -r "TYPE_CHECKING" src/ | wc -l

# Run import order test
python -c "import src.model.ast; import src.common.types; print('No circular imports!')"
```

## Conclusion

While the codebase uses TYPE_CHECKING effectively to avoid runtime circular imports, the underlying design issues should be addressed for better maintainability. The recommended refactoring would improve code organization and reduce complexity.