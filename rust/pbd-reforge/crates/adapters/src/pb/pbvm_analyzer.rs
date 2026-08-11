//! Automated analysis of PowerBuilder VM PE images.
//!
//! The first stage locates opcode-width tables by correlating the known PB 11
//! width profile with strided integer data in the runtime image. This replaces
//! version-specific machine-code byte signatures used by older tools.

use iced_x86::{Decoder, DecoderOptions, FlowControl, Formatter, IntelFormatter};
use serde::Serialize;
use std::collections::HashSet;
use thiserror::Error;

use super::opcodes::PB11_PLUS_OPERAND_WORDS;

const TARGET_OPCODES: [usize; 2] = [0x0251, 0x0253];
const ANCHOR_INDEX: usize = 0x13;
const MIN_REFERENCE_MATCH: usize = 64;
const MAX_TABLE_ENTRIES: usize = 2048;

#[derive(Debug, Clone, PartialEq, Eq, Error)]
pub enum PbVmAnalysisError {
    #[error("invalid PE image: {0}")]
    InvalidPe(String),
}

#[derive(Debug, Clone, PartialEq, Eq, Serialize)]
pub struct PbVmAnalysis {
    pub file_size: usize,
    pub blake3: String,
    pub machine: u16,
    pub bitness: u8,
    pub image_base: u64,
    pub entry_point_rva: u32,
    pub sections: Vec<PeSection>,
    pub width_table_candidates: Vec<WidthTableCandidate>,
}

#[derive(Debug, Clone, PartialEq, Eq, Serialize)]
pub struct PeSection {
    pub name: String,
    pub virtual_address: u32,
    pub virtual_size: u32,
    pub raw_offset: u32,
    pub raw_size: u32,
    pub characteristics: u32,
}

#[derive(Debug, Clone, PartialEq, Eq, Serialize)]
pub struct WidthTableCandidate {
    pub encoding: &'static str,
    /// File offset of opcode zero's width value, not necessarily record start.
    pub value_file_offset: usize,
    pub value_rva: Option<u32>,
    pub stride: usize,
    pub matched_reference_entries: usize,
    pub extracted_entry_count: usize,
    pub opcode_0251_words: Option<u8>,
    pub opcode_0253_words: Option<u8>,
    pub new_opcode_records: Vec<VmOpcodeRecord>,
}

#[derive(Debug, Clone, PartialEq, Eq, Serialize)]
pub struct VmOpcodeRecord {
    pub opcode: u16,
    pub handler_va: u32,
    pub handler_rva: Option<u32>,
    pub handler_file_offset: Option<usize>,
    pub operand_words: u8,
    pub metadata: u32,
    pub instructions: Vec<VmInstruction>,
}

#[derive(Debug, Clone, PartialEq, Eq, Serialize)]
pub struct VmInstruction {
    pub address: u64,
    pub bytes_hex: String,
    pub text: String,
}

pub fn analyze_pbvm(data: &[u8]) -> Result<PbVmAnalysis, PbVmAnalysisError> {
    let pe = parse_pe(data)?;
    let mut width_table_candidates = find_u32_width_tables(data, &pe);
    width_table_candidates.extend(find_byte_width_tables(data, &pe));
    width_table_candidates.sort_by(|left, right| {
        right
            .matched_reference_entries
            .cmp(&left.matched_reference_entries)
            .then_with(|| right.extracted_entry_count.cmp(&left.extracted_entry_count))
            .then_with(|| left.value_file_offset.cmp(&right.value_file_offset))
    });

    Ok(PbVmAnalysis {
        file_size: data.len(),
        blake3: blake3::hash(data).to_hex().to_string(),
        machine: pe.machine,
        bitness: pe.bitness,
        image_base: pe.image_base,
        entry_point_rva: pe.entry_point_rva,
        sections: pe.sections,
        width_table_candidates,
    })
}

