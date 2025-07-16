# Python File Inventory for src/ Directory

## Overview
This document provides a comprehensive inventory of all Python files in the src/ directory, organized by module, with descriptions of their purpose and identification of potential duplicates or files that could be merged.

## Executive Summary

### Key Findings:
1. **Significant Redundancy**: Multiple duplicate coordinators, incomplete migrations, and overlapping functionality
2. **Over-Engineering**: Common module contains many experimental features that may not be actively used
3. **Complex Hierarchies**: Deep nesting in generate and model modules makes navigation difficult
4. **Incomplete Refactoring**: Several modules show signs of partial refactoring with old and new implementations coexisting

### Top Priority Actions:
1. **Remove Duplicate Coordinators**: Both generate and model modules have duplicate coordinator files
2. **Complete Extraction Migration**: Legacy extraction folder still being used despite newer extractors implementation
3. **Consolidate Common Module**: Reduce from 20+ files to ~10 core files by removing experimental features
4. **Flatten Converter Hierarchy**: Simplify deep nesting in generate module converters

### Potential Impact:
- **File Reduction**: From ~300+ to ~150-200 files (40-50% reduction)
- **Improved Maintainability**: Clearer module boundaries and less duplication
- **Better Performance**: Fewer files to import and process

## Summary Statistics
- Total Python files in src/: ~300+ files
- Main modules: base (3), common (20+), contracts (9), decompile (30+), extract (40+), generate (50+), model (50+), parse (40+), pipeline (4)

## Module Organization

### 1. Base Module (`src/base/`)
Core interfaces and types used across the entire project.

**Files:**
- `__init__.py` - Module initialization
- `interfaces.py` - Core interface definitions for the project
- `types.py` - Base type definitions used throughout the system

### 2. Common Module (`src/common/`)
Shared utilities and infrastructure components.

**Core Files:**
- `__init__.py` - Module initialization
- `cache.py` - Caching infrastructure
- `constants.py` - Project-wide constants
- `core_utils.py` - Core utility functions
- `exceptions.py` - Common exception definitions
- `limits.py` - Resource limit definitions
- `security.py` - Security utilities

**Experimental/Advanced Features (potential for removal):**
- `async_coordinators.py` - Async coordination (may overlap with pipeline)
- `circuit_breaker.py` - Circuit breaker pattern implementation
- `dependency_injection.py` - DI framework (could be simplified)
- `distributed.py` - Distributed processing support
- `error_handling.py` - Error handling utilities (overlaps with exceptions.py)
- `event_bus.py` - Event bus implementation
- `parallel_pipeline.py` - Parallel pipeline execution
- `pipeline_streaming.py` - Streaming pipeline (overlaps with streaming.py)
- `state_management.py` - State management utilities
- `streaming.py` - Streaming support
- `streaming_pipeline.py` - Another streaming implementation

**Submodules:**
- `interfaces/__init__.py` - Interface definitions
- `patterns/__init__.py` - Design pattern implementations
- `pipeline/` - Pipeline infrastructure
  - `__init__.py`
  - `exceptions.py` - Pipeline-specific exceptions
  - `pipeline.py` - Core pipeline implementation
  - `pipeline_coordinator.py` - Pipeline coordination
  - `progress.py` - Progress tracking
  - `progress.pyi` - Type stubs for progress
- `types/` - Type definitions
  - `__init__.py`
  - `errors.py` - Error type definitions
  - `types.py` - Common type definitions
  - `types.pyi` - Type stubs
- `utils/` - Utility functions
  - `__init__.py`
  - `datawindow_utils.py` - DataWindow utilities
  - `error_recovery.py` - Error recovery utilities
  - `logging.py` - Logging utilities
  - `object_type_detector.py` - Object type detection

### 3. Contracts Module (`src/contracts/`)
Interface contracts for different components.

**Files:**
- `__init__.py` - Module initialization
- `decompilers.py` - Decompiler interfaces
- `events.py` - Event interfaces
- `extractors.py` - Extractor interfaces
- `generators.py` - Generator interfaces
- `models.py` - Model interfaces
- `parsers.py` - Parser interfaces
- `pipeline.py` - Pipeline interfaces
- `state.py` - State interfaces

### 4. Decompile Module (`src/decompile/`)
P-code decompilation to PowerBuilder source.

**Core Files:**
- `__init__.py` - Module initialization
- `coordinator.py` - Decompilation coordination
- `types.py` - Decompiler-specific types

