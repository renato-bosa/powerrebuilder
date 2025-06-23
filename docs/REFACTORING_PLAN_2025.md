# SIME Finch Structure Refactoring Plan

## Overview
This document outlines a systematic approach to refactor the SIME Finch project structure to address organic growth issues and improve maintainability.

## Principles
1. **Incremental Changes**: Small, testable changes with regression testing
2. **No Breaking Changes**: Maintain backward compatibility during refactoring
3. **Version Control**: Use jj (Jujutsu) for commits after each phase
4. **Test-Driven**: Run full test suite after each significant change
5. **Documentation**: Update docs as we go, not as afterthought

## Phase Order Rationale
The phases are ordered to:
- Start with least dependent modules (Common)
- Clean up obvious issues early (experimental files)
- Handle complex modules (Parse) after simpler ones
- End with documentation and final standardization

## Detailed Phase Plan

### Phase 0: Test Baseline (Critical)
**Goal**: Establish current test coverage and create regression test suite

**Steps**:
1. Run full test suite and document current pass/fail status
2. Check test coverage with pytest-cov
3. Create snapshot of current functionality
4. Document any known failing tests

**Commands**:
```bash
# Run tests with coverage
uv run pytest --cov=. --cov-report=html --cov-report=term

# Save baseline
cp coverage.xml tests/baseline/coverage_baseline.xml
```

**Commit**: `jj commit -m "test: establish test coverage baseline for refactoring"`

---

### Phase 1: Common Module Reorganization
**Goal**: Organize common utilities into clear submodules

**Steps**:
1. Create subdirectory structure:
   ```
   common/
   ├── pipeline/
   │   ├── __init__.py
   │   ├── pipeline.py
   │   ├── pipeline_coordinator.py
   │   └── progress.py
   ├── utils/
   │   ├── __init__.py
   │   ├── datawindow_utils.py
   │   ├── error_recovery.py
   │   └── object_type_detector.py
   ├── types/
   │   ├── __init__.py
   │   ├── types.py
   │   └── types.pyi
   └── __init__.py (updated imports)
   ```

2. Update all imports across codebase
3. Run tests after each file move
4. Consolidate .py/.pyi pairs

**Regression Test**: `uv run pytest tests/test_common/`

**Commit**: `jj commit -m "refactor: reorganize common module into submodules"`

---

### Phase 2: Clean Up Experimental and Suspicious Files
**Goal**: Remove or properly organize experimental code

**Steps**:
1. Investigate and remove `parse/grammar/experimental/~/` directory
2. Archive old experimental grammars to `tools/archive/grammars/`
3. Consolidate or remove duplicate grammar files
4. Clean up any backup files (*_backup, *_old, etc.)

**Regression Test**: `uv run pytest tests/test_parse/`

**Commit**: `jj commit -m "cleanup: remove experimental and suspicious files"`

---

### Phase 3: Extract Module Consolidation
**Goal**: Merge enhanced extractors into single implementation

**Steps**:
1. Analyze differences between extractors:
   - `extractor.py` vs `enhanced_extractor.py`
   - `enhanced_image_extractor.py` vs base
   - `unified_resource_extractor.py` purpose

2. Create consolidated extractor:
   ```python
   # extract/pbd/extraction/extractor.py
   class Extractor:
       def __init__(self, enhanced_mode=True):
           # Merge all functionality
   ```

3. Archive old extractors to `tools/archive/`
4. Update all references
5. Move `POSITION_BASED_CORRUPTION_SOLUTION.md` to docs

**Regression Test**: `uv run pytest tests/test_extract/`

**Commit**: `jj commit -m "refactor: consolidate extract module extractors"`

---

### Phase 4: Parse Module Reorganization (Complex)
**Goal**: Create clear structure for parsers and transformers

