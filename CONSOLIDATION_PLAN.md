# PowerBuilder Decompiler Consolidation Plan

## Executive Summary
This consolidation plan identifies opportunities to reduce the codebase by approximately 35-40% through elimination of duplicates, merging of similar functionality, and reorganization of scattered components. The plan is organized by priority and impact.

## Priority 1: High Impact Consolidations (Immediate)

### 1.1 Expression System Consolidation

**Current State:**
- model/ast/expressions.py
- model/entities/expressions.py
- decompile/core/expression_reconstructor.py
- decompile/core/advanced_expression_reconstructor.py

**Action:**
```bash
# Create unified expression module
mkdir -p model/expressions
# Merge all expression definitions into:
model/expressions/
├── __init__.py
├── ast_expressions.py      # AST expression nodes
├── evaluator.py           # Expression evaluation logic
└── reconstructor.py       # Unified expression reconstruction
```

**Benefits:** Eliminate duplicate Expression classes, unified reconstruction logic

### 1.2 Test File Consolidation

**Merge these test groups:**

```bash
# Advanced decompile tests (3 → 1)
tests/test_decompile/test_advanced_decompile.py  # Keep as base
tests/test_decompile/test_advanced_decompile_concise.py  # Merge into base
tests/test_decompile/test_advanced_decompile_simple.py   # Merge into base

# PBD extraction tests (2 → 1)
tests/test_extract/test_pbd_extraction.py        # Keep as base
tests/test_extract/test_pbd_extraction_simple.py # Merge into base

# P-code detector tests (2 → 1)
tests/test_decompile/test_pcode_detector.py          # Keep as base
tests/test_decompile/test_pcode_detector_enhanced.py # Merge into base

# Simple formatter tests (3 → 2)
tests/test_decompile/test_simple_formatter.py          # Keep
tests/test_decompile/test_simple_formatter_debug.py    # Merge into enhanced
tests/test_decompile/test_simple_formatter_enhanced.py # Keep
```

**Benefits:** Reduce test files from 10 to 5, eliminate duplicate test cases

### 1.3 Documentation Consolidation

**Action:**
```bash
# Consolidate 100% accuracy documentation (5 → 2)
docs/100_percent_accuracy_plan_complete.md     # Merge plan + executive + implementation
docs/100_percent_accuracy_results.md           # Merge final + progress

# Archive old status reports
mv docs/PROJECT_STATUS_REPORT_2025-06-20.md docs/archive/

# Remove duplicate architecture docs
rm docs/archive/architecture-mermaid.md  # Content already in ARCHITECTURE.md
rm docs/archive/pipeline_architecture.md # Outdated, keep PIPELINE_ARCHITECTURE.md
```

**Benefits:** Reduce documentation files by 40%, clearer documentation structure

## Priority 2: Medium Impact Consolidations

### 2.1 Debug Tools Consolidation

**Keep these 7 tools:**
```bash
tools/debug/
├── pcode_extractor.py              # Unified P-code tool
├── debug_pcode_pipeline.py         # Pipeline debugger
├── deep_pcode_analysis.py          # Executable analysis
├── analyze_real_fun_files.py       # Function analyzer
├── test_context_aware_decoder.py   # Decoder tests
├── final_decoder_summary.py        # Documentation
└── test_object_parser.py           # Object parser tests
```

**Remove these 13 tools:**
- analyze_pcode_patterns.py, analyze_pcode_structure.py, extract_pcode_from_fun.py
- debug_pcode_detection_detailed.py, debug_pcode_extraction.py, debug_pcode_final.py
- debug_pcode_simple.py, analyze_fun_simple.py, analyze_fun_structure.py
- analyze_real_fun.py, debug_decoder.py, test_decoder_improvements.py
- test_object_parser_simple.py

**Create new consolidated tool:**
```bash
tools/debug/pcode_file_analyzer.py  # Merge pattern/structure analysis
```

**Benefits:** Reduce debug tools from 20 to 8 scripts

### 2.2 Grammar File Deduplication