**Submodules:**
- `analysis/` - Code analysis
  - `__init__.py`
  - `control_flow.py` - Control flow analysis
  - `data_flow.py` - Data flow analysis
- `analyzers/` - Code analyzers
  - `__init__.py`
  - `object_parser.py` - Object parsing
  - `schema_documentation_generator.py` - Schema documentation
- `core/` - Core decompilation
  - `__init__.py`
  - `output_formatter.py` - Output formatting
  - `output_validator.py` - Output validation
  - `post_processor.py` - Post-processing
  - `simple_formatter.py` - Simple formatting
  - `special_opcode_formatter.py` - Special opcode handling
- `extractors/` - Data extractors
  - `__init__.py`
  - `business_logic.py` - Business logic extraction
  - `database_schema_extractor.py` - Database schema extraction
  - `datawindow.py` - DataWindow extraction
  - `enhanced_datawindow_extractor.py` - Enhanced DataWindow extraction
  - `enhanced_datawindow_integration.py` - DataWindow integration
  - `schema.py` - Schema extraction
- `opcodes/` - Opcode definitions
  - `__init__.py`
  - `opcodes.py` - Main opcode definitions
  - `unknown_opcodes.py` - Unknown opcode handling
- `pcode/` - P-code handling
  - `__init__.py`
  - `decoder.py` - P-code decoder
  - `detector.py` - P-code detector
  - `recovery.py` - P-code recovery
  - `opcodes/` - P-code opcodes
    - `__init__.py`
    - `definitions.py` - Opcode definitions
    - `variants.py` - Opcode variants
- `reconstruction/` - Code reconstruction
  - `__init__.py`
  - `expression.py` - Expression reconstruction
  - `formatter.py` - Code formatting
- `visualization/` - Code visualization
  - `__init__.py`
  - `cfg_visualizer.py` - Control flow graph visualization

### 5. Extract Module (`src/extract/`)
PBL/PBD file extraction.

**Core Files:**
- `__init__.py` - Module initialization
- `coordinator.py` - Extraction coordination

**Submodules:**
- `pbd/` - PBD file handling
  - `__init__.py`
  - `constants.py` - PBD constants
  - `exceptions.py` - PBD exceptions
  - `formatters.py` - PBD formatters
  - `reader.py` - PBD file reader (MERGED FILE)
  - `scanner.py` - PBD scanner
  - `extraction/` - Extraction logic (LEGACY - mostly moved to extractors/)
    - `__init__.py`
    - `enhanced_image_extractor.py` - Image extraction
    - `extractor.py` - Base extractor
    - `library.py` - Library extraction
    - `resource_catalog.py` - Resource catalog
    - `resource_extraction_manager.py` - Resource management
    - `string_extractor.py` - String extraction
  - `extractors/` - Modern extractors
    - `__init__.py`
    - `base.py` - Base extractor class
    - `binary.py` - Binary extraction (MERGED FILE)
    - `resource.py` - Resource extraction
  - `io/` - I/O operations
    - `__init__.py`
    - `progress.py` - Progress tracking
    - `resource_utils.py` - Resource utilities
  - `recovery/` - Recovery mechanisms
    - `__init__.py`
    - `checkpoint.py` - Checkpoint recovery
    - `corruption.py` - Corruption recovery
  - `structures/` - Data structures
    - `__init__.py`
    - `data_block.py` - Data block structure
    - `entry.py` - Entry structure
    - `entry_recovery.py` - Entry recovery
    - `header.py` - Header structure
    - `node.py` - Node structure
    - `object.py` - Object structure
  - `utils/` - Utilities
    - `text_extraction.py` - Text extraction utilities
- `security/` - Security features
  - `__init__.py`
  - `extract_coordinator.py` - Secure extraction coordination
  - `path_validator.py` - Path validation
  - `resource_limiter.py` - Resource limiting
- `utils/` - General utilities
  - `__init__.py`
  - `binary.py` - Binary utilities
  - `encoding.py` - Encoding utilities
  - `version.py` - Version utilities

### 6. Generate Module (`src/generate/`)
Code generation for target languages.

**Core Files:**
- `__init__.py` - Module initialization
- `base_generator.py` - Base generator class
- `coordinator.py` - Generation coordination
- `coordinator_refactored.py` - Refactored coordinator (DUPLICATE?)
- `jinja_filters.py` - Jinja template filters
- `model_generator.py` - Model generation
- `python_ui_generator.py` - Python UI generation
- `service_generator.py` - Service generation
- `template_schemas.py` - Template schema definitions

