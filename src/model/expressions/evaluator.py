"""Expression evaluation system for PowerBuilder expressions.

This module provides context and evaluation capabilities for PowerBuilder expressions
with proper type handling and runtime context.
"""

from __future__ import annotations

import logging
from collections.abc import Callable
from dataclasses import dataclass, field
from datetime import date, datetime
from decimal import Decimal
from typing import TYPE_CHECKING, Any, Optional, Union

from src.model.utils.errors import ModelError
from .pb_expressions import (
    PBLiteral,
    PBBooleanLiteral,
    PBNullLiteral,
    PBStringLiteral,
    PBNumberLiteral,
    PBVariable,
    PBBinaryOperator,
    PBUnaryOperator,
    PBFunctionCall,
    PBArrayAccess,
    PBMemberAccess,
)

if TYPE_CHECKING:
    from src.model.ast.nodes.base import Expression

logger = logging.getLogger(__name__)


class EvaluationError(ModelError):
    """Error during expression evaluation."""
    pass


@dataclass
class EvaluationContext:
    """Context for expression evaluation."""
    
    variables: dict[str, Any] = field(default_factory=dict)
    functions: dict[str, Callable] = field(default_factory=dict)
    types: dict[str, type] = field(default_factory=dict)
    parent: Optional[EvaluationContext] = None
    
    def get_variable(self, name: str) -> Any:
        """Get variable value, checking parent scopes."""
        if name in self.variables:
            return self.variables[name]
        if self.parent:
            return self.parent.get_variable(name)
        raise EvaluationError(f"Variable '{name}' not found")
    
    def set_variable(self, name: str, value: Any) -> None:
        """Set variable value in current scope."""
        self.variables[name] = value
    
    def get_function(self, name: str) -> Callable:
        """Get function, checking parent scopes."""
        # Normalize function name to lowercase
        name_lower = name.lower()
        
        if name_lower in self.functions:
            return self.functions[name_lower]
        
        # Check built-in functions
        builtin_func = BUILTIN_FUNCTIONS.get(name_lower)
        if builtin_func:
            return builtin_func
            
        if self.parent:
            return self.parent.get_function(name)
            
        raise EvaluationError(f"Function '{name}' not found")
    
    def create_child(self) -> EvaluationContext:
        """Create a child context."""
        return EvaluationContext(parent=self)


