# Pipeline Execution Report

## Test File: dcm_email.pbd

### Pipeline Command
```bash
uv run python main.py all --pbl-input-dir data/pipeline_test_input --base-output-dir data/test_pipeline_output --debug --enable-byte-recovery
```

### Pipeline Stages Summary

#### 1. Extraction Stage ✅ PARTIAL SUCCESS
- **Input**: 1 PBD file (dcm_email.pbd - 38,400 bytes)
- **Expected**: 2780 entries
- **Actual**: 4 entries extracted
- **Success Rate**: 0.14% (4/2780)
- **Output Files**:
  - n_cst_email.fun (5,937 bytes)
  - n_cst_mailsession.fun (2,299 bytes)
  - n_cst_pdfwriter.fun (8,521 bytes)
  - w_mail_test.fun (15,767 bytes)
- **Issues**:
  - Only extracted 4 out of 2780 expected entries
  - Multiple resource extraction failures (fonts, icons, cursors)
  - ResourceCatalog missing required methods

#### 2. Parsing Stage ❌ NO OUTPUT
- **Input**: 0 source files found (only P-code was extracted)
- **Output**: Empty parsed_summary.json
- **Success Rate**: N/A - No source files to parse
- **Issue**: Extract stage only produced P-code files, not source files

#### 3. Decompiling Stage ✅ SUCCESS
- **Input**: 4 P-code files (.fun)
- **Output**: 4 decompiled source files (.sru)
  - n_cst_email.sru (102,106 bytes)
  - n_cst_mailsession.sru (36,808 bytes)
  - n_cst_pdfwriter.sru (151,048 bytes)
  - w_mail_test.sru (251 bytes)
- **Success Rate**: 100% (4/4)
- **Issues**: 
  - Expression reconstruction failures
  - Output contains raw opcodes instead of reconstructed code

#### 4. Model Conversion Stage ❌ NO OUTPUT
- **Input**: 0 parsed AST files
- **Output**: 0 models created
- **Success Rate**: 0%
- **Issue**: No AST files from parsing stage

#### 5. Generation Stage ❌ NO OUTPUT
- **Input**: No models or parsed data
- **Output**:
  - 0 models generated
  - 0 services generated
  - 0 Flutter screens generated
  - 0 DataWindows generated
- **Success Rate**: 0%
- **Issue**: No input data from model conversion

### Overall Pipeline Status: ❌ FAILED

### Key Issues Identified

1. **Extraction Problems**:
   - Only 0.14% of entries successfully extracted
   - Resource extraction completely failing
   - Missing methods in ResourceCatalog class

2. **Pipeline Flow Problem**:
   - Parse and Decompile run in parallel, but Generate expects Parse output
   - Decompiled files aren't being fed into the generation pipeline
   - No mechanism to parse decompiled .sru files and generate from them

3. **Missing Integration**:
   - Decompiled output not connected to generation stage
   - Parser can't handle decompiled output format (raw opcodes)

### Recommendations

1. Fix the extraction stage to extract more entries
2. Implement proper expression reconstruction in decompiler
3. Create a pathway for decompiled files to be parsed and fed into generation
4. Fix ResourceCatalog implementation
5. Add better error handling and recovery mechanisms

### Pipeline Execution Time: 2.11 seconds

### Files Generated: 
- 4 P-code files extracted
- 4 decompiled source files created
- 0 modern code files generated