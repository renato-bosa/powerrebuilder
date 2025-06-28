# Decompile Module

## Overview

The Decompile module handles the decompilation of PowerBuilder compiled objects, particularly DataWindow objects (DWO/PDW files) and P-code analysis. It extracts meaningful source code and metadata from compiled binaries.

## Structure

```
decompile/
├── __init__.py
├── decompile_coordinator.py  # Main decompilation orchestrator
├── analyzers/               # Code analysis tools
│   ├── __init__.py
│   ├── business_logic_mapper.py    # Maps business logic patterns
│   ├── control_flow_analyzer.py    # Analyzes control flow
│   ├── object_parser.py           # Parses compiled objects
│   ├── pcode_detector.py          # Detects P-code sections
│   ├── pcode_detector_enhanced.py # Enhanced P-code detection
│   └── schema_documentation_generator.py
├── core/                    # Core decompilation logic
│   ├── __init__.py
│   ├── advanced_expression_reconstructor.py
│   ├── expression_reconstructor.py
│   ├── opcode_definitions.py      # P-code opcode mappings
│   ├── output_formatter.py        # Formats decompiled output
│   ├── pcode_decoder.py          # P-code decoder
│   ├── simple_formatter.py       # Simple output formatting
│   └── stack_emulator.py         # Stack-based VM emulator
├── extractors/              # Data extraction utilities
│   ├── __init__.py
│   ├── database_schema_extractor.py
│   ├── datawindow_extractor.py
│   ├── enhanced_datawindow_extractor.py
│   └── enhanced_datawindow_integration.py
├── pdw/                     # PDW-specific handling
│   ├── __init__.py
│   ├── enhanced_pdw_extractor.py
│   ├── pdw_blob_extractor.py
│   ├── pdw_comprehensive_extractor.py
│   ├── pdw_detector.py
│   ├── pdw_handler.py
│   └── pdw_sql_extractor.py
└── visualization/           # Visualization tools
    ├── __init__.py
    └── cfg_visualizer.py    # Control flow graph visualization
```

## Key Components

### P-code Decompilation

The module includes a sophisticated P-code decompiler:
- **Opcode Definitions**: Maps numeric opcodes to operations
- **Stack Emulator**: Simulates the P-code stack machine
- **Expression Reconstructor**: Rebuilds high-level expressions
- **Control Flow Analyzer**: Reconstructs program flow

### DataWindow Extraction

Specialized extractors for DataWindow objects:
- **DataWindowExtractor**: Basic DWO extraction
- **EnhancedDataWindowExtractor**: Advanced extraction with error recovery
- **PDW Handlers**: Handle compiled PDW format

### Code Analysis

- **Business Logic Mapper**: Identifies business logic patterns
- **Control Flow Analyzer**: Creates control flow graphs
- **Object Parser**: Parses compiled object structures

## Usage

```python
from decompile.decompile_coordinator import DecompileCoordinator

# Decompile a DataWindow
coordinator = DecompileCoordinator()
source = coordinator.decompile_datawindow("window.dwo")

# Decompile P-code
pcode_source = coordinator.decompile_pcode(compiled_data)
```

## P-code Opcodes

The module supports PowerBuilder P-code opcodes:

```python
# Example opcodes
0x00: "nop"         # No operation
0x01: "push_lit"    # Push literal
0x02: "push_var"    # Push variable
0x0E: "call"        # Function call
0x1C: "ret"         # Return
0x21: "jmp"         # Jump
0x22: "jz"          # Jump if zero
```

## DataWindow Format Support

- **DWO Files**: Text-based DataWindow objects
- **PDW Files**: Compiled DataWindow objects
- **SQL Extraction**: Extracts embedded SQL
- **Metadata Recovery**: Recovers column definitions

## Control Flow Analysis

The module can generate control flow graphs:

```python
from decompile.analyzers import ControlFlowAnalyzer
from decompile.visualization import CFGVisualizer

analyzer = ControlFlowAnalyzer()
cfg = analyzer.analyze_function(function_ast)

visualizer = CFGVisualizer()
visualizer.visualize(cfg, "output.png")
```

## Error Recovery

Robust error recovery mechanisms:
- Handles corrupted compiled files
- Partial decompilation support
- Magic number detection
- Position-based recovery

## Database Schema Extraction

Extracts database schema information:
- Table relationships
- Column definitions
- SQL operations
- Connection strings

## Dependencies

- Python 3.9+
- graphviz (optional, for CFG visualization)

## Related Modules

- **Extract**: Provides compiled files to decompile
- **Parse**: Further processes decompiled source
- **Model**: Creates AST from decompiled code
- **Generate**: Uses decompiled information