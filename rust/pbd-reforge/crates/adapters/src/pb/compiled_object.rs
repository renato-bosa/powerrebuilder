//! Structural parser for the PB 2022 `0x0152` and `0x0153` compiled-object envelopes.
//!
//! The layout follows the cursor order used by Hucxy/PbdViewer's `PbEntry`
//! parser. Alongside validated P-code boundaries, it retains the type, symbol,
//! enum, function-definition, and referenced-function records required by the
//! conservative semantic preview.

use serde::Serialize;
use thiserror::Error;

const PB2022_OBJECT_VERSION_MIN: u16 = 0x0152;
const PB2022_OBJECT_VERSION_MAX: u16 = 0x0153;

pub(super) fn is_supported_compiled_object_version(version: u16) -> bool {
    (PB2022_OBJECT_VERSION_MIN..=PB2022_OBJECT_VERSION_MAX).contains(&version)
}

#[derive(Debug, Clone, PartialEq, Eq)]
pub struct CompiledObjectLayout {
    pub version: u16,
    pub flags: u16,
    pub entry_type: u32,
    pub types: Vec<CompiledType>,
    pub enum_values: Vec<CompiledEnumValue>,
    pub global_variables: Vec<CompiledVariable>,
    pub object_definitions: Vec<CompiledObjectDefinition>,
    pub functions: Vec<CompiledFunctionRegion>,
}

#[derive(Debug, Clone, PartialEq, Eq, Serialize)]
pub struct CompiledObjectDefinition {
    pub index: u16,
    pub type_ref: u16,
    pub type_name: String,
    pub inherit_type_ref: u16,
    pub inherit_type_name: String,
    pub parent_type_ref: u16,
    pub parent_type_name: String,
    pub all_variable_count: u16,
    pub properties: Vec<CompiledVariable>,
}

#[derive(Debug, Clone, PartialEq, Eq, Serialize)]
pub struct CompiledEnumValue {
    pub enum_type_ref: u16,
    pub enum_type_name: String,
    pub item_index: u16,
    pub name: String,
}

#[derive(Debug, Clone, PartialEq, Eq)]
pub struct CompiledFunctionRegion {
    pub object_index: u16,
    pub function_index: u16,
    pub pcode_offset: usize,
    pub pcode_length: usize,
    pub debug_offset: usize,
    pub debug_length: usize,
    pub stack_buffer_offset: usize,
    pub stack_buffer: Vec<u8>,
    pub variables: Vec<CompiledVariable>,
    pub referenced_functions: Vec<CompiledReferencedFunction>,
    pub definition: Option<CompiledFunctionDefinition>,
}

#[derive(Debug, Clone, PartialEq, Eq, Serialize)]
pub struct CompiledType {
    pub index: u16,
    pub type_ref: u16,
    pub name: String,
    pub is_referenced_object: bool,
}

#[derive(Debug, Clone, PartialEq, Eq, Serialize)]
pub struct CompiledVariable {
    pub index: u16,
    pub name: String,
    pub type_ref: u16,
    pub type_name: String,
    pub array: String,
    pub flags: u8,
    pub is_shared: bool,
    pub is_referenced_global: bool,
    pub is_instance: bool,
    pub is_indirect: bool,
    pub is_constant: bool,
    pub value_or_global_index: u32,
}

#[derive(Debug, Clone, PartialEq, Eq, Serialize)]
pub struct CompiledFunctionDefinition {
    pub index: u16,
    pub name: String,
    pub return_type_ref: u16,
    pub return_type_name: String,
    pub flags: u8,
    pub global_index: u16,
    pub reference_index: u16,
    pub event_code: u16,
    pub parameters: Vec<CompiledFunctionParameter>,
    pub library: Option<String>,
    pub alias: Option<String>,
}

#[derive(Debug, Clone, PartialEq, Eq, Serialize)]
pub struct CompiledFunctionParameter {
    pub index: u8,
    pub name: String,
    pub type_ref: u16,
    pub type_name: String,
    pub array: String,
    pub is_read_only: bool,
    pub is_reference: bool,
}