**Submodules:**
- `builders/` - Code builders
  - `__init__.py`
- `converters/` - Language converters
  - `__init__.py`
  - `data/` - Data converters
    - `__init__.py`
    - `blob_converter.py` - BLOB conversion
    - `database_operation_formatter.py` - Database operation formatting
    - `relationship_extractor.py` - Relationship extraction
  - `flutter/` - Flutter converters
    - `__init__.py`
    - `business/` - Business logic
      - `__init__.py`
      - `logic_converter.py` - Logic conversion
    - `services/` - Service layer
      - `__init__.py`
      - `api_service.py` - API service generation
    - `state/` - State management
      - `__init__.py`
      - `event_converter.py` - Event conversion
      - `model_converter.py` - Model conversion
    - `ui/` - UI components
      - `__init__.py`
      - `datawindow_converter.py` - DataWindow conversion
      - `datawindow_enhancements.py` - DataWindow enhancements
      - `design_system_converter.py` - Design system conversion
      - `layout_converter.py` - Layout conversion
      - `menu_converter.py` - Menu conversion
      - `theme_converter.py` - Theme conversion
      - `widget_converter.py` - Widget conversion
  - `logic/` - Logic conversion
    - `__init__.py`
    - `application_converter.py` - Application conversion
    - `event_wiring.py` - Event wiring
  - `utils/` - Converter utilities
    - `__init__.py`
    - `ast_converter.py` - AST conversion
    - `expression_converter.py` - Expression conversion
    - `type_converter.py` - Type conversion
- `coordinators/` - Generation coordinators
  - `__init__.py`
  - `base.py` - Base coordinator
  - `flutter.py` - Flutter coordinator
  - `model.py` - Model coordinator
  - `service.py` - Service coordinator
- `extractors/` - AST extractors
  - `__init__.py`
  - `ast_extractor.py` - AST extraction
- `factories/` - Generator factories
  - `__init__.py`
  - `generator_factory.py` - Generator factory
- `processors/` - Code processors
  - `__init__.py`
  - `event_processor.py` - Event processing
  - `ui_processor.py` - UI processing
- `scaffolders/` - Project scaffolding
  - `__init__.py`
  - `project_scaffolder.py` - Project scaffolding
- `templates/` - Generation templates
  - `__init__.py`
  - `engine.py` - Template engine
  - `flutter/` - Flutter templates
    - `__init__.py`
  - `python/` - Python templates
    - `__init__.py`
    - `python.py` - Python generation

### 7. Model Module (`src/model/`)
AST and semantic model handling.

**Core Files:**
- `__init__.py` - Module initialization
- `coordinator.py` - Model coordination
- `coordinator_refactored.py` - Refactored coordinator (DUPLICATE?)

**Submodules:**
- `analysis/` - Model analysis
  - `__init__.py`
  - `cross_reference.py` - Cross-reference analysis
  - `security.py` - Security analysis
- `ast/` - AST definitions
  - `__init__.py`
  - `additional_nodes.py` - Additional AST nodes
  - `functions.py` - Function AST nodes
  - `io.py` - I/O AST nodes
  - `node_kind.py` - Node type definitions
  - `pb_types.py` - PowerBuilder types
  - `serialization.py` - AST serialization
  - `builders/` - AST builders
    - `__init__.py`
  - `nodes/` - AST node types
    - `__init__.py`
    - `base.py` - Base node types
    - `declarations.py` - Declaration nodes
    - `sql.py` - SQL nodes
  - `visitors/` - AST visitors
    - `__init__.py`
- `base/` - Base model classes
  - `__init__.py`
  - `pb_entity.py` - PowerBuilder entity base
- `constructs/` - Language constructs
  - `__init__.py`
  - `pb_access.py` - Access constructs
  - `pb_attribute_access.py` - Attribute access
- `entities/` - Model entities
  - `__init__.py`
  - `application.py` - Application model
  - `event.py` - Event model
  - `function.py` - Function model
  - `library.py` - Library model
  - `method_call.py` - Method call model
- `expressions/` - Expression handling
  - `__init__.py`
  - `ast_expressions.py` - AST expressions
  - `evaluator.py` - Expression evaluation
  - `pb_expressions.py` - PowerBuilder expressions
  - `reconstructor.py` - Expression reconstruction
