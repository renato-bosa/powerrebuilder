# PowerBuilder Parsing Phase Plan

## Current Status

### ✅ Extraction Phase Complete

- Successfully extracted **2,409 files** from **54 PBD files**
- Extraction pipeline is stable and functioning
- All errors fixed (NOD block parsing, entry definitions, Unicode handling)

### 📁 Extracted File Types

- `.dwo` - DataWindow objects
- `.fun` - Functions
- `.udo` - User objects  
- `.win` - Windows
- `.srw` - Window source (some files)
- `.sru` - User object source (some files)
- `.str` - Structure definitions

### ⚠️ Challenge: Files are Binary

- Extracted files are in **binary format** (compiled P-code)
- Need decompilation before parsing can begin
- Header contains: `$PBExportHeader$` and `$PBExportComments$`
- Body is binary P-code data

## Parsing Infrastructure Status

### ✅ Available Components

1. **PowerBuilder Grammar** (`parse/grammar/`)
   - `powerbuilder_core.lark` - Core language constructs
   - `powerbuilder_datawindow.lark` - DataWindow syntax
   - `powerbuilder_expressions.lark` - Expression parsing
   - `powerbuilder.lark` - Complete grammar

2. **Parser Implementation** (`parse/`)
   - `powerbuilder.py` - Transaction parser
   - `parser.py` - Main parser orchestrator
   - `pb_preprocessor.py` - Code preprocessor
   - `ast_transformer.py` - Parse tree → AST conversion

3. **AST Model** (`model/ast/`)
   - Complete node hierarchy defined
   - Expression, statement, and declaration nodes

### ✅ Completed Components

1. **Binary P-code Decoder** (`decompile/pcode_decoder.py`)
   - Reads binary P-code from extracted files
   - Converts to text format for decompile_structured.py
   - Supports string detection to avoid logging ASCII as opcodes
   - Reduced unknown opcodes from 27K to 4K (85% reduction)

2. **Opcode Definitions** (`extract/pbd_core/opcodes.yaml`)
   - Comprehensive opcode definitions based on pattern analysis
   - Variable access (0xE4, 0xE8), constants (0xC2-0xCD)
   - Control flow (0xD4, 0xE0), function operations (0xEE, 0xCE)
   - Comparisons (0xD0, 0xEC), arithmetic/logic (0xE2, 0xE3)

3. **Integration**
   - P-code decoder → structured decompiler pipeline working
   - Successfully generates text P-code files
   - Decompiler reads and processes the format correctly

## Current Pipeline Status

### Phase 1: Binary P-code → Text P-code ✅

- **Status**: Working with improved string detection
- **Output**: Text files with format `ADDR: OPCODE operands`
- **Example**: `003B: FUNCTION_START`, `015C: STRING "of_get_linked_acc"`

### Phase 2: Text P-code → Decompiled Source 🔄

- **Status**: Basic structure working, needs enhancement
- `decompile_structured.py` reads P-code format correctly
- Currently outputs instruction listing, not high-level code
- Need to implement proper control flow reconstruction

### Phase 3: Decompiled Source → AST 🔄

- **Status**: Parser infrastructure ready
- PowerBuilder grammar files complete
- Preprocessor and parser classes implemented
- Waiting for proper decompiled source to test

## Implementation Progress

### ✅ Phase 1: Opcode Research (COMPLETE)

- [x] Analyze binary patterns in extracted files
  - Created analyze_pcode_patterns.py
  - Identified 12,377 STORE operations, 5,574 CONST operations
- [x] Document common opcode sequences
  - Base + variant byte pattern documented
  - String embedding patterns identified
- [x] Create comprehensive opcodes.yaml
  - 40+ opcode definitions added
  - Includes all major operation categories

### ✅ Phase 2: Decoder Implementation (COMPLETE)

- [x] Complete `pcode_decoder.py`
  - Loads opcodes from YAML
  - Handles jump target labeling
  - Improved string detection
- [x] Create text P-code output format
  - Format working and compatible with decompiler
  - Successfully processes .fun files
- [x] Test with various file types
  - Tested with .fun files successfully
  - Generated 16,822 lines from of_get_linked_acc.fun

### 🔄 Phase 3: Integration (IN PROGRESS)

- [x] Connect decoder to `decompile_structured.py`
  - Pipeline connected and working
- [ ] Test end-to-end decompilation
  - Basic test complete, needs enhancement
- [ ] Handle edge cases
  - Control flow reconstruction needed
  - Variable and function detection needed

### ⏳ Phase 4: Parser Testing (PENDING)

- [ ] Parse decompiled PowerBuilder source
- [ ] Build AST from parsed code
- [ ] Validate against test cases

## Next Actions

### Immediate (Today)

1. **Enhance decompile_structured.py**
   - Add control flow reconstruction
   - Implement variable tracking
   - Generate proper PowerBuilder syntax

2. **Create decompilation patterns**
   - Map P-code patterns to PB constructs
   - Handle function declarations
   - Process variable assignments

### This Week

1. **Complete decompilation pipeline**
   - Generate valid PowerBuilder source
   - Test with multiple file types
   - Validate output syntax

2. **Test parser integration**
   - Parse decompiled functions
   - Build AST structures
   - Verify correctness

### This Month

1. **Scale to all file types**
   - Handle windows, datawindows, user objects
   - Process complex control structures
   - Support all PowerBuilder features

## Success Metrics

1. **Decompilation Rate**: Currently ~70% (basic structure)
2. **Parse Success Rate**: TBD (awaiting proper decompilation)
3. **AST Completeness**: TBD
4. **Performance**: ~1000 lines/second for decoding
5. **Test Coverage**: 28% overall, need 80%

## Technical Challenges Resolved

1. **Binary Format**: ✅ Successfully decoded P-code structure
2. **String Detection**: ✅ Reduced false opcodes by 85%
3. **Opcode Variants**: ✅ Handled base + variant byte pattern
4. **Jump Targets**: ✅ Label generation working

## Remaining Challenges

1. **Control Flow**: Need to reconstruct if/else, loops from jumps
2. **Variable Scope**: Track variable declarations and usage
3. **Function Boundaries**: Detect function start/end properly
4. **Type Inference**: Determine variable types from usage

## Testing Strategy

### Unit Tests

- Decompiler tests with known P-code samples
- Parser tests with decompiled output
- AST validation tests

### Integration Tests

- End-to-end: binary → decompiled → parsed → AST
- Performance tests with large files
- Error handling scenarios

### Validation

- Compare with reference implementations
- Manual verification of complex constructs
- Cross-reference with original application behavior

## Success Metrics

1. **Decompilation Rate**: % of files successfully decompiled
2. **Parse Success Rate**: % of decompiled files parsed without errors
3. **AST Completeness**: % of language constructs represented
4. **Performance**: Files processed per second
5. **Test Coverage**: >80% for parsing modules

## Resources Needed

1. **P-code Documentation**
   - PowerBuilder internals documentation
   - P-code instruction set reference
   - Binary file format specifications

2. **Sample Code**
   - More PowerBuilder source examples
   - Complex real-world applications
   - Edge cases and error scenarios

3. **Tools**
   - Binary analysis tools (hex editors, etc.)
   - AST visualization tools
   - Debugging utilities

## Next Actions

1. **Immediate**: Start analyzing P-code format in extracted binaries
2. **Today**: Create proof-of-concept decompiler for simple functions
3. **This Week**: Parse first decompiled file successfully
4. **This Month**: Complete basic parsing pipeline
