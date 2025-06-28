# SIME Finch

PowerBuilder reverse engineering toolkit that converts legacy PowerBuilder applications into modern web applications.

## Overview

SIME Finch provides a complete pipeline for transforming PowerBuilder applications:

### Pipeline Architecture

1. **Extract**: Extracts BOTH source code AND P-code files from PBL/PBD archives
   - Source files: `.srw`, `.sru`, `.srf`, `.srm`, `.srs`, `.sra`, `.srd`
   - P-code files: `.fun`, `.win`, `.udo`, `.men`, `.mef`, `.apl`, `.apf`

2. **Parse & Decompile** (PARALLEL EXECUTION):
   - **Parse**: Processes source files into Abstract Syntax Trees (ASTs)
   - **Decompile**: Reconstructs high-level code from P-code bytecode
   
3. **Model**: Builds semantic models from parsed ASTs

4. **Generate**: Combines outputs from BOTH Parse and Decompile to produce:
   - Flutter/Dart frontend applications
   - Python/Litestar backend services

**IMPORTANT**: Parse and Decompile run in PARALLEL, not sequentially. They process different file types extracted from the same PBL/PBD archives.

## Installation

```bash
uv sync
```

## Usage

```bash
uv run sime-finch --help
```

## Documentation

- **[Development Guide](docs/DEVELOPMENT_GUIDE.md)**: Active development documentation
  - Migration guide for recent changes
  - Test coverage improvement plan
  - File naming standards
  - Future architecture plans
  
- **[Project History](docs/PROJECT_HISTORY.md)**: Historical documentation
  - Consolidation analysis and results
  - Technical decisions and rationale
  - Lessons learned

## Development

```bash
# Install with dev dependencies
uv sync --dev

# Run tests
uv run pytest

# Run linting
uv run ruff check .

# Format code
uv run ruff format .
```

## Quick Start

### Option 1: Run Complete Pipeline
```bash
uv run sime-finch all input/ output/
```

This runs all stages automatically:
1. Extract → produces source + P-code files
2. Parse & Decompile → run in parallel on different file types
3. Generate → combines both outputs

### Option 2: Run Individual Stages

1. Extract PowerBuilder files:
   ```bash
   uv run sime-finch extract input/myapp.pbl output/extracted/
   ```
   This extracts BOTH source files (.srw, .sru, etc.) AND P-code files (.fun, .win, etc.)

2. Parse source files (handles .srw, .sru, .srf, etc.):
   ```bash
   uv run sime-finch parse output/extracted/ output/parsed/
   ```

3. Decompile P-code files (handles .fun, .win, .udo, etc.):
   ```bash
   uv run sime-finch decompile output/extracted/ output/decompiled/
   ```

4. Generate modern application:
   ```bash
   uv run sime-finch generate --parsed-dir output/parsed/ --decompiled-dir output/decompiled/
   ```

## Contributing

Please read the [Development Guide](docs/DEVELOPMENT_GUIDE.md) before contributing.

## License

[License information here]