- `optimization/` - Code optimization
  - `__init__.py`
  - `sql_optimizer.py` - SQL optimization
- `services/` - Model services
  - `__init__.py`
  - `ast_processor.py` - AST processing
  - `entity_factory.py` - Entity creation
  - `entity_validator.py` - Entity validation
  - `model_extractor.py` - Model extraction
  - `model_persistence.py` - Model persistence
  - `relationship_manager.py` - Relationship management
- `symbols/` - Symbol handling
  - `__init__.py`
  - `resolver.py` - Symbol resolution
  - `scope.py` - Scope management
  - `table.py` - Symbol table
- `system/` - System components
  - `__init__.py`
  - `events.py` - System events
  - `functions.py` - System functions
  - `globals.py` - Global definitions
- `transaction/` - Transaction handling
  - `__init__.py`
  - `distributed.py` - Distributed transactions
  - `error_handling.py` - Transaction error handling
  - `savepoint.py` - Savepoint management
  - `statement.py` - Transaction statements
  - `transaction.py` - Transaction model
- `transformers/` - Model transformers
  - `__init__.py`
  - `ast_to_model.py` - AST to model transformation
- `types/` - Type system
  - `__init__.py`
  - `inference.py` - Type inference
  - `validation.py` - Type validation
- `utils/` - Model utilities
  - `__init__.py`
  - `base.py` - Base utilities
  - `common.py` - Common utilities
  - `config.py` - Configuration utilities
  - `errors.py` - Error utilities
  - `type_checker.py` - Type checking
  - `validators.py` - Validation utilities
- `visitors/` - Model visitors
  - `__init__.py`
  - `ast_tree_visitor.py` - AST tree visitor
  - `ast_walker.py` - AST walker
  - `model_extractor_visitor.py` - Model extraction visitor

### 8. Parse Module (`src/parse/`)
PowerBuilder source code parsing.

**Core Files:**
- `__init__.py` - Module initialization
- `constants.py` - Parser constants
- `coordinator.py` - Parsing coordination
- `exceptions.py` - Parser exceptions
- `interfaces.py` - Parser interfaces
- `library.py` - Library parsing
- `type_resolution.py` - Type resolution
- `types.py` - Parser types

**Submodules:**
- `error_recovery/` - Error recovery
  - `__init__.py`
  - `strategy.py` - Recovery strategies
- `grammar/` - Grammar definitions
  - `__init__.py`
  - `loader.py` - Grammar loader
  - `definitions/` - Grammar files
    - `__init__.py`
    - `common_grammar.lark` - Common grammar
    - `powerbuilder.lark` - PowerBuilder grammar
    - `sql.lark` - SQL grammar
- `parser/` - Parser implementations
  - `__init__.py`
  - `base.py` - Base parser
  - `powerbuilder.py` - PowerBuilder parser (MERGED FILE)
  - `sql.py` - SQL parser
  - `specialized/` - Specialized parsers
    - `__init__.py`
    - `pseudocode_parser.py` - Pseudocode parser
    - `sql_parser.py` - SQL parser
    - `transaction_parser.py` - Transaction parser
    - `type_parser.py` - Type parser
- `preprocessor/` - Code preprocessing
  - `__init__.py`
  - `import_resolver.py` - Import resolution
  - `pb_preprocessor.py` - PowerBuilder preprocessing
- `transformer/` - AST transformation
  - `__init__.py`
  - `ast_builder.py` - AST building
  - `enhanced_type_transformer.py` - Type transformation
  - `sql_transformer.py` - SQL transformation
  - `type_resolver.py` - Type resolution
  - `visitors/` - Transformer visitors
    - `__init__.py`
    - `node_visitor.py` - Node visitor
    - `position_tracker.py` - Position tracking
- `utils/` - Parser utilities
  - `__init__.py`
  - `constants.py` - Utility constants
  - `exceptions.py` - Utility exceptions
  - `grammar_loader.py` - Grammar loading utilities
- `visitors/` - Parser visitors
  - `__init__.py`
  - `pb_js_transformer.py` - PowerBuilder to JS transformation
  - `sql_transformer.py` - SQL transformation
  - `transformer.py` - Base transformer

### 9. Pipeline Module (`src/pipeline/`)
Pipeline orchestration (appears minimal).

**Files:**
- `__init__.py` - Module initialization
- `execution/` - Pipeline execution
  - `__init__.py`
- `monitoring/` - Pipeline monitoring
  - `__init__.py`
