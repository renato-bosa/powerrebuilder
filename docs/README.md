# Documentation

## Overview

SIME Finch is a comprehensive PowerBuilder reverse engineering toolkit that extracts, parses, models, decompiles, and generates modern code from PowerBuilder applications.

## Documentation Structure

### 📐 Architecture
- **[architecture/ARCHITECTURE.md](architecture/ARCHITECTURE.md)** - System architecture, design patterns, and technical decisions

### 📚 Guides
- **[guides/DEVELOPMENT.md](guides/DEVELOPMENT.md)** - Development setup, coding standards, and contribution guidelines
- **[guides/DEPLOYMENT.md](guides/DEPLOYMENT.md)** - Installation, configuration, and usage instructions
- **[guides/API.md](guides/API.md)** - API reference and programmatic usage

### 📜 History
- **[history/CHANGELOG.md](history/CHANGELOG.md)** - Version history, releases, and migration notes

### 🔧 Core Technical Documentation
- **[PIPELINE_ARCHITECTURE.md](PIPELINE_ARCHITECTURE.md)** - Detailed pipeline design and data flow
- **[PIPELINE_DOCUMENTATION_UPDATE_2025-06-28.md](PIPELINE_DOCUMENTATION_UPDATE_2025-06-28.md)** - Latest pipeline improvements
- **[MODEL_MODULE_ANALYSIS.md](MODEL_MODULE_ANALYSIS.md)** - Model layer design and implementation
- **[IMPLEMENTATION.md](IMPLEMENTATION.md)** - Current implementation status and roadmap
- **[REFERENCE.md](REFERENCE.md)** - Technical references (opcodes, file formats, etc.)

### 📊 Status & Reports
- **[status/](status/)** - Analysis reports and project health metrics
- **[project/](project/)** - Project configuration and structure documentation
- **[issues/](issues/)** - Known issues and debugging guides

### 🎯 Feature-Specific Documentation

#### Extraction & Parsing
- [EXTRACTION_WARNINGS_AND_ERRORS.md](EXTRACTION_WARNINGS_AND_ERRORS.md)
- [parse_module_cleanup.md](parse_module_cleanup.md)
- [parser_to_ast_plan.md](parser_to_ast_plan.md)

#### DataWindow Support
- [PDW_EXTRACTION_CAPABILITIES.md](PDW_EXTRACTION_CAPABILITIES.md)
- [datawindow_failure_analysis.md](datawindow_failure_analysis.md)

#### Code Generation
- [POWERBUILDER_TO_FLUTTER_MAPPING.md](POWERBUILDER_TO_FLUTTER_MAPPING.md)
- [powerbuilder_flutter_conversion_example.md](powerbuilder_flutter_conversion_example.md)
- [powerbuilder_to_flutter_conversion_rules.md](powerbuilder_to_flutter_conversion_rules.md)

### 🗄️ Archive
- **[archive/](archive/)** - Historical documentation, completed work, and deprecated guides

## Quick Start

### For New Developers
1. Start with **[guides/DEVELOPMENT.md](guides/DEVELOPMENT.md)** for setup
2. Read **[architecture/ARCHITECTURE.md](architecture/ARCHITECTURE.md)** to understand the system
3. Review **[PIPELINE_ARCHITECTURE.md](PIPELINE_ARCHITECTURE.md)** for data flow

### For Users
1. See **[guides/DEPLOYMENT.md](guides/DEPLOYMENT.md)** for installation
2. Check **[guides/API.md](guides/API.md)** for programmatic usage
3. Review **[QUICK_REFERENCE.md](QUICK_REFERENCE.md)** for common tasks

### For Contributors
1. Review **[history/CHANGELOG.md](history/CHANGELOG.md)** for recent changes
2. Check **[status/](status/)** for current project health
3. See **[TODO_2025-06-22.md](TODO_2025-06-22.md)** for open tasks

## Key Features

- **Extraction**: PBL/PBD file extraction with 99.74% success rate
- **Parsing**: Grammar-based parsing using Lark EBNF
- **Modeling**: Comprehensive AST representation
- **Decompilation**: P-code to PowerBuilder source reconstruction
- **Generation**: Modern code generation (Flutter/Dart, Python)

## Project Status

- **Version**: 0.1.0 (Alpha)
- **Pipeline Status**: Core functional, ~60% feature complete
- **Test Coverage**: Improving (see latest reports in status/)

## Documentation Guidelines

1. **Keep it current** - Update docs with code changes
2. **Be concise** - Clear, direct explanations
3. **Use examples** - Show, don't just tell
4. **Archive old content** - Move outdated docs to archive/
5. **Cross-reference** - Link related documentation

---

*Last Updated: January 2025*