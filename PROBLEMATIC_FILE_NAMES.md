# Problematic File Naming Patterns in PowerRebuilder

This report identifies Python files with naming patterns that suggest duplicates, versions, or temporary code.

## Files with "enhanced_" prefix (excluding archive/venv)

### In src/:
1. `/src/extract/pbd/structures/enhanced_entry_parser.py`
2. `/src/decompile/extractors/enhanced_datawindow_extractor.py`
3. `/src/extract/pbd/extraction/enhanced_image_extractor.py`
4. `/src/decompile/extractors/enhanced_datawindow_integration.py`
5. `/src/decompile/analysis/enhanced_control_flow.py`
6. `/src/parse/transformer/enhanced_type_transformer.py`

### In tests/:
1. `/tests/test_enhanced_recovery.py`
2. `/tests/test_enhanced_error_recovery.py`
3. `/tests/test_enhanced_decode.py`
4. `/tests/test_100_percent_accuracy/test_enhanced_extraction.py`
5. `/tests/unit/decompile/test_simple_formatter_enhanced.py`
6. `/tests/unit/decompile/test_enhanced_datawindow_extractor.py`
7. `/tests/unit/decompile/test_enhanced_datawindow_integration.py`
8. `/tests/unit/decompile/test_control_flow_enhanced.py`
9. `/tests/unit/decompile/test_output_formatter_enhanced.py`
10. `/tests/unit/decompile/test_enhanced_decompilation.py`

### In tools/:
1. `/tools/pipeline/test_enhanced_decompiler.py`

## Files with "_refactored" suffix (excluding archive/venv)

1. `/src/model/coordinator_refactored.py`
2. `/src/generate/coordinator_refactored.py`

## Files with version patterns "_v2", "_v3", etc. (excluding archive/venv)

### In tests/:
1. `/tests/unit/decompile/test_pcode_decoder_v2.py`
2. `/tests/unit/decompile/test_stack_emulator_v2.py`

## Files with "_new" pattern (excluding archive/venv)

1. `/tests/integration/test_new_fixtures.py`

## Files with "_fixed" pattern (excluding archive/venv)

1. `/tests/test_fixed_pipeline.py`

## Other Problematic Patterns Found

### Duplicate base names (same filename in different directories)
- Multiple files have the same base name which can cause confusion:
  - `coordinator.py` appears in: src/extract/, src/parse/, src/decompile/, src/model/, src/generate/
  - `exceptions.py` appears in: src/parse/, src/extract/pbd/, src/common/, and more
  - `constants.py` appears in: src/parse/, src/extract/pbd/, src/common/
  - Many `__init__.py` files throughout (this is expected in Python)

### Confusing similar names
- `src/extract/pbd/extraction/` and `src/extract/pbd/extractors/` - two directories with very similar names
- `src/model/coordinator.py` and `src/model/coordinator_refactored.py` - duplicates
- `src/generate/coordinator.py` and `src/generate/coordinator_refactored.py` - duplicates
- Multiple template files with similar names in data/complete_pipeline_test/:
  - `2_decompiled/`, `2_decompiled_enhanced/`, `2_decompiled_final/`, `2_decompiled_fixed/`

## Summary

Total problematic files found (excluding archive and venv):
- **enhanced_** prefix: 17 files (6 in src/, 10 in tests/, 1 in tools/)
- **_refactored** suffix: 2 files (both in src/)
- **_v[0-9]** pattern: 2 files (both in tests/)
- **_new** pattern: 1 file (in tests/)
- **_fixed** pattern: 1 file (in tests/)
- **Duplicate base names**: 5+ coordinator.py files, 3+ exceptions.py files, 3+ constants.py files
- **Confusing similar directories**: extraction/ vs extractors/
- **Multiple versions in data**: 4 different decompiled directories

**Total: 23+ files with problematic naming patterns plus structural naming issues**

## Recommendations

1. **For "enhanced_" files**: These likely represent improved versions of existing functionality. Consider:
   - Merging enhanced functionality into the main implementation
   - Removing the "enhanced_" prefix if this is now the standard implementation
   - Deleting old versions if the enhanced version has replaced them

2. **For "_refactored" files**: These appear to be duplicate coordinators that should be:
   - Merged with the original coordinator files
   - Or replace the original if the refactored version is superior
   - Delete the duplicate to avoid confusion

3. **For version-numbered files (_v2, _v3)**: These suggest iterative development:
   - Keep only the latest version
   - Remove older versions or move to archive

4. **For "_new" and "_fixed" files**: These temporary names should be:
   - Renamed to proper descriptive names
   - Or merged with existing functionality

5. **For duplicate base names across modules**:
   - Consider using more specific names (e.g., `extract_coordinator.py` instead of just `coordinator.py`)
   - Or use a consistent naming pattern across all modules

6. **For confusing similar directories**:
   - `extraction/` vs `extractors/` should be clarified:
     - Consider merging them if they serve similar purposes
     - Or rename to be more distinct (e.g., `extraction_logic/` vs `extractor_classes/`)

7. **For multiple test data versions**:
   - Keep only the final/working version
   - Archive or remove intermediate versions
   - Use version control for tracking changes instead of filename suffixes