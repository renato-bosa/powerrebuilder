# PowerBuilder Decompilation System Analysis

## Current Decompilation Capabilities

### 1. **Supported Object Types for Decompilation**

Based on `decompile/decompile_coordinator.py` and `common/object_type_detector.py`, the system currently supports decompiling:

#### **Objects with P-code (Can be decompiled):**
- **Functions** (.fun) - Contains P-code
- **Windows** (.win) - Contains P-code  
- **User Objects** (.udo/.sru) - Contains P-code
- **Menus** (.men/.mef/.srm) - Contains P-code
- **Applications** (.apl/.apf/.sra) - Contains P-code

#### **Data-only Objects (Cannot be decompiled, only extracted):**
- **Structures** (.str/.srs) - Type definitions only
- **DataWindows** (.dwo/.srd) - SQL and layout definitions
- **Queries** (.srq) - SQL definitions
- **Pipelines** (.pip/.srp) - Pipeline definitions
- **Projects** (.srj) - Project configuration
- **Proxy Objects** (.prx) - Proxy definitions

### 2. **Comprehensive P-code Opcode Support**

The system has extensive opcode support in `decompile/opcodes/opcodes.py`:

- **Total opcodes defined:** 582 opcodes (0x00 - 0x246)
- **Version support:** PowerBuilder 6.0 through 12.0+
- Includes support for:
  - Control flow (JUMP, JUMPTRUE, JUMPFALSE, RETURN)
  - Database operations (DBSELECT, DBUPDATE, DBINSERT, etc.)
  - Variable operations (PUSH, POP, ASSIGN)
  - Type conversions (CNV_INT_TO_*, etc.)
  - Arithmetic operations (ADD, SUB, MULT, DIV)
  - Comparison operations (EQ, NE, GT, LT, GE, LE)
  - Object operations (DOT, INDEX, CREATE)
  - Advanced types (LONGLONG, BYTE - added in PB 8.0+)

### 3. **Decompilation Pipeline Components**

The system has a complete decompilation pipeline:

1. **P-code Detection** (`analysis/pcode_detector.py`, `analysis/pcode_detector_enhanced.py`)
   - EnhancedPCodeDetector for finding P-code sections

2. **Object Parsing** (`analysis/object_parser.py`)
   - Parses PowerBuilder object structure
   - Extracts P-code data

3. **P-code Decoding** (`core/pcode_decoder.py`)
   - Version-aware decoder
   - Handles instruction decoding with operands

4. **Control Flow Analysis** (`analysis/control_flow_analyzer.py`)
   - Analyzes control flow structures

5. **Expression Reconstruction** 
   - Basic: `core/expression_reconstructor.py`
   - Advanced: `core/advanced_expression_reconstructor.py`

6. **Output Generation**
   - Formatter: `core/output_formatter.py`
   - Validator: `core/output_validator.py`
   - Post-processor: `core/post_processor.py`

### 4. **Special Handling**

#### DataWindows:
- Multiple extractors for different DataWindow formats:
  - `analysis/datawindow_extractor.py`
  - `analysis/enhanced_datawindow_extractor.py`
  - `analysis/pdw_sql_extractor.py`
  - `analysis/pdw_comprehensive_extractor.py`

### 5. **What's Actually Missing**

Based on the analysis, the decompilation system appears to be **quite comprehensive**. The main limitations seem to be:

1. **Implementation gaps** rather than missing features:
   - Some object types might not be fully integrated into the extraction/decompilation flow
   - The reference implementation in `reference/decompilers/powerbuilder-decompile/pbd/definitions.py` shows additional object type mappings that may not all be handled

2. **Object types that might need attention:**
   - Type code mappings show additional types like:
     - Type 93 (.xxy) - Unknown type
     - Type 33 - Pipeline (mentioned but implementation unclear)
     - Type 36 - Project 
     - Type 44 - Proxy
     - Type 77 - Query

3. **Potential unused features:**
   - The system has extensive opcode support but it's unclear if all opcodes are properly handled in expression reconstruction
   - Advanced control flow patterns might not be fully reconstructed

### 6. **Recommendations**

1. **Verify extraction coverage**: Ensure all object types from PBD files are being extracted, not just the common ones

2. **Test comprehensive decompilation**: The infrastructure exists, but may need:
   - Better integration between extraction and decompilation
   - Handling of edge cases and less common object types

3. **Check for silent failures**: Some objects might be skipped without proper error reporting

4. **Utilize existing infrastructure**: The system has sophisticated components that may not be fully utilized