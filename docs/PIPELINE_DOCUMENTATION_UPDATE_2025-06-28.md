# Pipeline Architecture Documentation Update - 2025-06-28

## Summary

Comprehensive documentation has been updated throughout the SIME Finch project to clarify that **Parse and Decompile run in PARALLEL**, not sequentially. This prevents the common misconception that led to confusion about the pipeline architecture.

## Documentation Updates Completed

### 1. New Documentation Created

#### `/docs/PIPELINE_ARCHITECTURE.md`
- Comprehensive document explaining the parallel architecture
- Visual diagram showing the pipeline flow
- File type reference tables
- Common misconceptions section
- Performance considerations
- Example showing how both source and P-code are processed

### 2. Existing Documentation Updated

#### `/docs/ARCHITECTURE.md`
- Updated pipeline flow diagram to show parallel paths
- Module structure now indicates stages 2a (Parse) and 2b (Decompile)
- Added notes about parallel execution in module descriptions

#### `/README.md`
- Already correctly shows Pipeline Architecture section
- Shows parallel execution of Parse & Decompile

#### `/docs/TEST_STATUS_REPORT_2025-06-28.md`
- Updated pipeline status to show parallel architecture

### 3. Code Documentation Updated

#### `/main.py`
- Module docstring emphasizes BOTH outputs from Extract
- Parse command clarifies it handles source files ONLY
- Decompile command clarifies it handles P-code files ONLY
- Generate command emphasizes it combines BOTH outputs
- 'all' command explicitly notes parallel execution

#### `/common/pipeline/pipeline_coordinator.py`
- Module docstring explains parallel architecture
- Comments highlight that Parse and Decompile are parallel stages

#### `/extract/extract_coordinator.py`
- Docstring emphasizes extraction of BOTH source AND P-code files

#### `/parse/parse_coordinator.py`
- Docstring clarifies it handles source files ONLY
- Notes it runs in PARALLEL with Decompile

#### `/decompile/decompile_coordinator.py`
- Docstring clarifies it handles P-code files ONLY
- Notes it runs in PARALLEL with Parse

#### `/generate/generate_coordinator.py`
- Docstring emphasizes it COMBINES outputs from both parallel stages

### 4. Test Documentation Updated

#### `/tests/test_integration_pipeline.py`
- Comments clarify the parallel nature of Parse and Decompile

## Key Messages Consistently Documented

1. **Extract outputs BOTH file types**:
   - Source files: .srw, .sru, .srf, .srm, .srs, .sra, .srd
   - P-code files: .fun, .win, .udo, .men, .mef, .apl, .apf

2. **Parse and Decompile run in PARALLEL**:
   - They do NOT depend on each other
   - They process different file types
   - They can run concurrently

3. **Generate combines BOTH outputs**:
   - Takes ASTs from Parse
   - Takes high-level code from Decompile
   - Produces complete applications

## Visual Representation

The following diagram is now consistently used throughout the documentation:

```
PBL/PBD → Extract → ┬→ Parse (source files)    → ┐
                    └→ Decompile (P-code files) → ┴→ Generate → Modern App
```

## Prevention of Future Confusion

With these comprehensive updates:
- Every major module clearly states its role in the parallel architecture
- Visual diagrams reinforce the parallel nature
- Common misconceptions are explicitly addressed
- File type routing is clearly documented

This should prevent any future confusion about the pipeline architecture and ensure all developers understand that Parse and Decompile are parallel stages, not sequential.