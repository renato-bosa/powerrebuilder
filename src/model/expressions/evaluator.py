"""Expression evaluation system for PowerBuilder expressions.

This module provides context and evaluation capabilities for PowerBuilder expressions
with proper type handling and runtime context.
"""

from __future__ import annotations

import logging
import operator
from dataclasses import dataclass
from typing import TYPE_CHECKING, Any

from src.model.utils.errors import ModelError

if TYPE_CHECKING:
    from collections.abc import Callable

    from .ast_expressions import Expression

logger = logging.getLogger(__name__)


@dataclass
class EvaluationContext:
    """Runtime context for expression evaluation.

    Attributes:
        variables: Variable name to value mapping
        functions: Function name to callable mapping
        parent: Parent context for nested scopes
        this: Current object instance
        super: Super class instance
    """

    variables: dict[str, Any] = None
    functions: dict[str, Callable] = None
    parent: EvaluationContext | None = None
    this: Any = None
    super: Any = None

    def __post_init__(self) -> None:
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

    def call_function(self, name: str, args: list[Any]) -> Any:
        """Call a function with arguments."""
        func = self.get_function(name)
        return func(*args)

    def get_this(self) -> Any:
        """Get current object instance."""
        if self.this is not None:
            return self.this
        if self.parent:
            return self.parent.get_this()
        return "this"

    def get_super(self) -> Any:
        """Get super class instance."""
        if self.super is not None:
            return self.super
        if self.parent:
            return self.parent.get_super()
        return "super"

    def get_parent(self) -> Any:
        """Get parent object instance."""
        if "parent" in self.variables:
            return self.variables["parent"]
        if self.parent:
            return self.parent.get_parent()
        return "parent"

    def get_sql_variable(self, name: str) -> Any:
        """Get SQL variable value."""
        if name in self.variables:
            return self.variables[name]
        return f":{name}"

    def create_child_context(self) -> EvaluationContext:
        """Create a child context for nested scope."""
        return EvaluationContext(parent=self)


