//! I/O Adapters

pub mod fs_repo {
    //! Filesystem repository with memory-mapped I/O

    use application::ports::Repos;
    use domain::events::Event;
    use domain::ingestion::ArtifactId;

    pub struct FsRepo {
        base_path: std::path::PathBuf,
    }

    impl FsRepo {
        pub fn new(base_path: std::path::PathBuf) -> Self {
            Self { base_path }
        }
    }

    impl Repos for FsRepo {
        fn put_events(&self, _events: &[Event]) -> std::io::Result<()> {
            // Write events to event store
            Ok(())
        }

        fn get_bytes(&self, _id: ArtifactId) -> std::io::Result<Vec<u8>> {
            // Load artifact bytes
            Ok(vec![])
        }

        fn list_artifacts(&self) -> std::io::Result<Vec<ArtifactId>> {
            Ok(vec![])
        }
    }
}

#[cfg(feature = "sqlite")]
pub mod sqlite_catalogue {
    //! SQLite-backed catalogue for projections
}
