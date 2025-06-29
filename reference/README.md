# Reference Directory

This directory contains reference materials for the PowerBuilder decompiler project.

## Contents

### Core References
- `opcode_reference.json` - PowerBuilder opcode definitions
- `opcode_reference.yaml` - Alternative format for opcodes
- `learned_vocabulary.json` - Learned PowerBuilder vocabulary

### PowerBuilder Code Examples
- `pb_code_examples/` - Various PowerBuilder version examples

### External Tools (Should be moved)
The following are third-party projects that should not be in this repository:
- `decompilers/pbdviewer/` - C# PBD viewer project
- `decompilers/powerbuilder-decompile/` - Another decompiler project

## Recommended Actions

1. **Move External Projects**
   These should be referenced via:
   - Git submodules
   - Separate reference repository
   - Documentation links only

2. **Keep Only Essential References**
   - Opcode definitions
   - Minimal code examples
   - Our own analysis results

## Usage

### Opcode Reference
```python
import json
with open('reference/opcode_reference.json') as f:
    opcodes = json.load(f)
```

### Code Examples
The `pb_code_examples/` directory contains sample PowerBuilder code from various versions for testing and validation purposes.