class ExpressionEvaluator:
    """Evaluates PowerBuilder expressions."""
    
    def __init__(self, context: Optional[EvaluationContext] = None):
        """Initialize evaluator with optional context."""
        self.context = context or EvaluationContext()
        self._init_builtin_types()
    
    def _init_builtin_types(self) -> None:
        """Initialize built-in PowerBuilder types."""
        self.context.types.update({
            'integer': int,
            'long': int,
            'real': float,
            'double': float,
            'decimal': Decimal,
            'string': str,
            'boolean': bool,
            'date': date,
            'datetime': datetime,
        })
    
    def evaluate(self, expr: Expression) -> Any:
        """Evaluate an expression and return its value."""
        if expr is None:
            return None
            
        try:
            # Check if expression has its own evaluate method
            if hasattr(expr, 'evaluate'):
                return expr.evaluate(self.context)
            
            # Dispatch based on expression type
            expr_type = type(expr).__name__
            method_name = f'_evaluate_{expr_type.lower()}'
            method = getattr(self, method_name, None)
            
            if method:
                return method(expr)
            else:
                # Try generic evaluation based on expression class
                return self._evaluate_generic(expr)
                
        except EvaluationError:
            raise
        except Exception as e:
            raise EvaluationError(f"Error evaluating expression: {e}") from e
    
    def _evaluate_pbliteral(self, expr: PBLiteral) -> Any:
        """Evaluate a literal expression."""
        return expr.value
    
    def _evaluate_pbbooleanliteral(self, expr: PBBooleanLiteral) -> bool:
        """Evaluate a boolean literal."""
        return expr.value
    
    def _evaluate_pbnullliteral(self, expr: PBNullLiteral) -> None:
        """Evaluate a null literal."""
        return None
    
    def _evaluate_pbstringliteral(self, expr: PBStringLiteral) -> str:
        """Evaluate a string literal."""
        return expr.value
    
    def _evaluate_pbnumberliteral(self, expr: PBNumberLiteral) -> Union[int, float]:
        """Evaluate a number literal."""
        return expr.value
    
    def _evaluate_pbvariable(self, expr: PBVariable) -> Any:
        """Evaluate a variable reference."""
        return self.context.get_variable(expr.name)
    
    def _evaluate_pbbinaryoperator(self, expr: PBBinaryOperator) -> Any:
        """Evaluate a binary operator expression."""
        if not expr.left or not expr.right:
            raise EvaluationError("Binary operator missing operands")
            
        left_val = self.evaluate(expr.left)
        right_val = self.evaluate(expr.right)
        
        # PowerBuilder operators (case-insensitive)
        op = expr.operator.upper()
        
        # Arithmetic operators
        if op == '+':
            return self._add(left_val, right_val)
        elif op == '-':
            return self._subtract(left_val, right_val)
        elif op == '*':
            return self._multiply(left_val, right_val)
        elif op == '/':
            return self._divide(left_val, right_val)
        elif op == '^':
            return self._power(left_val, right_val)
        
        # Comparison operators
        elif op == '=':
            return self._equal(left_val, right_val)
        elif op == '<>':
            return self._not_equal(left_val, right_val)
        elif op == '<':
            return self._less_than(left_val, right_val)
        elif op == '>':
            return self._greater_than(left_val, right_val)
        elif op == '<=':
            return self._less_equal(left_val, right_val)
        elif op == '>=':
            return self._greater_equal(left_val, right_val)
        
        # Logical operators
        elif op == 'AND':
            return self._and(left_val, right_val)
        elif op == 'OR':
            return self._or(left_val, right_val)
        
        # String concatenation
        elif op == '+' and isinstance(left_val, str):
            return str(left_val) + str(right_val)
        
        else:
            raise EvaluationError(f"Unknown binary operator: {expr.operator}")
    
    def _evaluate_pbunaryoperator(self, expr: PBUnaryOperator) -> Any:
        """Evaluate a unary operator expression."""
        if not expr.operand:
            raise EvaluationError("Unary operator missing operand")
            
        val = self.evaluate(expr.operand)
        
        # PowerBuilder operators (case-insensitive)
        op = expr.operator.upper()
        
        if op == '-':
            return self._negate(val)
        elif op == '+':
            return self._positive(val)
        elif op == 'NOT':
            return self._not(val)
        else:
            raise EvaluationError(f"Unknown unary operator: {expr.operator}")
    
    def _evaluate_pbfunctioncall(self, expr: PBFunctionCall) -> Any:
        """Evaluate a function call expression."""
        func = self.context.get_function(expr.function_name)
        
        # Evaluate arguments
        args = []
        for arg in expr.arguments:
            args.append(self.evaluate(arg))
        
        # Call function
        try:
            return func(*args)
        except TypeError as e:
            raise EvaluationError(
                f"Error calling function '{expr.function_name}': {e}"
            ) from e
    
    def _evaluate_pbarrayaccess(self, expr: PBArrayAccess) -> Any:
        """Evaluate an array access expression."""
        if not expr.array:
            raise EvaluationError("Array access missing array expression")
            
        array_val = self.evaluate(expr.array)
        
        if not hasattr(array_val, '__getitem__'):
            raise EvaluationError(f"Value is not subscriptable: {type(array_val)}")
        
        # PowerBuilder arrays are 1-based
        indices = []
        for idx_expr in expr.indices:
            idx = self.evaluate(idx_expr)
            if not isinstance(idx, int):
                raise EvaluationError(f"Array index must be integer, got {type(idx)}")
            # Convert from 1-based to 0-based
            indices.append(idx - 1)
        
        # Access array
        try:
            result = array_val
            for idx in indices:
                result = result[idx]
            return result
        except (IndexError, KeyError) as e:
            raise EvaluationError(f"Array access error: {e}") from e
    
    def _evaluate_pbmemberaccess(self, expr: PBMemberAccess) -> Any:
        """Evaluate a member access expression."""
        if not expr.object:
            raise EvaluationError("Member access missing object expression")
            
        obj_val = self.evaluate(expr.object)
        
        # Try attribute access
        try:
            return getattr(obj_val, expr.member)
        except AttributeError:
            # Try dictionary access
            if hasattr(obj_val, '__getitem__'):
                try:
                    return obj_val[expr.member]
                except (KeyError, TypeError):
                    pass
            
            raise EvaluationError(
                f"Object has no member '{expr.member}': {type(obj_val)}"
            )
    
    def _evaluate_generic(self, expr: Expression) -> Any:
        """Generic evaluation for unknown expression types."""
        # If it's a simple value, return it
        if isinstance(expr, (int, float, str, bool, type(None))):
            return expr
            
        # Try to extract value attribute
        if hasattr(expr, 'value'):
            return expr.value
            
        # Default: can't evaluate
        raise EvaluationError(f"Cannot evaluate expression type: {type(expr)}")
    
    # Arithmetic operations with type coercion
    def _add(self, left: Any, right: Any) -> Any:
        """Add two values with PowerBuilder semantics."""
        # String concatenation
        if isinstance(left, str) or isinstance(right, str):
            return str(left) + str(right)
        
        # Numeric addition
        return self._coerce_numeric(left) + self._coerce_numeric(right)
    
    def _subtract(self, left: Any, right: Any) -> Any:
        """Subtract two values."""
        return self._coerce_numeric(left) - self._coerce_numeric(right)
    
    def _multiply(self, left: Any, right: Any) -> Any:
        """Multiply two values."""
        return self._coerce_numeric(left) * self._coerce_numeric(right)
    
    def _divide(self, left: Any, right: Any) -> Any:
        """Divide two values."""
        right_num = self._coerce_numeric(right)
        if right_num == 0:
            raise EvaluationError("Division by zero")
        return self._coerce_numeric(left) / right_num
    
    def _power(self, left: Any, right: Any) -> Any:
        """Raise left to the power of right."""
        return self._coerce_numeric(left) ** self._coerce_numeric(right)
    
    def _negate(self, val: Any) -> Any:
        """Negate a value."""
        return -self._coerce_numeric(val)
    
    def _positive(self, val: Any) -> Any:
        """Return positive value."""
        return +self._coerce_numeric(val)
    
    # Comparison operations
    def _equal(self, left: Any, right: Any) -> bool:
        """Check equality with PowerBuilder semantics."""
        # Handle null comparisons
        if left is None or right is None:
            return left is right
        
        # Type coercion for comparison
        if type(left) != type(right):
            # Try numeric coercion
            try:
                return self._coerce_numeric(left) == self._coerce_numeric(right)
            except (ValueError, TypeError):
                # Try string coercion
                return str(left) == str(right)
        
        return left == right
    
    def _not_equal(self, left: Any, right: Any) -> bool:
        """Check inequality."""
        return not self._equal(left, right)
    
    def _less_than(self, left: Any, right: Any) -> bool:
        """Less than comparison."""
        if type(left) != type(right):
            # Try numeric comparison
            try:
                return self._coerce_numeric(left) < self._coerce_numeric(right)
            except (ValueError, TypeError):
                # String comparison
                return str(left) < str(right)
        return left < right
    
    def _greater_than(self, left: Any, right: Any) -> bool:
        """Greater than comparison."""
        if type(left) != type(right):
            try:
                return self._coerce_numeric(left) > self._coerce_numeric(right)
            except (ValueError, TypeError):
                return str(left) > str(right)
        return left > right
    
    def _less_equal(self, left: Any, right: Any) -> bool:
        """Less than or equal comparison."""
        return self._less_than(left, right) or self._equal(left, right)
    
    def _greater_equal(self, left: Any, right: Any) -> bool:
        """Greater than or equal comparison."""
        return self._greater_than(left, right) or self._equal(left, right)
    
    # Logical operations
    def _and(self, left: Any, right: Any) -> bool:
        """Logical AND with PowerBuilder semantics."""
        return self._coerce_bool(left) and self._coerce_bool(right)
    
    def _or(self, left: Any, right: Any) -> bool:
        """Logical OR with PowerBuilder semantics."""
        return self._coerce_bool(left) or self._coerce_bool(right)
    
    def _not(self, val: Any) -> bool:
        """Logical NOT."""
        return not self._coerce_bool(val)
    
    # Type coercion helpers
    def _coerce_numeric(self, val: Any) -> Union[int, float, Decimal]:
        """Coerce value to numeric type."""
        if isinstance(val, (int, float, Decimal)):
            return val
        
        if isinstance(val, str):
            # Try to parse as number
            val = val.strip()
            if not val:
                return 0
            
            try:
                # Try integer first
                if '.' not in val and 'e' not in val.lower():
                    return int(val)
                else:
                    return float(val)
            except ValueError:
                raise EvaluationError(f"Cannot convert '{val}' to number")
        
        if isinstance(val, bool):
            return 1 if val else 0
        
        if val is None:
            return 0
        
        raise EvaluationError(f"Cannot convert {type(val)} to number")
    
    def _coerce_bool(self, val: Any) -> bool:
        """Coerce value to boolean with PowerBuilder semantics."""
        if isinstance(val, bool):
            return val
        
        if isinstance(val, (int, float, Decimal)):
            return val != 0
        
        if isinstance(val, str):
            # PowerBuilder string to boolean
            val_lower = val.lower().strip()
            if val_lower in ('true', 't', 'yes', 'y', '1'):
                return True
            elif val_lower in ('false', 'f', 'no', 'n', '0', ''):
                return False
            else:
                # Non-empty string is true
                return bool(val)
        
        if val is None:
            return False
        
        # Default: use Python's bool()
        return bool(val)


