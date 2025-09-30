//! Decode Bounded Context
//!
//! Parse format, disassemble bytecode, recover control and data flow, infer types.

pub mod cfg;
pub mod decoder;
pub mod infer;
pub mod opcode;
pub mod ssa;
pub mod version;
pub mod vm_spec;

pub use cfg::{BasicBlock, BlockId, Cfg, build_cfg};
pub use decoder::{DecodeErr, VersionDecoder};
pub use infer::{Ty, TypeHints, TypeMap, infer_types};
pub use opcode::{Imm, Instr, OpFamily, StackDelta, classify_opcode};
pub use ssa::{BinOp, Ssa, SsaBlock, SsaDef, SsaTerminator, SsaValue, SsaVar, to_ssa};
pub use version::{OpcodeSet, PBVersion, VersionFeatures};
pub use vm_spec::{EvalOutcome, SemResult, Value, VmSemantics, VmState, eval_block};
