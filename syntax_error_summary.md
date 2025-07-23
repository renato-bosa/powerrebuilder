# Syntax Error Summary Report

## Overview
- **Total files with errors:** 21
- **Total errors:** 21 (one per file)
- **Date:** 2025-07-23

## Error Distribution by Type

| Error Type | Count | Percentage |
|------------|-------|------------|
| elif/else without if | 10 | 47.6% |
| Unmatched parentheses | 4 | 19.0% |
| Unexpected indent | 3 | 14.3% |
| except without try | 2 | 9.5% |
| Invalid syntax (other) | 2 | 9.5% |

## Error Distribution by Module

| Module | Files with Errors |
|--------|-------------------|
| decompile | 8 |
| model | 6 |
| extract | 4 |
| parse | 3 |

## Most Common Patterns

### 1. Control Flow Errors (elif/else without if)
These errors typically occur when:
- An `if` statement is missing or incomplete
- Indentation issues cause the `elif`/`else` to not match with its `if`
- Code was partially deleted or refactored

**Example files:**
- `src/decompile/analyzers/parser.py:46`
- `src/parse/parser/specialized/types.py:84`
- `src/model/services/ast_processor.py:36`

### 2. Parentheses Mismatch
These errors occur from:
- Missing opening parenthesis
- Extra closing parenthesis
- Incomplete function calls or definitions

**Example files:**
- `src/decompile/pcode/detector.py:14`
- `src/extract/components/resources.py:91`
- `src/extract/components/statistics.py:83`

### 3. Indentation Errors
These are usually caused by:
- Mixed tabs and spaces
- Incorrect indentation levels
- Copy-paste errors

**Example files:**
- `src/decompile/pcode/opcodes/variants.py:426`
- `src/model/types/powerbuilder.py:24`
- `src/model/entities/method_call.py:40`

## Priority Fix Order

1. **Core Infrastructure** (4 files)
   - Files in pcode, types, and utils that other modules depend on
   
2. **Processing Pipeline** (6 files)
   - AST processor, model persistence, analyzers
   
3. **Parser System** (5 files)
   - Specialized parsers and preprocessors
   
4. **Analysis & Security** (2 files)
   - Security analyzer and symbol resolver
   
5. **Extract Components** (4 files)
   - Validator, recovery, resources, statistics

## Quick Fix Script

```bash
#!/bin/bash
# Verify all syntax errors are fixed

echo "Checking Python syntax errors..."

files=(
    "src/decompile/pcode/detector.py"
    "src/decompile/pcode/opcodes/variants.py"
    "src/model/types/powerbuilder.py"
    "src/extract/utils/encoding.py"
    "src/decompile/analyzers/parser.py"
    "src/decompile/analysis/control.py"
    "src/decompile/reconstruction/expression.py"
    "src/decompile/pcode/recovery.py"
    "src/model/services/ast_processor.py"
    "src/model/services/model_persistence.py"
    "src/parse/parser/specialized/transactions.py"
    "src/parse/parser/specialized/types.py"
    "src/parse/preprocessor/imports.py"
    "src/model/types/validation.py"
    "src/model/entities/method_call.py"
    "src/model/analysis/security.py"
    "src/model/symbols/resolver.py"
    "src/extract/components/validator.py"
    "src/extract/components/recovery.py"
    "src/extract/components/resources.py"
    "src/extract/components/statistics.py"
)

error_count=0
for file in "${files[@]}"; do
    if python3 -m py_compile "$file" 2>/dev/null; then
        echo "✓ $file"
    else
        echo "✗ $file - STILL HAS ERRORS"
        ((error_count++))
    done
done

echo ""
echo "Total files checked: ${#files[@]}"
echo "Files with errors: $error_count"
```

## Next Steps

1. Use `syntax_errors_to_fix.txt` as a checklist
2. Fix errors in priority order
3. Test each fix with `python3 -m py_compile`
4. Run the verification script after all fixes
5. Commit fixes in logical groups