#[derive(Debug, Clone, PartialEq, Eq, Serialize)]
pub struct CompiledReferencedFunction {
    pub index: u16,
    pub name: String,
    pub global_index: u16,
    pub is_global_function: bool,
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
    if !is_supported_compiled_object_version(version) {
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

    let _global_value_buffer = cursor.read_struct_buffer()?;
    let mut global_variables = cursor.read_variable_table(&[])?;

    let object_count = cursor.read_u16()? as usize;
    let base_object_count = cursor.read_u16()? as usize;
    let function_buffer = cursor.read_struct_buffer()?;
    let parameter_buffer = cursor.read_struct_buffer()?;
    let types = cursor.read_type_table()?;
    resolve_variable_types(&mut global_variables, &types);
    let enum_values = cursor
        .read_variable_table(&types)?
        .into_iter()
        .map(compiled_enum_value)
        .collect();

    let mut object_descriptors = Vec::with_capacity(object_count);
    for _ in 0..object_count {
        object_descriptors.push(cursor.read_fixed::<16>()?);
    }

    let mut base_descriptors = Vec::with_capacity(base_object_count);
    for _ in 0..base_object_count {
        base_descriptors.push(cursor.read_fixed::<32>()?);
    }

    let mut next_base_descriptor = 0;
    let mut object_definitions = Vec::with_capacity(base_object_count);
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
                object_definitions.push(cursor.read_object(
                    object_index as u16,
                    descriptor,
                    base,
                    &function_buffer,
                    &parameter_buffer,
                    &types,
                    &mut functions,
                )?);
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
        types,
        enum_values,
        global_variables,
        object_definitions,
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

    fn read_struct_buffer(&mut self) -> Result<Vec<u8>, CompiledObjectError> {
        let data_length = self.read_u32()? as usize;
        let auxiliary_length = self.read_u32()? as usize;
        data_length.checked_add(auxiliary_length).ok_or_else(|| {
            CompiledObjectError::InvalidField {
                offset: self.position.saturating_sub(8),
                message: "structured-buffer length overflow".to_string(),
            }
        })?;
        let data = self.take(data_length)?.to_vec();
        self.skip(auxiliary_length)?;
        Ok(data)
    }

    fn read_variable_table(
        &mut self,
        types: &[CompiledType],
    ) -> Result<Vec<CompiledVariable>, CompiledObjectError> {
        self.skip(6)?;
        let string_buffer = self.read_struct_buffer()?;
        let byte_length_offset = self.position;
        let byte_length = self.read_u16()? as usize;
        if byte_length % 20 != 0 {
            return Err(CompiledObjectError::InvalidField {
                offset: byte_length_offset,
                message: format!("variable-table byte length {byte_length} is not divisible by 20"),
            });
        }
        let mut variables = Vec::with_capacity(byte_length / 20);
        for index in 0..byte_length / 20 {
            let record_offset = self.position;
            let record = self.read_fixed::<20>()?;
            variables.push(parse_variable_record(
                index as u16,
                &record,
                &string_buffer,
                types,
                record_offset,
            )?);
        }
        Ok(variables)
    }

    fn read_type_table(&mut self) -> Result<Vec<CompiledType>, CompiledObjectError> {
        self.skip(6)?;
        let string_buffer = self.read_struct_buffer()?;
        let byte_length_offset = self.position;
        let byte_length = self.read_u16()? as usize;
        if byte_length % 20 != 0 {
            return Err(CompiledObjectError::InvalidField {
                offset: byte_length_offset,
                message: format!("type-table byte length {byte_length} is not divisible by 20"),
            });
        }
        let mut types = Vec::with_capacity(byte_length / 20);
        for index in 0..byte_length / 20 {
            let record_offset = self.position;
            let record = self.read_fixed::<20>()?;
            let name_offset = read_u32_at(&record, 8);
            let name = read_utf16le_string(&string_buffer, name_offset).ok_or_else(|| {
                CompiledObjectError::InvalidField {
                    offset: record_offset + 8,
                    message: format!("invalid type-name offset 0x{name_offset:08X}"),
                }
            })?;
            types.push(CompiledType {
                index: index as u16,
                type_ref: 0x8000 | index as u16,
                name,
                is_referenced_object: record[16] == 0x40,
            });
        }
        Ok(types)
    }

    fn read_object(
        &mut self,
        object_index: u16,
        object_descriptor: &[u8; 16],
        base_descriptor: &[u8; 32],
        function_buffer: &[u8],
        parameter_buffer: &[u8],
        types: &[CompiledType],
        functions: &mut Vec<CompiledFunctionRegion>,
    ) -> Result<CompiledObjectDefinition, CompiledObjectError> {
        let first_function = functions.len();
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
            let variables = self.read_variable_table(types)?;
            let stack_buffer_offset =
                self.position
                    .checked_add(8)
                    .ok_or_else(|| CompiledObjectError::InvalidField {
                        offset: self.position,
                        message: "stack-buffer offset overflow".to_string(),
                    })?;
            let stack_buffer = self.read_struct_buffer()?;

            functions.push(CompiledFunctionRegion {
                object_index,
                function_index,
                pcode_offset,
                pcode_length,
                debug_offset,
                debug_length,
                stack_buffer_offset,
                stack_buffer,
                variables,
                referenced_functions: Vec::new(),
                definition: None,
            });
        }

        self.skip_product(read_u16_at(base_descriptor, 24) as usize, 6)?;
        self.skip_product(read_u16_at(base_descriptor, 22) as usize, 4)?;
        let referenced_functions = self.read_referenced_functions()?;
        let properties = self.read_variable_table(types)?;
        self.skip_product(read_u16_at(base_descriptor, 28) as usize, 8)?;
        self.skip_product(read_u16_at(base_descriptor, 26) as usize, 16)?;
        let definition_count = read_u16_at(base_descriptor, 4) as usize;
        let mut definitions = Vec::with_capacity(definition_count);
        for definition_index in 0..definition_count {
            let record_offset = self.position;
            let record = self.read_fixed::<48>()?;
            definitions.push(parse_function_definition(
                definition_index as u16,
                &record,
                function_buffer,
                parameter_buffer,
                types,
                record_offset,
            )?);
        }
        for function in &mut functions[first_function..] {
            function.definition = definitions.get(function.function_index as usize).cloned();
            function.referenced_functions = referenced_functions.clone();
        }
        let type_ref = read_u16_at(object_descriptor, 2);
        let inherit_type_ref = read_u16_at(base_descriptor, 0);
        let parent_type_ref = read_u16_at(base_descriptor, 2);
        Ok(CompiledObjectDefinition {
            index: object_index,
            type_ref,
            type_name: resolve_type_name(type_ref, types),
            inherit_type_ref,
            inherit_type_name: resolve_type_name(inherit_type_ref, types),
            parent_type_ref,
            parent_type_name: resolve_type_name(parent_type_ref, types),
            all_variable_count: read_u16_at(base_descriptor, 28),
            properties,
        })
    }

