//! Conservative PowerScript-like previews for structurally validated functions.
//!
//! This is intentionally a small semantic slice. Unsupported instructions are
//! preserved as comments, and `semantically_complete` is only true when every
//! instruction was handled without inventing stack values.

use serde::Serialize;

use super::compiled_object::{
    resolve_type_name, CompiledEnumValue, CompiledFunctionDefinition, CompiledFunctionParameter,
    CompiledReferencedFunction, CompiledType, CompiledVariable,
};
use super::pcode_scanner::{PCodeInstruction, PCodeScan};

#[derive(Debug, Clone, PartialEq, Serialize)]
pub struct SemanticPreview {
    pub signature: String,
    pub declarations: Vec<String>,
    pub statements: Vec<PreviewStatement>,
    pub instruction_count: usize,
    pub supported_instruction_count: usize,
    pub semantic_coverage_percent: f64,
    pub semantically_complete: bool,
    pub unresolved: Vec<UnresolvedSemantic>,
    pub powerscript_like: String,
}

#[derive(Debug, Clone, PartialEq, Eq, Serialize)]
pub struct PreviewStatement {
    pub offset: usize,
    pub text: String,
}

#[derive(Debug, Clone, PartialEq, Eq, Serialize)]
pub struct UnresolvedSemantic {
    pub offset: usize,
    pub opcode: u16,
    pub mnemonic: &'static str,
    pub reason: String,
}

#[derive(Debug, Clone)]
struct Expression {
    text: String,
    precedence: u8,
    type_name: Option<String>,
}

pub fn build_semantic_preview(
    definition: &CompiledFunctionDefinition,
    variables: &[CompiledVariable],
    global_variables: &[CompiledVariable],
    types: &[CompiledType],
    enum_values: &[CompiledEnumValue],
    referenced_functions: &[CompiledReferencedFunction],
    stack_buffer: &[u8],
    scan: &PCodeScan,
) -> SemanticPreview {
    let signature = format_signature(definition);
    let declarations = variables
        .iter()
        .skip(definition.parameters.len())
        .map(format_variable)
        .collect::<Vec<_>>();
    let mut stack = Vec::<Expression>::new();
    let mut statements = Vec::new();
    let mut unresolved = Vec::new();
    let mut supported = 0usize;

    for instruction in &scan.instructions {
        let outcome = apply_instruction(
            instruction,
            variables,
            global_variables,
            types,
            enum_values,
            referenced_functions,
            stack_buffer,
            &mut stack,
            &mut statements,
        );
        match outcome {
            Ok(()) => supported += 1,
            Err(reason) => {
                unresolved.push(UnresolvedSemantic {
                    offset: instruction.offset,
                    opcode: instruction.opcode,
                    mnemonic: instruction.mnemonic,
                    reason: reason.clone(),
                });
                statements.push(PreviewStatement {
                    offset: instruction.offset,
                    text: format!(
                        "/* unresolved {} {} */",
                        instruction.mnemonic,
                        format_operands(&instruction.operands_u16_le)
                    )
                    .trim_end()
                    .to_string(),
                });
                stack.clear();
            }
        }
    }

    let semantic_coverage_percent = if scan.instruction_count == 0 {
        100.0
    } else {
        supported as f64 * 100.0 / scan.instruction_count as f64
    };
    let semantically_complete = scan.complete && unresolved.is_empty() && stack.is_empty();
    let powerscript_like = render_preview(&signature, &declarations, &statements);

    SemanticPreview {
        signature,
        declarations,
        statements,
        instruction_count: scan.instruction_count,
        supported_instruction_count: supported,
        semantic_coverage_percent,
        semantically_complete,
        unresolved,
        powerscript_like,
    }
}

