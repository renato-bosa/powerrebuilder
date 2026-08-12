//! Minimal PowerBuilder-specific control-flow model for semantic reconstruction.
//!
//! This deliberately models only instruction boundaries, direct branches,
//! fallthrough, and the exception table encoded by `PUSH_TRY`. It is not a
//! general CFG/SSA framework and does not attempt high-level structuring.

use std::collections::{BTreeSet, HashMap, HashSet};

use serde::Serialize;

use super::pcode_scanner::{PCodeInstruction, PCodeScan};

#[derive(Debug, Clone, PartialEq, Eq, Serialize)]
pub struct SemanticControlFlow {
    pub valid: bool,
    pub errors: Vec<String>,
    pub blocks: Vec<SemanticBasicBlock>,
    pub edges: Vec<SemanticFlowEdge>,
    pub exception_regions: Vec<ExceptionRegion>,
}

#[derive(Debug, Clone, PartialEq, Eq, Serialize)]
pub struct SemanticBasicBlock {
    pub id: usize,
    pub start_offset: usize,
    pub end_offset_exclusive: usize,
    pub instruction_offsets: Vec<usize>,
}

#[derive(Debug, Clone, Copy, PartialEq, Eq, Serialize)]
#[serde(rename_all = "snake_case")]
pub enum SemanticFlowEdgeKind {
    Fallthrough,
    BranchTaken,
    Jump,
    ExceptionDispatch,
}

#[derive(Debug, Clone, PartialEq, Eq, Serialize)]
pub struct SemanticFlowEdge {
    pub from_block: usize,
    pub to_block: usize,
    pub kind: SemanticFlowEdgeKind,
}

#[derive(Debug, Clone, PartialEq, Eq, Serialize)]
pub struct ExceptionRegion {
    pub setup_offset: usize,
    pub protected_start_offset: usize,
    pub handler_dispatch_offset: usize,
    pub end_offset: usize,
    pub handlers: Vec<ExceptionHandler>,
    /// Compiler-generated jumps found immediately before a handler boundary.
    /// Keeping this exact prevents arbitrary user `goto` statements that happen
    /// to target `end_offset` from being mistaken for exception scaffolding.
    pub exit_jump_offsets: Vec<usize>,
}

#[derive(Debug, Clone, PartialEq, Eq, Serialize)]
pub struct ExceptionHandler {
    pub entry_offset: usize,
    pub catch_value_offset: usize,
    pub catch_value_variable_index: u16,
    pub catch_offset: usize,
    pub guard_offset: usize,
    pub body_start_offset: usize,
    pub next_handler_or_end_offset: usize,
}

impl SemanticControlFlow {
    pub fn is_exception_scaffolding(&self, instruction: &PCodeInstruction) -> bool {
        self.exception_regions.iter().any(|region| {
            instruction.offset == region.setup_offset
                || instruction.offset == region.end_offset
                || region.handlers.iter().any(|handler| {
                    instruction.offset == handler.catch_value_offset
                        || instruction.offset == handler.catch_offset
                        || instruction.offset == handler.guard_offset
                })
                || region.exit_jump_offsets.contains(&instruction.offset)
        })
    }
}

