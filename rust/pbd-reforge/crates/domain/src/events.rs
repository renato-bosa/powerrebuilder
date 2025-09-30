//! Domain Events
//!
//! Events represent facts that have occurred in the system.
//! They are immutable and form the source of truth.

use crate::decode::PBVersion;
use crate::ingestion::{ArtifactId, ArtifactRef, LibraryId};
use chrono::{DateTime, Utc};
use serde::{Deserialize, Serialize};

/// All domain events
#[derive(Debug, Clone, Serialize, Deserialize)]
pub enum Event {
    /// Library was successfully imported
    LibraryImported {
        library_id: LibraryId,
        version: PBVersion,
        artifact_count: usize,
        timestamp: DateTime<Utc>,
    },

    /// Artifact was discovered in library
    ArtifactDiscovered {
        library_id: LibraryId,
        artifact_ref: ArtifactRef,
        timestamp: DateTime<Utc>,
    },

    /// Artifact was successfully decoded
    ArtifactDecoded {
        artifact_id: ArtifactId,
        instruction_count: usize,
        timestamp: DateTime<Utc>,
    },

    /// Control-flow graph was built
    FlowBuilt {
        artifact_id: ArtifactId,
        block_count: usize,
        timestamp: DateTime<Utc>,
    },

    /// Types were inferred
    TypesInferred {
        artifact_id: ArtifactId,
        type_count: usize,
        timestamp: DateTime<Utc>,
    },

    /// PowerBuilder IR was built
    PbIrBuilt {
        unit_id: String,
        member_count: usize,
        timestamp: DateTime<Utc>,
    },

    /// Core IR was normalized
    CoreIrNormalised {
        module_id: String,
        item_count: usize,
        timestamp: DateTime<Utc>,
    },

    /// UI IR was built
    UiIrBuilt {
        tree_id: String,
        node_count: usize,
        timestamp: DateTime<Utc>,
    },

    /// Target code was generated
    TargetGenerated {
        target_id: String,
        file_count: usize,
        timestamp: DateTime<Utc>,
    },

    /// Round-trip validation completed
    RoundTripValidated {
        original_id: LibraryId,
        result: ValidationResult,
        timestamp: DateTime<Utc>,
    },
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub enum ValidationResult {
    Success { differences: Vec<String> },
    Failure { errors: Vec<String> },
}

impl Event {
    pub fn timestamp(&self) -> DateTime<Utc> {
        match self {
            Self::LibraryImported { timestamp, .. }
            | Self::ArtifactDiscovered { timestamp, .. }
            | Self::ArtifactDecoded { timestamp, .. }
            | Self::FlowBuilt { timestamp, .. }
            | Self::TypesInferred { timestamp, .. }
            | Self::PbIrBuilt { timestamp, .. }
            | Self::CoreIrNormalised { timestamp, .. }
            | Self::UiIrBuilt { timestamp, .. }
            | Self::TargetGenerated { timestamp, .. }
            | Self::RoundTripValidated { timestamp, .. } => *timestamp,
        }
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_event_timestamp() {
        let now = Utc::now();
        let event = Event::LibraryImported {
            library_id: LibraryId::from_hash(b"test"),
            version: PBVersion::PB12,
            artifact_count: 5,
            timestamp: now,
        };

        assert_eq!(event.timestamp(), now);
    }
}