fn apply_instruction(
    instruction: &PCodeInstruction,
    variables: &[CompiledVariable],
    global_variables: &[CompiledVariable],
    types: &[CompiledType],
    enum_values: &[CompiledEnumValue],
    referenced_functions: &[CompiledReferencedFunction],
    stack_buffer: &[u8],
    stack: &mut Vec<Expression>,
    statements: &mut Vec<PreviewStatement>,
) -> Result<(), String> {
    match instruction.opcode {
        0x0000 => {
            if !statements
                .last()
                .is_some_and(|statement| statement.text.starts_with("return"))
            {
                statements.push(PreviewStatement {
                    offset: instruction.offset,
                    text: "return".to_string(),
                });
            }
        }
        0x0001 => {
            let returns_value = instruction.operands_u16_le.first().copied().unwrap_or(0) == 1;
            let text = if returns_value {
                format!(
                    "return {}",
                    stack
                        .pop()
                        .ok_or_else(|| "return-value stack is empty".to_string())?
                        .text
                )
            } else {
                "return".to_string()
            };
            statements.push(PreviewStatement {
                offset: instruction.offset,
                text,
            });
        }
        0x0002 | 0x0003 => {
            let target = first_operand(instruction)?;
            let condition = stack
                .pop()
                .ok_or_else(|| "conditional-jump stack is empty".to_string())?;
            let negation = if instruction.opcode == 0x0003 {
                "not "
            } else {
                ""
            };
            statements.push(PreviewStatement {
                offset: instruction.offset,
                text: format!("if {negation}{} then goto L_{target:04X}", condition.text),
            });
        }
        0x0004 => {
            let target = first_operand(instruction)?;
            let follows_return = statements
                .last()
                .is_some_and(|statement| statement.text.starts_with("return"));
            if !follows_return {
                statements.push(PreviewStatement {
                    offset: instruction.offset,
                    text: format!("goto L_{target:04X}"),
                });
            }
        }
        0x001e | 0x0030 | 0x0120 | 0x01a7 | 0x01a9 => {
            let index = first_operand(instruction)? as usize;
            let variable = variables
                .get(index)
                .ok_or_else(|| format!("local-variable index {index} is out of bounds"))?;
            stack.push(Expression {
                text: variable.name.clone(),
                precedence: 0,
                type_name: Some(variable.type_name.clone()),
            });
        }
        0x002f => {
            let index = first_operand(instruction)? as usize;
            let variable = variables
                .iter()
                .find(|variable| {
                    variable.is_referenced_global && variable.value_or_global_index == index as u32
                })
                .or_else(|| global_variables.get(index))
                .ok_or_else(|| format!("shared-variable index {index} is out of bounds"))?;
            stack.push(Expression {
                text: variable.name.clone(),
                precedence: 0,
                type_name: Some(variable.type_name.clone()),
            });
        }
        0x0021 => stack.push(Expression {
            text: "this".to_string(),
            precedence: 0,
            type_name: None,
        }),
        0x0022 => stack.push(Expression {
            text: "parent".to_string(),
            precedence: 0,
            type_name: None,
        }),
        0x0020 => {
            let offset = read_u32_operands(instruction)?;
            let descriptor = read_member_descriptor(stack_buffer, offset)
                .ok_or_else(|| format!("invalid member descriptor at 0x{offset:08X}"))?;
            let receiver_type = stack
                .last()
                .and_then(|receiver| receiver.type_name.as_deref());
            let catalog_member = receiver_type.and_then(|receiver_type| {
                pb2022_external_member(receiver_type, descriptor.member_index)
            });
            let direct_name = (descriptor.name_offset & 0xffff != 0xffff)
                .then(|| read_identifier(stack_buffer, descriptor.name_offset))
                .flatten();
            if let (Some(direct_name), Some((catalog_name, _))) =
                (direct_name.as_deref(), catalog_member)
            {
                if !direct_name.eq_ignore_ascii_case(catalog_name) {
                    return Err(format!(
                        "member descriptor name {direct_name} does not match catalog name {catalog_name}"
                    ));
                }
            }
            let name = direct_name
                .or_else(|| catalog_member.map(|(name, _)| name.to_string()))
                .ok_or_else(|| {
                    let receiver = receiver_type.unwrap_or("unknown type");
                    format!(
                        "member name is external for {receiver} index {}",
                        descriptor.member_index
                    )
                })?;
            stack.push(Expression {
                text: name,
                precedence: 0,
                type_name: catalog_member.map(|(_, type_name)| type_name.to_string()),
            });
        }
        0x0027 | 0x0122 => apply_member_access(stack)?,
        0x002c | 0x0171 => apply_function_call(instruction, stack_buffer, stack)?,
        0x0013 => apply_call_super(instruction, stack_buffer, stack)?,
        0x01bc => push_function_class(instruction, referenced_functions, stack)?,
        0x01bd => apply_global_function_call(instruction, stack)?,
        0x0011 => {
            let value = stack
                .pop()
                .ok_or_else(|| "destroy target is missing".to_string())?;
            statements.push(PreviewStatement {
                offset: instruction.offset,
                text: format!("destroy({})", value.text),
            });
        }
        0x016d => {
            let offset = read_u32_operands(instruction)?;
            let descriptor = read_type_descriptor(stack_buffer, offset)
                .ok_or_else(|| format!("invalid type descriptor at 0x{offset:08X}"))?;
            let resolved = resolve_type_name(descriptor.type_ref, types);
            if !resolved.starts_with("type_")
                && !resolved.starts_with("system_type_")
                && !resolved.eq_ignore_ascii_case(&descriptor.name)
            {
                return Err(format!(
                    "type descriptor name {} does not match {}",
                    descriptor.name, resolved
                ));
            }
            stack.push(Expression {
                text: format!("create {}", descriptor.name),
                precedence: 0,
                type_name: Some(descriptor.name),
            });
        }
        0x0014 => {
            let expression = stack
                .pop()
                .ok_or_else(|| "statement-expression stack is empty".to_string())?;
            statements.push(PreviewStatement {
                offset: instruction.offset,
                text: expression.text,
            });
        }
        0x011d => {
            let index = first_operand(instruction)? as usize;
            let variable = variables
                .get(index)
                .ok_or_else(|| format!("assignment-variable index {index} is out of bounds"))?;
            stack.push(Expression {
                text: variable.name.clone(),
                precedence: 0,
                type_name: Some(variable.type_name.clone()),
            });
        }
        0x0032 => stack.push(constant_expression(
            (first_operand(instruction)? as i16).to_string(),
        )),
        0x0033 => stack.push(constant_expression(first_operand(instruction)?.to_string())),
        0x0034 => {
            let value = read_u32_operands(instruction)? as i32;
            stack.push(constant_expression(value.to_string()));
        }
        0x0035 => stack.push(constant_expression(
            read_u32_operands(instruction)?.to_string(),
        )),
        0x003b => {
            let offset = read_u32_operands(instruction)?;
            let value = read_utf16le_string(stack_buffer, offset)
                .ok_or_else(|| format!("invalid string-buffer offset 0x{offset:08X}"))?;
            stack.push(constant_expression(format!(
                "\"{}\"",
                escape_string(&value)
            )));
        }
        0x003c => stack.push(constant_expression(
            (first_operand(instruction)? == 1).to_string(),
        )),
        0x003d => {
            let item_index = first_operand(instruction)?;
            let enum_type_ref = instruction
                .operands_u16_le
                .get(1)
                .copied()
                .ok_or_else(|| "enum constant has no enum type".to_string())?;
            let name = enum_values
                .iter()
                .find(|value| {
                    value.enum_type_ref == enum_type_ref && value.item_index == item_index
                })
                .map(|value| value.name.as_str())
                .or_else(|| pb2022_system_enum_name(enum_type_ref, item_index))
                .ok_or_else(|| {
                    format!("unknown enum constant 0x{enum_type_ref:04X}:{item_index}")
                })?;
            stack.push(constant_expression(format!("{name}!")));
        }
        0x0024 => apply_binary(stack, "and", 2)?,
        0x0025 => apply_binary(stack, "or", 2)?,
        0x0026 => apply_unary(stack, "not ")?,
        0x013b => {
            if stack.is_empty() {
                return Err("call cleanup has no call result on the stack".to_string());
            }
        }
        _ if instruction.mnemonic.starts_with("ASSIGN_") => {
            let value = stack
                .pop()
                .ok_or_else(|| format!("{} value is missing", instruction.mnemonic))?;
            let target = stack
                .pop()
                .ok_or_else(|| format!("{} target is missing", instruction.mnemonic))?;
            statements.push(PreviewStatement {
                offset: instruction.offset,
                text: format!("{} = {}", target.text, value.text),
            });
        }
        _ if is_transparent_conversion(instruction.mnemonic) => {
            if stack.is_empty() {
                return Err(format!(
                    "{} requires a value but the expression stack is empty",
                    instruction.mnemonic
                ));
            }
        }
        _ if binary_operator(instruction.mnemonic).is_some() => {
            let (operator, precedence) = binary_operator(instruction.mnemonic).unwrap();
            apply_binary(stack, operator, precedence)?;
        }
        _ if instruction.mnemonic.starts_with("NEGATE_") => apply_unary(stack, "-")?,
        _ if instruction.mnemonic == "ISVALID" => {
            let value = stack
                .pop()
                .ok_or_else(|| "isvalid stack is empty".to_string())?;
            stack.push(Expression {
                text: format!("isvalid({})", value.text),
                precedence: 0,
                type_name: Some("boolean".to_string()),
            });
        }
        _ => return Err("semantic rule not implemented".to_string()),
    }
    Ok(())
}

