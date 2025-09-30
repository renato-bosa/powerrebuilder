//! Library - The PowerBuilder library aggregate.
//!
//! Following FDM principles:
//! - Types colocated with their functions
//! - Immutable data structures
//! - Parse, don't validate (types only constructable via smart constructors)

use crate::decode::PBVersion;
use crate::events::Event;
use crate::ingestion::artifact::ArtifactRef;
use serde::{Deserialize, Serialize};
use std::fmt;

/// Unique identifier for a library
#[derive(Debug, Clone, Copy, PartialEq, Eq, Hash, Serialize, Deserialize)]
pub struct LibraryId(u64);

impl LibraryId {
    /// Create a new library ID from bytes hash
    pub fn from_hash(bytes: &[u8]) -> Self {
        use std::collections::hash_map::DefaultHasher;
        use std::hash::{Hash, Hasher};

        let mut hasher = DefaultHasher::new();
        bytes.hash(&mut hasher);
        Self(hasher.finish())
    }

    pub fn value(&self) -> u64 {
        self.0
    }
}

impl fmt::Display for LibraryId {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        write!(f, "{:016x}", self.0)
    }
}

/// The Library aggregate - root entity for ingestion context
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct Library {
    pub id: LibraryId,
    pub version: PBVersion,
    pub artifacts: Vec<ArtifactRef>,
}

/// Error during library import
#[derive(Debug, Clone, thiserror::Error)]
pub enum ImportErr {
    #[error("Invalid library format: {0}")]
    InvalidFormat(String),

    #[error("Unsupported version: {0}")]
    UnsupportedVersion(String),

    #[error("Corrupted data at offset {offset}: {message}")]
    CorruptedData { offset: usize, message: String },

    #[error("Empty library")]
    EmptyLibrary,
}

/// Accept import of library bytes
///
/// Pure function that parses library data and emits domain events.
/// This is the primary entry point for the ingestion context.
pub fn accept_import(
    bytes: &[u8],
    hint: Option<PBVersion>,
) -> Result<(Library, Vec<Event>), ImportErr> {
    // Validate minimum size
    if bytes.len() < 4 {
        return Err(ImportErr::InvalidFormat(
            "File too small to be a valid library".into(),
        ));
    }

    // Detect format and version
    let version = if let Some(v) = hint {
        v
    } else {
        detect_version(bytes)?
    };

    // Parse library structure
    let artifacts = extract_artifact_refs(bytes, version)?;

    if artifacts.is_empty() {
        return Err(ImportErr::EmptyLibrary);
    }

    let id = LibraryId::from_hash(bytes);

    let library = Library {
        id,
        version,
        artifacts: artifacts.clone(),
    };

    // Emit domain events
    let mut events = vec![Event::LibraryImported {
        library_id: id,
        version,
        artifact_count: artifacts.len(),
        timestamp: chrono::Utc::now(),
    }];

    for artifact in artifacts {
        events.push(Event::ArtifactDiscovered {
            library_id: id,
            artifact_ref: artifact,
            timestamp: chrono::Utc::now(),
        });
    }

    Ok((library, events))
}

/// Detect PowerBuilder version from library bytes
fn detect_version(bytes: &[u8]) -> Result<PBVersion, ImportErr> {
    // Check for HDR* signature (modern PBD format - PB 7.0+)
    if bytes.starts_with(b"HDR*") {
        return Ok(PBVersion::new(12, 5)); // Default to 12.5 for modern format
    }

    // Check for PBL signature (classic format)
    if bytes.starts_with(b"PBL") {
        // Try to read version from header
        if bytes.len() >= 8 {
            let version_byte = bytes[4];
            return Ok(PBVersion::new((version_byte / 10) as u16, (version_byte % 10) as u16));
        }
        return Ok(PBVersion::new(6, 0)); // Default to 6.0
    }

    Err(ImportErr::InvalidFormat(
        "Unknown file signature".into(),
    ))
}

/// Extract artifact references from library bytes
fn extract_artifact_refs(bytes: &[u8], version: PBVersion) -> Result<Vec<ArtifactRef>, ImportErr> {
    // This is a simplified extraction - real implementation would parse the full structure
    let mut refs = Vec::new();

    if bytes.starts_with(b"HDR*") {
        // Modern PBD format
        extract_hdr_artifacts(bytes, &mut refs)?;
    } else if bytes.starts_with(b"PBL") {
        // Classic PBL format
        extract_pbl_artifacts(bytes, &mut refs)?;
    }

    Ok(refs)
}

fn extract_hdr_artifacts(bytes: &[u8], refs: &mut Vec<ArtifactRef>) -> Result<(), ImportErr> {
    // Find ENT* section
    let ent_pos = bytes.windows(4).position(|w| w == b"ENT*");

    if let Some(pos) = ent_pos {
        // Simplified: just mark one artifact span
        // Real implementation would parse full ENT* structure
        refs.push(ArtifactRef {
            name: "extracted_object".into(),
            kind: crate::ingestion::artifact::ArtifactKind::Unknown,
            span: crate::ingestion::artifact::ByteSpan {
                offset: pos,
                length: bytes.len() - pos,
            },
        });
    }

    Ok(())
}

fn extract_pbl_artifacts(bytes: &[u8], refs: &mut Vec<ArtifactRef>) -> Result<(), ImportErr> {
    // Classic PBL format parsing would go here
    // Simplified for now
    refs.push(ArtifactRef {
        name: "pbl_object".into(),
        kind: crate::ingestion::artifact::ArtifactKind::Unknown,
        span: crate::ingestion::artifact::ByteSpan {
            offset: 0,
            length: bytes.len(),
        },
    });

    Ok(())
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_detect_hdr_format() {
        let mut data = vec![0u8; 1024];
        data[0..4].copy_from_slice(b"HDR*");

        let version = detect_version(&data).unwrap();
        assert!(version.major >= 7);
    }

    #[test]
    fn test_library_id_deterministic() {
        let data = b"test data";
        let id1 = LibraryId::from_hash(data);
        let id2 = LibraryId::from_hash(data);
        assert_eq!(id1, id2);
    }
}
