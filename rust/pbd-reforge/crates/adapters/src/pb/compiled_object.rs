//! Structural parser for the `0x0153` compiled-object envelope.
//!
//! The layout follows the cursor order used by Hucxy/PbdViewer's `PbEntry`
//! parser. Only offsets and lengths required to isolate P-code are retained;
//! semantic interpretation of types, symbols, and function definitions remains
//! out of scope here.

use thiserror::Error;

const PB2022_OBJECT_VERSION: u16 = 0x0153;

#[derive(Debug, Clone, PartialEq, Eq)]
pub struct CompiledObjectLayout {
    pub version: u16,
    pub flags: u16,
    pub entry_type: u32,
    pub functions: Vec<CompiledFunctionRegion>,
}

#[derive(Debug, Clone, PartialEq, Eq)]
pub struct CompiledFunctionRegion {
    pub object_index: u16,
    pub function_index: u16,
    pub pcode_offset: usize,
    pub pcode_length: usize,
    pub debug_offset: usize,
    pub debug_length: usize,
}

#[derive(Debug, Clone, PartialEq, Eq, Error)]
pub enum CompiledObjectError {
    #[error(
        "compiled object is too short at offset {offset}: need {needed} byte(s), have {remaining}"
    )]
    Truncated {
        offset: usize,
        needed: usize,
        remaining: usize,
    },

    #[error("unsupported compiled-object version 0x{version:04X}")]
    UnsupportedVersion { version: u16 },

    #[error("invalid compiled-object field at offset {offset}: {message}")]
    InvalidField { offset: usize, message: String },

    #[error("compiled-object parser stopped at {consumed} of {size} bytes")]
    TrailingData { consumed: usize, size: usize },
}

pub fn parse_compiled_object(data: &[u8]) -> Result<CompiledObjectLayout, CompiledObjectError> {
    let mut cursor = Cursor::new(data);
    let version = cursor.read_u16()?;
    if version != PB2022_OBJECT_VERSION {
        return Err(CompiledObjectError::UnsupportedVersion { version });
    }

    let flags = cursor.read_u16()?;
    let entry_type = cursor.read_u32()?;
    cursor.read_u32()?; // unknown header field
    cursor.read_u32()?; // modified timestamp (low word)

    // PB object version 0x014E (334) introduced 64-bit timestamp slots. The
    // PB 2022 R2 sample uses 0x0153 (339).
    if version >= 334 {
        cursor.read_u32()?;
    }
    cursor.read_u32()?; // compiled timestamp (low word)
    if version >= 334 {
        cursor.read_u32()?;
    }
    cursor.read_u32()?; // unknown header field

    let header_record_count = cursor.read_u16()? as usize;
    cursor.skip_product(header_record_count, 12)?;

    cursor.skip_struct_buffer()?; // global/shared variable names
    cursor.skip_variable_table()?;

    let object_count = cursor.read_u16()? as usize;
    let base_object_count = cursor.read_u16()? as usize;
    cursor.skip_struct_buffer()?; // function/symbol strings
    cursor.skip_struct_buffer()?; // parameter strings
    cursor.skip_type_table()?;
    cursor.skip_variable_table()?; // enum values

    let mut object_descriptors = Vec::with_capacity(object_count);
    for _ in 0..object_count {
        object_descriptors.push(cursor.read_fixed::<16>()?);
    }

    let mut base_descriptors = Vec::with_capacity(base_object_count);
    for _ in 0..base_object_count {
        base_descriptors.push(cursor.read_fixed::<32>()?);
    }

    let mut next_base_descriptor = 0;
    let mut functions = Vec::new();
    for (object_index, descriptor) in object_descriptors.iter().enumerate() {
        let descriptor_kind = (descriptor[0] >> 1) & 7;
        match descriptor_kind {
            0 => {
                let base = base_descriptors.get(next_base_descriptor).ok_or_else(|| {
                    CompiledObjectError::InvalidField {
                        offset: cursor.position(),
                        message: "object descriptor requires a missing 32-byte base descriptor"
                            .to_string(),
                    }
                })?;
                next_base_descriptor += 1;
                cursor.read_object(object_index as u16, base, &mut functions)?;
            }
            1 => {
                let extra_record_count =
                    u16::from_le_bytes([descriptor[4], descriptor[5]]) as usize;
                cursor.skip_product(extra_record_count, 8)?;
            }
            6 => {}
            _ => {}
        }
    }

    if next_base_descriptor != base_descriptors.len() {
        return Err(CompiledObjectError::InvalidField {
            offset: cursor.position(),
            message: format!(
                "used {next_base_descriptor} of {} base descriptors",
                base_descriptors.len()
            ),
        });
    }
    if cursor.position() != data.len() {
        return Err(CompiledObjectError::TrailingData {
            consumed: cursor.position(),
            size: data.len(),
        });
    }

    Ok(CompiledObjectLayout {
        version,
        flags,
        entry_type,
        functions,
    })
}

