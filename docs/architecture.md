Okay, here's a condensed and clearer version of the provided architecture overview, aiming to retain all essential information:

---

**Project Architecture & Pipeline Overview**

This document outlines the reverse-engineering project's architecture, detailing its pipeline, module interactions, and key components.

**1. Project Structure (Core Directories & Files)**

* **Input:** Raw PowerBuilder files and example fixtures.
* **Output:** All generated artifacts (extracted files, ASTs, pseudocode, generated code).
* **Main Script (`main.py`):** Orchestrates the CLI and subcommand execution.
* **Extract (`extract/`):** Extracts PBL/PBD artifacts into raw text and structured objects.
  * `pbd_core/`: Core logic for parsing PBD/PBL structures (header, nodes, entries, data blocks), PBD object representation, opcode handling, IR placeholders, symbol table placeholders, and PFC exclusion.
  * `pbd_io/`: Utilities for file operations, progress tracking, PBD/PE file scanning, and resource extraction.
  * `pbd_cli/`: Command-line interface for the extraction process.
* **Parse (`parse/`):** Lexes and parses raw PowerBuilder text into Abstract Syntax Trees (ASTs).
* **Model (`model/`):** Defines in-memory metamodel classes (using Python dataclasses).
* **Decompile (`decompile/`):** Performs structured decompilation of PCode into pseudocode.
* **Generate (`generate/`):** Generates backend and frontend code from metamodel instances.
* **Tests (`tests/`):** Pytest suite covering all modules.
* **Docs (`docs/`):** Documentation and design artifacts.

**2. Module Interactions & Capabilities**

* **Extraction Layer (`extract/`):**
  * **`Library` API (`extract.pbd_core.library.Library`):** Ergonomic, high-level API for PBD/PBL file interaction.
    * Manages a single file handle per PBD/PBL.
    * Parses header, NOD B-Tree, and ENT* entry definitions.
    * Provides access to individual `PbdObject` instances via `__getitem__`.
    * Offers `extract_all()` method to save all objects with progress tracking.
    * Implements context manager protocol for resource management.
  * **`PbdObject` (`extract.pbd_core.pbd_object.PbdObject`):** Represents a single extracted object.
    * Stores entry definition, data blocks, and status (e.g., `is_partial`).
    * Derives `raw_text_content` and `raw_pcode`.
    * Inflates zlib-compressed DataWindow syntax.
    * Extracts embedded resources (images) from `.srm` and other objects.
    * Calculates content hash for PFC exclusion.
  * **Format Resilience & Recovery:**
    * Signature-agnostic triage: Scans for HDR, NOD, DAT, ENT, FRE signatures if initial parsing fails.
    * Auto-detects block size (256/512/1024) from DAT* spacing.
    * Salvages partially recoverable objects (e.g., if DAT.next_offset is outside EOF).
    * Rebuilds a synthetic entry index by brute-scanning for ENT* signatures if NOD B-Tree is corrupt.
    * Detects and extracts embedded PBDs from PE files (via `extract.pbd_io.pe_scanner`).
  * **Resource Extraction (`extract.pbd_io.resource_utils`):**
    * Identifies and extracts embedded images (BMP, ICO, PNG, JPG, GIF) by parsing headers to determine size.
  * **Opcode & P-Code Infrastructure (Placeholders):**
    * Loads opcode definitions from `opcodes.yaml` (`extract.pbd_core.opcodes`).
    * Logs unknown opcodes with context.
    * Placeholder for symbolic execution fallback for unknown opcodes.
    * Basic Intermediate Representation (IR) node definitions (`extract.pbd_core.pcode_ir`).
  * **Symbol Table (Placeholder):**
    * Basic structures for symbols, scopes, and symbol table (`extract.pbd_core.symbol_table`).
  * **PFC Exclusion:**
    * Skips extraction/saving of objects matching known PFC SHA-1 hashes if enabled.
    * **Output:**
    * Exports objects in a deterministically sorted order (heuristic based on object type extension).
    * Saves extracted text, binary, and resource files.
* **Parser Layer:**
  * Comprehensive LARK grammar for PowerBuilder, including full DataWindow definitions, transaction blocks, try-catch-finally, and library definitions/imports.
* **Model Layer:**
  * Provides base AST node functionality and complete metamodels for DataWindows, transactions, exceptions, and libraries.
* **Analysis Layer:**
  * Generates call graphs, tracks data flow/variable dependencies, calculates code metrics, and produces visualizations (graphs, charts).
* **Code Generation Layer:**
  * **Backend:** REST/GraphQL APIs, database models, service layer.
  * **Frontend:** React/Astro components, form validation, API integration, error handling.

**3. Pipeline Workflow**

1. **Extraction:** Scans inputs (PBL/PBD or PE files containing PBDs).
    * The `Library` class opens the file, attempts to parse the header (with block size auto-detection and fallback to signature scanning).
    * It then reads the NOD B-Tree to find object entries, or brute-scans for ENT* signatures if the NOD tree is corrupt.
    * For each object:
        * Data blocks (DAT*) are read, handling partial reads if corruption is detected.
        * `PbdObject` instances are created.
        * DataWindow syntax within `PbdObject.raw_text_content` is inflated if zlib-compressed.
        * (If PFC exclusion is active) Object content is hashed; if it matches a PFC hash, the object is skipped.
        * Embedded resources (images) are extracted.
    * Objects are saved to the output directory in a deterministic order.
2. **Parsing:** Parses extracted source files using enhanced grammar, builds ASTs (with source location tracking), validates syntax, reports parse errors.
3. **Analysis:** Builds call graph, performs data flow analysis, calculates code metrics, generates visualizations.
4. **Generation:** Generates backend/frontend code, documentation, and test stubs.

