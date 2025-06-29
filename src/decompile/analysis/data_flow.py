"""Expression optimizer for PowerBuilder AST expressions.

This module provides optimization passes for expressions including:
- Constant folding
- Algebraic simplification
- Boolean expression optimization
- Dead code elimination
"""

import logging

from model.expressions import (Expression)
from model.expressions import (
    BinaryOperator,
    BooleanLiteral,
    NullLiteral,
    StringLiteral,
    UnaryOperator,
    Variable,
)

logger = logging.getLogger(__name__)


class ExpressionOptimizer:
    """Optimizes PowerBuilder expressions through various transformation passes."""

    def __init__(self) -> None:




        """Initialize the expression optimizer."""
        self.optimizations_applied = 0

    def optimize(self, expression: Expression) -> Expression:




        """Apply all optimization passes to an expression.

        Args:
            expression: The expression to optimize

        Returns:
            The optimized expression (may be the same object if no optimizations applied)
        """
        if not isinstance(expression, Expression):
            return expression

        # Reset counter for this optimization run
        self.optimizations_applied = 0

        # Apply optimization passes
        result = expression
        result = self._optimize_constants(result)
        result = self._optimize_algebraic(result)
        result = self._optimize_boolean(result)

        if self.optimizations_applied > 0:
            logger.debug("Applied %s optimizations", self.optimizations_applied)

        return result

    def _optimize_constants(self, expr: Expression) -> Expression:




        """Perform constant folding optimization.

        Args:
            expr: Expression to optimize

        Returns:
            Optimized expression
        """
        if isinstance(expr, PBBinaryOperator):
            # Recursively optimize operands
            left = self._optimize_constants(expr.left)
            right = self._optimize_constants(expr.right)

            # Check if both operands are literals
            if self._is_literal(left) and self._is_literal(right):
                result = self._fold_binary_constants(left, expr.operator, right)
                if result is not None:
                    self.optimizations_applied += 1
                    return result

            # Return expression with optimized operands
            if left is not expr.left or right is not expr.right:
                return PBBinaryOperator(left=left, operator=expr.operator, right=right)

        elif isinstance(expr, PBUnaryOperator):
            # Optimize operand
            operand = self._optimize_constants(expr.operand)

            # Check if operand is literal
            if self._is_literal(operand):
                result = self._fold_unary_constants(expr.operator, operand)
                if result is not None:
                    self.optimizations_applied += 1
                    return result

            # Return expression with optimized operand
            if operand is not expr.operand:
                return PBUnaryOperator(operator=expr.operator, operand=operand)

        elif isinstance(expr, PBConcatenationOperator):
            # Optimize operands
            operands = [self._optimize_constants(op) for op in expr.operands]

            # Try to fold string literals
            result = self._fold_concatenation(operands)
            if result is not None:
                self.optimizations_applied += 1
                return result

            # Return expression with optimized operands
            if operands != expr.operands:
                return PBConcatenationOperator(operands=operands)

        elif isinstance(expr, PBPowerOperator):
            # Optimize operands
            base = self._optimize_constants(expr.base)
            exponent = self._optimize_constants(expr.exponent)

            # Check if both are literals
            if self._is_literal(base) and self._is_literal(exponent):
                result = self._fold_power_constants(base, exponent)
                if result is not None:
                    self.optimizations_applied += 1
                    return result

            # Return expression with optimized operands
            if base is not expr.base or exponent is not expr.exponent:
                return PBPowerOperator(base=base, exponent=exponent)

        elif isinstance(expr, PBTernaryExpression):
            # Optimize condition
            condition = self._optimize_constants(expr.condition)

            # If condition is constant, return appropriate branch
            if isinstance(condition, PBBooleanLiteral):
                self.optimizations_applied += 1
                if condition.value:
                    return self._optimize_constants(expr.true_expr)
                else:
                    return self._optimize_constants(expr.false_expr)

            # Optimize branches
            true_expr = self._optimize_constants(expr.true_expr)
            false_expr = self._optimize_constants(expr.false_expr)

            # Return expression with optimized parts
            if (condition is not expr.condition or 
                true_expr is not expr.true_expr or 
                false_expr is not expr.false_expr):
                return PBTernaryExpression(
                    condition=condition, true_expr=true_expr, false_expr=false_expr,
                )

        return expr

    def _optimize_algebraic(self, expr: Expression) -> Expression:




        """Perform algebraic simplification.

        Args:
            expr: Expression to optimize

        Returns:
            Optimized expression
        """
        if isinstance(expr, PBBinaryOperator):
            # Recursively optimize operands
            left = self._optimize_algebraic(expr.left)
            right = self._optimize_algebraic(expr.right)

            # Apply algebraic identities
            result = self._apply_algebraic_rules(left, expr.operator, right)
            if result is not None:
                self.optimizations_applied += 1
                return result

            # Return expression with optimized operands
            if left is not expr.left or right is not expr.right:
                return PBBinaryOperator(left=left, operator=expr.operator, right=right)

        elif isinstance(expr, PBPowerOperator):
            # Optimize operands
            base = self._optimize_algebraic(expr.base)
            exponent = self._optimize_algebraic(expr.exponent)

            # Special cases for power
            if isinstance(exponent, PBNumberLiteral):
                if exponent.value == 0:
                    self.optimizations_applied += 1
                    return PBNumberLiteral(value=1)
                elif exponent.value == 1:
                    self.optimizations_applied += 1
                    return base

            # Return expression with optimized operands
            if base is not expr.base or exponent is not expr.exponent:
                return PBPowerOperator(base=base, exponent=exponent)

        elif isinstance(expr, PBUnaryOperator):
            # Optimize operand
            operand = self._optimize_algebraic(expr.operand)

            # Return expression with optimized operand
            if operand is not expr.operand:
                return PBUnaryOperator(operator=expr.operator, operand=operand)

        elif isinstance(expr, PBTernaryExpression):
            # Optimize all parts
            condition = self._optimize_algebraic(expr.condition)
            true_expr = self._optimize_algebraic(expr.true_expr)
            false_expr = self._optimize_algebraic(expr.false_expr)

            # Return expression with optimized parts
            if (condition is not expr.condition or 
                true_expr is not expr.true_expr or 
                false_expr is not expr.false_expr):
                return PBTernaryExpression(
                    condition=condition, true_expr=true_expr, false_expr=false_expr,
                )

        return expr

    def _optimize_boolean(self, expr: Expression) -> Expression:




        """Perform boolean expression optimization.

        Args:
            expr: Expression to optimize

        Returns:
            Optimized expression
        """
        if isinstance(expr, PBBinaryOperator):
            # Recursively optimize operands
            left = self._optimize_boolean(expr.left)
            right = self._optimize_boolean(expr.right)

            # Apply boolean identities
            if expr.operator in ["AND", "OR"]:
                result = self._apply_boolean_rules(left, expr.operator, right)
                if result is not None:
                    self.optimizations_applied += 1
                    return result

            # Return expression with optimized operands
            if left is not expr.left or right is not expr.right:
                return PBBinaryOperator(left=left, operator=expr.operator, right=right)

        elif isinstance(expr, PBUnaryOperator):
            # Optimize operand
            operand = self._optimize_boolean(expr.operand)

            # Double negation elimination
            if expr.operator == "NOT":
                if isinstance(operand, PBUnaryOperator) and operand.operator == "NOT":
                    self.optimizations_applied += 1
                    return operand.operand

            # Return expression with optimized operand
            if operand is not expr.operand:
                return PBUnaryOperator(operator=expr.operator, operand=operand)

        elif isinstance(expr, PBTernaryExpression):
            # Optimize all parts
            condition = self._optimize_boolean(expr.condition)
            true_expr = self._optimize_boolean(expr.true_expr)
            false_expr = self._optimize_boolean(expr.false_expr)

            # Return expression with optimized parts
            if (condition is not expr.condition or 
                true_expr is not expr.true_expr or 
                false_expr is not expr.false_expr):
                return PBTernaryExpression(
                    condition=condition, true_expr=true_expr, false_expr=false_expr,
                )

        return expr

    def _is_literal(self, expr: Expression) -> bool:




        """Check if an expression is a literal value."""
        return isinstance(expr, (PBNumberLiteral, PBStringLiteral, PBBooleanLiteral, PBNullLiteral))

    def _fold_binary_constants(self, left: Expression, operator: str, right: Expression) -> Expression | None:




        """Fold binary operations on constants.

        Args:
            left: Left operand (must be literal)
            operator: Binary operator
            right: Right operand (must be literal)

        Returns:
            Folded result or None if cannot fold
        """
        # Handle null operands
        if isinstance(left, PBNullLiteral) or isinstance(right, PBNullLiteral):
            # Most operations with null result in null in PowerBuilder
            if operator not in ["=", "<>", "IS", "IS NOT"]:
                return PBNullLiteral()

        # Numeric operations
        if isinstance(left, PBNumberLiteral) and isinstance(right, PBNumberLiteral):
            try:
                if operator == "+":
                    return PBNumberLiteral(value=left.value + right.value)
                elif operator == "-":
                    return PBNumberLiteral(value=left.value - right.value)
                elif operator == "*":
                    return PBNumberLiteral(value=left.value * right.value)
                elif operator == "/":
                    if right.value != 0:
                        return PBNumberLiteral(value=left.value / right.value)
                elif operator == "=":
                    return PBBooleanLiteral(value=left.value == right.value)
                elif operator == "<>":
                    return PBBooleanLiteral(value=left.value != right.value)
                elif operator == "<":
                    return PBBooleanLiteral(value=left.value < right.value)
                elif operator == "<=":
                    return PBBooleanLiteral(value=left.value <= right.value)
                elif operator == ">":
                    return PBBooleanLiteral(value=left.value > right.value)
                elif operator == ">=":
                    return PBBooleanLiteral(value=left.value >= right.value)
            except Exception:
                # If any arithmetic error, don't fold
                pass

        # String operations
        elif isinstance(left, PBStringLiteral) and isinstance(right, PBStringLiteral):
            if operator == "+":
                return PBStringLiteral(value=left.value + right.value)
            elif operator == "=":
                return PBBooleanLiteral(value=left.value == right.value)
            elif operator == "<>":
                return PBBooleanLiteral(value=left.value != right.value)

        # Boolean operations
        elif isinstance(left, PBBooleanLiteral) and isinstance(right, PBBooleanLiteral):
            if operator == "AND":
                return PBBooleanLiteral(value=left.value and right.value)
            elif operator == "OR":
                return PBBooleanLiteral(value=left.value or right.value)
            elif operator == "=":
                return PBBooleanLiteral(value=left.value == right.value)
            elif operator == "<>":
                return PBBooleanLiteral(value=left.value != right.value)

        return None

    def _fold_unary_constants(self, operator: str, operand: Expression) -> Expression | None:




        """Fold unary operations on constants.

        Args:
            operator: Unary operator
            operand: Operand (must be literal)

        Returns:
            Folded result or None if cannot fold
        """
        if operator == "-" and isinstance(operand, PBNumberLiteral):
            return PBNumberLiteral(value=-operand.value)
        elif operator == "NOT" and isinstance(operand, PBBooleanLiteral):
            return PBBooleanLiteral(value=not operand.value)

        return None

    def _fold_concatenation(self, operands: list[Expression]) -> Expression | None:




        """Fold concatenation of string literals.

        Args:
            operands: List of operands

        Returns:
            Folded result or None if cannot fold completely
        """
        # Check if all operands are string literals
        if all(isinstance(op, PBStringLiteral) for op in operands):
            combined = "".join(op.value for op in operands)
            return PBStringLiteral(value=combined)

        # Partial folding: combine adjacent string literals
        new_operands = []
        i = 0
        while i < len(operands):
            if isinstance(operands[i], PBStringLiteral):
                # Collect consecutive string literals
                strings = [operands[i].value]
                j = i + 1
                while j < len(operands) and isinstance(operands[j], PBStringLiteral):
                    strings.append(operands[j].value)
                    j += 1

                if len(strings) > 1:
                    # Multiple strings found, combine them
                    new_operands.append(PBStringLiteral(value="".join(strings)))
                    i = j
                else:
                    # Single string, keep as is
                    new_operands.append(operands[i])
                    i += 1
            else:
                new_operands.append(operands[i])
                i += 1

        # If we reduced the number of operands, return new concatenation
        if len(new_operands) < len(operands):
            if len(new_operands) == 1:
                return new_operands[0]
            else:
                return PBConcatenationOperator(operands=new_operands)

        return None

    def _fold_power_constants(self, base: Expression, exponent: Expression) -> Expression | None:




        """Fold power operations on constants.

        Args:
            base: Base (must be literal)
            exponent: Exponent (must be literal)

        Returns:
            Folded result or None if cannot fold
        """
        if isinstance(base, PBNumberLiteral) and isinstance(exponent, PBNumberLiteral):
            try:
                result = base.value ** exponent.value
                return PBNumberLiteral(value=result)
            except Exception:
                # If any arithmetic error, don't fold
                pass

        return None

    def _apply_algebraic_rules(self, left: Expression, operator: str, right: Expression) -> Expression | None:




        """Apply algebraic simplification rules.

        Args:
            left: Left operand
            operator: Binary operator
            right: Right operand

        Returns:
            Simplified expression or None if no rule applies
        """
        # Addition identities
        if operator == "+":
            # x + 0 = x
            if isinstance(right, PBNumberLiteral) and right.value == 0:
                return left
            # 0 + x = x
            if isinstance(left, PBNumberLiteral) and left.value == 0:
                return right

        # Subtraction identities
        elif operator == "-":
            # x - 0 = x
            if isinstance(right, PBNumberLiteral) and right.value == 0:
                return left
            # x - x = 0 (only for simple variables)
            if isinstance(left, PBVariable) and isinstance(right, PBVariable):
                if left.name == right.name:
                    return PBNumberLiteral(value=0)

        # Multiplication identities
        elif operator == "*":
            # x * 1 = x
            if isinstance(right, PBNumberLiteral) and right.value == 1:
                return left
            # 1 * x = x
            if isinstance(left, PBNumberLiteral) and left.value == 1:
                return right
            # x * 0 = 0
            if isinstance(right, PBNumberLiteral) and right.value == 0:
                return PBNumberLiteral(value=0)
            # 0 * x = 0
            if isinstance(left, PBNumberLiteral) and left.value == 0:
                return PBNumberLiteral(value=0)

        # Division identities
        elif operator == "/":
            # x / 1 = x
            if isinstance(right, PBNumberLiteral) and right.value == 1:
                return left

        return None

    def _apply_boolean_rules(self, left: Expression, operator: str, right: Expression) -> Expression | None:




        """Apply boolean simplification rules.

        Args:
            left: Left operand
            operator: Boolean operator (AND/OR)
            right: Right operand

        Returns:
            Simplified expression or None if no rule applies
        """
        if operator == "AND":
            # true AND x = x
            if isinstance(left, PBBooleanLiteral) and left.value:
                return right
            # x AND true = x
            if isinstance(right, PBBooleanLiteral) and right.value:
                return left
            # false AND x = false
            if isinstance(left, PBBooleanLiteral) and not left.value:
                return PBBooleanLiteral(value=False)
            # x AND false = false
            if isinstance(right, PBBooleanLiteral) and not right.value:
                return PBBooleanLiteral(value=False)

        elif operator == "OR":
            # false OR x = x
            if isinstance(left, PBBooleanLiteral) and not left.value:
                return right
            # x OR false = x
            if isinstance(right, PBBooleanLiteral) and not right.value:
                return left
            # true OR x = true
            if isinstance(left, PBBooleanLiteral) and left.value:
                return PBBooleanLiteral(value=True)
            # x OR true = true
            if isinstance(right, PBBooleanLiteral) and right.value:
                return PBBooleanLiteral(value=True)

        return None
