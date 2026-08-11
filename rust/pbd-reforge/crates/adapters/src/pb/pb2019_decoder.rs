//! PowerBuilder 2017/2019 Decoder
//!
//! Implements VersionDecoder for PowerBuilder 2017/2019.
//! Same opcode set as PB12, differences are at data representation level
//! (Unicode, generics, .NET integration).

use super::pb12_decoder::Pb12Decoder;
use domain::decode::{DecodeErr, Instr, PBVersion, VersionDecoder, VmSemantics};
use domain::model::pb_ir::PbUnit;

/// PowerBuilder 2017/2019 decoder
///
/// Delegates to PB12 decoder since opcode set is identical.
/// Version-specific differences (Unicode, generics) are handled
/// at the data representation level, not bytecode level.
pub struct Pb2019Decoder {
    version: PBVersion,
    inner: Pb12Decoder,
}

impl Pb2019Decoder {
    pub fn new() -> Self {
        Self {
            version: PBVersion::PB2019,
            inner: Pb12Decoder::for_version(PBVersion::PB2019),
        }
    }

    pub fn for_version(version: PBVersion) -> Self {
        Self {
            version,
            inner: Pb12Decoder::for_version(version),
        }
    }
}

impl Default for Pb2019Decoder {
    fn default() -> Self {
        Self::new()
    }
}

impl VersionDecoder for Pb2019Decoder {
    fn version(&self) -> PBVersion {
        self.version
    }

    fn disassemble(&self, bytes: &[u8]) -> Result<Vec<Instr>, DecodeErr> {
        // Delegate to PB12 decoder - opcode set is identical
        self.inner.disassemble(bytes)
    }

    fn lift_to_pb_ir(&self, instrs: &[Instr]) -> Result<PbUnit, DecodeErr> {
        // Delegate to PB12 decoder
        // In a full implementation, this would handle PB2019-specific features
        // like .NET generics, but the core lifting logic is the same
        self.inner.lift_to_pb_ir(instrs)
    }

    fn vm_semantics(&self) -> &'static VmSemantics {
        // PB2019 delegates to PB12 VM semantics
        self.inner.vm_semantics()
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_pb2019_decoder_version() {
        let decoder = Pb2019Decoder::new();
        assert_eq!(decoder.version().major, 19);
    }

    #[test]
    fn test_pb2019_supports_extended_opcodes() {
        let decoder = Pb2019Decoder::new();

        // Opcode 0x1EB (CNV_INT_TO_LONGLONG) - PB 8.0+
        let bytes = vec![0xEB, 0x01, 0x00, 0x00];
        let result = decoder.disassemble(&bytes);

        assert!(result.is_ok());
        let instrs = result.unwrap();
        assert_eq!(instrs.len(), 1);

        match &instrs[0] {
            domain::decode::Instr::Op { code, .. } => {
                assert_eq!(*code, 0x01EB);
            }
            _ => panic!("Expected Op instruction"),
        }
    }

    #[test]
    fn test_pb2019_for_version() {
        let decoder = Pb2019Decoder::for_version(PBVersion::PB2017);
        assert_eq!(decoder.version().major, 17);
    }
}
