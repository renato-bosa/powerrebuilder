//! PowerBuilder 12.x Decoder
//!
//! Implements VersionDecoder for PowerBuilder 12.x (and 8.0-11.x).
//! Supports full opcode set (0x00-0x246) including LongLong and Byte types.

use super::opcodes::{get_opcode_info, is_valid_for_version, operand_words_for_version};
use domain::decode::{
    DecodeErr, Imm, Instr, PBVersion, SemResult, StackDelta, VersionDecoder, VmSemantics, VmState,
};
use domain::ingestion::ArtifactKind;
use domain::model::pb_ir::{FnSig, PbMember, PbUnit};

/// PowerBuilder 12.x decoder
pub struct Pb12Decoder {
    version: PBVersion,
}

impl Pb12Decoder {
    pub fn new() -> Self {
        Self::for_version(PBVersion::PB12)
    }

    pub fn for_version(version: PBVersion) -> Self {
        Self { version }
    }

    /// Parse immediate value based on opcode hint
    fn parse_immediate(
        &self,
        bytes: &[u8],
        pos: usize,
        operand_words: u8,
        hint: Option<&str>,
    ) -> Option<Imm> {
        if operand_words == 0 {
            return None;
        }

        let operand_byte_len = operand_words as usize * 2;
        let end = pos + operand_byte_len;
        if end > bytes.len() {
            return None;
        }

        match hint {
            Some("int16") | Some("var_index") | Some("field_index") | Some("string_index") => {
                let val = i16::from_le_bytes([bytes[pos], bytes[pos + 1]]);
                Some(Imm::I32(val as i32))
            }
            Some("byte_value") => Some(Imm::Bool(bytes[pos] != 0)),
            Some("relative_offset") => {
                let offset = i16::from_le_bytes([bytes[pos], bytes[pos + 1]]);
                Some(Imm::I32(offset as i32))
            }
            _ => {
                // Generic immediate - try to parse as appropriate size
                match operand_byte_len {
                    2 => {
                        let val = i16::from_le_bytes([bytes[pos], bytes[pos + 1]]);
                        Some(Imm::I32(val as i32))
                    }
                    4 => {
                        let val = i32::from_le_bytes([
                            bytes[pos],
                            bytes[pos + 1],
                            bytes[pos + 2],
                            bytes[pos + 3],
                        ]);
                        Some(Imm::I32(val))
                    }
                    8 => {
                        let val = i64::from_le_bytes([
                            bytes[pos],
                            bytes[pos + 1],
                            bytes[pos + 2],
                            bytes[pos + 3],
                            bytes[pos + 4],
                            bytes[pos + 5],
                            bytes[pos + 6],
                            bytes[pos + 7],
                        ]);
                        Some(Imm::I64(val))
                    }
                    _ => {
                        // Unknown size, return as i32 if possible
                        Some(Imm::I32(bytes[pos] as i32))
                    }
                }
            }
        }
    }
}

impl Default for Pb12Decoder {
    fn default() -> Self {
        Self::new()
    }
}

impl VersionDecoder for Pb12Decoder {
    fn version(&self) -> PBVersion {
        self.version
    }

    fn disassemble(&self, bytes: &[u8]) -> Result<Vec<Instr>, DecodeErr> {
        let mut instructions = Vec::new();
        let mut pos = 0;

        while pos < bytes.len() {
            // Need at least 2 bytes for opcode
            if pos + 1 >= bytes.len() {
                return Err(DecodeErr::IncompleteInstruction { pos });
            }

            // Read opcode (little-endian u16)
            let code = u16::from_le_bytes([bytes[pos], bytes[pos + 1]]);
            let instr_pos = pos as u32;
            pos += 2;

            // Look up opcode info
            if let Some(info) = get_opcode_info(code) {
                // Validate opcode is supported in this version
                if !is_valid_for_version(code, self.version) {
                    // Version mismatch - treat as unknown
                    instructions.push(Instr::Unknown {
                        raw: code,
                        pos: instr_pos,
                    });
                    continue;
                }

                // Parse immediate operand if present
                let operand_words = operand_words_for_version(code, self.version)
                    .expect("known, version-valid opcode must have an operand width");
                let operand_byte_len = operand_words as usize * 2;
                let imm = if operand_words > 0 {
                    if pos + operand_byte_len > bytes.len() {
                        // Incomplete instruction
                        return Err(DecodeErr::IncompleteInstruction { pos });
                    }
                    self.parse_immediate(bytes, pos, operand_words, info.hint)
                } else {
                    None
                };

                // Advance position past operand
                pos += operand_byte_len;

                // Add instruction
                instructions.push(Instr::Op {
                    code,
                    imm,
                    pos: instr_pos,
                });
            } else {
                // Unknown opcode - preserve with provenance
                instructions.push(Instr::Unknown {
                    raw: code,
                    pos: instr_pos,
                });
            }
        }

        Ok(instructions)
    }

    fn lift_to_pb_ir(&self, instrs: &[Instr]) -> Result<PbUnit, DecodeErr> {
        if instrs.is_empty() {
            return Err(DecodeErr::InvalidBytecode {
                pos: 0,
                message: "Empty instruction list".to_string(),
            });
        }

        // Build CFG from instructions
        let cfg = domain::decode::build_cfg(instrs);

        // Convert to SSA form
        let ssa = domain::decode::to_ssa(&cfg);

        // Infer types (with empty hints for now)
        let hints = domain::decode::TypeHints::new();
        let _types = domain::decode::infer_types(&ssa, &hints);

        // For now, create a simple PbUnit with the SSA as a function body
        // More sophisticated lifting would extract functions, events, etc.
        Ok(PbUnit {
            name: "decompiled_function".to_string(),
            kind: ArtifactKind::Function,
            members: vec![PbMember::Function {
                sig: FnSig {
                    name: "main".to_string(),
                    parameters: vec![],
                    return_type: None,
                },
                body: ssa,
            }],
        })
    }

