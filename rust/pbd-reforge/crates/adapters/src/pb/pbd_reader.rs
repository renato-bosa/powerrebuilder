//! PBD Format Reader - Complete HDR* Format Implementation
//!
//! Ported from Python implementation with full HDR*/ENT*/DAT*/NOD*/FRE* support.
//! Pure functions for parsing PowerBuilder PBD (compiled) library files.

use memmap2::Mmap;
use std::collections::HashSet;
use std::fs::File;
use std::path::Path;
use thiserror::Error;

/// HDR* format signatures
const HDR_SIGNATURE: &[u8] = b"HDR*";
const ENT_SIGNATURE: &[u8] = b"ENT*";
const DAT_SIGNATURE: &[u8] = b"DAT*";
const NOD_SIGNATURE: &[u8] = b"NOD*";
#[cfg(test)]
const FRE_SIGNATURE: &[u8] = b"FRE*";

const BLOCK_SIZE: usize = 512;
const NODE_BLOCK_SIZE: usize = BLOCK_SIZE * 6;
const NODE_HEADER_SIZE: usize = 32;
const ENTRY_HEADER_SIZE: usize = 28;
const DATA_HEADER_SIZE: usize = 10;
const MAX_DATA_PAYLOAD: usize = BLOCK_SIZE - DATA_HEADER_SIZE;

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
    /// PBL container format version (for example, 0x0600).
    pub version: u32,
    /// PowerBuilder runtime/build string stored in the Unicode header comment.
    pub runtime_version: Option<String>,
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

#[derive(Debug, Clone)]
struct EntryDefinition {
    name: String,
    object_type: String,
    size: usize,
    data_offset: usize,
    directory_offset: usize,
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
    if data.len() < 40 {
        return Err(ExtractionError::HeaderTooSmall);
    }

    if &data[..4] != HDR_SIGNATURE {
        let mut sig = [0u8; 4];
        sig.copy_from_slice(&data[..4]);
        return Err(ExtractionError::NotHdrFormat(sig));
    }

    // Unicode PBL/PBD headers store the four-character container version at
    // byte 32 as UTF-16LE (for example "0600"). This is the container format
    // version, not the PowerBuilder product version.
    let version_text = decode_utf16le(&data[32..40]);
    let version = u32::from_str_radix(version_text.trim(), 16).unwrap_or(0);

    let header_end = data.len().min(1024);
    let runtime_version = find_runtime_version(&data[40..header_end]);
    let (definitions, _) = parse_node_entries(data);

    Ok(PBLHeader {
        signature: HDR_SIGNATURE.to_vec(),
        version,
        runtime_version,
        entry_count: definitions.len() as u32,
        format: "PBD".to_string(),
    })
}

/// Extract objects from HDR* format PBD
///
/// Pure function that handles the modern PBD format.
/// Returns extracted entries and any errors encountered.
pub fn extract_hdr_objects(data: &[u8]) -> (Vec<PBLEntry>, Vec<ExtractionError>) {
    match parse_hdr_header(data) {
        Ok(_) => {}
        Err(e) => {
            return (
                vec![],
                vec![ExtractionError::WithoutOffset {
                    entry_name: "<header>".to_string(),
                    message: e.to_string(),
                }],
            );
        }
    }

    let mut entries = Vec::new();
    let (definitions, mut errors) = parse_node_entries(data);

    if definitions.is_empty() {
        errors.push(ExtractionError::NoEntSection);
        return (entries, errors);
    }

    for definition in definitions {
        match extract_data_chain(data, definition.data_offset, definition.size) {
            Ok(object_data) => entries.push(PBLEntry {
                name: definition.name,
                object_type: definition.object_type,
                size: object_data.len(),
                offset: definition.data_offset,
                data: object_data,
            }),
            Err(e) => errors.push(ExtractionError::WithOffset {
                entry_name: definition.name,
                message: e.to_string(),
                offset: definition.directory_offset,
            }),
        }
    }

    (entries, errors)
}

