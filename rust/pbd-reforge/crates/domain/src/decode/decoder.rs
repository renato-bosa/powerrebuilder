//! Decoder Port Trait
//!
//! Abstract interface for version-specific decoders.
//! Implementations live in adapters crate.

use super::opcode::Instr;
use super::version::PBVersion;
use super::vm_spec::VmSemantics;
use crate::model::pb_ir::PbUnit;
use std::fmt;

/// Error during decoding
#[derive(Debug, Clone, thiserror::Error)]
pub enum DecodeErr {
    #[error("Invalid bytecode at position {pos}: {message}")]
    InvalidBytecode { pos: usize, message: String },

    #[error("Unsupported opcode: 0x{opcode:04x} at position {pos}")]
    UnsupportedOpcode { opcode: u16, pos: usize },

    #[error("Incomplete instruction at position {pos}")]
    IncompleteInstruction { pos: usize },

    #[error("Version mismatch: expected {expected}, got {actual}")]
    VersionMismatch { expected: String, actual: String },
}

/// Version-specific decoder trait
///
/// Each PowerBuilder version implements this to provide:
/// 1. Disassembly of bytes to instructions
/// 2. Lifting instructions to PB IR
/// 3. VM semantics for analysis
pub trait VersionDecoder: Send + Sync {
    /// Version this decoder handles
    fn version(&self) -> PBVersion;

    /// Disassemble bytes to instructions
    fn disassemble(&self, bytes: &[u8]) -> Result<Vec<Instr>, DecodeErr>;

    /// Lift instructions to PowerBuilder IR
    fn lift_to_pb_ir(&self, instrs: &[Instr]) -> Result<PbUnit, DecodeErr>;

    /// Get VM semantics for this version
    fn vm_semantics(&self) -> &'static VmSemantics;
}

impl fmt::Debug for dyn VersionDecoder {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        write!(f, "VersionDecoder({})", self.version())
    }
}
