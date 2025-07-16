# PowerRebuilder Architecture Analysis Report

## Executive Summary

Based on analysis using ruff and vulture, I've identified several architectural patterns and issues in the PowerRebuilder codebase:

### Key Findings

1. **Circular Dependency**: Parse and Model modules have a circular dependency that needs resolution
2. **Unused Imports**: 217 unused imports found across the codebase
3. **Dead Code**: 2963 blank lines with whitespace, numerous unused variables and functions
4. **Missing Dependencies**: 120 undefined names suggest missing imports or dependencies

## Architecture Overview

### Module Structure
```
src/
├── common/          # Shared utilities (pipeline, types, utils)
├── extract/         # PBD/PBL file extraction 
├── decompile/       # P-code decompilation
├── parse/           # PowerBuilder source parsing
├── model/           # AST and semantic models
└── generate/        # Code generation (Python/Dart)
```

### Pipeline Flow
1. **Extract** → Produces .fun files (P-code)
2. **Decompile** → Converts .fun to .sru (PowerBuilder source)
3. **Parse** → Converts .sru to AST JSON
4. **Model** → Converts AST to semantic models
5. **Generate** → Produces Python/Dart from models

## Architectural Issues

### 1. Circular Dependency: Parse ↔ Model

**Problem**: The Parse module imports from Model, and Model imports from Parse
- `src/parse/library.py` imports `src/model/ast/serialization`
- `src/model/coordinator.py` imports from parse modules

**Impact**: Makes the modules tightly coupled and difficult to test/maintain independently

**Recommendation**: 
- Move shared AST definitions to a separate `src/ast/` module
- Or move serialization utilities to `src/common/`

### 2. Unused Code

**STRING_TABLE_OFFSET Import**:
- Imported in 30+ files but never used
- Suggests a refactoring that wasn't completed

**Unused Variables in Transformers**:
- 100+ unused variables in parse/visitors/transformer.py
- Indicates either incomplete implementation or poor code cleanup

### 3. Module Dependencies

Based on the analysis, here's the actual dependency graph:

```
common (base layer)
   ↓
extract
   ↓
decompile
   ↓
parse ←→ model (circular!)
   ↓      ↓
generate
```

## Dataclass Architecture

The project uses 81 dataclasses for type safety:
- AST nodes (src/model/ast/nodes/)
- PowerBuilder entities (src/model/entities/)
- Extraction structures (src/extract/pbd/structures/)
- Type definitions (src/model/types/)

## Unused Modules

### In Root Directory
- Multiple test scripts (test_*.py) should be in tests/
- Analysis scripts should be in tools/
- Configuration files mixed with code

### In Archive Directory
- Old modules preserved for reference
- Should be moved to docs/legacy/ or removed

## Test Coverage

- ~200 tests total
- ~45% passing (90 tests)
- Main issues:
  - Missing test fixtures
  - Hardcoded paths
  - Integration tests need real PBD files

## Recommendations

### 1. Fix Circular Dependency
```python
# Option 1: Move AST to common
src/common/ast/
├── nodes.py
├── serialization.py
└── visitors.py

# Option 2: Use dependency injection
# In parse/library.py
def __init__(self, serializer=None):
    self.serializer = serializer or get_default_serializer()
```

### 2. Clean Up Imports
```bash
# Remove all unused STRING_TABLE_OFFSET imports
ruff check --select F401 --fix src/

# Remove other unused imports
ruff check --select F --fix src/
```

### 3. Reorganize Project Structure
```
powerrebuilder/
├── src/           # Core source code
├── tests/         # All tests
├── tools/         # Development tools
├── docs/          # Documentation
├── config/        # Configuration files
└── data/          # Test data
```

### 4. Module Decoupling Strategy

1. **Define Clear Interfaces**:
   - Each module should have a `contracts/` subdirectory
   - Define input/output types explicitly
   - Use dependency injection for cross-module communication

2. **Pipeline Coordinator Pattern**:
   - Current pipeline coordinator is good
   - Extend to handle all inter-module communication
   - Modules shouldn't import from each other directly

3. **Shared Types Module**:
   ```python
   src/types/
   ├── ast.py      # AST node types
   ├── powerbuilder.py  # PB-specific types
   ├── pipeline.py      # Pipeline communication types
   └── common.py        # Shared basic types
   ```

## Test Strategy

1. **Unit Tests**: Test each module in isolation
2. **Integration Tests**: Test pipeline stages
3. **End-to-End Tests**: Full PBD → Python/Dart conversion
4. **Property Tests**: Use hypothesis for parsers/transformers

## Performance Considerations

- Large number of regex compilations in parsers
- Consider caching compiled patterns
- Use lazy imports for heavy modules
- Profile the pipeline to find bottlenecks

## Security Considerations

- Path traversal protection in extract module
- Input validation for user-provided files
- Sandbox code generation to prevent injection

## Next Steps

1. **Immediate** (1-2 days):
   - Fix circular dependency
   - Clean up unused imports
   - Move test files to proper locations

2. **Short-term** (1 week):
   - Implement module interfaces
   - Add missing test fixtures
   - Document module boundaries

3. **Long-term** (2-4 weeks):
   - Refactor to microservice-ready architecture
   - Add comprehensive integration tests
   - Implement performance optimizations