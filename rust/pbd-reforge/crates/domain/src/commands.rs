//! Domain Commands
//!
//! Commands represent intentions to change system state.
//! They are validated and, if successful, emit events.

use crate::decode::PBVersion;
use crate::ingestion::{ArtifactId, LibraryId};
use serde::{Deserialize, Serialize};
use std::collections::HashMap;
use std::path::PathBuf;

/// Import a PowerBuilder library
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct ImportLibrary {
    pub path: PathBuf,
    pub version_hint: Option<PBVersion>,
}

/// Plan how to decode artifacts
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct PlanDecode {
    pub library_id: LibraryId,
    pub strategy: DecodeStrategy,
}

/// Alias for backward compatibility
pub type DecodePlan = PlanDecode;

#[derive(Debug, Clone, Serialize, Deserialize)]
pub enum DecodeStrategy {
    Parallel,
    Sequential,
    Adaptive,
}

/// Decode a single artifact
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct DecodeArtifact {
    pub artifact_id: ArtifactId,
    pub version: PBVersion,
}

/// Build PowerBuilder IR from decoded artifact
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct BuildPbIr {
    pub artifact_id: ArtifactId,
}

/// Normalize PB IR to Core IR
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct NormaliseToCoreIr {
    pub pb_unit_id: String,
}

/// Build UI IR from PB IR
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct BuildUiIr {
    pub pb_unit_id: String,
}

/// Generate code for target
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct GenerateTarget {
    pub target_id: String,
    pub core_modules: Vec<String>,
    pub ui_trees: Vec<String>,
    pub options: HashMap<String, String>,
}

/// Validate round-trip transformation
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct ValidateRoundTrip {
    pub original_library: LibraryId,
    pub generated_path: PathBuf,
    pub policy: ValidationPolicy,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub enum ValidationPolicy {
    Structural,
    Behavioral,
    Full,
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_import_command() {
        let cmd = ImportLibrary {
            path: PathBuf::from("/test/lib.pbd"),
            version_hint: None,
        };
        assert_eq!(cmd.path, PathBuf::from("/test/lib.pbd"));
    }
}
