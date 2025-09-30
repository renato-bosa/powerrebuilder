//! P-code Instructions
//!
//! Pure data definitions for PowerBuilder bytecode instructions.
//! Version-specific opcodes are handled through the decoder registry.

use serde::{Deserialize, Serialize};
use std::fmt;

/// Immediate operand value
#[derive(Debug, Clone, PartialEq, Serialize, Deserialize)]
pub enum Imm {
    I32(i32),
    I64(i64),
    F64(f64),
    Str(String),
    Bool(bool),
    Null,
}

impl fmt::Display for Imm {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        match self {
            Self::I32(v) => write!(f, "{}", v),
            Self::I64(v) => write!(f, "{}L", v),
            Self::F64(v) => write!(f, "{}", v),
            Self::Str(s) => write!(f, "\"{}\"", s),
            Self::Bool(b) => write!(f, "{}", b),
            Self::Null => write!(f, "null"),
        }
    }
}

/// P-code instruction
#[derive(Debug, Clone, PartialEq, Serialize, Deserialize)]
pub enum Instr {
    /// Known opcode with immediate
    Op {
        code: u16,
        imm: Option<Imm>,
        pos: u32,
    },
    /// Unknown opcode (captured for provenance)
    Unknown { raw: u16, pos: u32 },
}

impl Instr {
    pub fn position(&self) -> u32 {
        match self {
            Self::Op { pos, .. } | Self::Unknown { pos, .. } => *pos,
        }
    }

    pub fn is_unknown(&self) -> bool {
        matches!(self, Self::Unknown { .. })
    }
}

/// Stack effect of an instruction
#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub struct StackDelta {
    pub pop: usize,
    pub push: usize,
}

impl StackDelta {
    pub fn new(pop: usize, push: usize) -> Self {
        Self { pop, push }
    }

    pub fn net(&self) -> isize {
        self.push as isize - self.pop as isize
    }
}

/// Common opcode families (abstract, version-independent)
#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub enum OpFamily {
    Stack,      // push, pop, dup
    Load,       // load local/global
    Store,      // store local/global
    Arithmetic, // add, sub, mul, div
    Compare,    // eq, ne, lt, gt
    Logic,      // and, or, not
    Branch,     // jump, jumpif
    Call,       // call, return
    Object,     // new, destroy
    Property,   // getprop, setprop
    Unknown,
}

/// Map raw opcode to family
pub fn classify_opcode(code: u16) -> OpFamily {
    match code {
        0x00..=0x0F => OpFamily::Stack,
        0x10..=0x1F => OpFamily::Load,
        0x20..=0x2F => OpFamily::Store,
        0x30..=0x3F => OpFamily::Arithmetic,
        0x40..=0x4F => OpFamily::Compare,
        0x50..=0x5F => OpFamily::Logic,
        0x60..=0x6F => OpFamily::Branch,
        0x70..=0x7F => OpFamily::Call,
        0x80..=0x8F => OpFamily::Object,
        0x90..=0x9F => OpFamily::Property,
        _ => OpFamily::Unknown,
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_stack_delta_net() {
        let delta = StackDelta::new(1, 2);
        assert_eq!(delta.net(), 1);

        let delta = StackDelta::new(3, 1);
        assert_eq!(delta.net(), -2);
    }

    #[test]
    fn test_classify_opcode() {
        assert_eq!(classify_opcode(0x05), OpFamily::Stack);
        assert_eq!(classify_opcode(0x15), OpFamily::Load);
        assert_eq!(classify_opcode(0x35), OpFamily::Arithmetic);
        assert_eq!(classify_opcode(0xFF), OpFamily::Unknown);
    }

    #[test]
    fn test_imm_display() {
        assert_eq!(Imm::I32(42).to_string(), "42");
        assert_eq!(Imm::Str("hello".into()).to_string(), "\"hello\"");
        assert_eq!(Imm::Bool(true).to_string(), "true");
        assert_eq!(Imm::Null.to_string(), "null");
    }
}
