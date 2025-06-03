# SIME Finch Pipeline Architecture

## Overview

The SIME Finch pipeline processes PowerBuilder applications through five distinct stages:

```
┌─────────────┐    ┌──────────────┐    ┌─────────────┐    ┌─────────────┐    ┌──────────────┐
│   EXTRACT   │ → │   DECOMPILE   │ → │    PARSE    │ → │    MODEL    │ → │   GENERATE   │
└─────────────┘    └──────────────┘    └─────────────┘    └─────────────┘    └──────────────┘
     ↓                    ↓                   ↓                  ↓                   ↓
 PBL/PBD files       P-Code Binary      Source Files       AST Nodes         Modern Code
                     to Pseudocode      to AST Trees       (Shared)         (Web Apps)
```

## Detailed Module Breakdown

### 1. Extract Module (`/extract/`)

```
┌─────────────────────────────────────────────────────────────────────────┐
│                            EXTRACT MODULE                                │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                         │
│  Entry Points:                                                          │
│  ┌──────────────────────┐        ┌──────────────────────┐             │
│  │ pbd_cli/             │        │ pbd_core/            │             │
│  │ orchestrator.py      │───────►│ core.py              │             │
│  │ - extract_pbls()     │        │ - extract_pbl()      │             │
│  │ - extract_with_      │        │ - save_to_file()     │             │
│  │   recovery()         │        └──────────────────────┘             │
│  └──────────────────────┘                  │                           │
│                                            │                           │
│  ┌─────────────────────────────────────────┼─────────────────────┐    │
│  │                  Core Components        ▼                     │    │
│  │  ┌─────────────┐  ┌──────────────┐  ┌──────────────┐       │    │
│  │  │ header.py   │  │ node.py      │  │ entry.py     │       │    │
│  │  │ PBD headers │  │ NOD blocks   │  │ File entries │       │    │
│  │  └─────────────┘  └──────────────┘  └──────────────┘       │    │
│  │                                                               │    │
│  │  ┌─────────────┐  ┌──────────────┐  ┌──────────────┐       │    │
│  │  │ dat.py      │  │ pcode_ir.py  │  │ version_     │       │    │
│  │  │ Data blocks │  │ P-Code IR    │  │ detector.py  │       │    │
│  │  └─────────────┘  └──────────────┘  └──────────────┘       │    │
│  └───────────────────────────────────────────────────────────────┘    │
│                                                                         │
│  Output: Raw source files (.srw, .sru, .srd) + P-Code binary data     │
└─────────────────────────────────────────────────────────────────────────┘
```

### 2. Decompile Module (`/decompile/`)

```
┌─────────────────────────────────────────────────────────────────────────┐
│                           DECOMPILE MODULE                               │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                         │
│  Entry Points:                                                          │
│  ┌──────────────────────┐  ┌────────────────────┐  ┌────────────────┐ │
│  │ main_decompiler.py   │  │ decompile_         │  │ integrated_    │ │
│  │ - PowerBuilder       │  │ structured.py      │  │ decompiler.py  │ │
│  │   Decompiler class   │  │ - Template-based   │  │ - Combined     │ │
│  │ - decompile_pbd()    │  │   decompilation    │  │   approach     │ │
│  └──────────────────────┘  └────────────────────┘  └────────────────┘ │
│              │                                                          │
│              ▼                                                          │
│  ┌─────────────────────────────────────────────────────────────────┐  │
│  │                    Core Decompilation Pipeline                   │  │
│  │                                                                  │  │
│  │  ┌─────────────────┐    ┌──────────────────┐                  │  │
│  │  │ pcode_decoder_  │───►│ control_flow_    │                  │  │
│  │  │ v2.py           │    │ enhanced.py      │                  │  │
│  │  │ - Decode instrs │    │ - CFG analysis   │                  │  │
│  │  └─────────────────┘    └──────────────────┘                  │  │
│  │           │                      │                              │  │
│  │           ▼                      ▼                              │  │
│  │  ┌─────────────────┐    ┌──────────────────┐                  │  │
│  │  │ stack_          │    │ expression_      │                  │  │
│  │  │ emulator.py     │───►│ lifter.py        │                  │  │
│  │  │ - Stack ops     │    │ - High-level expr│                  │  │
│  │  └─────────────────┘    └──────────────────┘                  │  │
│  │                                  │                              │  │
│  │                                  ▼                              │  │
│  │                         ┌──────────────────┐                   │  │
│  │                         │ output_          │                   │  │
│  │                         │ formatter.py     │                   │  │
│  │                         │ - Format output  │                   │  │
│  │                         └──────────────────┘                   │  │
│  └─────────────────────────────────────────────────────────────────┘  │
│                                                                         │
│  ┌─────────────────────────────────────────────────────────────────┐  │
│  │                        Opcode Tables                             │  │
│  │  ┌────────────┐  ┌────────────┐  ┌────────────┐  ┌──────────┐ │  │
│  │  │ pb6_0.py   │  │ pb10_5.py  │  │ pb80_0.py  │  │ unified. │ │  │
│  │  │ PB 6.0     │  │ PB 10.5    │  │ PB 8.0     │  │ py       │ │  │
│  │  └────────────┘  └────────────┘  └────────────┘  └──────────┘ │  │
│  │                         Managed by: opcode_manager.py            │  │
│  └─────────────────────────────────────────────────────────────────┘  │
│                                                                         │
│  Output: Structured pseudocode / Python-like code                      │
└─────────────────────────────────────────────────────────────────────────┘
```

