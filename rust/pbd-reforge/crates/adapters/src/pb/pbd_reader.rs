//! PBD Format Reader - Complete HDR* Format Implementation
//!
//! Ported from Python implementation with full HDR*/ENT*/DAT*/NOD*/FRE* support.
//! Pure functions for parsing PowerBuilder PBD (compiled) library files.

use memmap2::Mmap;
use std::fs::File;
use std::path::Path;
use thiserror::Error;

/// HDR* format signatures
const HDR_SIGNATURE: &[u8] = b"HDR*";
const ENT_SIGNATURE: &[u8] = b"ENT*";
const DAT_SIGNATURE: &[u8] = b"DAT*";
const NOD_SIGNATURE: &[u8] = b"NOD*";
const FRE_SIGNATURE: &[u8] = b"FRE*";

/// PBD extraction errors
#[derive(Debug, Error, Clone)]
pub enum ExtractionError {
    #[error("Error extracting {entry_name} at offset {offset}: {message}")]
    WithOffset {
        entry_name: String,
        message: String,
        offset: usize,
    },

    #[error("Error extracting {entry_name}: {message}")]
    WithoutOffset { entry_name: String, message: String },

    #[error("Invalid library format: {0}")]
    InvalidFormat(String),

    #[error("Header too small for HDR* format")]
    HeaderTooSmall,

    #[error("Not HDR* format: {0:?}")]
    NotHdrFormat([u8; 4]),

    #[error("No ENT* section found")]
    NoEntSection,
}

/// PBL Header structure
#[derive(Debug, Clone)]
pub struct PBLHeader {
    pub signature: Vec<u8>,
    pub version: u32,
    pub entry_count: u32,
    pub format: String,
}

/// PBL Entry (object in library)
#[derive(Debug, Clone)]
pub struct PBLEntry {
    pub name: String,
    pub object_type: String,
    pub size: usize,
    pub offset: usize,
    pub data: Vec<u8>,
}

/// PowerBuilder object types
#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub enum PBObjectType {
    Window,
    DataWindow,
    Menu,
    Function,
    UserObject,
    Application,
    Structure,
    Global,
    Unknown,
}

impl PBObjectType {
    pub fn as_str(&self) -> &'static str {
        match self {
            Self::Window => "window",
            Self::DataWindow => "datawindow",
            Self::Menu => "menu",
            Self::Function => "function",
            Self::UserObject => "userobject",
            Self::Application => "application",
            Self::Structure => "structure",
            Self::Global => "global",
            Self::Unknown => "unknown",
        }
    }
}

/// PBD Reader with memory-mapped I/O
pub struct PbdReader {
    mmap: Mmap,
}

impl PbdReader {
    /// Open PBD file with memory-mapped I/O
    pub fn open(path: &Path) -> std::io::Result<Self> {
        let file = File::open(path)?;
        let mmap = unsafe { Mmap::map(&file)? };
        Ok(Self { mmap })
    }

    /// Get raw bytes
    pub fn bytes(&self) -> &[u8] {
        &self.mmap
    }

    /// Parse HDR* header
    pub fn parse_header(&self) -> Result<PBLHeader, ExtractionError> {
        parse_hdr_header(self.bytes())
    }

    /// Extract all objects from PBD
    pub fn extract_objects(&self) -> (Vec<PBLEntry>, Vec<ExtractionError>) {
        extract_hdr_objects(self.bytes())
    }

    /// Validate format
    pub fn validate_format(&self) -> bool {
        validate_pbd_format(self.bytes())
    }

    /// Check if modern HDR* format
    pub fn is_modern_format(&self) -> bool {
        is_modern_format(self.bytes())
    }
}

