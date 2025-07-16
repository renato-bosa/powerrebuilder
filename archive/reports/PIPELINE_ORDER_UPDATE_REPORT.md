# Pipeline Order Documentation Update Report

## Date: 2025-07-14

## Summary

All documentation has been updated to reflect the correct SEQUENTIAL pipeline order where Decompile MUST run before Parse. This corrects previous documentation that incorrectly stated they ran in parallel.

## Correct Pipeline Order

1. **Extract** → Extracts .fun files (P-code) from PBL/PBD
2. **Decompile** → Converts .fun to .sru (PowerBuilder source)
3. **Parse** → Converts .sru to AST JSON
4. **Model** → Converts AST to semantic models
5. **Generate** → Produces Python/Dart from models

## Files Updated

### 1. README.md
- **Changed**: Pipeline Architecture section from parallel to sequential
- **Updated**: Command examples to show correct execution order
- **Added**: Emphasis that Decompile must complete before Parse

### 2. docs/ARCHITECTURE.md
- **Changed**: System architecture diagram to show 5 sequential stages
- **Reordered**: Module descriptions (Decompile before Parse)
- **Added**: Model module section
- **Updated**: Stage descriptions to reflect sequential flow

### 3. docs/DATA_FLOW.md
- **Replaced**: Parallel flow diagram with sequential flow diagram
- **Corrected**: All stage descriptions to show proper order
- **Updated**: Performance section from "Parallelization" to "Sequential Processing"
- **Fixed**: Input/output descriptions for each stage

### 4. docs/PIPELINE_ARCHITECTURE.md
- **Complete rewrite**: Now explains sequential architecture
- **Added**: "Common Misconceptions (CORRECTED)" section
- **Added**: Clear explanation of why order matters
- **Updated**: All examples and code snippets

### 5. CLAUDE.md
- **Updated**: CLI commands section with correct order
- **Added**: "Pipeline Order (CRITICAL)" section
- **Emphasized**: Parse requires .sru files from Decompile

### 6. docs/QUICK_REFERENCE.md
- **Added**: "Pipeline Overview" section at the top
- **Emphasized**: Sequential nature of pipeline
- **Added**: Warning about Decompile before Parse

### 7. main.py
- **Updated**: Module docstring to show sequential 5-stage process
- **Corrected**: Stage descriptions
- **Added**: Emphasis on dependencies between stages

### 8. Coordinator Files
- **src/common/pipeline/pipeline_coordinator.py**: Already had correct sequential documentation
- **src/parse/coordinator.py**: Updated to show it runs AFTER Decompile
- **src/decompile/coordinator.py**: Updated to show it runs BEFORE Parse
- **src/generate/coordinator.py**: Updated to show full sequential pipeline
- **src/extract/coordinator.py**: Updated to show it produces .fun files for Decompile

## Key Changes Made

### 1. Corrected Misconceptions
- **OLD**: "Parse and Decompile run in parallel"
- **NEW**: "Decompile must complete before Parse begins"

### 2. File Flow Clarification
- **Extract** outputs .fun files (P-code)
- **Decompile** converts .fun to .sru (source)
- **Parse** processes .sru to create AST
- **Model** builds semantic models from AST
- **Generate** creates modern code from models

### 3. Rationale Documented
- Parse uses a grammar-based parser that requires PowerBuilder source syntax
- Decompile reconstructs source code from bytecode
- This creates a hard dependency: Parse cannot process P-code directly

## Diagrams Updated

### Old (Incorrect):
```
Extract → ┬→ Parse (source files)    → ┐
          └→ Decompile (P-code files) → ┴→ Generate
```

### New (Correct):
```
Extract → Decompile → Parse → Model → Generate
(.fun)    (.sru)     (AST)   (models) (code)
```

## Impact

1. **Simpler Architecture**: No complex synchronization needed
2. **Clear Dependencies**: Each stage has well-defined inputs/outputs
3. **Easier Debugging**: Linear flow makes issues easier to trace
4. **Better Documentation**: Prevents future confusion about pipeline order

## Additional Documentation Created

- **docs/PIPELINE_DOCUMENTATION_UPDATE_2025-07-14.md**: Comprehensive update summary
- **This report**: Detailed list of all changes made

## Verification

All documentation now consistently shows:
- Extract produces .fun files
- Decompile converts .fun to .sru
- Parse requires .sru files from Decompile
- Model processes AST from Parse
- Generate uses models from Model stage

The sequential nature is emphasized throughout, preventing future confusion about the pipeline architecture.