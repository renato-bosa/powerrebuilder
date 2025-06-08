# P-code Debug Script Analysis

## Overview
This document analyzes all P-code debug scripts in `/scripts/debug/` and provides recommendations for consolidation.

## Script Summaries

### 1. **test_real_pcode.py**
- **Purpose**: Tests P-code extraction from real PBD files using the Library API
- **Key Features**:
  - Extracts P-code from PBD entries (especially .fun files)
  - Uses PCodeDetector to find P-code sections
  - Performs opcode frequency analysis
  - Saves extracted P-code to output files
- **Dependencies**: extract.pbd_core.library, decompile.opcodes, decompile.analysis.pcode_detector

### 2. **test_real_pcode_simple.py**
- **Purpose**: Simplified version of test_real_pcode.py with basic P-code detection
- **Key Features**:
  - Simple heuristic-based P-code detection (looks for low byte patterns)
  - Extracts from multiple object types (.fun, .srf, .udo, .win)
  - Basic opcode frequency analysis
  - Pattern search for specific sequences
- **Dependencies**: extract.pbd_core.library, decompile.opcodes

### 3. **debug_pcode_extraction.py**
- **Purpose**: Debug why .fun files are not being created during extraction
- **Key Features**:
  - Full PBD parsing and entry analysis
  - Detailed logging of P-code detection logic
  - Tests actual extraction process
  - Saves raw data for P-code candidates
- **Dependencies**: extract.pbd_core.core, extract.pbd_core.entry

### 4. **debug_pcode_extraction_simple.py**
- **Purpose**: Low-level PBD analysis without full imports
- **Key Features**:
  - Direct binary parsing of PBD structure
  - Manual ENT* block detection
  - String extraction and pattern matching
  - No dependencies on project modules

### 5. **debug_pcode_detection_detailed.py**
- **Purpose**: Detailed analysis of P-code detection logic with Unicode support
- **Key Features**:
  - Handles both ANSI and Unicode PBD formats
  - Precise ENT* structure parsing
  - Explains why entries are/aren't detected as P-code
  - Shows exact detection criteria

### 6. **debug_pcode_final.py**
- **Purpose**: Final verification using actual extraction logic
- **Key Features**:
  - Uses real extraction functions (extract_pbl_header, extract_nods)
  - Analyzes NOD structures
  - Verifies P-code detection for source files
- **Dependencies**: extract.pbd_core modules

### 7. **analyze_pcode_patterns.py**
- **Purpose**: Statistical analysis of P-code patterns
- **Key Features**:
  - Byte frequency analysis
  - 2-byte sequence detection
  - String location detection (UTF-16)
  - Instruction pattern recognition
  - Verified opcode reference

### 8. **parse_pcode_text.py**
- **Purpose**: Parse text-format P-code files
- **Key Features**:
  - Parses human-readable P-code format
  - Extracts instruction sequences
  - Opcode frequency counting
  - Pattern analysis (functions, jumps, data ops)
  - Attempts to create opcode mappings

### 9. **test_corrected_decompiler.py**
- **Purpose**: Full decompilation pipeline test
- **Key Features**:
  - Tests complete decompilation process
  - Uses PCodeDecoder, ControlFlowAnalyzer, ExpressionReconstructor
  - Generates decompiled source code
  - Stack balance verification
- **Dependencies**: decompile.core modules

### 10. **test_simple_decompile.py**
- **Purpose**: Simple opcode analysis with corrected opcode table
- **Key Features**:
  - Basic instruction decoding
  - Operand handling (byte, string)
  - Pattern analysis (STORE, CONST, arithmetic)
  - Unknown opcode tracking

### 11. **debug_pbd_entries_summary.py**
- **Purpose**: Quick PBD file summary
- **Key Features**:
  - Shows all entries in a PBD
  - Extension-based summary
  - Identifies source files needing P-code
  - Uses hardcoded offsets for specific PBDs