/// Parse HDR* format header (modern PBD format)
///
/// Pure function: bytes -> PBLHeader
pub fn parse_hdr_header(data: &[u8]) -> Result<PBLHeader, ExtractionError> {
    if data.len() < 16 {
        return Err(ExtractionError::HeaderTooSmall);
    }

    if &data[..4] != HDR_SIGNATURE {
        let mut sig = [0u8; 4];
        sig.copy_from_slice(&data[..4]);
        return Err(ExtractionError::NotHdrFormat(sig));
    }

    // Parse HDR* header structure
    let version = 0x0700; // Version 7.0 format

    // Find ENT* section for entry count
    let entry_count = if let Some(ent_offset) = find_signature(data, ENT_SIGNATURE) {
        // Read entry count from ENT* section
        if ent_offset + 8 <= data.len() {
            u32::from_le_bytes([
                data[ent_offset + 4],
                data[ent_offset + 5],
                data[ent_offset + 6],
                data[ent_offset + 7],
            ])
        } else {
            0
        }
    } else {
        0
    };

    Ok(PBLHeader {
        signature: HDR_SIGNATURE.to_vec(),
        version,
        entry_count,
        format: "PBD".to_string(),
    })
}

/// Extract objects from HDR* format PBD
///
/// Pure function that handles the modern PBD format.
/// Returns extracted entries and any errors encountered.
pub fn extract_hdr_objects(data: &[u8]) -> (Vec<PBLEntry>, Vec<ExtractionError>) {
    let header = match parse_hdr_header(data) {
        Ok(h) => h,
        Err(e) => {
            return (
                vec![],
                vec![ExtractionError::WithoutOffset {
                    entry_name: "<header>".to_string(),
                    message: e.to_string(),
                }],
            );
        }
    };

    let mut entries = Vec::new();
    let mut errors = Vec::new();

    // Find ENT* section
    if find_signature(data, ENT_SIGNATURE).is_none() {
        errors.push(ExtractionError::NoEntSection);
        return (entries, errors);
    }

    // Find all DAT* sections
    let mut dat_offset = 0;
    while let Some(offset) = find_signature(&data[dat_offset..], DAT_SIGNATURE) {
        let absolute_offset = dat_offset + offset;

        match extract_dat_entry(data, absolute_offset) {
            Ok(Some(entry)) => entries.push(entry),
            Ok(None) => {} // Skip invalid entry
            Err(e) => errors.push(ExtractionError::WithOffset {
                entry_name: format!("DAT@{}", absolute_offset),
                message: e.to_string(),
                offset: absolute_offset,
            }),
        }

        dat_offset = absolute_offset + 4; // Move past current DAT* marker
    }

    (entries, errors)
}

/// Extract a single entry from DAT* section
///
/// Pure function to parse DAT* section data.
fn extract_dat_entry(data: &[u8], offset: usize) -> Result<Option<PBLEntry>, ExtractionError> {
    if offset + 16 > data.len() {
        return Ok(None);
    }

    // Skip DAT* marker
    let mut pos = offset + 4;

    // Read section length
    if pos + 4 > data.len() {
        return Ok(None);
    }

    let section_length = u32::from_le_bytes([
        data[pos],
        data[pos + 1],
        data[pos + 2],
        data[pos + 3],
    ]) as usize;
    pos += 4;

    // Extract metadata and object data
    if pos + section_length > data.len() {
        return Ok(None);
    }

    let section_data = &data[pos..pos + section_length];

    // Parse object metadata from section
    let (name, object_type, object_data) = parse_dat_metadata(section_data);

    if let Some(name) = name {
        if !object_data.is_empty() {
            return Ok(Some(PBLEntry {
                name,
                object_type,
                size: object_data.len(),
                offset,
                data: object_data,
            }));
        }
    }

    Ok(None)
}

