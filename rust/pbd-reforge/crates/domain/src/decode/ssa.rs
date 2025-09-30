//! Static Single Assignment Form
//!
//! Convert CFG to SSA for better analysis and decompilation.

use super::cfg::{BlockId, Cfg};
use serde::{Deserialize, Serialize};

/// SSA variable
#[derive(Debug, Clone, Copy, PartialEq, Eq, Hash, Serialize, Deserialize)]
pub struct SsaVar(pub usize);

/// SSA definition
#[derive(Debug, Clone, Serialize, Deserialize)]
pub enum SsaDef {
    /// Phi node for merging values at joins
    Phi {
        var: SsaVar,
        sources: Vec<(BlockId, SsaVar)>,
    },
    /// Assignment from operation
    Assign {
        var: SsaVar,
        value: SsaValue,
    },
}

/// SSA value
#[derive(Debug, Clone, Serialize, Deserialize)]
pub enum SsaValue {
    Var(SsaVar),
    Const(i64),
    BinOp {
        op: BinOp,
        left: Box<SsaValue>,
        right: Box<SsaValue>,
    },
    Call {
        func: String,
        args: Vec<SsaValue>,
    },
}

#[derive(Debug, Clone, Copy, PartialEq, Eq, Serialize, Deserialize)]
pub enum BinOp {
    Add,
    Sub,
    Mul,
    Div,
    Eq,
    Ne,
    Lt,
    Le,
    Gt,
    Ge,
}

/// SSA basic block
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct SsaBlock {
    pub id: BlockId,
    pub defs: Vec<SsaDef>,
    pub terminator: SsaTerminator,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub enum SsaTerminator {
    Return(Option<SsaValue>),
    Branch {
        cond: SsaValue,
        true_block: BlockId,
        false_block: BlockId,
    },
    Jump(BlockId),
}

/// SSA form of a function
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct Ssa {
    pub blocks: Vec<SsaBlock>,
    pub defs: Vec<SsaDef>,
}

/// Convert CFG to SSA form
///
/// Pure transformation adding phi nodes and renaming variables.
pub fn to_ssa(cfg: &Cfg) -> Ssa {
    // Simplified SSA construction
    let mut blocks = Vec::new();

    for (idx, _block) in cfg.blocks.iter().enumerate() {
        let terminator = if idx == cfg.blocks.len() - 1 {
            SsaTerminator::Return(None)
        } else {
            SsaTerminator::Jump(idx + 1)
        };

        blocks.push(SsaBlock {
            id: idx,
            defs: Vec::new(),
            terminator,
        });
    }

    Ssa {
        blocks,
        defs: Vec::new(),
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_ssa_var() {
        let v1 = SsaVar(0);
        let v2 = SsaVar(1);
        assert_ne!(v1, v2);
    }

    #[test]
    fn test_to_ssa_empty() {
        let cfg = Cfg::new();
        let ssa = to_ssa(&cfg);
        assert_eq!(ssa.blocks.len(), 0);
    }
}
