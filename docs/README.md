# SIME Finch Documentation

## Overview

SIME Finch is a comprehensive PowerBuilder reverse engineering toolkit that extracts, parses, models, decompiles, and generates modern code from PowerBuilder applications. This documentation directory has been reorganized into three main consolidated documents for easier navigation and maintenance.

## Documentation Structure

### 📘 Core Documentation

1. **[ARCHITECTURE.md](ARCHITECTURE.md)** - System Design & Technical Architecture
   - Complete system overview and pipeline architecture
   - Module descriptions and interactions
   - Design decisions and patterns
   - Technical architecture diagrams
   - Integration points and data flow

2. **[IMPLEMENTATION.md](IMPLEMENTATION.md)** - Development Guide & Progress
   - Current project state and progress tracking
   - Implementation phases and timelines
   - Module-specific progress and roadmaps
   - Development guidelines and standards
   - Command reference and quick fixes

3. **[REFERENCE.md](REFERENCE.md)** - Technical References & Standards
   - PowerBuilder P-code opcode reference (583 opcodes)
   - File extension mappings and conventions
   - Opcode discovery pipeline documentation
   - Project style guide and naming conventions
   - Documentation organization overview

### 📁 Additional Resources

- **[analysis/](analysis/)** - Technical analysis documents
- **[archive/](archive/)** - Historical documentation and completed analyses
- **[issues/](issues/)** - Issue reports and debugging documentation
- **[project/](project/)** - Project configuration and structure files

## Quick Start

### For New Developers
1. Start with [ARCHITECTURE.md](ARCHITECTURE.md) to understand the system
2. Review [IMPLEMENTATION.md](IMPLEMENTATION.md) for current status and next steps
3. Consult [REFERENCE.md](REFERENCE.md) for technical details and standards

### For Contributors
1. Check [IMPLEMENTATION.md](IMPLEMENTATION.md) for immediate priorities
2. Follow style guidelines in [REFERENCE.md](REFERENCE.md)
3. Update progress tracking in relevant sections

## Key Features

- **Extraction**: PBL/PBD file extraction with 99.74% success rate
- **Parsing**: Grammar-based parsing using Lark EBNF
- **Modeling**: Comprehensive AST representation
- **Decompilation**: P-code to PowerBuilder source reconstruction
- **Generation**: Modern code generation (Flutter/Dart, Python)

## Project Status

- **Version**: 0.1.0 (Alpha)
- **Pipeline Status**: Core functional, ~60% feature complete
- **Test Coverage**: Needs improvement (target: 80%+)

For detailed status, see [IMPLEMENTATION.md](IMPLEMENTATION.md).

## Documentation Maintenance

This documentation follows a consolidated approach to reduce file sprawl:
- Active development docs are in the three main files
- Historical/completed analyses are archived
- New documentation should be added to the appropriate main file
- Keep documentation close to code when possible

---

*Last Updated: January 2025*