**4. Future Enhancements (General Pipeline)**

* Additional CLI subcommands for comprehensive pipeline control.
* Expanded test suite for edge cases and robustness.
* Enhanced documentation with detailed examples and use cases.
* Support for more PowerBuilder features: advanced DataWindows, more transaction patterns, additional control types, system functions.

---

**PowerBuilder Metamodel Architecture (`model/` package)**

Model classes are organized into domain-specific subpackages under `model/`, with consolidated files and clear `__init__.py` exports for a clean public API.

**Package Organization:**

```
model/
├── ast/            # Abstract Syntax Tree nodes (expressions, statements, functions, etc.)
├── attribute/      # Attribute declarations, access, constant/readonly support
├── datawindow/     # DataWindow components (tables, columns, compute expressions, display)
├── transaction/    # Database transaction states, operations, savepoints
├── library/        # Library imports/exports, behavioral options/aliases
├── ui/             # UI components (windows, controls, menus, user objects)
├── source/         # Source code representation (files, positions, comments)
├── utils/          # Utility classes (base nodes, exceptions, validation)
├── analysis/       # Analysis tools (metrics, dependencies, call graphs)
└── __init__.py     # Public API exports
```

**Benefits:** Improved domain-based organization, reduced file count (~30+ to ~10), clearer dependencies, easier navigation/maintenance, simplified imports, and better discoverability. The public API allows importing specific components (e.g., `from model import Window`), entire domains (`from model.ui import *`), or utilities.

---

**Core Implementation Details & References**

**1. Code Origins & References**

* **Grammar & Parser Sources:**
  * **Primary:** `PSEUDOCODE_TO_PYTHON_TRANSLATOR` (core grammar, control flow, functions, basic I/O, types).
  * **Influences:**
    * `PyPse`: Enhanced arrays, multi-line comments, records, string literals, type inference.
    * `PseudocodeInterpreter`: CAIE-specific syntax, enhanced file/array operations, additional built-ins, error reporting.
    * `dudocode`: Enhanced control structures, error recovery, flexible syntax, enhanced type system, source mapping.
* **Template System (Jinja2):**
  * **Backend Templates:** Models (`generate/backend/templates/model.py.jinja2`), services (`.../service.py.jinja2`), decompiler (`decompile/templates/structured.py.jinja2`).
  * **Frontend Templates:** React (`generate/frontend/templates/component.tsx.jinja2`), Astro (`.../component.astro.jinja2`).

**2. Key Implementation Components**

* **Extractor (`extract/` module):**
  * **Core Parsing:** `extract.pbd_core.header`, `extract.pbd_core.node`, `extract.pbd_core.entry`, `extract.pbd_core.dat`.
  * **High-Level API:** `extract.pbd_core.library.Library`, `extract.pbd_core.pbd_object.PbdObject`.
  * **I/O & Scanning:** `extract.pbd_io.file_operations`, `extract.pbd_io.scanner`, `extract.pbd_io.pe_scanner`, `extract.pbd_io.resource_utils`.
  * **PFC Handling:** `extract.pbd_core.pfc_utils`.
  * **Opcode/IR/Symbol Stubs:** `extract.pbd_core.opcodes`, `extract.pbd_core.pcode_ir`, `extract.pbd_core.symbol_table`.
* **Parser:** Grammars (`parse/powerbuilder.lark`, `parse/pseudocode.lark`), infrastructure (`parse/parser.py`), transformer (`parse/pseudocode_transformer.py`).
* **Code Generation:** Model (`generate/backend/generate_models.py`), service (`.../generate_services.py`), component (`generate/frontend/generate_components.py`) generators.
* **Decompilation:** Structured decompiler (`decompile/decompile_structured.py`), type inference (`.../type_inference.py`), optimizer (`.../optimize.py`).

**3. Key Design Decisions**

* **Extraction Strategy:** Shifted from monolithic script to modular `pbd_core` (parsing logic, object representation), `pbd_io` (file/scanning utilities), and `pbd_cli`. Implemented a `Library` class as the primary API, focusing on robustness (corruption handling, signature scanning, block size detection) and feature completeness (PE scanning, resource extraction, DW inflation, PFC exclusion).
* **Grammar/Parsing:** Chose Lark (over ANTLR) for Python integration; enhanced with PowerBuilder specifics, error handling/recovery, and source location tracking.
* **Code Generation:** Used Jinja2 templates (separated by component type); implemented strict type checking and documentation generation.
* **Type System:** Enhanced inference from references; added PowerBuilder-specific/custom types and array bounds checking.
* **Error Handling:** Comprehensive hierarchy, source location tracking, contextual error messages, and debugging support.

**4. Testing Strategy**

* **Unit Tests:** Parser (`tests/parse/`), transformer (`.../transform/`), generator (`.../generate/`), template (`.../templates/`) tests.
* **Integration Tests:** End-to-end parsing, code generation, type system, and error handling tests.

**5. Future Improvements (Technical)**

* **High Priority:** Enhanced SQL query optimization, better transaction handling, comprehensive UI component mapping, more PowerBuilder-specific features.
* **Medium Priority:** Enhanced debugging, performance optimizations, additional analysis, documentation improvements.
* **Low Priority:** IDE integration, additional output formats, migration tools, compliance checking.

**6. PowerBuilder JS Grammar (Lark) Limitation**

* The grammar uses Lark's LALR parser with a contextual lexer.
* **Limitation:** Identifiers must not start with reserved keywords (e.g., `asc`, `lengthy`) due to Lark splitting such identifiers.
* **Workaround:** Use variable/function names not starting with keywords. For full robustness, a custom lexer or different parsing library would be needed.

---
