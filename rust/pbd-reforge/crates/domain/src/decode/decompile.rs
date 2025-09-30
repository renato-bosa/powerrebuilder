//! P-code Decompilation - Statement Reconstruction
//!
//! Pure functions for decompiling P-code bytecode to high-level statements.
//! Follows Parse Don't Validate pattern with factory functions.

use super::cfg::{BasicBlock, BlockId, Cfg};
use super::infer::{Ty, TypeMap};
use super::opcode::Instr;
use super::ssa::{Ssa, SsaBlock, SsaDef, SsaTerminator, SsaValue, SsaVar};
use serde::{Deserialize, Serialize};
use std::collections::HashMap;

/// Decompiled function
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct DecompiledFunction {
    pub name: String,
    pub return_type: Option<Ty>,
    pub parameters: Vec<Parameter>,
    pub local_variables: Vec<LocalVariable>,
    pub body: StatementBlock,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct Parameter {
    pub name: String,
    pub data_type: Ty,
    pub is_ref: bool,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct LocalVariable {
    pub name: String,
    pub data_type: Ty,
    pub initial_value: Option<Expression>,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct StatementBlock {
    pub statements: Vec<Statement>,
}

/// High-level statement
#[derive(Debug, Clone, Serialize, Deserialize)]
pub enum Statement {
    Assignment {
        target: Expression,
        value: Expression,
    },
    If {
        condition: Expression,
        then_block: StatementBlock,
        else_block: Option<StatementBlock>,
    },
    While {
        condition: Expression,
        body: StatementBlock,
    },
    For {
        init: Box<Statement>,
        condition: Expression,
        increment: Box<Statement>,
        body: StatementBlock,
    },
    Return {
        value: Option<Expression>,
    },
    Call {
        target: Option<Expression>,
        function_name: String,
        arguments: Vec<Expression>,
    },
    Block(StatementBlock),
    Empty,
}

/// Expression (can be nested)
#[derive(Debug, Clone, Serialize, Deserialize)]
pub enum Expression {
    Binary {
        left: Box<Expression>,
        operator: BinaryOp,
        right: Box<Expression>,
    },
    Unary {
        operator: UnaryOp,
        operand: Box<Expression>,
    },
    Literal {
        value: LiteralValue,
        literal_type: Ty,
    },
    Variable {
        name: String,
    },
    Member {
        object: Box<Expression>,
        member: String,
    },
    Call {
        function: String,
        arguments: Vec<Expression>,
    },
    Index {
        array: Box<Expression>,
        index: Box<Expression>,
    },
}

#[derive(Debug, Clone, Copy, PartialEq, Eq, Serialize, Deserialize)]
pub enum BinaryOp {
    Add,
    Sub,
    Mul,
    Div,
    Mod,
    Eq,
    Ne,
    Lt,
    Le,
    Gt,
    Ge,
    And,
    Or,
}

#[derive(Debug, Clone, Copy, PartialEq, Eq, Serialize, Deserialize)]
pub enum UnaryOp {
    Not,
    Neg,
    Plus,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub enum LiteralValue {
    Int(i64),
    Float(f64),
    String(String),
    Bool(bool),
    Null,
}

/// Symbol table entry
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct Symbol {
    pub name: String,
    pub symbol_type: SymbolType,
    pub data_type: Option<Ty>,
    pub scope: Scope,
    pub references: Vec<usize>,
}

#[derive(Debug, Clone, Copy, PartialEq, Eq, Serialize, Deserialize)]
pub enum SymbolType {
    Variable,
    Parameter,
    Function,
    Type,
}

#[derive(Debug, Clone, Copy, PartialEq, Eq, Serialize, Deserialize)]
pub enum Scope {
    Local,
    Global,
    Instance,
}

pub type SymbolTable = HashMap<String, Symbol>;

/// Loop structure
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct Loop {
    pub header: BlockId,
    pub back_edges: Vec<(BlockId, BlockId)>,
    pub body_blocks: Vec<BlockId>,
    pub loop_type: LoopType,
}

#[derive(Debug, Clone, Copy, PartialEq, Eq, Serialize, Deserialize)]
pub enum LoopType {
    While,
    DoWhile,
    For,
    Unknown,
}

/// Create decompiled function from instructions
///
/// Main entry point following Parse Don't Validate pattern.
pub fn create_decompiled_function(
    name: String,
    instrs: &[Instr],
    types: &TypeMap,
) -> Result<DecompiledFunction, String> {
    // Validate input
    if instrs.is_empty() {
        return Err("Empty instruction list".into());
    }

    // Build CFG
    let cfg = super::cfg::build_cfg(instrs);

    // Build SSA
    let ssa = super::ssa::to_ssa(&cfg);

    // Extract symbols
    let symbols = extract_symbols(&ssa, types);

    // Reconstruct statements
    let body = reconstruct_statements(&ssa, &symbols)?;

    // Extract metadata
    let (params, return_type, locals) = extract_metadata(&symbols, types);

    Ok(DecompiledFunction {
        name,
        return_type,
        parameters: params,
        local_variables: locals,
        body,
    })
}

/// Extract symbol table from SSA
fn extract_symbols(ssa: &Ssa, types: &TypeMap) -> SymbolTable {
    let mut symbols = HashMap::new();

    for (var, ty) in types.iter() {
        let name = format!("var_{}", var.0);
        symbols.insert(
            name.clone(),
            Symbol {
                name,
                symbol_type: SymbolType::Variable,
                data_type: Some(ty.clone()),
                scope: Scope::Local,
                references: vec![],
            },
        );
    }

    symbols
}

/// Reconstruct high-level statements from SSA
fn reconstruct_statements(
    ssa: &Ssa,
    symbols: &SymbolTable,
) -> Result<StatementBlock, String> {
    let mut statements = Vec::new();

    for block in &ssa.blocks {
        for def in &block.defs {
            if let Some(stmt) = ssa_def_to_statement(def, symbols) {
                statements.push(stmt);
            }
        }

        // Handle terminator
        if let Some(stmt) = terminator_to_statement(&block.terminator, symbols) {
            statements.push(stmt);
        }
    }

    Ok(StatementBlock { statements })
}

/// Convert SSA definition to statement
fn ssa_def_to_statement(def: &SsaDef, _symbols: &SymbolTable) -> Option<Statement> {
    match def {
        SsaDef::Assign { var, value } => {
            let target = Expression::Variable {
                name: format!("var_{}", var.0),
            };
            let val_expr = ssa_value_to_expression(value)?;
            Some(Statement::Assignment {
                target,
                value: val_expr,
            })
        }
        SsaDef::Phi { .. } => None, // Phi nodes don't translate to statements
    }
}

/// Convert SSA terminator to statement
fn terminator_to_statement(terminator: &SsaTerminator, _symbols: &SymbolTable) -> Option<Statement> {
    match terminator {
        SsaTerminator::Return(Some(value)) => {
            let expr = ssa_value_to_expression(value)?;
            Some(Statement::Return { value: Some(expr) })
        }
        SsaTerminator::Return(None) => Some(Statement::Return { value: None }),
        SsaTerminator::Branch {
            cond,
            true_block,
            false_block,
        } => {
            // Simplified - real implementation would reconstruct if-else structure
            let condition = ssa_value_to_expression(cond)?;
            Some(Statement::If {
                condition,
                then_block: StatementBlock { statements: vec![] },
                else_block: Some(StatementBlock { statements: vec![] }),
            })
        }
        SsaTerminator::Jump(_) => None,
    }
}

/// Convert SSA value to expression
fn ssa_value_to_expression(value: &SsaValue) -> Option<Expression> {
    match value {
        SsaValue::Var(var) => Some(Expression::Variable {
            name: format!("var_{}", var.0),
        }),
        SsaValue::Const(c) => Some(Expression::Literal {
            value: LiteralValue::Int(*c),
            literal_type: Ty::Int,
        }),
        SsaValue::BinOp { op, left, right } => {
            let left_expr = ssa_value_to_expression(left)?;
            let right_expr = ssa_value_to_expression(right)?;
            let operator = match op {
                super::ssa::BinOp::Add => BinaryOp::Add,
                super::ssa::BinOp::Sub => BinaryOp::Sub,
                super::ssa::BinOp::Mul => BinaryOp::Mul,
                super::ssa::BinOp::Div => BinaryOp::Div,
                super::ssa::BinOp::Eq => BinaryOp::Eq,
                super::ssa::BinOp::Ne => BinaryOp::Ne,
                super::ssa::BinOp::Lt => BinaryOp::Lt,
                super::ssa::BinOp::Le => BinaryOp::Le,
                super::ssa::BinOp::Gt => BinaryOp::Gt,
                super::ssa::BinOp::Ge => BinaryOp::Ge,
            };
            Some(Expression::Binary {
                left: Box::new(left_expr),
                operator,
                right: Box::new(right_expr),
            })
        }
        SsaValue::Call { func, args } => {
            let arguments = args
                .iter()
                .filter_map(ssa_value_to_expression)
                .collect();
            Some(Expression::Call {
                function: func.clone(),
                arguments,
            })
        }
    }
}

/// Extract function metadata
fn extract_metadata(
    symbols: &SymbolTable,
    types: &TypeMap,
) -> (Vec<Parameter>, Option<Ty>, Vec<LocalVariable>) {
    let params = vec![]; // Would extract from calling convention
    let return_type = None; // Would infer from return statements
    let locals: Vec<LocalVariable> = symbols
        .values()
        .filter(|s| s.symbol_type == SymbolType::Variable && s.scope == Scope::Local)
        .map(|s| LocalVariable {
            name: s.name.clone(),
            data_type: s.data_type.clone().unwrap_or(Ty::Unknown),
            initial_value: None,
        })
        .collect();

    (params, return_type, locals)
}

/// Detect loops in CFG
pub fn detect_loops(cfg: &Cfg) -> Vec<Loop> {
    let mut loops = Vec::new();

    // Find back edges (edges that go to earlier blocks)
    for (from_id, to_id) in &cfg.edges {
        if to_id < from_id {
            // This is a back edge - indicates a loop
            loops.push(Loop {
                header: *to_id,
                back_edges: vec![(*from_id, *to_id)],
                body_blocks: (*to_id..=*from_id).collect(),
                loop_type: LoopType::While, // Will refine based on pattern
            });
        }
    }

    loops
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_create_decompiled_function() {
        let instrs = vec![Instr::Op {
            code: 0x01,
            imm: None,
            pos: 0,
        }];
        let types = HashMap::new();

        let result = create_decompiled_function("test".into(), &instrs, &types);
        assert!(result.is_ok());
    }

    #[test]
    fn test_empty_instructions() {
        let instrs = vec![];
        let types = HashMap::new();

        let result = create_decompiled_function("test".into(), &instrs, &types);
        assert!(result.is_err());
    }
}
