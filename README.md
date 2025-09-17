# PowerRebuilder

[![GitHub Issues](https://img.shields.io/github/issues/michaelprowacki/powerrebuilder)](https://github.com/michaelprowacki/powerrebuilder/issues)
[![License](https://img.shields.io/badge/license-Apache%202.0-blue)](LICENSE)

Reverse engineering toolkit that transforms compiled PowerBuilder applications into modern codebases.

## What It Does

PowerRebuilder decompiles PowerBuilder PBL/PBD files through a 5-stage pipeline:
1. **Extract** P-code bytecode from compiled binaries
2. **Decompile** P-code to PowerBuilder source
3. **Parse** source into Abstract Syntax Trees
4. **Model** application structure and semantics
5. **Generate** modern code (Python/Litestar, Dart/Flutter)

## Quick Start

```bash
# Clone and install
git clone https://github.com/michaelprowacki/powerrebuilder.git
cd powerrebuilder
uv sync  # or pip install -e .

# Run full pipeline
python main.py all input.pbl output/

# Run individual stages (must be in order)
python main.py extract input.pbl output/extracted/
python main.py decompile output/extracted/ output/decompiled/
python main.py parse output/decompiled/ output/parsed/
python main.py model output/parsed/ output/models/
python main.py generate output/models/ output/generated/

# Choose output target
python main.py generate output/models/ output/ --target python   # Litestar
python main.py generate output/models/ output/ --target flutter  # Dart/Flutter
```

## Development

```bash
# Run tests
task test           # or: uv run pytest
task test:fast      # Skip slow tests
task test:parallel  # Run in parallel

# Code quality
task lint          # Ruff linting
task format        # Auto-format
task type          # Type checking

# Benchmarking
task benchmark:perf    # Performance tests
task profile:memory    # Memory profiling

# Full CI pipeline
task ci
```

See [Task](https://taskfile.dev) for all available commands: `task --list`

## Architecture

PowerRebuilder uses AST-based transformation with semantic preservation:
- **P-code Decompiler**: Reconstructs PowerScript from bytecode
- **Lark Parser**: Grammar-based PowerScript parsing
- **Code Generators**: Template-based modern code generation

## Documentation

- [Architecture Overview](docs/ARCHITECTURE.md)
- [PowerBuilder to Flutter Mapping](docs/POWERBUILDER_TO_FLUTTER_MAPPING.md)
- [API Reference](docs/API_REFERENCE.md)
- [Development Guide](CLAUDE.md)

## Contributing

See [open issues](https://github.com/michaelprowacki/powerrebuilder/issues) for areas needing help.

## License

Apache License 2.0 - See [LICENSE](LICENSE) for details.