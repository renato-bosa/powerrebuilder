//! Projection - Read Models
//!
//! Indexes, cross-references, deduplication, caches.
//! Built from domain events for query optimization.

use crate::events::Event;
use serde::{Deserialize, Serialize};
use std::collections::HashMap;

/// Location in source
#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
pub struct Location {
    pub file: String,
    pub line: usize,
    pub column: usize,
}

/// Read model catalogue
#[derive(Debug, Clone, Default, Serialize, Deserialize)]
pub struct Catalogue {
    symbols: HashMap<String, Vec<Location>>,
    metrics: Metrics,
}

#[derive(Debug, Clone, Default, Serialize, Deserialize)]
pub struct Metrics {
    pub total_libraries: usize,
    pub total_artifacts: usize,
    pub total_functions: usize,
}

impl Catalogue {
    pub fn new() -> Self {
        Self::default()
    }

    pub fn add_symbol(&mut self, name: String, loc: Location) {
        self.symbols.entry(name).or_default().push(loc);
    }

    pub fn get_locations(&self, name: &str) -> Vec<Location> {
        self.symbols.get(name).cloned().unwrap_or_default()
    }

    pub fn metrics(&self) -> &Metrics {
        &self.metrics
    }
}

/// Project events into read model
///
/// Pure function building catalogue from event stream.
pub fn project(events: &[Event]) -> Catalogue {
    let mut catalogue = Catalogue::new();

    for event in events {
        match event {
            Event::LibraryImported { .. } => {
                catalogue.metrics.total_libraries += 1;
            }
            Event::ArtifactDiscovered { .. } => {
                catalogue.metrics.total_artifacts += 1;
            }
            _ => {}
        }
    }

    catalogue
}

/// Cross-reference symbol lookup
pub fn xref_symbols(cat: &Catalogue, name: &str) -> Vec<Location> {
    cat.get_locations(name)
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_catalogue() {
        let mut cat = Catalogue::new();
        cat.add_symbol(
            "test_fn".into(),
            Location {
                file: "test.rs".into(),
                line: 10,
                column: 5,
            },
        );

        let locs = xref_symbols(&cat, "test_fn");
        assert_eq!(locs.len(), 1);
        assert_eq!(locs[0].line, 10);
    }

    #[test]
    fn test_projection() {
        use crate::ingestion::LibraryId;
        use crate::decode::PBVersion;

        let events = vec![
            Event::LibraryImported {
                library_id: LibraryId::from_hash(b"test"),
                version: PBVersion::PB12,
                artifact_count: 5,
                timestamp: chrono::Utc::now(),
            },
        ];

        let cat = project(&events);
        assert_eq!(cat.metrics().total_libraries, 1);
    }
}
