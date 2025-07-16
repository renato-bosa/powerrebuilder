# Current Structure Analysis

## Overall Statistics
- Total Python files: 385
- Total lines of code: 113,591
- Average file size: 295 lines

## Module Breakdown
| Module | Files | Lines | Classes | Functions | Max Depth |
|--------|-------|-------|---------|-----------|-----------|
| common | 16 | 5,352 | 66 | 127 | 2 |
| decompile | 36 | 14,133 | 69 | 360 | 2 |
| extract | 42 | 15,537 | 38 | 400 | 3 |
| generate | 33 | 19,106 | 135 | 580 | 3 |
| model | 71 | 19,772 | 442 | 809 | 2 |
| parse | 38 | 15,235 | 119 | 654 | 3 |
| tests | 31 | 1,604 | 24 | 74 | 3 |
| tools | 118 | 22,852 | 65 | 580 | 3 |

## Potential Duplicate Files
- extract/__init__.py ↔ extract/pbd/__init__.py
- extract/__init__.py ↔ extract/pbd/analysis/__init__.py
- extract/__init__.py ↔ extract/pbd/structures/__init__.py
- extract/__init__.py ↔ extract/pbd/io/__init__.py
- extract/__init__.py ↔ extract/pbd/formatters/__init__.py
- extract/__init__.py ↔ extract/pbd/utils/__init__.py
- extract/__init__.py ↔ extract/pbd/extraction/__init__.py
- extract/__init__.py ↔ parse/__init__.py
- extract/__init__.py ↔ parse/visitors/__init__.py
- extract/__init__.py ↔ parse/parsers/__init__.py
- extract/__init__.py ↔ parse/utils/__init__.py
- extract/__init__.py ↔ parse/transformers/__init__.py
- extract/__init__.py ↔ parse/error_recovery/__init__.py
- extract/__init__.py ↔ parse/parsers/specialized/__init__.py
- extract/__init__.py ↔ decompile/__init__.py
- extract/__init__.py ↔ decompile/visualization/__init__.py
- extract/__init__.py ↔ decompile/analyzers/__init__.py
- extract/__init__.py ↔ decompile/core/__init__.py
- extract/__init__.py ↔ decompile/extractors/__init__.py
- extract/__init__.py ↔ decompile/pdw/__init__.py
... and 1738 more

## Files with Deep Nesting (>3 levels)

## Migration Impact Estimates
- Estimated file reduction: 385 → ~192 files (50% reduction)
- Estimated duplicate removal: ~1758 files
- Estimated test consolidation: ~40% reduction in test files
- Estimated total reduction: ~55-60% fewer files