    fn read_referenced_functions(
        &mut self,
    ) -> Result<Vec<CompiledReferencedFunction>, CompiledObjectError> {
        self.skip(6)?;
        let string_buffer = self.read_struct_buffer()?;
        let byte_length_offset = self.position;
        let byte_length = self.read_u16()? as usize;
        if byte_length % 20 != 0 {
            return Err(CompiledObjectError::InvalidField {
                offset: byte_length_offset,
                message: format!(
                    "referenced-function byte length {byte_length} is not divisible by 20"
                ),
            });
        }
        let count = byte_length / 20;
        let mut functions = Vec::with_capacity(count);
        for index in 0..count {
            let record_offset = self.position;
            let record = self.read_fixed::<20>()?;
            functions.push(parse_referenced_function_record(
                index as u16,
                &record,
                &string_buffer,
                record_offset,
            )?);
        }
        Ok(functions)
    }
}

fn parse_referenced_function_record(
    index: u16,
    record: &[u8; 20],
    string_buffer: &[u8],
    record_offset: usize,
) -> Result<CompiledReferencedFunction, CompiledObjectError> {
    let name_offset = read_u32_at(record, 8);
    let name = read_utf16le_string(string_buffer, name_offset).ok_or_else(|| {
        CompiledObjectError::InvalidField {
            offset: record_offset + 8,
            message: format!("invalid referenced-function name offset 0x{name_offset:08X}"),
        }
    })?;
    Ok(CompiledReferencedFunction {
        index,
        name,
        global_index: read_u16_at(record, 12),
        is_global_function: record[16] == 2,
    })
}

