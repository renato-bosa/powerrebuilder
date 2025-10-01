# CLAUDE.md - PowerRebuilder Developer Guide

This file provides accurate guidance for Claude Code and developers working with PowerRebuilder.

## Project Overview

PowerRebuilder is a **Rust-based reverse engineering toolkit** that decompiles compiled PowerBuilder applications (PBD/PBL files) into modern codebases.

**Current Status:** The project has been fully ported to Rust with a complete decompilation and code generation pipeline.

## Architecture

PowerRebuilder uses **Feature-Driven Modules (FDM)** with **Domain-Driven Design (DDD)**:

```
rust/pbd-reforge/
├── crates/
│   ├── domain/         # Core domain logic (pure Rust, no I/O)
│   │   ├── decode/     # P-code decompilation (opcodes, CFG, SSA, type inference)
│   │   ├── ingestion/  # PBD/PBL parsing
│   │   ├── model/      # Semantic models (CoreModule, UiTree)
│   │   └── translation/# Language-agnostic ASTs (RustAst, IcedView, etc.)
│   ├── application/    # Use cases and ports (traits)
│   ├── adapters/       # I/O adapters (CLI, file I/O, emitters, decoders)
│   └── pbdreforge/     # Binary crate (main application)
└── bin/
    └── pbdreforge.rs   # CLI entry point
```

## Installation & Commands

### Setup
```bash
# Install Rust (if not already installed)
curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh

# Build the project
cd rust/pbd-reforge
cargo build --release

# Or use debug build for development
cargo build
```

### Running the CLI

**Decode PBD Files** (Extract and decompile P-code):
```bash
cargo run --bin pbdreforge -- decode <pbd-file> [--version 6|12|2019] [--out <dir>]

# Examples:
cargo run --bin pbdreforge -- decode data/app.pbd
cargo run --bin pbdreforge -- decode data/app.pbd --out decompiled/
cargo run --bin pbdreforge -- decode data/app.pbd --version 12
```

**Import PBD Files** (Parse and extract metadata):
```bash
cargo run --bin pbdreforge -- import <pbd-file>
```

**Emit Code** (Generate modern code from models):
```bash
cargo run --bin pbdreforge -- emit <target> --out <dir>

# Targets: python, typescript, react, vue, svelte, rust, iced, docs
cargo run --bin pbdreforge -- emit python --out generated/python/
cargo run --bin pbdreforge -- emit rust --out generated/rust/
cargo run --bin pbdreforge -- emit iced --out generated/iced-app/
```

### Testing

```bash
# Run all tests
cargo test

# Run specific test suite
cargo test --package adapters
cargo test --package domain

# Run integration tests
cargo test --test integration_test

# Run with output
cargo test -- --nocapture
```

### Development

```bash
# Check code without building
cargo check

# Format code
cargo fmt

# Lint code
cargo clippy

# Build documentation
cargo doc --open

# Watch for changes (requires cargo-watch)
cargo install cargo-watch
cargo watch -x check
```

## PowerBuilder Decompilation Pipeline

### Stage 1: Extract P-code
- **Input**: PBD/PBL binary archives
- **Output**: Raw P-code bytecode
- **Module**: `adapters::pb::pbd_reader`

### Stage 2: Disassemble
- **Input**: P-code bytecode
- **Output**: Instruction stream
- **Module**: `adapters::pb::{pb6_decoder, pb12_decoder, pb2019_decoder}`
- **Features**:
  - 591 PowerBuilder opcodes (0x00-0x246)
  - Version-specific decoding (PB 6.0, 8.0-12.5, 2017-2019)
  - Automatic version detection

### Stage 3: Lift to IR
- **Input**: Instruction stream
- **Output**: PowerBuilder IR (PbUnit with SSA form)
- **Module**: `domain::decode`
- **Features**:
  - Control Flow Graph (CFG) construction
  - Static Single Assignment (SSA) conversion
  - Type inference with constraint solving
  - VM semantics for symbolic execution

### Stage 4: Model Extraction
- **Input**: PowerBuilder IR
- **Output**: Semantic models (CoreModule, UiTree)
- **Module**: `domain::model`

