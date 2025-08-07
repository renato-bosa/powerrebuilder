"""SQL AST transformer.

This module provides the transformer class that converts SQL parse trees (from sql.lark)
into detailed SQL AST nodes defined in model.ast.nodes.
"""

from __future__ import annotations

import logging
from typing import Any

from lark import Token, Transformer, Tree

from src.model.ast.nodes.base import Expression, Identifier
from src.model.ast.nodes.literals import (
    NumberLiteral,
    NullLiteral,
    StringLiteral,
)

# Type alias for return type compatibility
Literal = Expression
from src.model.ast.nodes.sql import (
    CaseExpression as SQLCase,
    ColumnReference as SQLColumn,
    DeleteStatement as SQLDeleteStatement,
    SubqueryExpression as SQLSubquery,
    SelectStatement as SQLSelectStatement,
    InsertStatement as SQLInsertStatement,
    UpdateStatement as SQLUpdateStatement,
    TableReference as SQLTable,
    JoinClause as SQLJoin,
    WhereClause as SQLWhereClause,
    GroupByClause as SQLGroupBy,
    HavingClause as SQLHaving,
    OrderByClause as SQLOrderBy,
    WithClause as SQLWith,
    CaseWhenClause as SQLWhen,
)

# Create aliases for missing classes to avoid breaking existing code
# These represent SQL concepts that may not be fully implemented yet
class SQLExpression:
    """Placeholder for general SQL expressions."""
    pass

class SQLFunction:
    """Placeholder for SQL function calls."""
    
    def __init__(self):
        self.name: str = ""
        self.arguments: list[Any] = []

class SQLIntoClause:
    """Placeholder for INSERT INTO clauses."""
    
    def __init__(self):
        self.table: Any = None
        self.columns: list[Any] = []

class SQLSet:
    """Placeholder for UPDATE SET clauses."""
    
    def __init__(self):
        self.assignments: list[Any] = []

class SQLUnion:
    """Placeholder for UNION operations."""
    
    def __init__(self):
        self.left: Any = None
        self.right: Any = None
        self.union_all: bool = False

class SQLValues:
    """Placeholder for VALUES clauses."""
    
    def __init__(self):
        self.rows: list[Any] = []

logger = logging.getLogger(__name__)