struct Cursor<'a> {
    data: &'a [u8],
    position: usize,
}

impl<'a> Cursor<'a> {
    fn new(data: &'a [u8]) -> Self {
        Self { data, position: 0 }
    }

    fn position(&self) -> usize {
        self.position
    }

    fn read_u16(&mut self) -> Result<u16, CompiledObjectError> {
        let bytes = self.read_fixed::<2>()?;
        Ok(u16::from_le_bytes(bytes))
    }

    fn read_u32(&mut self) -> Result<u32, CompiledObjectError> {
        let bytes = self.read_fixed::<4>()?;
        Ok(u32::from_le_bytes(bytes))
    }

    fn read_fixed<const SIZE: usize>(&mut self) -> Result<[u8; SIZE], CompiledObjectError> {
        let bytes = self.take(SIZE)?;
        let mut result = [0; SIZE];
        result.copy_from_slice(bytes);
        Ok(result)
    }

    fn take(&mut self, length: usize) -> Result<&'a [u8], CompiledObjectError> {
        let end =
            self.position
                .checked_add(length)
                .ok_or_else(|| CompiledObjectError::InvalidField {
                    offset: self.position,
                    message: "offset overflow".to_string(),
                })?;
        let bytes =
            self.data
                .get(self.position..end)
                .ok_or_else(|| CompiledObjectError::Truncated {
                    offset: self.position,
                    needed: length,
                    remaining: self.data.len().saturating_sub(self.position),
                })?;
        self.position = end;
        Ok(bytes)
    }

    fn skip(&mut self, length: usize) -> Result<(), CompiledObjectError> {
        self.take(length).map(|_| ())
    }

    fn skip_product(&mut self, count: usize, item_size: usize) -> Result<(), CompiledObjectError> {
        let length =
            count
                .checked_mul(item_size)
                .ok_or_else(|| CompiledObjectError::InvalidField {
                    offset: self.position,
                    message: "record-table length overflow".to_string(),
                })?;
        self.skip(length)
    }

    fn skip_struct_buffer(&mut self) -> Result<(), CompiledObjectError> {
        let data_length = self.read_u32()? as usize;
        let auxiliary_length = self.read_u32()? as usize;
        let total = data_length.checked_add(auxiliary_length).ok_or_else(|| {
            CompiledObjectError::InvalidField {
                offset: self.position.saturating_sub(8),
                message: "structured-buffer length overflow".to_string(),
            }
        })?;
        self.skip(total)
    }

    fn skip_variable_table(&mut self) -> Result<(), CompiledObjectError> {
        self.skip(6)?;
        self.skip_struct_buffer()?;
        let byte_length_offset = self.position;
        let byte_length = self.read_u16()? as usize;
        if byte_length % 20 != 0 {
            return Err(CompiledObjectError::InvalidField {
                offset: byte_length_offset,
                message: format!("variable-table byte length {byte_length} is not divisible by 20"),
            });
        }
        self.skip(byte_length)
    }

    fn skip_type_table(&mut self) -> Result<(), CompiledObjectError> {
        self.skip(6)?;
        self.skip_struct_buffer()?;
        let byte_length_offset = self.position;
        let byte_length = self.read_u16()? as usize;
        if byte_length % 20 != 0 {
            return Err(CompiledObjectError::InvalidField {
                offset: byte_length_offset,
                message: format!("type-table byte length {byte_length} is not divisible by 20"),
            });
        }
        self.skip(byte_length)
    }

    fn read_object(
        &mut self,
        object_index: u16,
        base_descriptor: &[u8; 32],
        functions: &mut Vec<CompiledFunctionRegion>,
    ) -> Result<(), CompiledObjectError> {
        let function_count = self.read_u16()? as usize;
        let mut function_indices = Vec::with_capacity(function_count);
        for _ in 0..function_count {
            let index_record = self.read_fixed::<4>()?;
            function_indices.push(u16::from_le_bytes([index_record[2], index_record[3]]));
        }

        for function_index in function_indices {
            let pcode_length = self.read_u16()? as usize;
            let debug_record_count = self.read_u16()? as usize;
            self.read_u16()?; // unknown function field

            if pcode_length % 2 != 0 {
                return Err(CompiledObjectError::InvalidField {
                    offset: self.position.saturating_sub(6),
                    message: format!("P-code length {pcode_length} is not word-aligned"),
                });
            }
            let pcode_offset = self.position;
            self.skip(pcode_length)?;
            let debug_offset = self.position;
            let debug_length = debug_record_count.checked_mul(4).ok_or_else(|| {
                CompiledObjectError::InvalidField {
                    offset: debug_offset,
                    message: "debug-table length overflow".to_string(),
                }
            })?;
            self.skip(debug_length)?;
            self.skip_variable_table()?;
            self.skip_struct_buffer()?;

            functions.push(CompiledFunctionRegion {
                object_index,
                function_index,
                pcode_offset,
                pcode_length,
                debug_offset,
                debug_length,
            });
        }

        self.skip_product(read_u16_at(base_descriptor, 24) as usize, 6)?;
        self.skip_product(read_u16_at(base_descriptor, 22) as usize, 4)?;
        self.skip_variable_table()?; // referenced functions/events
        self.skip_variable_table()?; // properties/controls
        self.skip_product(read_u16_at(base_descriptor, 28) as usize, 8)?;
        self.skip_product(read_u16_at(base_descriptor, 26) as usize, 16)?;
        self.skip_product(read_u16_at(base_descriptor, 4) as usize, 48)?;
        Ok(())
    }
}

