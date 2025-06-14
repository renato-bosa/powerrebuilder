# SIME Finch - PowerBuilder Reverse Engineering Toolkit

Welcome to SIME Finch, a comprehensive toolkit for reverse engineering PowerBuilder applications.

## Overview

SIME Finch provides a complete pipeline for:

- **Extracting** PowerBuilder source code from PBL/PBD files
- **Parsing** PowerBuilder syntax into structured AST
- **Modeling** PowerBuilder applications with a rich object model
- **Decompiling** P-code back to readable PowerBuilder source
- **Generating** modern code from PowerBuilder applications

## Key Features

- 🎯 **100% Extraction Accuracy** - Enhanced extraction with magic number recovery
- 🔍 **Advanced P-code Decompilation** - Decode PowerBuilder bytecode
- 🏗️ **Rich Object Model** - Full PowerBuilder language support
- 🚀 **Modern Code Generation** - Convert to Python, TypeScript, and more
- 📊 **Static Analysis** - Dependency graphs and code metrics

## Quick Start

```bash
# Install with UV
uv sync --dev

# Run the full pipeline
uv run python main.py all

# Extract PBD files
uv run python main.py extract files input/pbd_files output/extracted

# Parse PowerBuilder files
uv run python main.py parse file path/to/file.srw

# Decompile P-code
uv run python main.py decompile files output/extracted output/decompiled

# Generate modern code
uv run python main.py generate python output/parsed output/generated
```

## Development Setup

```bash
# Install all development dependencies
uv sync --dev

# Run all checks
python scripts/dev-tools.py all

# Run specific tools
python scripts/dev-tools.py lint --fix
python scripts/dev-tools.py typecheck
python scripts/dev-tools.py test -n auto
python scripts/dev-tools.py docs --serve
```

## Architecture

SIME Finch uses a modular pipeline architecture:

```mermaid
graph LR
    A[PBL/PBD Files] --> B[Extract]
    B --> C[Parse]
    C --> D[Model]
    D --> E[Decompile]
    E --> F[Generate]
    F --> G[Modern Code]
```

Each module can be used independently or as part of the full pipeline.

## Documentation

- [Installation Guide](getting-started/installation.md)
- [Architecture Overview](architecture/overview.md)
- [API Reference](api/index.md)
- [Development Guide](development/contributing.md)

## Contributing

We welcome contributions! Please see our [Contributing Guide](development/contributing.md) for details.

## License

SIME Finch is licensed under the MIT License. See [LICENSE](https://github.com/yourusername/sime-finch/blob/main/LICENSE) for details.