### 3. Parse Module (`/parse/`)

```
┌─────────────────────────────────────────────────────────────────────────┐
│                            PARSE MODULE                                  │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                         │
│  Entry Points:                                                          │
│  ┌──────────────────────┐  ┌──────────────────┐  ┌────────────────┐   │
│  │ parser.py            │  │ parse_ui.py      │  │ parse_schema.  │   │
│  │ - Extension-based    │  │ - UI elements    │  │ py             │   │
│  │   router             │  │                  │  │ - DB schemas   │   │
│  └──────────────────────┘  └──────────────────┘  └────────────────┘   │
│              │                                                          │
│              ▼                                                          │
│  ┌─────────────────────────────────────────────────────────────────┐  │
│  │                      Parser Components                           │  │
│  │                                                                  │  │
│  │  ┌─────────────────┐    ┌──────────────────┐                  │  │
│  │  │ powerbuilder.py │    │ pb_preprocessor. │                  │  │
│  │  │ - PB parsing    │◄───│ py               │                  │  │
│  │  │   logic         │    │ - Macros/includes│                  │  │
│  │  └─────────────────┘    └──────────────────┘                  │  │
│  │           │                                                     │  │
│  │           ▼                                                     │  │
│  │  ┌─────────────────┐    ┌──────────────────┐                  │  │
│  │  │ sql_parser.py   │    │ pseudocode_      │                  │  │
│  │  │ - SQL queries   │    │ parser.py        │                  │  │
│  │  │ - Transactions  │    │ - Parse decompiled│                  │  │
│  │  └─────────────────┘    └──────────────────┘                  │  │
│  └─────────────────────────────────────────────────────────────────┘  │
│                                                                         │
│  ┌─────────────────────────────────────────────────────────────────┐  │
│  │                         Visitors                                 │  │
│  │  ┌──────────────────┐  ┌────────────────┐  ┌────────────────┐ │  │
│  │  │ pb_transformer.  │  │ model_         │  │ entity_        │ │  │
│  │  │ py               │  │ generator.py   │  │ creator.py     │ │  │
│  │  │ - Parse tree →   │  │ - Generate     │  │ - Create       │ │  │
│  │  │   AST            │  │   models       │  │   entities     │ │  │
│  │  └──────────────────┘  └────────────────┘  └────────────────┘ │  │
│  │                                                                  │  │
│  │  ┌──────────────────┐  ┌────────────────┐                     │  │
│  │  │ sql_transformer. │  │ position_      │                     │  │
│  │  │ py               │  │ tracker.py     │                     │  │
│  │  │ - SQL → AST      │  │ - Track source │                     │  │
│  │  └──────────────────┘  └────────────────┘                     │  │
│  └─────────────────────────────────────────────────────────────────┘  │
│                                                                         │
│  Grammar Files: /grammar/*.lark (Lark parser definitions)              │
│                                                                         │
│  Output: AST nodes and model objects                                   │
└─────────────────────────────────────────────────────────────────────────┘
```