fn constant_expression(text: String) -> Expression {
    Expression {
        text,
        precedence: 0,
        type_name: None,
    }
}

fn apply_binary(stack: &mut Vec<Expression>, operator: &str, precedence: u8) -> Result<(), String> {
    let right = stack
        .pop()
        .ok_or_else(|| format!("{operator} right operand is missing"))?;
    let left = stack
        .pop()
        .ok_or_else(|| format!("{operator} left operand is missing"))?;
    let left_text = parenthesize(left, precedence);
    let right_text = parenthesize(right, precedence);
    stack.push(Expression {
        text: format!("{left_text} {operator} {right_text}"),
        precedence,
        type_name: None,
    });
    Ok(())
}

fn apply_unary(stack: &mut Vec<Expression>, operator: &str) -> Result<(), String> {
    let value = stack
        .pop()
        .ok_or_else(|| format!("{operator} operand is missing"))?;
    let text = if value.precedence == 0 {
        value.text
    } else {
        format!("({})", value.text)
    };
    stack.push(Expression {
        text: format!("{operator}{text}"),
        precedence: 6,
        type_name: None,
    });
    Ok(())
}

fn apply_member_access(stack: &mut Vec<Expression>) -> Result<(), String> {
    let member = stack
        .pop()
        .ok_or_else(|| "member name is missing".to_string())?;
    let receiver = stack
        .pop()
        .ok_or_else(|| "member receiver is missing".to_string())?;
    let type_name = member.type_name;
    stack.push(Expression {
        text: format!("{}.{}", receiver.text, member.text),
        precedence: 0,
        type_name,
    });
    Ok(())
}

fn apply_function_call(
    instruction: &PCodeInstruction,
    stack_buffer: &[u8],
    stack: &mut Vec<Expression>,
) -> Result<(), String> {
    let descriptor_offset = read_u32_operands(instruction)? as usize;
    let descriptor = stack_buffer
        .get(descriptor_offset..descriptor_offset.saturating_add(8))
        .ok_or_else(|| format!("invalid call descriptor offset 0x{descriptor_offset:08X}"))?;
    let name_offset =
        u32::from_le_bytes([descriptor[4], descriptor[5], descriptor[6], descriptor[7]]);
    let name = read_identifier(stack_buffer, name_offset)
        .ok_or_else(|| format!("invalid call-name offset 0x{name_offset:08X}"))?;
    let argument_count = instruction
        .operands_u16_le
        .get(2)
        .copied()
        .ok_or_else(|| "function call has no argument count".to_string())?
        as usize;
    if stack.len() < argument_count + 1 {
        return Err(format!(
            "function call requires a receiver and {argument_count} argument(s), but the stack has {} value(s)",
            stack.len()
        ));
    }
    let arguments_start = stack.len() - argument_count;
    let arguments = stack
        .drain(arguments_start..)
        .map(|argument| argument.text)
        .collect::<Vec<_>>();
    let receiver = stack
        .pop()
        .ok_or_else(|| "function-call receiver is missing".to_string())?;
    let flags = instruction.operands_u16_le.get(3).copied().unwrap_or(0);
    let name = qualify_call_name(name, flags);
    stack.push(Expression {
        text: format!("{}.{}({})", receiver.text, name, arguments.join(", ")),
        precedence: 0,
        type_name: None,
    });
    Ok(())
}

fn apply_call_super(
    instruction: &PCodeInstruction,
    stack_buffer: &[u8],
    stack: &mut Vec<Expression>,
) -> Result<(), String> {
    let argument_count = instruction
        .operands_u16_le
        .get(1)
        .copied()
        .ok_or_else(|| "super call has no argument count".to_string())?
        as usize;
    let name_offset = read_u32_operand_pair(instruction, 3)?;
    let name = read_identifier(stack_buffer, name_offset)
        .ok_or_else(|| format!("invalid super-call name offset 0x{name_offset:08X}"))?;
    if stack.len() < argument_count {
        return Err(format!(
            "super call requires {argument_count} argument(s), but the stack has {} value(s)",
            stack.len()
        ));
    }
    let arguments_start = stack.len() - argument_count;
    let arguments = stack
        .drain(arguments_start..)
        .map(|argument| argument.text)
        .collect::<Vec<_>>();
    let call = if arguments.is_empty() {
        format!("call super::{name}")
    } else {
        format!("call super::{name}({})", arguments.join(", "))
    };
    stack.push(Expression {
        text: call,
        precedence: 0,
        type_name: None,
    });
    Ok(())
}

