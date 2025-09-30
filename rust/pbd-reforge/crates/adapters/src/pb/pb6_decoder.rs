//! PowerBuilder 6.x Decoder
//!
//! Implements VersionDecoder for PowerBuilder 6.x.
//! Limited opcode set (0x00-0xFF) - no LongLong or Byte types.

use domain::decode::{
    DecodeErr, Imm, Instr, PBVersion, VersionDecoder,
    VmSemantics, VmState, SemResult, StackDelta,
};
use domain::ingestion::ArtifactKind;
use domain::model::pb_ir::{PbUnit, PbMember, FnSig};
use super::opcodes::{get_opcode_info, is_valid_for_version};

/// PowerBuilder 6.x decoder
pub struct Pb6Decoder {
    version: PBVersion,
}

impl Pb6Decoder {
    pub fn new() -> Self {
        Self {
            version: PBVersion::PB6,
        }
    }

    /// Parse immediate value (same logic as PB12, but restricted opcode set)
    fn parse_immediate(&self, bytes: &[u8], pos: usize, operand_len: u8, hint: Option<&str>) -> Option<Imm> {
        if operand_len == 0 {
            return None;
        }

        let end = pos + operand_len as usize;
        if end > bytes.len() {
            return None;
        }

        match hint {
            Some("int16") | Some("var_index") | Some("field_index") | Some("string_index") => {
                if operand_len == 1 {
                    Some(Imm::I32(bytes[pos] as i32))
                } else if operand_len >= 2 {
                    let val = i16::from_le_bytes([bytes[pos], bytes[pos + 1]]);
                    Some(Imm::I32(val as i32))
                } else {
                    None
                }
            }
            Some("byte_value") => {
                Some(Imm::Bool(bytes[pos] != 0))
            }
            Some("relative_offset") => {
                let offset = bytes[pos] as i8;
                Some(Imm::I32(offset as i32))
            }
            _ => {
                match operand_len {
                    1 => Some(Imm::I32(bytes[pos] as i32)),
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
                    _ => Some(Imm::I32(bytes[pos] as i32)),
                }
            }
        }
    }
}

impl Default for Pb6Decoder {
    fn default() -> Self {
        Self::new()
    }
}

impl VersionDecoder for Pb6Decoder {
    fn version(&self) -> PBVersion {
        self.version
    }

    fn disassemble(&self, bytes: &[u8]) -> Result<Vec<Instr>, DecodeErr> {
        let mut instructions = Vec::new();
        let mut pos = 0;

        while pos < bytes.len() {
            if pos + 1 >= bytes.len() {
                break;
            }

            // For PB6, opcodes are still 2 bytes but range is limited
            let code = u16::from_le_bytes([bytes[pos], bytes[pos + 1]]);
            let instr_pos = pos as u32;
            pos += 2;

            // PB6 only supports opcodes 0x00-0xFF
            if code > 0xFF {
                instructions.push(Instr::Unknown {
                    raw: code,
                    pos: instr_pos,
                });
                continue;
            }

            if let Some(info) = get_opcode_info(code) {
                if !is_valid_for_version(code, self.version) {
                    instructions.push(Instr::Unknown {
                        raw: code,
                        pos: instr_pos,
                    });
                    continue;
                }

                let imm = if info.operand_len > 0 {
                    if pos + info.operand_len as usize > bytes.len() {
                        return Err(DecodeErr::IncompleteInstruction { pos });
                    }
                    self.parse_immediate(bytes, pos, info.operand_len, info.hint)
                } else {
                    None
                };

                pos += info.operand_len as usize;

                instructions.push(Instr::Op {
                    code,
                    imm,
                    pos: instr_pos,
                });
            } else {
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

        let cfg = domain::decode::build_cfg(instrs);
        let ssa = domain::decode::to_ssa(&cfg);
        let hints = domain::decode::TypeHints::new();
        let _types = domain::decode::infer_types(&ssa, &hints);

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
        static PB6_SEMANTICS: VmSemantics = VmSemantics {
            stack_effect: pb6_stack_effect,
            eval: pb6_eval,
        };
        &PB6_SEMANTICS
    }
}

/// Stack effect for PB6 instructions
fn pb6_stack_effect(instr: &Instr) -> StackDelta {
    // Same as PB12 for basic opcodes
    match instr {
        Instr::Op { code, .. } => {
            match *code {
                0x00 => StackDelta::new(0, 0), // RETURN
                0x1E => StackDelta::new(0, 1), // PUSH_LOCAL_VAR
                0x32..=0x3D => StackDelta::new(0, 1), // PUSH_CONST_*
                0x53..=0x5E => StackDelta::new(2, 1), // ADD_*, SUB_*
                0x24..=0x26 => StackDelta::new(2, 1), // AND, OR, NOT
                _ => StackDelta::new(0, 0),
            }
        }
        Instr::Unknown { .. } => StackDelta::new(0, 0),
    }
}

/// Evaluate PB6 instruction
fn pb6_eval(instr: &Instr, state: &mut VmState) -> SemResult {
    match instr {
        Instr::Op { code, .. } => {
            match *code {
                0x00 => SemResult::Return(None),
                _ => {
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
    fn test_pb6_decoder_version() {
        let decoder = Pb6Decoder::new();
        assert_eq!(decoder.version().major, 6);
    }

    #[test]
    fn test_pb6_rejects_extended_opcodes() {
        let decoder = Pb6Decoder::new();

        // Try to decode opcode 0x100 (DECR_ULONG - PB 8.0+)
        let bytes = vec![0x00, 0x01]; // 0x0100 in little-endian
        let result = decoder.disassemble(&bytes);

        assert!(result.is_ok());
        let instrs = result.unwrap();
        assert_eq!(instrs.len(), 1);

        // Should be treated as Unknown since > 0xFF
        match &instrs[0] {
            Instr::Unknown { raw, .. } => {
                assert_eq!(*raw, 0x0100);
            }
            _ => panic!("Expected Unknown instruction for extended opcode"),
        }
    }

    #[test]
    fn test_pb6_accepts_basic_opcodes() {
        let decoder = Pb6Decoder::new();

        // RETURN (0x00) - valid in PB6
        let bytes = vec![0x00, 0x00];
        let result = decoder.disassemble(&bytes);

        assert!(result.is_ok());
        let instrs = result.unwrap();
        assert_eq!(instrs.len(), 1);

        match &instrs[0] {
            Instr::Op { code, .. } => {
                assert_eq!(*code, 0x00);
            }
            _ => panic!("Expected Op instruction"),
        }
    }
}
