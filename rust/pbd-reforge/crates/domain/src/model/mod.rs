//! Model Bounded Context
//!
//! Raise PowerBuilder-aware IR, normalize to core language-neutral IR,
//! and extract UI IR.

pub mod core_ir;
pub mod pb_ir;
pub mod type_system;
pub mod ui_ir;

pub use core_ir::{CoreExpr, CoreItem, CoreModule, DataDef, FnSig as CoreFnSig, Literal, ModuleId, normalise};
pub use pb_ir::{EmuSnapshot, FnSig, Parameter, PbMember, PbUnit, UiSpec, merge_semantics};
pub use type_system::{Subtype, TypeConstraint, TypeDef, TypeKind};
pub use ui_ir::{ControlKind, Layout, MenuItem, PropMap, UiNode, UiTree, build_ui_ir};
