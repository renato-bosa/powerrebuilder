# Pipeline Order Test Report

## Summary

This report analyzes the effectiveness of two different pipeline orders for PowerRebuilder:

1. **Current Order**: Extract → Parse/Decompile (parallel) → Generate
2. **Proposed Order**: Extract → Decompile → Parse → Generate

## Test Results

### Current Pipeline Order (Parse in Parallel with Decompile)

The current pipeline attempts to parse extracted files directly, but encounters issues:

- **Extract Phase**: Successfully extracts .fun files (P-code) from PBD files
- **Parse Phase**: Attempts to parse .fun files directly, which are binary P-code files
- **Result**: Parse fails because .fun files are not PowerBuilder source code

### Proposed Pipeline Order (Decompile First, Then Parse)

Testing the proposed order revealed:

#### 1. Extract → Decompile
- **Input**: .fun files (binary P-code)
- **Output**: .sru files containing opcode listings
- **Issue**: Decompiler produces opcode dumps rather than reconstructed PowerBuilder source

Example decompiler output:
```
userobject n_cst_menu.fun

do while condition
    // 0000: LVALUE_EXPR
    // 0001: RETURN
    // 0002: RETURN
    // ... (raw opcodes)
```

#### 2. Decompile → Parse
- **Input**: Decompiled .sru files (opcode listings)
- **Output**: Parse errors - cannot understand opcode format
- **Result**: Parser expects PowerBuilder syntax, not opcode listings

### Key Findings

1. **File Types from Extraction**:
   - .fun files: Binary P-code (functions/objects)
   - .dwo files: DataWindow objects (SQL-like syntax)
   - .ttf files: Font resources
   - No .sr* source files extracted

2. **Decompiler Limitations**:
   - Currently outputs raw opcodes, not reconstructed source
   - Expression reconstruction consistently fails
   - Not producing parseable PowerBuilder code

3. **Parser Expectations**:
   - Expects valid PowerBuilder syntax
   - Cannot parse binary files (.fun)
   - Cannot parse opcode listings

## Conclusion

**Neither pipeline order works effectively** with the current implementation:

1. **Current Order Fails**: Parser cannot handle binary .fun files
2. **Proposed Order Fails**: Decompiler doesn't produce parseable PowerBuilder source

## Recommendations

1. **Fix the Decompiler**: The decompiler needs to reconstruct actual PowerBuilder source code from opcodes, not just list the opcodes

2. **Separate File Paths**: 
   - Binary files (.fun, .win) → Decompile → Parse → Generate
   - Text files (.dwo, if any .sr* exist) → Parse directly → Generate

3. **Pipeline Should Be**:
   ```
   Extract → Route by file type:
     - Binary (.fun) → Decompile (fixed) → Parse → Generate
     - Text (.dwo, .sr*) → Parse → Generate
   ```

4. **Success Metrics**:
   - Decompiler should produce valid PowerBuilder syntax
   - Parser should successfully create ASTs
   - Generator should produce working Dart/Python code

## Current Success Rate

- **Extract**: ✅ 100% (extracts files successfully)
- **Decompile**: ⚠️ 10% (runs but produces unparseable output)
- **Parse**: ❌ 0% (cannot parse current outputs)
- **Generate**: ❌ 0% (no valid ASTs to generate from)

The pipeline needs significant work on the decompilation phase to produce parseable PowerBuilder source code rather than opcode listings.