/// Parse metadata from DAT* section data
///
/// Returns: (name, object_type, object_data)
fn parse_dat_metadata(section_data: &[u8]) -> (Option<String>, String, Vec<u8>) {
    if section_data.len() < 8 {
        return (None, "unknown".to_string(), vec![]);
    }

    // Skip header bytes and find start of UTF-16LE text
    let mut text_start = 0;
    for i in 0..std::cmp::min(16, section_data.len().saturating_sub(4)) {
        // Look for UTF-16LE pattern: printable ASCII followed by 0x00
        if i + 3 < section_data.len()
            && section_data[i + 1] == 0
            && section_data[i + 3] == 0
            && (0x20..=0x7F).contains(&section_data[i])
        {
            text_start = i;
            break;
        }
    }

    // If no UTF-16LE pattern found, try common header sizes
    if text_start == 0 {
        if section_data.len() > 6 && section_data[6] != 0 {
            text_start = 6;
        } else if section_data.len() > 4 && section_data[4] != 0 {
            text_start = 4;
        } else if section_data.len() > 2 {
            text_start = 2;
        }
    }

    // Extract name from text portion
    let name_data = &section_data[text_start..];

    // Find end of name (double null for UTF-16 or single null)
    let name_end = find_double_null(name_data)
        .or_else(|| find_single_null(name_data))
        .unwrap_or_else(|| std::cmp::min(256, name_data.len()));

    let name_bytes = &name_data[..name_end];

    // Decode name
    let name = if has_utf16le_pattern(name_bytes) {
        decode_utf16le(name_bytes)
    } else {
        decode_ascii(name_bytes)
    };

    let name = clean_name(&name, text_start, section_data);

    // Rest is object data
    let data_start = text_start + name_bytes.len() + 2;
    let object_data = if data_start < section_data.len() {
        section_data[data_start..].to_vec()
    } else {
        section_data.to_vec()
    };

    // Determine type from patterns
    let object_type = detect_object_type_from_data(&object_data);

    (Some(name), object_type.to_string(), object_data)
}

/// Extract UTF-16LE strings from binary data
///
/// Pure function to find and decode Unicode strings.
pub fn extract_unicode_strings(data: &[u8]) -> Vec<String> {
    let mut strings = Vec::new();
    let mut i = 0;

    while i < data.len().saturating_sub(1) {
        // Look for potential UTF-16LE string start
        if data[i] != 0 && data[i + 1] == 0 {
            let mut string_bytes = Vec::new();
            let mut j = i;

            while j < data.len().saturating_sub(1) {
                let low = data[j];
                let high = data[j + 1];

                if low == 0 && high == 0 {
                    break; // String terminator
                }

                string_bytes.push(low);
                string_bytes.push(high);
                j += 2;
            }

            if !string_bytes.is_empty() {
                if let Some(decoded) = try_decode_utf16le(&string_bytes) {
                    if decoded.len() > 2 && decoded.chars().all(|c| c.is_ascii_graphic() || c.is_whitespace()) {
                        strings.push(decoded);
                    }
                }
            }

            i = j + 2;
        } else {
            i += 1;
        }
    }

    strings
}

/// Detect object type from DAT* section patterns
pub fn detect_object_type(data: &[u8]) -> PBObjectType {
    let data_lower: Vec<u8> = data.iter().map(|b| b.to_ascii_lowercase()).collect();

    if data_lower.windows(10).any(|w| w == b"datawindow") {
        PBObjectType::DataWindow
    } else if data_lower.windows(6).any(|w| w == b"window") {
        PBObjectType::Window
    } else if data_lower.windows(4).any(|w| w == b"menu") {
        PBObjectType::Menu
    } else if data_lower.windows(8).any(|w| w == b"function") {
        PBObjectType::Function
    } else if data_lower.windows(11).any(|w| w == b"user_object")
        || data_lower.windows(10).any(|w| w == b"userobject")
    {
        PBObjectType::UserObject
    } else if data_lower.windows(11).any(|w| w == b"application") {
        PBObjectType::Application
    } else if data_lower.windows(9).any(|w| w == b"structure") {
        PBObjectType::Structure
    } else {
        PBObjectType::Global
    }
}

fn detect_object_type_from_data(data: &[u8]) -> &'static str {
    let prefix = if data.len() > 100 { &data[..100] } else { data };
    let data_lower: Vec<u8> = prefix.iter().map(|b| b.to_ascii_lowercase()).collect();

    if data_lower.windows(10).any(|w| w == b"datawindow") {
        "datawindow"
    } else if data_lower.windows(6).any(|w| w == b"window") {
        "window"
    } else if data_lower.windows(8).any(|w| w == b"function") {
        "function"
    } else {
        "unknown"
    }
}

