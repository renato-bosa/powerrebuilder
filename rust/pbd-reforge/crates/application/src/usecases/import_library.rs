//! Import Library Use Case
//!
//! Orchestrates library import workflow.

use crate::ports::Repos;
use crate::{AppErr, AppResult};
use domain::decode::PBVersion;
use domain::ingestion::{accept_import, LibraryId};
use std::fs;
use std::path::Path;

/// Execute library import use case
///
/// 1. Load file bytes
/// 2. Parse and validate library
/// 3. Emit domain events
/// 4. Return library ID
pub fn run(
    path: &Path,
    version_hint: Option<PBVersion>,
    repos: &dyn Repos,
) -> AppResult<LibraryId> {
    // Load bytes (effect at boundary)
    let bytes = fs::read(path)?;

    // Pure domain function
    let (library, events) =
        accept_import(&bytes, version_hint).map_err(|e| AppErr::Domain(e.to_string()))?;

    // Persist events (effect at boundary)
    repos.put_events(&events)?;

    Ok(library.id)
}

#[cfg(test)]
mod tests {
    use super::*;

    struct MockRepos;

    impl Repos for MockRepos {
        fn put_events(&self, _events: &[domain::events::Event]) -> std::io::Result<()> {
            Ok(())
        }

        fn get_bytes(&self, _id: domain::ingestion::ArtifactId) -> std::io::Result<Vec<u8>> {
            Ok(vec![])
        }

        fn list_artifacts(&self) -> std::io::Result<Vec<domain::ingestion::ArtifactId>> {
            Ok(vec![])
        }
    }

    #[test]
    fn test_import_validates_input() {
        let repos = MockRepos;
        let result = run(Path::new("/nonexistent"), None, &repos);
        assert!(result.is_err());
    }
}
