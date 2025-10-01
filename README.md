# PowerRebuilder

[![GitHub Issues](https://img.shields.io/github/issues/michaelprowacki/powerrebuilder)](https://github.com/michaelprowacki/powerrebuilder/issues)
[![License](https://img.shields.io/badge/license-Apache%202.0-blue)](LICENSE)

**Rust-based reverse engineering toolkit** that decompiles compiled PowerBuilder applications (PBD/PBL files) into modern codebases.

## What It Does

PowerRebuilder extracts, decompiles, and transforms PowerBuilder applications through a complete pipeline:

1. **Extract** - Parse PBD/PBL binary archives and extract P-code bytecode
2. **Disassemble** - Convert P-code to instruction streams (591 opcodes, PB 6.0-2019)
3. **Decompile** - Lift instructions to SSA IR with CFG analysis and type inference
4. **Model** - Build semantic models (CoreModule, UiTree) from decompiled code
5. **Generate** - Emit modern code (Python, TypeScript, React, Vue, Svelte, Rust, Iced)

## Quick Start

### Installation

```bash
# Clone repository
git clone https://github.com/michaelprowacki/powerrebuilder.git
cd powerrebuilder

# Install Rust (if not already installed)
curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh

# Build
cd rust/pbd-reforge
cargo build --release
```

### Usage

**Decode PBD files** (extract and decompile):
```bash
cargo run --bin pbdreforge -- decode data/app.pbd

# Save decompiled IR to directory
cargo run --bin pbdreforge -- decode data/app.pbd --out decompiled/

# Specify PowerBuilder version
cargo run --bin pbdreforge -- decode data/app.pbd --version 12
```

**Import PBD files** (extract metadata):
```bash
cargo run --bin pbdreforge -- import data/app.pbd
```

**Generate code**:
```bash
# Generate Python/Litestar API
cargo run --bin pbdreforge -- emit python --out generated/python/

# Generate Rust code
cargo run --bin pbdreforge -- emit rust --out generated/rust/

# Generate Iced GUI application (Rust)
cargo run --bin pbdreforge -- emit iced --out generated/iced-app/

# Other targets: typescript, react, vue, svelte, docs
```

## Features

### PowerBuilder Version Support
- ✅ **PB 6.0** - 256 opcodes (0x00-0xFF)
- ✅ **PB 7.0-12.5** - 591 opcodes (0x00-0x246)
- ✅ **PB 2017-2019** - 591 opcodes with Unicode support
- ✅ **Auto-detection** - Scans for extended opcodes

### Decompilation Pipeline
- **P-code Disassembly** - Complete opcode table with operand hints
- **Control Flow Analysis** - CFG construction with dominance analysis
- **SSA Form** - Phi node insertion, variable renaming, def-use chains
- **Type Inference** - Constraint-based type recovery
- **VM Semantics** - Stack effect analysis and symbolic execution

### Code Generators
- **Python** - Litestar APIs with SQLModel/Pydantic
- **TypeScript** - Type-safe TypeScript code
- **React** - React components with hooks
- **Vue** - Vue.js 3 composition API
- **Svelte** - Svelte components
- **Rust** - Idiomatic Rust code
- **Iced** - Rust GUI applications
- **Documentation** - Markdown documentation

## Architecture

PowerRebuilder uses **Feature-Driven Modules (FDM)** with **Domain-Driven Design (DDD)**:

```
rust/pbd-reforge/
├── domain/         # Pure domain logic (no I/O)
│   ├── decode/     # P-code decompilation
│   ├── ingestion/  # PBD/PBL parsing
│   ├── model/      # Semantic models
│   └── translation/# Language ASTs
├── application/    # Use cases and ports
├── adapters/       # I/O, CLI, emitters, decoders
└── pbdreforge/     # Binary crate
```

**Design Principles:**
- **Domain-first** - Core logic independent of I/O
- **Port-Adapter** - Clean separation of concerns
- **Type-safe** - Full Rust type checking
- **Template-free** - Direct AST-based code generation

## Development

```bash
# Run tests
cargo test

# Run specific test suite
cargo test --package adapters
cargo test --test integration_test

# Check without building
cargo check

# Format and lint
cargo fmt
cargo clippy

# Documentation
cargo doc --open

# Watch for changes
cargo install cargo-watch
cargo watch -x check
```

## Testing

PowerRebuilder has been tested on real-world PBD files:

| Size | Object Count | Success Rate |
|------|-------------|--------------|
| Small (38K-97K) | 26-83 | 100% ✅ |
| Medium (264K-390K) | 242-372 | 100% ✅ |
| Large (732K-3.3M) | 689-3212 | 100% ✅ |

Test files: `data/pbd_files/`

## Documentation

- **[CLAUDE.md](CLAUDE.md)** - Comprehensive developer guide
- **[Rust Docs](rust/pbd-reforge/README.md)** - Rust implementation details
- **[GitHub Issues](https://github.com/michaelprowacki/powerrebuilder/issues)** - Bugs and feature requests

## Project History

PowerRebuilder was originally implemented in Python and has been **fully ported to Rust** for performance, type safety, and maintainability. The Python implementations are archived in `.archive/` for reference.

## Contributing

Contributions welcome! See [open issues](https://github.com/michaelprowacki/powerrebuilder/issues) for areas needing help.

Priority areas:
- PowerScript source parsing (for non-compiled objects)
- DataWindow decompilation
- Advanced control flow recovery
- Additional code generators (Go, C#, Java)

## License

Apache License 2.0 - See [LICENSE](LICENSE) for details.
