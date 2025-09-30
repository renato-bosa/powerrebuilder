//! Target Emitter Port Trait
//!
//! Abstract interface for code generation to different target languages/frameworks.

use crate::model::{CoreModule, UiTree};
use std::collections::HashMap;
use std::fmt;

/// Feature set query
#[derive(Debug, Clone)]
pub struct FeatureSet {
    pub features: Vec<String>,
}

impl FeatureSet {
    pub fn new() -> Self {
        Self { features: Vec::new() }
    }

    pub fn with_feature(mut self, feature: impl Into<String>) -> Self {
        self.features.push(feature.into());
        self
    }

    pub fn has(&self, feature: &str) -> bool {
        self.features.iter().any(|f| f == feature)
    }
}

impl Default for FeatureSet {
    fn default() -> Self {
        Self::new()
    }
}

/// Emission unit - generated code ready to write
#[derive(Debug, Clone)]
pub struct EmissionUnit {
    pub files: Vec<EmittedFile>,
    pub metadata: HashMap<String, String>,
}

#[derive(Debug, Clone)]
pub struct EmittedFile {
    pub path: String,
    pub content: String,
    pub is_executable: bool,
}

/// Error during emission
#[derive(Debug, Clone, thiserror::Error)]
pub enum EmitErr {
    #[error("Unsupported feature: {0}")]
    UnsupportedFeature(String),

    #[error("Invalid IR structure: {0}")]
    InvalidIr(String),

    #[error("Code generation failed: {0}")]
    GenerationFailed(String),
}

/// Target emitter trait
///
/// Implementations generate code for specific languages/frameworks.
pub trait TargetEmitter: Send + Sync {
    /// Target identifier (e.g., "rust", "rust+iced", "typescript")
    fn target_id(&self) -> &'static str;

    /// Check if this emitter supports required features
    fn supports(&self, features: &FeatureSet) -> bool;

    /// Emit code from Core IR
    fn emit_core(&self, ir: &CoreModule) -> Result<EmissionUnit, EmitErr>;

    /// Emit UI code from UI IR
    fn emit_ui(&self, ui: &UiTree) -> Result<EmissionUnit, EmitErr>;
}

impl fmt::Debug for dyn TargetEmitter {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        write!(f, "TargetEmitter({})", self.target_id())
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_feature_set() {
        let features = FeatureSet::new()
            .with_feature("async")
            .with_feature("gui");

        assert!(features.has("async"));
        assert!(features.has("gui"));
        assert!(!features.has("web"));
    }

    #[test]
    fn test_emission_unit() {
        let unit = EmissionUnit {
            files: vec![EmittedFile {
                path: "main.rs".into(),
                content: "fn main() {}".into(),
                is_executable: true,
            }],
            metadata: HashMap::new(),
        };

        assert_eq!(unit.files.len(), 1);
        assert_eq!(unit.files[0].path, "main.rs");
    }
}
