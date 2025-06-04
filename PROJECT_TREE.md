# SIME Finch Project Directory Tree

Generated comprehensive directory structure with detailed file descriptions and accurate line counts.

## Project Overview

SIME Finch is a sophisticated PowerBuilder reverse engineering toolkit that transforms legacy PowerBuilder applications into modern web applications. The pipeline consists of four main stages:

1. **Extract**: Reads PowerBuilder binary files (PBL/PBD) and extracts source code
2. **Parse**: Converts PowerBuilder source into Abstract Syntax Trees (ASTs)
3. **Decompile**: Transforms PowerBuilder P-code into readable pseudocode
4. **Generate**: Creates modern web applications (Litestar backend, React/Astro frontend)

```
/Users/michael/Projects/sime-finch/
├── main.py  # CLI entry point orchestrating the 4-stage pipeline (extract→parse→decompile→generate) (299 lines)
├── pyproject.toml  # Project configuration with dependencies for parsing (Lark), web (Litestar), and testing (217 lines)
├── Makefile  # Development automation: install, test, clean, format, lint commands (41 lines)
├── README.md  # Project overview and quick start guide (31 lines)
├── CONFIG_FILES.md  # Documentation for configuration file formats and usage (68 lines)
├── PROJECT_TREE.md  # This file - comprehensive project structure documentation (719 lines)
│
├── extract/  # Stage 1: PowerBuilder binary file extraction module (5,977 lines total)
│   ├── __init__.py  # Module exports: extract_pbls, Library, and core functions (50 lines)
│   ├── extract_coordinator.py  # Orchestrates extraction pipeline with error recovery strategies (383 lines)
│   │
│   ├── pbd_core/  # Core binary file parsing logic (2,823 lines)
│   │   ├── __init__.py  # Core module initialization (13 lines)
│   │   ├── library.py  # High-level API for PBL/PBD file access with lazy loading (398 lines)
│   │   ├── header.py  # Parses file headers to detect format (ASCII/Unicode) and metadata (225 lines)
│   │   ├── node.py  # Parses NOD blocks containing file entry metadata (289 lines)
│   │   ├── entry.py  # Parses ENT* structures with object metadata and boundaries (462 lines)
│   │   ├── dat.py  # Extracts DAT blocks containing actual source code (177 lines)
│   │   ├── datawindow.py  # Specialized extraction for DataWindow objects (170 lines)
│   │   ├── crossref.py  # Cross-reference handling for object dependencies (114 lines)
│   │   ├── pbd_object.py  # PowerBuilder object representation with type detection (174 lines)
│   │   ├── opcodes.py  # Opcode definitions for P-code interpretation (223 lines)
│   │   ├── symbol_table.py  # Symbol table management for name resolution (171 lines)
│   │   ├── version_detector.py  # PowerBuilder version detection from binary signatures (137 lines)
│   │   ├── pfc_utils.py  # PowerBuilder Foundation Class detection utilities (58 lines)
│   │   ├── exceptions.py  # Custom exceptions for extraction errors (43 lines)
│   │   ├── pcode_ir.py  # P-code intermediate representation structures (61 lines)
│   │   │
│   │   └── utils/  # Core utility functions
│   │       ├── __init__.py  # Utils initialization (0 lines)
│   │       ├── hexdump_viewer.py  # Binary data visualization for debugging (98 lines)
│   │       └── inspect_pbd.py  # PBD file inspection and analysis utilities (168 lines)
│   │
│   ├── pbd_io/  # I/O operations and file handling (1,154 lines)
│   │   ├── __init__.py  # I/O module initialization (11 lines)
│   │   ├── utils.py  # Binary conversion functions (bin2int, decode, MIME detection) (336 lines)
│   │   ├── scanner.py  # Signature scanning for corrupted file recovery (225 lines)
│   │   ├── file_operations.py  # Safe file writing with PowerBuilder export headers (115 lines)
│   │   ├── progress.py  # Progress tracking with tqdm integration (316 lines)
│   │   ├── resource_utils.py  # Embedded resource extraction (images, OLE objects) (257 lines)
│   │   └── pe_scanner.py  # PE file format scanning for embedded PBDs (96 lines)
│   │
│   └── cli/  # Command-line interface tools (331 lines)
│       ├── __init__.py  # CLI module initialization (0 lines)
│       └── bin/  # Executable scripts
│           ├── __init__.py  # Bin module initialization (0 lines)
│           ├── extract_binary_file.py  # Standalone PBD/PBL extraction script (125 lines)
│           ├── pb_to_text.py  # PowerBuilder to text conversion utility (89 lines)
│           └── run_utils.py  # Common CLI utility functions (63 lines)
│
├── parse/  # Stage 2: PowerBuilder source code parsing module (11,045 lines total)
│   ├── __init__.py  # Module exports: parse functions and parser classes (59 lines)
│   ├── parse_coordinator.py  # Orchestrates parsing with extension-based parser selection (445 lines)
│   ├── powerbuilder.py  # Main PowerBuilder parser implementation (234 lines)
│   ├── sql_parser.py  # SQL statement parser with parameter handling (546 lines)
│   ├── pb_preprocessor.py  # Handles includes, conditionals, and macros (335 lines)
│   ├── base_parser.py  # Abstract base parser with registry pattern (123 lines)
│   ├── parse_schema.py  # Database schema parsing from SQL files (156 lines)
│   ├── parse_ui.py  # UI element parsing utilities (189 lines)
│   ├── interactive.py  # Interactive parsing REPL for testing (313 lines)
│   ├── pseudocode_parser.py  # Parses decompiled pseudocode (178 lines)
│   ├── pseudocode_transformer.py  # Transforms pseudocode parse trees to AST (512 lines)
│   ├── constants.py  # Parser constants and token definitions (56 lines)
│   ├── errors.py  # Parser-specific error classes (98 lines)
│   ├── exceptions.py  # Additional exception types (67 lines)
│   ├── debug.py  # Debug utilities for parser development (78 lines)
│   ├── logging.py  # Parser logging configuration (45 lines)
│   ├── grammar.py  # Grammar loading and management (89 lines)
│   ├── pseudocode.lark  # Pseudocode grammar definition (89 lines)
│   │
│   ├── grammar/  # Lark grammar definitions (2,192 lines)
│   │   ├── powerbuilder.lark  # Main PowerBuilder grammar with control structures (583 lines)
│   │   ├── powerbuilder_core.lark  # Core language constructs (234 lines)
│   │   ├── powerbuilder_js.lark  # JavaScript-style PowerBuilder syntax (156 lines)
│   │   ├── sql.lark  # SQL grammar for embedded queries (237 lines)
│   │   ├── sql_grammar.lark  # Extended SQL grammar with transactions (223 lines)
│   │   ├── datawindow.lark  # DataWindow-specific syntax (267 lines)
│   │   ├── datawindow_grammar.lark  # Full DataWindow grammar (189 lines)
│   │   ├── window_grammar.lark  # Window and control definitions (134 lines)
│   │   └── common_grammar.lark  # Shared grammar rules (145 lines)
│   │
│   └── visitors/  # AST transformation visitors (5,600 lines)
│       ├── __init__.py  # Visitors initialization (0 lines)
│       ├── transformer.py  # Main AST transformer with position tracking (1,028 lines)
│       ├── sql_transformer.py  # SQL-specific AST transformation (1,723 lines)
│       ├── abstract_visitor.py  # Abstract visitor base with traversal logic (490 lines)
│       ├── entity_creator.py  # Creates model entities from parse trees (494 lines)
│       ├── model_generator.py  # Generates model classes from AST (345 lines)
│       ├── pb_transformer.py  # PowerBuilder-specific transformations (267 lines)
│       ├── pb_js_transformer.py  # JavaScript-style syntax transformer (189 lines)
│       ├── pb_function.py  # Function parsing and transformation (223 lines)
│       ├── pb_types.py  # Type annotation parsing (145 lines)
│       ├── code_rewrite.py  # AST rewriting for code modernization (234 lines)
│       ├── position_tracker.py  # Source position tracking for error reporting (98 lines)
│       └── famix_importer.py  # FAMIX model import support (178 lines)
│
├── decompile/  # Stage 3: PowerBuilder P-code decompilation module (12,562 lines total)
│   ├── __init__.py  # Module exports: decompilation functions (56 lines)
│   ├── decompile_coordinator.py  # Orchestrates decompilation pipeline (319 lines)
│   │
│   ├── core/  # Core decompilation algorithms (2,553 lines)
│   │   ├── __init__.py  # Core module initialization (0 lines)
│   │   ├── pcode_decoder.py  # Decodes P-code instructions from binary (469 lines)
│   │   ├── stack_emulator.py  # Stack machine emulation for expression reconstruction (495 lines)
│   │   ├── control_flow.py  # Control flow graph construction and analysis (497 lines)
│   │   ├── expression_lifter.py  # Lifts stack operations to high-level expressions (729 lines)
│   │   └── output_formatter.py  # Formats decompiled code with proper indentation (363 lines)
│   │
│   ├── analysis/  # Code analysis components (808 lines)
│   │   ├── __init__.py  # Analysis module initialization (0 lines)
│   │   ├── pcode_detector.py  # Enhanced P-code section detection in binaries (259 lines)
│   │   ├── control_flow_analyzer.py  # Identifies loops, conditionals, and jumps (379 lines)
│   │   └── datawindow_extractor.py  # Specialized DataWindow object extraction (170 lines)
│   │
│   ├── generators/  # Code generation from analysis (1,004 lines)
│   │   ├── __init__.py  # Generators initialization (0 lines)
│   │   ├── integrated_decompiler.py  # Integrates all decompilation components (263 lines)
│   │   ├── structured_decompiler.py  # Generates structured code from CFG (312 lines)
│   │   └── pcode_to_source.py  # Converts P-code to PowerBuilder source (429 lines)
│   │
│   ├── opcodes/  # PowerBuilder opcode definitions (3,907 lines)
│   │   ├── __init__.py  # Opcode module initialization (25 lines)
│   │   ├── opcode_manager.py  # Version-specific opcode table selection (98 lines)
│   │   ├── opcodes_unified.py  # Unified opcode definitions (582 opcodes) (688 lines)
│   │   ├── pb6_0.py  # PowerBuilder 6.0 specific opcodes (161 lines)
│   │   ├── pb10_5.py  # PowerBuilder 10.5 specific opcodes (161 lines)
│   │   ├── pb80_0.py  # PowerBuilder 8.0 specific opcodes (597 lines)
│   │   ├── unified.py  # Fallback unified opcode table (161 lines)
│   │   └── missing_opcodes.yaml  # Tracking unimplemented opcode variants (2,160 lines)
│   │
│   ├── legacy/  # Previous decompiler implementations (3,020 lines)
│   │   ├── __init__.py  # Legacy module initialization (0 lines)
│   │   ├── decompiler.py  # Original decompiler implementation (394 lines)
│   │   ├── decompile_structured.py  # First structured decompilation attempt (440 lines)
│   │   ├── decompile_structured_v2.py  # Improved structured decompiler (139 lines)
│   │   ├── expression_builder.py  # Original expression building logic (329 lines)
│   │   ├── stack_simulator.py  # Original stack simulation (460 lines)
│   │   ├── pcode_decoder_v1.py  # First P-code decoder version (484 lines)
│   │   ├── pcode_detector.py  # Original P-code detection (160 lines)
│   │   └── control_flow_v1.py  # First control flow implementation (494 lines)
│   │
│   ├── templates/  # Code generation templates (270 lines)
│   │   ├── structured.py.jinja2  # Template for structured code output (130 lines)
│   │   └── structured_v2.py.jinja2  # Improved structured code template (140 lines)
│   │
│   └── violations/  # Code quality analysis (481 lines)
│       └── visitor.py  # AST visitor for detecting code violations (481 lines)
│
├── model/  # Data models and AST node definitions (10,608 lines total)
│   ├── __init__.py  # Comprehensive module exports (381 lines)
│   │
│   ├── base/  # Base model classes (790 lines)
│   │   ├── __init__.py  # Base module initialization (0 lines)
│   │   ├── pb_entity.py  # Base entity class with metadata (167 lines)
│   │   ├── pb_behavioral.py  # Base for functions, events with behavior (298 lines)
│   │   ├── pb_behavioral_library.py  # Library of behavioral entities (78 lines)
│   │   ├── pb_file.py  # File representation with parsing support (298 lines)
│   │   ├── pb_type.py  # Type system base classes and enums (267 lines)
│   │   └── exception.py  # Model-specific exceptions (29 lines)
│   │
│   ├── entities/  # PowerBuilder entity models (1,089 lines)
│   │   ├── __init__.py  # Entities initialization (0 lines)
│   │   ├── pb_application.py  # Application-level configuration (94 lines)
│   │   ├── pb_function.py  # Function definitions with parameters (178 lines)
│   │   ├── pb_event.py  # Event definitions with handlers (134 lines)
│   │   ├── pb_variable.py  # Variable declarations with scope (145 lines)
│   │   ├── pb_argument.py  # Function/event argument definitions (67 lines)
│   │   └── pb_expression.py  # Expression evaluation model (189 lines)
│   │
│   ├── constructs/  # Language constructs (657 lines)
│   │   ├── __init__.py  # Constructs initialization (0 lines)
│   │   ├── pb_array.py  # Array type with bounds checking (112 lines)
│   │   ├── pb_sql.py  # SQL statement representations (234 lines)
│   │   ├── pb_access.py  # Access modifier handling (58 lines)
│   │   ├── pb_attribute_access.py  # Attribute access patterns (45 lines)
│   │   ├── global_vars.py  # Global variable management (103 lines)
│   │   └── pcode.py  # P-code instruction representation (89 lines)
│   │
│   ├── ast/  # Abstract Syntax Tree nodes (1,943 lines)
│   │   ├── __init__.py  # AST module exports (28 lines)
│   │   ├── nodes.py  # Core AST node base classes (453 lines)
│   │   ├── control.py  # Control flow nodes (if, while, for) (405 lines)
│   │   ├── functions.py  # Function-related AST nodes (234 lines)
│   │   ├── arrays.py  # Array access and manipulation nodes (123 lines)
│   │   ├── types.py  # Type annotation nodes (289 lines)
│   │   ├── io.py  # I/O operation nodes (156 lines)
│   │   ├── controlflow.py  # Control flow analysis helpers (89 lines)
│   │   └── node_kind.py  # Node type enumeration (78 lines)
│   │
│   ├── datawindow/  # DataWindow models (343 lines)
│   │   ├── __init__.py  # DataWindow module initialization (0 lines)
│   │   ├── datawindow.py  # Main DataWindow implementation (298 lines)
│   │   └── datawindow_stubs.py  # Type stubs for DataWindow (45 lines)
│   │
│   ├── pb_datawindow/  # PowerBuilder DataWindow specifics (435 lines)
│   │   ├── __init__.py  # PB DataWindow initialization (0 lines)
│   │   ├── datawindow.py  # DataWindow object model (234 lines)
│   │   ├── column.py  # DataWindow column definitions (89 lines)
│   │   └── table.py  # DataWindow table mappings (112 lines)
│   │
│   ├── pb_transaction/  # Transaction handling (755 lines)
│   │   ├── __init__.py  # Transaction module initialization (0 lines)
│   │   ├── transaction.py  # Core transaction model (289 lines)
│   │   ├── distributed.py  # Distributed transaction support (156 lines)
│   │   ├── error_handling.py  # Transaction error patterns (98 lines)
│   │   ├── savepoint.py  # Savepoint management (67 lines)
│   │   └── statement.py  # Transaction SQL statements (145 lines)
│   │
│   ├── system/  # System-level definitions (1,610 lines)
│   │   ├── __init__.py  # System module initialization (0 lines)
│   │   ├── functions.py  # PowerBuilder system functions catalog (769 lines)
│   │   ├── events.py  # System event definitions and handlers (521 lines)
│   │   └── globals.py  # System global variables and constants (320 lines)
│   │
│   ├── ui/  # UI element models (1,294 lines)
│   │   ├── __init__.py  # UI module initialization (0 lines)
│   │   └── ui_elements.py  # Comprehensive UI control hierarchy (1,294 lines)
│   │
│   ├── library/  # Library management (167 lines)
│   │   ├── __init__.py  # Library module initialization (0 lines)
│   │   └── library.py  # PowerBuilder library representation (167 lines)
│   │
│   ├── source/  # Source code representation (134 lines)
│   │   ├── __init__.py  # Source module initialization (0 lines)
│   │   └── source.py  # Source file model with location tracking (134 lines)
│   │
│   ├── transaction/  # Additional transaction support (268 lines)
│   │   ├── __init__.py  # Transaction initialization (0 lines)
│   │   ├── transaction.py  # Transaction implementation (234 lines)
│   │   └── transaction_stubs.py  # Transaction type stubs (34 lines)
│   │
│   ├── attribute/  # Attribute handling (123 lines)
│   │   ├── __init__.py  # Attribute module initialization (0 lines)
│   │   └── attribute.py  # Attribute access and modification (123 lines)
│   │
│   ├── analysis/  # Code analysis tools (145 lines)
│   │   ├── __init__.py  # Analysis module initialization (0 lines)
│   │   └── analysis.py  # Static analysis implementation (145 lines)
│   │
│   └── utils/  # Model utilities (2,190 lines)
│       ├── __init__.py  # Utils exports (18 lines)
│       ├── type_system.py  # Type validation and compatibility (307 lines)
│       ├── common.py  # Common utility functions (429 lines)
│       ├── errors.py  # Error hierarchy and handling (394 lines)
│       ├── validators.py  # Data validation implementations (234 lines)
│       ├── type.py  # Type manipulation utilities (198 lines)
│       ├── utils.py  # General utility functions (167 lines)
│       ├── scope.py  # Variable scope management (123 lines)
│       ├── base.py  # Base utility classes (89 lines)
│       ├── validation.py  # Validation framework (89 lines)
│       ├── config.py  # Configuration management (67 lines)
│       └── logging.py  # Logging configuration (45 lines)
│
├── generate/  # Stage 4: Modern code generation module (1,596 lines total)
│   ├── __init__.py  # Module exports for generators (14 lines)
│   ├── generate_coordinator.py  # Base CodeGenerator class with Jinja2 integration (248 lines)
│   ├── jinja_filters.py  # Custom Jinja2 filters for code formatting (160 lines)
│   │
│   ├── backend/  # Backend code generation (756 lines)
│   │   ├── __init__.py  # Backend module initialization (0 lines)
│   │   ├── generate_models.py  # SQLModel model generation from schemas (167 lines)
│   │   ├── generate_services.py  # Litestar service layer generation (95 lines)
│   │   │
│   │   └── templates/  # Backend code templates (494 lines)
│   │       ├── sqlmodel_model.jinja2  # SQLModel class template (98 lines)
│   │       ├── service.py.jinja2  # Service layer template (112 lines)
│   │       ├── system_functions.py.jinja2  # System function implementations (45 lines)
│   │       └── python.py  # Advanced Python code generation with AST (404 lines)
│   │
│   └── frontend/  # Frontend code generation (626 lines)
│       ├── __init__.py  # Frontend module initialization (0 lines)
│       ├── generate_component.py  # React/Astro component generation (157 lines)
│       │
│       └── templates/  # Frontend component templates (469 lines)
│           ├── component.tsx.jinja2  # React TypeScript component (134 lines)
│           ├── component.astro.jinja2  # Astro component template (78 lines)
│           ├── listview.tsx.jinja2  # Data grid component with Material-UI (168 lines)
│           └── richtext.tsx.jinja2  # Rich text editor with Quill.js (89 lines)
│
├── scripts/  # Development and maintenance scripts (5,242 lines total)
│   │
│   ├── analysis/  # Code analysis scripts (354 lines)
│   │   ├── analyze_missing_opcodes.py  # Identifies unimplemented opcodes (156 lines)
│   │   └── verify_opcode_mappings.py  # Validates opcode consistency (198 lines)
│   │
│   ├── debug/  # Debugging utilities (1,109 lines)
│   │   ├── debug_entry_33.py  # Debug specific PBD entry (89 lines)
│   │   ├── debug_nod_size.py  # NOD block size debugging (78 lines)
│   │   ├── debug_pbd_entries_summary.py  # PBD entry analysis (98 lines)
│   │   ├── debug_pcode_detection_detailed.py  # Detailed P-code detection (234 lines)
│   │   ├── debug_pcode_extraction.py  # P-code extraction debugging (189 lines)
│   │   ├── debug_pcode_extraction_simple.py  # Simplified extraction debug (123 lines)
│   │   └── debug_pcode_final.py  # Final P-code debugging (167 lines)
│   │
│   ├── maintenance/  # Project maintenance scripts (119 lines)
│   │   ├── clean.sh  # Cleanup temporary files and caches (18 lines)
│   │   ├── download_all_resources.sh  # Download reference materials (34 lines)
│   │   └── setup_dev.sh  # Development environment setup (67 lines)
│   │
│   ├── opcodes/  # Opcode management scripts (3,660 lines)
│   │   ├── discovery/  # Opcode discovery automation (1,948 lines)
│   │   │   ├── opcode_discovery_pipeline.py  # Main discovery pipeline (437 lines)
│   │   │   ├── opcode_discovery_config.py  # Discovery configuration (99 lines)
│   │   │   ├── add_missing_opcodes.py  # Add discovered opcodes (178 lines)
│   │   │   ├── add_specific_variants.py  # Add opcode variants (116 lines)
│   │   │   ├── add_final_missing_variants.py  # Final variant additions (104 lines)
│   │   │   ├── add_missing_final_opcodes.py  # Final opcode additions (92 lines)
│   │   │   ├── update_opcodes_from_verified.py  # Update from verified source (116 lines)
│   │   │   └── update_decoder_to_verified.py  # Update decoder tables (87 lines)
│   │   │
│   │   ├── extraction/  # Opcode extraction tools (721 lines)
│   │   │   ├── extract_all_opcodes.py  # Extract opcodes from all files (324 lines)
│   │   │   ├── extract_opcodes_from_reference.py  # Extract from reference impl (136 lines)
│   │   │   ├── extract_reference_opcodes.py  # Extract reference opcodes (77 lines)
│   │   │   └── list_all_objects.py  # List all PBD objects (84 lines)
│   │   │
│   │   ├── generation/  # Opcode reference generation (335 lines)
│   │   │   └── generate_opcode_reference.py  # Generate opcode documentation (335 lines)
│   │   │
│   │   └── validation/  # Opcode validation tools (656 lines)
│   │       ├── compare_decompilers.py  # Compare decompiler outputs (185 lines)
│   │       ├── compare_opcodes.py  # Compare opcode definitions (166 lines)
│   │       └── validate_opcode_logic.py  # Validate opcode implementation (243 lines)
│   │
│   └── pipeline/  # Pipeline testing scripts (1,532 lines)
│       ├── root_test_full_pipeline.py  # Complete pipeline test (419 lines)
│       ├── root_test_pipeline_simplified.py  # Simplified pipeline test (180 lines)
│       ├── test_enhanced_decompiler.py  # Enhanced decompiler tests (256 lines)
│       ├── test_enhanced_decompiler_debug.py  # Decompiler debugging (189 lines)
│       ├── test_full_pipeline.py  # Full pipeline integration test (234 lines)
│       ├── test_pcode_detection_logic.py  # P-code detection tests (178 lines)
│       └── test_pcode_extraction.py  # P-code extraction tests (234 lines)
│
├── tests/  # Comprehensive test suite (20,121 lines total)
│   ├── conftest.py  # Pytest configuration and fixtures (98 lines)
│   ├── verify_imports.py  # Import validation script (78 lines)
│   ├── test_common.py  # Common test utilities (329 lines)
│   ├── test_main.py  # Main entry point tests (89 lines)
│   ├── test_extract.py  # Extraction module tests (145 lines)
│   ├── test_errors.py  # Error handling tests (67 lines)
│   ├── test_type_system.py  # Type system tests (267 lines)
│   ├── test_validation.py  # Validation framework tests (123 lines)
│   ├── test_validators.py  # Validator implementation tests (189 lines)
│   ├── test_pbd_extraction.py  # PBD extraction integration tests (234 lines)
│   ├── test_pbd_extraction_simple.py  # Simple extraction tests (156 lines)
│   ├── test_pbd_fixtures.py  # PBD test fixture management (178 lines)
│   │
│   ├── fixtures/  # Test data and fixtures (423 lines)
│   │   ├── __init__.py  # Fixtures initialization (0 lines)
│   │   ├── custom_control.sru  # Custom control test fixture (45 lines)
│   │   ├── globals.sra  # Global variables test fixture (34 lines)
│   │   ├── main_menu.srm  # Menu test fixture (67 lines)
│   │   ├── simple_window.srw  # Window test fixture (89 lines)
│   │   ├── test_tj_report_structured.pb  # Structured report fixture (123 lines)
│   │   │
│   │   ├── pbd_files/  # Binary test files
│   │   │   └── (various .pbd test files)
│   │   │
│   │   └── pcode_files/  # P-code test files (292 lines)
│   │       ├── test.pcode  # Basic P-code test (23 lines)
│   │       ├── test_debug.pcode  # Debug P-code test (34 lines)
│   │       ├── test_decode.pcode  # Decode test (45 lines)
│   │       ├── test_tj_report.pcode  # Report P-code test (67 lines)
│   │       ├── test_update_coa.pcode  # COA update test (56 lines)
│   │       ├── test_update_utf8.pcode  # UTF-8 test (38 lines)
│   │       └── test_username.pcode  # Username test (29 lines)
│   │
│   ├── test_parse/  # Parser tests (3,169 lines)
│   │   ├── __init__.py  # Parse tests initialization (0 lines)
│   │   ├── conftest.py  # Parse test configuration (78 lines)
│   │   ├── test_parser.py  # General parser tests (223 lines)
│   │   ├── test_powerbuilder_parser.py  # PowerBuilder parser tests (332 lines)
│   │   ├── test_sql_parser.py  # SQL parser tests (267 lines)
│   │   ├── test_pb_preprocessor.py  # Preprocessor tests (198 lines)
│   │   ├── test_core_grammar.py  # Core grammar tests (234 lines)
│   │   ├── test_pseudocode.py  # Pseudocode parsing tests (349 lines)
│   │   ├── test_constants.py  # Parser constants tests (98 lines)
│   │   ├── test_event_parser.py  # Event parsing tests (189 lines)
│   │   ├── test_globals.py  # Global variable parsing (145 lines)
│   │   ├── test_menu.py  # Menu parsing tests (167 lines)
│   │   ├── test_user_object.py  # User object tests (189 lines)
│   │   └── test_window.py  # Window parsing tests (234 lines)
│   │
│   ├── test_model/  # Model tests (7,156 lines)
│   │   ├── __init__.py  # Model tests initialization (0 lines)
│   │   ├── conftest.py  # Model test configuration (89 lines)
│   │   ├── test_ast_nodes.py  # AST node tests (319 lines)
│   │   ├── test_pb_behavioral.py  # Behavioral entity tests (411 lines)
│   │   ├── test_datawindow.py  # DataWindow model tests (234 lines)
│   │   ├── test_transaction.py  # Transaction tests (223 lines)
│   │   ├── test_system_functions.py  # System function tests (298 lines)
│   │   ├── test_specialized_controls.py  # UI control tests (757 lines)
│   │   ├── test_treeview_control.py  # TreeView specific tests (319 lines)
│   │   └── (45 more test files for specific model components)
│   │
│   ├── test_decompile/  # Decompilation tests (1,534 lines)
│   │   ├── __init__.py  # Decompile tests initialization (0 lines)
│   │   ├── test_control_flow_enhanced.py  # Control flow tests (234 lines)
│   │   ├── test_expression_lifter.py  # Expression lifting tests (309 lines)
│   │   ├── test_pcode_decoder_v2.py  # P-code decoder tests (256 lines)
│   │   ├── test_stack_emulator_v2.py  # Stack emulation tests (312 lines)
│   │   ├── test_output_formatter.py  # Output formatting tests (189 lines)
│   │   └── test_pcode_detector_enhanced.py  # P-code detection tests (223 lines)
│   │
│   ├── test_generate/  # Generation tests (455 lines)
│   │   ├── __init__.py  # Generate tests initialization (0 lines)
│   │   ├── test_code_generator.py  # Code generator tests (310 lines)
│   │   └── test_jinja_filters.py  # Template filter tests (145 lines)
│   │
│   ├── test_app/  # Application-level tests (357 lines)
│   │   ├── __init__.py  # App tests initialization (0 lines)
│   │   ├── conftest.py  # App test configuration (45 lines)
│   │   ├── test_application.py  # Application tests (189 lines)
│   │   └── test_access_tracking.py  # Access tracking tests (123 lines)
│   │
│   ├── test_ast/  # AST-specific tests (1,299 lines)
│   │   ├── __init__.py  # AST tests initialization (0 lines)
│   │   ├── conftest.py  # AST test configuration (67 lines)
│   │   ├── test_nodes.py  # Node structure tests (189 lines)
│   │   ├── test_expressions.py  # Expression AST tests (298 lines)
│   │   ├── test_statements.py  # Statement AST tests (267 lines)
│   │   ├── test_events.py  # Event AST tests (234 lines)
│   │   ├── test_sql.py  # SQL AST tests (223 lines)
│   │   └── test_types.py  # Type AST tests (178 lines)
│   │
│   └── test_utils/  # Utility tests (390 lines)
│       ├── __init__.py  # Utils tests initialization (0 lines)
│       ├── conftest.py  # Utils test configuration (45 lines)
│       ├── test_type.py  # Type utility tests (156 lines)
│       └── test_type_system.py  # Type system tests (189 lines)
│
├── reference/  # Reference implementations and documentation (515 files)
│   ├── __init__.py  # Reference module initialization (0 lines)
│   ├── file_index.txt  # File index for reference materials (156 lines)
│   ├── opcode_reference.json  # JSON opcode reference (8,789 lines)
│   ├── opcode_reference.yaml  # YAML opcode reference (7,117 lines)
│   │
│   ├── decompilers/  # Reference decompiler implementations
│   │   ├── pbdviewer/  # C# PBD viewer implementation
│   │   │   ├── README.md  # PBD viewer documentation (67 lines)
│   │   │   ├── PbdViewer.csproj  # C# project configuration (78 lines)
│   │   │   ├── MainWindow.xaml.cs  # Main window implementation (234 lines)
│   │   │   └── (C# implementation files)
│   │   │
│   │   └── powerbuilder-decompile/  # Python reference decompiler
│   │       ├── README.md  # Decompiler documentation (89 lines)
│   │       ├── analyse.py  # PBD analysis script (178 lines)
│   │       ├── pbd_analyse.py  # Detailed PBD analysis (234 lines)
│   │       └── pbd/  # PBD handling module
│   │           ├── pcode.py  # P-code implementation (1,264 lines)
│   │           ├── system_functions.py  # System functions (4,279 lines)
│   │           └── definitions.py  # PBD format definitions (1,201 lines)
│   │
│   ├── pb_code_examples/  # PowerBuilder version examples
│   │   ├── README.md  # Examples overview (45 lines)
│   │   └── (PowerBuilder version directories 6.0 through 2022)
│   │
│   └── (additional reference directories)
│
├── docs/  # Project documentation (6,782 lines total)
│   ├── README.md  # Main documentation hub (446 lines)
│   ├── architecture.md  # System architecture overview (198 lines)
│   ├── architecture-mermaid.md  # Architecture diagrams (173 lines)
│   ├── architectural_decisions.md  # Key design decisions (347 lines)
│   ├── changelog.md  # Detailed project changelog (612 lines)
│   ├── comprehensive_project_review.md  # Full project analysis (395 lines)
│   ├── development_roadmap.md  # Future development plans (214 lines)
│   ├── implementation_roadmap.md  # Implementation details (396 lines)
│   ├── opcode_reference.md  # PowerBuilder opcode documentation (611 lines)
│   ├── pipeline_architecture.md  # Pipeline design details (339 lines)
│   ├── parsing_phase_plan.md  # Parser implementation plan (173 lines)
│   ├── decompilation_progress.md  # Decompiler status (120 lines)
│   ├── TODO_Phases.md  # Development task tracking (92 lines)
│   └── (additional documentation files)
│
├── input/  # Input files and test data
│   └── pbd_files/  # PBD input files for testing
│
├── output/  # Generated output directory
│   ├── extracted/  # Stage 1 output - extracted source files
│   ├── parsed/  # Stage 2 output - parsed ASTs
│   ├── decompiled/  # Stage 3 output - decompiled code
│   └── generated/  # Stage 4 output - modern web app code
│
└── logs/  # Application logs
    └── unknown_opcodes.log  # Unrecognized opcode tracking
```

## Module Interactions

The project follows a clear pipeline architecture where each stage builds upon the previous:

1. **Extract Module** → Reads binary PBL/PBD files and outputs text source files
2. **Parse Module** → Parses source files into AST using Lark grammars
3. **Decompile Module** → Converts P-code sections into readable PowerBuilder code
4. **Model Module** → Provides shared data structures used by all stages
5. **Generate Module** → Transforms ASTs into modern web application code

The `main.py` CLI orchestrates this pipeline, allowing users to run individual stages or the complete transformation process.

## Summary Statistics

- **Total Project Size**: ~75,000 lines of code and documentation
- **Core Python Code**: ~41,788 lines (excluding tests)
- **Test Coverage**: ~20,121 lines of test code
- **Documentation**: ~6,782 lines
- **Supported PowerBuilder Versions**: 6.0 through 2022
- **Output Formats**: SQLModel, Litestar, React, Astro