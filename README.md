# SIME Finch

PowerBuilder reverse engineering toolkit that converts legacy PowerBuilder applications into modern web applications.

## Overview

SIME Finch provides a complete pipeline for transforming PowerBuilder applications:
- **Extract**: Extracts source code from PBL/PBD files
- **Parse**: Parses PowerBuilder syntax into AST
- **Model**: Builds semantic models from AST
- **Decompile**: Reconstructs high-level code from P-code
- **Generate**: Produces Flutter/Dart frontend and Python backend

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

1. Extract PowerBuilder files:
   ```bash
   uv run sime-finch extract input/myapp.pbl output/extracted/
   ```

2. Parse extracted files:
   ```bash
   uv run sime-finch parse output/extracted/ output/parsed/
   ```

3. Generate Flutter app:
   ```bash
   uv run sime-finch generate output/parsed/ output/flutter/
   ```

## Contributing

Please read the [Development Guide](docs/DEVELOPMENT_GUIDE.md) before contributing.

## License

[License information here]
