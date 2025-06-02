# SIME Finch Project Structure Overview

## Core Directories

### 1. **extract/** - PBD/PBL File Extraction
Handles the extraction of PowerBuilder compiled files (PBD/PBL) into analyzable components.

- **pbd_core/** - Core extraction logic
  - `core.py` - Main extraction engine
  - `entry.py` - PBD entry handling
  - `header.py` - PBD header parsing
  - `library.py` - Library management
  - `node.py` - Node structure handling
  - `opcodes.py` - Opcode definitions
  - `datawindow.py` - DataWindow extraction
  - `pcode_ir.py` - P-code intermediate representation

- **pbd_io/** - I/O operations
  - `file_operations.py` - File handling
  - `pe_scanner.py` - PE file scanning
  - `resource_utils.py` - Resource extraction

- **pbd_cli/** - Command-line interface
  - `orchestrator.py` - CLI orchestration

- **scripts/** - Utility scripts
  - `extract_all_opcodes.py` - Extract opcodes from reference implementations
  - `extract_opcodes_from_reference.py` - Extract opcodes from documentation
  - `extract_reference_opcodes.py` - Extract reference opcodes
  - `list_all_objects.py` - List objects in PBD files

### 2. **parse/** - PowerBuilder Source Code Parsing
Parses PowerBuilder source code and creates AST structures.

- **Main files:**
  - `parser.py` - Main parser entry point
  - `powerbuilder.py` - PowerBuilder-specific parsing
  - `sql_parser.py` - SQL parsing
  - `pseudocode_parser.py` - Pseudocode parsing

- **grammar/** - Lark grammar files
  - `powerbuilder.lark` - Main PB grammar
  - `common_grammar.lark` - Shared grammar rules
  - `sql.lark` - SQL grammar
  - `datawindow.lark` - DataWindow grammar

- **visitors/** - AST transformers and visitors
  - `pb_transformer.py` - PowerBuilder transformer
  - `sql_transformer.py` - SQL transformer
  - `model_generator.py` - Model generation

### 3. **decompile/** - P-code Decompilation
Decompiles PowerBuilder P-code back to source code.

- **Core decompilers:**
  - `structured_decompiler.py` - Main structured decompiler
  - `decompile_structured.py` - Structured decompilation v1
  - `decompile_structured_v2.py` - Enhanced v2
  - `main_decompiler.py` - Decompiler orchestration

- **Components:**
  - `pcode_decoder.py` - Basic P-code decoder
  - `pcode_decoder_v2.py` - Enhanced decoder
  - `control_flow_enhanced.py` - Enhanced control flow analysis
  - `expression_lifter.py` - Expression lifting
  - `stack_emulator.py` - Stack-based emulation
  - `output_formatter.py` - Output formatting

- **opcode_tables/** - Version-specific opcode definitions
  - `pb6_0.py` - PowerBuilder 6.0 opcodes
  - `pb10_5.py` - PowerBuilder 10.5 opcodes
  - `pb80_0.py` - PowerBuilder 8.0 opcodes
  - `unified.py` - Unified opcode table

- **scripts/** - Decompilation utilities
  - `opcode_discovery_pipeline.py` - Automated opcode discovery
  - `compare_decompilers.py` - Compare decompiler outputs
  - `add_missing_opcodes.py` - Add discovered opcodes
  - `validate_opcode_logic.py` - Validate opcode logic

### 4. **model/** - Data Model and AST
Defines the data structures for representing PowerBuilder code.

- **ast/** - Abstract Syntax Tree nodes
  - `nodes.py` - Base node definitions
  - `control.py` - Control flow nodes
  - `functions.py` - Function-related nodes
  - `types.py` - Type definitions
  - `arrays.py` - Array handling

- **Core models:**
  - `pb_application.py` - Application model
  - `pb_function.py` - Function model
  - `pb_variable.py` - Variable model
  - `pb_event.py` - Event model
  - `pb_expression.py` - Expression model

- **pb_datawindow/** - DataWindow models
  - `datawindow.py` - DataWindow representation
  - `column.py` - Column definitions
  - `table.py` - Table structures

- **utils/** - Utility functions
  - `type_system.py` - Type system implementation
  - `validation.py` - Model validation

### 5. **generate/** - Code Generation
Generates code from the parsed/decompiled structures.

- **backend/** - Backend code generation
  - `generate_models.py` - Generate model classes
  - `generate_services.py` - Generate service classes

- **frontend/** - Frontend code generation
  - `generate_component.py` - Generate UI components

- **scripts/**
  - `generate_opcode_reference.py` - Generate opcode reference documentation

### 6. **tests/** - Test Suite
Comprehensive test coverage for all components.

- **Unit tests by module:**
  - `test_extract/` - Extraction tests
  - `test_parse/` - Parser tests
  - `test_decompile/` - Decompiler tests
  - `test_model/` - Model tests
  - `test_generate/` - Generation tests

- **fixtures/** - Test data
  - `pbd_files/` - Sample PBD files
  - `pcode_files/` - P-code test files

### 7. **scripts/** - Utility Scripts
Additional scripts for development and debugging.

- **testing/** - Test-related scripts
  - `test_enhanced_decompiler.py`
  - `test_pcode_extraction.py`

- **debugging/** - Debug utilities
  - `debug_entry_33.py`
  - `debug_nod_size.py`

### 8. **docs/** - Documentation
Project documentation and references.

- Architecture and design documents
- Implementation roadmaps
- Changelog and session notes
- Opcode references and remediation plans

### 9. **reference/** - Reference Materials
External references and implementations.

- **pbdviewer/** - C# reference implementation
- **powerbuilder-decompile/** - Python reference
- **pb_code_examples/** - PowerBuilder code samples
- Opcode reference files

## Main Entry Point

- **main.py** - The main CLI tool that orchestrates the entire pipeline:
  - Extract → Parse → Model → Decompile → Generate

## Key Configuration Files

- **pyproject.toml** - Python project configuration
- **setup.cfg** - Setup configuration
- **decompile/missing_opcodes.yaml** - Missing opcode definitions

## Workflow

1. **Extract**: Read PBD/PBL files and extract components
2. **Parse**: Parse PowerBuilder source code into AST
3. **Model**: Transform AST into semantic model
4. **Decompile**: Convert P-code back to source
5. **Generate**: Generate target code from model

Each phase has its own directory with focused responsibilities, making the codebase modular and maintainable.