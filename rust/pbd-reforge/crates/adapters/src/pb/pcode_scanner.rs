//! Strict, diagnostic-only scanner for validated P-code regions.
//!
//! Unlike the legacy decoder, this scanner stops at the first opcode that is
//! absent from the selected version table. Continuing past an unknown opcode
//! would require knowing its operand width and could silently desynchronize the
//! remainder of the region.

use domain::decode::PBVersion;
use serde::Serialize;

use super::opcodes::{get_opcode_info, is_valid_for_version, operand_words_for_version};

#[derive(Debug, Clone, PartialEq, Eq, Serialize)]
pub struct PCodeInstruction {
    pub offset: usize,
    pub opcode: u16,
    pub mnemonic: &'static str,
    pub operand_words: u8,
    pub operand_bytes_hex: String,
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

        instructions.push(PCodeInstruction {
            offset,
            opcode,
            mnemonic: info.mnemonic,
            operand_words,
            operand_bytes_hex: bytes_to_hex(&bytes[operand_start..instruction_end]),
        });
        offset = instruction_end;
    }

    PCodeScan {
        region_length: bytes.len(),
        consumed_bytes: bytes.len(),
        instruction_count: instructions.len(),
        complete: true,
        stop: None,
        instructions,
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
    }
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
}
