//! Core Language-Neutral IR
//!
//! Universal intermediate representation that all targets can consume.
//! Stripped of PowerBuilder-specific concepts.

use crate::decode::infer::{Ty, TypeMap};
use crate::model::pb_ir::PbUnit;
use serde::{Deserialize, Serialize};

/// Module identifier
pub type ModuleId = String;

/// Core module - language-neutral compilation unit
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct CoreModule {
    pub id: ModuleId,
    pub items: Vec<CoreItem>,
}

/// Top-level item in a module
#[derive(Debug, Clone, Serialize, Deserialize)]
pub enum CoreItem {
    Fn { sig: FnSig, body: CoreExpr },
    Data { def: DataDef },
    Extern { sig: FnSig },
}

/// Function signature
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct FnSig {
    pub name: String,
    pub params: Vec<(String, Ty)>,
    pub return_ty: Ty,
}

/// Data definition (struct, enum, etc.)
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct DataDef {
    pub name: String,
    pub fields: Vec<(String, Ty)>,
}

/// Core expression
#[derive(Debug, Clone, Serialize, Deserialize)]
pub enum CoreExpr {
    Lit(Literal),
    Var(String),
    BinOp { op: String, left: Box<CoreExpr>, right: Box<CoreExpr> },
    Call { func: String, args: Vec<CoreExpr> },
    If { cond: Box<CoreExpr>, then: Box<CoreExpr>, else_: Option<Box<CoreExpr>> },
    Block(Vec<CoreExpr>),
    Return(Option<Box<CoreExpr>>),
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub enum Literal {
    Int(i64),
    Float(f64),
    String(String),
    Bool(bool),
}

/// Normalize PowerBuilder IR to Core IR
///
/// Pure transformation removing PB-specific concepts.
pub fn normalise(pb: &PbUnit, _ty: &TypeMap) -> CoreModule {
    CoreModule {
        id: pb.name.clone(),
        items: vec![],
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_core_module() {
        let module = CoreModule {
            id: "test".into(),
            items: vec![],
        };
        assert_eq!(module.id, "test");
    }
}
