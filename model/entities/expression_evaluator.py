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
    from model.ast.functions import FunctionCall
    from model.entities.expressions import (
        PBArrayAccess,
        PBFieldReference,
        PBTernaryExpression,
        PBConstructorCall,
        PBThisExpression,
        PBParentExpression,
        PBSuperExpression,
        PBConcatenationOperator,
        PBPowerOperator,
        PBSqlVariableExpression,
        PBDynamicSqlExpression,
        PBMethodCall,
        PBCastExpression,
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

    def visit_functioncall(self, expr: 'FunctionCall') -> Any:
        """Evaluate a function call expression."""
        # Handle both AST FunctionCall and PBFunctionCall
        function_name = getattr(expr, 'function_name', None) or getattr(expr, 'name', None)
        if not function_name:
            msg = "Function call has no function name"
            raise ModelError(msg)
            
        func = self.context.get_function(function_name)
        args = [self.evaluate(arg) for arg in expr.arguments]

        try:
            return func(*args)
        except Exception as e:
            msg = f"Error calling function {function_name}: {e}"
            raise ModelError(msg)

    def visit_fieldreference(self, expr: 'PBFieldReference') -> Any:
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

    def visit_arrayaccess(self, expr: 'PBArrayAccess') -> Any:
        """Evaluate array access expression."""
        array = self.evaluate(expr.array)
        
        # Handle multiple indices for multi-dimensional arrays
        indices = getattr(expr, 'indices', None) or [getattr(expr, 'index', None)]
        
        result = array
        for index_expr in indices:
            if index_expr is None:
                continue
            index = self.evaluate(index_expr)
            try:
                # PowerBuilder arrays are 1-based, Python are 0-based
                if isinstance(index, int) and index > 0:
                    result = result[index - 1]
                else:
                    result = result[index]
            except (IndexError, KeyError, TypeError) as e:
                msg = f"Error accessing array element: {e}"
                raise ModelError(msg)
        
        return result

    def visit_conditional(self, expr: 'PBTernaryExpression') -> Any:
        """Evaluate conditional expression (ternary operator)."""
        condition = self.evaluate(expr.condition)

        if condition:
            # Handle both then_expr and true_expr attributes
            then_expr = getattr(expr, 'then_expr', None) or getattr(expr, 'true_expr', None)
            return self.evaluate(then_expr)
        
        # Handle both else_expr and false_expr attributes  
        else_expr = getattr(expr, 'else_expr', None) or getattr(expr, 'false_expr', None)
        return self.evaluate(else_expr)

    def visit_pbfunctioncall(self, expr: 'PBFunctionCall') -> Any:
        """Evaluate PBFunctionCall expression."""
        return self.visit_functioncall(expr)

    def visit_pbfieldreference(self, expr: 'PBFieldReference') -> Any:
        """Evaluate PBFieldReference expression."""
        return self.visit_fieldreference(expr)

    def visit_pbarrayaccess(self, expr: 'PBArrayAccess') -> Any:
        """Evaluate PBArrayAccess expression."""
        return self.visit_arrayaccess(expr)

    def visit_pbternaryexpression(self, expr: 'PBTernaryExpression') -> Any:
        """Evaluate PBTernaryExpression expression."""
        return self.visit_conditional(expr)

    def visit_pbcastexpression(self, expr: 'PBCastExpression') -> Any:
        """Evaluate type cast expression."""
        value = self.evaluate(expr.expression)
        target_type = expr.target_type.lower()

        try:
            if target_type in ('string', 'str'):
                return str(value)
            elif target_type in ('integer', 'int', 'long'):
                return int(value)
            elif target_type in ('double', 'real', 'decimal', 'float'):
                return float(value)
            elif target_type in ('boolean', 'bool'):
                return bool(value)
            elif target_type == 'char' and isinstance(value, str):
                return value[0] if value else ''
            elif target_type == 'byte':
                return int(value) & 0xFF
            else:
                msg = f"Cast to {expr.target_type} not implemented"
                raise ModelError(msg)
        except (ValueError, TypeError, IndexError) as e:
            msg = f"Error casting to {expr.target_type}: {e}"
            raise ModelError(msg)

    def visit_pbconstructorcall(self, expr: 'PBConstructorCall') -> Any:
        """Evaluate constructor call expression."""
        # Check if constructor is registered as a function
        if expr.class_name in self.context.functions:
            constructor = self.context.functions[expr.class_name]
            args = [self.evaluate(arg) for arg in expr.arguments]
            return constructor(*args)
        
        msg = f"Constructor for class '{expr.class_name}' not found in context"
        raise ModelError(msg)

    def visit_pbthisexpression(self, expr: 'PBThisExpression') -> Any:
        """Evaluate 'this' reference."""
        if 'this' in self.context.variables:
            return self.context.variables['this']
        msg = "'This' reference requires runtime context with current object"
        raise ModelError(msg)

    def visit_pbparentexpression(self, expr: 'PBParentExpression') -> Any:
        """Evaluate 'parent' reference."""
        if 'parent' in self.context.variables:
            return self.context.variables['parent']
        msg = "'Parent' reference requires runtime context with parent object"
        raise ModelError(msg)

    def visit_pbsuperexpression(self, expr: 'PBSuperExpression') -> Any:
        """Evaluate 'super' reference."""
        if 'super' in self.context.variables:
            return self.context.variables['super']
        msg = "'Super' reference requires runtime context with super class"
        raise ModelError(msg)

    def visit_pbconcatenationoperator(self, expr: 'PBConcatenationOperator') -> Any:
        """Evaluate string concatenation for multiple operands."""
        result = []
        for operand in expr.operands:
            value = self.evaluate(operand)
            result.append(str(value))
        return ''.join(result)

    def visit_pbpoweroperator(self, expr: 'PBPowerOperator') -> Any:
        """Evaluate power operation."""
        base = self.evaluate(expr.base)
        exponent = self.evaluate(expr.exponent)
        try:
            return base ** exponent
        except Exception as e:
            msg = f"Error in power operation {base} ^ {exponent}: {e}"
            raise ModelError(msg)

    def visit_pbsqlvariableexpression(self, expr: 'PBSqlVariableExpression') -> Any:
        """Evaluate SQL variable expression."""
        if expr.variable_name in self.context.variables:
            return self.context.variables[expr.variable_name]
        # Return placeholder for SQL generation
        return f":{expr.variable_name}"

    def visit_pbdynamicsqlexpression(self, expr: 'PBDynamicSqlExpression') -> Any:
        """Evaluate dynamic SQL expression."""
        result = []
        for part in expr.sql_parts:
            if isinstance(part, str):
                result.append(part)
            else:
                value = self.evaluate(part)
                result.append(str(value))
        return ''.join(result)

    def visit_pbmethodcall(self, expr: 'PBMethodCall') -> Any:
        """Evaluate method call expression."""
        # Method calls need object context
        if expr.object:
            obj = self.evaluate(expr.object)
            if hasattr(obj, expr.function_name):
                method = getattr(obj, expr.function_name)
                args = [self.evaluate(arg) for arg in expr.arguments]
                return method(*args)
            msg = f"Object has no method '{expr.function_name}'"
            raise ModelError(msg)
        # Fall back to regular function call
        return self.visit_functioncall(expr)


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