### 4. Model Module (`/model/`)

```
┌─────────────────────────────────────────────────────────────────────────┐
│                            MODEL MODULE                                  │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                         │
│  ┌─────────────────────────────────────────────────────────────────┐  │
│  │                        AST Components                            │  │
│  │  ┌────────────┐  ┌────────────┐  ┌────────────┐  ┌──────────┐ │  │
│  │  │ nodes.py   │  │ control.py │  │ functions. │  │ types.py │ │  │
│  │  │ Base nodes │  │ Control    │  │ py         │  │ Type     │ │  │
│  │  │            │  │ flow       │  │ Functions  │  │ system   │ │  │
│  │  └────────────┘  └────────────┘  └────────────┘  └──────────┘ │  │
│  │                                                                  │  │
│  │  ┌────────────┐  ┌────────────┐  ┌────────────┐               │  │
│  │  │ arrays.py  │  │ io.py      │  │ controlflow│               │  │
│  │  │ Array ops  │  │ File I/O   │  │ .py        │               │  │
│  │  └────────────┘  └────────────┘  └────────────┘               │  │
│  └─────────────────────────────────────────────────────────────────┘  │
│                                                                         │
│  ┌─────────────────────────────────────────────────────────────────┐  │
│  │                   PowerBuilder Entities                          │  │
│  │                                                                  │  │
│  │  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐        │  │
│  │  │ pb_entity.py │  │ pb_function. │  │ pb_event.py  │        │  │
│  │  │ Base entity  │  │ py           │  │ Events       │        │  │
│  │  └──────────────┘  └──────────────┘  └──────────────┘        │  │
│  │                                                                  │  │
│  │  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐        │  │
│  │  │ pb_variable. │  │ pb_          │  │ pb_sql.py    │        │  │
│  │  │ py           │  │ expression.py│  │ SQL nodes    │        │  │
│  │  └──────────────┘  └──────────────┘  └──────────────┘        │  │
│  └─────────────────────────────────────────────────────────────────┘  │
│                                                                         │
│  ┌─────────────────────────────────────────────────────────────────┐  │
│  │                   Specialized Components                         │  │
│  │                                                                  │  │
│  │  ┌──────────────────┐  ┌──────────────────┐  ┌──────────────┐ │  │
│  │  │ pb_datawindow/   │  │ pb_transaction/  │  │ ui/          │ │  │
│  │  │ - DataWindow     │  │ - Transactions   │  │ ui_elements. │ │  │
│  │  │   models         │  │ - Error handling │  │ py           │ │  │
│  │  └──────────────────┘  └──────────────────┘  └──────────────┘ │  │
│  │                                                                  │  │
│  │  ┌──────────────────┐  ┌──────────────────┐                   │  │
│  │  │ library/         │  │ system/          │                   │  │
│  │  │ - Library mgmt   │  │ - System funcs   │                   │  │
│  │  └──────────────────┘  └──────────────────┘                   │  │
│  └─────────────────────────────────────────────────────────────────┘  │
│                                                                         │
│  Utilities: /utils/ (type system, validation, errors, scope)           │
│                                                                         │
│  Role: Shared data structures for all pipeline stages                  │
└─────────────────────────────────────────────────────────────────────────┘
```

### 5. Generate Module (`/generate/`)

