"""Node kind enumeration for PowerBuilder AST nodes.

This module defines an enumeration of all possible node types in the PowerBuilder AST.
It helps with node categorization, visitor pattern implementation, and type checking.
"""

from typing import Any, Dict, List, Optional, Union

from __future__ import annotations

from enum import Enum, auto


class NodeKind(Enum):
    """Enumeration of all PowerBuilder AST node types."""

    # ─── Base Node Types ──────────────────────────────────────────────────────
    UNKNOWN = auto()
    ERROR = auto()

    # ─── Statement Types ──────────────────────────────────────────────────────
    STATEMENT = auto()
    ASSIGNMENT_STATEMENT = auto()
    EXPRESSION_STATEMENT = auto()
    RETURN_STATEMENT = auto()
    IF_STATEMENT = auto()
    ELSE_STATEMENT = auto()
    ELSEIF_STATEMENT = auto()
    FOR_LOOP = auto()
    WHILE_LOOP = auto()
    DO_WHILE_LOOP = auto()
    DO_UNTIL_LOOP = auto()
    REPEAT_UNTIL_LOOP = auto()
    CONTINUE_STATEMENT = auto()
    BREAK_STATEMENT = auto()
    EXIT_STATEMENT = auto()
    GOTO_STATEMENT = auto()
    CASE_STATEMENT = auto()
    CHOOSE_CASE_STATEMENT = auto()
    TRY_CATCH_STATEMENT = auto()
    THROW_STATEMENT = auto()

    # ─── Declaration Types ────────────────────────────────────────────────────
    VARIABLE_DECLARATION = auto()
    CONSTANT_DECLARATION = auto()
    FUNCTION_DECLARATION = auto()
    PROCEDURE_DECLARATION = auto()
    EVENT_DECLARATION = auto()
    TYPE_DECLARATION = auto()
    FORWARD_DECLARATION = auto()
    GLOBAL_DECLARATION = auto()
    SHARED_DECLARATION = auto()

    # ─── Expression Types ─────────────────────────────────────────────────────
    EXPRESSION = auto()
    BINARY_EXPRESSION = auto()
    UNARY_EXPRESSION = auto()
    TERNARY_EXPRESSION = auto()
    LITERAL_EXPRESSION = auto()
    IDENTIFIER_EXPRESSION = auto()
    MEMBER_ACCESS_EXPRESSION = auto()
    ARRAY_ACCESS_EXPRESSION = auto()
    FUNCTION_CALL_EXPRESSION = auto()
    METHOD_CALL_EXPRESSION = auto()
    CAST_EXPRESSION = auto()
    PARENTHESIZED_EXPRESSION = auto()

    # ─── Literal Types ────────────────────────────────────────────────────────
    INTEGER_LITERAL = auto()
    REAL_LITERAL = auto()
    STRING_LITERAL = auto()
    BOOLEAN_LITERAL = auto()
    NULL_LITERAL = auto()
    DATE_LITERAL = auto()
    TIME_LITERAL = auto()

    # ─── Type Types ───────────────────────────────────────────────────────────
    BASIC_TYPE = auto()
    ARRAY_TYPE = auto()
    CUSTOM_TYPE = auto()
    ENUMERATED_TYPE = auto()

    # ─── Object Types ─────────────────────────────────────────────────────────
    WINDOW = auto()
    USER_OBJECT = auto()
    MENU = auto()
    DATAWINDOW = auto()
    STRUCTURE = auto()

    # ─── Control Types ────────────────────────────────────────────────────────
    CONTROL = auto()
    BUTTON_CONTROL = auto()
    EDIT_CONTROL = auto()
    STATIC_TEXT_CONTROL = auto()
    CHECKBOX_CONTROL = auto()
    RADIOBUTTON_CONTROL = auto()
    LISTBOX_CONTROL = auto()
    DROPDOWNLIST_CONTROL = auto()
    COMBOBOX_CONTROL = auto()
    PICTURE_CONTROL = auto()
    GROUPBOX_CONTROL = auto()
    TREEVIEW_CONTROL = auto()
    LISTVIEW_CONTROL = auto()
    RICHTEXT_CONTROL = auto()
    DATAWINDOW_CONTROL = auto()
    TAB_CONTROL = auto()

    # ─── SQL Types ────────────────────────────────────────────────────────────
    SQL_STATEMENT = auto()
    SQL_SELECT = auto()
    SQL_INSERT = auto()
    SQL_UPDATE = auto()
    SQL_DELETE = auto()
    SQL_CURSOR = auto()
    SQL_PROCEDURE = auto()
    SQL_TRANSACTION = auto()
    SQL_QUERY = auto()
    SQL_COMMIT = auto()
    SQL_ROLLBACK = auto()
    SQL_PREPARE = auto()
    SQL_VARIABLE = auto()
    SQL_PARAMETER = auto()

    # ─── DataWindow Types ─────────────────────────────────────────────────────
    DW_COLUMN = auto()
    DW_COMPUTE = auto()
    DW_TABLE = auto()
    DW_GRAPH = auto()
    DW_CROSSTAB = auto()
    DW_NESTED = auto()

    # ─── Event Types ──────────────────────────────────────────────────────────
    EVENT = auto()
    EVENT_TRIGGER = auto()
    EVENT_POST = auto()
    SYSTEM_EVENT = auto()
    USER_EVENT = auto()

    # ─── Behavioral Types ─────────────────────────────────────────────────────
    BEHAVIORAL = auto()
    BEHAVIORAL_OPTION = auto()
    BEHAVIORAL_ALIAS = auto()
    BEHAVIORAL_LIBRARY = auto()

    # ─── Modifier Types ───────────────────────────────────────────────────────
    ACCESS_MODIFIER = auto()
    ARGUMENT_MODIFIER = auto()

    # ─── Other Types ──────────────────────────────────────────────────────────
    COMMENT = auto()
    ATTRIBUTE = auto()
    PARAMETER = auto()
    ARGUMENT = auto()
    IMPORT = auto()
    EXPORT = auto()
    LIBRARY = auto()

    def is_statement(self) -> bool:
        """Check if this node kind represents a statement."""
        return self.name.endswith("_STATEMENT") or self in {
            NodeKind.FOR_LOOP,
            NodeKind.WHILE_LOOP,
            NodeKind.DO_WHILE_LOOP,
            NodeKind.DO_UNTIL_LOOP,
            NodeKind.REPEAT_UNTIL_LOOP,
        }

    def is_expression(self) -> bool:
        """Check if this node kind represents an expression."""
        return self.name.endswith("_EXPRESSION") or self.name.endswith("_LITERAL")

    def is_declaration(self) -> bool:
        """Check if this node kind represents a declaration."""
        return self.name.endswith("_DECLARATION")

    def is_control(self) -> bool:
        """Check if this node kind represents a UI control."""
        return self.name.endswith("_CONTROL") or self == NodeKind.CONTROL

    def is_type(self) -> bool:
        """Check if this node kind represents a type."""
        return self.name.endswith("_TYPE") and self not in {
            NodeKind.EVENT_TYPE,
            NodeKind.SYSTEM_EVENT,
            NodeKind.USER_EVENT,
        }

    def is_sql(self) -> bool:
        """Check if this node kind represents SQL-related node."""
        return self.name.startswith("SQL_")

    def is_datawindow(self) -> bool:
        """Check if this node kind represents DataWindow-related node."""
        return self.name.startswith("DW_") or self == NodeKind.DATAWINDOW
