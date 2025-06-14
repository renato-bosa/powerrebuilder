"""Expression evaluation system for PowerBuilder expressions.

This module provides a visitor-based expression evaluator that can evaluate
PowerBuilder expressions with proper type handling and runtime context.
"""

from __future__ import annotations

import operator
from dataclasses import dataclass
from typing import TYPE_CHECKING, Any

from model.utils.errors import ModelError

if TYPE_CHECKING:
    from collections.abc import Callable

    from model.ast.ast_nodes import (
        BinaryExpression,
        Expression,
        Literal,
        UnaryExpression,
        Variable,
    )


@dataclass
class EvaluationContext:
    """Runtime context for expression evaluation.

    Attributes:
        variables: Variable name to value mapping
        functions: Function name to callable mapping
        parent: Parent context for nested scopes
    """

    variables: dict[str, Any] = None
    functions: dict[str, Callable] = None
    parent: EvaluationContext | None = None

    def __post_init__(self):
        if self.variables is None:
            self.variables = {}
        if self.functions is None:
            self.functions = {}

    def get_variable(self, name: str) -> Any:
        """Get variable value, checking parent contexts if needed."""
        if name in self.variables:
            return self.variables[name]
        if self.parent:
            return self.parent.get_variable(name)
        msg = f"Undefined variable: {name}"
        raise ModelError(msg)

    def set_variable(self, name: str, value: Any) -> None:
        """Set variable value in current context."""
        self.variables[name] = value

    def get_function(self, name: str) -> Callable:
        """Get function, checking parent contexts if needed."""
        if name in self.functions:
            return self.functions[name]
        if self.parent:
            return self.parent.get_function(name)
        msg = f"Undefined function: {name}"
        raise ModelError(msg)

    def create_child_context(self) -> EvaluationContext:
        """Create a child context for nested scope."""
        return EvaluationContext(parent=self)


