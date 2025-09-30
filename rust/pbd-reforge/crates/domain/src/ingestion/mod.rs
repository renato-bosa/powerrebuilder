//! Ingestion Bounded Context
//!
//! Discovers libraries and extracts artifact references.
//! Pure domain logic for library import and artifact discovery.

pub mod artifact;
pub mod library;

pub use artifact::{Artifact, ArtifactId, ArtifactKind, ArtifactRef, ByteSpan, SymTab, classify};
pub use library::{Library, LibraryId, ImportErr, accept_import};
