"""SQL query optimization for PowerBuilder.

This module provides SQL query optimization functionality for converting
PowerBuilder SQL to efficient Dart database queries.
"""

from __future__ import annotations
from typing import Any
import copy
import logging

from src.model.ast.nodes.sql import (
    SelectStatement, UpdateStatement, DeleteStatement, InsertStatement,
    SetOperationStatement, WhereClause, Expression, BinaryExpression, 
    UnaryExpression, BooleanOperation, SubqueryExpression, Literal,
    ResultColumn
)

logger = logging.getLogger(__name__)


class SQLOptimizer:
    """SQL query optimizer for PowerBuilder statements."""

    def optimize(self, sql_statement: Any) -> Any:
        """Optimize an SQL statement.

        Applies various optimizations:
        - Remove redundant DISTINCT
        - Simplify WHERE conditions
        - Optimize subqueries
        - Remove unnecessary ORDER BY in subqueries
        - Simplify redundant expressions

        Args:
            sql_statement: The SQL statement to optimize

        Returns:
            The optimized SQL statement
        """
        # Create a deep copy to avoid modifying the original
        optimized = copy.deepcopy(sql_statement)

        # Apply optimizations based on statement type
        if isinstance(optimized, SelectStatement):
            optimized = self._optimize_select(optimized)
        elif isinstance(optimized, UpdateStatement):
            optimized = self._optimize_update(optimized)
        elif isinstance(optimized, DeleteStatement):
            optimized = self._optimize_delete(optimized)
        elif isinstance(optimized, InsertStatement):
            optimized = self._optimize_insert(optimized)
        elif isinstance(optimized, SetOperationStatement):
            optimized = self._optimize_set_operation(
                optimized)

        return optimized

    def _optimize_select(self, stmt: SelectStatement) -> SelectStatement:
        """Optimize a SELECT statement."""
        # Optimize WHERE clause
        if stmt.where_clause:
            stmt.where_clause = self._optimize_where_clause(stmt.where_clause)

        # Remove redundant DISTINCT if we have GROUP BY on all columns
        if stmt.distinct_clause == "DISTINCT" and stmt.group_by_clause:
            # Check if GROUP BY includes all result columns
            if self._group_by_covers_all_columns(stmt):
                stmt.distinct_clause = None

        # Optimize subqueries in FROM clause
        if stmt.from_clause:
            stmt.from_clause = self._optimize_from_clause(
                stmt.from_clause)

        # Remove ORDER BY if this is a subquery (unless LIMIT is present)
        # This will be handled at a higher level

        # Optimize result columns
        stmt.result_columns = self._optimize_result_columns(
        stmt.result_columns)

        return stmt

    def _optimize_update(self, stmt: UpdateStatement) -> UpdateStatement:
        """Optimize an UPDATE statement."""
        if stmt.where_clause:
            stmt.where_clause = self._optimize_where_clause(stmt.where_clause)
        return stmt

    def _optimize_delete(self, stmt: DeleteStatement) -> DeleteStatement:
        """Optimize a DELETE statement."""
        if stmt.where_clause:
            stmt.where_clause = self._optimize_where_clause(stmt.where_clause)
        return stmt

    def _optimize_insert(self, stmt: InsertStatement) -> InsertStatement:
        """Optimize an INSERT statement."""
        # Optimize SELECT in INSERT ... SELECT
        if stmt.select_statement:
            stmt.select_statement = self._optimize_select(
                stmt.select_statement)
        return stmt

    def _optimize_set_operation(
        self,
        stmt: SetOperationStatement) -> SetOperationStatement:
        """Optimize a set operation (UNION, INTERSECT, EXCEPT)."""
        if stmt.left:
            if isinstance(stmt.left, SelectStatement):
                stmt.left = self._optimize_select(stmt.left)
            elif isinstance(stmt.left, SetOperationStatement):
                stmt.left = self._optimize_set_operation(stmt.left)

        if stmt.right:
            if isinstance(stmt.right, SelectStatement):
                stmt.right = self._optimize_select(stmt.right)
            elif isinstance(stmt.right, SetOperationStatement):
                stmt.right = self._optimize_set_operation(
                    stmt.right)

        # Convert UNION to UNION ALL if we know there are no duplicates
        if stmt.operator == "UNION" and self._can_use_union_all(
                stmt):
            stmt.operator = "UNION ALL"

        return stmt

    def _optimize_where_clause(self, where: WhereClause) -> WhereClause:
        """Optimize a WHERE clause."""
        if where.condition:
            where.condition = self._optimize_expression(where.condition)
        return where

    def _optimize_expression(self, expr: Expression) -> Expression:
        """Optimize an expression by simplifying it."""
        if isinstance(expr, BinaryExpression):
            # Check if it's a comparison operation
            if expr.operator in ['=', '!=', '<>', '<', '>', '<=', '>=']:
                return self._optimize_comparison(expr)
            else:
                return self._optimize_binary_operation(expr)
        elif isinstance(expr, UnaryExpression):
            return self._optimize_unary_operation(expr)
        elif isinstance(expr, BooleanOperation):
            return self._optimize_logical_operation(expr)
        elif isinstance(expr, SubqueryExpression):
            return self._optimize_subquery_expression(expr)

        return expr

    def _optimize_binary_operation(self, op: BinaryExpression) -> Expression:
        """Optimize binary operations."""
        # Optimize operands first
        op.left = self._optimize_expression(op.left)
        op.right = self._optimize_expression(op.right)

        # Constant folding
        if isinstance(op.left, Literal) and isinstance(op.right, Literal):
            result = self._evaluate_binary_op(op.operator, op.left, op.right)
            if result is not None:
                return result

        # Identity operations
        if op.operator == "+" and isinstance(op.right, Literal) and op.right.value == 0:
            return op.left
        if op.operator == "+" and isinstance(op.left, Literal) and op.left.value == 0:
            return op.right
        if op.operator == "*" and isinstance(op.right, Literal) and op.right.value == 1:
            return op.left
        if op.operator == "*" and isinstance(op.left, Literal) and op.left.value == 1:
            return op.right

        return op

    def _optimize_unary_operation(self, op: UnaryExpression) -> Expression:
        """Optimize unary operations."""
        op.operand = self._optimize_expression(op.operand)

        # Double negation elimination
        if (op.operator == "NOT" and isinstance(op.operand, UnaryExpression) 
            and op.operand.operator == "NOT"):
            return op.operand.operand

        # Constant folding
        if isinstance(op.operand, Literal):
            result = self._evaluate_unary_op(op.operator, op.operand)
            if result is not None:
                return result

        return op

    def _optimize_comparison(self, comp: BinaryExpression) -> Expression:
        """Optimize comparison operations."""
        comp.left = self._optimize_expression(comp.left)
        comp.right = self._optimize_expression(comp.right)

        # Constant comparison
        if isinstance(comp.left, Literal) and isinstance(comp.right, Literal):
            result = self._evaluate_comparison(
                comp.operator, comp.left, comp.right)
            if result is not None:
                return Literal(value=result)

        # NULL comparisons
        if (comp.operator in ["=", "!=", "<>"] and isinstance(comp.right, Literal) 
            and comp.right.value is None):
            # Convert = NULL to IS NULL, != NULL to IS NOT NULL
            if comp.operator == "=":
                return UnaryExpression(
                    operator="IS NULL", operand=comp.left)
            else:
                return UnaryExpression(
                    operator="IS NOT NULL", operand=comp.left)

        return comp

    def _optimize_logical_operation(
        self, logic: BooleanOperation) -> Expression:
        """Optimize logical operations (AND, OR)."""
        # Optimize operands
        optimized_operands = [
            self._optimize_expression(op) for op in logic.operands]

        # Remove always-true conditions from AND
        if logic.operator == "AND":
            filtered = [
                op for op in optimized_operands if not self._is_always_true(op)]
            if not filtered:
                return Literal(value=True)
            if len(filtered) == 1:
                return filtered[0]
            logic.operands = filtered

        # Remove always-false conditions from OR
        elif logic.operator == "OR":
            filtered = [
                op for op in optimized_operands if not self._is_always_false(op)]
            if not filtered:
                return Literal(value=False)
            if len(filtered) == 1:
                return filtered[0]
            # Check if any condition is always true
            if any(self._is_always_true(op) for op in filtered):
                return Literal(value=True)
            logic.operands = filtered

        return logic

    def _optimize_subquery_expression(
        self, subquery: SubqueryExpression) -> SubqueryExpression:
        """Optimize a subquery expression."""
        if subquery.query:
            # Remove ORDER BY from subqueries unless they have LIMIT
            if isinstance(subquery.query, SelectStatement):
                if subquery.query.order_by_clause and not subquery.query.limit_clause:
                    subquery.query.order_by_clause = None
                # Recursively optimize the subquery
                subquery.query = self._optimize_select(subquery.query)

        return subquery

    def _optimize_from_clause(self, from_clause) -> Any:
        """Optimize FROM clause including joins."""
        # Optimize subqueries in FROM
        for i, table in enumerate(from_clause.tables):
            if isinstance(table, SubqueryExpression):
                from_clause.tables[i] = self._optimize_subquery_expression(table)

        # Optimize join conditions
        for join in from_clause.joins:
            if join.on_condition:
                join.on_condition = self._optimize_expression(join.on_condition)

        return from_clause

    def _optimize_result_columns(
        self, columns: list[ResultColumn]) -> list[ResultColumn]:
        """Optimize result columns."""
        for col in columns:
            if col.expression:
                col.expression = self._optimize_expression(col.expression)
        return columns

    def _group_by_covers_all_columns(self, stmt: SelectStatement) -> bool:
        """Check if GROUP BY covers all non-aggregate columns."""
        # This is a simplified check - in practice would need more
        # sophisticated analysis
        return False

    def _can_use_union_all(self, stmt: SetOperationStatement) -> bool:
        """Check if UNION can be converted to UNION ALL."""
        # This requires analyzing if the result sets are guaranteed to be distinct
        # For now, return False to be safe
        return False

    def _is_always_true(self, expr: Expression) -> bool:
        """Check if an expression is always true."""
        if isinstance(expr, Literal):
            return bool(expr.value)
        if isinstance(expr, BinaryExpression) and expr.operator in ['=', '!=', '<>', '<', '>', '<=', '>=']:
            # Check for tautologies like 1 = 1
            if isinstance(expr.left, Literal) and isinstance(expr.right, Literal):
                return self._evaluate_comparison(expr.operator, expr.left, expr.right)
        return False

    def _is_always_false(self, expr: Expression) -> bool:
        """Check if an expression is always false."""
        if isinstance(expr, Literal):
            return not bool(expr.value)
        if isinstance(expr, BinaryExpression) and expr.operator in ['=', '!=', '<>', '<', '>', '<=', '>=']:
            # Check for contradictions like 1 = 2
            if isinstance(expr.left, Literal) and isinstance(expr.right, Literal):
                return self._evaluate_comparison(expr.operator, expr.left, expr.right) == False
        return False

    def _evaluate_binary_op(
        self,
        operator: str,
        left: Literal,
        right: Literal) -> Literal | None:
        """Evaluate a binary operation on literals."""
        try:
            if operator == "+":
                return Literal(value=left.value + right.value)
            elif operator == "-":
                return Literal(value=left.value - right.value)
            elif operator == "*":
                return Literal(value=left.value * right.value)
            elif operator == "/" and right.value != 0:
                return Literal(value=left.value / right.value)
        except Exception as e:
            logger.debug("Exception caught: %s", e)
        return None

    def _evaluate_unary_op(
        self,
        operator: str,
        operand: Literal) -> Literal | None:
        """Evaluate a unary operation on a literal."""
        try:
            if operator == "-":
                return Literal(value=-operand.value)
            elif operator == "NOT":
                return Literal(value=not operand.value)
        except Exception as e:
            logger.debug("Exception caught: %s", e)
        return None

    def _evaluate_comparison(
        self,
        operator: str,
        left: Literal,
        right: Literal) -> bool | None:
        """Evaluate a comparison between literals."""
        try:
            if operator == "=":
                return left.value == right.value
            elif operator in ["!=", "<>"]:
                return left.value != right.value
            elif operator == "<":
                return left.value < right.value
            elif operator == "<=":
                return left.value <= right.value
            elif operator == ">":
                return left.value > right.value
            elif operator == ">=":
                return left.value >= right.value
        except Exception as e:
            logger.debug("Exception caught: %s", e)
        return None

def optimize_sql(sql_statement: Any) -> Any:
    """Optimize an SQL statement.

    Args:
        sql_statement: The SQL statement to optimize

    Returns:
        The optimized SQL statement
    """
    optimizer = SQLOptimizer()
    return optimizer.optimize(sql_statement)