fn find_u32_width_tables(data: &[u8], pe: &ParsedPe) -> Vec<WidthTableCandidate> {
    let anchor = PB11_PLUS_OPERAND_WORDS[ANCHOR_INDEX] as u32;
    let anchor_bytes = anchor.to_le_bytes();
    let mut seen = HashSet::new();
    let mut candidates = Vec::new();

    for anchor_offset in find_subslices(data, &anchor_bytes) {
        for stride in 4..=32 {
            let Some(value_file_offset) = anchor_offset.checked_sub(ANCHOR_INDEX * stride) else {
                continue;
            };
            if !seen.insert((value_file_offset, stride)) {
                continue;
            }

            let matched = count_reference_matches_u32(data, value_file_offset, stride);
            if matched < MIN_REFERENCE_MATCH {
                continue;
            }

            let values = extract_u32_widths(data, value_file_offset, stride);
            candidates.push(make_candidate(
                "little_endian_u32_strided",
                value_file_offset,
                stride,
                matched,
                &values,
                data,
                pe,
            ));
        }
    }

    candidates
}

fn find_byte_width_tables(data: &[u8], pe: &ParsedPe) -> Vec<WidthTableCandidate> {
    let reference = PB11_PLUS_OPERAND_WORDS.as_slice();
    find_subslices(data, &reference[..MIN_REFERENCE_MATCH])
        .into_iter()
        .map(|value_file_offset| {
            let mut values = Vec::new();
            for &value in data[value_file_offset..].iter().take(MAX_TABLE_ENTRIES) {
                values.push(value);
            }
            make_candidate(
                "byte_array",
                value_file_offset,
                1,
                count_reference_matches_bytes(data, value_file_offset),
                &values,
                data,
                pe,
            )
        })
        .collect()
}

fn make_candidate(
    encoding: &'static str,
    value_file_offset: usize,
    stride: usize,
    matched_reference_entries: usize,
    values: &[u8],
    data: &[u8],
    pe: &ParsedPe,
) -> WidthTableCandidate {
    let new_opcode_records = if encoding == "little_endian_u32_strided" && stride >= 12 {
        extract_opcode_records(data, value_file_offset, stride, values, pe)
    } else {
        Vec::new()
    };
    WidthTableCandidate {
        encoding,
        value_file_offset,
        value_rva: file_offset_to_rva(value_file_offset, &pe.sections),
        stride,
        matched_reference_entries,
        extracted_entry_count: values.len(),
        opcode_0251_words: values.get(TARGET_OPCODES[0]).copied(),
        opcode_0253_words: values.get(TARGET_OPCODES[1]).copied(),
        new_opcode_records,
    }
}

fn extract_opcode_records(
    data: &[u8],
    value_file_offset: usize,
    stride: usize,
    values: &[u8],
    pe: &ParsedPe,
) -> Vec<VmOpcodeRecord> {
    let Some(record_start) = value_file_offset.checked_sub(4) else {
        return Vec::new();
    };
    (0x0247..values.len().min(u16::MAX as usize))
        .filter_map(|opcode| {
            let offset = record_start.checked_add(opcode.checked_mul(stride)?)?;
            let handler_va = read_u32(data, offset)?;
            let metadata = read_u32(data, offset + 8)?;
            let handler_rva = u64::from(handler_va)
                .checked_sub(pe.image_base)
                .and_then(|rva| u32::try_from(rva).ok());
            let handler_file_offset =
                handler_rva.and_then(|rva| rva_to_file_offset(rva, &pe.sections));
            let instructions = handler_file_offset
                .map(|file_offset| {
                    disassemble_handler(data, file_offset, u64::from(handler_va), pe.bitness.into())
                })
                .unwrap_or_default();
            Some(VmOpcodeRecord {
                opcode: opcode as u16,
                handler_va,
                handler_rva,
                handler_file_offset,
                operand_words: values[opcode],
                metadata,
                instructions,
            })
        })
        .collect()
}

fn disassemble_handler(
    data: &[u8],
    file_offset: usize,
    virtual_address: u64,
    bitness: u32,
) -> Vec<VmInstruction> {
    const MAX_HANDLER_BYTES: usize = 192;
    const MAX_HANDLER_INSTRUCTIONS: usize = 48;

    let end = data
        .len()
        .min(file_offset.saturating_add(MAX_HANDLER_BYTES));
    let bytes = &data[file_offset..end];
    let mut decoder = Decoder::with_ip(bitness, bytes, virtual_address, DecoderOptions::NONE);
    let mut formatter = IntelFormatter::new();
    let mut result = Vec::new();

    while decoder.can_decode() && result.len() < MAX_HANDLER_INSTRUCTIONS {
        let instruction = decoder.decode();
        let start = instruction.ip().saturating_sub(virtual_address) as usize;
        let finish = start.saturating_add(instruction.len()).min(bytes.len());
        let mut text = String::new();
        formatter.format(&instruction, &mut text);
        result.push(VmInstruction {
            address: instruction.ip(),
            bytes_hex: bytes_to_hex(&bytes[start..finish]),
            text,
        });
        if matches!(instruction.flow_control(), FlowControl::Return) {
            break;
        }
    }
    result
}

