# SIME Finch Pipeline - Simplified Visual Diagram

## High-Level Pipeline Flow

```mermaid
graph TB
    subgraph "Input"
        PBL[PBL/PBD Files<br/>PowerBuilder Binary]
    end
    
    subgraph "1. EXTRACT"
        E1[extract_coordinator.py<br/>Main Entry]
        E2[core.py<br/>Extract Logic]
        E3[header.py<br/>node.py<br/>entry.py]
        E4[pcode_ir.py<br/>P-Code IR]
        
        E1 --> E2
        E2 --> E3
        E3 --> E4
    end
    
    subgraph "2. DECOMPILE"
        D1[decompile_coordinator.py<br/>Orchestrator]
        D2[pcode_decoder_v2.py<br/>Decode Instructions]
        D3[control_flow_enhanced.py<br/>CFG Analysis]
        D4[stack_emulator.py<br/>expression_lifter.py]
        D5[output_formatter.py<br/>Format Output]
        
        D1 --> D2
        D2 --> D3
        D3 --> D4
        D4 --> D5
    end
    
    subgraph "3. PARSE"
        P1[parse_coordinator.py<br/>Router]
        P2[powerbuilder.py<br/>PB Parser]
        P3[sql_parser.py<br/>SQL Parser]
        P4[pb_transformer.py<br/>AST Transform]
        P5[model_generator.py<br/>Create Models]
        
        P1 --> P2
        P1 --> P3
        P2 --> P4
        P3 --> P4
        P4 --> P5
    end
    
    subgraph "4. MODEL"
        M1[AST Nodes<br/>nodes.py, control.py]
        M2[PB Entities<br/>pb_function.py, pb_event.py]
        M3[Specialized<br/>datawindow, transaction, ui]
        M4[Utils<br/>type_system, validation]
        
        M1 -.-> M2
        M2 -.-> M3
        M1 -.-> M4
    end
    
    subgraph "5. GENERATE"
        G1[generate_coordinator.py<br/>Main Generator]
        G2[Backend<br/>generate_models.py<br/>generate_services.py]
        G3[Frontend<br/>generate_component.py]
        G4[Templates<br/>Jinja2 Templates]
        
        G1 --> G2
        G1 --> G3
        G2 --> G4
        G3 --> G4
    end
    
    subgraph "Output"
        OUT[Modern Web App<br/>Litestar + React]
    end
    
    PBL --> E1
    E4 --> D1
    E3 -.->|Source Files| P1
    D5 -->|Pseudocode| P1
    P5 --> M1
    M3 --> G1
    G4 --> OUT
    
    style PBL fill:#f9f,stroke:#333,stroke-width:4px
    style OUT fill:#9f9,stroke:#333,stroke-width:4px
    style M1 fill:#ff9,stroke:#333,stroke-width:2px
    style M2 fill:#ff9,stroke:#333,stroke-width:2px
    style M3 fill:#ff9,stroke:#333,stroke-width:2px
    style M4 fill:#ff9,stroke:#333,stroke-width:2px
```

## Key File Relationships

### Extract Module Files
- **Entry**: `pbd_cli/extract_coordinator.py`
- **Core Logic**: `pbd_core/core.py`
- **Outputs**: Raw source files + P-Code binary

### Decompile Module Files
- **Entry**: `decompile_coordinator.py`
- **Pipeline**: 
  - `pcode_decoder_v2.py` → Decode P-Code
  - `control_flow_enhanced.py` → Build CFG
  - `stack_emulator.py` + `expression_lifter.py` → Reconstruct expressions
  - `output_formatter.py` → Format code
- **Outputs**: Structured pseudocode

### Parse Module Files
- **Entry**: `parse_coordinator.py` (routes by file extension)
- **Parsers**:
  - `powerbuilder.py` → Parse PB syntax
  - `sql_parser.py` → Parse SQL
  - `pseudocode_parser.py` → Parse decompiled code
- **Transformers**:
  - `pb_transformer.py` → Convert to AST
  - `model_generator.py` → Create model objects
- **Outputs**: AST nodes and model instances

### Model Module Files
- **AST Layer**: `ast/nodes.py`, `ast/control.py`, `ast/functions.py`
- **PB Layer**: `pb_function.py`, `pb_event.py`, `pb_variable.py`
- **Specialized**: `pb_datawindow/`, `pb_transaction/`, `ui/`
- **Role**: Shared data structures for entire pipeline

### Generate Module Files
- **Entry**: `generate_coordinator.py`
- **Generators**:
  - `backend/generate_models.py` → SQLModel models
  - `backend/generate_services.py` → Litestar services
  - `frontend/generate_component.py` → React components
- **Templates**: Jinja2 templates in `templates/`
- **Outputs**: Modern web application code

## Data Flow Examples

### Example 1: Window Object
```
1. Extract: w_main.srw (raw file) from PBL
2. Parse: parse_coordinator.py → powerbuilder.py → AST
3. Model: Window object with controls, events, functions
4. Generate: React component + API endpoints
```

### Example 2: P-Code Function
```
1. Extract: P-Code binary from PBD
2. Decompile: Bytecode → Instructions → Pseudocode
3. Parse: pseudocode_parser.py → AST
4. Model: Function object with parameters, body
5. Generate: Python function implementation
```

### Example 3: DataWindow
```
1. Extract: d_employee.srd from PBL
2. Parse: parse_coordinator.py → DataWindow syntax parser
3. Model: DataWindow object with SQL, columns, UI
4. Generate: SQLModel model + React data grid
```