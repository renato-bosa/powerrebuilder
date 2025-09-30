# PBD Reforge - PowerBuilder Reverse Engineering in Rust

A fast, extensible reverse-engineering system that ingests PowerBuilder (PB) PBD libraries, recovers source, raises a language-neutral Intermediate Representation (IR), and re-emits to Rust with Iced GUI as well as other targets.

Built following **Functional Domain Modeling (FDM)** and **Domain-Driven Design (DDD)** principles.

## Architecture

### Bounded Contexts

1. **Ingestion** - Discover libraries and artifacts
2. **Decode** - Parse format, disassemble bytecode, recover control/data flow, infer types
3. **Model** - Raise PowerBuilder-aware IR then normalize to core language-neutral IR + UI IR
4. **Translation** - Map IR to target ASTs and project files
5. **Projection** - Indexes, cross-refs, dedup, caches
6. **Orchestration** - Pipelines, concurrency, fault isolation (application layer)
7. **Verification** - Round-trip checks, partial evaluation, golden tests

### Layers

```
┌─────────────────────────────────────────────┐
│              Binary (pbdreforge)            │
│         Composition Root & CLI              │
└─────────────────────────────────────────────┘
                      ↓
┌─────────────────────────────────────────────┐
│            Adapters Layer                   │
│  I/O • PB Decoders • Emitters • Telemetry   │
└─────────────────────────────────────────────┘
                      ↓
┌─────────────────────────────────────────────┐
│          Application Layer                  │
│    Use Cases • Services • Ports             │
└─────────────────────────────────────────────┘
                      ↓
┌─────────────────────────────────────────────┐
│            Domain Layer                     │
│  Pure Business Logic • Events • Commands    │
│  7 Bounded Contexts (see above)             │
└─────────────────────────────────────────────┘
```

### Domain Architecture Rules

- **Pure Domain**: All domain functions are total, deterministic, no panics
- **Events & Commands**: Event-sourced aggregates
- **Data-Driven Versioning**: No hardcoded version branches
- **Domain Language**: Business terms (not "workflow", "manager", "service")
- **Vertical Slices**: Self-contained modules per object kind
- **Safety**: Unknown opcodes become explicit IR nodes with provenance

## Project Structure

```
pbd-reforge/
├── Cargo.toml              # Workspace root
├── bin/
│   └── pbdreforge.rs       # CLI composition root
├── crates/
│   ├── domain/             # Pure domain logic
│   │   └── src/
│   │       ├── ingestion/  # Library & artifact discovery
│   │       ├── decode/     # Bytecode disassembly & analysis
│   │       ├── model/      # IR representations (PB, Core, UI)
│   │       ├── translation/# Target code generation
│   │       ├── projection/ # Read models & queries
│   │       ├── commands.rs # Domain commands
│   │       └── events.rs   # Domain events
│   │
│   ├── application/        # Use cases & orchestration
│   │   └── src/
│   │       ├── usecases/   # Business workflows
│   │       ├── services/   # Pipeline, cache, scheduler
│   │       └── ports.rs    # Abstract interfaces
│   │
│   └── adapters/           # Infrastructure implementations
│       └── src/
│           ├── io/         # Filesystem, mmap, SQLite
│           ├── pb/         # PB version decoders
│           ├── emit/       # Code emitters (Rust, Iced, TS, C#)
│           ├── cli/        # CLI argument parsing
│           └── telemetry/  # Logging & metrics
```

## Usage

### Build

```bash
cd rust/pbd-reforge
cargo build --release
```

### Commands

```bash
# Import a PowerBuilder library
pbdreforge import path/to/lib.pbd --version 12.5

# Decode artifacts
pbdreforge decode <library-id>

# Generate Rust + Iced code
pbdreforge emit rust+iced --out ./output

# Validate round-trip
pbdreforge validate --out ./output
```

## Key Traits

### VersionDecoder (Domain Port)

```rust
pub trait VersionDecoder: Send + Sync {
    fn version(&self) -> PBVersion;
    fn disassemble(&self, bytes: &[u8]) -> Result<Vec<Instr>, DecodeErr>;
    fn lift_to_pb_ir(&self, instrs: &[Instr]) -> Result<PbUnit, DecodeErr>;
    fn vm_semantics(&self) -> &'static VmSemantics;
}
```

### TargetEmitter (Domain Port)

```rust
pub trait TargetEmitter: Send + Sync {
    fn target_id(&self) -> &'static str;
    fn supports(&self, features: &FeatureSet) -> bool;
    fn emit_core(&self, ir: &CoreModule) -> Result<EmissionUnit, EmitErr>;
    fn emit_ui(&self, ui: &UiTree) -> Result<EmissionUnit, EmitErr>;
}
```

## Performance Features

- **Memory-mapped I/O**: Zero-copy file access via memmap2
- **Parallel Processing**: Rayon-based data parallelism for artifact decoding
- **Content-Addressed Caching**: Blake3 hashes for incremental builds
- **Deterministic Scheduling**: Reproducible outputs

## Extensibility

### Adding a New PowerBuilder Version

1. Implement `VersionDecoder` trait in `adapters/src/pb/`
2. Register in version registry
3. No changes to domain logic required

### Adding a New Target Language

1. Implement `TargetEmitter` trait in `adapters/src/emit/`
2. Register in emitter registry
3. No changes to domain or application logic required

## Development

### Testing

```bash
# Run all tests
cargo test

# Run domain tests only
cargo test -p domain

# Run with logging
RUST_LOG=debug cargo test
```

### Linting

```bash
cargo clippy --all-targets --all-features
```

### Formatting

```bash
cargo fmt --all
```

## Reverse Engineering Methods

1. **Format Parsing**: Strict spec with tolerant fallback
2. **Signature Scanning**: Entropy heuristics to locate bytecode
3. **Bytecode Disassembly**: Version-specific VM semantics
4. **Emulator-Assisted**: Pure VM model for constant refinement
5. **CFG & SSA**: High-quality decompilation
6. **Type Inference**: From usage, literals, UI bindings, DataWindow metadata
7. **Provenance Tracking**: Every IR node has source attribution

## Status

🚧 **Early Development** - Core architecture established, implementation in progress.

### Completed

- ✅ Workspace structure with 3 crates + binary
- ✅ Domain layer with 7 bounded contexts
- ✅ Application layer with use cases and services
- ✅ Adapters layer scaffolding
- ✅ CLI composition root
- ✅ Event-sourced architecture
- ✅ Pure domain functions

### In Progress

- 🔨 PowerBuilder version decoders (PB6, PB12, PB2019)
- 🔨 Code emitters (Rust, Iced, TypeScript, C#)
- 🔨 Full CFG and SSA implementation
- 🔨 Type inference engine

### Planned

- 📋 Round-trip validation framework
- 📋 Incremental caching
- 📋 SQLite catalogue for projections
- 📋 Web UI for browsing decompiled code

## Contributing

This project follows strict FDM and DDD principles. All contributions must:

1. Keep domain pure (no I/O, no panics, total functions)
2. Use Result types for error handling
3. Emit events for all state changes
4. Use business terminology (not CS jargon)
5. Colocate types with functions in same module

## License

MIT License - See LICENSE file for details.