- `stages/` - Pipeline stages
  - `__init__.py`

### 10. Examples Module (`src/examples/`)
Example usage code.

**Files:**
- `clean_architecture_usage.py` - Clean architecture example

## Identified Issues and Recommendations

### 1. Duplicate/Redundant Files

#### Confirmed Duplicates:
- **Generate Module**:
  - `coordinator.py` - Original coordinator using direct imports
  - `coordinator_refactored.py` - Refactored version using dependency injection
  - **Action**: Keep the refactored version as it follows better architectural patterns

- **Model Module**:
  - `coordinator.py` - Original coordinator
  - `coordinator_refactored.py` - Refactored version (likely duplicate of generate pattern)
  - **Action**: Review and keep the better implementation

- **Extraction Module**:
  - `src/extract/pbd/extraction/` - Legacy extraction implementations
  - `src/extract/pbd/extractors/` - Modern consolidated extractors
  - **Note**: The extractors still import from extraction folder, so migration is incomplete
  - **Action**: Complete migration to extractors and remove extraction folder

- **Common Module Streaming**:
  - `streaming.py` - Basic streaming utilities
  - `streaming_pipeline.py` - Streaming pipeline coordinator
  - `pipeline_streaming.py` - Pipeline streaming utilities
  - **Action**: Consolidate into a single streaming module

### 2. Files That Should Be Merged

#### Common Module:
- **Error Handling**: 
  - Merge `exceptions.py` and `error_handling.py` → `exceptions.py`
  - Both define error handling mechanisms
  
- **Pipeline Infrastructure**:
  - Move `pipeline_streaming.py` → `pipeline/streaming.py`
  - Consolidate all pipeline-related code in one place

- **Experimental Features** (consider removing if unused):
  - `async_coordinators.py`
  - `circuit_breaker.py` 
  - `distributed.py`
  - `event_bus.py`
  - `parallel_pipeline.py`
  - `state_management.py`

#### Extract Module:
- **PBD Extraction**:
  - Complete migration from `extraction/` to `extractors/`
  - Move: `enhanced_image_extractor.py`, `string_extractor.py`, `resource_extraction_manager.py` → `binary.py`
  - Move: `resource_catalog.py` → `resource.py`
  - Keep: `library.py` if still needed, otherwise integrate

- **Utilities**:
  - Consider merging `pbd/utils/text_extraction.py` with `utils/encoding.py`

#### Model Module:
- **Visitors**:
  - `visitors/` and `ast/visitors/` have similar purposes
  - Consider consolidating visitor patterns in one location

- **Type Handling**:
  - `types/` and `ast/pb_types.py` handle type definitions
  - Consider consolidating type system

- **Expression Handling**:
  - `expressions/ast_expressions.py` and `expressions/pb_expressions.py`
  - Could be merged into a single expression module

### 3. Overly Complex Areas

#### Common Module (20+ files):
- Too many experimental/advanced features
- Recommendation: Keep only actively used infrastructure
- Core files to keep: `cache.py`, `constants.py`, `exceptions.py`, `pipeline/`, `types/`, `utils/`

#### Generate Module Converters:
- Deep hierarchy: `converters/flutter/ui/`, `converters/flutter/business/`, etc.
- Consider flattening to: `converters/flutter_ui.py`, `converters/flutter_business.py`

#### Model Module (50+ files):
- Very complex structure with many small files
- Consider consolidating utilities and small helper files

### 4. Specific Merge Recommendations

#### Phase 1 - Quick Wins:
1. Remove `coordinator_refactored.py` duplicates after choosing best implementation
2. Complete extraction module migration and remove legacy folder
3. Merge common module error handling files
4. Consolidate streaming implementations

#### Phase 2 - Structural Improvements:
1. Flatten generate converter hierarchy
2. Consolidate model visitors
3. Merge related type definitions
4. Remove unused experimental features from common

#### Phase 3 - Major Consolidation:
1. Reduce common module to ~10 core files
2. Reduce model module complexity by merging utilities
3. Simplify parse module by consolidating parser variants

### 5. File Count Reduction Potential
- Current: ~300+ Python files
- Target: ~150-200 files (40-50% reduction)
- Biggest opportunities: common module (reduce by 50%), model module (reduce by 30%)

## Next Steps
1. Review each identified duplicate/redundant file
2. Create a consolidation plan
3. Update imports after consolidation
4. Remove unused experimental features
5. Document the final structure