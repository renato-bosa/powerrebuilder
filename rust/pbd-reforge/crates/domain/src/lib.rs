//! Domain Layer - Pure Business Logic
//!
//! Following Domain-Driven Design (DDD) and Functional Domain Modeling (FDM) principles.
//! All domain logic is:
//! - Pure (deterministic, no side effects)
//! - Total (no panics, all errors explicit)
//! - Immutable (data structures are Copy/Clone)
//! - Domain-language focused (business terms, not CS jargon)

pub mod commands;
pub mod decode;
pub mod events;
pub mod ingestion;
pub mod model;
pub mod projection;
pub mod translation;

/// Re-export commonly used types
pub mod prelude {
    pub use crate::commands::*;
    pub use crate::events::*;
    pub use crate::ingestion::{Artifact, ArtifactKind, ArtifactRef, Library, LibraryId};
    pub use crate::decode::{PBVersion, VersionDecoder, Instr, Cfg, Ssa};
    pub use crate::model::{CoreModule, PbUnit, UiTree};
    pub use crate::translation::{TargetEmitter, EmissionUnit};
}
