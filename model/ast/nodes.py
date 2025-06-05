"""Abstract Syntax Tree nodes for PowerBuilder.

This module contains all AST node classes for representing PowerBuilder code structure.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from ..utils.base import PBNode
from .node_kind import NodeKind

# Import types that are used in this module but defined elsewhere
from .types import Type
from .functions import Function, Parameter


# ─── Base AST Nodes ─────────────────────────────────────────────────────
@dataclass
class Expression(PBNode):
    """Base class for all expressions."""

    @property
    def kind(self) -> NodeKind:
        """Get the node kind for expression."""
        return NodeKind.EXPRESSION


@dataclass
class Statement(PBNode):
    """Base class for all statements."""

    @property
    def kind(self) -> NodeKind:
        """Get the node kind for statement."""
        return NodeKind.STATEMENT


# ─── Event Nodes ───────────────────────────────────────────────────────
@dataclass
class Event(Statement):
    """Event declaration or trigger."""

    name: str
    parameters: list[Parameter] = field(default_factory=list)
    body: list[Statement] = field(default_factory=list)

    @property
    def kind(self) -> NodeKind:
        """Get the node kind for event."""
        return NodeKind.EVENT


@dataclass
class EventTrigger(Statement):
    """Event trigger statement."""

    event: Event
    arguments: list[Argument] = field(default_factory=list)

    @property
    def kind(self) -> NodeKind:
        """Get the node kind for event trigger."""
        return NodeKind.EVENT_TRIGGER


# ─── Expression Nodes ────────────────────────────────────────────────────
@dataclass
class Literal(Expression):
    """Literal value expression."""

    value: str
    type: str  # number, string, boolean, etc.

    @property
    def kind(self) -> NodeKind:
        """Get the node kind for literal."""
        type_map = {
            "number": NodeKind.INTEGER_LITERAL,
            "integer": NodeKind.INTEGER_LITERAL,
            "real": NodeKind.REAL_LITERAL,
            "float": NodeKind.REAL_LITERAL,
            "string": NodeKind.STRING_LITERAL,
            "boolean": NodeKind.BOOLEAN_LITERAL,
            "bool": NodeKind.BOOLEAN_LITERAL,
            "date": NodeKind.DATE_LITERAL,
            "time": NodeKind.TIME_LITERAL,
            "null": NodeKind.NULL_LITERAL,
        }
        return type_map.get(self.type.lower(), NodeKind.LITERAL_EXPRESSION)


@dataclass
class BinaryExpression(Expression):
    """Binary operator expression."""

    left: Expression
    operator: str
    right: Expression

    @property
    def kind(self) -> NodeKind:
        """Get the node kind for binary expression."""
        return NodeKind.BINARY_EXPRESSION


@dataclass
class UnaryExpression(Expression):
    """Unary operator expression."""

    operator: str
    operand: Expression

    @property
    def kind(self) -> NodeKind:
        """Get the node kind for unary expression."""
        return NodeKind.UNARY_EXPRESSION


# Note: Function, Parameter, and Argument classes are defined in ast/functions.py


# Note: Type and CustomType classes are defined in ast/types.py


# ─── Variable Nodes ─────────────────────────────────────────────────────
@dataclass
class Variable(Expression):
    """Variable reference."""

    name: str
    type: Type | None = None


@dataclass
class VariableDeclaration(Statement):
    """Variable declaration."""

    name: str
    type: Type
    initial_value: Expression | None = None


# ─── SQL Nodes ─────────────────────────────────────────────────────────
@dataclass
class SQLQuery(Statement):
    """SQL query statement."""

    query: str
    using_clause: str | None = None


@dataclass
class SQLCursor(Statement):
    """SQL cursor declaration."""

    name: str
    query: SQLQuery | str
    is_dynamic: bool = False


@dataclass
class SQLTransaction(Statement):
    """SQL transaction statement."""

    action: str  # commit, rollback
    using_clause: str | None = None


@dataclass
class SqlParameter(Expression):
    """Base class for SQL parameter markers."""

    name: str | None = field(
        default=None,
        metadata={
            "description": "Name of the parameter, if applicable (e.g., for :variable style).",
        },
    )
    position: int | None = field(
        default=None,
        metadata={"description": "Positional index of the parameter, if applicable."},
    )
    node_type: str = field(default="SqlParameter", init=False)


@dataclass
class QuestionMarkParameter(SqlParameter):
    """Represents a '?' SQL parameter marker."""

    node_type: str = field(default="QuestionMarkParameter", init=False)


@dataclass
class ColonParameter(SqlParameter):
    """Represents a ':variable' SQL parameter marker."""

    node_type: str = field(default="ColonParameter", init=False)


# ─── Detailed SQL AST Nodes ────────────────────────────────────────────
# These nodes are for representing the parsed structure of SQL queries from sql.lark


@dataclass
class SqlStatement(Statement):
    """Base class for all detailed SQL statements."""

    pass


@dataclass
class SelectStatement(SqlStatement):
    """Represents a SELECT SQL statement."""

    distinct_clause: str | None = None  # "DISTINCT" or "ALL"
    result_columns: list[ResultColumn] = field(default_factory=list)
    from_clause: FromClause | None = None
    where_clause: WhereClause | None = None
    group_by_clause: GroupByClause | None = None
    having_clause: HavingClause | None = None
    order_by_clause: OrderByClause | None = None
    limit_clause: LimitClause | None = None
    with_clause: WithClause | None = None  # For CTEs
    node_type: str = field(default="SelectStatement", init=False)


@dataclass
class ResultColumn(PBNode):
    """Represents a column or expression in the SELECT list."""

    expression: Expression
    alias: str | None = None
    table_name: str | None = None  # For table.*
    node_type: str = field(default="ResultColumn", init=False)


@dataclass
class FromClause(PBNode):
    """Represents the FROM clause of a SELECT statement."""

    tables: list[TableReference | SubqueryExpression] = field(
        default_factory=list,
    )
    joins: list[JoinClause] = field(
        default_factory=list,
    )  # Joins are part of the from_clause conceptually
    node_type: str = field(default="FromClause", init=False)


@dataclass
class TableReference(
    Expression,
):  # Inherits from Expression as it can be a source in FROM
    """Represents a reference to a table."""

    table_name: str
    alias: str | None = None
    node_type: str = field(default="TableReference", init=False)


@dataclass
class JoinClause(PBNode):
    """Represents a JOIN clause."""

    join_operator: str  # e.g., "JOIN", "LEFT JOIN", "INNER JOIN"
    table: TableReference | SubqueryExpression
    on_condition: Expression | None = None
    using_columns: list[str] | None = None
    node_type: str = field(default="JoinClause", init=False)


@dataclass
class WhereClause(PBNode):
    """Represents a WHERE clause."""

    condition: Expression
    node_type: str = field(default="WhereClause", init=False)


@dataclass
class GroupByClause(PBNode):
    """Represents a GROUP BY clause."""

    expressions: list[Expression] = field(default_factory=list)
    node_type: str = field(default="GroupByClause", init=False)


@dataclass
class HavingClause(PBNode):
    """Represents a HAVING clause."""

    condition: Expression
    node_type: str = field(default="HavingClause", init=False)


@dataclass
class OrderByClause(PBNode):
    """Represents an ORDER BY clause."""

    terms: list[OrderingTerm] = field(default_factory=list)
    node_type: str = field(default="OrderByClause", init=False)


@dataclass
class OrderingTerm(PBNode):
    """Represents a term in the ORDER BY clause."""

    expression: Expression
    direction: str | None = None  # "ASC" or "DESC"
    nulls: str | None = None  # "FIRST" or "LAST"
    node_type: str = field(default="OrderingTerm", init=False)


@dataclass
class LimitClause(PBNode):
    """Represents a LIMIT clause."""

    limit: Expression
    offset: Expression | None = None
    node_type: str = field(default="LimitClause", init=False)


@dataclass
class SubqueryExpression(
    Expression,
):  # A subquery that acts as an expression or table source
    """Represents a subquery, often used in FROM or WHERE clauses."""

    query: SelectStatement  # Or a more general SqlStatement if other types can be subqueried
    alias: str | None = None  # If the subquery is aliased (e.g., in FROM clause)
    node_type: str = field(default="SubqueryExpression", init=False)


# Placeholder for other SQL statement types
@dataclass
class InsertStatement(SqlStatement):
    """Represents an INSERT SQL statement. (Placeholder - to be detailed)."""

    table: TableReference
    columns: list[str] | None = None  # List of column names
    values: list[list[Expression]] | None = (
        None  # For VALUES clause, list of rows, each row is list of expressions
    )
    select_statement: SelectStatement | None = None  # For INSERT INTO ... SELECT
    node_type: str = field(default="InsertStatement", init=False)


@dataclass
class UpdateStatement(SqlStatement):
    """Represents an UPDATE SQL statement. (Placeholder - to be detailed)."""

    table: TableReference
    assignments: list[Assignment] = field(default_factory=list)  # e.g., column = expr
    where_clause: WhereClause | None = None
    node_type: str = field(default="UpdateStatement", init=False)


@dataclass
class DeleteStatement(SqlStatement):
    """Represents a DELETE SQL statement. (Placeholder - to be detailed)."""

    table: TableReference
    where_clause: WhereClause | None = None
    node_type: str = field(default="DeleteStatement", init=False)


@dataclass
class Assignment(PBNode):  # Could be a common node if not already defined
    """Represents an assignment 'target = value' used in UPDATE SET."""

    target_column: str  # Or ColumnReference node
    value: Expression
    node_type: str = field(default="Assignment", init=False)


# For CTEs (Common Table Expressions)
@dataclass
class WithClause(PBNode):
    expressions: list[WithExpression] = field(default_factory=list)
    node_type: str = field(default="WithClause", init=False)


@dataclass
class WithExpression(PBNode):
    name: str
    query: SelectStatement  # Moved before 'columns'
    columns: list[str] | None = None
    node_type: str = field(default="WithExpression", init=False)


# General Expression Nodes (Ensure these are compatible with SQL needs or extend them)
# Existing Literal, BinaryExpression, UnaryExpression, Variable, FunctionCall might be reusable.
# Need to ensure FunctionCall can represent SQL functions.
# Variable might represent column names if not explicitly typed as ColumnReference.


# Potentially add a ColumnReference(Expression) if 'Variable' is too generic
@dataclass
class ColumnReference(Expression):
    column_name: str
    table_name: str | None = None  # For table.column
    node_type: str = field(default="ColumnReference", init=False)


# Ensure all new nodes are available if this file is imported directly
# (This might be handled by an __all__ in __init__.py later)
