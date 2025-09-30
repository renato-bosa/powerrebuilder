//! Rust AST Target Model
//!
//! Representation of Rust code for emission.

use crate::model::CoreModule;
use serde::{Deserialize, Serialize};

/// Rust file
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct RsFile {
    pub path: String,
    pub items: Vec<RsItem>,
}

/// Top-level Rust item
#[derive(Debug, Clone, Serialize, Deserialize)]
pub enum RsItem {
    Fn(RsFn),
    Struct(RsStruct),
    Enum(RsEnum),
    Impl(RsImpl),
    Use(String),
    Mod(String),
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct RsFn {
    pub name: String,
    pub params: Vec<(String, String)>,
    pub return_ty: Option<String>,
    pub body: String,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct RsStruct {
    pub name: String,
    pub fields: Vec<(String, String)>,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct RsEnum {
    pub name: String,
    pub variants: Vec<String>,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct RsImpl {
    pub target: String,
    pub items: Vec<RsItem>,
}

/// Rust AST collection
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct RustAst {
    pub files: Vec<RsFile>,
}

/// Convert Core IR to Rust AST
pub fn core_to_rust_ast(m: &CoreModule) -> RustAst {
    RustAst {
        files: vec![RsFile {
            path: format!("{}.rs", m.id),
            items: vec![],
        }],
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_rust_ast() {
        let ast = RustAst {
            files: vec![RsFile {
                path: "lib.rs".into(),
                items: vec![],
            }],
        };
        assert_eq!(ast.files[0].path, "lib.rs");
    }
}
