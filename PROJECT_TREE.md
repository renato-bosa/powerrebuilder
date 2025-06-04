# SIME Finch Project Directory Tree

Generated comprehensive directory structure with file descriptions and line counts.

```
/Users/michael/Projects/sime-finch/
├── main.py  # Main CLI entry point for PowerBuilder reverse engineering tool (299 lines)
├── test_full_pipeline.py  # End-to-end pipeline testing script (419 lines)
├── test_pipeline_simplified.py  # Simplified pipeline testing for debugging (180 lines)
├── pyproject.toml  # Project configuration and dependencies (218 lines)
├── setup.cfg  # Additional project setup configuration (2 lines)
├── .gitignore  # Git ignore patterns (62 lines)
├── .cursorignore  # Cursor IDE ignore patterns (1 lines)
├── CONFIG_FILES.md  # Documentation for configuration files (35 lines)
│
├── .claude/  # Claude AI configuration directory
│   ├── CLAUDE.md  # Claude AI instructions and context (106 lines)
│   ├── critical_issues_priority.md  # Priority issues for Claude to address (68 lines)
│   ├── project_review_instructions.md  # Instructions for project review (86 lines)
│   └── settings.local.json  # Local Claude settings (8 lines)
│
├── .vscode/  # VS Code configuration
│   └── settings.json  # VS Code workspace settings (7 lines)
│
├── .pytest_cache/  # Pytest cache directory
│   └── README.md  # Pytest cache documentation (8 lines)
│
├── docs/  # Project documentation
│   ├── README.md  # Main project documentation (446 lines)
│   ├── TODO_Phases.md  # Development phases and tasks (92 lines)
│   ├── architectural_decisions.md  # Key architectural decisions (347 lines)
│   ├── architecture-mermaid.md  # Architecture diagrams in Mermaid (173 lines)
│   ├── architecture.md  # System architecture documentation (198 lines)
│   ├── changelog.md  # Project changelog (612 lines)
│   ├── changelog old.md  # Historical changelog (83 lines)
│   ├── comprehensive_project_review.md  # Comprehensive project analysis (395 lines)
│   ├── decompilation_progress.md  # Decompilation feature progress (120 lines)
│   ├── development_roadmap.md  # Future development plans (214 lines)
│   ├── implementation_comparison.md  # Comparison of implementation approaches (84 lines)
│   ├── implementation_roadmap.md  # Detailed implementation plan (396 lines)
│   ├── opcode_discovery_automation.md  # Opcode discovery process documentation (203 lines)
│   ├── opcode_discovery_lessons.md  # Lessons learned from opcode discovery (104 lines)
│   ├── OPCODE_DISCOVERY_TOOLS.md  # Tools for opcode discovery (69 lines)
│   ├── opcode_reference.md  # PowerBuilder opcode reference (611 lines)
│   ├── opcode_remediation_plan.md  # Plan for fixing opcode issues (166 lines)
│   ├── parsing_phase_plan.md  # Parsing phase implementation plan (173 lines)
│   ├── pipeline_architecture.md  # Pipeline architecture details (339 lines)
│   ├── pipeline_diagram_simple.md  # Simplified pipeline diagram (41 lines)
│   ├── powerbuilder_file_extensions.md  # PowerBuilder file type reference (48 lines)
│   ├── project_structure_map.md  # Project structure overview (118 lines)
│   ├── project_structure_overview.md  # Detailed project structure (165 lines)
│   ├── session_notes_2024.md  # Development session notes from 2024 (180 lines)
│   ├── session_notes_2025_06_03.md  # Development session notes from June 2025 (214 lines)
│   ├── style_guide.txt  # Code style guidelines (54 lines)
│   └── technical_analysis.md  # Technical analysis of the system (440 lines)
│
├── decompile/  # PowerBuilder PCode decompilation module
│   ├── __init__.py  # Decompile module initialization (0 lines)
│   ├── control_flow.py  # Control flow analysis for decompilation (494 lines)
│   ├── control_flow_analyzer.py  # Enhanced control flow analyzer (379 lines)
│   ├── control_flow_enhanced.py  # Advanced control flow features (497 lines)
│   ├── datawindow_extractor.py  # DataWindow extraction utilities (78 lines)
│   ├── decompile_coordinator.py  # Coordinates decompilation pipeline (319 lines)
│   ├── decompile_structured.py  # Structured decompilation approach (440 lines)
│   ├── decompile_structured_v2.py  # Version 2 of structured decompiler (139 lines)
│   ├── decompiler.py  # Main decompiler implementation (394 lines)
│   ├── expression_builder.py  # Builds expressions from PCode (329 lines)
│   ├── expression_lifter.py  # Lifts low-level expressions to high-level (729 lines)
│   ├── integrated_decompiler.py  # Integrated decompilation pipeline (223 lines)
│   ├── output_formatter.py  # Formats decompiled output (363 lines)
│   ├── pcode_decoder.py  # PCode instruction decoder (484 lines)
│   ├── pcode_decoder_v2.py  # Version 2 of PCode decoder (469 lines)
│   ├── pcode_detector.py  # Detects PCode in binary data (160 lines)
│   ├── pcode_detector_enhanced.py  # Enhanced PCode detection (248 lines)
│   ├── pcode_to_source.py  # Converts PCode to source code (429 lines)
│   ├── stack_emulator.py  # Emulates PCode stack operations (495 lines)
│   ├── stack_simulator.py  # Simulates stack for decompilation (460 lines)
│   ├── structured_decompiler.py  # Structured approach to decompilation (312 lines)
│   │
│   ├── opcodes/  # PowerBuilder opcode definitions and tables
│   │   ├── __init__.py  # Opcode tables initialization (25 lines)
│   │   ├── opcode_manager.py  # Manages opcode table selection (107 lines)
│   │   ├── missing_opcodes.yaml  # List of unimplemented opcodes (2160 lines)
│   │   ├── opcodes_unified.py  # Unified opcode definitions (688 lines)
│   │   ├── pb10_5.py  # PowerBuilder 10.5 opcodes (161 lines)
│   │   ├── pb6_0.py  # PowerBuilder 6.0 opcodes (161 lines)
│   │   ├── pb80_0.py  # PowerBuilder 8.0 opcodes (597 lines)
│   │   └── unified.py  # Unified opcode definitions (161 lines)
│   │
│   ├── scripts/  # Decompilation utility scripts
│   │   ├── add_final_missing_variants.py  # Adds final missing opcode variants (104 lines)
│   │   ├── add_missing_final_opcodes.py  # Adds remaining missing opcodes (92 lines)
│   │   ├── add_missing_opcodes.py  # Adds missing opcodes to tables (178 lines)
│   │   ├── add_specific_variants.py  # Adds specific opcode variants (116 lines)
│   │   ├── compare_decompilers.py  # Compares decompiler implementations (185 lines)
│   │   ├── compare_opcodes.py  # Compares opcode definitions (166 lines)
│   │   ├── opcode_discovery_config.py  # Configuration for opcode discovery (99 lines)
│   │   ├── opcode_discovery_pipeline.py  # Pipeline for discovering opcodes (437 lines)
│   │   ├── update_decoder_to_verified.py  # Updates decoder with verified opcodes (87 lines)
│   │   ├── update_opcodes_from_verified.py  # Updates opcodes from verified source (116 lines)
│   │   └── validate_opcode_logic.py  # Validates opcode implementation logic (243 lines)
│   │
│   ├── templates/  # Jinja2 templates for code generation
│   │   ├── structured.py.jinja2  # Template for structured decompilation (130 lines)
│   │   └── structured_v2.py.jinja2  # Version 2 structured template (140 lines)
│   │
│   └── violations/  # Code violation detection
│       └── visitor.py  # AST visitor for detecting violations (481 lines)
│
├── extract/  # PowerBuilder file extraction module
│   ├── __init__.py  # Extract module initialization (50 lines)
│   ├── extract_coordinator.py  # Coordinates extraction pipeline (383 lines)
│   │
│   ├── cli/  # Command-line interface tools for extraction
│   │   ├── __init__.py  # CLI module initialization (0 lines)
│   │   │
│   │   └── bin/  # CLI executable scripts
│   │       ├── __init__.py  # Bin module initialization (0 lines)
│   │       ├── extract_binary_file.py  # Extracts binary PBD/PBL files (125 lines)
│   │       ├── pb_to_text.py  # Converts PowerBuilder to text (89 lines)
│   │       └── run_utils.py  # Utility functions for CLI (63 lines)
│   │
│   ├── pbd_core/  # Core PBD/PBL file handling
│   │   ├── __init__.py  # Core module initialization (13 lines)
│   │   ├── core.py  # Core extraction functionality (287 lines)
│   │   ├── crossref.py  # Cross-reference handling (114 lines)
│   │   ├── dat.py  # DAT file handling (61 lines)
│   │   ├── datawindow.py  # DataWindow extraction (225 lines)
│   │   ├── entry.py  # PBD entry handling (462 lines)
│   │   ├── exceptions.py  # Custom exceptions (43 lines)
│   │   ├── header.py  # PBD header parsing (182 lines)
│   │   ├── library.py  # PowerBuilder library handling (398 lines)
│   │   ├── node.py  # Node structure for PBD data (290 lines)
│   │   ├── opcodes.py  # Opcode definitions and handling (223 lines)
│   │   ├── opcodes.yaml  # Main opcode configuration (5304 lines)
│   │   ├── opcodes_guessed.yaml  # Guessed opcode definitions (3952 lines)
│   │   ├── opcodes_verified.yaml  # Verified opcode definitions (4419 lines)
│   │   ├── pbd_object.py  # PowerBuilder object representation (174 lines)
│   │   ├── pcode_ir.py  # PCode intermediate representation (61 lines)
│   │   ├── pfc_hashes.yaml  # PowerBuilder Foundation Class hashes (73 lines)
│   │   ├── pfc_utils.py  # PFC utility functions (58 lines)
│   │   ├── symbol_table.py  # Symbol table management (171 lines)
│   │   ├── version_detector.py  # PowerBuilder version detection (137 lines)
│   │   │
│   │   └── utils/  # Core utility functions
│   │       ├── __init__.py  # Utils initialization (0 lines)
│   │       ├── hexdump_viewer.py  # Hex dump visualization (98 lines)
│   │       └── inspect_pbd.py  # PBD file inspection utilities (168 lines)
│   │
│   ├── pbd_io/  # I/O operations for PBD files
│   │   ├── __init__.py  # I/O module initialization (11 lines)
│   │   ├── file_operations.py  # File operation utilities (167 lines)
│   │   ├── pe_scanner.py  # PE file scanning (96 lines)
│   │   ├── progress.py  # Progress tracking utilities (316 lines)
│   │   ├── resource_utils.py  # Resource handling utilities (129 lines)
│   │   ├── scanner.py  # PBD file scanner (235 lines)
│   │   └── utils.py  # General I/O utilities (336 lines)
│   │
│   └── scripts/  # Extraction utility scripts
│       ├── extract_all_opcodes.py  # Extracts all opcodes from files (324 lines)
│       ├── extract_opcodes_from_reference.py  # Extracts opcodes from reference (136 lines)
│       ├── extract_reference_opcodes.py  # Extracts reference implementation opcodes (77 lines)
│       └── list_all_objects.py  # Lists all objects in PBD files (84 lines)
│
├── generate/  # Code generation module
│   ├── __init__.py  # Generate module initialization (0 lines)
│   ├── generate_coordinator.py  # Coordinates code generation pipeline (298 lines)
│   ├── jinja_filters.py  # Custom Jinja2 filters for templates (226 lines)
│   │
│   ├── backend/  # Backend code generation
│   │   ├── __init__.py  # Backend module initialization (0 lines)
│   │   ├── generate_models.py  # Generates model classes (167 lines)
│   │   ├── generate_services.py  # Generates service classes (189 lines)
│   │   │
│   │   └── templates/  # Backend code templates
│   │       ├── model.py.jinja2  # Model class template (98 lines)
│   │       ├── python.py  # Python code templates (404 lines)
│   │       ├── service.py.jinja2  # Service class template (112 lines)
│   │       └── system_functions.py.jinja2  # System functions template (45 lines)
│   │
│   ├── frontend/  # Frontend code generation
│   │   ├── __init__.py  # Frontend module initialization (0 lines)
│   │   ├── generate_component.py  # Generates React/Astro components (245 lines)
│   │   │
│   │   └── templates/  # Frontend code templates
│   │       ├── component.astro.jinja2  # Astro component template (78 lines)
│   │       ├── component.tsx.jinja2  # React TypeScript component template (134 lines)
│   │       ├── listview.tsx.jinja2  # ListView component template (168 lines)
│   │       └── richtext.tsx.jinja2  # RichText component template (89 lines)
│   │
│   └── scripts/  # Generation utility scripts
│       └── generate_opcode_reference.py  # Generates opcode reference docs (335 lines)
│
├── model/  # PowerBuilder AST model definitions
│   ├── __init__.py  # Model module initialization with all exports (430 lines)
│   ├── exception.py  # Model exception definitions (29 lines)
│   ├── global_vars.py  # Global variable handling (103 lines)
│   ├── pb_access.py  # PowerBuilder access modifiers (58 lines)
│   ├── pb_application.py  # Application-level model (94 lines)
│   ├── pb_argument.py  # Function argument model (67 lines)
│   ├── pb_array.py  # Array type model (112 lines)
│   ├── pb_attribute_access.py  # Attribute access model (45 lines)
│   ├── pb_behavioral.py  # Behavioral entity model (298 lines)
│   ├── pb_behavioral_library.py  # Behavioral library model (78 lines)
│   ├── pb_entity.py  # Base entity model (167 lines)
│   ├── pb_event.py  # Event model (134 lines)
│   ├── pb_expression.py  # Expression model (189 lines)
│   ├── pb_file.py  # File representation model (298 lines)
│   ├── pb_function.py  # Function model (178 lines)
│   ├── pb_sql.py  # SQL statement model (234 lines)
│   ├── pb_type.py  # Type system model (267 lines)
│   ├── pb_variable.py  # Variable model (145 lines)
│   ├── pcode.py  # PCode representation model (89 lines)
│   │
│   ├── analysis/  # Code analysis utilities
│   │   ├── __init__.py  # Analysis module initialization (0 lines)
│   │   └── analysis.py  # Code analysis implementation (145 lines)
│   │
│   ├── ast/  # Abstract Syntax Tree definitions
│   │   ├── __init__.py  # AST module initialization (28 lines)
│   │   ├── arrays.py  # Array-related AST nodes (123 lines)
│   │   ├── control.py  # Control flow AST nodes (405 lines)
│   │   ├── controlflow.py  # Control flow analysis (89 lines)
│   │   ├── functions.py  # Function-related AST nodes (234 lines)
│   │   ├── io.py  # I/O operation AST nodes (156 lines)
│   │   ├── node_kind.py  # AST node type enumeration (78 lines)
│   │   ├── nodes.py  # Core AST node definitions (453 lines)
│   │   └── types.py  # Type-related AST nodes (289 lines)
│   │
│   ├── attribute/  # Attribute handling
│   │   ├── __init__.py  # Attribute module initialization (0 lines)
│   │   └── attribute.py  # Attribute implementation (123 lines)
│   │
│   ├── datawindow/  # DataWindow model
│   │   ├── __init__.py  # DataWindow module initialization (0 lines)
│   │   ├── datawindow.py  # DataWindow implementation (298 lines)
│   │   └── datawindow_stubs.py  # DataWindow type stubs (45 lines)
│   │
│   ├── library/  # Library model
│   │   ├── __init__.py  # Library module initialization (0 lines)
│   │   └── library.py  # Library implementation (167 lines)
│   │
│   ├── pb_datawindow/  # PowerBuilder DataWindow specific
│   │   ├── __init__.py  # PB DataWindow initialization (0 lines)
│   │   ├── column.py  # DataWindow column model (89 lines)
│   │   ├── datawindow.py  # DataWindow model (234 lines)
│   │   └── table.py  # DataWindow table model (112 lines)
│   │
│   ├── pb_transaction/  # Transaction handling
│   │   ├── __init__.py  # Transaction module initialization (0 lines)
│   │   ├── distributed.py  # Distributed transaction support (156 lines)
│   │   ├── error_handling.py  # Transaction error handling (98 lines)
│   │   ├── savepoint.py  # Savepoint support (67 lines)
│   │   ├── statement.py  # Transaction statements (145 lines)
│   │   └── transaction.py  # Core transaction model (289 lines)
│   │
│   ├── source/  # Source code representation
│   │   ├── __init__.py  # Source module initialization (0 lines)
│   │   └── source.py  # Source code model (134 lines)
│   │
│   ├── system/  # System-level definitions
│   │   ├── __init__.py  # System module initialization (0 lines)
│   │   ├── events.py  # System event definitions (521 lines)
│   │   ├── functions.py  # System function definitions (769 lines)
│   │   └── globals.py  # System global definitions (320 lines)
│   │
│   ├── transaction/  # Transaction models
│   │   ├── __init__.py  # Transaction initialization (0 lines)
│   │   ├── transaction.py  # Transaction implementation (234 lines)
│   │   └── transaction_stubs.py  # Transaction type stubs (34 lines)
│   │
│   ├── ui/  # UI element models
│   │   ├── __init__.py  # UI module initialization (0 lines)
│   │   └── ui_elements.py  # UI element definitions (1294 lines)
│   │
│   └── utils/  # Model utilities
│       ├── __init__.py  # Utils initialization (18 lines)
│       ├── base.py  # Base model utilities (89 lines)
│       ├── common.py  # Common utilities (429 lines)
│       ├── config.py  # Configuration utilities (67 lines)
│       ├── errors.py  # Error definitions (394 lines)
│       ├── logging.py  # Logging utilities (45 lines)
│       ├── scope.py  # Scope management (123 lines)
│       ├── type.py  # Type utilities (198 lines)
│       ├── type_system.py  # Type system implementation (307 lines)
│       ├── utils.py  # General utilities (167 lines)
│       ├── validation.py  # Validation utilities (89 lines)
│       └── validators.py  # Validator implementations (234 lines)
│
├── parse/  # PowerBuilder parsing module
│   ├── __init__.py  # Parse module initialization (15 lines)
│   ├── base_parser.py  # Base parser class (123 lines)
│   ├── constants.py  # Parser constants (56 lines)
│   ├── debug.py  # Debug utilities for parser (78 lines)
│   ├── errors.py  # Parser error definitions (98 lines)
│   ├── exceptions.py  # Parser exceptions (67 lines)
│   ├── grammar.py  # Grammar handling (89 lines)
│   ├── interactive.py  # Interactive parsing utilities (313 lines)
│   ├── logging.py  # Parser logging (45 lines)
│   ├── parse_coordinator.py  # Coordinates parsing pipeline (445 lines)
│   ├── parse_schema.py  # Schema parsing (156 lines)
│   ├── parse_ui.py  # UI parsing utilities (189 lines)
│   ├── parser.py  # Main parser implementation (267 lines)
│   ├── pb_preprocessor.py  # PowerBuilder preprocessor (335 lines)
│   ├── powerbuilder.py  # PowerBuilder-specific parsing (234 lines)
│   ├── pseudocode.lark  # Pseudocode grammar definition (89 lines)
│   ├── pseudocode_parser.py  # Pseudocode parser (178 lines)
│   ├── pseudocode_transformer.py  # Pseudocode AST transformer (512 lines)
│   ├── sql_parser.py  # SQL parsing (546 lines)
│   │
│   ├── grammar/  # Grammar definitions
│   │   ├── common_grammar.lark  # Common grammar rules (145 lines)
│   │   ├── datawindow.lark  # DataWindow grammar (267 lines)
│   │   ├── datawindow_grammar.lark  # Full DataWindow grammar (189 lines)
│   │   ├── powerbuilder.lark  # Main PowerBuilder grammar (583 lines)
│   │   ├── powerbuilder_core.lark  # Core PB grammar (234 lines)
│   │   ├── powerbuilder_js.lark  # JavaScript-style PB grammar (156 lines)
│   │   ├── sql.lark  # SQL grammar (198 lines)
│   │   ├── sql_grammar.lark  # Extended SQL grammar (223 lines)
│   │   └── window_grammar.lark  # Window definition grammar (134 lines)
│   │
│   └── visitors/  # AST visitors
│       ├── __init__.py  # Visitors initialization (0 lines)
│       ├── abstract_visitor.py  # Abstract visitor base class (490 lines)
│       ├── code_rewrite.py  # Code rewriting visitor (234 lines)
│       ├── entity_creator.py  # Entity creation visitor (494 lines)
│       ├── famix_importer.py  # FAMIX import visitor (178 lines)
│       ├── model_generator.py  # Model generation visitor (345 lines)
│       ├── pb_function.py  # Function parsing visitor (223 lines)
│       ├── pb_js_transformer.py  # JavaScript-style transformer (189 lines)
│       ├── pb_transformer.py  # PowerBuilder transformer (267 lines)
│       ├── pb_types.py  # Type parsing visitor (145 lines)
│       ├── position_tracker.py  # Source position tracking (98 lines)
│       ├── sql_transformer.py  # SQL AST transformer (1723 lines)
│       └── transformer.py  # Main AST transformer (1028 lines)
│
├── scripts/  # Utility scripts
│   ├── analyze_missing_opcodes.py  # Analyzes missing opcodes (156 lines)
│   ├── clean.sh  # Cleanup script (18 lines)
│   ├── debug_pbd_entries_summary.py  # Summarizes PBD entries (98 lines)
│   ├── debug_pcode_detection_detailed.py  # Detailed PCode detection debug (234 lines)
│   ├── debug_pcode_extraction.py  # PCode extraction debugging (189 lines)
│   ├── debug_pcode_extraction_simple.py  # Simple PCode extraction debug (123 lines)
│   ├── debug_pcode_final.py  # Final PCode debugging (167 lines)
│   ├── download_all_resources.sh  # Downloads all resources (34 lines)
│   ├── pcode_extraction_debug_report.md  # PCode extraction debug report (145 lines)
│   ├── setup_dev.sh  # Development environment setup (67 lines)
│   ├── test_full_pipeline.py  # Full pipeline testing (234 lines)
│   ├── test_pcode_detection_logic.py  # PCode detection testing (178 lines)
│   ├── update_opcodes_from_verified.py  # Updates opcodes (156 lines)
│   ├── verify_opcode_mappings.py  # Verifies opcode mappings (198 lines)
│   │
│   ├── debugging/  # Debugging utilities
│   │   ├── debug_entry_33.py  # Debug specific entry 33 (89 lines)
│   │   └── debug_nod_size.py  # Debug NOD size issues (78 lines)
│   │
│   └── testing/  # Testing scripts
│       ├── test_enhanced_decompiler.py  # Tests enhanced decompiler (256 lines)
│       ├── test_enhanced_decompiler_debug.py  # Debug enhanced decompiler (189 lines)
│       └── test_pcode_extraction.py  # Tests PCode extraction (234 lines)
│
├── tests/  # Test suite
│   ├── conftest.py  # Pytest configuration (98 lines)
│   ├── test_common.py  # Common test utilities (329 lines)
│   ├── test_errors.py  # Error handling tests (67 lines)
│   ├── test_extract.py  # Extraction tests (145 lines)
│   ├── test_main.py  # Main entry point tests (89 lines)
│   ├── test_pbd_extraction.py  # PBD extraction tests (234 lines)
│   ├── test_pbd_extraction_simple.py  # Simple PBD extraction tests (156 lines)
│   ├── test_pbd_fixtures.py  # PBD test fixtures (178 lines)
│   ├── test_type_system.py  # Type system tests (267 lines)
│   ├── test_validation.py  # Validation tests (123 lines)
│   ├── test_validators.py  # Validator tests (189 lines)
│   ├── verify_imports.py  # Import verification (78 lines)
│   │
│   ├── fixtures/  # Test fixtures
│   │   ├── __init__.py  # Fixtures initialization (0 lines)
│   │   ├── custom_control.sru  # Custom control fixture (45 lines)
│   │   ├── globals.sra  # Global variables fixture (34 lines)
│   │   ├── main_menu.srm  # Menu fixture (67 lines)
│   │   ├── simple_window.srw  # Window fixture (89 lines)
│   │   ├── test_tj_report_structured.pb  # Structured report fixture (123 lines)
│   │   │
│   │   ├── pbd_files/  # PBD test files
│   │   │   └── (binary test files)
│   │   │
│   │   └── pcode_files/  # PCode test files
│   │       ├── test.pcode  # Basic PCode test (23 lines)
│   │       ├── test_debug.pcode  # Debug PCode test (34 lines)
│   │       ├── test_decode.pcode  # Decode test (45 lines)
│   │       ├── test_tj_report.pcode  # Report PCode test (67 lines)
│   │       ├── test_update_coa.pcode  # Update COA test (56 lines)
│   │       ├── test_update_utf8.pcode  # UTF-8 update test (38 lines)
│   │       └── test_username.pcode  # Username test (29 lines)
│   │
│   ├── generate/  # Generation tests
│   │   ├── test_python.py  # Python generation tests (189 lines)
│   │   └── test_system_functions_template.py  # System functions template tests (145 lines)
│   │
│   ├── opcode_verification/  # Opcode verification tests
│   │   └── test_opcodes.py  # Opcode testing (234 lines)
│   │
│   ├── parse/  # Parser tests
│   │   ├── test_arrays.py  # Array parsing tests (178 lines)
│   │   ├── test_control_structures.py  # Control structure tests (489 lines)
│   │   ├── test_core_grammar.py  # Core grammar tests (234 lines)
│   │   ├── test_debug.py  # Debug functionality tests (123 lines)
│   │   ├── test_direct_grammar.py  # Direct grammar tests (156 lines)
│   │   ├── test_functions.py  # Function parsing tests (267 lines)
│   │   ├── test_interactive.py  # Interactive parsing tests (189 lines)
│   │   ├── test_io.py  # I/O parsing tests (145 lines)
│   │   ├── test_parse.py  # General parsing tests (223 lines)
│   │   ├── test_pb_direct.py  # Direct PB parsing tests (198 lines)
│   │   ├── test_pb_grammar.py  # PB grammar tests (267 lines)
│   │   ├── test_pb_js_transformer.py  # JS transformer tests (189 lines)
│   │   ├── test_pseudocode_examples.py  # Pseudocode example tests (375 lines)
│   │   ├── test_pseudocode_parser.py  # Pseudocode parser tests (234 lines)
│   │   ├── test_pseudocode_transformer.py  # Pseudocode transformer tests (444 lines)
│   │   ├── test_simple_grammar.py  # Simple grammar tests (123 lines)
│   │   ├── test_simple_pb.py  # Simple PB tests (145 lines)
│   │   ├── test_sql_parser.py  # SQL parser tests (1297 lines)
│   │   ├── test_type.py  # Type parsing tests (178 lines)
│   │   ├── test_type_system.py  # Type system tests (320 lines)
│   │   └── test_very_simple.py  # Very simple tests (89 lines)
│   │
│   ├── test_app/  # Application tests
│   │   ├── __init__.py  # App tests initialization (0 lines)
│   │   ├── conftest.py  # App test configuration (45 lines)
│   │   ├── test_access_tracking.py  # Access tracking tests (123 lines)
│   │   └── test_application.py  # Application tests (189 lines)
│   │
│   ├── test_ast/  # AST tests
│   │   ├── __init__.py  # AST tests initialization (0 lines)
│   │   ├── conftest.py  # AST test configuration (67 lines)
│   │   ├── test_events.py  # Event AST tests (234 lines)
│   │   ├── test_expressions.py  # Expression AST tests (298 lines)
│   │   ├── test_nodes.py  # Node tests (189 lines)
│   │   ├── test_sql.py  # SQL AST tests (223 lines)
│   │   ├── test_statements.py  # Statement AST tests (267 lines)
│   │   └── test_types.py  # Type AST tests (178 lines)
│   │
│   ├── test_decompile/  # Decompilation tests
│   │   ├── __init__.py  # Decompile tests initialization (0 lines)
│   │   ├── test_control_flow_enhanced.py  # Enhanced control flow tests (234 lines)
│   │   ├── test_expression_lifter.py  # Expression lifter tests (309 lines)
│   │   ├── test_output_formatter.py  # Output formatter tests (189 lines)
│   │   ├── test_pcode_decoder_v2.py  # PCode decoder v2 tests (256 lines)
│   │   ├── test_pcode_detector_enhanced.py  # Enhanced detector tests (223 lines)
│   │   └── test_stack_emulator_v2.py  # Stack emulator v2 tests (312 lines)
│   │
│   ├── test_generate/  # Generation tests
│   │   ├── __init__.py  # Generate tests initialization (0 lines)
│   │   ├── test_code_generator.py  # Code generator tests (310 lines)
│   │   └── test_jinja_filters.py  # Jinja filter tests (145 lines)
│   │
│   ├── test_model/  # Model tests
│   │   ├── __init__.py  # Model tests initialization (0 lines)
│   │   ├── conftest.py  # Model test configuration (89 lines)
│   │   ├── test_ast_nodes.py  # AST node model tests (319 lines)
│   │   ├── test_attribute.py  # Attribute model tests (156 lines)
│   │   ├── test_behavioral.py  # Behavioral model tests (411 lines)
│   │   ├── test_datawindow.py  # DataWindow model tests (234 lines)
│   │   ├── test_distributed_transaction.py  # Distributed transaction tests (189 lines)
│   │   ├── test_example_model.py  # Example model tests (145 lines)
│   │   ├── test_file.py  # File model tests (167 lines)
│   │   ├── test_global_variables.py  # Global variable tests (123 lines)
│   │   ├── test_pb_base.py  # Base PB model tests (198 lines)
│   │   ├── test_pb_behavioral.py  # PB behavioral tests (234 lines)
│   │   ├── test_pb_custom_call_statement.py  # Custom call tests (156 lines)
│   │   ├── test_pb_custom_type_node.py  # Custom type tests (178 lines)
│   │   ├── test_pb_data_component_node.py  # Data component tests (145 lines)
│   │   ├── test_pb_data_window_file_node.py  # DataWindow file tests (167 lines)
│   │   ├── test_pb_data_window_node.py  # DataWindow node tests (189 lines)
│   │   ├── test_pb_declare_cursor_node.py  # Cursor declaration tests (123 lines)
│   │   ├── test_pb_declare_procedure_node.py  # Procedure declaration tests (134 lines)
│   │   ├── test_pb_default_event_type_node.py  # Default event tests (112 lines)
│   │   ├── test_pb_default_variable_node.py  # Default variable tests (98 lines)
│   │   ├── test_pb_descriptor_node.py  # Descriptor tests (156 lines)
│   │   ├── test_pb_destroy_statement_node.py  # Destroy statement tests (123 lines)
│   │   ├── test_pb_do_loop_until_node.py  # Do-until loop tests (145 lines)
│   │   ├── test_pb_do_loop_while_node.py  # Do-while loop tests (134 lines)
│   │   ├── test_pb_do_until_loop_node.py  # Do-until tests (123 lines)
│   │   ├── test_pb_do_while_loop_node.py  # Do-while tests (134 lines)
│   │   ├── test_pb_dynamic_method_invocation_node.py  # Dynamic method tests (167 lines)
│   │   ├── test_pb_else_if_node.py  # Else-if tests (112 lines)
│   │   ├── test_pb_else_node.py  # Else tests (98 lines)
│   │   ├── test_pb_else_on_line_node.py  # Else on line tests (89 lines)
│   │   ├── test_pb_end_forward_node.py  # End forward tests (78 lines)
│   │   ├── test_pb_event_attribute_node.py  # Event attribute tests (134 lines)
│   │   ├── test_pb_event_declaration_node.py  # Event declaration tests (156 lines)
│   │   ├── test_pb_event_invocation_node.py  # Event invocation tests (145 lines)
│   │   ├── test_pb_event_long_node.py  # Event long tests (123 lines)
│   │   ├── test_pb_event_name_node.py  # Event name tests (98 lines)
│   │   ├── test_pb_event_reference_name_node.py  # Event reference tests (112 lines)
│   │   ├── test_pb_expression.py  # Expression tests (267 lines)
│   │   ├── test_pb_function_argument_node.py  # Function argument tests (145 lines)
│   │   ├── test_pb_sql.py  # SQL tests (234 lines)
│   │   ├── test_pb_type.py  # Type tests (189 lines)
│   │   ├── test_source_anchor.py  # Source anchor tests (98 lines)
│   │   ├── test_specialized_controls.py  # Specialized control tests (757 lines)
│   │   ├── test_system_events.py  # System event tests (234 lines)
│   │   ├── test_system_functions.py  # System function tests (298 lines)
│   │   ├── test_transaction.py  # Transaction tests (223 lines)
│   │   ├── test_transaction_error_handling.py  # Transaction error tests (189 lines)
│   │   ├── test_treeview_control.py  # TreeView control tests (319 lines)
│   │   ├── test_ui.py  # UI tests (234 lines)
│   │   └── test_utils.py  # Utility tests (548 lines)
│   │
│   ├── test_parse/  # Parse module tests
│   │   ├── __init__.py  # Parse tests initialization (0 lines)
│   │   ├── conftest.py  # Parse test configuration (78 lines)
│   │   ├── test_constants.py  # Constants tests (98 lines)
│   │   ├── test_core_grammar.py  # Core grammar tests (234 lines)
│   │   ├── test_event_parser.py  # Event parser tests (189 lines)
│   │   ├── test_globals.py  # Global parsing tests (145 lines)
│   │   ├── test_menu.py  # Menu parsing tests (167 lines)
│   │   ├── test_parser.py  # Parser tests (223 lines)
│   │   ├── test_pb_preprocessor.py  # Preprocessor tests (198 lines)
│   │   ├── test_powerbuilder_parser.py  # PowerBuilder parser tests (332 lines)
│   │   ├── test_pseudocode.py  # Pseudocode tests (349 lines)
│   │   ├── test_sql_parser.py  # SQL parser tests (267 lines)
│   │   ├── test_user_object.py  # User object tests (189 lines)
│   │   └── test_window.py  # Window parsing tests (234 lines)
│   │
│   └── test_utils/  # Utility tests
│       ├── __init__.py  # Utils tests initialization (0 lines)
│       ├── conftest.py  # Utils test configuration (45 lines)
│       ├── test_type.py  # Type utility tests (156 lines)
│       └── test_type_system.py  # Type system tests (189 lines)
│
├── input/  # Input files and resources
│   ├── schema.json  # PowerBuilder schema definition (1985 lines)
│   │
│   └── pbd_files/  # PBD input files
│       └── project-tree.txt  # Project structure reference (2666 lines)
│
├── output/  # Generated output directory
│   ├── __init__.py  # Output module initialization (0 lines)
│   │
│   ├── debug_pcode_simple/  # Simple PCode debug output
│   │   └── pcode_detection_simple.txt  # Simple detection results (123 lines)
│   │
│   ├── opcode_backups/  # Opcode definition backups
│   │   ├── opcodes_20250531_170702_initial.yaml  # Initial backup (3880 lines)
│   │   ├── opcodes_20250531_171312_initial.yaml  # Second backup (3880 lines)
│   │   ├── opcodes_20250603_135722_initial.yaml  # Third backup (3952 lines)
│   │   ├── opcodes_20250603_143617_initial.yaml  # Fourth backup (3952 lines)
│   │   ├── opcodes_20250603_144324_initial.yaml  # Fifth backup (4288 lines)
│   │   └── opcodes_20250603_144403_initial.yaml  # Latest backup (4294 lines)
│   │
│   └── opcode_discovery_reports/  # Opcode discovery results
│       ├── discovery_report_20250531_170703.json  # First discovery (234 lines)
│       ├── discovery_report_20250531_171313.json  # Second discovery (245 lines)
│       ├── discovery_report_20250603_135726.json  # Third discovery (267 lines)
│       ├── discovery_report_20250603_143621.json  # Fourth discovery (278 lines)
│       └── discovery_report_20250603_144328.json  # Latest discovery (289 lines)
│
├── reference/  # Reference implementations and documentation
│   ├── __init__.py  # Reference module initialization (0 lines)
│   ├── file_index.txt  # File index reference (156 lines)
│   ├── opcode_reference.json  # JSON opcode reference (8789 lines)
│   ├── opcode_reference.yaml  # YAML opcode reference (7117 lines)
│   │
│   ├── implementations/  # Reference implementations
│   │   └── Opcodes.cs  # C# opcode implementation (234 lines)
│   │
│   ├── decompilers/  # Reference decompiler implementations
│   │   ├── pbdviewer/  # PBD Viewer C# implementation
│   │   │   └── (C# implementation files)
│   │   │
│   │   └── powerbuilder-decompile/  # Python reference decompiler
│   │       ├── README.md  # Decompiler documentation (89 lines)
│   │       ├── analyse.py  # Analysis script (178 lines)
│   │       ├── analyse_folder.py  # Folder analysis (145 lines)
│   │       ├── pbd_analyse.py  # PBD analysis (234 lines)
│   │       ├── pbd_dump.py  # PBD dumping (189 lines)
│   │       │
│   │       └── pbd/  # PBD handling module
│   │           ├── __init__.py  # Module initialization (0 lines)
│   │           ├── definitions.py  # PBD definitions (1201 lines)
│   │           ├── old_system_enums.py  # Old system enumerations (347 lines)
│   │           ├── pcode.py  # PCode handling (1264 lines)
│   │           ├── system_enums.py  # System enumerations (1635 lines)
│   │           ├── system_functions.py  # System functions (4279 lines)
│   │           └── types.py  # Type definitions (347 lines)
│   │
│   ├── pb_code_examples/  # PowerBuilder code examples by version
│   │   ├── README.md  # Examples documentation (45 lines)
│   │   ├── PowerBuilder 6.0/  # PB 6.0 examples
│   │   ├── PowerBuilder 6.5/  # PB 6.5 examples
│   │   ├── PowerBuilder 7.0/  # PB 7.0 examples
│   │   ├── PowerBuilder 8.0/  # PB 8.0 examples
│   │   ├── PowerBuilder 9.0/  # PB 9.0 examples
│   │   ├── PowerBuilder 10.0/  # PB 10.0 examples
│   │   ├── PowerBuilder 10.5/  # PB 10.5 examples
│   │   ├── PowerBuilder 11.0/  # PB 11.0 examples
│   │   ├── PowerBuilder 11.2/  # PB 11.2 examples
│   │   ├── PowerBuilder 11.5/  # PB 11.5 examples
│   │   ├── PowerBuilder 12.0/  # PB 12.0 examples
│   │   ├── PowerBuilder 12.1/  # PB 12.1 examples
│   │   ├── PowerBuilder 12.5/  # PB 12.5 examples
│   │   ├── PowerBuilder 12.6/  # PB 12.6 examples
│   │   ├── PowerBuilder 15.0/  # PB 15.0 examples
│   │   ├── PowerBuilder 2017/  # PB 2017 examples
│   │   ├── PowerBuilder 2017R2/  # PB 2017R2 examples
│   │   ├── PowerBuilder 2017R3/  # PB 2017R3 examples
│   │   ├── PowerBuilder 2018/  # PB 2018 examples
│   │   ├── PowerBuilder 2019/  # PB 2019 examples
│   │   ├── PowerBuilder 2019 R2/  # PB 2019R2 examples
│   │   ├── PowerBuilder 2019 R3/  # PB 2019R3 examples
│   │   ├── PowerBuilder 2021_1288/  # PB 2021 build 1288
│   │   ├── PowerBuilder 2021_1311/  # PB 2021 build 1311
│   │   ├── PowerBuilder 2021_1506/  # PB 2021 build 1506
│   │   ├── PowerBuilder 2021_1509/  # PB 2021 build 1509
│   │   ├── PowerBuilder 2022_1716/  # PB 2022 build 1716
│   │   ├── PowerBuilder 2022_1878/  # PB 2022 build 1878
│   │   └── PowerBuilder 2022_1892/  # PB 2022 build 1892
│   │
│   ├── pbdviewer/  # PBD Viewer reference implementation
│   │   ├── README.md  # PBD Viewer documentation (67 lines)
│   │   ├── App.xaml  # WPF application definition (12 lines)
│   │   ├── App.xaml.cs  # Application code-behind (34 lines)
│   │   ├── MainWindow.xaml  # Main window XAML (89 lines)
│   │   ├── MainWindow.xaml.cs  # Main window code-behind (234 lines)
│   │   ├── PbdViewer.csproj  # C# project file (78 lines)
│   │   ├── PbdViewer.sln  # Visual Studio solution (23 lines)
│   │   │
│   │   ├── DataModel/  # Data model classes
│   │   │   ├── ControlNode.cs  # Control node model (89 lines)
│   │   │   ├── DirectoryNode.cs  # Directory node model (67 lines)
│   │   │   ├── EntryNode.cs  # Entry node model (123 lines)
│   │   │   ├── ExternalFunctionsNode.cs  # External functions model (98 lines)
│   │   │   ├── FileNode.cs  # File node model (145 lines)
│   │   │   ├── FunctionNode.cs  # Function node model (178 lines)
│   │   │   ├── NodeType.cs  # Node type enumeration (45 lines)
│   │   │   ├── StructureNode.cs  # Structure node model (134 lines)
│   │   │   ├── TreeNode.cs  # Tree node base class (234 lines)
│   │   │   └── VariablesNode.cs  # Variables node model (112 lines)
│   │   │
│   │   ├── Properties/  # Project properties
│   │   │   ├── AssemblyInfo.cs  # Assembly information (34 lines)
│   │   │   ├── Resources.cs  # Resource definitions (23 lines)
│   │   │   └── Settings.Designer.cs  # Settings designer (67 lines)
│   │   │
│   │   ├── Uitils/  # Utility classes
│   │   │   ├── BufferHelper.cs  # Buffer handling utilities (189 lines)
│   │   │   ├── CodeArea.cs  # Code area representation (234 lines)
│   │   │   ├── CodeLine.cs  # Code line representation (98 lines)
│   │   │   ├── JmpType.cs  # Jump type enumeration (34 lines)
│   │   │   ├── PCodeHelper.cs  # PCode helper utilities (298 lines)
│   │   │   ├── PEHelper.cs  # PE file utilities (156 lines)
│   │   │   │
│   │   │   ├── PCode/  # PCode parsers
│   │   │   │   ├── PCodeParser90.cs  # PB 9.0 PCode parser (234 lines)
│   │   │   │   ├── PCodeParser100.cs  # PB 10.0 PCode parser (256 lines)
│   │   │   │   ├── PCodeParser105.cs  # PB 10.5 PCode parser (267 lines)
│   │   │   │   ├── PCodeParser110.cs  # PB 11.0 PCode parser (278 lines)
│   │   │   │   └── PCodeParserBase.cs  # Base PCode parser (345 lines)
│   │   │   │
│   │   │   └── PbClass/  # PowerBuilder class models
│   │   │       ├── PbEntry.cs  # PB entry class (189 lines)
│   │   │       ├── PbEnum.cs  # PB enumeration (67 lines)
│   │   │       ├── PbFile.cs  # PB file representation (234 lines)
│   │   │       ├── PbFunction.cs  # PB function class (267 lines)
│   │   │       ├── PbFunctionDefinition.cs  # Function definition (156 lines)
│   │   │       ├── PbFunctionFlag.cs  # Function flags (45 lines)
│   │   │       ├── PbFunctionParam.cs  # Function parameters (98 lines)
│   │   │       ├── PbObject.cs  # PB object base class (298 lines)
│   │   │       ├── PbProject.cs  # PB project class (178 lines)
│   │   │       ├── PbReferencedFunction.cs  # Referenced functions (123 lines)
│   │   │       ├── PbType.cs  # PB type definitions (234 lines)
│   │   │       ├── PbVariable.cs  # PB variable class (189 lines)
│   │   │       └── PbVariableFlag.cs  # Variable flags (56 lines)
│   │   │
│   │   └── ViewModel/  # View models
│   │       └── WindowViewModel.cs  # Main window view model (345 lines)
│   │
│   ├── powerbuilder-decompile/  # Duplicate reference (see decompilers/)
│   │
│   ├── datawindow_docs/  # DataWindow documentation
│   ├── pb_users_guide/  # PowerBuilder user guides
│   ├── pblib_mirror/  # PowerBuilder library mirror
│   ├── pbni_docs/  # PowerBuilder Native Interface docs
│   ├── sap_forum_export/  # SAP forum exports
│   └── stackexchange_pbvm/  # StackExchange PB VM discussions
│
├── logs/  # Log files directory
│   └── unknown_opcodes.log  # Unknown opcodes log (234 lines)
│
├── backup/  # Backup directory
│   └── pipeline_results/  # Pipeline result backups
│
├── htmlcov/  # Coverage report HTML files
│
├── sime_finch.egg-info/  # Package distribution info
│
├── opcode_analysis_report.md  # Opcode analysis report (298 lines)
├── opcode_analysis_summary.md  # Opcode analysis summary (156 lines)
├── .markdownlint.json  # Markdown linting configuration (12 lines)
└── Makefile  # Build automation (34 lines)
```

## Summary

The SIME Finch project is a comprehensive PowerBuilder reverse engineering tool that:

1. **Extracts** PowerBuilder binary files (PBL/PBD) into readable formats
2. **Parses** PowerBuilder source code into Abstract Syntax Trees
3. **Decompiles** PowerBuilder PCode into structured pseudocode
4. **Generates** modern web applications (Litestar backend, React/Astro frontend)

The project is well-organized with clear separation of concerns:
- `extract/` - Binary file extraction
- `parse/` - Source code parsing
- `decompile/` - PCode decompilation
- `generate/` - Code generation
- `model/` - AST and data models
- `tests/` - Comprehensive test suite
- `reference/` - Reference implementations and documentation
- `docs/` - Project documentation