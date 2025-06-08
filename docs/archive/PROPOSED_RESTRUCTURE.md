# Proposed Project Restructure

## Current Issues
1. Duplicate SQL parser implementations
2. Inconsistent naming conventions
3. Some modules doing too much (grammar.py)
4. Deprecated modules still present
5. Model coordinator not integrated with pipeline

## Proposed New Structure

```
sime-finch/
├── common/
│   ├── __init__.py
│   ├── exceptions.py          # Already consolidated ✓
│   ├── types.py               # Type definitions
│   └── utils/
│       ├── __init__.py
│       ├── file_utils.py      # Common file operations
│       ├── string_utils.py    # String manipulation
│       └── validation.py      # Common validation functions
│
├── extract/
│   ├── __init__.py
│   ├── coordinator.py         # Renamed from extract_coordinator.py
│   ├── core/                  # Renamed from pbd_core/
│   │   ├── __init__.py
│   │   ├── core.py
│   │   ├── cross_reference.py
│   │   ├── data_block.py
│   │   ├── datawindow.py
│   │   ├── entry.py
│   │   ├── header.py
│   │   ├── library.py
│   │   ├── node.py
│   │   ├── pbd_object.py
│   │   ├── pfc_utils.py
│   │   ├── symbol_table.py
│   │   ├── text_extraction.py
│   │   └── version_detector.py
│   └── io/                    # Renamed from pbd_io/
│       ├── __init__.py
│       ├── constants.py
│       ├── file_operations.py
│       ├── pe_scanner.py
│       ├── progress.py
│       ├── resource_utils.py
│       ├── scanner.py
│       └── utils.py
│
├── parse/
│   ├── __init__.py
│   ├── coordinator.py         # Renamed from parse_coordinator.py
│   ├── base_parser.py
│   ├── constants.py
│   ├── debug.py
│   ├── interactive.py
│   ├── powerbuilder_preprocessor.py  # Renamed from pb_preprocessor.py
│   ├── grammar/
│   │   └── [grammar files unchanged]
│   ├── parsers/               # NEW: Consolidate all parsers
│   │   ├── __init__.py
│   │   ├── datawindow.py      # From PowerBuilderDataWindowParser
│   │   ├── powerbuilder.py    # From PowerBuilderParser
│   │   ├── pseudocode.py      # From pseudocode_parser.py
│   │   ├── sql.py             # Consolidated SQL parser
│   │   └── transaction.py     # Fixed to extend base parser
│   ├── transformers/          # Renamed from visitors/
│   │   ├── __init__.py
│   │   ├── base.py            # Renamed from abstract_visitor.py
│   │   ├── powerbuilder_js.py # Renamed from pb_js_transformer.py
│   │   ├── position_tracker.py
│   │   ├── powerbuilder.py    # Renamed from transformer.py
│   │   └── sql.py             # Renamed from sql_transformer.py
│   └── utils/
│       ├── __init__.py
│       └── grammar_loader.py  # Renamed from grammar.py
│
├── decompile/
│   ├── __init__.py
│   ├── coordinator.py         # Renamed from decompile_coordinator.py
│   └── [rest unchanged]
│
├── model/
│   ├── __init__.py
│   ├── coordinator.py         # Renamed from model_coordinator.py
│   ├── analysis/
│   ├── ast/
│   │   └── exception_handling.py  # Renamed from base/exception.py
│   ├── [rest of structure unchanged]
│   └── utils/
│       ├── __init__.py
│       ├── base.py
│       ├── validation.py
│       └── validators.py
│       # Remove: common.py (move to common/utils/)
│       # Remove: type_system.py (deprecated)
│
├── generate/
│   ├── __init__.py
│   ├── coordinator.py         # Renamed from generate_coordinator.py
│   └── [rest unchanged]
│
└── main.py
```

## Key Changes

### 1. Standardize Coordinator Names
All coordinator files renamed to just `coordinator.py` since they're already in descriptive module directories.

### 2. Consolidate Parsers
Create `parse/parsers/` directory with one parser per file type, eliminating duplicates.

### 3. Fix Naming Issues
- `pb_preprocessor.py` → `powerbuilder_preprocessor.py`
- `visitors/` → `transformers/` (more accurate)
- `grammar.py` → `utils/grammar_loader.py`
- `model/base/exception.py` → `model/ast/exception_handling.py`

### 4. Simplify Module Names
- `pbd_core/` → `core/`
- `pbd_io/` → `io/`

### 5. Remove Deprecated Modules
- `model/utils/type_system.py`
- All re-export exception modules (after migration period)

### 6. Centralize Common Utils
Move truly common utilities to `common/utils/` to avoid duplication.

## Implementation Plan

### Phase 1: Non-Breaking Changes
1. Create new directory structure
2. Copy files to new locations
3. Update imports to use new paths
4. Add deprecation warnings to old locations

### Phase 2: Code Consolidation  
1. Merge duplicate SQL parsers
2. Fix parser hierarchy issues
3. Consolidate common utilities
4. Update all parsers to use consistent patterns

### Phase 3: Cleanup
1. Remove deprecated modules
2. Update documentation
3. Update tests
4. Remove old file locations

## Benefits

1. **Clearer Structure**: Module purposes are immediately obvious
2. **Less Duplication**: Consolidated parsers and utilities
3. **Consistent Naming**: All files follow clear conventions
4. **Better Organization**: Related files grouped together
5. **Easier Navigation**: Simpler, flatter structure where appropriate

## Migration Notes

- Use `__init__.py` files to maintain backward compatibility during transition
- Add clear deprecation warnings with suggested new imports
- Update one module at a time to minimize disruption
- Run full test suite after each change