fn count_reference_matches_u32(data: &[u8], start: usize, stride: usize) -> usize {
    PB11_PLUS_OPERAND_WORDS
        .iter()
        .enumerate()
        .take_while(|(index, expected)| {
            read_u32(data, start + index * stride)
                .map(|actual| actual == **expected as u32)
                .unwrap_or(false)
        })
        .count()
}

fn count_reference_matches_bytes(data: &[u8], start: usize) -> usize {
    PB11_PLUS_OPERAND_WORDS
        .iter()
        .enumerate()
        .take_while(|(index, expected)| data.get(start + index) == Some(expected))
        .count()
}

fn extract_u32_widths(data: &[u8], start: usize, stride: usize) -> Vec<u8> {
    let mut result = Vec::new();
    for index in 0..MAX_TABLE_ENTRIES {
        let Some(value) = read_u32(data, start + index * stride) else {
            break;
        };
        let Ok(width) = u8::try_from(value) else {
            break;
        };
        result.push(width);
    }
    result
}

fn find_subslices(data: &[u8], needle: &[u8]) -> Vec<usize> {
    if needle.is_empty() || needle.len() > data.len() {
        return Vec::new();
    }
    data.windows(needle.len())
        .enumerate()
        .filter_map(|(offset, window)| (window == needle).then_some(offset))
        .collect()
}

#[derive(Debug)]
struct ParsedPe {
    machine: u16,
    bitness: u8,
    image_base: u64,
    entry_point_rva: u32,
    sections: Vec<PeSection>,
}

fn parse_pe(data: &[u8]) -> Result<ParsedPe, PbVmAnalysisError> {
    if data.get(..2) != Some(b"MZ") {
        return Err(PbVmAnalysisError::InvalidPe(
            "missing DOS MZ signature".to_string(),
        ));
    }
    let pe_offset = read_u32(data, 0x3c)
        .ok_or_else(|| PbVmAnalysisError::InvalidPe("missing e_lfanew".to_string()))?
        as usize;
    if data.get(pe_offset..pe_offset + 4) != Some(b"PE\0\0") {
        return Err(PbVmAnalysisError::InvalidPe(
            "missing PE signature".to_string(),
        ));
    }

    let coff = pe_offset + 4;
    let machine = read_u16(data, coff)
        .ok_or_else(|| PbVmAnalysisError::InvalidPe("truncated COFF header".to_string()))?;
    let section_count = read_u16(data, coff + 2)
        .ok_or_else(|| PbVmAnalysisError::InvalidPe("truncated section count".to_string()))?
        as usize;
    let optional_size = read_u16(data, coff + 16)
        .ok_or_else(|| PbVmAnalysisError::InvalidPe("truncated optional size".to_string()))?
        as usize;
    let optional = coff + 20;
    let optional_magic = read_u16(data, optional)
        .ok_or_else(|| PbVmAnalysisError::InvalidPe("missing optional header".to_string()))?;
    let (bitness, image_base) = match optional_magic {
        0x010b => (
            32,
            read_u32(data, optional + 28)
                .ok_or_else(|| PbVmAnalysisError::InvalidPe("missing image base".to_string()))?
                as u64,
        ),
        0x020b => (
            64,
            read_u64(data, optional + 24)
                .ok_or_else(|| PbVmAnalysisError::InvalidPe("missing image base".to_string()))?,
        ),
        magic => {
            return Err(PbVmAnalysisError::InvalidPe(format!(
                "unsupported optional-header magic 0x{magic:04X}"
            )))
        }
    };
    let entry_point_rva = read_u32(data, optional + 16)
        .ok_or_else(|| PbVmAnalysisError::InvalidPe("missing entry point".to_string()))?;

    let section_table = optional + optional_size;
    let mut sections = Vec::with_capacity(section_count);
    for index in 0..section_count {
        let offset = section_table + index * 40;
        let record = data.get(offset..offset + 40).ok_or_else(|| {
            PbVmAnalysisError::InvalidPe(format!("truncated section header {index}"))
        })?;
        let name_end = record[..8].iter().position(|byte| *byte == 0).unwrap_or(8);
        sections.push(PeSection {
            name: String::from_utf8_lossy(&record[..name_end]).to_string(),
            virtual_size: u32::from_le_bytes(record[8..12].try_into().unwrap()),
            virtual_address: u32::from_le_bytes(record[12..16].try_into().unwrap()),
            raw_size: u32::from_le_bytes(record[16..20].try_into().unwrap()),
            raw_offset: u32::from_le_bytes(record[20..24].try_into().unwrap()),
            characteristics: u32::from_le_bytes(record[36..40].try_into().unwrap()),
        });
    }

    Ok(ParsedPe {
        machine,
        bitness,
        image_base,
        entry_point_rva,
        sections,
    })
}

