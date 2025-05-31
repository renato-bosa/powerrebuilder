# Opcode Discovery Tools

This directory contains various tools for discovering and managing PowerBuilder P-code opcodes.

## Automated Pipeline

### `opcode_discovery_pipeline.py`

Main automated pipeline that orchestrates the entire discovery process. Runs iteratively until coverage targets are met.

### `opcode_discovery_config.py`

Configuration module for the pipeline. Defines coverage targets, test file patterns, and other settings.

## Analysis Tools

### `analyze_pcode_patterns.py`

Analyzes binary P-code files to discover opcode patterns and frequencies. Useful for initial discovery.

### `analyze_unknown_opcodes.py`

Analyzes the `unknown_opcodes.log` file to categorize and count unknown opcodes. Helps identify which opcodes to add next.

## Opcode Addition Tools

### `add_missing_opcodes.py`

Automatically adds missing opcodes to `opcodes.yaml` based on analysis. Detects patterns and adds appropriate definitions.

### `add_specific_variants.py`

Adds specific opcode variants to `opcodes.yaml` with proper YAML formatting. Used for targeted additions.

## Generated Files

### `missing_opcodes.yaml`

Contains opcodes that were detected but not yet added to the main opcodes.yaml file.

### `unknown_opcodes.log`

Log of all unknown opcodes encountered during decoding, with context.

### `unknown_opcodes_old.log`

Previous version of the unknown opcodes log (backup).

## Usage

For most users, simply run:

```bash
python opcode_discovery_pipeline.py
```

This will automatically discover opcodes and add them until 95% coverage is achieved.

For manual analysis and addition:

```bash
# Analyze patterns in a P-code file
python analyze_pcode_patterns.py path/to/file.pcode

# Analyze unknown opcodes from log
python analyze_unknown_opcodes.py

# Add missing opcodes automatically
python add_missing_opcodes.py

# Add specific variants manually
python add_specific_variants.py
```
