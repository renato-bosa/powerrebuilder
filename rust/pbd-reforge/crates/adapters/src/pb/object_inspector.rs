//! Conservative inspection of compiled PowerBuilder object payloads.
//!
//! This module deliberately separates observations from claims. It identifies
//! stable signatures and string-bearing regions, but it does not label any
//! bytes as P-code until their boundaries have been independently validated.

use serde::Serialize;

use super::compiled_object::{
    is_supported_compiled_object_version, parse_compiled_object, CompiledFunctionDefinition,
    CompiledVariable,
};

const DATAWINDOW_MAGIC: &[u8] = b"PDW";
const MAX_STRING_CANDIDATES: usize = 512;

#[derive(Debug, Clone, PartialEq, Eq, Serialize)]
#[serde(tag = "kind", rename_all = "snake_case")]
pub enum ObjectBinaryFormat {
    CompiledObject {
        revision: u16,
        object_type_code: u16,
    },
    DataWindow {
        format_tag: String,
    },
    Unknown {
        leading_bytes_hex: String,
    },
}

#[derive(Debug, Clone, PartialEq, Eq, Serialize)]
pub struct StringCandidate {
    pub offset: usize,
    pub byte_length: usize,
    pub encoding: &'static str,
    pub value: String,
}

#[derive(Debug, Clone, PartialEq, Eq, Serialize)]
pub struct SectionCandidate {
    pub kind: &'static str,
    pub offset: usize,
    pub length: usize,
    pub confidence: &'static str,
    pub evidence: String,
}

#[derive(Debug, Clone, PartialEq, Serialize)]
pub struct ObjectInspection {
    pub format: ObjectBinaryFormat,
    pub size: usize,
    pub leading_bytes_hex: String,
    pub zero_byte_ratio: f64,
    pub string_candidates: Vec<StringCandidate>,
    pub string_candidates_truncated: bool,
    pub section_candidates: Vec<SectionCandidate>,
    /// Regions whose offsets and lengths were proven by a format-specific parser.
    pub validated_pcode_regions: Vec<ValidatedPCodeRegion>,
    pub decode_status: String,
}

#[derive(Debug, Clone, PartialEq, Eq, Serialize)]
pub struct ValidatedPCodeRegion {
    pub function_index: u16,
    pub offset: usize,
    pub length: usize,
    pub debug_offset: usize,
    pub debug_length: usize,
    pub stack_buffer_offset: usize,
    pub stack_buffer_length: usize,
    #[serde(skip_serializing)]
    pub stack_buffer: Vec<u8>,
    pub definition: Option<CompiledFunctionDefinition>,
    pub variables: Vec<CompiledVariable>,
    pub global_variables: Vec<CompiledVariable>,
    pub owner: String,
}

pub fn inspect_object(data: &[u8]) -> ObjectInspection {
    let format = detect_format(data);
    let mut strings = extract_ascii_strings(data);
    strings.extend(extract_utf16le_strings(data));
    strings.sort_by_key(|candidate| candidate.offset);

    let string_candidates_truncated = strings.len() > MAX_STRING_CANDIDATES;
    strings.truncate(MAX_STRING_CANDIDATES);

    let mut section_candidates = fixed_prefix_candidate(data, &format);
    section_candidates.extend(string_cluster_candidates(&strings));

    let zero_count = data.iter().filter(|&&byte| byte == 0).count();
    let zero_byte_ratio = if data.is_empty() {
        0.0
    } else {
        zero_count as f64 / data.len() as f64
    };

    let (validated_pcode_regions, decode_status) = match &format {
        ObjectBinaryFormat::CompiledObject { .. } => match parse_compiled_object(data) {
            Ok(layout) => {
                let regions = layout
                    .functions
                    .iter()
                    .filter(|function| function.pcode_length > 0)
                    .map(|function| ValidatedPCodeRegion {
                        function_index: function.function_index,
                        offset: function.pcode_offset,
                        length: function.pcode_length,
                        debug_offset: function.debug_offset,
                        debug_length: function.debug_length,
                        stack_buffer_offset: function.stack_buffer_offset,
                        stack_buffer_length: function.stack_buffer.len(),
                        stack_buffer: function.stack_buffer.clone(),
                        definition: function.definition.clone(),
                        variables: function.variables.clone(),
                        global_variables: layout.global_variables.clone(),
                        owner: function.definition.as_ref().map_or_else(
                            || {
                                format!(
                                    "object_{:04}_function_{:04}",
                                    function.object_index, function.function_index
                                )
                            },
                            |definition| definition.name.clone(),
                        ),
                    })
                    .collect::<Vec<_>>();
                let status = if regions.is_empty() {
                    "compiled_object_parsed_no_pcode_regions".to_string()
                } else {
                    "pcode_regions_validated_structurally".to_string()
                };
                (regions, status)
            }
            Err(error) => (Vec::new(), format!("compiled_object_parse_error: {error}")),
        },
        ObjectBinaryFormat::DataWindow { .. } => (
            Vec::new(),
            "datawindow_pcode_layout_not_implemented".to_string(),
        ),
        ObjectBinaryFormat::Unknown { .. } => (Vec::new(), "unknown_object_envelope".to_string()),
    };

    ObjectInspection {
        format,
        size: data.len(),
        leading_bytes_hex: bytes_to_hex(&data[..data.len().min(32)]),
        zero_byte_ratio,
        string_candidates: strings,
        string_candidates_truncated,
        section_candidates,
        validated_pcode_regions,
        decode_status,
    }
}

