"""SQL query optimizer.

This module provides optimization passes for SQL queries, including:
- Redundant DISTINCT removal
- WHERE clause simplification
- Dead code elimination
- Basic query rewriting
"""

from __future__ import annotations

import logging
from typing import Any

from model.ast import (
    BinaryExpression,
    BooleanLiteral,
    ColumnReference,
    Expression,
    FromClause,
    IntegerLiteral,
    Literal,
    SelectStatement,
    SetOperationStatement,
    SqlStatement,
    StringLiteral,
    TableReference,
    WhereClause,
)
logger = logging.getLogger(__name__)


class SQLOptimizer:
    """SQL query optimizer that applies various optimization passes."""

    def __init__(self) -> None:
        """Initialize the SQL optimizer."""
        self.optimizations_applied = 0
        self.optimization_log = []

    def visit(self, node: Any) -> Any:
        """Visit a node and dispatch to the appropriate handler."""
        if node is None:
            return None
        
        # Get the visitor method name
        method_name = f"visit_{type(node).__name__}"
        visitor = getattr(self, method_name, None)
        
        if visitor:
            return visitor(node)
        else:
            # Default: return node unchanged
            return node

    def optimize(self, sql_stmt: SqlStatement) -> SqlStatement:
        """Optimize a SQL statement.

        Args:
            sql_stmt: The SQL statement to optimize

        Returns:
            The optimized SQL statement
        """
        self.optimizations_applied = 0
        self.optimization_log = []
        
        # Apply optimization passes
        result = self.visit(sql_stmt)
        
        if self.optimizations_applied > 0:
            logger.info(
                f"Applied {self.optimizations_applied} SQL optimizations"
            )
            for msg in self.optimization_log:
                logger.debug(f"  - {msg}")
        
        return result if result else sql_stmt

    def visit_SelectStatement(self, node: SelectStatement) -> SelectStatement:
        """Optimize a SELECT statement."""
        # Optimize WHERE clause
        if node.where_clause:
            optimized_where = self._optimize_where_clause(node.where_clause)
            if optimized_where != node.where_clause:
                node.where_clause = optimized_where
                self._log_optimization("Optimized WHERE clause")
        
        # Remove redundant DISTINCT
        if node.distinct_clause == "DISTINCT":
            if self._can_remove_distinct(node):
                node.distinct_clause = None
                self._log_optimization("Removed redundant DISTINCT")
        
        # Optimize subqueries in FROM clause
        if node.from_clause:
            node.from_clause = self.visit(node.from_clause)
        
        return node

    def visit_SetOperationStatement(
        self, node: SetOperationStatement
    ) -> SetOperationStatement:
        """Optimize set operations."""
        # Optimize left and right sides
        if node.left:
            node.left = self.visit(node.left)
        if node.right:
            node.right = self.visit(node.right)
        
        # TODO: Add optimizations for set operations
        # - UNION ALL of identical queries -> single query
        # - INTERSECT with empty result set -> empty
        # - EXCEPT with identical queries -> empty
        
        return node

    def visit_WhereClause(self, node: WhereClause) -> WhereClause | None:
        """Optimize a WHERE clause."""
        if node.condition:
            optimized = self._optimize_expression(node.condition)
            
            # If condition is always true, remove WHERE clause
            if self._is_always_true(optimized):
                self._log_optimization("Removed WHERE clause (always true)")
                return None
            
            # If condition is always false, we could optimize the entire query
            # but for now just simplify the condition
            if self._is_always_false(optimized):
                node.condition = BooleanLiteral(value=False)
                self._log_optimization("Simplified WHERE clause to FALSE")
            else:
                node.condition = optimized
        
        return node

    def _optimize_where_clause(self, where_clause: WhereClause) -> WhereClause | None:
        """Optimize a WHERE clause, potentially removing it."""
        return self.visit_WhereClause(where_clause)

    def _optimize_expression(self, expr: Expression) -> Expression:
        """Optimize an expression recursively."""
        if isinstance(expr, BinaryExpression):
            return self._optimize_binary_expression(expr)
        elif isinstance(expr, Literal):
            return expr
        # TODO: Handle other expression types
        return expr

    def _optimize_binary_expression(self, expr: BinaryExpression) -> Expression:
        """Optimize a binary expression."""
        # First, optimize operands
        left = self._optimize_expression(expr.left)
        right = self._optimize_expression(expr.right)
        
        # Constant folding for comparisons
        if isinstance(left, Literal) and isinstance(right, Literal):
            result = self._evaluate_binary_op(left, expr.operator, right)
            if result is not None:
                self._log_optimization(
                    f"Constant folded: {left.value} {expr.operator} {right.value} -> {result}"
                )
                return BooleanLiteral(value=result)
        
        # Simplify comparisons with same column
        if (isinstance(left, ColumnReference) and 
            isinstance(right, ColumnReference) and
            left.column_name == right.column_name):
            if expr.operator in ("=", "<=", ">="):
                self._log_optimization(
                    f"Simplified: {left.column_name} {expr.operator} {left.column_name} -> TRUE"
                )
                return BooleanLiteral(value=True)
            elif expr.operator in ("!=", "<>", "<", ">"):
                self._log_optimization(
                    f"Simplified: {left.column_name} {expr.operator} {left.column_name} -> FALSE"
                )
                return BooleanLiteral(value=False)
        
        # Simplify AND/OR with boolean literals
        if expr.operator == "AND":
            if self._is_always_false(left) or self._is_always_false(right):
                return BooleanLiteral(value=False)
            if self._is_always_true(left):
                return right
            if self._is_always_true(right):
                return left
        elif expr.operator == "OR":
            if self._is_always_true(left) or self._is_always_true(right):
                return BooleanLiteral(value=True)
            if self._is_always_false(left):
                return right
            if self._is_always_false(right):
                return left
        
        # Return optimized expression
        expr.left = left
        expr.right = right
        return expr

    def _evaluate_binary_op(
        self, left: Literal, operator: str, right: Literal
    ) -> bool | None:
        """Evaluate a binary operation on literals."""
        try:
            left_val = left.value
            right_val = right.value
            
            # Handle numeric comparisons
            if isinstance(left, (IntegerLiteral, BooleanLiteral)) and \
               isinstance(right, (IntegerLiteral, BooleanLiteral)):
                # Convert booleans to int for comparison
                if isinstance(left, BooleanLiteral):
                    left_val = 1 if left_val else 0
                if isinstance(right, BooleanLiteral):
                    right_val = 1 if right_val else 0
                
                if operator == "=":
                    return left_val == right_val
                elif operator in ("!=", "<>"):
                    return left_val != right_val
                elif operator == "<":
                    return left_val < right_val
                elif operator == "<=":
                    return left_val <= right_val
                elif operator == ">":
                    return left_val > right_val
                elif operator == ">=":
                    return left_val >= right_val
            
            # Handle string comparisons
            elif isinstance(left, StringLiteral) and isinstance(right, StringLiteral):
                if operator == "=":
                    return left_val == right_val
                elif operator in ("!=", "<>"):
                    return left_val != right_val
            
        except Exception as e:
            logger.debug(f"Error evaluating {left} {operator} {right}: {e}")
        
        return None

    def _is_always_true(self, expr: Expression) -> bool:
        """Check if an expression is always true."""
        if isinstance(expr, BooleanLiteral):
            return expr.value
        if isinstance(expr, IntegerLiteral):
            return expr.value != 0
        return False

    def _is_always_false(self, expr: Expression) -> bool:
        """Check if an expression is always false."""
        if isinstance(expr, BooleanLiteral):
            return not expr.value
        if isinstance(expr, IntegerLiteral):
            return expr.value == 0
        return False

    def _can_remove_distinct(self, select_stmt: SelectStatement) -> bool:
        """Check if DISTINCT can be safely removed.
        
        DISTINCT can be removed when:
        - Selecting from a single table with a unique constraint
        - All selected columns form a unique key
        - The query already ensures uniqueness through GROUP BY
        """
        # For now, only remove DISTINCT when there's a GROUP BY
        # that covers all non-aggregate result columns
        if select_stmt.group_by_clause:
            # TODO: Implement proper check for GROUP BY coverage
            # For now, conservatively return False
            pass
        
        return False

    def _log_optimization(self, message: str) -> None:
        """Log an optimization that was applied."""
        self.optimizations_applied += 1
        self.optimization_log.append(message)


def optimize_sql(sql_stmt: SqlStatement) -> SqlStatement:
    """Convenience function to optimize a SQL statement.
    
    Args:
        sql_stmt: The SQL statement to optimize
        
    Returns:
        The optimized SQL statement
    """
    optimizer = SQLOptimizer()
    return optimizer.optimize(sql_stmt)