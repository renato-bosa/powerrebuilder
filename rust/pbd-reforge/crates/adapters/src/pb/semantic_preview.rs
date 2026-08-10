//! Conservative PowerScript-like previews for structurally validated functions.
//!
//! This is intentionally a small semantic slice. Unsupported instructions are
//! preserved as comments, and `semantically_complete` is only true when every
//! instruction was handled without inventing stack values.

use serde::Serialize;

use super::compiled_object::{
    CompiledFunctionDefinition, CompiledFunctionParameter, CompiledVariable,
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
}

pub fn build_semantic_preview(
    definition: &CompiledFunctionDefinition,
    variables: &[CompiledVariable],
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
        0x001e | 0x0030 | 0x01a7 | 0x01a9 => {
            let index = first_operand(instruction)? as usize;
            let variable = variables
                .get(index)
                .ok_or_else(|| format!("local-variable index {index} is out of bounds"))?;
            stack.push(Expression {
                text: variable.name.clone(),
                precedence: 0,
            });
        }
        0x0021 => stack.push(Expression {
            text: "this".to_string(),
            precedence: 0,
        }),
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
        0x0024 => apply_binary(stack, "and", 2)?,
        0x0025 => apply_binary(stack, "or", 2)?,
        0x0026 => apply_unary(stack, "not ")?,
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
    });
    Ok(())
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
    let low = *instruction
        .operands_u16_le
        .first()
        .ok_or_else(|| format!("{} has no low word", instruction.mnemonic))?;
    let high = *instruction
        .operands_u16_le
        .get(1)
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
        let preview = build_semantic_preview(&integer_function("done"), &[], &[], &scan);
        assert!(preview.semantically_complete);
        assert!(preview.powerscript_like.contains("return 1"));
        assert!(!preview.powerscript_like.contains("goto"));
    }
}
