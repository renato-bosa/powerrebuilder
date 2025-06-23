# Tools Directory

This directory contains development tools, scripts, and utilities for the SIME Finch project.

## Directory Structure

- **analysis/** - Code analysis and inspection tools
  - Extraction result analysis
  - Coverage analysis
  - Code quality checks
  - P-code analysis tools

- **maintenance/** - Project maintenance utilities
  - Development setup scripts
  - Code cleanup utilities
  - Template validation
  - Benchmark tools

- **migration/** - One-time migration scripts
  - Code transformation tools
  - Legacy code fixes

- **debug/** - Debugging and investigation tools
  - P-code debugging utilities
  - Binary format analyzers
  - Test utilities for specific components

- **demos/** - Demonstration scripts
  - Feature demonstrations
  - Usage examples
  - Visualization demos

- **opcodes/** - PowerBuilder opcode tools
  - discovery/ - Opcode discovery pipeline
  - extraction/ - Opcode extraction from binaries
  - generation/ - Reference generation
  - validation/ - Opcode validation and comparison

- **pipeline/** - Pipeline testing tools
  - End-to-end pipeline tests
  - Component integration tests

- **archive/** - Historical/deprecated tools
  - decoders/ - Old decoder implementations
  - scripts/ - One-time fix scripts
  - grammars/ - Old grammar versions

## Usage

Most tools can be run directly with Python:

```bash
python tools/analysis/code_quality_check.py
```

Some shell scripts may need execution permissions:

```bash
chmod +x tools/maintenance/setup_dev.sh
./tools/maintenance/setup_dev.sh
```

## Note

Tools in the `archive/` directory are kept for historical reference but should not be used for current development.