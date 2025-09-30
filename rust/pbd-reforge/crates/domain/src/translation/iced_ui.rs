//! Iced UI Target
//!
//! Map UI IR to Iced framework components.

use crate::model::UiTree;
use crate::translation::rust_ast::RsFile;
use serde::{Deserialize, Serialize};

/// Iced view representation
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct IcedView {
    pub files: Vec<RsFile>,
}

/// Convert UI IR to Iced view code
pub fn ui_to_iced(ui: &UiTree) -> IcedView {
    // Extract window title for module name
    let module_name = match &ui.root {
        crate::model::UiNode::Window { title, .. } => title.clone(),
        _ => "app".to_string(),
    };

    IcedView {
        files: vec![RsFile {
            path: format!("{}_view.rs", module_name.to_lowercase()),
            items: vec![],
        }],
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    use crate::model::UiNode;

    #[test]
    fn test_ui_to_iced() {
        let ui = UiTree {
            root: UiNode::Window {
                title: "TestApp".into(),
                children: vec![],
            },
        };
        let view = ui_to_iced(&ui);
        assert_eq!(view.files[0].path, "testapp_view.rs");
    }
}