fn detect_format(data: &[u8]) -> ObjectBinaryFormat {
    if data.len() >= 8
        && is_supported_compiled_object_version(u16::from_le_bytes([data[0], data[1]]))
    {
        return ObjectBinaryFormat::CompiledObject {
            revision: u16::from_le_bytes([data[2], data[3]]),
            object_type_code: u16::from_le_bytes([data[4], data[5]]),
        };
    }

    if data.starts_with(DATAWINDOW_MAGIC) {
        let tag_end = data
            .iter()
            .position(|&byte| byte == 0)
            .unwrap_or(data.len().min(16));
        let tag = String::from_utf8_lossy(&data[..tag_end]).to_string();
        return ObjectBinaryFormat::DataWindow { format_tag: tag };
    }

    ObjectBinaryFormat::Unknown {
        leading_bytes_hex: bytes_to_hex(&data[..data.len().min(8)]),
    }
}

fn fixed_prefix_candidate(data: &[u8], format: &ObjectBinaryFormat) -> Vec<SectionCandidate> {
    match format {
        ObjectBinaryFormat::CompiledObject { .. } => vec![SectionCandidate {
            kind: "compiled_object_prefix",
            offset: 0,
            length: data.len().min(16),
            confidence: "high",
            evidence: "PB 2022 0x0152/0x0153 compiled-object envelope".to_string(),
        }],
        ObjectBinaryFormat::DataWindow { format_tag } => vec![SectionCandidate {
            kind: "datawindow_prefix",
            offset: 0,
            length: data.len().min(format_tag.len() + 1),
            confidence: "high",
            evidence: format!("DataWindow format tag {format_tag}"),
        }],
        ObjectBinaryFormat::Unknown { .. } => Vec::new(),
    }
}

fn extract_ascii_strings(data: &[u8]) -> Vec<StringCandidate> {
    let mut result = Vec::new();
    let mut offset = 0;

    while offset < data.len() {
        if !is_printable_ascii(data[offset]) {
            offset += 1;
            continue;
        }

        let start = offset;
        while offset < data.len() && is_printable_ascii(data[offset]) {
            offset += 1;
        }
        let value = String::from_utf8_lossy(&data[start..offset]).to_string();
        if value.trim().len() >= 4 && looks_like_text(&value) {
            result.push(StringCandidate {
                offset: start,
                byte_length: offset - start,
                encoding: "ascii",
                value,
            });
        }
    }

    result
}