fn parse_variable_record(
    index: u16,
    record: &[u8; 20],
    string_buffer: &[u8],
    types: &[CompiledType],
    record_offset: usize,
) -> Result<CompiledVariable, CompiledObjectError> {
    let name_offset = read_u32_at(record, 8);
    let name = read_utf16le_string(string_buffer, name_offset).ok_or_else(|| {
        CompiledObjectError::InvalidField {
            offset: record_offset + 8,
            message: format!("invalid variable-name offset 0x{name_offset:08X}"),
        }
    })?;
    let array_offset = read_u32_at(record, 4);
    let array = read_array_shape(string_buffer, array_offset).ok_or_else(|| {
        CompiledObjectError::InvalidField {
            offset: record_offset + 4,
            message: format!("invalid variable-array offset 0x{array_offset:08X}"),
        }
    })?;
    let type_ref = read_u16_at(record, 18);
    let flags = record[17];
    Ok(CompiledVariable {
        index,
        name,
        type_ref,
        type_name: resolve_type_name(type_ref, types),
        array,
        flags,
        is_shared: flags & 0x02 != 0,
        is_referenced_global: record[16] & 0x40 != 0,
        is_instance: record[0] & 0x0f <= 1,
        is_indirect: record[0] & 0x02 != 0,
        is_constant: record[0] & 0x04 != 0,
        value_or_global_index: read_u32_at(record, 12),
    })
}

fn compiled_enum_value(value: CompiledVariable) -> CompiledEnumValue {
    CompiledEnumValue {
        enum_type_ref: value.type_ref,
        enum_type_name: value.type_name,
        item_index: value.value_or_global_index as u16,
        name: value.name,
    }
}

fn parse_function_definition(
    index: u16,
    record: &[u8; 48],
    function_buffer: &[u8],
    parameter_buffer: &[u8],
    types: &[CompiledType],
    record_offset: usize,
) -> Result<CompiledFunctionDefinition, CompiledObjectError> {
    let name_offset = read_u32_at(record, 0);
    let mut name = read_utf16le_string(function_buffer, name_offset).ok_or_else(|| {
        CompiledObjectError::InvalidField {
            offset: record_offset,
            message: format!("invalid function-name offset 0x{name_offset:08X}"),
        }
    })?;
    if let Some(stripped) = name.strip_prefix('+') {
        name = stripped.to_string();
    }

    let parameter_offset = read_u32_at(record, 8);
    let parameter_count = record[30];
    let mut parameters = Vec::with_capacity(parameter_count as usize);
    if !is_missing_offset(parameter_offset) {
        let start = (parameter_offset & 0x7fff_ffff) as usize;
        for parameter_index in 0..parameter_count {
            let offset = start
                .checked_add(parameter_index as usize * 12)
                .ok_or_else(|| CompiledObjectError::InvalidField {
                    offset: record_offset + 8,
                    message: "parameter-table offset overflow".to_string(),
                })?;
            let parameter = parameter_buffer.get(offset..offset + 12).ok_or_else(|| {
                CompiledObjectError::InvalidField {
                    offset: record_offset + 8,
                    message: format!(
                        "parameter {parameter_index} at buffer offset 0x{offset:X} is out of bounds"
                    ),
                }
            })?;
            let parameter_name_offset = read_u32_at(parameter, 0);
            let parameter_name = read_utf16le_string(function_buffer, parameter_name_offset)
                .ok_or_else(|| CompiledObjectError::InvalidField {
                    offset: record_offset + 8,
                    message: format!("invalid parameter-name offset 0x{parameter_name_offset:08X}"),
                })?;
            let array_offset = read_u32_at(parameter, 4);
            let array = read_array_shape(function_buffer, array_offset).ok_or_else(|| {
                CompiledObjectError::InvalidField {
                    offset: record_offset + 8,
                    message: format!("invalid parameter-array offset 0x{array_offset:08X}"),
                }
            })?;
            let type_ref = read_u16_at(parameter, 8);
            parameters.push(CompiledFunctionParameter {
                index: parameter_index,
                name: parameter_name,
                type_ref,
                type_name: resolve_type_name(type_ref, types),
                array,
                is_read_only: parameter[10] & 0x04 != 0,
                is_reference: parameter[10] & 0x02 != 0,
            });
        }
    } else if parameter_count != 0 {
        return Err(CompiledObjectError::InvalidField {
            offset: record_offset + 8,
            message: format!(
                "function declares {parameter_count} parameters but has no parameter-table offset"
            ),
        });
    }

    let alias_offset = read_u32_at(record, 12);
    let library_offset = read_u32_at(record, 16);
    let (library, alias) = if is_missing_offset(alias_offset) {
        (None, None)
    } else {
        (
            read_utf16le_string(function_buffer, library_offset),
            read_utf16le_string(function_buffer, alias_offset),
        )
    };
    let return_type_ref = read_u16_at(record, 28);
    Ok(CompiledFunctionDefinition {
        index,
        name,
        return_type_ref,
        return_type_name: resolve_type_name(return_type_ref, types),
        flags: record[31],
        global_index: read_u16_at(record, 20),
        reference_index: read_u16_at(record, 22),
        event_code: read_u16_at(record, 32),
        parameters,
        library,
        alias,
    })
}

