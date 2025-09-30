//! Type System
//!
//! Nominal and structural type definitions for Core IR.

use crate::decode::infer::Ty;
use serde::{Deserialize, Serialize};

/// Type definition
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct TypeDef {
    pub name: String,
    pub kind: TypeKind,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub enum TypeKind {
    Nominal { base: Ty },
    Structural { fields: Vec<(String, Ty)> },
    Alias { target: Ty },
}

/// Subtyping relationship
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct Subtype {
    pub subtype: Ty,
    pub supertype: Ty,
    pub is_nominal: bool,
}

/// Type constraint
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct TypeConstraint {
    pub ty: Ty,
    pub constraint: String,
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_type_def() {
        let def = TypeDef {
            name: "MyType".into(),
            kind: TypeKind::Nominal { base: Ty::Int },
        };
        assert_eq!(def.name, "MyType");
    }
}