# Built-in PowerBuilder functions
def pb_len(s: Any) -> int:
    """PowerBuilder Len function."""
    if s is None:
        return 0
    return len(str(s))


def pb_trim(s: Any) -> str:
    """PowerBuilder Trim function."""
    if s is None:
        return ""
    return str(s).strip()


def pb_left(s: Any, n: int) -> str:
    """PowerBuilder Left function."""
    if s is None:
        return ""
    s = str(s)
    n = max(0, int(n))
    return s[:n]


def pb_right(s: Any, n: int) -> str:
    """PowerBuilder Right function."""
    if s is None:
        return ""
    s = str(s)
    n = max(0, int(n))
    return s[-n:] if n > 0 else ""


def pb_mid(s: Any, start: int, length: Optional[int] = None) -> str:
    """PowerBuilder Mid function (1-based indexing)."""
    if s is None:
        return ""
    s = str(s)
    start = max(1, int(start))
    
    # Convert to 0-based
    start_idx = start - 1
    
    if length is None:
        return s[start_idx:]
    else:
        length = max(0, int(length))
        return s[start_idx:start_idx + length]


def pb_pos(s1: Any, s2: Any, start: int = 1) -> int:
    """PowerBuilder Pos function (1-based result)."""
    if s1 is None or s2 is None:
        return 0
    
    s1 = str(s1)
    s2 = str(s2)
    start = max(1, int(start))
    
    # Convert to 0-based
    start_idx = start - 1
    
    pos = s1.find(s2, start_idx)
    # Convert back to 1-based (0 means not found)
    return pos + 1 if pos >= 0 else 0