class ExpressionEvaluator:
    """Visitor for evaluating PowerBuilder expressions.

    This evaluator supports:
    - Literals (numbers, strings, booleans, null)
    - Variables and field references
    - Unary operations (-, not, +)
    - Binary operations (+, -, *, /, %, and, or, comparisons)
    - Function calls
    - Type coercion where appropriate
    """

    def __init__(self, context: EvaluationContext | None = None) -> None:
        """Initialize evaluator with optional context."""
        self.context = context or EvaluationContext()

        # Binary operator mappings
        self.binary_ops = {
            "+": operator.add,
            "-": operator.sub,
            "*": operator.mul,
            "/": operator.truediv,
            "%": operator.mod,
            "**": operator.pow,
            "==": operator.eq,
            "!=": operator.ne,
            "<": operator.lt,
            "<=": operator.le,
            ">": operator.gt,
            ">=": operator.ge,
            "and": lambda a, b: bool(a) and bool(b),
            "or": lambda a, b: bool(a) or bool(b),
            "&": operator.and_,
            "|": operator.or_,
            "^": operator.xor,
            "<<": operator.lshift,
            ">>": operator.rshift,
        }

        # Unary operator mappings
        self.unary_ops = {
            "-": operator.neg,
            "+": operator.pos,
            "not": operator.not_,
            "~": operator.invert,
        }

    def evaluate(self, expr: Expression) -> Any:
        """Evaluate an expression and return its value.

        Args:
            expr: Expression to evaluate

        Returns:
            Evaluated value

        Raises:
            ModelError: If evaluation fails
        """
        method_name = f"visit_{expr.__class__.__name__.lower()}"
        visitor = getattr(self, method_name, self.generic_visit)
        return visitor(expr)

    def generic_visit(self, expr: Expression) -> Any:
        """Default visitor for unknown expression types."""
        # Try to call evaluate method on the expression itself
        if hasattr(expr, "evaluate") and callable(expr.evaluate):
            try:
                # Check if evaluate expects context
                import inspect

                sig = inspect.signature(expr.evaluate)
                if "context" in sig.parameters:
                    return expr.evaluate(context=self.context)
                return expr.evaluate()
            except NotImplementedError:
                pass

        msg = f"Cannot evaluate expression type: {expr.__class__.__name__}"
        raise ModelError(msg)

    def visit_literal(self, expr: Literal) -> Any:
        """Evaluate a literal expression."""
        return expr.value

    def visit_variable(self, expr: Variable) -> Any:
        """Evaluate a variable reference."""
        return self.context.get_variable(expr.name)

    def visit_binaryexpression(self, expr: BinaryExpression) -> Any:
        """Evaluate a binary expression."""
        left = self.evaluate(expr.left)
        right = self.evaluate(expr.right)

        if expr.operator in self.binary_ops:
            try:
                # Handle string concatenation with +
                if expr.operator == "+" and (
                    isinstance(left, str) or isinstance(right, str)
                ):
                    return str(left) + str(right)

                # Handle division by zero
                if expr.operator == "/" and right == 0:
                    msg = "Division by zero"
                    raise ModelError(msg)

                return self.binary_ops[expr.operator](left, right)
            except Exception as e:
                msg = f"Error evaluating {left} {expr.operator} {right}: {e}"
                raise ModelError(msg)
        else:
            msg = f"Unknown binary operator: {expr.operator}"
            raise ModelError(msg)

    def visit_unaryexpression(self, expr: UnaryExpression) -> Any:
        """Evaluate a unary expression."""
        operand = self.evaluate(expr.operand)

        if expr.operator in self.unary_ops:
            try:
                return self.unary_ops[expr.operator](operand)
            except Exception as e:
                msg = f"Error evaluating {expr.operator}{operand}: {e}"
                raise ModelError(msg)
        else:
            msg = f"Unknown unary operator: {expr.operator}"
            raise ModelError(msg)

    def visit_functioncall(self, expr: FunctionCall) -> Any:
        """Evaluate a function call expression."""
        func = self.context.get_function(expr.name)
        args = [self.evaluate(arg) for arg in expr.arguments]

        try:
            return func(*args)
        except Exception as e:
            msg = f"Error calling function {expr.name}: {e}"
            raise ModelError(msg)

    def visit_fieldreference(self, expr: FieldReference) -> Any:
        """Evaluate a field reference (object.field)."""
        obj = self.evaluate(expr.object)

        # Handle dictionary-like objects
        if isinstance(obj, dict) and expr.field_name in obj:
            return obj[expr.field_name]

        # Handle object attributes
        if hasattr(obj, expr.field_name):
            return getattr(obj, expr.field_name)

        msg = f"Object has no field '{expr.field_name}'"
        raise ModelError(msg)

    def visit_arrayaccess(self, expr: ArrayAccess) -> Any:
        """Evaluate array access expression."""
        array = self.evaluate(expr.array)
        index = self.evaluate(expr.index)

        try:
            # PowerBuilder arrays are 1-based, Python are 0-based
            if isinstance(index, int) and index > 0:
                return array[index - 1]
            return array[index]
        except (IndexError, KeyError, TypeError) as e:
            msg = f"Error accessing array element: {e}"
            raise ModelError(msg)

    def visit_conditional(self, expr: Conditional) -> Any:
        """Evaluate conditional expression (ternary operator)."""
        condition = self.evaluate(expr.condition)

        if condition:
            return self.evaluate(expr.then_expr)
        return self.evaluate(expr.else_expr)


def evaluate_expression(
    expr: Expression,
    variables: dict[str, Any] | None = None,
    functions: dict[str, Callable] | None = None,
) -> Any:
    """Convenience function to evaluate an expression.

    Args:
        expr: Expression to evaluate
        variables: Variable bindings
        functions: Function bindings

    Returns:
        Evaluated value
    """
    context = EvaluationContext(variables=variables, functions=functions)
    evaluator = ExpressionEvaluator(context)
    return evaluator.evaluate(expr)
