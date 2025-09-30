//! Code Emitters - Adapters to external code generation
//!
//! Implements TargetEmitter trait for different output formats.

// Modern web framework emitters
pub mod flutter_emitter;
pub mod react_emitter;
pub mod vue_emitter;
pub mod svelte_emitter;
pub mod python_emitter;
pub mod docs_emitter;

// Rust native emitters
pub mod rust_emitter;
pub mod iced_emitter;

pub mod ts_emitter {
    //! TypeScript emitter
}

pub mod csharp_emitter {
    //! C# emitter
}

// Re-exports
pub use flutter_emitter::{FlutterEmitter, FlutterGeneratorConfig};
pub use react_emitter::{ReactEmitter, ReactGeneratorConfig};
pub use vue_emitter::{VueEmitter, VueGeneratorConfig};
pub use svelte_emitter::{SvelteEmitter, SvelteGeneratorConfig};
pub use python_emitter::{PythonEmitter, PythonGeneratorConfig};
pub use docs_emitter::{DocsEmitter, DocsGeneratorConfig};
pub use rust_emitter::{RustEmitter, RustGeneratorConfig};
pub use iced_emitter::{IcedEmitter, IcedGeneratorConfig};