class ExpressionEvaluator:
    """Evaluator for PowerBuilder expressions.

    This evaluator supports all expression types defined in ast_expressions.py
    and provides proper type handling and runtime evaluation.
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
            "^": operator.pow,  # PowerBuilder power operator
            "==": operator.eq,
            "=": operator.eq,   # PowerBuilder equality
            "!=": operator.ne,
            "<>": operator.ne,  # PowerBuilder not equal
            "<": operator.lt,
            "<=": operator.le,
            ">": operator.gt,
            ">=": operator.ge,
            "and": lambda a, b: bool(a) and bool(b),
            "or": lambda a, b: bool(a) or bool(b),
            "&": operator.and_,
            "|": operator.or_,
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
        if expr is None:
            return None

        # First check if expression has its own evaluate method
        if hasattr(expr, "evaluate") and callable(expr.evaluate):
            try:
                import inspect
                sig = inspect.signature(expr.evaluate)
                if "context" in sig.parameters:
                    return expr.evaluate(context=self.context)
                return expr.evaluate()
            except (NotImplementedError, TypeError):
                pass

        # Use visitor pattern for evaluation
        method_name = f"visit_{expr.__class__.__name__.lower()}"
        visitor = getattr(self, method_name, self.generic_visit)
        return visitor(expr)

    def generic_visit(self, expr: Expression) -> Any:
        """Default visitor for unknown expression types."""
        logger.warning(
            f"Cannot evaluate unknown expression type: {expr.__class__.__name__}. "
            f"Returning string representation."
        )
        return str(expr)

    # Visitor methods for each expression type
    def visit_integerliteral(self, expr) -> int:
        """Evaluate integer literal."""
        return expr.value

    def visit_realliteral(self, expr) -> float:
        """Evaluate real literal."""
        return expr.value

    def visit_stringliteral(self, expr) -> str:
        """Evaluate string literal."""
        return expr.value

    def visit_booleanliteral(self, expr) -> bool:
        """Evaluate boolean literal."""
        return expr.value

    def visit_nullliteral(self, expr) -> None:
        """Evaluate null literal."""
        return None

    def visit_variable(self, expr) -> Any:
        """Evaluate variable reference."""
        return self.context.get_variable(expr.name)

    def visit_fieldaccessexpression(self, expr) -> Any:
        """Evaluate field access expression."""
        if expr.object:
            obj = self.evaluate(expr.object)

            # Handle dictionary-like objects
            if isinstance(obj, dict) and expr.field in obj:
                return obj[expr.field]

            # Handle object attributes
            if hasattr(obj, expr.field):
                return getattr(obj, expr.field)

            msg = f"Object has no field '{expr.field}'"
            raise ModelError(msg)

        # No object means accessing field on current context
        return self.context.get_variable(expr.field)

    def visit_binaryexpression(self, expr) -> Any:
        """Evaluate binary expression."""
        left = self.evaluate(expr.left)
        right = self.evaluate(expr.right)
        op = expr.operator.value if hasattr(expr.operator, 'value') else str(expr.operator)

        if op in self.binary_ops:
            try:
                # Handle string concatenation
                if op in ["+", "&"] and (isinstance(left, str) or isinstance(right, str)):
                    return str(left) + str(right)

                # Handle division by zero
                if op == "/" and right == 0:
                    msg = "Division by zero"
                    raise ModelError(msg)

                return self.binary_ops[op](left, right)
            except Exception as e:
                msg = f"Error evaluating {left} {op} {right}: {e}"
                raise ModelError(msg)
        else:
            msg = f"Unknown binary operator: {op}"
            raise ModelError(msg)

    def visit_unaryexpression(self, expr) -> Any:
        """Evaluate unary expression."""
        operand = self.evaluate(expr.operand)
        op = expr.operator.value if hasattr(expr.operator, 'value') else str(expr.operator)

        if op in self.unary_ops:
            try:
                return self.unary_ops[op](operand)
            except Exception as e:
                msg = f"Error evaluating {op}{operand}: {e}"
                raise ModelError(msg)
        else:
            msg = f"Unknown unary operator: {op}"
            raise ModelError(msg)

    def visit_callexpression(self, expr) -> Any:
        """Evaluate function/method call expression."""
        # Get function name
        if isinstance(expr.function, str):
            func_name = expr.function
        else:
            func_name = self.evaluate(expr.function)

        # Evaluate arguments
        args = [self.evaluate(arg) for arg in expr.arguments]

        # Call function
        return self.context.call_function(func_name, args)

    def visit_arrayaccessexpression(self, expr) -> Any:
        """Evaluate array access expression."""
        array = self.evaluate(expr.array)
        index = self.evaluate(expr.index)

        try:
            # PowerBuilder arrays are 1-based, Python are 0-based
            if isinstance(index, int) and index > 0:
                return array[index - 1]
            else:
                return array[index]
        except (IndexError, KeyError, TypeError) as e:
            msg = f"Error accessing array element: {e}"
            raise ModelError(msg)

    def visit_conditionalexpression(self, expr) -> Any:
        """Evaluate conditional (ternary) expression."""
        condition = self.evaluate(expr.condition)

        if condition:
            return self.evaluate(expr.true_expression)
        else:
            return self.evaluate(expr.false_expression)

    def visit_castexpression(self, expr) -> Any:
        """Evaluate type cast expression."""
        value = self.evaluate(expr.expression)
        target_type = expr.target_type.lower()

        try:
            if target_type in ("string", "str"):
                return str(value)
            elif target_type in ("integer", "int", "long"):
                return int(value)
            elif target_type in ("double", "real", "decimal", "float"):
                return float(value)
            elif target_type in ("boolean", "bool"):
                return bool(value)
            elif target_type == "char" and isinstance(value, str):
                return value[0] if value else ""
            elif target_type == "byte":
                return int(value) & 0xFF
            else:
                msg = f"Cast to {expr.target_type} not implemented"
                raise ModelError(msg)
        except (ValueError, TypeError, IndexError) as e:
            msg = f"Error casting to {expr.target_type}: {e}"
            raise ModelError(msg)

    def visit_thisexpression(self, expr) -> Any:
        """Evaluate 'this' reference."""
        return self.context.get_this()

    def visit_superexpression(self, expr) -> Any:
        """Evaluate 'super' reference."""
        return self.context.get_super()

    def visit_parentexpression(self, expr) -> Any:
        """Evaluate 'parent' reference."""
        return self.context.get_parent()

    def visit_sqlvariableexpression(self, expr) -> Any:
        """Evaluate SQL variable expression."""
        return self.context.get_sql_variable(expr.variable_name)

    def visit_inexpression(self, expr) -> Any:
        """Evaluate IN expression."""
        expr_val = self.evaluate(expr.expression)
        value_list = [self.evaluate(v) for v in expr.values]
        return expr_val in value_list

    def visit_likeexpression(self, expr) -> Any:
        """Evaluate LIKE expression."""
        expr_val = str(self.evaluate(expr.expression))
        pattern_val = str(self.evaluate(expr.pattern))

        # Simple LIKE implementation
        import re
        pattern_regex = pattern_val.replace('%', '.*').replace('_', '.')
        return bool(re.match(pattern_regex, expr_val))

    def visit_betweenexpression(self, expr) -> Any:
        """Evaluate BETWEEN expression."""
        val = self.evaluate(expr.expression)
        lower = self.evaluate(expr.lower_bound)
        upper = self.evaluate(expr.upper_bound)
        return lower <= val <= upper

    def visit_existsexpression(self, expr) -> Any:
        """Evaluate EXISTS expression."""
        # EXISTS would need SQL execution context
        return f"EXISTS({expr.subquery})"


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