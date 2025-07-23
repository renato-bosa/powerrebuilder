# Test Recovery Status Report

Generated: 2025-07-23

## Summary

After the module consolidation and flattening, many test imports were broken. This report tracks the recovery progress.

## Import Mapping Created

### Common Utilities
- `src.model.utils.common` → Split into:
  - `src.common.utils.strings` (camel_to_snake, snake_to_camel, truncate, pluralize)
  - `src.common.utils.files` (ensure_directory, get_file_extension, normalize_path, read_file_safe, format_timestamp, safe_cast, safe_json_loads, to_bool)
  - `src.common.utils.collections` (chunk_list, find_duplicates, filter_dict, merge_dicts)

### Contracts
- `src.contracts.extractors` → `src.contracts`
- `src.contracts.parsers` → `src.contracts`
- `src.contracts.decompilers` → `src.contracts`
- `src.contracts.generators` → `src.contracts`

### Model/AST
- Fixed `src.model.ast.__init__.py` - removed imports from non-existent modules
- Created minimal node classes in `src.model.ast.literals.py`

### Pipeline
- Fixed exports in `src.common.pipeline.__init__.py`
- Added backward compatibility aliases for renamed classes

## Test Status

### ✅ Working Test Modules

1. **tests/unit/common/test_common.py**
   - Status: All 16 tests passing
   - Fixed imports from consolidated utils modules

2. **tests/unit/common/test_common_pipeline.py**
   - Status: 17/20 tests passing
   - Issues:
     - Logger name assertion needs updating
     - Mock patch targets need fixing for `extract.pbd`

### 🔧 Modules Still Needing Fixes

Based on initial pytest collection errors:

1. **tests/generate/test_python.py**
   - Issue: `ModuleNotFoundError: No module named 'src.model.ast.node_kind'`
   - Fix: Already addressed in ast __init__.py

2. **tests/generate/test_system_functions_template.py**
   - Issue: `NameError: name 'register_system_function' is not defined`
   - Status: Import path updated to `src.model.expressions`

3. **tests/integration/experimental/test_corruption_fix.py**
   - Issue: `ModuleNotFoundError: No module named 'src.contracts.extractors'`
   - Status: Import path updated

4. **tests/integration/experimental/test_hypothesis_examples.py**
   - Issue: `ModuleNotFoundError: No module named 'src.common.utils.datawindow'`
   - Fix: Need to locate or recreate DataWindowDetector

5. **tests/integration/experimental/test_with_factories.py**
   - Issue: `ModuleNotFoundError: No module named 'tests.factories'`
   - Status: Import path updated to `tests.utils.factories`

## Next Steps

1. **Fix remaining import issues in test files**
   - Update mock patch targets
   - Fix test assertions for changed module paths
   - Locate missing utility classes like DataWindowDetector

2. **Run tests by module**
   - Start with unit tests that have fewest dependencies
   - Progress to integration tests
   - Document any missing functionality

3. **Create missing test fixtures/mocks**
   - Identify what test utilities are missing
   - Create minimal implementations as needed

4. **Update CI configuration**
   - Ensure test discovery works with new structure
   - Update any hardcoded paths

## Estimated Completion

- Import fixes: 60% complete
- Test recovery: 20% complete
- Estimated time to full recovery: 2-3 hours of focused work

## Recommendations

1. Focus on unit tests first as they have fewer dependencies
2. Create a script to automatically fix common import patterns
3. Consider creating compatibility shims for heavily used moved modules
4. Document all moved/renamed modules for future reference