    fn vm_semantics(&self) -> &'static VmSemantics {
        // Return PB12 VM semantics
        static PB12_SEMANTICS: VmSemantics = VmSemantics {
            stack_effect: pb12_stack_effect,
            eval: pb12_eval,
        };
        &PB12_SEMANTICS
    }
}

/// Stack effect for PB12 instructions
fn pb12_stack_effect(instr: &Instr) -> StackDelta {
    match instr {
        Instr::Op { code, .. } => {
            // Basic stack effects for common opcodes
            match *code {
                0x00 => StackDelta::new(0, 0),        // RETURN
                0x1E => StackDelta::new(0, 1),        // PUSH_LOCAL_VAR
                0x32..=0x3D => StackDelta::new(0, 1), // PUSH_CONST_*
                0x53..=0x5E => StackDelta::new(2, 1), // ADD_*, SUB_*
                0x24..=0x26 => StackDelta::new(2, 1), // AND, OR, NOT (NOT pops 1)
                _ => StackDelta::new(0, 0),           // Unknown - conservative estimate
            }
        }
        Instr::Unknown { .. } => StackDelta::new(0, 0),
    }
}

/// Evaluate PB12 instruction
fn pb12_eval(instr: &Instr, state: &mut VmState) -> SemResult {
    match instr {
        Instr::Op { code, .. } => {
            match *code {
                0x00 => SemResult::Return(None), // RETURN
                _ => {
                    // Default: continue execution
                    state.pc += 1;
                    SemResult::Continue(state.clone())
                }
            }
        }
        Instr::Unknown { .. } => {
            state.pc += 1;
            SemResult::Continue(state.clone())
        }
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_pb12_decoder_version() {
        let decoder = Pb12Decoder::new();
        assert_eq!(decoder.version().major, 12);
    }

    #[test]
    fn test_disassemble_simple() {
        let decoder = Pb12Decoder::new();

        // Simple bytecode: RETURN (0x00)
        let bytes = vec![0x00, 0x00];
        let result = decoder.disassemble(&bytes);

        assert!(result.is_ok());
        let instrs = result.unwrap();
        assert_eq!(instrs.len(), 1);

        match &instrs[0] {
            Instr::Op { code, imm, .. } => {
                assert_eq!(*code, 0x00);
                assert!(imm.is_none());
            }
            _ => panic!("Expected Op instruction"),
        }
    }

    #[test]
    fn test_disassemble_with_operand() {
        let decoder = Pb12Decoder::new();

        // PUSH_LOCAL_VAR (0x1E) with var_index 5
        let bytes = vec![0x1E, 0x00, 0x05, 0x00];
        let result = decoder.disassemble(&bytes);

        assert!(result.is_ok());
        let instrs = result.unwrap();
        assert_eq!(instrs.len(), 1);

        match &instrs[0] {
            Instr::Op { code, imm, .. } => {
                assert_eq!(*code, 0x1E);
                assert!(imm.is_some());
                match imm {
                    Some(Imm::I32(val)) => assert_eq!(*val, 5),
                    _ => panic!("Expected I32 immediate"),
                }
            }
            _ => panic!("Expected Op instruction"),
        }
    }

    #[test]
    fn test_disassemble_unknown_opcode() {
        let decoder = Pb12Decoder::new();

        // Unknown opcode 0xFFFF
        let bytes = vec![0xFF, 0xFF];
        let result = decoder.disassemble(&bytes);

        assert!(result.is_ok());
        let instrs = result.unwrap();
        assert_eq!(instrs.len(), 1);

        match &instrs[0] {
            Instr::Unknown { raw, .. } => {
                assert_eq!(*raw, 0xFFFF);
            }
            _ => panic!("Expected Unknown instruction"),
        }
    }

    #[test]
    fn test_disassemble_incomplete() {
        let decoder = Pb12Decoder::new();

        // PUSH_LOCAL_VAR (0x1E) with incomplete operand
        let bytes = vec![0x1E, 0x00]; // Missing the var_index word
        let result = decoder.disassemble(&bytes);

        assert!(result.is_err());
        match result {
            Err(DecodeErr::IncompleteInstruction { .. }) => {}
            _ => panic!("Expected IncompleteInstruction error"),
        }
    }

    #[test]
    fn test_lift_to_pb_ir() {
        let decoder = Pb12Decoder::new();

        // Simple instruction sequence
        let instrs = vec![
            Instr::Op {
                code: 0x00,
                imm: None,
                pos: 0,
            }, // RETURN
        ];

        let result = decoder.lift_to_pb_ir(&instrs);
        assert!(result.is_ok());

        let pb_unit = result.unwrap();
        assert_eq!(pb_unit.kind, ArtifactKind::Function);
        assert_eq!(pb_unit.members.len(), 1);
    }

    #[test]
    fn test_lift_empty_instructions() {
        let decoder = Pb12Decoder::new();
        let result = decoder.lift_to_pb_ir(&[]);
        assert!(result.is_err());
    }
}
