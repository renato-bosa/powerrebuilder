//! Strict, diagnostic-only scanner for validated P-code regions.
//!
//! Unlike the legacy decoder, this scanner stops at the first opcode that is
//! absent from the selected version table. Continuing past an unknown opcode
//! would require knowing its operand width and could silently desynchronize the
//! remainder of the region.

use domain::decode::PBVersion;
use serde::Serialize;
use std::collections::HashSet;

use super::opcodes::{get_opcode_info, is_valid_for_version, operand_words_for_version};

#[derive(Debug, Clone, PartialEq, Eq, Serialize)]
pub struct PCodeInstruction {
    pub offset: usize,
    pub opcode: u16,
    pub mnemonic: &'static str,
    pub operand_words: u8,
    pub operand_bytes_hex: String,
    pub operands_u16_le: Vec<u16>,
}

#[derive(Debug, Clone, PartialEq, Eq, Serialize)]
pub struct BranchTargetValidation {
    pub instruction_offset: usize,
    pub opcode: u16,
    pub target_offset: usize,
    pub valid_instruction_boundary: bool,
}

#[derive(Debug, Clone, PartialEq, Eq, Serialize)]
pub struct DebugMapValidation {
    pub record_count: usize,
    pub trailing_bytes: usize,
    pub invalid_pcode_offsets: Vec<usize>,
    pub valid: bool,
}

#[derive(Debug, Clone, PartialEq, Eq, Serialize)]
#[serde(tag = "kind", rename_all = "snake_case")]
pub enum PCodeScanStop {
    UnknownOpcode {
        offset: usize,
        opcode: u16,
    },
    UnsupportedForVersion {
        offset: usize,
        opcode: u16,
        version: PBVersion,
    },
    IncompleteOpcode {
        offset: usize,
        remaining_bytes: usize,
    },
    IncompleteOperand {
        offset: usize,
        opcode: u16,
        required_bytes: usize,
        remaining_bytes: usize,
    },
}

#[derive(Debug, Clone, PartialEq, Eq, Serialize)]
pub struct PCodeScan {
    pub region_length: usize,
    /// Length of the prefix parsed without guessing any unknown instruction.
    pub consumed_bytes: usize,
    pub instruction_count: usize,
    pub complete: bool,
    pub stop: Option<PCodeScanStop>,
    pub instructions: Vec<PCodeInstruction>,
    pub branch_targets: Vec<BranchTargetValidation>,
}

pub fn scan_pcode_strict(bytes: &[u8], version: PBVersion) -> PCodeScan {
    let mut instructions = Vec::new();
    let mut offset = 0;

    while offset < bytes.len() {
        if bytes.len() - offset < 2 {
            return stopped(
                bytes.len(),
                offset,
                instructions,
                PCodeScanStop::IncompleteOpcode {
                    offset,
                    remaining_bytes: bytes.len() - offset,
                },
            );
        }

        let opcode = u16::from_le_bytes([bytes[offset], bytes[offset + 1]]);
        let Some(info) = get_opcode_info(opcode) else {
            return stopped(
                bytes.len(),
                offset,
                instructions,
                PCodeScanStop::UnknownOpcode { offset, opcode },
            );
        };

        if !is_valid_for_version(opcode, version) {
            return stopped(
                bytes.len(),
                offset,
                instructions,
                PCodeScanStop::UnsupportedForVersion {
                    offset,
                    opcode,
                    version,
                },
            );
        }

        let operand_words = operand_words_for_version(opcode, version)
            .expect("known, version-valid opcode must have an operand width");
        let operand_start = offset + 2;
        let operand_byte_len = operand_words as usize * 2;
        let instruction_end = operand_start + operand_byte_len;
        if instruction_end > bytes.len() {
            return stopped(
                bytes.len(),
                offset,
                instructions,
                PCodeScanStop::IncompleteOperand {
                    offset,
                    opcode,
                    required_bytes: operand_byte_len,
                    remaining_bytes: bytes.len().saturating_sub(operand_start),
                },
            );
        }

        let operand_bytes = &bytes[operand_start..instruction_end];
        instructions.push(PCodeInstruction {
            offset,
            opcode,
            mnemonic: info.mnemonic,
            operand_words,
            operand_bytes_hex: bytes_to_hex(operand_bytes),
            operands_u16_le: operand_bytes
                .chunks_exact(2)
                .map(|word| u16::from_le_bytes([word[0], word[1]]))
                .collect(),
        });
        offset = instruction_end;
    }

    let branch_targets = validate_branch_targets(&instructions);
    PCodeScan {
        region_length: bytes.len(),
        consumed_bytes: bytes.len(),
        instruction_count: instructions.len(),
        complete: true,
        stop: None,
        instructions,
        branch_targets,
    }
}