### 12. **test_fun_file_creation.py**
- **Purpose**: Verify .fun file creation during extraction
- **Key Features**:
  - Uses extract_coordinator API
  - Temporary directory testing
  - Comprehensive file listing
  - Success/failure reporting

### 13. **analyze_real_fun.py**
- **Purpose**: Analyze existing .fun files
- **Key Features**:
  - Hex dump visualization
  - Byte frequency with opcode names
  - P-code start detection
  - Pattern-specific searches

## Overlapping Functionality

### Group 1: Real P-code Extraction Testing
- `test_real_pcode.py` and `test_real_pcode_simple.py`
- Both extract P-code from PBD files and analyze opcodes
- Simple version has fewer dependencies

### Group 2: P-code Detection Debugging
- `debug_pcode_extraction.py`, `debug_pcode_extraction_simple.py`, `debug_pcode_detection_detailed.py`, `debug_pcode_final.py`
- All focus on understanding why .fun files aren't created
- Each provides different levels of detail and approaches

### Group 3: Decompilation Testing
- `test_corrected_decompiler.py` and `test_simple_decompile.py`
- Both test opcode decoding with the corrected opcode table
- Corrected version tests full pipeline, simple version just decodes

### Group 4: P-code Analysis
- `analyze_pcode_patterns.py` and `analyze_real_fun.py`
- Both analyze P-code byte patterns and frequencies
- Pattern analyzer works on raw P-code, fun analyzer on .fun files

## Consolidation Recommendations

### 1. **Unified P-code Extractor Tool** (`pcode_extractor.py`)
Combine functionality from:
- `test_real_pcode.py`
- `test_real_pcode_simple.py`
- `debug_pcode_extraction.py`
- `test_fun_file_creation.py`

Features:
- Extract P-code from PBD files
- Support multiple detection methods
- Save extracted P-code
- Verify .fun file creation
- Detailed logging options

### 2. **PBD Analysis Tool** (`pbd_analyzer.py`)
Combine functionality from:
- `debug_pcode_extraction_simple.py`
- `debug_pcode_detection_detailed.py`
- `debug_pbd_entries_summary.py`
- `debug_pcode_final.py`

Features:
- Low-level PBD structure analysis
- Unicode/ANSI format detection
- Entry enumeration and classification
- P-code detection logic explanation
- No dependencies on project modules (standalone)

### 3. **P-code Pattern Analyzer** (`pcode_pattern_analyzer.py`)
Combine functionality from:
- `analyze_pcode_patterns.py`
- `analyze_real_fun.py`
- `parse_pcode_text.py`

Features:
- Byte frequency analysis
- Pattern detection (strings, instructions, sequences)
- Support for binary and text P-code formats
- Opcode mapping discovery
- Statistical analysis

### 4. **Decompiler Test Suite** (`test_decompiler.py`)
Combine functionality from:
- `test_corrected_decompiler.py`
- `test_simple_decompile.py`

Features:
- Simple decoding tests
- Full pipeline tests
- Stack balance verification
- Unknown opcode reporting
- Performance metrics

### 5. **Scripts to Remove**
The following scripts have limited unique functionality and can be removed after consolidation:
- `debug_entry_33.py` (specific entry debugging)
- `debug_first_opcode.py` (too specific)
- `debug_nod_size.py` (NOD structure debugging)

## Implementation Priority

1. **High Priority**: Create `pbd_analyzer.py` first - this will be the most useful for understanding PBD structure
2. **Medium Priority**: Create `pcode_pattern_analyzer.py` - essential for opcode discovery
3. **Medium Priority**: Create `pcode_extractor.py` - consolidates extraction functionality
4. **Low Priority**: Create `test_decompiler.py` - can wait until decompiler is more mature

## Benefits of Consolidation

1. **Reduced Redundancy**: Eliminate duplicate code across scripts
2. **Better Maintenance**: Fewer files to update when APIs change
3. **Improved Usability**: Clear tool purposes with comprehensive features
4. **Modular Design**: Each tool focuses on a specific aspect of P-code analysis
5. **Dependency Management**: Standalone tools where possible, clear dependencies otherwise