//! Adapters Layer - Infrastructure and External Integrations
//!
//! Implements ports defined by domain and application layers.
//! All side effects (I/O, external systems) happen here.

pub mod cli;
pub mod emit;
pub mod io;
pub mod pb;
pub mod telemetry;

// Re-export commonly used adapters
pub use io::fs_repo::FsRepo;
pub use pb::pbd_reader::PbdReader;