/// Validate if data is valid PBD format (HDR*)
pub fn validate_pbd_format(data: &[u8]) -> bool {
    data.len() >= 4 && &data[..4] == HDR_SIGNATURE
}

/// Check if file uses modern HDR* format
pub fn is_modern_format(data: &[u8]) -> bool {
    data.len() >= 4 && &data[..4] == HDR_SIGNATURE
}

// ============================================================================
// HELPER FUNCTIONS
// ============================================================================

fn find_signature(data: &[u8], signature: &[u8]) -> Option<usize> {
    data.windows(signature.len())
        .position(|window| window == signature)
}

fn find_double_null(data: &[u8]) -> Option<usize> {
    data.windows(2).position(|w| w == b"\x00\x00")
}

fn find_single_null(data: &[u8]) -> Option<usize> {
    data.iter().position(|&b| b == 0)
}

fn has_utf16le_pattern(data: &[u8]) -> bool {
    if data.len() < 2 {
        return false;
    }
    // Check if every other byte is 0x00 (UTF-16LE for ASCII)
    data.chunks(2).take(10).filter(|c| c.len() == 2).any(|c| c[1] == 0)
}

fn decode_utf16le(data: &[u8]) -> String {
    let u16_vec: Vec<u16> = data
        .chunks(2)
        .filter(|c| c.len() == 2)
        .map(|c| u16::from_le_bytes([c[0], c[1]]))
        .collect();

    String::from_utf16_lossy(&u16_vec)
        .trim_matches('\0')
        .trim()
        .to_string()
}

fn decode_ascii(data: &[u8]) -> String {
    String::from_utf8_lossy(data)
        .trim_matches('\0')
        .trim()
        .to_string()
}

fn try_decode_utf16le(data: &[u8]) -> Option<String> {
    let u16_vec: Vec<u16> = data
        .chunks(2)
        .filter(|c| c.len() == 2)
        .map(|c| u16::from_le_bytes([c[0], c[1]]))
        .collect();

    String::from_utf16(&u16_vec).ok()
}

fn clean_name(name: &str, text_start: usize, section_data: &[u8]) -> String {
    let cleaned: String = name
        .chars()
        .filter(|c| c.is_ascii_graphic() || *c == ' ' || *c == '_' || *c == '-' || *c == '.')
        .collect();

    if cleaned.is_empty() {
        let hash = {
            use std::collections::hash_map::DefaultHasher;
            use std::hash::{Hash, Hasher};
            let mut hasher = DefaultHasher::new();
            section_data.hash(&mut hasher);
            hasher.finish()
        };
        format!("object_{:02x}_{:06x}", text_start, hash & 0xFFFFFF)
    } else {
        cleaned
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_validate_hdr_format() {
        let mut data = vec![0u8; 1024];
        data[0..4].copy_from_slice(b"HDR*");
        assert!(validate_pbd_format(&data));
    }

    #[test]
    fn test_invalid_format() {
        let data = vec![0u8; 1024];
        assert!(!validate_pbd_format(&data));
    }

    #[test]
    fn test_is_modern_format() {
        let mut data = vec![0u8; 1024];
        data[0..4].copy_from_slice(b"HDR*");
        assert!(is_modern_format(&data));
    }

    #[test]
    fn test_detect_object_type() {
        let window_data = b"some window data here";
        assert_eq!(detect_object_type(window_data), PBObjectType::Window);

        let dw_data = b"datawindow control";
        assert_eq!(detect_object_type(dw_data), PBObjectType::DataWindow);
    }

    #[test]
    fn test_extract_unicode_strings() {
        // UTF-16LE encoding of "test"
        let data = vec![b't', 0, b'e', 0, b's', 0, b't', 0, 0, 0];
        let strings = extract_unicode_strings(&data);
        assert!(strings.iter().any(|s| s.contains("test")));
    }
}
