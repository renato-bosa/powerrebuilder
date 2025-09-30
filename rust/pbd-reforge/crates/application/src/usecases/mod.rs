//! Use Cases
//!
//! Each module represents a business workflow that orchestrates domain logic.

pub mod import_library;

// Stub modules for other use cases
pub mod decode_objects {
    use crate::{AppErr, AppResult, ports::Env};
    use domain::commands::DecodePlan;
    use domain::ingestion::{ArtifactId, LibraryId};

    pub fn run(_lib: LibraryId, _plan: DecodePlan, _env: &dyn Env) -> AppResult<Vec<ArtifactId>> {
        // Implementation would:
        // 1. Load artifacts from library
        // 2. Shard by kind for parallel processing
        // 3. Decode using version-specific decoder
        // 4. Emit ArtifactDecoded events
        Ok(vec![])
    }
}

pub mod build_ir {
    use crate::{AppErr, AppResult, ports::Env};
    use domain::ingestion::ArtifactId;
    use domain::model::{CoreModule, UiTree};

    pub fn run(_ids: &[ArtifactId], _env: &dyn Env) -> AppResult<Vec<(CoreModule, Option<UiTree>)>> {
        // Implementation would:
        // 1. Lift instructions to PB IR
        // 2. Normalize to Core IR
        // 3. Extract UI IR if applicable
        // 4. Emit events for each step
        Ok(vec![])
    }
}

pub mod generate_target {
    use crate::{AppErr, AppResult};
    use domain::model::{CoreModule, UiTree};
    use domain::translation::TargetEmitter;
    use std::path::Path;

    pub fn run(
        _core: &[CoreModule],
        _ui: &[UiTree],
        _target: &dyn TargetEmitter,
        _out: &Path,
    ) -> AppResult<()> {
        // Implementation would:
        // 1. Emit core modules
        // 2. Emit UI trees
        // 3. Write files to disk
        // 4. Emit TargetGenerated event
        Ok(())
    }
}

pub mod validate_roundtrip {
    use crate::{AppErr, AppResult};
    use domain::commands::ValidationPolicy;
    use domain::ingestion::LibraryId;
    use std::path::Path;

    #[derive(Debug, Clone)]
    pub struct Report {
        pub success: bool,
        pub differences: Vec<String>,
    }

    pub fn run(_original: &LibraryId, _emitted: &Path, _policy: ValidationPolicy) -> AppResult<Report> {
        // Implementation would:
        // 1. Load original and generated
        // 2. Compare structures/behavior
        // 3. Generate report
        // 4. Emit RoundTripValidated event
        Ok(Report {
            success: true,
            differences: vec![],
        })
    }
}