**Steps**:
1. Create new structure:
   ```
   parse/
   ├── parsers/
   │   ├── __init__.py
   │   ├── base_parser.py
   │   ├── window_parser.py
   │   ├── sql_parser.py
   │   ├── datawindow_parser.py
   │   ├── pseudocode_parser.py
   │   └── transaction_parser.py
   ├── transformers/
   │   ├── __init__.py
   │   ├── base_transformer.py
   │   ├── powerbuilder_transformer.py
   │   ├── type_transformer.py
   │   └── sql_transformer.py
   ├── grammar/
   │   └── (existing, cleaned)
   ├── visitors/
   │   └── (existing)
   ├── utils/
   │   └── (parser utilities)
   └── parse_coordinator.py
   ```

2. Move files incrementally, testing after each
3. Update imports throughout codebase
4. Merge "enhanced" versions into main implementations

**Regression Test**: `uv run pytest tests/test_parse/`

**Commit**: `jj commit -m "refactor: reorganize parse module structure"`

---

### Phase 5: Model Module Standardization
**Goal**: Consistent naming and organization

**Steps**:
1. Decide on naming convention (remove pb_ prefix uniformly)
2. Merge `constructs/` and `entities/` based on analysis
3. Create `core/` for fundamental model files
4. Rename folders for consistency:
   - `pb_datawindow/` → `datawindow/`
   - `pb_transaction/` → `transaction/`

**Regression Test**: `uv run pytest tests/test_model/`

**Commit**: `jj commit -m "refactor: standardize model module naming"`

---

### Phase 6: Decompile Module Restructuring
**Goal**: Split analysis folder and consolidate extractors

**Steps**:
1. Create new structure:
   ```
   decompile/
   ├── analyzers/
   │   ├── control_flow_analyzer.py
   │   ├── pcode_detector.py
   │   └── business_logic_mapper.py
   ├── extractors/
   │   ├── datawindow_extractor.py (consolidated)
   │   ├── schema_extractor.py
   │   └── pdw_extractor.py (consolidated)
   ```

2. Consolidate duplicate PDW/DataWindow extractors
3. Move visualization to analyzers or expand

**Regression Test**: `uv run pytest tests/test_decompile/`

**Commit**: `jj commit -m "refactor: restructure decompile module"`

---

### Phase 7: Generate Module Template Consolidation
**Goal**: Centralize templates and organize converters

**Steps**:
1. Create unified template structure:
   ```
   generate/
   ├── templates/
   │   ├── python/
   │   ├── flutter/
   │   └── base/
   ├── converters/
   │   ├── ui/
   │   ├── data/
   │   └── logic/
   ```

2. Move all templates to central location
3. Categorize converters by type
4. Rename `backend/` to `python/`

**Regression Test**: `uv run pytest tests/test_generate/`

**Commit**: `jj commit -m "refactor: consolidate generate module templates"`

---

### Phase 8: Documentation and README Creation
**Goal**: Add module-level documentation

**Steps**:
1. Create README.md for each major module
2. Document module purpose and structure
3. Add usage examples
4. Create module dependency diagram

**Commit**: `jj commit -m "docs: add module-level documentation"`

---

### Phase 9: Final Naming Standardization
**Goal**: Final pass for consistent naming

**Steps**:
1. Remove all "enhanced" prefixes
2. Standardize file naming (snake_case)
3. Ensure consistent use of abbreviations
4. Update any remaining imports

**Final Full Test**: `uv run pytest`

**Commit**: `jj commit -m "refactor: final naming standardization"`

---

## Risk Mitigation

1. **Import Errors**: Use `grep` to find all imports before moving files
2. **Test Failures**: Run specific test suites after each phase
3. **Breaking Changes**: Keep old imports with deprecation warnings temporarily
4. **Large Commits**: Use jj's excellent merge capabilities if conflicts arise

## Success Metrics

- All tests passing after each phase
- No decrease in test coverage
- Improved code navigation (measurable by IDE performance)
- Clearer module boundaries (fewer cross-module imports)
- Reduced file count at module roots

## Rollback Plan

If any phase causes significant issues:
1. Use `jj` to revert to previous commit
2. Analyze what went wrong
3. Break phase into smaller steps
4. Retry with more granular changes