fn resolve_variable_types(variables: &mut [CompiledVariable], types: &[CompiledType]) {
    for variable in variables {
        variable.type_name = resolve_type_name(variable.type_ref, types);
    }
}

pub(super) fn resolve_type_name(type_ref: u16, types: &[CompiledType]) -> String {
    let builtin = match type_ref {
        0 => "",
        1 => "integer",
        2 => "long",
        3 => "real",
        4 => "double",
        5 => "decimal",
        6 => "string",
        7 => "boolean",
        8 => "any",
        9 => "uint",
        10 => "ulong",
        11 => "blob",
        12 => "date",
        13 => "time",
        14 => "datetime",
        15 => "cursor",
        16 => "procedure",
        18 => "char",
        19 => "objhandle",
        20 => "longlong",
        21 => "byte",
        _ => "",
    };
    if !builtin.is_empty() || type_ref == 0 {
        return builtin.to_string();
    }
    if type_ref & 0xf000 == 0x8000 {
        return types
            .iter()
            .find(|candidate| candidate.type_ref == type_ref)
            .map(|candidate| candidate.name.clone())
            .unwrap_or_else(|| format!("type_{type_ref:04X}"));
    }
    if type_ref & 0xf000 == 0x4000 {
        return format!("system_type_{type_ref:04X}");
    }
    format!("type_{type_ref:04X}")
}

fn read_utf16le_string(buffer: &[u8], offset: u32) -> Option<String> {
    let start = (offset & 0x7fff_ffff) as usize;
    if start > buffer.len() || start % 2 != 0 {
        return None;
    }
    let tail = buffer.get(start..)?;
    let mut words = Vec::new();
    for bytes in tail.chunks_exact(2) {
        let word = u16::from_le_bytes([bytes[0], bytes[1]]);
        if word == 0 {
            return String::from_utf16(&words).ok();
        }
        words.push(word);
    }
    None
}

fn read_array_shape(buffer: &[u8], offset: u32) -> Option<String> {
    if is_missing_offset(offset) {
        return Some(String::new());
    }
    let start = (offset & 0x7fff_ffff) as usize;
    let dimensions = *buffer.get(start)? as usize;
    let mut result = Vec::with_capacity(dimensions);
    for index in 0..dimensions {
        let dimension = start.checked_add(4 + index * 8)?;
        let lower = read_u32_at(buffer.get(dimension..dimension + 8)?, 0);
        let upper = read_u32_at(buffer.get(dimension..dimension + 8)?, 4);
        if lower == 1 {
            result.push(upper.to_string());
        } else if lower != upper || upper != 0 {
            result.push(format!("{lower} to {upper}"));
        } else {
            result.push(String::new());
        }
    }
    Some(format!("[{}]", result.join(",")))
}

fn is_missing_offset(offset: u32) -> bool {
    offset == 0x0000_ffff || offset == 0xffff_ffff
}

fn read_u16_at(data: &[u8], offset: usize) -> u16 {
    u16::from_le_bytes([data[offset], data[offset + 1]])
}