fn read_u16_at(data: &[u8], offset: usize) -> u16 {
    u16::from_le_bytes([data[offset], data[offset + 1]])
}

#[cfg(test)]
mod tests {
    use super::*;

    fn push_u16(data: &mut Vec<u8>, value: u16) {
        data.extend_from_slice(&value.to_le_bytes());
    }

    fn push_u32(data: &mut Vec<u8>, value: u32) {
        data.extend_from_slice(&value.to_le_bytes());
    }

    fn push_empty_struct_buffer(data: &mut Vec<u8>) {
        push_u32(data, 0);
        push_u32(data, 0);
    }

    fn push_empty_variable_table(data: &mut Vec<u8>) {
        data.extend_from_slice(&[0; 6]);
        push_empty_struct_buffer(data);
        push_u16(data, 0);
    }

    fn compiled_object_with_one_function() -> Vec<u8> {
        let mut data = Vec::new();
        push_u16(&mut data, PB2022_OBJECT_VERSION);
        push_u16(&mut data, 3);
        push_u32(&mut data, 0x0001_407d);
        push_u32(&mut data, 16);
        push_u32(&mut data, 1);
        push_u32(&mut data, 0);
        push_u32(&mut data, 2);
        push_u32(&mut data, 0);
        push_u32(&mut data, 0);
        push_u16(&mut data, 0);
        push_empty_struct_buffer(&mut data);
        push_empty_variable_table(&mut data);
        push_u16(&mut data, 1);
        push_u16(&mut data, 1);
        push_empty_struct_buffer(&mut data);
        push_empty_struct_buffer(&mut data);
        push_empty_variable_table(&mut data);
        push_empty_variable_table(&mut data);

        let mut object_descriptor = [0u8; 16];
        object_descriptor[2..4].copy_from_slice(&0x407d_u16.to_le_bytes());
        data.extend_from_slice(&object_descriptor);
        let base_descriptor = [0u8; 32];
        data.extend_from_slice(&base_descriptor);

        push_u16(&mut data, 1);
        data.extend_from_slice(&[0, 0]);
        push_u16(&mut data, 7);
        push_u16(&mut data, 4);
        push_u16(&mut data, 0);
        push_u16(&mut data, 0);
        let expected_offset = data.len();
        data.extend_from_slice(&[0x00, 0x00, 0x32, 0x00]);
        push_empty_variable_table(&mut data);
        push_empty_struct_buffer(&mut data);
        push_empty_variable_table(&mut data);
        push_empty_variable_table(&mut data);

        let layout = parse_compiled_object(&data).unwrap();
        assert_eq!(layout.functions.len(), 1);
        assert_eq!(layout.functions[0].function_index, 7);
        assert_eq!(layout.functions[0].pcode_offset, expected_offset);
        assert_eq!(layout.functions[0].pcode_length, 4);
        data
    }

    #[test]
    fn locates_pcode_without_interpreting_it() {
        let data = compiled_object_with_one_function();
        let layout = parse_compiled_object(&data).unwrap();
        assert_eq!(layout.version, PB2022_OBJECT_VERSION);
        assert_eq!(layout.entry_type, 0x0001_407d);
    }

    #[test]
    fn reports_truncated_object() {
        let mut data = compiled_object_with_one_function();
        data.pop();
        assert!(matches!(
            parse_compiled_object(&data),
            Err(CompiledObjectError::Truncated { .. })
        ));
    }
}
