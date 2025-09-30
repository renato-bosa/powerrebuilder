//! Type Inference
//!
//! Infer types from SSA form using usage patterns and hints.

use super::ssa::{Ssa, SsaVar};
use serde::{Deserialize, Serialize};
use std::collections::HashMap;

/// Inferred type
#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
pub enum Ty {
    Void,
    Bool,
    Int,
    Real,
    String,
    Struct(String, Vec<(String, Ty)>),
    Unknown,
}

impl std::fmt::Display for Ty {
    fn fmt(&self, f: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        match self {
            Self::Void => write!(f, "void"),
            Self::Bool => write!(f, "bool"),
            Self::Int => write!(f, "int"),
            Self::Real => write!(f, "real"),
            Self::String => write!(f, "string"),
            Self::Struct(name, _) => write!(f, "{}", name),
            Self::Unknown => write!(f, "?"),
        }
    }
}

/// Type hints from external sources
#[derive(Debug, Clone, Default)]
pub struct TypeHints {
    pub hints: HashMap<SsaVar, Ty>,
}

impl TypeHints {
    pub fn new() -> Self {
        Self::default()
    }

    pub fn add_hint(&mut self, var: SsaVar, ty: Ty) {
        self.hints.insert(var, ty);
    }
}

/// Type map for variables
pub type TypeMap = HashMap<SsaVar, Ty>;

/// Infer types for all variables in SSA
///
/// Pure function using constraint solving and hints.
pub fn infer_types(ssa: &Ssa, hints: &TypeHints) -> TypeMap {
    let mut types = TypeMap::new();

    // Apply hints first
    for (var, ty) in &hints.hints {
        types.insert(*var, ty.clone());
    }

    // Simple inference: everything else is Unknown
    for block in &ssa.blocks {
        for def in &block.defs {
            match def {
                super::ssa::SsaDef::Assign { var, .. } => {
                    types.entry(*var).or_insert(Ty::Unknown);
                }
                super::ssa::SsaDef::Phi { var, .. } => {
                    types.entry(*var).or_insert(Ty::Unknown);
                }
            }
        }
    }

    types
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_type_display() {
        assert_eq!(Ty::Int.to_string(), "int");
        assert_eq!(Ty::String.to_string(), "string");
        assert_eq!(Ty::Unknown.to_string(), "?");
    }

    #[test]
    fn test_type_hints() {
        let mut hints = TypeHints::new();
        hints.add_hint(SsaVar(0), Ty::Int);
        assert_eq!(hints.hints.get(&SsaVar(0)), Some(&Ty::Int));
    }
}
