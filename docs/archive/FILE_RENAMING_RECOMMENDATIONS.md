# File Renaming Recommendations

## Files That Need Renaming

### 1. Misleading Names (High Priority)

| Current Name | Proposed Name | Reason |
|-------------|---------------|---------|
| `model/base/exception.py` | `model/ast/exception_handling.py` | Contains AST nodes for try-catch, not exceptions |
| `model/utils/type_system.py` | **DELETE** | Deprecated re-export module |
| `parse/grammar.py` | `parse/utils/grammar_loader.py` | Does more than just grammar - loads and parses types |

### 2. Inconsistent Naming (Medium Priority)

| Current Name | Proposed Name | Reason |
|-------------|---------------|---------|
| `parse/pb_preprocessor.py` | `parse/powerbuilder_preprocessor.py` | Consistency - avoid abbreviations |
| `extract/pbd_core/` | `extract/core/` | Redundant prefix - already in extract module |
| `extract/pbd_io/` | `extract/io/` | Redundant prefix |
| `parse/visitors/` | `parse/transformers/` | More accurate - they transform, not just visit |

### 3. Generic Names (Low Priority)

| Current Name | Proposed Name | Reason |
|-------------|---------------|---------|
| `*_coordinator.py` | `coordinator.py` | Since they're already in descriptive directories |
| `parse/base_parser.py` | `parse/parser_base.py` | Noun-first convention |
| `model/utils/base.py` | `model/utils/node_base.py` | More specific about what base it provides |

### 4. Visitor/Transformer Files

| Current Name | Proposed Name | Reason |
|-------------|---------------|---------|
| `parse/visitors/abstract_visitor.py` | `parse/transformers/base.py` | Simpler, clearer |
| `parse/visitors/pb_js_transformer.py` | `parse/transformers/powerbuilder_js.py` | Consistency |
| `parse/visitors/transformer.py` | `parse/transformers/powerbuilder.py` | More specific |
| `parse/visitors/sql_transformer.py` | `parse/transformers/sql.py` | Simpler |

### 5. Parser Files That Need Consolidation

| Current Files | Proposed Single File | Reason |
|-------------|---------------------|---------|
| `parse_coordinator.py::PowerBuilderQueryParser` + `sql_parser.py::PowerBuilderSQLParser` | `parse/parsers/sql.py` | Duplicate SQL parsers |
| `transaction_parser.py::Parser` | `parse/parsers/transaction.py::TransactionParser` | Generic class name |

## Files That Are Named Well ✓

These files have clear, descriptive names and should NOT be changed:

- `extract/core/data_block.py` (already renamed from dat.py)
- `extract/core/cross_reference.py` (already renamed from crossref.py)
- `extract/core/library.py`
- `extract/core/entry.py`
- `extract/core/header.py`
- `extract/core/node.py`
- `decompile/analysis/control_flow_analyzer.py`
- `decompile/core/expression_reconstructor.py`
- `model/entities/pb_application.py`
- `model/entities/pb_function.py`
- All template files (clearly named)

## Implementation Order

### Phase 1: Fix Misleading Names
1. Rename `model/base/exception.py` → `model/ast/exception_handling.py`
2. Delete `model/utils/type_system.py`
3. Rename `parse/grammar.py` → `parse/utils/grammar_loader.py`

### Phase 2: Standardize Naming
1. Rename `pb_preprocessor.py` → `powerbuilder_preprocessor.py`
2. Rename visitor files to transformer pattern
3. Update all imports

### Phase 3: Simplify Structure
1. Remove `pbd_` prefix from directories
2. Rename coordinators to just `coordinator.py`
3. Consolidate parser files

## Git Commands for Renaming

```bash
# Preserve history with git mv
git mv model/base/exception.py model/ast/exception_handling.py
git mv parse/pb_preprocessor.py parse/powerbuilder_preprocessor.py
git mv parse/grammar.py parse/utils/grammar_loader.py
git mv parse/visitors parse/transformers

# Update imports in all Python files
find . -name "*.py" -exec sed -i 's/from model.base.exception/from model.ast.exception_handling/g' {} +
find . -name "*.py" -exec sed -i 's/import model.base.exception/import model.ast.exception_handling/g' {} +
```

## Benefits of Renaming

1. **Clarity**: File names accurately describe contents
2. **Consistency**: Similar files follow similar naming patterns
3. **Discoverability**: Easier to find files by function
4. **Reduced Confusion**: No more misleading names
5. **Professional**: Clean, well-organized codebase