fn read_u32_at(data: &[u8], offset: usize) -> u32 {
    u32::from_le_bytes([
        data[offset],
        data[offset + 1],
        data[offset + 2],
        data[offset + 3],
    ])
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

    fn push_utf16z(data: &mut Vec<u8>, value: &str) -> u32 {
        let offset = data.len() as u32;
        for word in value.encode_utf16() {
            data.extend_from_slice(&word.to_le_bytes());
        }
        data.extend_from_slice(&0u16.to_le_bytes());
        offset
    }

    fn compiled_object_with_one_function_version(version: u16) -> Vec<u8> {
        let mut data = Vec::new();
        push_u16(&mut data, version);
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

    fn compiled_object_with_one_function() -> Vec<u8> {
        compiled_object_with_one_function_version(PB2022_OBJECT_VERSION_MAX)
    }

    #[test]
    fn locates_pcode_without_interpreting_it() {
        let data = compiled_object_with_one_function();
        let layout = parse_compiled_object(&data).unwrap();
        assert_eq!(layout.version, PB2022_OBJECT_VERSION_MAX);
        assert_eq!(layout.entry_type, 0x0001_407d);
        assert_eq!(layout.object_definitions.len(), 1);
        assert_eq!(layout.object_definitions[0].type_ref, 0x407d);
        assert_eq!(layout.object_definitions[0].all_variable_count, 0);
    }

    #[test]
    fn accepts_adjacent_pb2022_object_envelope_versions() {
        for version in PB2022_OBJECT_VERSION_MIN..=PB2022_OBJECT_VERSION_MAX {
            let data = compiled_object_with_one_function_version(version);
            let layout = parse_compiled_object(&data).unwrap();
            assert_eq!(layout.version, version);
            assert_eq!(layout.functions.len(), 1);
        }
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

    #[test]
    fn parses_variable_names_and_builtin_types() {
        let mut strings = Vec::new();
        let name_offset = push_utf16z(&mut strings, "li_result");
        let mut record = [0u8; 20];
        record[4..8].copy_from_slice(&0x0000_ffff_u32.to_le_bytes());
        record[8..12].copy_from_slice(&name_offset.to_le_bytes());
        record[18..20].copy_from_slice(&1u16.to_le_bytes());
        let variable = parse_variable_record(3, &record, &strings, &[], 100).unwrap();
        assert_eq!(variable.index, 3);
        assert_eq!(variable.name, "li_result");
        assert_eq!(variable.type_name, "integer");
        assert_eq!(variable.array, "");
    }

    #[test]
    fn parses_referenced_function_metadata() {
        let mut strings = Vec::new();
        let name_offset = push_utf16z(&mut strings, "gf_lookup");
        let mut record = [0u8; 20];
        record[8..12].copy_from_slice(&name_offset.to_le_bytes());
        record[12..14].copy_from_slice(&31u16.to_le_bytes());
        record[16] = 2;

        let function = parse_referenced_function_record(4, &record, &strings, 200).unwrap();

        assert_eq!(function.index, 4);
        assert_eq!(function.name, "gf_lookup");
        assert_eq!(function.global_index, 31);
        assert!(function.is_global_function);
    }

    #[test]
    fn retains_enum_type_item_index_and_name() {
        let mut strings = Vec::new();
        let name_offset = push_utf16z(&mut strings, "approved");
        let mut record = [0u8; 20];
        record[4..8].copy_from_slice(&0x0000_ffff_u32.to_le_bytes());
        record[8..12].copy_from_slice(&name_offset.to_le_bytes());
        record[12..16].copy_from_slice(&2u32.to_le_bytes());
        record[18..20].copy_from_slice(&0x8000u16.to_le_bytes());
        let types = [CompiledType {
            index: 0,
            type_ref: 0x8000,
            name: "e_status".to_string(),
            is_referenced_object: true,
        }];
        let variable = parse_variable_record(0, &record, &strings, &types, 100).unwrap();
        let value = compiled_enum_value(variable);

        assert_eq!(value.enum_type_ref, 0x8000);
        assert_eq!(value.enum_type_name, "e_status");
        assert_eq!(value.item_index, 2);
        assert_eq!(value.name, "approved");
    }

    #[test]
    fn parses_function_signature_and_parameter_metadata() {
        let mut function_strings = Vec::new();
        let function_name = push_utf16z(&mut function_strings, "of_status");
        let parameter_name = push_utf16z(&mut function_strings, "as_value");
        let mut parameter_buffer = [0u8; 12];
        parameter_buffer[0..4].copy_from_slice(&parameter_name.to_le_bytes());
        parameter_buffer[4..8].copy_from_slice(&0x0000_ffff_u32.to_le_bytes());
        parameter_buffer[8..10].copy_from_slice(&6u16.to_le_bytes());
        parameter_buffer[10] = 0x04;

        let mut record = [0u8; 48];
        record[0..4].copy_from_slice(&function_name.to_le_bytes());
        record[8..12].copy_from_slice(&0u32.to_le_bytes());
        record[12..16].copy_from_slice(&0x0000_ffff_u32.to_le_bytes());
        record[28..30].copy_from_slice(&1u16.to_le_bytes());
        record[30] = 1;

        let definition =
            parse_function_definition(2, &record, &function_strings, &parameter_buffer, &[], 200)
                .unwrap();
        assert_eq!(definition.name, "of_status");
        assert_eq!(definition.return_type_name, "integer");
        assert_eq!(definition.parameters[0].name, "as_value");
        assert_eq!(definition.parameters[0].type_name, "string");
        assert!(definition.parameters[0].is_read_only);
    }
}
