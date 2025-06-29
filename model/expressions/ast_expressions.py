"""Consolidated AST expression nodes for PowerBuilder.

This module combines expression definitions from ast_nodes.py and entities/expressions.py,
providing a unified hierarchy for all expression types.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from enum import Enum, auto
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from src.model.ast.nodes.declarations import Type
    from model.utils.base import SourceAnchor


class BinaryOperator(Enum):
    """Binary operators in PowerBuilder."""
    
    # Arithmetic
    ADD = "+"
    SUBTRACT = "-"
    MULTIPLY = "*"
    DIVIDE = "/"
    POWER = "^"
    MODULO = "MOD"
    
    # Comparison
    EQUAL = "="
    NOT_EQUAL = "<>"
    LESS_THAN = "<"
    GREATER_THAN = ">"
    LESS_EQUAL = "<="
    GREATER_EQUAL = ">="
    
    # Logical
    AND = "AND"
    OR = "OR"
    
    # String
    CONCATENATE = "&"
    
    # Assignment
    ASSIGN = "="
    ADD_ASSIGN = "+="
    SUBTRACT_ASSIGN = "-="
    MULTIPLY_ASSIGN = "*="
    DIVIDE_ASSIGN = "/="


class UnaryOperator(Enum):
    """Unary operators in PowerBuilder."""
    
    NOT = "NOT"
    NEGATE = "-"
    POSITIVE = "+"
    INCREMENT = "++"
    DECREMENT = "--"


class ExpressionKind(Enum):
    """Kinds of expressions."""
    
    LITERAL = auto()
    VARIABLE = auto()
    BINARY = auto()
    UNARY = auto()
    CALL = auto()
    FIELD_ACCESS = auto()
    ARRAY_ACCESS = auto()
    CAST = auto()
    CONDITIONAL = auto()
    THIS = auto()
    SUPER = auto()
    PARENT = auto()
    SQL_VARIABLE = auto()
    DYNAMIC_SQL = auto()
    LAMBDA = auto()
    IN = auto()
    LIKE = auto()
    BETWEEN = auto()
    EXISTS = auto()


# Base Expression Classes
@dataclass
class Expression(ABC):
    """Base class for all expressions."""
    
    source_anchor: SourceAnchor | None = field(default=None)
    type: Type | None = field(default=None, init=False)
    
    @property
    @abstractmethod
    def kind(self) -> ExpressionKind:
        """Return the kind of this expression."""
    
    @abstractmethod
    def evaluate(self, context: Any = None) -> Any:
        """Evaluate the expression with optional context."""


# Literal Expressions
@dataclass
class Literal(Expression):
    """Base class for literal expressions."""
    
    value: Any = field(default=None)
    
    @property
    def kind(self) -> ExpressionKind:
        return ExpressionKind.LITERAL


@dataclass
class IntegerLiteral(Literal):
    """Integer literal expression."""
    
    value: int = 0
    
    def evaluate(self, context: Any = None) -> int:
        return self.value


@dataclass
class RealLiteral(Literal):
    """Real number literal expression."""
    
    value: float = 0.0
    
    def evaluate(self, context: Any = None) -> float:
        return self.value


@dataclass
class StringLiteral(Literal):
    """String literal expression."""
    
    value: str = ""
    
    def evaluate(self, context: Any = None) -> str:
        return self.value


@dataclass
class BooleanLiteral(Literal):
    """Boolean literal expression."""
    
    value: bool = False
    
    def evaluate(self, context: Any = None) -> bool:
        return self.value


@dataclass
class NullLiteral(Literal):
    """Null literal expression."""
    
    value: None = None
    
    def evaluate(self, context: Any = None) -> None:
        return None


# Variable and Reference Expressions
@dataclass
class Variable(Expression):
    """Variable reference expression."""
    
    name: str = ""
    
    @property
    def kind(self) -> ExpressionKind:
        return ExpressionKind.VARIABLE
    
    def evaluate(self, context: Any = None) -> Any:
        if context and hasattr(context, 'get_variable'):
            return context.get_variable(self.name)
        return f"${self.name}"


@dataclass
class FieldAccessExpression(Expression):
    """Field access expression (object.field)."""
    
    object: Expression | None = None
    field: str = ""
    
    @property
    def kind(self) -> ExpressionKind:
        return ExpressionKind.FIELD_ACCESS
    
    def evaluate(self, context: Any = None) -> Any:
        if self.object and context:
            obj = self.object.evaluate(context)
            if hasattr(obj, self.field):
                return getattr(obj, self.field)
        return f"{self.object.evaluate(context) if self.object else 'null'}.{self.field}"


# Operator Expressions
@dataclass
class BinaryExpression(Expression):
    """Binary operator expression."""
    
    left: Expression | None = None
    operator: BinaryOperator = BinaryOperator.ADD
    right: Expression | None = None
    
    @property
    def kind(self) -> ExpressionKind:
        return ExpressionKind.BINARY
    
    def evaluate(self, context: Any = None) -> Any:
        if not self.left or not self.right:
            return None
            
        left_val = self.left.evaluate(context)
        right_val = self.right.evaluate(context)
        
        # Arithmetic operators
        if self.operator == BinaryOperator.ADD:
            return left_val + right_val
        elif self.operator == BinaryOperator.SUBTRACT:
            return left_val - right_val
        elif self.operator == BinaryOperator.MULTIPLY:
            return left_val * right_val
        elif self.operator == BinaryOperator.DIVIDE:
            return left_val / right_val if right_val != 0 else None
        elif self.operator == BinaryOperator.POWER:
            return left_val ** right_val
        elif self.operator == BinaryOperator.MODULO:
            return left_val % right_val
        
        # Comparison operators
        elif self.operator == BinaryOperator.EQUAL:
            return left_val == right_val
        elif self.operator == BinaryOperator.NOT_EQUAL:
            return left_val != right_val
        elif self.operator == BinaryOperator.LESS_THAN:
            return left_val < right_val
        elif self.operator == BinaryOperator.GREATER_THAN:
            return left_val > right_val
        elif self.operator == BinaryOperator.LESS_EQUAL:
            return left_val <= right_val
        elif self.operator == BinaryOperator.GREATER_EQUAL:
            return left_val >= right_val
        
        # Logical operators
        elif self.operator == BinaryOperator.AND:
            return left_val and right_val
        elif self.operator == BinaryOperator.OR:
            return left_val or right_val
        
        # String concatenation
        elif self.operator == BinaryOperator.CONCATENATE:
            return str(left_val) + str(right_val)
        
        return None


@dataclass
class UnaryExpression(Expression):
    """Unary operator expression."""
    
    operator: UnaryOperator = UnaryOperator.NEGATE
    operand: Expression | None = None
    
    @property
    def kind(self) -> ExpressionKind:
        return ExpressionKind.UNARY
    
    def evaluate(self, context: Any = None) -> Any:
        if not self.operand:
            return None
            
        val = self.operand.evaluate(context)
        
        if self.operator == UnaryOperator.NOT:
            return not val
        elif self.operator == UnaryOperator.NEGATE:
            return -val
        elif self.operator == UnaryOperator.POSITIVE:
            return +val
        
        return val


# Complex Expressions
@dataclass
class CallExpression(Expression):
    """Function or method call expression."""
    
    function: Expression | None = None
    arguments: list[Expression] = field(default_factory=list)
    
    @property
    def kind(self) -> ExpressionKind:
        return ExpressionKind.CALL
    
    def evaluate(self, context: Any = None) -> Any:
        func_name = self.function.evaluate(context) if self.function else "unknown"
        args = [arg.evaluate(context) for arg in self.arguments]
        
        if context and hasattr(context, 'call_function'):
            return context.call_function(func_name, args)
        
        return f"{func_name}({', '.join(str(arg) for arg in args)})"


@dataclass
class ArrayAccessExpression(Expression):
    """Array access expression (array[index])."""
    
    array: Expression | None = None
    index: Expression | None = None
    
    @property
    def kind(self) -> ExpressionKind:
        return ExpressionKind.ARRAY_ACCESS
    
    def evaluate(self, context: Any = None) -> Any:
        if not self.array or not self.index:
            return None
            
        arr = self.array.evaluate(context)
        idx = self.index.evaluate(context)
        
        if isinstance(arr, list) and isinstance(idx, int) and 0 <= idx < len(arr):
            return arr[idx]
        
        return f"{arr}[{idx}]"


@dataclass
class ConditionalExpression(Expression):
    """Ternary conditional expression (condition ? true_expr : false_expr)."""
    
    condition: Expression | None = None
    true_expression: Expression | None = None
    false_expression: Expression | None = None
    
    @property
    def kind(self) -> ExpressionKind:
        return ExpressionKind.CONDITIONAL
    
    def evaluate(self, context: Any = None) -> Any:
        if not self.condition:
            return None
            
        cond_val = self.condition.evaluate(context)
        
        if cond_val:
            return self.true_expression.evaluate(context) if self.true_expression else None
        else:
            return self.false_expression.evaluate(context) if self.false_expression else None


@dataclass
class CastExpression(Expression):
    """Type cast expression."""
    
    expression: Expression | None = None
    target_type: str = ""
    
    @property
    def kind(self) -> ExpressionKind:
        return ExpressionKind.CAST
    
    def evaluate(self, context: Any = None) -> Any:
        if not self.expression:
            return None
            
        val = self.expression.evaluate(context)
        
        # Attempt type conversion
        if self.target_type.lower() in ['integer', 'long']:
            try:
                return int(val)
            except (ValueError, TypeError):
                return None
        elif self.target_type.lower() in ['real', 'double', 'decimal']:
            try:
                return float(val)
            except (ValueError, TypeError):
                return None
        elif self.target_type.lower() == 'string':
            return str(val)
        elif self.target_type.lower() == 'boolean':
            return bool(val)
        
        return val


# PowerBuilder-specific Expressions
@dataclass
class ThisExpression(Expression):
    """'this' reference in PowerBuilder."""
    
    @property
    def kind(self) -> ExpressionKind:
        return ExpressionKind.THIS
    
    def evaluate(self, context: Any = None) -> Any:
        if context and hasattr(context, 'get_this'):
            return context.get_this()
        return "this"


@dataclass
class SuperExpression(Expression):
    """'super' reference in PowerBuilder."""
    
    @property
    def kind(self) -> ExpressionKind:
        return ExpressionKind.SUPER
    
    def evaluate(self, context: Any = None) -> Any:
        if context and hasattr(context, 'get_super'):
            return context.get_super()
        return "super"


@dataclass
class ParentExpression(Expression):
    """'parent' reference in PowerBuilder."""
    
    @property
    def kind(self) -> ExpressionKind:
        return ExpressionKind.PARENT
    
    def evaluate(self, context: Any = None) -> Any:
        if context and hasattr(context, 'get_parent'):
            return context.get_parent()
        return "parent"


# SQL-related Expressions
@dataclass
class SqlVariableExpression(Expression):
    """SQL variable expression (:variable)."""
    
    variable_name: str = ""
    
    @property
    def kind(self) -> ExpressionKind:
        return ExpressionKind.SQL_VARIABLE
    
    def evaluate(self, context: Any = None) -> Any:
        if context and hasattr(context, 'get_sql_variable'):
            return context.get_sql_variable(self.variable_name)
        return f":{self.variable_name}"


@dataclass
class InExpression(Expression):
    """SQL IN expression."""
    
    expression: Expression | None = None
    values: list[Expression] = field(default_factory=list)
    
    @property
    def kind(self) -> ExpressionKind:
        return ExpressionKind.IN
    
    def evaluate(self, context: Any = None) -> Any:
        if not self.expression:
            return False
            
        expr_val = self.expression.evaluate(context)
        value_list = [v.evaluate(context) for v in self.values]
        
        return expr_val in value_list


@dataclass
class LikeExpression(Expression):
    """SQL LIKE expression."""
    
    expression: Expression | None = None
    pattern: Expression | None = None
    
    @property
    def kind(self) -> ExpressionKind:
        return ExpressionKind.LIKE
    
    def evaluate(self, context: Any = None) -> Any:
        if not self.expression or not self.pattern:
            return False
            
        expr_val = str(self.expression.evaluate(context))
        pattern_val = str(self.pattern.evaluate(context))
        
        # Simple LIKE implementation (would need proper SQL LIKE logic)
        import re
        pattern_regex = pattern_val.replace('%', '.*').replace('_', '.')
        return bool(re.match(pattern_regex, expr_val))


@dataclass
class BetweenExpression(Expression):
    """SQL BETWEEN expression."""
    
    expression: Expression | None = None
    lower_bound: Expression | None = None
    upper_bound: Expression | None = None
    
    @property
    def kind(self) -> ExpressionKind:
        return ExpressionKind.BETWEEN
    
    def evaluate(self, context: Any = None) -> Any:
        if not all([self.expression, self.lower_bound, self.upper_bound]):
            return False
            
        val = self.expression.evaluate(context)
        lower = self.lower_bound.evaluate(context)
        upper = self.upper_bound.evaluate(context)
        
        return lower <= val <= upper


@dataclass
class ExistsExpression(Expression):
    """SQL EXISTS expression."""
    
    subquery: Any = None  # Would be a SQL query node
    
    @property
    def kind(self) -> ExpressionKind:
        return ExpressionKind.EXISTS
    
    def evaluate(self, context: Any = None) -> Any:
        # EXISTS would need SQL execution context
        return f"EXISTS({self.subquery})"