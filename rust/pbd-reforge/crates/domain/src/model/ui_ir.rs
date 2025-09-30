//! UI-Specific IR
//!
//! Represents user interface structure independent of PowerBuilder or target framework.

use crate::model::pb_ir::PbUnit;
use serde::{Deserialize, Serialize};
use std::collections::HashMap;

/// UI tree representation
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct UiTree {
    pub root: UiNode,
}

/// UI node - hierarchical UI element
#[derive(Debug, Clone, Serialize, Deserialize)]
pub enum UiNode {
    Window { title: String, children: Vec<UiNode> },
    Menu { items: Vec<MenuItem> },
    Control { kind: ControlKind, props: PropMap },
    Container { layout: Layout, children: Vec<UiNode> },
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct MenuItem {
    pub text: String,
    pub action: Option<String>,
    pub children: Vec<MenuItem>,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub enum ControlKind {
    Button,
    TextBox,
    Label,
    ComboBox,
    ListBox,
    DataGrid,
    Custom(String),
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub enum Layout {
    Vertical,
    Horizontal,
    Grid { rows: usize, cols: usize },
    Absolute,
}

pub type PropMap = HashMap<String, String>;

/// Build UI IR from PowerBuilder unit
///
/// Extracts UI structure from PB-specific representation.
pub fn build_ui_ir(pb: &PbUnit) -> UiTree {
    UiTree {
        root: UiNode::Window {
            title: pb.name.clone(),
            children: vec![],
        },
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_ui_tree() {
        let tree = UiTree {
            root: UiNode::Window {
                title: "Test".into(),
                children: vec![],
            },
        };
        match tree.root {
            UiNode::Window { title, .. } => assert_eq!(title, "Test"),
            _ => panic!("Expected Window node"),
        }
    }
}