**Immediate fixes:**
```python
# In each grammar file, add at top:
%import common_grammar.HEX_INT
%import common_grammar.DATE_LIT
%import common_grammar.TIME_LIT
%import common_grammar.STRING
%import common_grammar.ESCAPED_STRING
%import common_grammar.COMMENT
%import common_grammar.LPAR
%import common_grammar.RPAR
# ... etc for all common tokens

# Remove all duplicate token definitions
```

**Long-term structure:**
```bash
parse/grammar/
├── common/
│   ├── tokens.lark       # All shared tokens
│   ├── expressions.lark  # Expression rules
│   └── control_flow.lark # Control structures
├── powerbuilder.lark     # Main grammar (merge type_extensions.lark)
├── datawindow.lark       # DataWindow-specific
├── sql.lark              # SQL grammar
└── pseudocode.lark       # Pseudocode grammar
```

**Benefits:** Eliminate 80% of token duplication, cleaner grammar structure

### 2.3 Model Node Test Consolidation

**Current:** 40+ individual test_pb_*.py files in tests/test_model/

**Action:**
```python
# Create consolidated test suites
tests/test_model/
├── test_ast_nodes_suite.py       # All AST node tests
├── test_expression_nodes.py      # Expression-specific tests
├── test_statement_nodes.py       # Statement node tests
├── test_declaration_nodes.py     # Declaration node tests
└── test_specialized_nodes.py     # Special node types
```

**Benefits:** Reduce from 40+ files to 5 comprehensive test suites

## Priority 3: Low Impact Consolidations

### 3.1 Extract Utilities Consolidation

**Action:**
```python
# Create common extraction utilities
common/extraction_utils.py  # Shared extraction patterns

# Document extraction layers
docs/EXTRACTION_ARCHITECTURE.md
- Binary extraction (extract/pbd/)
- Syntax extraction (decompile/extractors/)
- Format-specific (decompile/pdw/)
```

### 3.2 Exact Duplicate Removal

**Remove these exact duplicates:**
```bash
# Empty __init__.py files can share a single version
# Configuration test duplicates
tests/test_app/conftest.py  # Keep one
tests/test_model/conftest.py # Remove, use shared

# Reference duplicates (keep latest versions only)
# Remove older PowerBuilder example versions
```

## Implementation Strategy

### Phase 1 (Week 1): High Priority Items
1. Create consolidation branch
2. Consolidate expression system
3. Merge test files
4. Clean up documentation

### Phase 2 (Week 2): Medium Priority Items
1. Consolidate debug tools
2. Fix grammar file imports
3. Consolidate model tests

### Phase 3 (Week 3): Low Priority & Testing
1. Create extraction utilities
2. Remove exact duplicates
3. Run full test suite
4. Update all imports

## Validation Checklist

- [ ] All tests pass after each consolidation
- [ ] No circular imports introduced
- [ ] Documentation updated for new structure
- [ ] Import statements updated project-wide
- [ ] Coverage remains at or above current levels
- [ ] Performance benchmarks show no regression

## Expected Outcomes

1. **File Count Reduction:**
   - Documentation: 40% fewer files
   - Tests: 35% fewer files
   - Debug tools: 60% fewer files
   - Overall: 35-40% reduction

2. **Code Quality Improvements:**
   - Clearer module boundaries
   - Eliminated duplicate functionality
   - Better organized test suites
   - Reduced maintenance burden

3. **Developer Experience:**
   - Easier to find functionality
   - Less confusion about which module to use
   - Clearer architecture
   - Faster test execution

## Risk Mitigation

1. **Backup Strategy:** Create comprehensive backup before starting
2. **Incremental Approach:** Consolidate one module at a time
3. **Testing:** Run tests after each consolidation step
4. **Rollback Plan:** Keep consolidation branch separate until validated
5. **Documentation:** Update docs immediately after each change

## Success Metrics

- Total file count reduced by 35-40%
- Test execution time reduced by 20%
- Zero functionality loss
- All tests passing
- Improved code coverage

---

**Note:** This plan should be executed incrementally with careful testing at each step. Create a `CONSOLIDATION_LOG.md` to track progress and any issues encountered.