# Python File Cohesion Analysis and Merge Plan

## Summary

Analyzed 302 Python files in src/ directory:
- 99 files have no functions/classes (mostly __init__.py files)
- 3 files have exactly 1 definition
- 4 files identified as utility files
- 17 files identified as interface/base files
- Many files are just re-exports or have very low cohesion

## Priority 1: Remove Pure Re-export Files

These files exist only to re-export from other modules and can be eliminated:

1. **src/extract/security/limits.py** (4 lines)
   - Just re-exports from `src.core.resource_limits`
   - Action: Update imports to use `src.core.resource_limits` directly

2. **src/model/utils/base.py** (5 lines)
   - Just re-exports from `src.model.types.base`
   - Action: Update imports to use `src.model.types.base` directly

3. **src/model/ast/node_kind.py** (5 lines)
   - Just re-exports from `src.model.types.base`
   - Action: Update imports to use `src.model.types.base` directly

## Priority 2: Consolidate String/Text Utilities

Multiple files with text processing functions that could be merged:

1. **Merge into `src/common/utils/strings.py`:**
   - `src/extract/pbd/text.py` - Text extraction utilities
   - Any string manipulation functions from other utils files
   - Functions: camel_to_snake, snake_to_camel, truncate, pluralize

## Priority 3: Consolidate Image/Resource Utilities

1. **Create `src/extract/utils/images.py`:**
   - Move functions from `src/extract/pbd/io.py`: get_bmp_size, get_ico_size, get_image_format
   - Move image-related functions from `src/extract/pbd/images.py`
   - Keep resource-specific functions separate

## Priority 4: Merge Small Type Definition Files

1. **Merge type files with < 2 definitions:**
   - `src/decompile/types.py` (2 definitions) → merge into parent module
   - `src/parse/types.py` (2 definitions) → merge into parent module
   - `src/model/types/decompile.py` (2 definitions) → merge into parent module

## Priority 5: Consolidate Constants

1. **Review constant files:**
   - `src/core/constants.py` (1894 lines, 1 class) - Very large, keep separate
   - `src/extract/pbd/constants.py` (83 lines) - Could merge with PBD base module

## Priority 6: Clean Up Empty __init__.py Files

Many __init__.py files contain only imports/exports. Consider:
1. Using proper package exports in parent __init__.py
2. Removing unnecessary re-exports
3. Consolidating related modules

## Cohesion Issues Found

### Files with Mixed Purposes

1. **src/extract/pbd/io.py**
   - Contains: Image format detection + resource size estimation
   - Should split: Image functions → image utils, Resource functions → resource utils

2. **src/common/utils/strings.py**
   - Contains: Case conversion + text manipulation + pluralization
   - Cohesive enough, but could separate formatting from manipulation

3. **src/parse/utils/loader.py**
   - Contains: Type parsing + grammar loading + rule extraction
   - Should split: Grammar operations vs type operations

## Recommendations

### Immediate Actions (High Impact, Low Risk)

1. **Delete pure re-export files** (3 files)
   - Update all imports
   - Remove redundant files

2. **Merge single-function files** into related modules
   - `src/parse/parser/specialized/sql.py` (1 function) → merge into SQL parser

3. **Consolidate utility functions** by domain
   - String utilities
   - File utilities  
   - Type utilities

### Medium-term Actions

1. **Reorganize module structure** to reduce depth
   - Many modules have 4-5 levels of nesting
   - Consider flattening where logical

2. **Create domain-specific utility modules**
   - `imaging.py` for all image operations
   - `text_processing.py` for all text operations
   - `type_utils.py` for all type conversions

### Testing Considerations

- Each merge should maintain existing test coverage
- Update import statements in tests
- Run full test suite after each consolidation

## Metrics After Proposed Changes

- Estimated file reduction: ~20-30 files
- Improved module cohesion
- Reduced import complexity
- Better code discoverability