def pb_upper(s: Any) -> str:
    """PowerBuilder Upper function."""
    if s is None:
        return ""
    return str(s).upper()


def pb_lower(s: Any) -> str:
    """PowerBuilder Lower function."""
    if s is None:
        return ""
    return str(s).lower()


def pb_string(val: Any, format_str: Optional[str] = None) -> str:
    """PowerBuilder String function."""
    if val is None:
        return ""
    
    if format_str:
        # TODO: Implement PowerBuilder format strings
        logger.warning(f"Format string '{format_str}' not yet implemented")
    
    return str(val)


def pb_isnull(val: Any) -> bool:
    """PowerBuilder IsNull function."""
    return val is None


def pb_abs(n: Any) -> Union[int, float]:
    """PowerBuilder Abs function."""
    return abs(ExpressionEvaluator()._coerce_numeric(n))


def pb_int(n: Any) -> int:
    """PowerBuilder Int function (truncates towards zero)."""
    num = ExpressionEvaluator()._coerce_numeric(n)
    return int(num)


def pb_round(n: Any, decimals: int = 0) -> Union[int, float]:
    """PowerBuilder Round function."""
    num = ExpressionEvaluator()._coerce_numeric(n)
    decimals = int(decimals)
    return round(num, decimals)


def pb_mod(n: Any, divisor: Any) -> Union[int, float]:
    """PowerBuilder Mod function."""
    num = ExpressionEvaluator()._coerce_numeric(n)
    div = ExpressionEvaluator()._coerce_numeric(divisor)
    if div == 0:
        raise EvaluationError("Modulo by zero")
    return num % div