```
┌─────────────────────────────────────────────────────────────────────────┐
│                           GENERATE MODULE                                │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                         │
│  Entry Point:                                                           │
│  ┌──────────────────────────────────────────┐                         │
│  │ code_generator.py                         │                         │
│  │ - CodeGenerator class                     │                         │
│  │ - generate_models()                       │                         │
│  │ - generate_services()                     │                         │
│  │ - generate_frontend()                     │                         │
│  └──────────────────────────────────────────┘                         │
│                    │                                                    │
│         ┌──────────┴───────────┬─────────────┐                        │
│         ▼                      ▼             ▼                        │
│  ┌──────────────┐    ┌──────────────┐  ┌──────────────┐             │
│  │   Backend    │    │   Frontend   │  │    Jinja     │             │
│  │  Generation  │    │  Generation  │  │   Filters    │             │
│  └──────────────┘    └──────────────┘  └──────────────┘             │
│         │                     │                │                       │
│         ▼                     ▼                ▼                       │
│  ┌─────────────────────────────────────────────────────────────────┐  │
│  │                      Backend Components                          │  │
│  │                                                                  │  │
│  │  ┌─────────────────┐    ┌──────────────────┐                  │  │
│  │  │ generate_       │    │ generate_        │                  │  │
│  │  │ models.py       │    │ services.py      │                  │  │
│  │  │ - SQLModel      │    │ - Litestar       │                  │  │
│  │  │   models        │    │   endpoints      │                  │  │
│  │  └─────────────────┘    └──────────────────┘                  │  │
│  │                                                                  │  │
│  │  Templates:                                                     │  │
│  │  - model.py.jinja2                                             │  │
│  │  - service.py.jinja2                                           │  │
│  │  - system_functions.py.jinja2                                  │  │
│  └─────────────────────────────────────────────────────────────────┘  │
│                                                                         │
│  ┌─────────────────────────────────────────────────────────────────┐  │
│  │                     Frontend Components                          │  │
│  │                                                                  │  │
│  │  ┌─────────────────┐                                           │  │
│  │  │ generate_       │    Templates:                             │  │
│  │  │ component.py    │    - component.astro.jinja2               │  │
│  │  │ - React/Astro   │    - component.tsx.jinja2                 │  │
│  │  │   components    │    - listview.tsx.jinja2                  │  │
│  │  └─────────────────┘    - richtext.tsx.jinja2                  │  │
│  └─────────────────────────────────────────────────────────────────┘  │
│                                                                         │
│  jinja_filters.py - Custom filters for template processing             │
│                                                                         │
│  Output: Modern web application code (Python backend, React frontend)  │
└─────────────────────────────────────────────────────────────────────────┘
```

## Data Flow Summary

```
┌─────────────────────────────────────────────────────────────────────────┐
│                         PIPELINE DATA FLOW                               │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                         │
│  PBL/PBD Files                                                          │
│       │                                                                 │
│       ▼                                                                 │
│  ┌─────────┐                                                           │
│  │ EXTRACT │──────► Raw Source Files (.srw, .sru, .srd)               │
│  └─────────┘              │                                            │
│       │                   │                                            │
│       │                   ▼                                            │
│       │              ┌─────────┐                                       │
│       └─────────────►│  PARSE  │                                       │
│       P-Code         └─────────┘                                       │
│       Binary              │                                            │
│       │                   │ AST                                        │
│       ▼                   ▼ Nodes                                      │
│  ┌──────────┐        ┌─────────┐                                      │
│  │DECOMPILE │───────►│  MODEL  │◄─── Shared Data Structures           │
│  └──────────┘        └─────────┘                                      │
│   Pseudocode              │                                            │
│       │                   │                                            │
│       ▼                   │                                            │
│  ┌─────────┐             │                                            │
│  │  PARSE  │─────────────┘                                            │
│  └─────────┘                                                           │
│                           │                                            │
│                           ▼                                            │
│                      ┌──────────┐                                      │
│                      │ GENERATE │                                      │
│                      └──────────┘                                      │
│                           │                                            │
│                           ▼                                            │
│                   Modern Web Application                               │
│                   - Python/Litestar Backend                            │
│                   - React/Astro Frontend                               │
│                   - SQLModel Models                                    │
└─────────────────────────────────────────────────────────────────────────┘
```

## Key Integration Points

1. **Extract → Decompile**: 
   - `pbd_core/pcode_ir.py` provides P-Code data structure
   - `main_decompiler.py` uses `extract.pbd_core` modules

2. **Extract/Decompile → Parse**:
   - Raw source files parsed by `parser.py`
   - Pseudocode parsed by `pseudocode_parser.py`

3. **Parse → Model**:
   - `pb_transformer.py` creates model objects
   - `model_generator.py` generates model instances

4. **Model → All**:
   - Model classes used as shared data structures
   - Type system and validation utilities

5. **Model → Generate**:
   - Model objects drive code generation
   - Templates use model properties

## CLI Entry Points

- `main.py` - Main CLI with commands for each stage
- Individual module entry points for standalone usage