fn push_function_class(
    instruction: &PCodeInstruction,
    referenced_functions: &[CompiledReferencedFunction],
    stack: &mut Vec<Expression>,
) -> Result<(), String> {
    let function_index = first_operand(instruction)? as usize;
    let object_index = instruction
        .operands_u16_le
        .get(1)
        .copied()
        .ok_or_else(|| "function-class reference has no object index".to_string())?;
    let name = if object_index & 0x8000 != 0 {
        referenced_functions
            .get(function_index)
            .map(|function| function.name.as_str())
            .ok_or_else(|| format!("referenced-function index {function_index} is out of bounds"))?
    } else if object_index & 0x4000 != 0 {
        pb2022_system_function_name(object_index, function_index as u16).ok_or_else(|| {
            format!(
                "unknown PB 2022 system-function reference 0x{object_index:04X}:{function_index}"
            )
        })?
    } else {
        return Err(format!(
            "unsupported function-class object index 0x{object_index:04X}"
        ));
    };
    stack.push(Expression {
        text: name.to_string(),
        precedence: 0,
        type_name: None,
    });
    Ok(())
}

fn apply_global_function_call(
    instruction: &PCodeInstruction,
    stack: &mut Vec<Expression>,
) -> Result<(), String> {
    let argument_count = instruction
        .operands_u16_le
        .get(1)
        .copied()
        .ok_or_else(|| "global function call has no argument count".to_string())?
        as usize;
    let flags = instruction
        .operands_u16_le
        .get(2)
        .copied()
        .ok_or_else(|| "global function call has no flags".to_string())?;
    let function = stack
        .pop()
        .ok_or_else(|| "global function name is missing".to_string())?;
    if stack.len() < argument_count {
        return Err(format!(
            "global function call requires {argument_count} argument(s), but the stack has {} value(s)",
            stack.len()
        ));
    }
    let arguments_start = stack.len() - argument_count;
    let arguments = stack
        .drain(arguments_start..)
        .map(|argument| argument.text)
        .collect::<Vec<_>>();
    let name = qualify_call_name(function.text, flags);
    stack.push(Expression {
        text: format!("{name}({})", arguments.join(", ")),
        precedence: 0,
        type_name: None,
    });
    Ok(())
}

fn qualify_call_name(name: String, flags: u16) -> String {
    let mut qualifiers = Vec::new();
    if flags & 1 != 0 {
        qualifiers.push("post");
    }
    if flags & 2 != 0 {
        qualifiers.push("dynamic");
    }
    if flags & 4 != 0 {
        qualifiers.push("event");
    }
    if qualifiers.is_empty() {
        name
    } else {
        format!("{} {name}", qualifiers.join(" "))
    }
}

fn pb2022_system_function_name(object_index: u16, function_index: u16) -> Option<&'static str> {
    // Confirmed against PB 2022 binaries and matching source from the
    // OpenSourcePFC exmmain and appexmfe fixtures at commit 19b7ec2.
    match (object_index, function_index) {
        (0x40d5, 20) => Some("classname"),
        (0x40d5, 25) => Some("closewithreturn"),
        (0x40d5, 57) => Some("fileexists"),
        (0x40d5, 65) => Some("fileopen"),
        (0x40d5, 106) => Some("getfilesavename"),
        (0x40d5, 176) => Some("messagebox"),
        (0x40d5, 177) => Some("messagebox"),
        (0x40d5, 187) => Some("open"),
        (0x40d5, 271) => Some("openwithparm"),
        (0x40d5, 279) => Some("pos"),
        (0x40d5, 342) => Some("rgb"),
        (0x40d5, 357) => Some("setpointer"),
        (0x40d5, 371..=373) => Some("showhelp"),
        (0x40d5, 387..=388) => Some("string"),
        (0x40d5, 399) => Some("today"),
        (0x40d5, 409) => Some("trim"),
        (0x40d5, 416) => Some("year"),
        _ => None,
    }
}

fn pb2022_system_enum_name(enum_type_ref: u16, item_index: u16) -> Option<&'static str> {
    // Each pair below occurs in a PB 2022 OpenSourcePFC binary and is matched
    // to the corresponding exported PowerScript source at commit 19b7ec2.
    match (enum_type_ref, item_index) {
        (0x4007, 0) => Some("ok"),
        (0x4017, 1) => Some("write"),
        (0x4018, 2) => Some("lockwrite"),
        (0x4019, 0) => Some("linemode"),
        (0x402d, 0) => Some("index"),
        (0x402d, 1) => Some("topic"),
        (0x402d, 2) => Some("keyword"),
        (0x402f, 1) => Some("stopsign"),
        (0x402f, 2) => Some("exclamation"),
        (0x403f, 0) => Some("listviewlargeicon"),
        (0x403f, 1) => Some("listviewsmallicon"),
        (0x403f, 2) => Some("listviewlist"),
        (0x403f, 3) => Some("listviewreport"),
        (0x4055, 8) => Some("hourglass"),
        (0x4067, 9) => Some("currenttreeitem"),
        (0x4070, 1) => Some("replace"),
        _ => None,
    }
}