def pb_max(*args: Any) -> Any:
    """PowerBuilder Max function."""
    if not args:
        return None
    
    # Filter out None values
    valid_args = [arg for arg in args if arg is not None]
    if not valid_args:
        return None
    
    return max(valid_args)


def pb_min(*args: Any) -> Any:
    """PowerBuilder Min function."""
    if not args:
        return None
    
    # Filter out None values
    valid_args = [arg for arg in args if arg is not None]
    if not valid_args:
        return None
    
    return min(valid_args)


# Dictionary of built-in functions
BUILTIN_FUNCTIONS: dict[str, Callable] = {
    # String functions
    'len': pb_len,
    'trim': pb_trim,
    'left': pb_left,
    'right': pb_right,
    'mid': pb_mid,
    'pos': pb_pos,
    'upper': pb_upper,
    'lower': pb_lower,
    'string': pb_string,
    
    # Type checking
    'isnull': pb_isnull,
    
    # Numeric functions
    'abs': pb_abs,
    'int': pb_int,
    'round': pb_round,
    'mod': pb_mod,
    'max': pb_max,
    'min': pb_min,
    
    # Add more built-in functions as needed
}


class ExpressionVisitor:
    """Visitor that evaluates expressions using the ExpressionEvaluator.
    
    This class provides compatibility with the visitor pattern used
    throughout the codebase while delegating actual evaluation to
    the ExpressionEvaluator.
    """
    
    def __init__(self, context: Optional[EvaluationContext] = None):
        """Initialize visitor with evaluation context."""
        self.evaluator = ExpressionEvaluator(context)
        self.context = self.evaluator.context
    
    def visit(self, node: Any) -> Any:
        """Visit a node and evaluate it."""
        return self.evaluator.evaluate(node)
    
    # Specific visit methods for expression types
    def visit_literal(self, node: PBLiteral) -> Any:
        """Visit a literal expression."""
        return self.evaluator._evaluate_pbliteral(node)
    
    def visit_boolean_literal(self, node: PBBooleanLiteral) -> bool:
        """Visit a boolean literal."""
        return self.evaluator._evaluate_pbbooleanliteral(node)
    
    def visit_null_literal(self, node: PBNullLiteral) -> None:
        """Visit a null literal."""
        return self.evaluator._evaluate_pbnullliteral(node)
    
    def visit_string_literal(self, node: PBStringLiteral) -> str:
        """Visit a string literal."""
        return self.evaluator._evaluate_pbstringliteral(node)
    
    def visit_number_literal(self, node: PBNumberLiteral) -> Union[int, float]:
        """Visit a number literal."""
        return self.evaluator._evaluate_pbnumberliteral(node)
    
    def visit_variable(self, node: PBVariable) -> Any:
        """Visit a variable reference."""
        return self.evaluator._evaluate_pbvariable(node)
    
    def visit_binary_operator(self, node: PBBinaryOperator) -> Any:
        """Visit a binary operator."""
        return self.evaluator._evaluate_pbbinaryoperator(node)
    
    def visit_unary_operator(self, node: PBUnaryOperator) -> Any:
        """Visit a unary operator."""
        return self.evaluator._evaluate_pbunaryoperator(node)
    
    def visit_function_call(self, node: PBFunctionCall) -> Any:
        """Visit a function call."""
        return self.evaluator._evaluate_pbfunctioncall(node)
    
    def visit_array_access(self, node: PBArrayAccess) -> Any:
        """Visit an array access."""
        return self.evaluator._evaluate_pbarrayaccess(node)
    
    def visit_member_access(self, node: PBMemberAccess) -> Any:
        """Visit a member access."""
        return self.evaluator._evaluate_pbmemberaccess(node)
    
    # Generic visit method for unknown nodes
    def generic_visit(self, node: Any) -> Any:
        """Generic visit for unknown node types."""
        return self.evaluator.evaluate(node)