fn file_offset_to_rva(offset: usize, sections: &[PeSection]) -> Option<u32> {
    sections.iter().find_map(|section| {
        let start = section.raw_offset as usize;
        let end = start.checked_add(section.raw_size as usize)?;
        (start..end).contains(&offset).then(|| {
            section.virtual_address
                + u32::try_from(offset - start).expect("PE section delta fits u32")
        })
    })
}

fn rva_to_file_offset(rva: u32, sections: &[PeSection]) -> Option<usize> {
    sections.iter().find_map(|section| {
        let start = section.virtual_address;
        let span = section.virtual_size.max(section.raw_size);
        let end = start.checked_add(span)?;
        (start..end)
            .contains(&rva)
            .then(|| section.raw_offset as usize + (rva - section.virtual_address) as usize)
    })
}

fn bytes_to_hex(bytes: &[u8]) -> String {
    bytes
        .iter()
        .map(|byte| format!("{byte:02X}"))
        .collect::<Vec<_>>()
        .join(" ")
}

fn read_u16(data: &[u8], offset: usize) -> Option<u16> {
    Some(u16::from_le_bytes(
        data.get(offset..offset + 2)?.try_into().ok()?,
    ))
}

fn read_u32(data: &[u8], offset: usize) -> Option<u32> {
    Some(u32::from_le_bytes(
        data.get(offset..offset + 4)?.try_into().ok()?,
    ))
}

fn read_u64(data: &[u8], offset: usize) -> Option<u64> {
    Some(u64::from_le_bytes(
        data.get(offset..offset + 8)?.try_into().ok()?,
    ))
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn finds_strided_width_profile_and_extracts_new_entries() {
        let stride = 12;
        let value_start = 7;
        let mut bytes = vec![0xCC; value_start + 0x254 * stride + 4];
        for index in 0..0x254 {
            bytes[value_start + index * stride..value_start + index * stride + 4]
                .copy_from_slice(&0u32.to_le_bytes());
        }
        for (index, width) in PB11_PLUS_OPERAND_WORDS.iter().enumerate() {
            bytes[value_start + index * stride..value_start + index * stride + 4]
                .copy_from_slice(&u32::from(*width).to_le_bytes());
        }
        bytes[value_start + 0x251 * stride..value_start + 0x251 * stride + 4]
            .copy_from_slice(&2u32.to_le_bytes());
        bytes[value_start + 0x253 * stride..value_start + 0x253 * stride + 4]
            .copy_from_slice(&4u32.to_le_bytes());

        let pe = ParsedPe {
            machine: 0x014c,
            bitness: 32,
            image_base: 0x1000_0000,
            entry_point_rva: 0,
            sections: Vec::new(),
        };
        let candidates = find_u32_width_tables(&bytes, &pe);
        let candidate = candidates
            .iter()
            .find(|candidate| {
                candidate.value_file_offset == value_start && candidate.stride == stride
            })
            .unwrap();
        assert_eq!(candidate.matched_reference_entries, 0x247);
        assert_eq!(candidate.opcode_0251_words, Some(2));
        assert_eq!(candidate.opcode_0253_words, Some(4));
    }
}
