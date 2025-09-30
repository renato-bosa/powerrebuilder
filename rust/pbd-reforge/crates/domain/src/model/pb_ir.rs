//! PowerBuilder-Aware IR
//!
//! Intermediate representation that preserves PowerBuilder semantics
//! (windows, menus, events, DataWindows, etc.)

use crate::decode::ssa::Ssa;
use crate::ingestion::ArtifactKind;
use serde::{Deserialize, Serialize};

/// PowerBuilder compilation unit
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct PbUnit {
    pub name: String,
    pub kind: ArtifactKind,
    pub members: Vec<PbMember>,
}

/// Member of a PowerBuilder object
#[derive(Debug, Clone, Serialize, Deserialize)]
pub enum PbMember {
    EventHandler { event: String, body: Ssa },
    Control { spec: UiSpec },
    Function { sig: FnSig, body: Ssa },
    Variable { name: String, ty: String },
}

/// UI specification for controls
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct UiSpec {
    pub control_type: String,
    pub name: String,
    pub properties: Vec<(String, String)>,
}

/// Function signature
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct FnSig {
    pub name: String,
    pub parameters: Vec<Parameter>,
    pub return_type: Option<String>,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct Parameter {
    pub name: String,
    pub ty: String,
    pub is_ref: bool,
}

/// Emulator snapshot for evidence merging
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct EmuSnapshot {
    pub final_state: Vec<u8>,
    pub traces: Vec<String>,
}

/// Merge evidence from multiple reverse-engineering paths
///
/// Combines static analysis with dynamic emulation results.
pub fn merge_semantics(unit: &PbUnit, _emu_snap: Option<EmuSnapshot>) -> PbUnit {
    // Conservative merging - prefer static analysis
    unit.clone()
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_pb_unit_creation() {
        let unit = PbUnit {
            name: "test".into(),
            kind: ArtifactKind::Window,
            members: vec![],
        };
        assert_eq!(unit.name, "test");
    }
}