fn stopped(
    region_length: usize,
    consumed_bytes: usize,
    instructions: Vec<PCodeInstruction>,
    stop: PCodeScanStop,
) -> PCodeScan {
    PCodeScan {
        region_length,
        consumed_bytes,
        instruction_count: instructions.len(),
        complete: false,
        stop: Some(stop),
        instructions,
        branch_targets: Vec::new(),
    }
}

pub fn validate_debug_map(debug_bytes: &[u8], scan: &PCodeScan) -> DebugMapValidation {
    let boundaries: HashSet<usize> = scan
        .instructions
        .iter()
        .map(|instruction| instruction.offset)
        .collect();
    let invalid_pcode_offsets = debug_bytes
        .chunks_exact(4)
        .filter_map(|record| {
            let offset = u16::from_le_bytes([record[2], record[3]]) as usize;
            (!boundaries.contains(&offset)).then_some(offset)
        })
        .collect::<Vec<_>>();
    let trailing_bytes = debug_bytes.len() % 4;
    DebugMapValidation {
        record_count: debug_bytes.len() / 4,
        trailing_bytes,
        valid: trailing_bytes == 0 && invalid_pcode_offsets.is_empty(),
        invalid_pcode_offsets,
    }
}

fn validate_branch_targets(instructions: &[PCodeInstruction]) -> Vec<BranchTargetValidation> {
    let boundaries: HashSet<usize> = instructions
        .iter()
        .map(|instruction| instruction.offset)
        .collect();
    instructions
        .iter()
        .filter(|instruction| matches!(instruction.opcode, 0x02..=0x04))
        .filter_map(|instruction| {
            let target_offset = *instruction.operands_u16_le.first()? as usize;
            Some(BranchTargetValidation {
                instruction_offset: instruction.offset,
                opcode: instruction.opcode,
                target_offset,
                valid_instruction_boundary: boundaries.contains(&target_offset),
            })
        })
        .collect()
}

fn bytes_to_hex(bytes: &[u8]) -> String {
    bytes
        .iter()
        .map(|byte| format!("{byte:02X}"))
        .collect::<Vec<_>>()
        .join(" ")
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn scans_operand_lengths_as_sixteen_bit_words() {
        let scan = scan_pcode_strict(&[0x1e, 0x00, 0x05, 0x00, 0x00, 0x00], PBVersion::PB12);

        assert!(scan.complete);
        assert_eq!(scan.consumed_bytes, 6);
        assert_eq!(scan.instruction_count, 2);
        assert_eq!(scan.instructions[0].operand_words, 1);
        assert_eq!(scan.instructions[0].operand_bytes_hex, "05 00");
        assert_eq!(scan.instructions[0].operands_u16_le, vec![5]);
    }

    #[test]
    fn stops_before_unknown_opcode_to_preserve_alignment() {
        let scan = scan_pcode_strict(&[0xff, 0xff, 0x00, 0x00], PBVersion::PB12);

        assert!(!scan.complete);
        assert_eq!(scan.consumed_bytes, 0);
        assert_eq!(scan.instruction_count, 0);
        assert_eq!(
            scan.stop,
            Some(PCodeScanStop::UnknownOpcode {
                offset: 0,
                opcode: 0xffff,
            })
        );
    }

    #[test]
    fn reports_incomplete_operand_without_consuming_instruction() {
        let scan = scan_pcode_strict(&[0x1e, 0x00, 0x05], PBVersion::PB12);

        assert!(!scan.complete);
        assert_eq!(scan.consumed_bytes, 0);
        assert!(matches!(
            scan.stop,
            Some(PCodeScanStop::IncompleteOperand { .. })
        ));
    }

    #[test]
    fn validates_absolute_branch_targets() {
        let scan = scan_pcode_strict(&[0x04, 0x00, 0x04, 0x00, 0x00, 0x00], PBVersion::PB12);
        assert!(scan.complete);
        assert_eq!(scan.branch_targets.len(), 1);
        assert!(scan.branch_targets[0].valid_instruction_boundary);
    }

    #[test]
    fn validates_debug_offsets_against_instruction_boundaries() {
        let scan = scan_pcode_strict(&[0x00, 0x00], PBVersion::PB12);
        let debug = [7, 0, 0, 0];
        let validation = validate_debug_map(&debug, &scan);
        assert!(validation.valid);
    }
}