pub fn build_semantic_control_flow(scan: &PCodeScan) -> SemanticControlFlow {
    let mut errors = Vec::new();
    if !scan.complete {
        errors.push("P-code scan did not reach the end of the function".to_string());
    }
    if scan.instructions.is_empty() {
        return SemanticControlFlow {
            valid: errors.is_empty(),
            errors,
            blocks: Vec::new(),
            edges: Vec::new(),
            exception_regions: Vec::new(),
        };
    }

    let boundaries = scan
        .instructions
        .iter()
        .map(|instruction| instruction.offset)
        .collect::<HashSet<_>>();
    let by_offset = scan
        .instructions
        .iter()
        .enumerate()
        .map(|(index, instruction)| (instruction.offset, index))
        .collect::<HashMap<_, _>>();
    let mut leaders = BTreeSet::from([scan.instructions[0].offset]);

    for (index, instruction) in scan.instructions.iter().enumerate() {
        if matches!(instruction.opcode, 0x0002..=0x0004) {
            add_target_leader(instruction, &boundaries, &mut leaders, &mut errors);
            if let Some(next) = scan.instructions.get(index + 1) {
                leaders.insert(next.offset);
            }
        }
        if instruction.opcode == 0x01e5 {
            if instruction.operands_u16_le.len() != 2 {
                errors.push(format!(
                    "PUSH_TRY at 0x{:04X} requires two target operands",
                    instruction.offset
                ));
            }
            for target in &instruction.operands_u16_le {
                let target = *target as usize;
                if boundaries.contains(&target) {
                    leaders.insert(target);
                } else {
                    errors.push(format!(
                        "PUSH_TRY at 0x{:04X} targets non-boundary 0x{target:04X}",
                        instruction.offset
                    ));
                }
            }
            if let Some(next) = scan.instructions.get(index + 1) {
                leaders.insert(next.offset);
            }
        }
        if matches!(instruction.opcode, 0x0000 | 0x01e8) {
            if let Some(next) = scan.instructions.get(index + 1) {
                leaders.insert(next.offset);
            }
        }
    }

    let leader_offsets = leaders.into_iter().collect::<Vec<_>>();
    let blocks = build_blocks(scan, &leader_offsets);
    let block_by_offset = blocks
        .iter()
        .flat_map(|block| {
            block
                .instruction_offsets
                .iter()
                .map(move |offset| (*offset, block.id))
        })
        .collect::<HashMap<_, _>>();
    let mut edges = build_direct_edges(scan, &blocks, &block_by_offset, &mut errors);
    let exception_regions = build_exception_regions(scan, &by_offset, &boundaries, &mut errors);

    for region in &exception_regions {
        let Some(from_block) = block_by_offset.get(&region.setup_offset).copied() else {
            continue;
        };
        let Some(to_block) = block_by_offset
            .get(&region.handler_dispatch_offset)
            .copied()
        else {
            continue;
        };
        add_edge(
            &mut edges,
            SemanticFlowEdge {
                from_block,
                to_block,
                kind: SemanticFlowEdgeKind::ExceptionDispatch,
            },
        );
    }

    SemanticControlFlow {
        valid: errors.is_empty(),
        errors,
        blocks,
        edges,
        exception_regions,
    }
}

fn add_target_leader(
    instruction: &PCodeInstruction,
    boundaries: &HashSet<usize>,
    leaders: &mut BTreeSet<usize>,
    errors: &mut Vec<String>,
) {
    let Some(target) = instruction.operands_u16_le.first().copied() else {
        errors.push(format!(
            "{} at 0x{:04X} has no target operand",
            instruction.mnemonic, instruction.offset
        ));
        return;
    };
    let target = target as usize;
    if boundaries.contains(&target) {
        leaders.insert(target);
    } else {
        errors.push(format!(
            "{} at 0x{:04X} targets non-boundary 0x{target:04X}",
            instruction.mnemonic, instruction.offset
        ));
    }
}

fn build_blocks(scan: &PCodeScan, leaders: &[usize]) -> Vec<SemanticBasicBlock> {
    leaders
        .iter()
        .enumerate()
        .filter_map(|(id, start)| {
            let end = leaders.get(id + 1).copied().unwrap_or(scan.region_length);
            let instruction_offsets = scan
                .instructions
                .iter()
                .filter(|instruction| instruction.offset >= *start && instruction.offset < end)
                .map(|instruction| instruction.offset)
                .collect::<Vec<_>>();
            (!instruction_offsets.is_empty()).then_some(SemanticBasicBlock {
                id,
                start_offset: *start,
                end_offset_exclusive: end,
                instruction_offsets,
            })
        })
        .collect()
}

fn build_direct_edges(
    scan: &PCodeScan,
    blocks: &[SemanticBasicBlock],
    block_by_offset: &HashMap<usize, usize>,
    errors: &mut Vec<String>,
) -> Vec<SemanticFlowEdge> {
    let instruction_by_offset = scan
        .instructions
        .iter()
        .map(|instruction| (instruction.offset, instruction))
        .collect::<HashMap<_, _>>();
    let mut edges = Vec::new();

    for (position, block) in blocks.iter().enumerate() {
        let Some(last_offset) = block.instruction_offsets.last() else {
            continue;
        };
        let instruction = instruction_by_offset[last_offset];
        match instruction.opcode {
            0x0002 | 0x0003 => {
                add_branch_edge(
                    &mut edges,
                    block.id,
                    instruction,
                    block_by_offset,
                    SemanticFlowEdgeKind::BranchTaken,
                    errors,
                );
                if let Some(next) = blocks.get(position + 1) {
                    add_edge(
                        &mut edges,
                        SemanticFlowEdge {
                            from_block: block.id,
                            to_block: next.id,
                            kind: SemanticFlowEdgeKind::Fallthrough,
                        },
                    );
                }
            }
            0x0004 => add_branch_edge(
                &mut edges,
                block.id,
                instruction,
                block_by_offset,
                SemanticFlowEdgeKind::Jump,
                errors,
            ),
            0x0000 | 0x01e8 => {}
            _ => {
                if let Some(next) = blocks.get(position + 1) {
                    add_edge(
                        &mut edges,
                        SemanticFlowEdge {
                            from_block: block.id,
                            to_block: next.id,
                            kind: SemanticFlowEdgeKind::Fallthrough,
                        },
                    );
                }
            }
        }
    }
    edges
}

