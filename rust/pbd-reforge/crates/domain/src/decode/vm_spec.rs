//! VM Semantics - Pure functional model of PowerBuilder VM
//!
//! Defines stack effects and semantics as pure data and functions.

use super::opcode::{Instr, StackDelta};
use serde::{Deserialize, Serialize};

/// Pure VM state for symbolic execution
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct VmState {
    pub stack_depth: usize,
    pub locals: Vec<Option<Value>>,
    pub pc: u32,
}

/// Abstract value for symbolic execution
#[derive(Debug, Clone, PartialEq, Serialize, Deserialize)]
pub enum Value {
    Const(i64),
    Unknown,
    LocalVar(usize),
    Parameter(usize),
}

/// Result of evaluating instruction
#[derive(Debug, Clone)]
pub enum SemResult {
    Continue(VmState),
    Branch { true_pc: u32, false_pc: u32 },
    Return(Option<Value>),
    Error(String),
}

/// Outcome of evaluating a basic block
#[derive(Debug, Clone)]
pub struct EvalOutcome {
    pub final_state: VmState,
    pub side_effects: Vec<String>,
}

/// VM semantics table
///
/// Pure functions defining instruction behavior
pub struct VmSemantics {
    pub stack_effect: fn(&Instr) -> StackDelta,
    pub eval: fn(&Instr, &mut VmState) -> SemResult,
}

/// Evaluate a block of instructions symbolically
pub fn eval_block(mut state: VmState, block: &[Instr]) -> EvalOutcome {
    let mut side_effects = Vec::new();

    for instr in block {
        // Simplified evaluation - real version would be more sophisticated
        state.pc = instr.position();

        match instr {
            Instr::Op { code, .. } if *code == 0x20 => {
                // CALL instruction
                side_effects.push(format!("call at {}", state.pc));
            }
            Instr::Unknown { raw, pos } => {
                side_effects.push(format!("unknown opcode 0x{:04x} at {}", raw, pos));
            }
            _ => {}
        }
    }

    EvalOutcome {
        final_state: state,
        side_effects,
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_vm_state_creation() {
        let state = VmState {
            stack_depth: 0,
            locals: vec![],
            pc: 0,
        };
        assert_eq!(state.stack_depth, 0);
    }

    #[test]
    fn test_eval_block_empty() {
        let state = VmState {
            stack_depth: 0,
            locals: vec![],
            pc: 0,
        };
        let outcome = eval_block(state, &[]);
        assert_eq!(outcome.side_effects.len(), 0);
    }
}
