"""SQL AST nodes for PowerBuilder.

This module contains all SQL-related AST nodes for representing SQL statements,
queries, cursors, and transactions in PowerBuilder code.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from src.model.types.base import PBNode

from .base import Expression, Statement
from ..node_kind import NodeKind
from ..literals import Literal, BinaryExpression, UnaryExpression, Identifier
from ..functions import FunctionCall


# ─── Basic SQL Nodes ────────────────────────────────────────────────────
@dataclass
class SQLQuery(Statement):
    """SQL query statement."""

    query: str = ""
    using_clause: str | None = None

    @property
    def kind(self) -> NodeKind:


        """Get the node kind."""
        return NodeKind.SQL_QUERY


class SQLCursor(Statement):
    """SQL cursor declaration."""

    name: str = ""
    query: SQLQuery | str = ""
    is_dynamic: bool = False

    @property
    def kind(self) -> NodeKind:


        """Get the node kind."""
        return NodeKind.SQL_CURSOR


class SQLTransaction(Statement):
    """SQL transaction statement."""

    action: str = ""  # commit, rollback
    using_clause: str | None = None

    @property
    def kind(self) -> NodeKind:


        """Get the node kind."""
        return NodeKind.SQL_TRANSACTION


class SQLCommit(Statement):
    """SQL COMMIT statement."""

    using_clause: str | None = None

    @property
    def kind(self) -> NodeKind:


        """Get the node kind."""
        return NodeKind.SQL_COMMIT


class SQLRollback(Statement):
    """SQL ROLLBACK statement."""

    using_clause: str | None = None
    savepoint: str | None = None

    @property
    def kind(self) -> NodeKind:


        """Get the node kind."""
        return NodeKind.SQL_ROLLBACK


class SQLPrepare(Statement):
    """SQL PREPARE statement."""

    statement_name: str = ""
    query: str = ""
    using_clause: str | None = None

    @property
    def kind(self) -> NodeKind:


        """Get the node kind."""
        return NodeKind.SQL_PREPARE


class SQLVariable(Expression):
    """SQL variable reference."""

    name: str = ""
    indicator: str | None = None  # For null indicators

    @property
    def kind(self) -> NodeKind:


        """Get the node kind."""
        return NodeKind.SQL_VARIABLE


# ─── SQL Parameters ─────────────────────────────────────────────────────
@dataclass
class SqlParameter(Expression):
    """Base class for SQL parameter markers."""

    name: str | None = field(
        default=None, metadata={
            "description": "Name of the parameter, if applicable (e.g., for :variable style).", }, )
    position: int | None = field(
        default=None, metadata={"description": "Positional index of the parameter, if applicable."}, )
    node_type: str = field(default="SqlParameter", init=False)


class QuestionMarkParameter(SqlParameter):
    """Represents a '?' SQL parameter marker."""

    node_type: str = field(default="QuestionMarkParameter", init=False)


class ColonParameter(SqlParameter):
    """Represents a ':variable' SQL parameter marker."""

    node_type: str = field(default="ColonParameter", init=False)


# ─── Detailed SQL AST Nodes ────────────────────────────────────────────
# These nodes are for representing the parsed structure of SQL queries


class SqlStatement(Statement):
    """Base class for all detailed SQL statements."""


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


class SetOperationStatement(SqlStatement):
    """Represents a SQL statement with set operations (UNION, INTERSECT, EXCEPT)."""

    left: SelectStatement | SetOperationStatement | None = None
    operator: str = ""  # "UNION", "UNION ALL", "INTERSECT", "INTERSECT ALL", "EXCEPT"
    right: SelectStatement | SetOperationStatement | None = None
    order_by_clause: OrderByClause | None = None
    limit_clause: LimitClause | None = None
    with_clause: WithClause | None = None  # For CTEs at the top level
    node_type: str = field(default="SetOperationStatement", init=False)


class ResultColumn(PBNode):
    """Represents a column or expression in the SELECT list."""

    expression: Expression | None = None
    alias: str | None = None
    table_name: str | None = None  # For table.*
    node_type: str = field(default="ResultColumn", init=False)


class FromClause(PBNode):
    """Represents the FROM clause of a SELECT statement."""

    tables: list[TableReference | SubqueryExpression] = field(
        default_factory=list, )
    joins: list[JoinClause] = field(
        default_factory=list, )  # Joins are part of the from_clause conceptually
    node_type: str = field(default="FromClause", init=False)


# Alias for backward compatibility
SQLFromClause = FromClause


class TableReference(Expression):
    """Represents a reference to a table."""

    table_name: str = ""
    alias: str | None = None
    node_type: str = field(default="TableReference", init=False)


class JoinClause(PBNode):
    """Represents a JOIN clause."""

    join_operator: str = ""  # e.g., "JOIN", "LEFT JOIN", "INNER JOIN"
    table: TableReference | SubqueryExpression | None = None
    on_condition: Expression | None = None
    using_columns: list[str] | None = None
    node_type: str = field(default="JoinClause", init=False)


class WhereClause(PBNode):
    """Represents a WHERE clause."""

    condition: Expression | None = None
    node_type: str = field(default="WhereClause", init=False)


class GroupByClause(PBNode):
    """Represents a GROUP BY clause."""

    expressions: list[Expression] = field(default_factory=list)
    node_type: str = field(default="GroupByClause", init=False)


class HavingClause(PBNode):
    """Represents a HAVING clause."""

    condition: Expression | None = None
    node_type: str = field(default="HavingClause", init=False)


class OrderByClause(PBNode):
    """Represents an ORDER BY clause."""

    terms: list[OrderingTerm] = field(default_factory=list)
    node_type: str = field(default="OrderByClause", init=False)


class OrderingTerm(PBNode):
    """Represents a term in the ORDER BY clause."""

    expression: Expression | None = None
    direction: str | None = None  # "ASC" or "DESC"
    nulls: str | None = None  # "FIRST" or "LAST"
    node_type: str = field(default="OrderingTerm", init=False)


class LimitClause(PBNode):
    """Represents a LIMIT clause."""

    limit: Expression | None = None
    offset: Expression | None = None
    node_type: str = field(default="LimitClause", init=False)


class SubqueryExpression(Expression):
    """Represents a subquery, often used in FROM or WHERE clauses."""

    query: SelectStatement | None = (
        None  # Or a more general SqlStatement if other types can be subqueried
    )
    alias: str | None = None  # If the subquery is aliased (e.g., in FROM clause)
    node_type: str = field(default="SubqueryExpression", init=False)


# ─── DML Statements ─────────────────────────────────────────────────────
@dataclass
class InsertStatement(SqlStatement):
    """Represents an INSERT SQL statement."""

    table: TableReference | None = None
    columns: list[str] | None = None  # List of column names
    values: list[list[Expression]] | None = None  # For VALUES clause
    select_statement: SelectStatement | None = None  # For INSERT INTO ... SELECT
    node_type: str = field(default="InsertStatement", init=False)


class UpdateStatement(SqlStatement):
    """Represents an UPDATE SQL statement."""

    table: TableReference | None = None
    assignments: list[Assignment] = field(default_factory=list)
    where_clause: WhereClause | None = None
    node_type: str = field(default="UpdateStatement", init=False)


class DeleteStatement(SqlStatement):
    """Represents a DELETE SQL statement."""

    table: TableReference | None = None
    from_clause: FromClause | None = None
    where_clause: WhereClause | None = None
    node_type: str = field(default="DeleteStatement", init=False)


class Assignment(PBNode):
    """Represents an assignment 'target = value' used in UPDATE SET."""

    target_column: str = ""  # Or ColumnReference node
    value: Expression | None = None
    node_type: str = field(default="Assignment", init=False)


# ─── Common Table Expressions (CTEs) ────────────────────────────────────
@dataclass
class WithClause(PBNode):
    """Represents a WITH clause for CTEs."""

    expressions: list[WithExpression] = field(default_factory=list)
    node_type: str = field(default="WithClause", init=False)


class WithExpression(PBNode):
    """Represents a single CTE in a WITH clause."""

    query: SelectStatement | None = None
    columns: list[str] | None = None
    node_type: str = field(default="WithExpression", init=False)

    def __init__(self, name: str = "", query: SelectStatement | None = None, columns: list[str] | None = None):
        super().__init__()
        self.name = name  # Use inherited property
        self.query = query
        self.columns = columns


# ─── Column References ──────────────────────────────────────────────────
@dataclass
class ColumnReference(Expression):
    """Represents a reference to a column."""

    column_name: str = ""
    table_name: str | None = None  # For table.column
    alias: str | None = None  # For column AS alias
    node_type: str = field(default="ColumnReference", init=False)


# ─── Additional SQL Expression Nodes ───────────────────────────────────────

@dataclass
class BooleanOperation(Expression):
    """Represents a boolean operation (AND, OR) with multiple operands."""
    
    operator: str = ""  # "AND" or "OR"
    operands: list[Expression] = field(default_factory=list)
    node_type: str = field(default="BooleanOperation", init=False)


@dataclass
class CaseExpression(Expression):
    """Represents a SQL CASE expression."""
    
    expression: Expression | None = None  # Expression to evaluate (for simple CASE)
    when_clauses: list['CaseWhenClause'] = field(default_factory=list)
    else_clause: Expression | None = None
    node_type: str = field(default="CaseExpression", init=False)


@dataclass
class CaseWhenClause(PBNode):
    """Represents a WHEN clause in a CASE expression."""
    
    condition: Expression | None = None  # For searched CASE
    value: Expression | None = None      # For simple CASE
    result: Expression | None = None
    node_type: str = field(default="CaseWhenClause", init=False)