fn add_branch_edge(
    edges: &mut Vec<SemanticFlowEdge>,
    from_block: usize,
    instruction: &PCodeInstruction,
    block_by_offset: &HashMap<usize, usize>,
    kind: SemanticFlowEdgeKind,
    errors: &mut Vec<String>,
) {
    let Some(target) = instruction.operands_u16_le.first().copied() else {
        return;
    };
    let target = target as usize;
    let Some(to_block) = block_by_offset.get(&target).copied() else {
        errors.push(format!(
            "{} at 0x{:04X} has no destination block for 0x{target:04X}",
            instruction.mnemonic, instruction.offset
        ));
        return;
    };
    add_edge(
        edges,
        SemanticFlowEdge {
            from_block,
            to_block,
            kind,
        },
    );
}

fn add_edge(edges: &mut Vec<SemanticFlowEdge>, edge: SemanticFlowEdge) {
    if !edges.contains(&edge) {
        edges.push(edge);
    }
}

fn build_exception_regions(
    scan: &PCodeScan,
    by_offset: &HashMap<usize, usize>,
    boundaries: &HashSet<usize>,
    errors: &mut Vec<String>,
) -> Vec<ExceptionRegion> {
    let mut regions = Vec::new();
    for (setup_index, setup) in scan
        .instructions
        .iter()
        .enumerate()
        .filter(|(_, instruction)| instruction.opcode == 0x01e5)
    {
        let Some((&handler_dispatch, &end)) = setup
            .operands_u16_le
            .first()
            .zip(setup.operands_u16_le.get(1))
        else {
            continue;
        };
        let handler_dispatch = handler_dispatch as usize;
        let end = end as usize;
        let Some(protected_start) = scan.instructions.get(setup_index + 1).map(|i| i.offset) else {
            errors.push(format!(
                "PUSH_TRY at 0x{:04X} has no protected instruction",
                setup.offset
            ));
            continue;
        };
        if handler_dispatch <= protected_start || end <= handler_dispatch {
            errors.push(format!(
                "PUSH_TRY at 0x{:04X} has invalid ordered region 0x{protected_start:04X}..0x{handler_dispatch:04X}..0x{end:04X}",
                setup.offset
            ));
            continue;
        }
        if !boundaries.contains(&handler_dispatch) || !boundaries.contains(&end) {
            continue;
        }
        if scan.instructions[*by_offset.get(&end).expect("validated boundary")].opcode != 0x01e6 {
            errors.push(format!(
                "exception region ending at 0x{end:04X} does not point to POP_TRY"
            ));
            continue;
        }

        let mut handlers = Vec::new();
        let mut entry = handler_dispatch;
        let mut seen = HashSet::new();
        while entry < end && seen.insert(entry) {
            let Some(entry_index) = by_offset.get(&entry).copied() else {
                break;
            };
            let Some(catch_value) = scan.instructions.get(entry_index) else {
                break;
            };
            let Some(catch) = scan.instructions.get(entry_index + 1) else {
                break;
            };
            let Some(guard) = scan.instructions.get(entry_index + 2) else {
                break;
            };
            let Some(body_start) = scan.instructions.get(entry_index + 3).map(|i| i.offset) else {
                break;
            };
            if catch_value.opcode != 0x01a9 || catch.opcode != 0x01e7 || guard.opcode != 0x0003 {
                errors.push(format!(
                    "exception handler at 0x{entry:04X} does not match PUSH_LOCAL_VAR_RP/CATCH_EXCEPTION/JUMPFALSE scaffolding"
                ));
                break;
            }
            let Some(variable_index) = catch_value.operands_u16_le.first().copied() else {
                errors.push(format!(
                    "exception handler value at 0x{:04X} has no variable index",
                    catch_value.offset
                ));
                break;
            };
            let Some(next) = guard.operands_u16_le.first().copied().map(usize::from) else {
                break;
            };
            if next <= entry || next > end || !boundaries.contains(&next) {
                errors.push(format!(
                    "exception handler guard at 0x{:04X} has invalid next target 0x{next:04X}",
                    guard.offset
                ));
                break;
            }
            handlers.push(ExceptionHandler {
                entry_offset: entry,
                catch_value_offset: catch_value.offset,
                catch_value_variable_index: variable_index,
                catch_offset: catch.offset,
                guard_offset: guard.offset,
                body_start_offset: body_start,
                next_handler_or_end_offset: next,
            });
            entry = next;
        }
        if handlers.is_empty() || entry != end {
            errors.push(format!(
                "exception region at 0x{:04X} did not resolve a complete handler chain",
                setup.offset
            ));
            continue;
        }
        let exit_jump_offsets = std::iter::once(handler_dispatch)
            .chain(
                handlers
                    .iter()
                    .map(|handler| handler.next_handler_or_end_offset),
            )
            .filter_map(|boundary| {
                let index = by_offset.get(&boundary).copied()?;
                let candidate = index
                    .checked_sub(1)
                    .and_then(|index| scan.instructions.get(index))?;
                (candidate.opcode == 0x0004
                    && candidate
                        .operands_u16_le
                        .first()
                        .is_some_and(|target| *target as usize == end))
                .then_some(candidate.offset)
            })
            .collect::<BTreeSet<_>>()
            .into_iter()
            .collect();
        regions.push(ExceptionRegion {
            setup_offset: setup.offset,
            protected_start_offset: protected_start,
            handler_dispatch_offset: handler_dispatch,
            end_offset: end,
            handlers,
            exit_jump_offsets,
        });
    }
    regions
}

