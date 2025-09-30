//! PowerBuilder Adapters

pub mod opcodes;
pub mod pbd_reader;
pub mod pb6_decoder;
pub mod pb12_decoder;
pub mod pb2019_decoder;
pub mod registry;

pub mod pbd_scanner {
    //! Signature scanning and heuristics
}

// Re-export commonly used types
pub use pb6_decoder::Pb6Decoder;
pub use pb12_decoder::Pb12Decoder;
pub use pb2019_decoder::Pb2019Decoder;
pub use registry::{get_decoder, detect_version, get_default_decoder, DECODER_REGISTRY};
