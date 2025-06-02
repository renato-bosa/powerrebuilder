# Automated Opcode Discovery Pipeline

## Overview

Automates the process of discovering and adding missing PowerBuilder P-code opcodes to the decoder.

## Usage

```bash
# Basic usage
python decompile/scripts/opcode_discovery_pipeline.py

# With options
python decompile/scripts/opcode_discovery_pipeline.py --coverage 0.90 --max-files 20 --verbose

# Specific test files
python decompile/scripts/opcode_discovery_pipeline.py --test-file output/test_bytes_fix/file.fun
```

## Options

- `--coverage FLOAT` - Target coverage percentage (0-1), default: 0.95
- `--max-files INT` - Maximum test files to use, default: 10
- `--verbose` - Enable detailed logging
- `--test-file FILE` - Specific test file (can be repeated)

## How It Works

1. **Discovery** - Finds test files matching patterns (*.fun,*.win, *.dwo,*.udo)
2. **Decode** - Runs decoder and collects unknown opcodes
3. **Analyze** - Identifies opcode patterns occurring ≥5 times
4. **Add** - Updates opcodes.yaml with new definitions
5. **Iterate** - Repeats until coverage target is met

## Output

- **Backups**: `output/opcode_backups/` - Timestamped opcodes.yaml versions
- **Reports**: `output/opcode_discovery_reports/` - JSON coverage reports
- **Exit Codes**: 0 = success, 1 = below target (CI/CD friendly)

## Configuration

Edit `opcode_discovery_config.py` to customize:

- Test file patterns
- Coverage targets
- Occurrence thresholds
- Output directories

## Components

### 1. `opcode_discovery_pipeline.py`

The main pipeline script that orchestrates the discovery process.

### 2. `opcode_discovery_config.py`

Configuration module that defines:

- Coverage targets
- Test file patterns
- Thresholds and limits
- Output directories

### 3. Generated Artifacts

- **Backups**: `output/opcode_backups/` - Timestamped backups of `opcodes.yaml`
- **Reports**: `output/opcode_discovery_reports/` - JSON reports of each run
- **Logs**: `logs/unknown_opcodes.log` - Detailed unknown opcode information

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

## Reports

Each run generates a JSON report containing:

- Configuration used
- Final coverage per file
- Average coverage achieved
- Total duration
- Iteration history with:
  - Unknown count per iteration
  - Coverage improvement
  - Time per iteration

Example report structure:

```json
{
  "timestamp": "2025-05-31T11:30:00",
  "config": {
    "coverage_target": 0.95,
    "max_iterations": 10,
    "min_occurrence_threshold": 5,
    "test_files_count": 3
  },
  "results": {
    "final_coverage": {
      "of_tj_report.fun": 0.9995,
      "f_get_username.fun": 0.94,
      "of_update_coa.fun": 0.93
    },
    "average_coverage": 0.9565,
    "total_duration_seconds": 45.2,
    "iterations_completed": 4
  },
  "iteration_history": [...]
}
```

## Best Practices

1. **Start Small**: Test with a few files first to ensure the pipeline works
2. **Monitor Progress**: Use `--verbose` to see detailed progress
3. **Review Changes**: Check the backups in `output/opcode_backups/` to review what was added
4. **Manual Review**: For production use, review auto-discovered opcodes for correctness
5. **UTF-8 Awareness**: The decoder already handles UTF-8 strings, so E4-E9 ranges may be text

## Troubleshooting

1. **No test files found**: Check that your test file patterns match actual files
2. **Low coverage**: Some files may contain non-P-code data (strings, headers, etc.)
3. **Pipeline stops early**: Check the min_occurrence_threshold - too high may miss rare opcodes
4. **Decoder fails**: Ensure the decoder script path is correct and Python environment is set up

## Integration with CI/CD

The pipeline exits with:

- Code 0: Target coverage achieved
- Code 1: Target coverage not achieved

This makes it suitable for CI/CD integration:

```bash
# In CI script
python decompile/scripts/opcode_discovery_pipeline.py --coverage 0.90
if [ $? -eq 0 ]; then
    echo "✓ Opcode coverage target met"
else
    echo "✗ Opcode coverage below target"
    exit 1
fi
```
