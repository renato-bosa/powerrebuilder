"""SQL AST transformer.

This module provides the transformer class that converts SQL parse trees (from sql.lark)
into detailed SQL AST nodes defined in model.ast.nodes.sql.
"""

from __future__ import annotations

import logging
from typing import Any

from lark import Token, Transformer, Tree

from src.model.ast.literals import (
    IntegerLiteral,
    Literal,
    NullLiteral,
    RealLiteral,
    StringLiteral,
)
from src.model.ast.nodes.base import Expression
from src.model.ast.nodes.sql import (
    ColumnReference,
    FromClause,
    GroupByClause,
    HavingClause,
    JoinClause,
    LimitClause,
    OrderByClause,
    OrderingTerm,
    ResultColumn,
    SelectStatement,
    SubqueryExpression,
    TableReference,
    WhereClause,
)

logger = logging.getLogger(__name__)


class SQLTransformer(Transformer):
    """Transforms a Lark parse tree (generated from sql.lark) into detailed SQL AST."""

    def __init__(self, visit_tokens: bool = True) -> None:
        super().__init__(visit_tokens)

    def sql_statements(self, items: list[Any]) -> list[Any]:
        """Transform multiple SQL statements."""
        statements = []
        for item in items:
            if item is not None:
                statements.append(item)
        return statements

    def sql_statement(self, items: list[Any]) -> Any:
        """Transform a single SQL statement."""
        if items:
            return items[0]
        return None

    def select_statement(self, items: list[Any]) -> SelectStatement:
        """Transform SELECT statement."""
        stmt = SelectStatement()

        for item in items:
            if isinstance(item, Tree):
                if item.data == "distinct_clause":
                    stmt.distinct_clause = "DISTINCT"
                elif item.data == "result_columns":
                    stmt.result_columns = self._process_result_columns(item)
                elif item.data == "from_clause":
                    stmt.from_clause = self.transform(item)
                elif item.data == "where_clause":
                    stmt.where_clause = self.transform(item)
                elif item.data == "group_by_clause":
                    stmt.group_by_clause = self.transform(item)
                elif item.data == "having_clause":
                    stmt.having_clause = self.transform(item)
                elif item.data == "order_by_clause":
                    stmt.order_by_clause = self.transform(item)
                elif item.data == "limit_clause":
                    stmt.limit_clause = self.transform(item)
            elif isinstance(item, list):
                # Handle result columns if passed as list
                if all(isinstance(col, (ResultColumn, Tree)) for col in item):
                    stmt.result_columns = item

        return stmt

    def _process_result_columns(self, tree: Tree) -> list[ResultColumn]:
        """Process result columns from tree."""
        columns = []
        for child in tree.children:
            if isinstance(child, Tree):
                col = self.transform(child)
                if isinstance(col, ResultColumn):
                    columns.append(col)
            elif isinstance(child, ResultColumn):
                columns.append(child)
        return columns

    def result_column(self, items: list[Any]) -> ResultColumn:
        """Transform result column."""
        col = ResultColumn()

        if len(items) == 1:
            # Single expression or wildcard
            item = items[0]
            if isinstance(item, Token) and item.value == "*":
                col.expression = Literal(value="*", type="wildcard")
            else:
                col.expression = item
        elif len(items) == 2:
            # Expression with alias
            col.expression = items[0]
            if isinstance(items[1], Token):
                col.alias = str(items[1])
            else:
                col.alias = str(items[1])
        elif len(items) == 3 and isinstance(items[1], Token) and items[1].value == ".":
            # table.* format
            col.table_name = str(items[0])
            col.expression = Literal(value="*", type="wildcard")

        return col

    def from_clause(self, items: list[Any]) -> FromClause:
        """Transform FROM clause."""
        clause = FromClause()

        for item in items:
            if isinstance(item, (TableReference, SubqueryExpression)):
                clause.tables.append(item)
            elif isinstance(item, JoinClause):
                clause.joins.append(item)
            elif isinstance(item, Tree):
                # Process tree items
                transformed = self.transform(item)
                if isinstance(transformed, TableReference):
                    clause.tables.append(transformed)
                elif isinstance(transformed, JoinClause):
                    clause.joins.append(transformed)

        return clause

    def table_reference(self, items: list[Any]) -> TableReference:
        """Transform table reference."""
        ref = TableReference()

        if len(items) == 1:
            # Simple table name
            ref.table_name = str(items[0])
        elif len(items) == 2:
            # Table with alias
            ref.table_name = str(items[0])
            ref.alias = str(items[1])

        return ref

    def where_clause(self, items: list[Any]) -> WhereClause:
        """Transform WHERE clause."""
        clause = WhereClause()
        if items:
            clause.condition = items[0]
        return clause

    def group_by_clause(self, items: list[Any]) -> GroupByClause:
        """Transform GROUP BY clause."""
        clause = GroupByClause()
        for item in items:
            if isinstance(item, (ColumnReference, Expression)):
                clause.expressions.append(item)
        return clause

    def having_clause(self, items: list[Any]) -> HavingClause:
        """Transform HAVING clause."""
        clause = HavingClause()
        if items:
            clause.condition = items[0]
        return clause

    def order_by_clause(self, items: list[Any]) -> OrderByClause:
        """Transform ORDER BY clause."""
        clause = OrderByClause()
        for item in items:
            if isinstance(item, OrderingTerm):
                clause.terms.append(item)
        return clause

    def ordering_term(self, items: list[Any]) -> OrderingTerm:
        """Transform ordering term."""
        term = OrderingTerm()

        if items:
            term.expression = items[0]

            # Look for ASC/DESC
            for item in items[1:]:
                if isinstance(item, Token):
                    token_upper = str(item).upper()
                    if token_upper in ("ASC", "DESC"):
                        term.direction = token_upper
                    elif token_upper == "NULLS":
                        # Look for FIRST/LAST
                        idx = items.index(item)
                        if idx + 1 < len(items):
                            next_token = str(items[idx + 1]).upper()
                            if next_token in ("FIRST", "LAST"):
                                term.nulls = next_token

        return term

    def limit_clause(self, items: list[Any]) -> LimitClause:
        """Transform LIMIT clause."""
        clause = LimitClause()

        if len(items) >= 1:
            clause.limit = items[0]
        if len(items) >= 2:
            clause.offset = items[1]

        return clause

    def column_reference(self, items: list[Any]) -> ColumnReference:
        """Transform column reference."""
        ref = ColumnReference()

        if len(items) == 1:
            # Simple column name
            ref.column_name = str(items[0])
        elif len(items) == 3 and str(items[1]) == ".":
            # table.column
            ref.table_name = str(items[0])
            ref.column_name = str(items[2])

        return ref

    def identifier(self, items: list[Any]) -> str:
        """Transform identifier to string."""
        if items:
            return str(items[0])
        return ""

    def number(self, items: list[Any]) -> Literal:
        """Transform number literal."""
        if items:
            value_str = str(items[0])
            try:
                if "." not in value_str and "e" not in value_str.lower():
                    return IntegerLiteral(value=int(value_str))
                return RealLiteral(value=float(value_str))
            except ValueError:
                return StringLiteral(value=value_str)
        return IntegerLiteral(value=0)

    def string_literal(self, items: list[Any]) -> StringLiteral:
        """Transform string literal."""
        if items:
            # Remove quotes
            value = str(items[0])
            if value.startswith(("'", '"')) and value.endswith(("'", '"')):
                value = value[1:-1]
            return StringLiteral(value=value)
        return StringLiteral(value="")

    def null_literal(self, items: list[Any]) -> NullLiteral:
        """Transform NULL literal."""
        return NullLiteral()

    # Add more transformation methods as needed for other SQL constructs

    def __default__(self, data: str, children: list[Any], meta: Any):
        """Default handler for unhandled rules."""
        # For debugging
        logger.debug("Unhandled rule: %s", data)
        # Return first child if only one, otherwise return children
        if len(children) == 1:
            return children[0]
        return children
