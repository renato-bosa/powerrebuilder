"""Additional AST nodes for PowerBuilder.

This module contains additional AST node implementations that were missing
from the core AST structure, including enumerations, compound assignments,
SQL operations, and PowerBuilder-specific constructs.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from src.base import PBNode

from .nodes.base import Expression, Statement
from .node_kind import NodeKind

# ─── Declaration Nodes ────────────────────────────────────────────────────────

@dataclass
class EnumerationDeclaration(Statement):
    """Enumeration declaration node."""

    name: str = ""
    values: list[EnumerationValue] = field(default_factory=list)
    access: str = "public"  # public, private, protected

    def __post_init__(self) -> None:
        """  post init  .
        """


        if not self.name:
            raise ValueError("EnumerationDeclaration requires name")
        self.node_kind = NodeKind.TYPE_DECLARATION

    def accept(self, visitor):




        """Accept a visitor."""
        return visitor.visit_enumeration_declaration(self)


@dataclass
class EnumerationValue(PBNode):
    """Single value in an enumeration."""

    name: str = ""
    value: int | None = None  # If not specified, auto-increment from previous

    def __post_init__(self) -> None:
        """  post init  .
        """


        if not self.name:
            raise ValueError("EnumerationValue requires name")


@dataclass 
class GlobalVariableDeclaration(Statement):
    """Global variable declaration with scoping."""

    name: str = ""
    type_name: str = ""
    initial_value: Expression | None = None
    is_constant: bool = False
    access: str = "public"  # public, private, protected

    def __post_init__(self) -> None:
        """  post init  .
        """


        if not self.name:
            raise ValueError("GlobalVariableDeclaration requires name")
        if not self.type_name:
            raise ValueError("GlobalVariableDeclaration requires type_name")
        self.node_kind = NodeKind.GLOBAL_DECLARATION

    def accept(self, visitor):




        """Accept a visitor."""
        return visitor.visit_global_variable_declaration(self)


@dataclass
class SharedVariableDeclaration(Statement):
    """Shared variable declaration (class-level static)."""

    name: str = ""
    type_name: str = ""
    initial_value: Expression | None = None
    is_constant: bool = False
    access: str = "public"

    def __post_init__(self) -> None:
        """  post init  .
        """


        if not self.name:
            raise ValueError("SharedVariableDeclaration requires name")
        if not self.type_name:
            raise ValueError("SharedVariableDeclaration requires type_name")
        self.node_kind = NodeKind.SHARED_DECLARATION

    def accept(self, visitor):




        """Accept a visitor."""
        return visitor.visit_shared_variable_declaration(self)


@dataclass
class ForwardDeclarationEnd(Statement):
    """End of forward declaration section."""

    def __post_init__(self) -> None:
        """  post init  .
        """


        self.node_kind = NodeKind.FORWARD_DECLARATION

    def accept(self, visitor):




        """Accept a visitor."""
        return visitor.visit_forward_declaration_end(self)


# ─── Statement Nodes ──────────────────────────────────────────────────────────

@dataclass
class CreateStatement(Statement):
    """CREATE statement for object instantiation."""

    target: Expression = None
    type_name: str | None = None
    using_expr: Expression | None = None  # For CREATE USING

    def __post_init__(self) -> None:
        """  post init  .
        """


        if self.target is None:
            raise ValueError("CreateStatement requires target")
        self.node_kind = NodeKind.STATEMENT

    def accept(self, visitor):




        """Accept a visitor."""
        return visitor.visit_create_statement(self)


@dataclass 
class DestroyStatement(Statement):
    """DESTROY statement for object destruction."""

    target: Expression = None

    def __post_init__(self) -> None:
        """  post init  .
        """


        if self.target is None:
            raise ValueError("DestroyStatement requires target")
        self.node_kind = NodeKind.STATEMENT

    def accept(self, visitor):




        """Accept a visitor."""
        return visitor.visit_destroy_statement(self)


@dataclass
class CallStatement(Statement):
    """CALL statement for procedure/event invocation."""

    target: str = ""  # Procedure/event name
    object_expr: Expression | None = None  # Object to call on
    arguments: list[Expression] = field(default_factory=list)
    is_dynamic: bool = False

    def __post_init__(self) -> None:
        """  post init  .
        """


        if not self.target:
            raise ValueError("CallStatement requires target")
        self.node_kind = NodeKind.STATEMENT

    def accept(self, visitor):




        """Accept a visitor."""
        return visitor.visit_call_statement(self)


@dataclass
class CompoundAssignment(Statement):
    """Compound assignment operators (+=, -=, *=, /=)."""

    target: Expression = None
    operator: str = ""  # +=, -=, *=, /=, etc.
    value: Expression = None

    def __post_init__(self) -> None:
        """  post init  .
        """


        if self.target is None:
            raise ValueError("CompoundAssignment requires target")
        if not self.operator:
            raise ValueError("CompoundAssignment requires operator")
        if self.value is None:
            raise ValueError("CompoundAssignment requires value")
        self.node_kind = NodeKind.ASSIGNMENT_STATEMENT

    def accept(self, visitor):




        """Accept a visitor."""
        return visitor.visit_compound_assignment(self)


# ─── SQL/Database Nodes ───────────────────────────────────────────────────────

@dataclass
class OpenCursorStatement(Statement):
    """OPEN cursor statement for SQL cursors."""

    cursor_name: str = ""
    using_transaction: Expression | None = None

    def __post_init__(self) -> None:
        """  post init  .
        """


        if not self.cursor_name:
            raise ValueError("OpenCursorStatement requires cursor_name")
        self.node_kind = NodeKind.SQL_CURSOR

    def accept(self, visitor):




        """Accept a visitor."""
        return visitor.visit_open_cursor_statement(self)


@dataclass
class FetchCursorStatement(Statement):
    """FETCH cursor statement for retrieving data."""

    cursor_name: str = ""
    into_variables: list[str] = field(default_factory=list)

    def __post_init__(self) -> None:
        """  post init  .
        """


        if not self.cursor_name:
            raise ValueError("FetchCursorStatement requires cursor_name")
        if not self.into_variables:
            raise ValueError("FetchCursorStatement requires into_variables")
        self.node_kind = NodeKind.SQL_CURSOR

    def accept(self, visitor):




        """Accept a visitor."""
        return visitor.visit_fetch_cursor_statement(self)


@dataclass
class ExecuteImmediateStatement(Statement):
    """EXECUTE IMMEDIATE for dynamic SQL."""

    sql_expression: Expression = None
    into_variables: list[str] = field(default_factory=list)
    using_variables: list[Expression] = field(default_factory=list)

    def __post_init__(self) -> None:
        """  post init  .
        """


        if self.sql_expression is None:
            raise ValueError("ExecuteImmediateStatement requires sql_expression")
        self.node_kind = NodeKind.SQL_STATEMENT

    def accept(self, visitor):




        """Accept a visitor."""
        return visitor.visit_execute_immediate_statement(self)


@dataclass
class DeclareProcedureStatement(Statement):
    """DECLARE stored procedure statement."""

    procedure_name: str = ""
    parameters: list[ProcedureParameter] = field(default_factory=list)

    def __post_init__(self) -> None:
        """  post init  .
        """


        if not self.procedure_name:
            raise ValueError("DeclareProcedureStatement requires procedure_name")
        self.node_kind = NodeKind.SQL_PROCEDURE

    def accept(self, visitor):




        """Accept a visitor."""
        return visitor.visit_declare_procedure_statement(self)


@dataclass
class ExecuteProcedureStatement(Statement):
    """EXECUTE stored procedure statement."""

    procedure_name: str = ""
    arguments: list[Expression] = field(default_factory=list)
    using_transaction: Expression | None = None

    def __post_init__(self) -> None:
        """  post init  .
        """


        if not self.procedure_name:
            raise ValueError("ExecuteProcedureStatement requires procedure_name")
        self.node_kind = NodeKind.SQL_PROCEDURE

    def accept(self, visitor):




        """Accept a visitor."""
        return visitor.visit_execute_procedure_statement(self)


@dataclass
class ProcedureParameter(PBNode):
    """Parameter for stored procedure declaration."""

    name: str = ""
    type_name: str = ""
    direction: str = "IN"  # IN, OUT, INOUT

    def __post_init__(self) -> None:
        """  post init  .
        """


        if not self.name:
            raise ValueError("ProcedureParameter requires name")
        if not self.type_name:
            raise ValueError("ProcedureParameter requires type_name")


# ─── Expression Nodes ─────────────────────────────────────────────────────────

@dataclass
class InExpression(Expression):
    """SQL IN operator expression."""

    value: Expression = None
    in_list: list[Expression] = field(default_factory=list)
    is_not_in: bool = False

    def __post_init__(self) -> None:
        """  post init  .
        """


        if self.value is None:
            raise ValueError("InExpression requires value")
        if not self.in_list:
            raise ValueError("InExpression requires in_list")
        self.node_kind = NodeKind.BINARY_EXPRESSION

    def accept(self, visitor):




        """Accept a visitor."""
        return visitor.visit_in_expression(self)


@dataclass
class LikeExpression(Expression):
    """SQL LIKE pattern matching expression."""

    value: Expression = None
    pattern: Expression = None
    escape_char: str | None = None
    is_not_like: bool = False

    def __post_init__(self) -> None:
        """  post init  .
        """


        if self.value is None:
            raise ValueError("LikeExpression requires value")
        if self.pattern is None:
            raise ValueError("LikeExpression requires pattern")
        self.node_kind = NodeKind.BINARY_EXPRESSION

    def accept(self, visitor):




        """Accept a visitor."""
        return visitor.visit_like_expression(self)


@dataclass
class ExistsExpression(Expression):
    """SQL EXISTS subquery expression."""

    subquery: Expression = None  # Should be a SelectStatement
    is_not_exists: bool = False

    def __post_init__(self) -> None:
        """  post init  .
        """


        if self.subquery is None:
            raise ValueError("ExistsExpression requires subquery")
        self.node_kind = NodeKind.UNARY_EXPRESSION

    def accept(self, visitor):




        """Accept a visitor."""
        return visitor.visit_exists_expression(self)


@dataclass
class BetweenExpression(Expression):
    """SQL BETWEEN range expression."""

    value: Expression = None
    lower_bound: Expression = None
    upper_bound: Expression = None
    is_not_between: bool = False

    def __post_init__(self) -> None:
        """  post init  .
        """


        if self.value is None:
            raise ValueError("BetweenExpression requires value")
        if self.lower_bound is None:
            raise ValueError("BetweenExpression requires lower_bound")
        if self.upper_bound is None:
            raise ValueError("BetweenExpression requires upper_bound")
        self.node_kind = NodeKind.BINARY_EXPRESSION

    def accept(self, visitor):




        """Accept a visitor."""
        return visitor.visit_between_expression(self)


# ─── PowerBuilder-Specific Nodes ──────────────────────────────────────────────

@dataclass
class DynamicMethodInvocation(Expression):
    """Dynamic method invocation using string name."""

    object_expr: Expression = None
    method_name: Expression = None  # String expression
    arguments: list[Expression] = field(default_factory=list)

    def __post_init__(self) -> None:
        """  post init  .
        """


        if self.object_expr is None:
            raise ValueError("DynamicMethodInvocation requires object_expr")
        if self.method_name is None:
            raise ValueError("DynamicMethodInvocation requires method_name")
        self.node_kind = NodeKind.METHOD_CALL_EXPRESSION

    def accept(self, visitor):




        """Accept a visitor."""
        return visitor.visit_dynamic_method_invocation(self)


@dataclass
class ExportStatement(Statement):
    """EXPORT statement for DataWindow/data export."""

    source: Expression = None  # DataWindow or data source
    file_path: Expression = None
    format: str = "TEXT"  # TEXT, CSV, XML, etc.
    options: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        """  post init  .
        """


        if self.source is None:
            raise ValueError("ExportStatement requires source")
        if self.file_path is None:
            raise ValueError("ExportStatement requires file_path")
        self.node_kind = NodeKind.EXPORT

    def accept(self, visitor):




        """Accept a visitor."""
        return visitor.visit_export_statement(self)


@dataclass
class ImportStatement(Statement):
    """IMPORT statement for DataWindow/data import."""

    target: Expression = None  # DataWindow or data target
    file_path: Expression = None
    format: str = "TEXT"
    options: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        """  post init  .
        """


        if self.target is None:
            raise ValueError("ImportStatement requires target")
        if self.file_path is None:
            raise ValueError("ImportStatement requires file_path")
        self.node_kind = NodeKind.IMPORT

    def accept(self, visitor):




        """Accept a visitor."""
        return visitor.visit_import_statement(self)


@dataclass
class DescriptorNode(PBNode):
    """Descriptor for dynamic property/method access."""

    name: str = ""
    type_name: str = ""
    attributes: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        """  post init  .
        """


        if not self.name:
            raise ValueError("DescriptorNode requires name")


@dataclass
class OleAutomationNode(Statement):
    """OLE/ActiveX automation node."""

    object_name: str = ""
    method_name: str = ""
    arguments: list[Expression] = field(default_factory=list)
    return_value: str | None = None  # Variable to store return

    def __post_init__(self) -> None:
        """  post init  .
        """


        if not self.object_name:
            raise ValueError("OleAutomationNode requires object_name")
        if not self.method_name:
            raise ValueError("OleAutomationNode requires method_name")
        self.node_kind = NodeKind.STATEMENT

    def accept(self, visitor):




        """Accept a visitor."""
        return visitor.visit_ole_automation_node(self)


@dataclass
class DescribeStatement(Statement):
    """SQL DESCRIBE statement for dynamic SQL metadata."""

    sql_statement: str = ""  # Statement identifier
    into_descriptor: str = ""  # SQLDA variable

    def __post_init__(self) -> None:
        """  post init  .
        """


        if not self.sql_statement:
            raise ValueError("DescribeStatement requires sql_statement")
        if not self.into_descriptor:
            raise ValueError("DescribeStatement requires into_descriptor")
        self.node_kind = NodeKind.SQL_STATEMENT

    def accept(self, visitor):




        """Accept a visitor."""
        return visitor.visit_describe_statement(self)


# ─── Metadata/Documentation Nodes ─────────────────────────────────────────────

@dataclass
class CommentNode(PBNode):
    """Comment node for preserving comments in AST."""

    text: str = ""
    is_multiline: bool = False
    is_documentation: bool = False  # True for doc comments

    def __post_init__(self) -> None:
        """  post init  .
        """


        self.node_kind = NodeKind.COMMENT

    def accept(self, visitor):




        """Accept a visitor."""
        return visitor.visit_comment_node(self)


@dataclass
class AttributeNode(PBNode):
    """Attribute/annotation node for metadata."""

    name: str = ""
    arguments: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        """  post init  .
        """


        if not self.name:
            raise ValueError("AttributeNode requires name")
        self.node_kind = NodeKind.ATTRIBUTE

    def accept(self, visitor):




        """Accept a visitor."""
        return visitor.visit_attribute_node(self)


@dataclass
class LibraryReference(PBNode):
    """Library reference for external dependencies."""

    library_name: str = ""
    alias: str | None = None
    functions: list[str] = field(default_factory=list)  # Imported functions

    def __post_init__(self) -> None:
        """  post init  .
        """


        if not self.library_name:
            raise ValueError("LibraryReference requires library_name")
        self.node_kind = NodeKind.LIBRARY

    def accept(self, visitor):




        """Accept a visitor."""
        return visitor.visit_library_reference(self)


# Export all new node classes
__all__ = [
    # Declaration nodes
    "EnumerationDeclaration", "EnumerationValue", "GlobalVariableDeclaration", "SharedVariableDeclaration", "ForwardDeclarationEnd", # Statement nodes
    "CreateStatement", "DestroyStatement", "CallStatement", "CompoundAssignment", # SQL nodes
    "OpenCursorStatement", "FetchCursorStatement", "ExecuteImmediateStatement", "DeclareProcedureStatement", "ExecuteProcedureStatement", "ProcedureParameter", # Expression nodes
    "InExpression", "LikeExpression", "ExistsExpression", "BetweenExpression", # PowerBuilder-specific nodes
    "DynamicMethodInvocation", "ExportStatement", "ImportStatement", "DescriptorNode", "OleAutomationNode", "DescribeStatement", # Metadata nodes
    "CommentNode", "AttributeNode", "LibraryReference", ]
