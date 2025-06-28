# SIME Finch Pipeline Architecture

## Overview

The SIME Finch pipeline processes PowerBuilder applications through a sophisticated architecture that handles both source code and compiled P-code in parallel. This document clarifies the exact flow and prevents common misconceptions.

## The Pipeline Flow

```
┌─────────────────┐
│   PBL/PBD Files │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│     EXTRACT     │ Decompresses and extracts ALL contents
└────────┬────────┘
         │
    ┌────┴────┐
    ▼         ▼
┌────────┐ ┌────────────┐
│ Source │ │   P-code   │  Extract outputs BOTH types
│ Files  │ │   Files    │
└────┬───┘ └─────┬──────┘
     │           │
     ▼           ▼
┌────────┐ ┌────────────┐
│ PARSE  │ │ DECOMPILE  │  These run in PARALLEL
└────┬───┘ └─────┬──────┘
     │           │
     └─────┬─────┘
           ▼
    ┌─────────────┐
    │  GENERATE   │ Combines outputs from both stages
    └─────────────┘
           │
           ▼
    Modern Web App
```

## Key Points

### 1. Extract Stage Outputs BOTH File Types

PowerBuilder PBL/PBD files contain:
- **Source files**: Human-readable PowerBuilder code
- **P-code files**: Compiled bytecode requiring decompilation

The Extract stage outputs BOTH types, not just one or the other.

### 2. Parse and Decompile Run in PARALLEL

**This is NOT a sequential pipeline!** Parse and Decompile process different file types simultaneously:

- **Parse** handles source files
- **Decompile** handles P-code files
- They do NOT depend on each other
- They can run concurrently for better performance

### 3. Generate Combines Both Outputs

The Generate stage needs outputs from BOTH:
- ASTs from Parse (for source files)
- Decompiled code from Decompile (for P-code files)

## File Type Reference

### Source Files (→ Parse)
| Extension | Description | Contains |
|-----------|-------------|----------|
| .srw | Window source | Layout, events, controls |
| .sru | User object source | Methods, properties |
| .srf | Function source | Function implementations |
| .srm | Menu source | Menu structure, events |
| .srs | Structure source | Type definitions |
| .sra | Application source | Application settings |
| .srd | DataWindow source | SQL, layout, properties |

### P-code Files (→ Decompile)
| Extension | Description | Contains |
|-----------|-------------|----------|
| .fun | Compiled function | P-code bytecode |
| .win | Compiled window | P-code + layout data |
| .udo | User object compiled | P-code bytecode |
| .men | Menu compiled | P-code + menu data |
| .mef | Menu function | P-code for menu events |
| .apl | Application compiled | P-code + settings |
| .apf | App function | P-code for app events |

### Data Files (Special Handling)
| Extension | Description | Processing |
|-----------|-------------|------------|
| .dwo | DataWindow compiled | Extract → Special parser |
| .str | Structure compiled | Extract → Type extractor |

## Common Misconceptions

### ❌ WRONG: "Parse comes before Decompile"
This suggests a sequential flow where Parse must complete before Decompile starts.

### ✅ CORRECT: "Parse and Decompile run in parallel"
They process different file types simultaneously.

### ❌ WRONG: "Decompile processes Parse output"
Decompile does NOT use Parse output. It processes P-code files directly from Extract.

### ✅ CORRECT: "Both Parse and Decompile process Extract output"
Extract provides files to both stages independently.

### ❌ WRONG: "All files go through Parse"
Only source files go through Parse. P-code files skip Parse entirely.

### ✅ CORRECT: "Files are routed based on type"
The pipeline intelligently routes files to the appropriate processor.

## Implementation Details

### File Classification (ObjectTypeDetector)

```python
# Source files → Parse
if file_path.suffix in ['.srw', '.sru', '.srf', '.srm', '.srs', '.sra', '.srd']:
    route_to_parse(file_path)

# P-code files → Decompile  
elif file_path.suffix in ['.fun', '.win', '.udo', '.men', '.mef', '.apl', '.apf']:
    route_to_decompile(file_path)
```

### Parallel Execution

When running the full pipeline:
1. Extract runs first and completes
2. Parse and Decompile start simultaneously
3. Generate waits for both to complete
4. Generate combines all outputs

## Performance Considerations

### Benefits of Parallel Architecture
- **Speed**: Parse and Decompile run concurrently
- **Efficiency**: No unnecessary conversions
- **Scalability**: Can process on separate threads/processes
- **Flexibility**: Can run only needed stages

### Resource Usage
- Parse is typically CPU-bound (grammar processing)
- Decompile is I/O and CPU intensive (bytecode analysis)
- Running in parallel maximizes resource utilization

## Example: Processing a Window

Consider a PowerBuilder window `w_customer`:

1. **Extract** finds:
   - `w_customer.srw` (source with layout)
   - `w_customer.win` (P-code with events)

2. **Parallel Processing**:
   - Parse processes `w_customer.srw` → AST with layout
   - Decompile processes `w_customer.win` → Event code

3. **Generate** combines:
   - Layout from Parse AST
   - Event handlers from Decompile
   - Produces complete modern component

## Summary

The SIME Finch pipeline is a sophisticated parallel architecture, not a simple sequential flow. Understanding this is crucial for:
- Debugging pipeline issues
- Optimizing performance  
- Adding new features
- Maintaining the codebase

Remember: **Parse and Decompile are partners, not parent and child!**