### Stage 5: Code Generation
- **Input**: Semantic models
- **Output**: Modern application code
- **Module**: `adapters::emit`
- **Generators**:
  - `python_emitter` - Python/Litestar APIs
  - `typescript_emitter` - TypeScript code
  - `react_emitter` - React components
  - `vue_emitter` - Vue.js components
  - `svelte_emitter` - Svelte components
  - `rust_emitter` - Rust code
  - `iced_emitter` - Iced GUI applications (Rust)
  - `docs_emitter` - Markdown documentation

## PowerBuilder Version Support

| Version | Opcode Range | Decoder | Status |
|---------|-------------|---------|--------|
| PB 6.0 | 0x00-0xFF (256) | `Pb6Decoder` | ✅ Complete |
| PB 7.0-12.5 | 0x00-0x246 (591) | `Pb12Decoder` | ✅ Complete |
| PB 2017-2019 | 0x00-0x246 (591) | `Pb2019Decoder` | ✅ Complete |

**Auto-detection**: Scans bytecode for extended opcodes (> 0xFF) to determine version.

## Key Implementation Notes

### Domain Types
- **`PbUnit`** - Decompiled PowerBuilder artifact (function, window, user object)
- **`CoreModule`** - Language-agnostic module with data definitions and functions
- **`UiTree`** - UI component tree for frontend generation
- **`RustAst`** - Rust abstract syntax tree for code emission
- **`IcedView`** - Iced GUI component tree

### Decompilation Features
- **Opcode Table**: Complete 591-opcode table with mnemonics and operand hints
- **CFG Analysis**: Basic block detection, edge construction, dominance analysis
- **SSA Form**: Phi node insertion, variable renaming, def-use chains
- **Type Inference**: Constraint-based type recovery with PowerBuilder type system
- **VM Semantics**: Stack effect analysis and symbolic evaluation

### Code Generation Features
- **Translation Layer**: Pure domain types → language-specific ASTs
- **Emitters**: AST → concrete code with proper formatting
- **Template-free**: Direct code construction (no Jinja2/templating)
- **Type-safe**: Full Rust type checking throughout pipeline

## Testing with Real PBD Files

Test files are located in `data/pbd_files/`:
```
data/pbd_files/
├── small/  (38K-97K)   - 26-83 objects
├── medium/ (264K-390K) - 242-372 objects
└── large/  (732K-3.3M) - 689-3212 objects
```

Tested decode success rate: **100%** across all file sizes.

## Archived Python Code

The original Python implementations have been archived in `.archive/`:
- `.archive/src-original/` - Original Python pipeline
- `.archive/src_new/` - Second Python iteration
- `.archive/scripts/` - Standalone processing scripts
- `.archive/tests-python/` - Python test suite
- `.archive/config/` - Python configuration (pyproject.toml, pytest.ini, taskfile.yml)

These are kept for reference but are no longer maintained.

## Common Development Tasks

### Add Support for New PowerBuilder Feature
1. Update domain types in `domain/src/decode/` (e.g., add new opcode)
2. Update decompiler logic if needed
3. Add translation in `domain/src/translation/`
4. Update emitters in `adapters/src/emit/`
5. Add tests

### Add New Code Generator
1. Create translation types in `domain/src/translation/` (e.g., `go_ast.rs`)
2. Implement emitter in `adapters/src/emit/` (e.g., `go_emitter.rs`)
3. Register in CLI (`bin/pbdreforge.rs`)
4. Add integration test

### Debug Decompilation Issues
```bash
# Enable debug logging
RUST_LOG=debug cargo run --bin pbdreforge -- decode file.pbd

# Inspect intermediate IR
cargo run --bin pbdreforge -- decode file.pbd --out ir/ --format json

# Run single test with output
cargo test test_name -- --nocapture --test-threads=1
```

## Getting Help

- **GitHub Issues**: https://github.com/michaelprowacki/powerrebuilder/issues
- **Documentation**: `cargo doc --open` for inline Rust docs
- **Codebase**: Start with `bin/pbdreforge.rs` → follow imports

## Project Status

- ✅ PBD/PBL binary parsing
- ✅ P-code extraction and disassembly
- ✅ CFG/SSA decompilation
- ✅ Type inference
- ✅ 8 code generators (Python, TypeScript, React, Vue, Svelte, Rust, Iced, Docs)
- ✅ CLI with import/emit/decode commands
- ✅ Integration tests
- 🚧 PowerScript source parsing (for non-compiled objects)
- 🚧 DataWindow decompilation
- 🚧 Advanced control flow recovery
