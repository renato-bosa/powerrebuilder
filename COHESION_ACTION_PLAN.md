# Cohesion-Based File Consolidation Action Plan

## Executive Summary

Analysis of 302 Python files revealed:
- 99 files with no functions/classes (33%)
- 3 pure re-export files that can be immediately removed
- Multiple low-cohesion files with mixed responsibilities
- Opportunities to consolidate ~20-30 files

## Immediate Actions (Safe, High Impact)

### 1. Remove Pure Re-export Files

These files only re-export from other modules and add no value:

```bash
# Update imports in affected files
sed -i '' 's/from src.model.ast.node_kind import NodeKind/from src.model.types.base import NodeKind/g' src/decompile/extractors/datawindow_integration.py
sed -i '' 's/from src.model.ast.node_kind import NodeKind/from src.model.types.base import NodeKind/g' src/model/expressions/ast_expressions.py
sed -i '' 's/from src.model.utils.base import PBNode/from src.model.types.base import PBNode/g' src/model/base/pb_entity.py

# Remove the re-export files
rm src/extract/security/limits.py
rm src/model/utils/base.py
rm src/model/ast/node_kind.py
```

### 2. Consolidate Frequently-Used Constants

**src/extract/pbd/constants.py** (0 definitions, imported by 7 files)
- Action: Move constants to `src/extract/pbd/__init__.py` or create `src/extract/pbd/core.py`
- This centralizes PBD-specific constants where they're most used

## Short-term Actions (1-2 days)

### 3. Merge Small Specialized Parsers

**src/parse/parser/specialized/sql.py** (1 function: `parse_sql`)
- Action: Move to `src/parse/parser/sql.py` if it exists, or create a unified SQL parser module

### 4. Consolidate Type Definition Files

These files have 2 or fewer type definitions:
- `src/decompile/types.py` (2 definitions, used by 4 files)
- `src/parse/types.py` (2 definitions)
- `src/model/types/decompile.py` (2 definitions)

Action: Review if these types belong in their parent module's `__init__.py` or a central types module

### 5. Merge Utility Functions by Domain

**String/Text Utilities:**
- Keep `src/common/utils/strings.py` as the central location
- Move text extraction functions from `src/extract/pbd/text.py` if they're generic

**Image Utilities:**
- Create `src/common/utils/images.py`
- Move from `src/extract/pbd/io.py`: get_bmp_size, get_ico_size, get_image_format
- Keep PBD-specific image handling in extract module

## Medium-term Actions (1 week)

### 6. Refactor Mixed-Purpose Files

**src/extract/pbd/io.py** - Currently contains:
- Image format detection (get_image_format, get_bmp_size, get_ico_size)
- Resource size estimation (estimate_resource_size)

Action: Split into:
- Image functions → `src/common/utils/images.py`
- Resource estimation → keep in module or move to `src/extract/pbd/resources.py`

### 7. Consolidate Empty __init__.py Files

Many __init__.py files only contain imports. Options:
1. Use `__all__` exports in parent modules
2. Remove unnecessary re-exports
3. Merge small submodules into parent

Priority targets:
- All files with 0 definitions and < 20 lines of code
- Focus on deep nesting (4+ levels)

## Long-term Actions (2-4 weeks)

### 8. Module Structure Simplification

Current issues:
- Deep nesting (up to 5 levels)
- Many single-file modules
- Unclear boundaries between modules

Proposed structure:
```
src/
├── common/       # Shared utilities
│   ├── utils.py  # Or utils/ with domain files
│   └── types.py  # Common type definitions
├── extract/      # Extraction logic
│   ├── pbd.py    # Consolidate small PBD files
│   └── ...
├── parse/        # Parsing logic
│   ├── grammar/  # Keep separate (large)
│   └── ...
└── ...
```

## Testing Strategy

For each consolidation:
1. Run existing tests to ensure they pass
2. Update import statements in tests
3. Check for dynamic imports or string-based imports
4. Run coverage to ensure no regression

## Risk Mitigation

1. **Version Control**: Create a branch for each consolidation phase
2. **Incremental Changes**: One module at a time
3. **Import Verification**: Use AST analysis to find all imports
4. **CI/CD**: Ensure all tests pass before merging

## Success Metrics

- Reduce file count by 10-15% (30-45 files)
- Improve average cohesion score
- Reduce import depth
- Maintain 100% test coverage
- No runtime errors from import changes

## Excluded from Consolidation

These files should remain separate despite low cohesion:
- `src/core/constants.py` - Large file (1894 lines) with domain-specific constants
- `__init__.py` files that contain package documentation
- Interface/protocol files that define contracts
- Files with version-specific or platform-specific code