fn pb2022_external_member(
    receiver_type: &str,
    member_index: u16,
) -> Option<(&'static str, &'static str)> {
    // The name is absent from the local descriptor. The receiver type and
    // member index are independently confirmed by w_master.activate source.
    match (receiver_type.to_ascii_lowercase().as_str(), member_index) {
        ("n_exampleappmanager", 2) => Some(("iapp_object", "application")),
        ("application", 6) => Some(("toolbarusercontrol", "boolean")),
        _ => None,
    }
}

fn parenthesize(expression: Expression, precedence: u8) -> String {
    if expression.precedence != 0 && expression.precedence < precedence {
        format!("({})", expression.text)
    } else {
        expression.text
    }
}

fn binary_operator(mnemonic: &str) -> Option<(&'static str, u8)> {
    let prefix = mnemonic.split('_').next()?;
    match prefix {
        "ADD" | "CAT" => Some(("+", 5)),
        "SUB" => Some(("-", 5)),
        "MULT" => Some(("*", 4)),
        "DIV" => Some(("/", 4)),
        "POWER" => Some(("^", 3)),
        "EQ" => Some(("=", 1)),
        "NE" => Some(("<>", 1)),
        "GT" => Some((">", 1)),
        "LT" => Some(("<", 1)),
        "GE" => Some((">=", 1)),
        "LE" => Some(("<=", 1)),
        _ => None,
    }
}

fn is_transparent_conversion(mnemonic: &str) -> bool {
    mnemonic.starts_with("CNV_") || mnemonic.starts_with("COPY_")
}

fn first_operand(instruction: &PCodeInstruction) -> Result<u16, String> {
    instruction
        .operands_u16_le
        .first()
        .copied()
        .ok_or_else(|| format!("{} has no first operand", instruction.mnemonic))
}

fn read_u32_operands(instruction: &PCodeInstruction) -> Result<u32, String> {
    read_u32_operand_pair(instruction, 0)
}

fn read_u32_operand_pair(
    instruction: &PCodeInstruction,
    word_offset: usize,
) -> Result<u32, String> {
    let low = *instruction
        .operands_u16_le
        .get(word_offset)
        .ok_or_else(|| format!("{} has no low word", instruction.mnemonic))?;
    let high = *instruction
        .operands_u16_le
        .get(word_offset + 1)
        .ok_or_else(|| format!("{} has no high word", instruction.mnemonic))?;
    Ok(u32::from(low) | (u32::from(high) << 16))
}