fn extract_utf16le_strings(data: &[u8]) -> Vec<StringCandidate> {
    let mut result = Vec::new();
    let mut offset = 0;

    while offset + 1 < data.len() {
        if !is_printable_ascii(data[offset]) || data[offset + 1] != 0 {
            offset += 1;
            continue;
        }

        let start = offset;
        let mut units = Vec::new();
        while offset + 1 < data.len() && is_printable_ascii(data[offset]) && data[offset + 1] == 0 {
            units.push(data[offset] as u16);
            offset += 2;
        }

        let value = String::from_utf16_lossy(&units);
        if value.trim().len() >= 3 && looks_like_text(&value) {
            result.push(StringCandidate {
                offset: start,
                byte_length: offset - start,
                encoding: "utf-16le",
                value,
            });
        }
    }

    result
}

fn string_cluster_candidates(strings: &[StringCandidate]) -> Vec<SectionCandidate> {
    let mut clusters = Vec::new();
    let mut cursor = 0;

    while cursor < strings.len() {
        let start_index = cursor;
        let start = strings[cursor].offset;
        let mut end = strings[cursor].offset + strings[cursor].byte_length;
        cursor += 1;

        while cursor < strings.len() && strings[cursor].offset <= end.saturating_add(64) {
            end = end.max(strings[cursor].offset + strings[cursor].byte_length);
            cursor += 1;
        }

        let count = cursor - start_index;
        if count >= 2 || strings[start_index].value.len() >= 8 {
            clusters.push(SectionCandidate {
                kind: "string_cluster",
                offset: start,
                length: end - start,
                confidence: "candidate",
                evidence: format!("{count} printable string candidate(s) within 64-byte gaps"),
            });
        }
    }

    clusters
}

fn is_printable_ascii(byte: u8) -> bool {
    (0x20..=0x7e).contains(&byte)
}

fn looks_like_text(value: &str) -> bool {
    let trimmed = value.trim();
    let meaningful = trimmed
        .chars()
        .filter(|character| {
            character.is_ascii_alphanumeric()
                || character.is_ascii_whitespace()
                || matches!(character, '_' | '-' | '.' | ':' | '/' | '\\')
        })
        .count();

    trimmed
        .chars()
        .any(|character| character.is_ascii_alphanumeric())
        && meaningful * 4 >= trimmed.chars().count() * 3
}

fn bytes_to_hex(data: &[u8]) -> String {
    data.iter()
        .map(|byte| format!("{byte:02X}"))
        .collect::<Vec<_>>()
        .join(" ")
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn identifies_compiled_object_without_claiming_pcode() {
        let mut data = vec![0x53, 0x01, 0x03, 0x00, 0x7d, 0x40, 0x01, 0x00];
        data.extend_from_slice(&[0; 24]);
        data.extend("f_test\0".encode_utf16().flat_map(u16::to_le_bytes));

        let inspection = inspect_object(&data);
        assert_eq!(
            inspection.format,
            ObjectBinaryFormat::CompiledObject {
                revision: 3,
                object_type_code: 0x407d,
            }
        );
        assert!(inspection.validated_pcode_regions.is_empty());
        assert!(inspection
            .decode_status
            .starts_with("compiled_object_parse_error"));
        assert!(inspection
            .string_candidates
            .iter()
            .any(|candidate| candidate.value == "f_test"));
    }

    #[test]
    fn identifies_0152_pb2022_compiled_object_envelope() {
        let data = [0x52, 0x01, 0x03, 0x00, 0x7d, 0x40, 0x01, 0x00];
        let inspection = inspect_object(&data);

        assert_eq!(
            inspection.format,
            ObjectBinaryFormat::CompiledObject {
                revision: 3,
                object_type_code: 0x407d,
            }
        );
        assert!(inspection
            .decode_status
            .starts_with("compiled_object_parse_error"));
    }

    #[test]
    fn identifies_datawindow_format_tag() {
        let inspection = inspect_object(b"PDW2200\0rest");
        assert_eq!(
            inspection.format,
            ObjectBinaryFormat::DataWindow {
                format_tag: "PDW2200".to_string(),
            }
        );
    }

    #[test]
    fn ignores_whitespace_only_string_runs() {
        let inspection = inspect_object(&[b' ', 0, b' ', 0, b' ', 0, b' ', 0]);
        assert!(inspection.string_candidates.is_empty());
    }

    #[test]
    fn ignores_binary_punctuation_that_only_looks_printable() {
        let inspection = inspect_object(b"}@}@");
        assert!(inspection.string_candidates.is_empty());
    }
}