/// Parse all directory entries stored in 3072-byte NOD* blocks.
fn parse_node_entries(data: &[u8]) -> (Vec<EntryDefinition>, Vec<ExtractionError>) {
    let mut definitions = Vec::new();
    let mut errors = Vec::new();

    for node_offset in (0..data.len().saturating_sub(NODE_HEADER_SIZE)).step_by(BLOCK_SIZE) {
        if &data[node_offset..node_offset + 4] != NOD_SIGNATURE {
            continue;
        }

        let node_end = (node_offset + NODE_BLOCK_SIZE).min(data.len());
        let entry_count = read_u16(data, node_offset + 20).unwrap_or(0) as usize;
        if entry_count > 2048 {
            errors.push(ExtractionError::WithOffset {
                entry_name: "<node>".to_string(),
                message: format!("unreasonable entry count {entry_count}"),
                offset: node_offset,
            });
            continue;
        }

        let mut entry_offset = node_offset + NODE_HEADER_SIZE;
        for _ in 0..entry_count {
            match parse_entry_definition(data, entry_offset, node_end) {
                Ok((definition, next_offset)) => {
                    definitions.push(definition);
                    entry_offset = next_offset;
                }
                Err(e) => {
                    errors.push(ExtractionError::WithOffset {
                        entry_name: "<entry>".to_string(),
                        message: e.to_string(),
                        offset: entry_offset,
                    });
                    break;
                }
            }
        }
    }

    (definitions, errors)
}

fn parse_entry_definition(
    data: &[u8],
    offset: usize,
    node_end: usize,
) -> Result<(EntryDefinition, usize), ExtractionError> {
    if offset + ENTRY_HEADER_SIZE > node_end || offset + ENTRY_HEADER_SIZE > data.len() {
        return Err(ExtractionError::InvalidFormat(
            "entry header extends past its NOD block".to_string(),
        ));
    }
    if &data[offset..offset + 4] != ENT_SIGNATURE {
        return Err(ExtractionError::InvalidFormat(format!(
            "expected ENT* signature, found {:?}",
            &data[offset..offset + 4]
        )));
    }

    let entry_version = decode_utf16le(&data[offset + 4..offset + 12]);
    if entry_version.len() != 4 || !entry_version.chars().all(|c| c.is_ascii_hexdigit()) {
        return Err(ExtractionError::InvalidFormat(format!(
            "invalid Unicode entry version {entry_version:?}"
        )));
    }

    let data_offset = read_u32(data, offset + 12).unwrap_or(0) as usize;
    let size = read_u32(data, offset + 16).unwrap_or(0) as usize;
    let comment_length = read_u16(data, offset + 24).unwrap_or(0) as usize;
    let name_length = read_u16(data, offset + 26).unwrap_or(0) as usize;
    let next_offset = offset
        .checked_add(ENTRY_HEADER_SIZE)
        .and_then(|value| value.checked_add(name_length))
        .and_then(|value| value.checked_add(comment_length))
        .ok_or_else(|| ExtractionError::InvalidFormat("entry length overflow".to_string()))?;

    if name_length < 2 || name_length % 2 != 0 || next_offset > node_end || next_offset > data.len()
    {
        return Err(ExtractionError::InvalidFormat(format!(
            "invalid entry lengths: name={name_length}, comment={comment_length}"
        )));
    }

    let name_end = offset + ENTRY_HEADER_SIZE + name_length;
    let name = decode_utf16le(&data[offset + ENTRY_HEADER_SIZE..name_end]);
    if name.is_empty() || name.chars().any(char::is_control) {
        return Err(ExtractionError::InvalidFormat(format!(
            "invalid object name {name:?}"
        )));
    }

    if data_offset % BLOCK_SIZE != 0
        || data_offset + DATA_HEADER_SIZE > data.len()
        || &data[data_offset..data_offset + 4] != DAT_SIGNATURE
    {
        return Err(ExtractionError::InvalidFormat(format!(
            "entry {name} points to invalid DAT* block at {data_offset}"
        )));
    }
    if size > data.len() {
        return Err(ExtractionError::InvalidFormat(format!(
            "entry {name} declares implausible size {size}"
        )));
    }

    Ok((
        EntryDefinition {
            object_type: object_type_from_name(&name).to_string(),
            name,
            size,
            data_offset,
            directory_offset: offset,
        },
        next_offset,
    ))
}

