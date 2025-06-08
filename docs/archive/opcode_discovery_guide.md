# PowerBuilder Opcode Discovery Guide

This comprehensive guide covers the automated opcode discovery pipeline and related tools for finding, analyzing, and adding missing PowerBuilder P-code opcodes.

## Quick Start

For most users, simply run:

```bash
# Basic usage - discovers opcodes until 95% coverage is achieved
python scripts/opcodes/discovery/opcode_discovery_pipeline.py

# With custom options
python scripts/opcodes/discovery/opcode_discovery_pipeline.py --coverage 0.90 --max-files 20 --verbose

# Test specific files
python scripts/opcodes/discovery/opcode_discovery_pipeline.py --test-file output/test_bytes_fix/file.fun
```

## How It Works

The automated pipeline follows this process:

1. **Discovery** - Finds test files matching patterns (*.fun, *.win, *.dwo, *.udo)
2. **Decode** - Runs decoder and collects unknown opcodes
3. **Analyze** - Identifies opcode patterns occurring ≥5 times
4. **Add** - Updates opcodes.yaml with new definitions
5. **Iterate** - Repeats until coverage target is met

## Command Line Options

- `--coverage FLOAT` - Target coverage percentage (0-1), default: 0.95
- `--max-files INT` - Maximum test files to use, default: 10
- `--verbose` - Enable detailed logging
- `--test-file FILE` - Specific test file (can be repeated)

## Tools Overview

### Main Pipeline

#### `opcode_discovery_pipeline.py`
Main automated pipeline that orchestrates the entire discovery process. Runs iteratively until coverage targets are met.

#### `opcode_discovery_config.py`
Configuration module that defines:
- Coverage targets
- Test file patterns
- Thresholds and limits
- Output directories

### Analysis Tools

#### `analyze_missing_opcodes.py`
Analyzes the verified opcode mappings to find and categorize missing opcodes.

#### `analyze_unknown_opcodes.py`
Analyzes the `logs/unknown_opcodes.log` file to categorize and count unknown opcodes. Helps identify which opcodes to add next.

### Opcode Addition Tools

#### `add_missing_opcodes.py`
Automatically adds missing opcodes to `opcodes.yaml` based on analysis. Detects patterns and adds appropriate definitions.

#### `add_specific_variants.py`
Adds specific opcode variants to `opcodes.yaml` with proper YAML formatting. Used for targeted additions.

#### `add_missing_final_opcodes.py`
Adds the final set of missing opcodes with verified mappings.

## Generated Files and Artifacts

### Backups
- **Location**: `backup/opcodes_*.yaml`
- **Purpose**: Timestamped backups of opcodes.yaml before modifications

### Reports
- **Location**: `output/opcode_discovery_reports/`
- **Format**: JSON reports containing:
  - Configuration used
  - Final coverage per file
  - Average coverage achieved
  - Total duration
  - Iteration history

### Logs
- **`logs/unknown_opcodes.log`** - Detailed unknown opcode information with context
- **`missing_opcodes.yaml`** - Opcodes detected but not yet added to main opcodes.yaml

## Opcode Categories

New opcodes are automatically categorized based on their byte value:

| Range | Category | Description |
|-------|----------|-------------|
| 0x00-0x1F | control | Control characters |
| 0x20-0x7F | ascii | ASCII printable characters |
| 0x80-0x9F | special | Special operations |
| 0xA0-0xBF | variable_ops | Variable operations |
| 0xC0-0xCF | constants | Constant loading |
| 0xD0-0xDF | control_flow | Control flow |
| 0xE0-0xE3 | jumps | Jump operations |
| 0xE4-0xE7 | variable_access | Variable access |
| 0xE8-0xEB | store_ops | Store operations |
| 0xEC-0xEF | test_ops | Test operations |
| 0xF0-0xFF | extended_ops | Extended operations |

## Configuration

Edit `opcode_discovery_config.py` to customize:

```python
# Example configuration
CONFIG = {
    'coverage_target': 0.95,
    'max_test_files': 10,
    'min_occurrences': 5,
    'file_patterns': ['*.fun', '*.win', '*.dwo', '*.udo'],
    'backup_dir': 'output/opcode_backups',
    'report_dir': 'output/opcode_discovery_reports'
}
```

## Manual Analysis and Addition

For manual opcode discovery and addition:

```bash
# Analyze unknown opcodes from log
python scripts/opcodes/discovery/analyze_unknown_opcodes.py

# Add missing opcodes automatically
python scripts/opcodes/discovery/add_missing_opcodes.py

# Add specific variants manually
python scripts/opcodes/discovery/add_specific_variants.py
```

## Integration with CI/CD

The pipeline is designed to work with CI/CD systems:

- **Exit Code 0**: Target coverage achieved
- **Exit Code 1**: Below target coverage (useful for quality gates)

```bash
# Example CI/CD usage
python scripts/opcodes/discovery/opcode_discovery_pipeline.py --coverage 0.95 || exit 1
```

## Best Practices

1. **Regular Runs**: Run the pipeline regularly as new test files are added
2. **Backup Review**: Review opcode backups before committing changes
3. **Coverage Targets**: Start with lower coverage (0.90) for initial runs, increase gradually
4. **Test Files**: Use diverse test files for better opcode discovery
5. **Manual Review**: Review generated opcodes for sensibility

## Troubleshooting

### Common Issues

1. **Low Coverage**: Add more diverse test files or lower the occurrence threshold
2. **False Positives**: Review and manually edit opcodes.yaml if incorrect patterns are detected
3. **Performance**: Reduce max-files if processing takes too long

### Debug Mode

Enable verbose logging for detailed information:

```bash
python scripts/opcodes/discovery/opcode_discovery_pipeline.py --verbose
```

## Related Documentation

- **opcode_reference.md** - Complete reference of all verified PowerBuilder opcodes
- **Archived History** - Historical documentation in `docs/archive/opcode_history/`

## Future Enhancements

- Pattern-based opcode name inference
- Automatic operand type detection
- Machine learning for opcode categorization
- Integration with decompiler test suite