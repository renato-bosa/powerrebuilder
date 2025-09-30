//! Application Ports
//!
//! Abstract interfaces for infrastructure dependencies.

use domain::events::Event;
use domain::ingestion::ArtifactId;
use std::path::Path;

/// Repository port for event persistence and data access
pub trait Repos: Send + Sync {
    /// Persist events to storage
    fn put_events(&self, events: &[Event]) -> std::io::Result<()>;

    /// Retrieve artifact bytes by ID
    fn get_bytes(&self, id: ArtifactId) -> std::io::Result<Vec<u8>>;

    /// List all artifact IDs
    fn list_artifacts(&self) -> std::io::Result<Vec<ArtifactId>>;
}

/// Clock port for time operations
pub trait Clock: Send + Sync {
    /// Current UTC timestamp
    fn now(&self) -> chrono::DateTime<chrono::Utc>;
}

/// Hashing port for content addressing
pub trait Hasher: Send + Sync {
    /// Hash bytes to content address
    fn hash(&self, bytes: &[u8]) -> [u8; 32];
}

/// Environment aggregates all ports
pub trait Env: Send + Sync {
    fn repos(&self) -> &dyn Repos;
    fn clock(&self) -> &dyn Clock;
    fn hasher(&self) -> &dyn Hasher;
}

/// Standard library clock implementation
pub struct SystemClock;

impl Clock for SystemClock {
    fn now(&self) -> chrono::DateTime<chrono::Utc> {
        chrono::Utc::now()
    }
}