class SQLTransformer(Transformer[Any]):
    """Transforms a Lark parse tree (generated from sql.lark) into a detailed SQL AST."""

    def __init__(self, visit_tokens: bool = True) -> None:
        super().__init__(visit_tokens)

    def _create_literal(self, value: Any, literal_type: str | None = None) -> Literal:
        """Create the appropriate literal based on value and type."""
        if literal_type == "null" or value is None:
            return NullLiteral()
        if literal_type == "number":
            # Determine if it's an integer or real number
            value_str = str(value)
            try:
                # Try to parse as integer first
                if "." not in value_str and "e" not in value_str.lower():
                    int_value = int(value_str)
                    return NumberLiteral(value=int_value)
                # It's a float/real number
                float_value = float(value_str)
                return NumberLiteral(value=float_value)
            except ValueError:
                # Fallback to string literal if parsing fails
                return StringLiteral(value=value_str)
        elif literal_type in [
            "string",
            "text",
            "wildcard",
            "type_name",
            "placeholder",
            "list",
        ]:
            lit = StringLiteral(value=str(value))
            lit.type = literal_type  # Set the type attribute
            return lit
        else:
            # Default to string literal
            return StringLiteral(value=str(value))

    def select_statement(self, items: list[Any]) -> SQLSelectStatement:
        """Transform SELECT statement."""
        stmt = SQLSelectStatement()

        for item in items:
            if isinstance(item, dict):
                if item.get("type") == "columns":
                    stmt.result_columns = item.get("columns", [])
                elif item.get("type") == "from":
                    stmt.from_clause = item.get("tables", [])
                elif item.get("type") == "where":
                    stmt.where_clause = item.get("condition")
                elif item.get("type") == "order_by":
                    stmt.order_by_clause = item.get("items", [])
                elif item.get("type") == "group_by":
                    stmt.group_by_clause = item.get("items", [])
                elif item.get("type") == "having":
                    stmt.having_clause = item.get("condition")

        return stmt

    def insert_statement(self, items: list[Any]) -> SQLInsertStatement:
        """Transform INSERT statement."""
        stmt = SQLInsertStatement()

        for item in items:
            if isinstance(item, dict):
                if item.get("type") == "table":
                    stmt.table = item.get("table")
                elif item.get("type") == "columns":
                    stmt.columns = item.get("columns", [])
                elif item.get("type") == "values":
                    stmt.values = item.get("values", [])
                elif item.get("type") == "select":
                    stmt.select_statement = item.get("select")

        return stmt

    def update_statement(self, items: list[Any]) -> SQLUpdateStatement:
        """Transform UPDATE statement."""
        stmt = SQLUpdateStatement()

        for item in items:
            if isinstance(item, dict):
                if item.get("type") == "table":
                    stmt.table = item.get("table")
                elif item.get("type") == "set":
                    stmt.assignments = item.get("assignments", [])
                elif item.get("type") == "where":
                    stmt.where_clause = item.get("condition")

        return stmt

    def delete_statement(self, items: list[Any]) -> SQLDeleteStatement:
        """Transform DELETE statement."""
        stmt = SQLDeleteStatement()

        for item in items:
            if isinstance(item, dict):
                if item.get("type") == "from":
                    stmt.from_clause = item.get("table")
                elif item.get("type") == "where":
                    stmt.where_clause = item.get("condition")

        return stmt

    def column(self, items: list[Any]) -> SQLColumn:
        """Transform column reference."""
        if len(items) == 1:
            # Simple column name
            return SQLColumn(column_name=str(items[0]))
        if len(items) == 2:
            # Table.column
            return SQLColumn(table_name=str(items[0]), column_name=str(items[1]))
        if len(items) >= 3:
            # Schema.table.column or alias
            col = SQLColumn(
                column_name=str(items[2]), table_name=f"{str(items[0])}.{str(items[1])}"
            )
            if len(items) > 3:
                col.alias = str(items[3])
            return col
        return SQLColumn(column_name="unknown")

    def table(self, items: list[Any]) -> SQLTable:
        """Transform table reference."""
        if len(items) == 1:
            # Simple table name
            return SQLTable(name=str(items[0]))
        if len(items) == 2:
            # Schema.table or table alias
            if isinstance(items[1], Token) and items[1].type == "IDENTIFIER":
                return SQLTable(name=str(items[0]), alias=str(items[1]))
            return SQLTable(schema=str(items[0]), name=str(items[1]))
        if len(items) >= 3:
            # Schema.table alias
            return SQLTable(
                schema=str(items[0]), name=str(items[1]), alias=str(items[2])
            )
        return SQLTable(name="unknown")

    def where_clause(self, items: list[Any]) -> SQLWhereClause:
        """Transform WHERE clause."""
        if items:
            return SQLWhereClause(condition=items[0])
        return SQLWhereClause()

    def sql_expression(self, items: list[Any]) -> SQLExpression:
        """Transform SQL expression."""
        if len(items) == 1:
            return SQLExpression(value=items[0])
        if len(items) == 3:
            # Binary expression
            return SQLExpression(left=items[0], operator=str(items[1]), right=items[2])
        return SQLExpression(value=items)

    def join_clause(self, items: list[Any]) -> SQLJoin:
        """Transform JOIN clause."""
        join = SQLJoin()
        join_type = "INNER"

        for item in items:
            if isinstance(item, Token):
                token_str = str(item).upper()
                if token_str in ["LEFT", "RIGHT", "FULL", "INNER", "OUTER", "CROSS"]:
                    join_type = token_str
            elif isinstance(item, SQLTable):
                join.table = item
            elif isinstance(item, SQLExpression):
                join.on_condition = item

        join.join_operator = join_type
        return join

    def order_by_clause(self, items: list[Any]) -> SQLOrderBy:
        """Transform ORDER BY clause."""
        order_by = SQLOrderBy()

        for item in items:
            if isinstance(item, dict) and item.get("type") == "order_item":
                order_by.terms.append(item)
            elif isinstance(item, SQLColumn):
                order_by.terms.append({"column": item, "direction": "ASC"})

        return order_by

    def group_by_clause(self, items: list[Any]) -> SQLGroupBy:
        """Transform GROUP BY clause."""
        group_by = SQLGroupBy()

        for item in items:
            if isinstance(item, SQLColumn):
                group_by.expressions.append(item)

        return group_by

    def having_clause(self, items: list[Any]) -> SQLHaving:
        """Transform HAVING clause."""
        if items:
            return SQLHaving(condition=items[0])
        return SQLHaving()

    def sql_function(self, items: list[Any]) -> SQLFunction:
        """Transform SQL function call."""
        func = SQLFunction()

        for item in items:
            if isinstance(item, Token) and item.type == "IDENTIFIER":
                func.name = str(item)
            elif isinstance(item, list):
                func.arguments = item

        return func

    def subquery(self, items: list[Any]) -> SQLSubquery:
        """Transform subquery."""
        if items and isinstance(items[0], SQLSelectStatement):
            return SQLSubquery(select=items[0])
        return SQLSubquery()

    def case_expression(self, items: list[Any]) -> SQLCase:
        """Transform CASE expression."""
        case = SQLCase()

        for item in items:
            if isinstance(item, dict):
                if item.get("type") == "case_value":
                    case.expression = item.get("value")
                elif item.get("type") == "when":
                    case.when_clauses.append(item)
                elif item.get("type") == "else":
                    case.else_clause = item.get("value")

        return case

    def when_clause(self, items: list[Any]) -> SQLWhen:
        """Transform WHEN clause."""
        when = SQLWhen()

        if len(items) >= 2:
            when.condition = items[0]
            when.result = items[1]

        return when

    def with_clause(self, items: list[Any]) -> SQLWith:
        """Transform WITH clause (CTE)."""
        with_clause = SQLWith()

        for item in items:
            if isinstance(item, dict) and item.get("type") == "cte":
                with_clause.ctes.append(item)

        return with_clause

    def union_clause(self, items: list[Any]) -> SQLUnion:
        """Transform UNION clause."""
        union = SQLUnion()

        if len(items) >= 2:
            union.left = items[0]
            union.right = items[1]

            # Check for UNION ALL
            for item in items:
                if isinstance(item, Token) and str(item).upper() == "ALL":
                    union.union_all = True
                    break

        return union

    def into_clause(self, items: list[Any]) -> SQLIntoClause:
        """Transform INTO clause."""
        into = SQLIntoClause()

        for item in items:
            if isinstance(item, SQLTable):
                into.table = item
            elif isinstance(item, list):
                into.columns = item

        return into

    def values_clause(self, items: list[Any]) -> SQLValues:
        """Transform VALUES clause."""
        values = SQLValues()

        for item in items:
            if isinstance(item, list):
                values.rows.append(item)

        return values

    def set_clause(self, items: list[Any]) -> SQLSet:
        """Transform SET clause."""
        set_clause = SQLSet()

        for item in items:
            if isinstance(item, dict) and item.get("type") == "assignment":
                set_clause.assignments.append(item)

        return set_clause

    def identifier(self, items: list[Any]) -> Identifier:
        """Transform identifier."""
        if items:
            return Identifier(name=str(items[0]))
        return Identifier(name="unknown")

    def number(self, items: list[Any]) -> Literal:
        """Transform number literal."""
        if items:
            return self._create_literal(items[0], "number")
        return NumberLiteral(value=0)

    def string(self, items: list[Any]) -> StringLiteral:
        """Transform string literal."""
        if items:
            # Remove quotes if present
            value = str(items[0])
            if len(value) >= 2 and value[0] in ["'", '"'] and value[-1] == value[0]:
                value = value[1:-1]
            return StringLiteral(value=value)
        return StringLiteral(value="")

    def null(self, items: list[Any]) -> NullLiteral:
        """Transform NULL literal."""
        return NullLiteral()

    def star(self, items: list[Any]) -> SQLColumn:
        """Transform * (star) column."""
        return SQLColumn(name="*")

    def sql_comment(self, items: list[Any]) -> dict:
        """Transform SQL comment."""
        if items:
            return {"type": "comment", "text": str(items[0])}
        return {"type": "comment", "text": ""}

    def placeholder(self, items: list[Any]) -> dict:
        """Transform placeholder (?, :param)."""
        if items:
            return {"type": "placeholder", "name": str(items[0])}
        return {"type": "placeholder", "name": "?"}

    def __default__(self, data: str, children: list[Any], meta: Any):
        """Default handler for unrecognized rules."""
        logger.debug("Unhandled rule: %s", data)
        return Tree(data, children, meta)
