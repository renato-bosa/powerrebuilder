//! Translation Bounded Context
//!
//! Map IR to target ASTs and project files.

pub mod iced_ui;
pub mod rust_ast;
pub mod target_trait;

pub use iced_ui::{IcedView, ui_to_iced};
pub use rust_ast::{RsEnum, RsFile, RsFn, RsImpl, RsItem, RsStruct, RustAst, core_to_rust_ast};
pub use target_trait::{EmissionUnit, EmitErr, EmittedFile, FeatureSet, TargetEmitter};
