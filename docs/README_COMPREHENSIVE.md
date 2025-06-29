# SIME Finch - PowerBuilder Migration Tool

## Overview

SIME Finch is a comprehensive tool for migrating legacy PowerBuilder applications to modern languages and frameworks. It provides a complete pipeline for extracting, parsing, analyzing, and converting PowerBuilder code to Python (Tkinter) or Flutter/Dart.

## Architecture

The project follows a modular pipeline architecture:

```
┌─────────┐    ┌───────┐    ┌───────┐    ┌───────────┐    ┌──────────┐
│ EXTRACT │ -> │ PARSE │ -> │ MODEL │ -> │ DECOMPILE │ -> │ GENERATE │
└─────────┘    └───────┘    └───────┘    └───────────┘    └──────────┘
     ↓             ↓            ↓              ↓                ↓
  PBD Files    Source AST    AST Model    Enhanced AST    Target Code
```

## Project Structure

```
sime-finch/
├── extract/          # PBD file extraction
├── parse/            # PowerBuilder parsing
├── model/            # AST representation
├── decompile/        # Binary decompilation
├── generate/         # Code generation
├── common/           # Shared utilities
├── tests/            # Test suite
├── tools/            # Development tools
├── docs/             # Documentation
├── input/            # Input files
└── output/           # Generated output
```

## Pipeline Stages

### 1. Extract Stage
Extracts PowerBuilder source code from compiled PBD files:
- Reads PBD file structure
- Extracts individual objects (windows, functions, DataWindows)
- Handles corruption recovery
- Outputs source files

### 2. Parse Stage
Parses PowerBuilder source code into AST:
- Lark-based grammar parsing
- Error recovery mechanisms
- Support for all PowerBuilder constructs
- SQL and DataWindow parsing

### 3. Model Stage
Provides structured AST representation:
- Type-safe node definitions
- Visitor pattern support
- Symbol table management
- Validation and analysis

### 4. Decompile Stage
Enhances AST with decompiled information:
- P-code decompilation
- DataWindow extraction
- Control flow analysis
- Business logic mapping

### 5. Generate Stage
Converts AST to target language:
- Template-based generation
- Multiple target support (Python, Flutter)
- UI framework mapping
- Business logic conversion

## Features

### Language Support
- **PowerBuilder**: Full PowerScript support including:
  - Object-oriented features
  - Event handling
  - DataWindow syntax
  - Embedded SQL
  - Custom types

### Target Platforms
- **Python**: 
  - Tkinter UI framework
  - SQLModel for database
  - Event-driven architecture
  
- **Flutter/Dart**:
  - Material Design UI
  - State management
  - Responsive layouts

### Advanced Features
- **Error Recovery**: Continues processing despite errors
- **Corruption Handling**: Recovers from corrupted PBD files
- **Type Resolution**: Resolves complex type hierarchies
- **Dependency Analysis**: Maps object relationships
- **Security Analysis**: Identifies potential security issues

## Installation

```bash
# Clone repository
git clone https://github.com/yourusername/sime-finch.git
cd sime-finch

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

## Usage

### Basic Usage

```bash
# Extract and convert a PBD file to Python
python -m extract.extract_coordinator input.pbd --output extracted/
python -m generate.generate_coordinator extracted/ --target python --output generated/

# Direct conversion with pipeline
python pipeline.py input.pbd --target flutter --output myapp/
```

### Python API

```python
from extract import ExtractCoordinator
from parse import parse_file
from generate import GenerateCoordinator

# Extract PBD
extractor = ExtractCoordinator()
extractor.extract_pbd("app.pbd", "extracted/")

# Parse to AST
ast = parse_file("extracted/window.srw")

# Generate Python code
generator = GenerateCoordinator(target="python")
generator.generate(ast, "output/")
```

## Configuration

Configuration options in `config.yaml`:

```yaml
extraction:
  error_recovery: true
  corruption_threshold: 0.1

parsing:
  error_recovery: true
  partial_ast: true

generation:
  target: python
  ui_framework: tkinter
  layout_strategy: absolute
```

## Testing

```bash
# Run all tests
pytest

# Run specific module tests
pytest tests/test_extract/
pytest tests/test_parse/
pytest tests/test_generate/

# Run with coverage
pytest --cov=. --cov-report=html
```

## Development

### Adding New Features

1. **New Parser Grammar**: Add to `parse/grammar/`
2. **New AST Nodes**: Add to `model/core/`
3. **New Converters**: Add to `generate/converters/`
4. **New Templates**: Add to `generate/templates/`

### Code Style

```bash
# Format code
black .

# Type checking
mypy .

# Linting
ruff check .
```

## Common Issues

### PBD Extraction Issues
- **Corrupted files**: Enable error recovery in config
- **Unknown format**: Check PowerBuilder version compatibility

### Parsing Errors
- **Syntax errors**: Parser includes error recovery
- **Missing imports**: Check library dependencies

### Generation Issues
- **Template errors**: Validate template syntax
- **Type mismatches**: Check converter mappings

## Architecture Decisions

1. **Modular Pipeline**: Each stage is independent
2. **AST-based**: Central AST representation
3. **Template Generation**: Flexible output via templates
4. **Error Recovery**: Graceful handling throughout

## Contributing

1. Fork the repository
2. Create feature branch (`git checkout -b feature/amazing`)
3. Commit changes (`git commit -m 'Add amazing feature'`)
4. Push branch (`git push origin feature/amazing`)
5. Open Pull Request

## License

This project is licensed under the MIT License - see LICENSE file.

## Acknowledgments

- Lark parser for grammar support
- Jinja2 for template engine
- PowerBuilder community for documentation