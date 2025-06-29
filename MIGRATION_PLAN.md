# SIME Finch Codebase Migration Plan

## Executive Summary

This plan outlines the comprehensive reorganization of the SIME Finch codebase to achieve:
- **50-60% reduction** in file count
- Clearer module boundaries
- Better testability
- Improved maintainability
- Consistent structure across all modules

## Current vs Desired Structure

### Current Issues
- Scattered functionality across multiple files
- Duplicate implementations
- Unclear module boundaries
- Deep nesting without clear purpose
- Mixed concerns within modules

### Desired Structure
```
src/
├── extract/     # Binary extraction from PBD/PBL files
├── parse/       # Grammar-based parsing to AST
├── decompile/   # P-code decompilation
├── model/       # Object model and analysis
├── generate/    # Code generation (Flutter/Dart)
├── common/      # Shared utilities
└── pipeline/    # Orchestration and execution
```

## Migration Strategy

### Phase 1: Preparation (Day 1)
1. **Create full backup**
   ```bash
   cp -r . ../sime-finch-backup-$(date +%Y%m%d)
   ```

2. **Run migration script in dry-run mode**
   ```bash
   python tools/migration/reorganize_structure.py --dry-run > migration_preview.txt
   ```

3. **Review migration preview**
   - Check file movements
   - Verify no critical files are deleted
   - Ensure all merges make sense

### Phase 2: Structure Creation (Day 1)
1. **Create new directory structure**
   ```bash
   python tools/migration/reorganize_structure.py --create-dirs-only
   ```

2. **Verify structure**
   ```bash
   tree src/ -d -L 3
   ```

### Phase 3: Module Migration (Days 2-4)

#### Day 2: Extract & Parse Modules
1. **Migrate Extract module**
   - Move core extraction logic
   - Consolidate binary utilities
   - Merge redundant extractors

2. **Migrate Parse module**
   - Move grammar files
   - Consolidate parsers
   - Merge transformer logic

#### Day 3: Decompile & Model Modules
1. **Migrate Decompile module**
   - Consolidate P-code handling
   - Merge formatters
   - Unify reconstruction logic

2. **Migrate Model module**
   - Reorganize AST nodes
   - Consolidate entities
   - Create clear type system

#### Day 4: Generate & Common Modules
1. **Migrate Generate module**
   - Focus on Flutter generation
   - Remove Python generation
   - Consolidate converters

2. **Migrate Common module**
   - Create shared interfaces
   - Consolidate utilities
   - Set up pipeline structure

### Phase 4: Test Reorganization (Day 5)
1. **Consolidate unit tests**
   ```
   tests/unit/
   ├── extract/
   ├── parse/
   ├── decompile/
   ├── model/
   └── generate/
   ```

2. **Move integration tests**
   ```
   tests/integration/
   ├── test_pipeline.py
   ├── test_e2e_pbd_to_flutter.py
   └── test_cross_module.py
   ```

### Phase 5: Import Updates (Day 6)
1. **Run import updater**
   ```bash
   python tools/migration/update_imports.py
   ```

2. **Fix remaining import issues**
   - Manual review of complex imports
   - Update relative imports
   - Fix circular dependencies

### Phase 6: Cleanup (Day 7)
1. **Remove old directories**
   ```bash
   python tools/migration/cleanup_old_structure.py
   ```

2. **Update configuration files**
   - `pyproject.toml`
   - `Makefile`
   - `.github/workflows/`

3. **Update documentation**
   - README.md
   - Architecture docs
   - Development guides

## Key Consolidations

### Extract Module
- **File Operations** (3 files → 1 reader.py)
  - file_operations.py
  - pe_scanner.py
  - resource_utils.py

- **Binary Extractors** (3 files → 1 binary.py)
  - string_extractor.py
  - enhanced_image_extractor.py
  - resource_extraction_manager.py

### Parse Module
- **Parsers** (2 files → 1 powerbuilder.py)
  - parser.py
  - enhanced_parser.py

- **Error Recovery** (2 files → 1 strategy.py)
  - error_recovery.py
  - enhanced_error_recovery.py

### Decompile Module
- **Formatters** (2 files → 1 formatter.py)
  - output_formatter.py
  - simple_formatter.py

- **Expression Reconstruction** (2 files → 1 expression.py)
  - expression_reconstructor.py
  - advanced_expression_reconstructor.py

### Model Module
- **UI Components** (1 file → 3 files)
  - ui.py → window.py, menu.py, user_object.py

- **DataWindow** (directory → 1 file)
  - datawindow/*.py → entities/datawindow.py

### Generate Module
- **Remove Python generation**
  - Delete generate/python/
  - Delete generate/templates/python/
  - Focus exclusively on Flutter

## File Merge Guidelines

When merging files:

1. **Preserve all functionality**
   - Don't delete code without verification
   - Mark duplicates for later cleanup

2. **Organize by responsibility**
   ```python
   # Example merge structure
   class UnifiedExtractor:
       """Merged from multiple extractors."""
       
       # From string_extractor.py
       def extract_strings(self, data: bytes) -> List[str]:
           ...
       
       # From enhanced_image_extractor.py
       def extract_images(self, data: bytes) -> List[Image]:
           ...
       
       # From resource_extraction_manager.py
       def extract_resources(self, data: bytes) -> Dict[str, Any]:
           ...
   ```

3. **Update imports progressively**
   - Keep old imports working temporarily
   - Add deprecation warnings
   - Remove after full migration

## Success Criteria

1. **All tests pass**
   ```bash
   pytest tests/
   ```

2. **No broken imports**
   ```bash
   python -m py_compile src/**/*.py
   ```

3. **Documentation updated**
   - Architecture reflects new structure
   - README has correct paths
   - Examples work

4. **Clean git status**
   ```bash
   git status --porcelain
   ```

## Rollback Plan

If issues arise:

1. **Restore from backup**
   ```bash
   rm -rf ./*
   cp -r ../sime-finch-backup/* .
   ```

2. **Reset git**
   ```bash
   git reset --hard HEAD
   git clean -fd
   ```

3. **Document issues**
   - What failed?
   - Which step caused problems?
   - How to avoid in retry?

## Post-Migration Tasks

1. **Update CI/CD**
   - Fix GitHub Actions paths
   - Update test commands
   - Verify builds work

2. **Performance testing**
   - Benchmark before/after
   - Ensure no regressions
   - Document improvements

3. **Team communication**
   - Announce structure changes
   - Update development docs
   - Provide migration guide

## Timeline

- **Week 1**: Preparation and core module migration
- **Week 2**: Test migration and import updates
- **Week 3**: Cleanup and documentation
- **Week 4**: Team onboarding and optimization

## Notes

- Run migration during low-activity period
- Keep backup for at least 30 days
- Document any deviations from plan
- Create issues for delayed consolidations