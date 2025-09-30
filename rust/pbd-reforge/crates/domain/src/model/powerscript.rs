//! PowerScript Domain Types
//!
//! PowerScript is PowerBuilder's programming language.
//! These types represent PowerScript constructs for parsing and code generation.

use serde::{Deserialize, Serialize};

/// PowerScript AST node types
#[derive(Debug, Clone, Copy, PartialEq, Eq, Serialize, Deserialize)]
pub enum PowerScriptNodeType {
    // PowerBuilder Objects
    Window,
    DataWindow,
    UserObject,
    Menu,
    Application,

    // PowerScript Elements
    Function,
    Event,
    Property,
    InstanceVar,

    // PowerScript Statements
    ScriptBlock,
    IfStatement,
    ChooseCase, // PowerScript's switch statement
    DoLoop,     // PowerScript DO...LOOP
    ForLoop,
    ReturnStatement,
    Assignment,
    TryCatch, // PowerScript exception handling

    // Expressions
    BinaryOp,
    UnaryOp,
    Call,
    Identifier,
    Literal,

    // Types
    Type,
    ArrayType,

    // DataWindow Elements (PowerBuilder's unique technology)
    DwSql,     // DataWindow SQL
    DwColumn,  // DataWindow column
    DwCompute, // Computed field
    DwBand,    // DataWindow band (header, detail, footer)
    DwControl, // DataWindow control
}

/// PowerScript token types
#[derive(Debug, Clone, Copy, PartialEq, Eq, Serialize, Deserialize)]
pub enum PowerScriptTokenType {
    // PowerScript Keywords
    If,
    Then,
    Else,
    ElseIf,
    EndIf,
    Function,
    Subroutine, // PowerScript subroutine
    Event,
    Return,
    For,
    To,
    Next,
    Do,
    Loop,
    Choose, // PowerScript CHOOSE CASE
    Case,

    // Operators
    Plus,
    Minus,
    Multiply,
    Divide,
    Assign,
    Equals,

    // Delimiters
    LParen,
    RParen,
    Semicolon,
    Comma,

    // Literals
    IntegerLiteral,
    StringLiteral,
    Identifier,
}

impl PowerScriptNodeType {
    pub fn as_str(&self) -> &'static str {
        match self {
            Self::Window => "window",
            Self::DataWindow => "datawindow",
            Self::UserObject => "userobject",
            Self::Menu => "menu",
            Self::Application => "application",
            Self::Function => "function",
            Self::Event => "event",
            Self::Property => "property",
            Self::InstanceVar => "instance_variable",
            Self::ScriptBlock => "script_block",
            Self::IfStatement => "if",
            Self::ChooseCase => "choose_case",
            Self::DoLoop => "do_loop",
            Self::ForLoop => "for",
            Self::ReturnStatement => "return",
            Self::Assignment => "assignment",
            Self::TryCatch => "try_catch",
            Self::BinaryOp => "binary_op",
            Self::UnaryOp => "unary_op",
            Self::Call => "call",
            Self::Identifier => "identifier",
            Self::Literal => "literal",
            Self::Type => "type",
            Self::ArrayType => "array_type",
            Self::DwSql => "dw_sql",
            Self::DwColumn => "dw_column",
            Self::DwCompute => "dw_compute",
            Self::DwBand => "dw_band",
            Self::DwControl => "dw_control",
        }
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_node_type_as_str() {
        assert_eq!(PowerScriptNodeType::Window.as_str(), "window");
        assert_eq!(PowerScriptNodeType::DataWindow.as_str(), "datawindow");
        assert_eq!(PowerScriptNodeType::ChooseCase.as_str(), "choose_case");
    }
}
