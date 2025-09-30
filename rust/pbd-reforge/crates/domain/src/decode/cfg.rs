//! Control-Flow Graph Construction
//!
//! Pure function to build CFG from instructions.

use super::opcode::{classify_opcode, Instr, OpFamily};
use serde::{Deserialize, Serialize};

/// Basic block identifier
pub type BlockId = usize;

/// Basic block - straight-line code with single entry, single exit
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct BasicBlock {
    pub id: BlockId,
    pub start_pc: u32,
    pub end_pc: u32,
    pub instructions: Vec<Instr>,
    pub successors: Vec<BlockId>,
}

/// Control-Flow Graph
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct Cfg {
    pub blocks: Vec<BasicBlock>,
    pub edges: Vec<(BlockId, BlockId)>,
    pub entry_block: BlockId,
}

impl Cfg {
    pub fn new() -> Self {
        Self {
            blocks: Vec::new(),
            edges: Vec::new(),
            entry_block: 0,
        }
    }

    pub fn add_block(&mut self, block: BasicBlock) {
        self.blocks.push(block);
    }

    pub fn add_edge(&mut self, from: BlockId, to: BlockId) {
        self.edges.push((from, to));
    }
}

impl Default for Cfg {
    fn default() -> Self {
        Self::new()
    }
}

/// Build CFG from instructions
///
/// Pure function that identifies basic blocks and control flow edges.
pub fn build_cfg(instrs: &[Instr]) -> Cfg {
    if instrs.is_empty() {
        return Cfg::new();
    }

    let mut cfg = Cfg::new();
    let mut current_block = Vec::new();
    let mut block_id = 0;
    let start_pc = instrs[0].position();

    for (idx, instr) in instrs.iter().enumerate() {
        let family = match instr {
            Instr::Op { code, .. } => classify_opcode(*code),
            Instr::Unknown { .. } => OpFamily::Unknown,
        };

        current_block.push(instr.clone());

        // Block terminators: branches, calls, returns
        let is_terminator = matches!(family, OpFamily::Branch | OpFamily::Call);
        let is_last = idx == instrs.len() - 1;

        if is_terminator || is_last {
            // Create basic block
            let end_pc = instr.position();
            let block = BasicBlock {
                id: block_id,
                start_pc,
                end_pc,
                instructions: current_block.clone(),
                successors: Vec::new(),
            };
            cfg.add_block(block);

            current_block.clear();
            block_id += 1;
        }
    }

    // Simplified: linear flow for now
    for i in 0..cfg.blocks.len() - 1 {
        cfg.add_edge(i, i + 1);
    }

    cfg
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_empty_cfg() {
        let cfg = build_cfg(&[]);
        assert_eq!(cfg.blocks.len(), 0);
    }

    #[test]
    fn test_single_block() {
        let instrs = vec![Instr::Op {
            code: 0x01,
            imm: None,
            pos: 0,
        }];
        let cfg = build_cfg(&instrs);
        assert_eq!(cfg.blocks.len(), 1);
    }
}
