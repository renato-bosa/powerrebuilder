//! Decoder Registry
//!
//! Manages version-specific decoders with auto-registration.

use domain::decode::{PBVersion, VersionDecoder};
use once_cell::sync::Lazy;
use std::collections::HashMap;
use std::sync::Arc;

use super::pb6_decoder::Pb6Decoder;
use super::pb12_decoder::Pb12Decoder;
use super::pb2019_decoder::Pb2019Decoder;

/// Decoder registry - maps PowerBuilder versions to decoders
pub struct DecoderRegistry {
    decoders: HashMap<PBVersion, Arc<dyn VersionDecoder>>,
}

impl DecoderRegistry {
    /// Create new registry with all decoders registered
    fn new() -> Self {
        let mut decoders: HashMap<PBVersion, Arc<dyn VersionDecoder>> = HashMap::new();

        // Register PB6 decoder
        decoders.insert(PBVersion::PB6, Arc::new(Pb6Decoder::new()));

        // PB7-9 use PB6 decoder (opcodes are compatible)
        decoders.insert(PBVersion::PB7, Arc::new(Pb6Decoder::new()));
        decoders.insert(PBVersion::PB9, Arc::new(Pb6Decoder::new()));

        // PB10-12 use PB12 decoder (extended opcode set)
        decoders.insert(PBVersion::PB10, Arc::new(Pb12Decoder::new()));
        decoders.insert(PBVersion::PB11, Arc::new(Pb12Decoder::new()));
        decoders.insert(PBVersion::PB12, Arc::new(Pb12Decoder::new()));
        decoders.insert(PBVersion::PB12_5, Arc::new(Pb12Decoder::new()));

        // PB2017+ use PB2019 decoder (same as PB12 but different version)
        decoders.insert(
            PBVersion::PB2017,
            Arc::new(Pb2019Decoder::for_version(PBVersion::PB2017)),
        );
        decoders.insert(PBVersion::PB2019, Arc::new(Pb2019Decoder::new()));

        Self { decoders }
    }

    /// Get decoder for specific version
    pub fn get_decoder(&self, version: PBVersion) -> Option<Arc<dyn VersionDecoder>> {
        self.decoders.get(&version).cloned()
    }

    /// Detect PowerBuilder version from bytecode
    ///
    /// Uses heuristics to identify the most likely version.
    /// Returns best guess or None if detection fails.
    pub fn detect_version(bytes: &[u8]) -> Option<PBVersion> {
        if bytes.len() < 2 {
            return None;
        }

        // Heuristic: Scan for extended opcodes
        // If we find opcodes > 0xFF, it's PB 8.0+
        let mut has_extended_opcodes = false;
        let mut pos = 0;

        while pos + 1 < bytes.len().min(1024) {
            // Check first 1KB
            let code = u16::from_le_bytes([bytes[pos], bytes[pos + 1]]);

            if code > 0xFF && code <= 0x246 {
                has_extended_opcodes = true;
                break;
            }

            // Advance by 2 bytes (could be more sophisticated)
            pos += 2;
        }

        if has_extended_opcodes {
            // Extended opcodes present - likely PB 8.0+
            // Default to PB12 as it's most common
            Some(PBVersion::PB12)
        } else {
            // No extended opcodes - likely PB 6.x-7.x
            Some(PBVersion::PB6)
        }
    }

    /// Get default decoder (PB12 - most common)
    pub fn get_default_decoder(&self) -> Arc<dyn VersionDecoder> {
        self.get_decoder(PBVersion::PB12)
            .expect("PB12 decoder should always be registered")
    }

    /// List all registered versions
    pub fn registered_versions(&self) -> Vec<PBVersion> {
        let mut versions: Vec<_> = self.decoders.keys().copied().collect();
        versions.sort();
        versions
    }
}

/// Global decoder registry instance
pub static DECODER_REGISTRY: Lazy<DecoderRegistry> = Lazy::new(DecoderRegistry::new);

/// Get decoder for version (convenience function)
pub fn get_decoder(version: PBVersion) -> Option<Arc<dyn VersionDecoder>> {
    DECODER_REGISTRY.get_decoder(version)
}

/// Detect version from bytecode (convenience function)
pub fn detect_version(bytes: &[u8]) -> Option<PBVersion> {
    DecoderRegistry::detect_version(bytes)
}

/// Get default decoder (convenience function)
pub fn get_default_decoder() -> Arc<dyn VersionDecoder> {
    DECODER_REGISTRY.get_default_decoder()
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_registry_has_all_versions() {
        let registry = DecoderRegistry::new();
        let versions = registry.registered_versions();

        // Should have at least PB6, PB12, PB2019
        assert!(versions.contains(&PBVersion::PB6));
        assert!(versions.contains(&PBVersion::PB12));
        assert!(versions.contains(&PBVersion::PB2019));
    }

    #[test]
    fn test_get_decoder() {
        let decoder = get_decoder(PBVersion::PB12);
        assert!(decoder.is_some());
        assert_eq!(decoder.unwrap().version(), PBVersion::PB12);
    }

    #[test]
    fn test_get_default_decoder() {
        let decoder = get_default_decoder();
        assert_eq!(decoder.version(), PBVersion::PB12);
    }

    #[test]
    fn test_detect_version_basic() {
        // Bytecode with only basic opcodes (0x00)
        let bytes = vec![0x00, 0x00, 0x00, 0x00];
        let version = detect_version(&bytes);
        assert!(version.is_some());
        assert_eq!(version.unwrap(), PBVersion::PB6);
    }

    #[test]
    fn test_detect_version_extended() {
        // Bytecode with extended opcode (0x01EB = CNV_INT_TO_LONGLONG)
        let bytes = vec![0xEB, 0x01];
        let version = detect_version(&bytes);
        assert!(version.is_some());
        assert_eq!(version.unwrap(), PBVersion::PB12);
    }

    #[test]
    fn test_detect_version_empty() {
        let bytes = vec![];
        let version = detect_version(&bytes);
        assert!(version.is_none());
    }

    #[test]
    fn test_global_registry() {
        // Test that global registry works
        let decoder1 = DECODER_REGISTRY.get_decoder(PBVersion::PB6);
        let decoder2 = DECODER_REGISTRY.get_decoder(PBVersion::PB6);

        assert!(decoder1.is_some());
        assert!(decoder2.is_some());

        // Should be same Arc instance
        assert!(Arc::ptr_eq(&decoder1.unwrap(), &decoder2.unwrap()));
    }
}
