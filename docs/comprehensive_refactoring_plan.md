# Comprehensive Refactoring Plan for SIME-Finch Project

## Executive Summary

After analyzing all Python modules in the project, I've identified significant opportunities for consolidation and cleanup. The main issues are:

1. **Duplicate implementations** - Multiple parsers, decompilers, and AST nodes doing the same thing
2. **Poor organization** - Files in wrong directories, misleading names, artificial separations
3. **Incomplete migrations** - Half-finished reorganization attempts leaving duplicates
4. **Circular dependencies** - Especially in the extract module
5. **Unused code** - Empty files, stub implementations, and abandoned features

## Module-by-Module Findings

### 1. Parse Module

**Major Issues:**
- Duplicate parser implementations in root vs `parsers/` subdirectory
- `parse_coordinator.py` contains actual parser implementations, not coordination
- Incomplete migration to organized structure

**Files to Remove:**
```
parse/parsers/             # Entire directory - duplicate implementations
parse/pseudocode_parser.py # Old implementation
parse/logging.py          # Already removed
```

**Files to Rename:**
- `parse_coordinator.py` → `powerbuilder_parser.py` (or split into multiple files)
- `transaction_parser.py` - Fix class name from `Parser` to `TransactionParser`

### 2. Extract Module

**Major Issues:**
- Artificial split between `pbd_core/` and `pbd_io/` causing circular dependencies
- Redundant exception handling through multiple layers
- Poor naming (`core.py` is too generic)

**Consolidation Plan:**
Merge into single `pbd/` module:
```
extract/pbd/
├── structures/      # Header, Node, Entry, DataBlock
├── extraction/      # Core extraction logic
├── io/             # File operations, scanning
├── utils/          # Text, binary, hash utilities
└── analysis/       # Cross-references, DataWindow detection
```

### 3. Decompile Module

**Major Issues:**
- Two complete decompiler implementations
- Unused IR implementation and templates
- Unnecessary `generators/` directory with one file

**Files to Remove:**
```
decompile/generators/unified_decompiler.py  # Duplicate implementation
decompile/generators/                       # Directory no longer needed
decompile/core/pcode_ir.py                 # Unused IR
decompile/templates/                        # Unused Jinja2 template
```

**Files to Move:**
- `decompile_coordinator.py` → `core/decompiler.py`

### 4. Model Module

**Major Issues:**
- Multiple representations of same concepts (3 ways to represent function arguments!)
- Stub implementations mixed with real ones
- Unclear distinction between `ast/`, `constructs/`, `entities/`

**Duplicate Classes to Consolidate:**
1. Function Arguments: Choose one of:
   - `entities/pb_function.py` → `PBFunctionArgumentNode`
   - `ast/functions.py` → `Parameter`
   - `entities/pb_argument.py` → `PBArgumentNode`

2. Variables: Consolidate multiple `PBVariable` classes
3. Functions: Consolidate `Function` and `PBFunction` implementations

### 5. Generate Module

**Major Issues:**
- `python.py` in wrong location (it's not a template)
- Extremely long template files (1400+ lines)
- Missing template organization features

**Actions:**
- Move `backend/templates/python.py` → `backend/code_generator.py`
- Split `datawindow_widget.dart.jinja2` into smaller components
- Add template inheritance and partials

## Priority Action Plan

### Phase 1: Remove Duplicates (High Priority)
1. Delete `parse/parsers/` directory and `pseudocode_parser.py`
2. Delete duplicate decompiler in `generators/`
3. Remove unused `pcode_ir.py` and templates
4. Clean up empty `__init__.py` files

### Phase 2: Fix Naming and Organization (Medium Priority)
1. Rename `parse_coordinator.py` appropriately
2. Fix `Parser` class name to `TransactionParser`
3. Move `decompile_coordinator.py` to `core/decompiler.py`
4. Move `python.py` out of templates directory

### Phase 3: Consolidate Modules (Medium Priority)
1. Merge `pbd_core/` and `pbd_io/` into single `pbd/` module
2. Consolidate duplicate AST node implementations in model
3. Remove stub implementations from `pb_behavioral.py`

### Phase 4: Improve Structure (Low Priority)
1. Split large template files
2. Add template inheritance
3. Implement missing methods (e.g., `is_pcode_object()`)
4. Add proper error handling and validation

## Expected Benefits

1. **Reduced Complexity**: ~30% fewer files to maintain
2. **Clearer Structure**: Obvious where to find/add functionality
3. **No Circular Dependencies**: Clean module boundaries
4. **Better Performance**: Less redundant code execution
5. **Easier Onboarding**: New developers can understand the structure

## Implementation Strategy

1. **Create a branch** for each phase
2. **Update imports** after each change
3. **Run tests** to ensure nothing breaks
4. **Update documentation** to reflect new structure
5. **Commit atomically** for easy rollback if needed

## Files to Delete Immediately

These files are safe to delete with no impact:
```bash
# Empty or nearly empty files
find . -name "__init__.py" -size 0 -delete

# Duplicate implementations
rm -rf parse/parsers/
rm parse/pseudocode_parser.py
rm decompile/generators/unified_decompiler.py
rm decompile/core/pcode_ir.py
rm -rf decompile/templates/

# Old debug scripts (already cleaned up)
# Scripts in scripts/debug/ that were removed
```

## Long-term Recommendations

1. **Establish naming conventions** - Document and enforce consistent naming
2. **Create architectural guidelines** - Define when to create new modules vs extending existing ones
3. **Regular cleanup sprints** - Prevent accumulation of duplicate/unused code
4. **Improve test coverage** - Better tests make refactoring safer
5. **Add CI checks** - Detect circular dependencies, unused imports, etc.

This refactoring will significantly improve code maintainability and developer experience while preserving all functionality.