#[cfg(test)]
mod tests {
    use domain::decode::PBVersion;

    use super::*;
    use crate::pb::pcode_scanner::scan_pcode_strict;

    #[test]
    fn builds_conditional_target_and_fallthrough_edges() {
        let bytes = [
            0x32, 0x00, 0x01, 0x00, // 0000 PUSH_CONST_INT 1
            0x03, 0x00, 0x0c, 0x00, // 0004 JUMPFALSE 000C
            0x04, 0x00, 0x0e, 0x00, // 0008 JUMP 000E
            0x00, 0x00, // 000C RETURN
            0x00, 0x00, // 000E RETURN
        ];
        let cfg = build_semantic_control_flow(&scan_pcode_strict(&bytes, PBVersion::PB2022));

        assert!(cfg.valid, "{:?}", cfg.errors);
        assert_eq!(cfg.blocks.len(), 4);
        assert!(cfg
            .edges
            .iter()
            .any(|edge| edge.kind == SemanticFlowEdgeKind::BranchTaken));
        assert!(cfg
            .edges
            .iter()
            .any(|edge| edge.kind == SemanticFlowEdgeKind::Fallthrough));
        assert!(cfg
            .edges
            .iter()
            .any(|edge| edge.kind == SemanticFlowEdgeKind::Jump));
    }

    #[test]
    fn rejects_branch_target_that_is_not_an_instruction_boundary() {
        let bytes = [0x04, 0x00, 0x03, 0x00, 0x00, 0x00];
        let cfg = build_semantic_control_flow(&scan_pcode_strict(&bytes, PBVersion::PB2022));

        assert!(!cfg.valid);
        assert!(cfg
            .errors
            .iter()
            .any(|error| error.contains("non-boundary")));
    }

    #[test]
    fn suppresses_only_boundary_exit_jumps_as_exception_scaffolding() {
        let bytes = [
            0xe5, 0x01, 0x0e, 0x00, 0x1c, 0x00, // 0000 PUSH_TRY 000E,001C
            0x04, 0x00, 0x1c, 0x00, // 0006 user jump to end
            0x04, 0x00, 0x1c, 0x00, // 000A protected exit at boundary
            0xa9, 0x01, 0x00, 0x00, // 000E PUSH_LOCAL_VAR_RP
            0xe7, 0x01, // 0012 CATCH_EXCEPTION
            0x03, 0x00, 0x1c, 0x00, // 0014 JUMPFALSE 001C
            0x04, 0x00, 0x1c, 0x00, // 0018 handler exit at boundary
            0xe6, 0x01, // 001C POP_TRY
            0x00, 0x00, // 001E RETURN
        ];
        let scan = scan_pcode_strict(&bytes, PBVersion::PB2022);
        let cfg = build_semantic_control_flow(&scan);

        assert!(cfg.valid, "{:?}", cfg.errors);
        assert_eq!(
            cfg.exception_regions[0].exit_jump_offsets,
            vec![0x000a, 0x0018]
        );
        assert!(!cfg.is_exception_scaffolding(&scan.instructions[1]));
        assert!(cfg.is_exception_scaffolding(&scan.instructions[2]));
        assert!(cfg.is_exception_scaffolding(&scan.instructions[6]));
    }
}
