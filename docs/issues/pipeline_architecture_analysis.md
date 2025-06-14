# Pipeline Architecture Analysis: Complete Data Flow

## Executive Summary

The current pipeline has a fundamental architectural mismatch between what each stage produces and what the next stage expects. This analysis traces through the actual data flow and identifies all mismatches.

## 1. What Actually Happens When Running "all" Command

When running `python main.py all`, the pipeline executes these stages in order:

1. **Extract** (`extract_pbls`)
2. **Parse** (`parse_powerbuilder_directory`) 
3. **Decompile** (`decompile_directory`)
4. **Generate** (`generate_models`, `generate_services`, `generate_flutter`)

## 2. Stage Input/Output Analysis

### Extract Stage
**Input**: PBD/PBL files (e.g., `input/netpsych/legacy/pbd_files/*.pbd`)
**Process**: Extracts binary content from PowerBuilder library files
**Output**:
- Directory structure: `output/extracted/{pbd_name}/{pbd_name}/`
- File types produced:
  - `.fun` files - Binary P-code (compiled functions)
  - `.str` files - Mixed binary/text (structure definitions with P-code)
  - `.men` files - Mixed binary/text (menu definitions with P-code)
  - `.bin` files - Pure binary data
  - `.apf`, `.apl` files - Application files (binary)
  - `.mef` files - Menu export format (binary)
  - `.ico`, `.bmp`, `.cur` files - Resource files
  - NO `.sru`, `.srw`, `.sra` etc. source files!

**Key Finding**: The extraction stage does NOT produce PowerBuilder source files. It produces binary P-code files that need decompilation.

### Parse Stage
**Input Expected**: PowerBuilder source files (`.sra`, `.srw`, `.sru`, `.srf`, `.srm`, `.srs`, `.srq`, `.srd`)
**Input Received**: Directory with binary files (`.fun`, `.str`, `.men`, etc.)
**Process**: Searches for PowerBuilder source files to parse
**Output**: Nothing - finds 0 files to parse
**Problem**: Parser is looking for source code files that don't exist in the extracted output

### Decompile Stage
**Input Expected**: Originally looking for `.pbd` files in the extracted directory
**Input Received**: Directories containing extracted binary files
**Process**: Should decompile P-code to source
**Output**: Should produce `.pb` files with decompiled source
**Problem**: The decompiler is looking for PBD files but should be looking for `.fun` files

### Generate Stage
**Input Expected**: 
- Parsed AST files from parse stage
- Decompiled function implementations from decompile stage
**Input Received**: 
- Empty parsed directory (parser found nothing)
- Possibly some decompiled files if decompiler worked
**Output**: Generated backend/frontend code
**Problem**: No parsed data to work with

## 3. Root Cause Analysis

### The Fundamental Misunderstanding

The pipeline assumes this flow:
```
PBD → Extract → Source Files → Parse → AST → Generate
                     ↓
                Decompile → Function Implementations
```

But the actual flow should be:
```
PBD → Extract → Binary P-code Files → Decompile → Source Files → Parse → AST → Generate
```

### Why This Happened

1. **Incorrect Assumptions**: The pipeline was designed assuming extraction produces source files
2. **Missing Step**: Decompilation should happen BEFORE parsing, not in parallel
3. **Wrong File Types**: Parser expects `.sru` files but extractor produces `.fun` files

## 4. Correct Pipeline Architecture

### Option 1: Sequential Pipeline (Recommended)
```
1. Extract: PBD → Binary files (.fun, .str, .men)
2. Decompile: Binary files → Source files (.sru, .srw, etc.)
3. Parse: Source files → AST
4. Generate: AST → Modern code
```

### Option 2: Parallel Pipeline (Current but Fixed)
```
1. Extract: PBD → Binary files
2a. Decompile Functions: .fun files → Function implementations
2b. Parse Structures: .str files → Structure definitions  
3. Combine: Merge decompiled functions with parsed structures
4. Generate: Combined data → Modern code
```

## 5. Specific Fixes Required

### Fix 1: Update Decompiler Input
```python
# Current (wrong):
for pbd_file in input_path.rglob('*.pbd'):
    
# Should be:
for fun_file in input_path.rglob('*.fun'):
    # Decompile P-code to source
```

### Fix 2: Update Pipeline Order in main.py
```python
# Extract
extract_pbls(...)

# Decompile BEFORE parse
decompile_directory(extract_output_dir_path, decompile_output_dir_path)

# Parse decompiled output, not extracted output
parse_powerbuilder_directory(decompile_output_dir_path, parse_output_dir_path)
```

### Fix 3: Update Decompiler to Handle All File Types
- `.fun` files → Function source code
- `.str` files → Structure definitions (may need special handling)
- `.men` files → Menu definitions (may need special handling)

### Fix 4: DataWindow Generation
DataWindow objects (`.dwo` files) are being extracted but not processed correctly:
- Extract stage tries to extract DataWindow SQL but often fails
- Need dedicated DataWindow processing in the pipeline
- Should generate DataWindow definitions for the frontend

## 6. Why Parser Finds 0 Files

The parser finds 0 files because:
1. It's looking for `.sru`, `.srw`, etc. files
2. The extracted directory only contains `.fun`, `.str`, `.men` files
3. These binary files need decompilation first to produce source files

## 7. Why Decompiler Gets Directories

The decompiler expects to find `.pbd` files but:
1. The extracted output has already processed PBD files
2. It should be looking for the extracted binary files (`.fun`, etc.)
3. The current logic tries to re-process already extracted PBDs

## 8. Recommended Immediate Actions

1. **Fix Pipeline Order**: Run decompile before parse
2. **Fix Decompiler Input**: Look for `.fun` files, not `.pbd` files
3. **Fix Parser Input**: Point to decompiled output, not extracted output
4. **Add Logging**: Add debug logging to show what files each stage finds
5. **Create Integration Test**: Test the full pipeline with a small PBD file

## 9. Long-term Improvements

1. **Unified Extraction/Decompilation**: Combine extract and decompile into one stage
2. **Streaming Pipeline**: Process files as they're extracted rather than in batches
3. **Better Error Handling**: Gracefully handle partially corrupted files
4. **Progress Tracking**: Show clear progress through the entire pipeline
5. **Validation**: Validate output at each stage before proceeding

## Conclusion

The pipeline architecture is fundamentally sound but has a critical ordering issue. The decompiler needs to run on the extracted binary files to produce source code before the parser can work. This explains why the parser finds 0 files and why the decompiler is looking in the wrong place. The fixes are straightforward once the data flow is understood correctly.