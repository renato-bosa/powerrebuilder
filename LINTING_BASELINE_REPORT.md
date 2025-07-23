# Ruff Linting Baseline Report

## Summary

**Date:** 2025-07-22  
**Directory:** src/  
**Total Issues Found:** 5,606 errors  
**Fixable with --fix:** 13 errors  
**Additional fixes with --unsafe-fixes:** 351 errors  

## Critical Issues (Must Fix)

### 1. Syntax Errors
These files have critical syntax errors that prevent the code from running:

- **src/common/pipeline/modes/streaming.py** - 31 syntax errors
  - Multiple indentation errors after function definitions
  - Missing indented blocks
  
- **src/core/circuit_breaker.py** - 19 syntax errors  
  - Missing indented blocks after class definitions
  - Indentation errors in control flow statements

### 2. Import Issues
- **PLC0415** (import-outside-top-level): Found extensively in src/common/di_configuration.py
  - 66 occurrences in this file alone (full file has 706 total lines of output including context)
  - These are imports inside methods/functions instead of at module level
  - This pattern appears to be used for lazy loading in the dependency injection configuration

## Common Error Categories

Based on analysis of the contracts directory as a sample:

| Error Code | Description | Count | Fixable |
|------------|-------------|-------|---------|
| ANN003 | Missing type annotations for **kwargs | 28 | No |
| ANN401 | Using Any type | 22 | No |
| ANN002 | Missing type annotations for *args | 19 | No |
| FBT001 | Boolean type hint in positional argument | 6 | No |
| PLC0415 | Import outside top-level | 6 | No |
| FBT002 | Boolean default value in positional argument | 3 | No |
| ANN204 | Missing return type for special methods | 2 | No |
| I001 | Unsorted imports | 2 | Yes |
| W292 | Missing newline at end of file | 2 | Yes |

## Files with Most Issues

Based on the initial run output, these files/patterns appear frequently:
1. src/common/di_configuration.py - Heavy use of imports inside methods
2. src/common/pipeline/modes/streaming.py - Syntax errors
3. src/core/circuit_breaker.py - Syntax errors
4. Multiple files with type annotation issues (ANN* errors)

## Recommendations

### Immediate Actions (Critical)
1. **Fix syntax errors** in streaming.py and circuit_breaker.py - code won't run until fixed
2. **Move imports to top-level** in di_configuration.py and similar files

### Safe Automated Fixes
Running `ruff check src/ --fix` would safely fix:
- Unsorted imports (I001)
- Missing newlines at end of files (W292)
- Some formatting issues

### Manual Review Required
- Type annotations (ANN* errors) - Need careful consideration
- Boolean argument patterns (FBT* errors) - May require API design changes
- Import placement (PLC0415) - May be intentional for lazy loading

## Running Safe Fix

To apply safe fixes:
```bash
ruff check src/ --fix
```

This will only apply the 13 safe fixes identified.

## Notable Findings

### Issues NOT Found
- **F401** (unused-import): No unused imports detected
- **E501** (line-too-long): No long line violations (likely configured with appropriate line length)

### Code Quality Observations
- The codebase appears to have good import hygiene (no unused imports)
- Line length is well-managed
- Main issues are around type annotations and code structure

## Next Steps

1. **Fix critical syntax errors first** - Priority 1
   - src/common/pipeline/modes/streaming.py
   - src/core/circuit_breaker.py
2. **Run safe automated fixes** - Priority 2
   ```bash
   ruff check src/ --fix
   ```
3. **Review import placement** in di_configuration.py - Priority 3
   - Determine if lazy loading pattern is necessary
4. **Address type annotations systematically** - Priority 4
   - Start with contracts directory
   - Use gradual typing approach
5. **Consider stricter ruff configuration** after baseline is clean