fn read_utf16le_string(buffer: &[u8], offset: u32) -> Option<String> {
    let start = (offset & 0x7fff_ffff) as usize;
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

fn read_identifier(buffer: &[u8], offset: u32) -> Option<String> {
    let value = read_utf16le_string(buffer, offset)?;
    let mut characters = value.chars();
    let first = characters.next()?;
    if first != '_' && !first.is_alphabetic() {
        return None;
    }
    characters
        .all(|character| character == '_' || character.is_alphanumeric())
        .then_some(value)
}

#[derive(Debug, Clone, Copy, PartialEq, Eq)]
struct MemberDescriptor {
    name_offset: u32,
    member_index: u16,
}

#[derive(Debug, Clone, PartialEq, Eq)]
struct TypeDescriptor {
    name: String,
    type_ref: u16,
}

fn read_member_descriptor(buffer: &[u8], descriptor_offset: u32) -> Option<MemberDescriptor> {
    let start = (descriptor_offset & 0x7fff_ffff) as usize;
    let descriptor = buffer.get(start..start.checked_add(8)?)?;
    let name_offset =
        u32::from_le_bytes([descriptor[0], descriptor[1], descriptor[2], descriptor[3]]);
    Some(MemberDescriptor {
        name_offset,
        member_index: u16::from_le_bytes([descriptor[4], descriptor[5]]),
    })
}

fn read_type_descriptor(buffer: &[u8], descriptor_offset: u32) -> Option<TypeDescriptor> {
    let descriptor = read_member_descriptor(buffer, descriptor_offset)?;
    Some(TypeDescriptor {
        name: read_identifier(buffer, descriptor.name_offset)?,
        type_ref: descriptor.member_index,
    })
}

fn escape_string(value: &str) -> String {
    value
        .replace('~', "~~")
        .replace('\r', "~r")
        .replace('\n', "~n")
        .replace('\t', "~t")
        .replace('"', "~\"")
}

fn format_signature(definition: &CompiledFunctionDefinition) -> String {
    let parameters = definition
        .parameters
        .iter()
        .map(format_parameter)
        .collect::<Vec<_>>()
        .join(", ");
    if definition.flags & 0x01 != 0 {
        return format!("event {}({parameters})", definition.name);
    }
    let access = if definition.flags & 0x10 != 0 {
        "private "
    } else if definition.flags & 0x20 != 0 {
        "protected "
    } else {
        "public "
    };
    if definition.return_type_ref == 0 {
        format!("{access}subroutine {}({parameters})", definition.name)
    } else {
        format!(
            "{access}function {} {}({parameters})",
            definition.return_type_name, definition.name
        )
    }
}

fn format_parameter(parameter: &CompiledFunctionParameter) -> String {
    let modifier = if parameter.is_read_only {
        "readonly "
    } else if parameter.is_reference {
        "ref "
    } else {
        ""
    };
    format!(
        "{modifier}{} {}{}",
        parameter.type_name, parameter.name, parameter.array
    )
}

fn format_variable(variable: &CompiledVariable) -> String {
    format!("{} {}{}", variable.type_name, variable.name, variable.array)
}

fn render_preview(
    signature: &str,
    declarations: &[String],
    statements: &[PreviewStatement],
) -> String {
    let mut lines = vec![signature.to_string()];
    for declaration in declarations {
        lines.push(format!("    {declaration}"));
    }
    if !declarations.is_empty() && !statements.is_empty() {
        lines.push(String::new());
    }
    for statement in statements {
        lines.push(format!("    {}", statement.text));
    }
    lines.push("end".to_string());
    lines.join("\n")
}

fn format_operands(operands: &[u16]) -> String {
    operands
        .iter()
        .map(|operand| format!("0x{operand:04X}"))
        .collect::<Vec<_>>()
        .join(" ")
}

#[cfg(test)]
mod tests {
    use domain::decode::PBVersion;

    use super::*;
    use crate::pb::pcode_scanner::scan_pcode_strict;

    fn integer_function(name: &str) -> CompiledFunctionDefinition {
        CompiledFunctionDefinition {
            index: 0,
            name: name.to_string(),
            return_type_ref: 1,
            return_type_name: "integer".to_string(),
            flags: 0,
            global_index: 0,
            reference_index: 0,
            event_code: 0,
            parameters: Vec::new(),
            library: None,
            alias: None,
        }
    }

    #[test]
    fn renders_constant_return_without_the_compiler_epilogue() {
        let bytes = [
            0x32, 0x00, 0x01, 0x00, // push integer 1
            0x01, 0x00, 0x01, 0x00, // return stack value
            0x04, 0x00, 0x0c, 0x00, // compiler jump to final return
            0x00, 0x00, // final return
        ];
        let scan = scan_pcode_strict(&bytes, PBVersion::PB2022);
        let preview = build_semantic_preview(
            &integer_function("done"),
            &[],
            &[],
            &[],
            &[],
            &[],
            &[],
            &scan,
        );
        assert!(preview.semantically_complete);
        assert!(preview.powerscript_like.contains("return 1"));
        assert!(!preview.powerscript_like.contains("goto"));
    }

    #[test]
    fn renders_known_source_local_assignment_and_method_call() {
        let mut bytes = Vec::new();
        let mut push = |opcode: u16, operands: &[u16]| {
            bytes.extend_from_slice(&opcode.to_le_bytes());
            for operand in operands {
                bytes.extend_from_slice(&operand.to_le_bytes());
            }
        };
        push(0x011d, &[0]);
        push(0x0021, &[]);
        push(0x003b, &[16, 0]);
        push(0x0133, &[1]);
        push(0x002c, &[76, 0, 1, 0]);
        push(0x013b, &[2]);
        push(0x0082, &[0]);
        push(0x001e, &[0]);
        push(0x0034, &[0, 0]);
        push(0x00a8, &[]);
        push(0x0003, &[64]);
        push(0x0034, &[1, 0]);
        push(0x0001, &[1]);
        push(0x0004, &[76]);
        push(0x001e, &[0]);
        push(0x0001, &[1]);
        push(0x0004, &[76]);
        push(0x0000, &[]);

        let mut stack_buffer = vec![0; 84];
        write_utf16z(&mut stack_buffer, 16, "Begin Transaction");
        write_utf16z(&mut stack_buffer, 52, "of_execute");
        stack_buffer[76..78].copy_from_slice(&0u16.to_le_bytes());
        stack_buffer[78..80].copy_from_slice(&37u16.to_le_bytes());
        stack_buffer[80..84].copy_from_slice(&52u32.to_le_bytes());
        let variable = CompiledVariable {
            index: 0,
            name: "ll_rc".to_string(),
            type_ref: 2,
            type_name: "long".to_string(),
            array: String::new(),
            flags: 0,
            is_shared: false,
            is_referenced_global: false,
            is_instance: true,
            is_indirect: false,
            is_constant: false,
            value_or_global_index: 0,
        };
        let scan = scan_pcode_strict(&bytes, PBVersion::PB2022);
        let preview = build_semantic_preview(
            &CompiledFunctionDefinition {
                return_type_ref: 2,
                return_type_name: "long".to_string(),
                ..integer_function("of_begin")
            },
            &[variable],
            &[],
            &[],
            &[],
            &[],
            &stack_buffer,
            &scan,
        );

        assert!(preview.semantically_complete, "{:?}", preview.unresolved);
        assert!(preview
            .powerscript_like
            .contains("ll_rc = this.of_execute(\"Begin Transaction\")"));
        assert!(preview.powerscript_like.contains("return ll_rc"));
    }

    #[test]
    fn resolves_referenced_global_by_global_index() {
        let bytes = [
            0x2f, 0x00, 0x1f, 0x00, // referenced global with index 31
            0x01, 0x00, 0x01, 0x00, // return stack value
            0x00, 0x00, // final return
        ];
        let variable = CompiledVariable {
            index: 0,
            name: "gnv_app".to_string(),
            type_ref: 0x8000,
            type_name: "n_appmanager".to_string(),
            array: String::new(),
            flags: 0,
            is_shared: true,
            is_referenced_global: true,
            is_instance: true,
            is_indirect: false,
            is_constant: false,
            value_or_global_index: 31,
        };
        let scan = scan_pcode_strict(&bytes, PBVersion::PB2022);
        let preview = build_semantic_preview(
            &integer_function("get_app"),
            &[variable],
            &[],
            &[],
            &[],
            &[],
            &[],
            &scan,
        );

        assert!(preview.semantically_complete, "{:?}", preview.unresolved);
        assert!(preview.powerscript_like.contains("return gnv_app"));
    }

    fn write_utf16z(buffer: &mut [u8], offset: usize, value: &str) {
        let mut cursor = offset;
        for word in value.encode_utf16().chain(std::iter::once(0)) {
            buffer[cursor..cursor + 2].copy_from_slice(&word.to_le_bytes());
            cursor += 2;
        }
    }

    #[test]
    fn rejects_non_identifier_member_names() {
        let mut stack_buffer = vec![0; 32];
        write_utf16z(&mut stack_buffer, 0, "0");
        write_utf16z(&mut stack_buffer, 4, "valid_name");

        assert_eq!(read_identifier(&stack_buffer, 0), None);
        assert_eq!(
            read_identifier(&stack_buffer, 4).as_deref(),
            Some("valid_name")
        );
    }

    #[test]
    fn resolves_member_name_through_const_ref_descriptor() {
        let bytes = [
            0x21, 0x00, // this
            0x20, 0x00, 0x20, 0x00, 0x00, 0x00, // descriptor at 32
            0x27, 0x00, 0x00, 0x00, // member access
            0x01, 0x00, 0x01, 0x00, // return stack value
            0x00, 0x00, // final return
        ];
        let mut stack_buffer = vec![0; 40];
        write_utf16z(&mut stack_buffer, 8, "title");
        stack_buffer[32..36].copy_from_slice(&8u32.to_le_bytes());
        let scan = scan_pcode_strict(&bytes, PBVersion::PB2022);
        let preview = build_semantic_preview(
            &integer_function("get_title"),
            &[],
            &[],
            &[],
            &[],
            &[],
            &stack_buffer,
            &scan,
        );

        assert!(preview.semantically_complete, "{:?}", preview.unresolved);
        assert!(preview.powerscript_like.contains("return this.title"));
    }

    #[test]
    fn renders_super_call_from_direct_name_offset() {
        let bytes = [
            0x13, 0x00, 0x26, 0x00, 0x00, 0x00, 0x01, 0x80, 0x10, 0x00, 0x00, 0x00, 0x3b, 0x01,
            0x00, 0x00, // call cleanup
            0x14, 0x00, // expression statement
            0x00, 0x00, // final return
        ];
        let mut stack_buffer = vec![0; 32];
        write_utf16z(&mut stack_buffer, 16, "open");
        let scan = scan_pcode_strict(&bytes, PBVersion::PB2022);
        let preview = build_semantic_preview(
            &integer_function("open"),
            &[],
            &[],
            &[],
            &[],
            &[],
            &stack_buffer,
            &scan,
        );

        assert!(preview.semantically_complete, "{:?}", preview.unresolved);
        assert!(preview.powerscript_like.contains("call super::open"));
    }

    #[test]
    fn renders_validated_pb2022_system_function_call() {
        let mut bytes = Vec::new();
        let mut push = |opcode: u16, operands: &[u16]| {
            bytes.extend_from_slice(&opcode.to_le_bytes());
            for operand in operands {
                bytes.extend_from_slice(&operand.to_le_bytes());
            }
        };
        push(0x003b, &[8, 0]);
        push(0x0133, &[1]);
        push(0x003b, &[16, 0]);
        push(0x0133, &[1]);
        push(0x01bc, &[279, 0x40d5]);
        push(0x01bd, &[279, 2, 0]);
        push(0x013b, &[2]);
        push(0x0001, &[1]);
        push(0x0000, &[]);
        let mut stack_buffer = vec![0; 24];
        write_utf16z(&mut stack_buffer, 8, "abc");
        write_utf16z(&mut stack_buffer, 16, "b");
        let scan = scan_pcode_strict(&bytes, PBVersion::PB2022);
        let preview = build_semantic_preview(
            &integer_function("find"),
            &[],
            &[],
            &[],
            &[],
            &[],
            &stack_buffer,
            &scan,
        );

        assert!(preview.semantically_complete, "{:?}", preview.unresolved);
        assert!(preview
            .powerscript_like
            .contains("return pos(\"abc\", \"b\")"));
    }

    #[test]
    fn renders_referenced_global_function_call() {
        let mut bytes = Vec::new();
        let mut push = |opcode: u16, operands: &[u16]| {
            bytes.extend_from_slice(&opcode.to_le_bytes());
            for operand in operands {
                bytes.extend_from_slice(&operand.to_le_bytes());
            }
        };
        push(0x0034, &[7, 0]);
        push(0x01bc, &[0, 0x8001]);
        push(0x01bd, &[0, 1, 0]);
        push(0x013b, &[1]);
        push(0x0001, &[1]);
        push(0x0000, &[]);
        let referenced = CompiledReferencedFunction {
            index: 0,
            name: "gf_lookup".to_string(),
            global_index: 31,
            is_global_function: true,
        };
        let scan = scan_pcode_strict(&bytes, PBVersion::PB2022);
        let preview = build_semantic_preview(
            &integer_function("lookup"),
            &[],
            &[],
            &[],
            &[],
            &[referenced],
            &[],
            &scan,
        );

        assert!(preview.semantically_complete, "{:?}", preview.unresolved);
        assert!(preview.powerscript_like.contains("return gf_lookup(7)"));
    }

    #[test]
    fn renders_dynamic_event_method_call() {
        let mut bytes = Vec::new();
        let mut push = |opcode: u16, operands: &[u16]| {
            bytes.extend_from_slice(&opcode.to_le_bytes());
            for operand in operands {
                bytes.extend_from_slice(&operand.to_le_bytes());
            }
        };
        push(0x0021, &[]);
        push(0x0171, &[32, 0, 0, 6]);
        push(0x013b, &[1]);
        push(0x0014, &[]);
        push(0x0000, &[]);
        let mut stack_buffer = vec![0; 40];
        write_utf16z(&mut stack_buffer, 8, "ue_changed");
        stack_buffer[36..40].copy_from_slice(&8u32.to_le_bytes());
        let scan = scan_pcode_strict(&bytes, PBVersion::PB2022);
        let preview = build_semantic_preview(
            &integer_function("changed"),
            &[],
            &[],
            &[],
            &[],
            &[],
            &stack_buffer,
            &scan,
        );

        assert!(preview.semantically_complete, "{:?}", preview.unresolved);
        assert!(preview
            .powerscript_like
            .contains("this.dynamic event ue_changed()"));
    }

    #[test]
    fn renders_external_object_creation_assignment() {
        let bytes = [
            0x1d, 0x01, 0x00, 0x00, // begin assignment to local 0
            0x6d, 0x01, 0x10, 0x00, 0x00, 0x00, // type descriptor at 16
            0x8a, 0x00, 0x00, 0x00, // assign object instance
            0x00, 0x00, // return
        ];
        let mut stack_buffer = vec![0; 24];
        write_utf16z(&mut stack_buffer, 0, "n_ds");
        stack_buffer[16..20].copy_from_slice(&0u32.to_le_bytes());
        stack_buffer[20..22].copy_from_slice(&0x8000u16.to_le_bytes());
        let variable = CompiledVariable {
            index: 0,
            name: "lds_titles".to_string(),
            type_ref: 0x8000,
            type_name: "n_ds".to_string(),
            array: String::new(),
            flags: 0,
            is_shared: false,
            is_referenced_global: false,
            is_instance: true,
            is_indirect: false,
            is_constant: false,
            value_or_global_index: 0,
        };
        let object_type = CompiledType {
            index: 0,
            type_ref: 0x8000,
            name: "n_ds".to_string(),
            is_referenced_object: true,
        };
        let scan = scan_pcode_strict(&bytes, PBVersion::PB2022);
        let preview = build_semantic_preview(
            &integer_function("create_ds"),
            &[variable],
            &[],
            &[object_type],
            &[],
            &[],
            &stack_buffer,
            &scan,
        );

        assert!(preview.semantically_complete, "{:?}", preview.unresolved);
        assert!(preview
            .powerscript_like
            .contains("lds_titles = create n_ds"));
    }

    #[test]
    fn resolves_local_and_validated_system_enum_constants() {
        let local_bytes = [
            0x3d, 0x00, 0x02, 0x00, 0x00, 0x80, // local enum item 2
            0x01, 0x00, 0x01, 0x00, // return value
            0x00, 0x00,
        ];
        let enum_value = CompiledEnumValue {
            enum_type_ref: 0x8000,
            enum_type_name: "e_choice".to_string(),
            item_index: 2,
            name: "selected".to_string(),
        };
        let local_scan = scan_pcode_strict(&local_bytes, PBVersion::PB2022);
        let local_preview = build_semantic_preview(
            &integer_function("local_enum"),
            &[],
            &[],
            &[],
            &[enum_value],
            &[],
            &[],
            &local_scan,
        );
        assert!(local_preview.semantically_complete);
        assert!(local_preview.powerscript_like.contains("return selected!"));

        let system_bytes = [
            0x3d, 0x00, 0x08, 0x00, 0x55, 0x40, // hourglass!
            0xbc, 0x01, 0x65, 0x01, 0xd5, 0x40, // system SetPointer
            0xbd, 0x01, 0x65, 0x01, 0x01, 0x00, 0x00, 0x00, // one argument
            0x3b, 0x01, 0x01, 0x00, // cleanup
            0x14, 0x00, // statement expression
            0x00, 0x00,
        ];
        let system_scan = scan_pcode_strict(&system_bytes, PBVersion::PB2022);
        let system_preview = build_semantic_preview(
            &integer_function("pointer"),
            &[],
            &[],
            &[],
            &[],
            &[],
            &[],
            &system_scan,
        );
        assert!(
            system_preview.semantically_complete,
            "{:?}",
            system_preview.unresolved
        );
        assert!(system_preview
            .powerscript_like
            .contains("setpointer(hourglass!)"));
    }

    #[test]
    fn resolves_member_name_from_validated_external_type_metadata() {
        let bytes = [
            0x1e, 0x00, 0x00, 0x00, // gnv_app
            0x20, 0x00, 0x20, 0x00, 0x00, 0x00, // iapp_object descriptor
            0x27, 0x00, 0x00, 0x00, // member read
            0x20, 0x00, 0x28, 0x00, 0x00, 0x00, // external member descriptor
            0x22, 0x01, 0x02, 0x00, // member lvalue
            0x3c, 0x00, 0x00, 0x00, // false
            0x80, 0x00, 0x02, 0x00, // assign integer/boolean
            0x00, 0x00,
        ];
        let mut stack_buffer = vec![0; 48];
        write_utf16z(&mut stack_buffer, 0, "iapp_object");
        stack_buffer[32..36].copy_from_slice(&0u32.to_le_bytes());
        stack_buffer[36..38].copy_from_slice(&2u16.to_le_bytes());
        stack_buffer[38..40].copy_from_slice(&0x8000u16.to_le_bytes());
        stack_buffer[40..44].copy_from_slice(&0x0000_ffffu32.to_le_bytes());
        stack_buffer[44..46].copy_from_slice(&6u16.to_le_bytes());
        stack_buffer[46..48].copy_from_slice(&7u16.to_le_bytes());
        let variable = CompiledVariable {
            index: 0,
            name: "gnv_app".to_string(),
            type_ref: 0x8001,
            type_name: "n_exampleappmanager".to_string(),
            array: String::new(),
            flags: 0,
            is_shared: true,
            is_referenced_global: true,
            is_instance: true,
            is_indirect: false,
            is_constant: false,
            value_or_global_index: 31,
        };
        let application_type = CompiledType {
            index: 0,
            type_ref: 0x8000,
            name: "application".to_string(),
            is_referenced_object: true,
        };
        let scan = scan_pcode_strict(&bytes, PBVersion::PB2022);
        let preview = build_semantic_preview(
            &integer_function("disable_toolbar"),
            &[variable],
            &[],
            &[application_type],
            &[],
            &[],
            &stack_buffer,
            &scan,
        );

        assert!(preview.semantically_complete, "{:?}", preview.unresolved);
        assert!(preview
            .powerscript_like
            .contains("gnv_app.iapp_object.toolbarusercontrol = false"));
    }
}