/// Follow the forward-linked DAT* blocks for one entry.
fn extract_data_chain(
    data: &[u8],
    first_offset: usize,
    expected_size: usize,
) -> Result<Vec<u8>, ExtractionError> {
    if expected_size == 0 {
        return Ok(Vec::new());
    }

    let mut result = Vec::with_capacity(expected_size);
    let mut current_offset = first_offset;
    let mut visited = HashSet::new();

    while result.len() < expected_size {
        if !visited.insert(current_offset) {
            return Err(ExtractionError::InvalidFormat(format!(
                "cycle in DAT* chain at {current_offset}"
            )));
        }
        if current_offset % BLOCK_SIZE != 0 || current_offset + DATA_HEADER_SIZE > data.len() {
            return Err(ExtractionError::InvalidFormat(format!(
                "invalid DAT* block offset {current_offset}"
            )));
        }
        if &data[current_offset..current_offset + 4] != DAT_SIGNATURE {
            return Err(ExtractionError::InvalidFormat(format!(
                "missing DAT* signature at {current_offset}"
            )));
        }

        let next_offset = read_u32(data, current_offset + 4).unwrap_or(0) as usize;
        let payload_length = read_u16(data, current_offset + 8).unwrap_or(0) as usize;
        if payload_length > MAX_DATA_PAYLOAD
            || current_offset + DATA_HEADER_SIZE + payload_length > data.len()
        {
            return Err(ExtractionError::InvalidFormat(format!(
                "invalid DAT* payload length {payload_length} at {current_offset}"
            )));
        }

        let remaining = expected_size - result.len();
        if payload_length > remaining {
            return Err(ExtractionError::InvalidFormat(format!(
                "DAT* chain contains more data than the declared object size at {current_offset}"
            )));
        }
        result.extend_from_slice(
            &data[current_offset + DATA_HEADER_SIZE
                ..current_offset + DATA_HEADER_SIZE + payload_length],
        );

        if result.len() == expected_size {
            break;
        }
        if next_offset == 0 {
            return Err(ExtractionError::InvalidFormat(format!(
                "DAT* chain ended after {} of {expected_size} bytes",
                result.len()
            )));
        }
        current_offset = next_offset;
    }

    Ok(result)
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
                    if decoded.len() > 2
                        && decoded
                            .chars()
                            .all(|c| c.is_ascii_graphic() || c.is_whitespace())
                    {
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

fn object_type_from_name(name: &str) -> &'static str {
    let extension = name.rsplit('.').next().unwrap_or_default();
    match extension.to_ascii_lowercase().as_str() {
        "apl" | "sra" => "application",
        "dwo" | "srd" => "datawindow",
        "fun" | "srf" => "function",
        "men" | "srm" => "menu",
        "str" | "srs" => "structure",
        "udo" | "sru" => "userobject",
        "win" | "srw" => "window",
        _ => "unknown",
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

fn read_u16(data: &[u8], offset: usize) -> Option<u16> {
    let bytes = data.get(offset..offset + 2)?;
    Some(u16::from_le_bytes([bytes[0], bytes[1]]))
}

fn read_u32(data: &[u8], offset: usize) -> Option<u32> {
    let bytes = data.get(offset..offset + 4)?;
    Some(u32::from_le_bytes([bytes[0], bytes[1], bytes[2], bytes[3]]))
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

fn try_decode_utf16le(data: &[u8]) -> Option<String> {
    let u16_vec: Vec<u16> = data
        .chunks(2)
        .filter(|c| c.len() == 2)
        .map(|c| u16::from_le_bytes([c[0], c[1]]))
        .collect();

    String::from_utf16(&u16_vec).ok()
}

fn find_runtime_version(data: &[u8]) -> Option<String> {
    let mut offset = 0;
    while offset + 1 < data.len() {
        if data[offset].is_ascii_digit() && data[offset + 1] == 0 {
            let mut current = offset;
            let mut value = String::new();
            while current + 1 < data.len()
                && data[current + 1] == 0
                && (data[current].is_ascii_digit() || data[current] == b'.')
            {
                value.push(data[current] as char);
                current += 2;
            }
            if value.len() >= 3 && value.contains('.') {
                return Some(value);
            }
            offset = current;
        } else {
            offset += 2;
        }
    }
    None
}

#[cfg(test)]
mod tests {
    use super::*;

    fn write_u16(data: &mut [u8], offset: usize, value: u16) {
        data[offset..offset + 2].copy_from_slice(&value.to_le_bytes());
    }

    fn write_u32(data: &mut [u8], offset: usize, value: u32) {
        data[offset..offset + 4].copy_from_slice(&value.to_le_bytes());
    }

    fn utf16z(value: &str) -> Vec<u8> {
        value
            .encode_utf16()
            .chain(std::iter::once(0))
            .flat_map(u16::to_le_bytes)
            .collect()
    }

    fn write_entry(
        data: &mut [u8],
        offset: usize,
        name: &str,
        data_offset: usize,
        size: usize,
    ) -> usize {
        data[offset..offset + 4].copy_from_slice(ENT_SIGNATURE);
        let version: Vec<u8> = "0600".encode_utf16().flat_map(u16::to_le_bytes).collect();
        data[offset + 4..offset + 12].copy_from_slice(&version);
        write_u32(data, offset + 12, data_offset as u32);
        write_u32(data, offset + 16, size as u32);
        let encoded_name = utf16z(name);
        write_u16(data, offset + 26, encoded_name.len() as u16);
        data[offset + ENTRY_HEADER_SIZE..offset + ENTRY_HEADER_SIZE + encoded_name.len()]
            .copy_from_slice(&encoded_name);
        offset + ENTRY_HEADER_SIZE + encoded_name.len()
    }

    fn write_data_chain(data: &mut [u8], offsets: &[usize], payload: &[u8]) {
        let mut consumed = 0;
        for (index, &offset) in offsets.iter().enumerate() {
            let length = (payload.len() - consumed).min(MAX_DATA_PAYLOAD);
            data[offset..offset + 4].copy_from_slice(DAT_SIGNATURE);
            let next = offsets.get(index + 1).copied().unwrap_or(0);
            write_u32(data, offset + 4, next as u32);
            write_u16(data, offset + 8, length as u16);
            data[offset + DATA_HEADER_SIZE..offset + DATA_HEADER_SIZE + length]
                .copy_from_slice(&payload[consumed..consumed + length]);
            consumed += length;
        }
        assert_eq!(consumed, payload.len());
    }

    fn synthetic_pbd() -> (Vec<u8>, Vec<u8>, Vec<u8>) {
        let mut data = vec![0u8; 6144];
        data[0..4].copy_from_slice(HDR_SIGNATURE);
        let product: Vec<u8> = "PowerBuilder\0"
            .encode_utf16()
            .flat_map(u16::to_le_bytes)
            .collect();
        data[4..4 + product.len()].copy_from_slice(&product);
        let version: Vec<u8> = "0600".encode_utf16().flat_map(u16::to_le_bytes).collect();
        data[32..40].copy_from_slice(&version);
        let runtime: Vec<u8> = "22.1.0.2819\0"
            .encode_utf16()
            .flat_map(u16::to_le_bytes)
            .collect();
        data[46..46 + runtime.len()].copy_from_slice(&runtime);
        data[1024..1028].copy_from_slice(FRE_SIGNATURE);

        let node_offset = 1536;
        data[node_offset..node_offset + 4].copy_from_slice(NOD_SIGNATURE);
        write_u16(&mut data, node_offset + 20, 2);

        let first_payload = b"first compiled object".to_vec();
        let second_payload = vec![0xA5; 600];
        let next_entry = write_entry(
            &mut data,
            node_offset + NODE_HEADER_SIZE,
            "app.apl",
            4608,
            first_payload.len(),
        );
        write_entry(
            &mut data,
            next_entry,
            "window.win",
            5120,
            second_payload.len(),
        );
        write_data_chain(&mut data, &[4608], &first_payload);
        write_data_chain(&mut data, &[5120, 5632], &second_payload);

        (data, first_payload, second_payload)
    }

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

    #[test]
    fn test_parse_unicode_header_and_directory_count() {
        let (data, _, _) = synthetic_pbd();
        let header = parse_hdr_header(&data).unwrap();

        assert_eq!(header.version, 0x0600);
        assert_eq!(header.runtime_version.as_deref(), Some("22.1.0.2819"));
        assert_eq!(header.entry_count, 2);
    }

    #[test]
    fn test_extract_entries_through_dat_chains() {
        let (data, first_payload, second_payload) = synthetic_pbd();
        let (entries, errors) = extract_hdr_objects(&data);

        assert!(errors.is_empty(), "unexpected errors: {errors:?}");
        assert_eq!(entries.len(), 2);
        assert_eq!(entries[0].name, "app.apl");
        assert_eq!(entries[0].object_type, "application");
        assert_eq!(entries[0].data, first_payload);
        assert_eq!(entries[1].name, "window.win");
        assert_eq!(entries[1].object_type, "window");
        assert_eq!(entries[1].data, second_payload);
    }

    #[test]
    fn test_reports_truncated_dat_chain() {
        let (mut data, _, _) = synthetic_pbd();
        write_u32(&mut data, 5120 + 4, 0);
        let (entries, errors) = extract_hdr_objects(&data);

        assert_eq!(entries.len(), 1);
        assert_eq!(errors.len(), 1);
        assert!(errors[0].to_string().contains("chain ended"));
    }
}
