"""Consolidated AST expression nodes for PowerBuilder.

This module combines expression definitions from ast_nodes.py and entities/expressions.py,
providing a unified hierarchy for all expression types.
"""

from __future__ import annotations

import re
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from enum import Enum, auto
from typing import TYPE_CHECKING, Any, Optional, Union

from src.model.ast.nodes.base import Expression
from src.model.ast.nodes.declarations import Type
from src.model.types.base import NodeKind
from src.model.types import SourceAnchor

if TYPE_CHECKING:
    from src.model.ast.nodes.base import Statement


# ─── Expression Categories ────────────────────────────────────────────────────


class ExpressionKind(Enum):
    """Categories of expressions."""
    
    LITERAL = auto()
    IDENTIFIER = auto()
    BINARY = auto()
    UNARY = auto()
    TERNARY = auto()
    ASSIGNMENT = auto()
    FUNCTION_CALL = auto()
    METHOD_CALL = auto()
    ARRAY_ACCESS = auto()
    MEMBER_ACCESS = auto()
    CAST = auto()
    PARENTHESIZED = auto()
    LAMBDA = auto()
    SQL = auto()
    SPECIAL = auto()


# ─── Base Expression Node ─────────────────────────────────────────────────────


@dataclass
class ASTExpression(Expression):
    """Base class for all AST expressions."""
    
    source_anchor: Optional[SourceAnchor] = None
    parent_node: Optional[Any] = None
    
    @property
    @abstractmethod
    def kind(self) -> ExpressionKind:
        """Return the expression kind."""
        pass
    
    @property
    def node_kind(self) -> NodeKind:
        """Return the AST node kind."""
        return NodeKind.EXPRESSION
    
    def accept(self, visitor):
        """Accept a visitor."""
        method_name = f"visit_{self.__class__.__name__.lower()}"
        method = getattr(visitor, method_name, None)
        if method:
            return method(self)
        return visitor.generic_visit(self)
    
    def evaluate(self, context: Any = None) -> Any:
        """Evaluate the expression in the given context."""
        # Default implementation - subclasses should override
        return None


# ─── Literal Expressions ──────────────────────────────────────────────────────


@dataclass
class LiteralExpression(ASTExpression):
    """Base class for literal expressions."""
    
    value: Any = None
    literal_type: Optional[str] = None
    
    @property
    def kind(self) -> ExpressionKind:
        return ExpressionKind.LITERAL
    
    def evaluate(self, context: Any = None) -> Any:
        return self.value


@dataclass
class IntegerLiteral(LiteralExpression):
    """Integer literal expression."""
    
    value: int = 0
    
    def __post_init__(self):
        self.literal_type = "integer"


@dataclass
class LongLiteral(LiteralExpression):
    """Long integer literal expression."""
    
    value: int = 0
    
    def __post_init__(self):
        self.literal_type = "long"


@dataclass
class RealLiteral(LiteralExpression):
    """Real/float literal expression."""
    
    value: float = 0.0
    
    def __post_init__(self):
        self.literal_type = "real"


@dataclass
class DecimalLiteral(LiteralExpression):
    """Decimal literal expression."""
    
    value: Union[float, str] = 0.0  # Can be string for precise representation
    
    def __post_init__(self):
        self.literal_type = "decimal"


@dataclass
class StringLiteral(LiteralExpression):
    """String literal expression."""
    
    value: str = ""
    
    def __post_init__(self):
        self.literal_type = "string"


@dataclass
class BooleanLiteral(LiteralExpression):
    """Boolean literal expression."""
    
    value: bool = False
    
    def __post_init__(self):
        self.literal_type = "boolean"


@dataclass
class NullLiteral(LiteralExpression):
    """Null literal expression."""
    
    value: None = None
    
    def __post_init__(self):
        self.literal_type = "null"


@dataclass
class DateLiteral(LiteralExpression):
    """Date literal expression."""
    
    value: str = ""  # Date string representation
    
    def __post_init__(self):
        self.literal_type = "date"


@dataclass
class TimeLiteral(LiteralExpression):
    """Time literal expression."""
    
    value: str = ""  # Time string representation
    
    def __post_init__(self):
        self.literal_type = "time"


@dataclass
class DateTimeLiteral(LiteralExpression):
    """DateTime literal expression."""
    
    value: str = ""  # DateTime string representation
    
    def __post_init__(self):
        self.literal_type = "datetime"


# ─── Identifier Expressions ───────────────────────────────────────────────────


@dataclass
class IdentifierExpression(ASTExpression):
    """Identifier reference expression."""
    
    name: str = ""
    is_qualified: bool = False
    qualifier: Optional[str] = None
    
    @property
    def kind(self) -> ExpressionKind:
        return ExpressionKind.IDENTIFIER
    
    def __post_init__(self):
        if not self.name:
            raise ValueError("IdentifierExpression requires name")
    
    def evaluate(self, context: Any = None) -> Any:
        if context and hasattr(context, 'get_variable'):
            return context.get_variable(self.name)
        return None


@dataclass
class ThisExpression(IdentifierExpression):
    """'this' reference expression."""
    
    def __post_init__(self):
        self.name = "this"


@dataclass
class SuperExpression(IdentifierExpression):
    """'super' reference expression."""
    
    def __post_init__(self):
        self.name = "super"


@dataclass
class ParentExpression(IdentifierExpression):
    """'parent' reference expression."""
    
    def __post_init__(self):
        self.name = "parent"


# ─── Binary Expressions ───────────────────────────────────────────────────────


@dataclass
class BinaryExpression(ASTExpression):
    """Binary operator expression."""
    
    left: Optional[Expression] = None
    operator: str = ""
    right: Optional[Expression] = None
    
    @property
    def kind(self) -> ExpressionKind:
        return ExpressionKind.BINARY
    
    def __post_init__(self):
        if not self.operator:
            raise ValueError("BinaryExpression requires operator")
    
    def evaluate(self, context: Any = None) -> Any:
        # Delegate to evaluator for complex logic
        return None


@dataclass
class ArithmeticExpression(BinaryExpression):
    """Arithmetic binary expression (+, -, *, /, ^)."""
    pass


@dataclass
class ComparisonExpression(BinaryExpression):
    """Comparison binary expression (=, <>, <, >, <=, >=)."""
    pass


@dataclass
class LogicalExpression(BinaryExpression):
    """Logical binary expression (AND, OR)."""
    pass


@dataclass
class AssignmentExpression(BinaryExpression):
    """Assignment expression (=)."""
    
    @property
    def kind(self) -> ExpressionKind:
        return ExpressionKind.ASSIGNMENT


@dataclass
class CompoundAssignmentExpression(AssignmentExpression):
    """Compound assignment expression (+=, -=, *=, /=)."""
    pass


# ─── Unary Expressions ────────────────────────────────────────────────────────


@dataclass
class UnaryExpression(ASTExpression):
    """Unary operator expression."""
    
    operator: str = ""
    operand: Optional[Expression] = None
    is_prefix: bool = True  # True for prefix, False for postfix
    
    @property
    def kind(self) -> ExpressionKind:
        return ExpressionKind.UNARY
    
    def __post_init__(self):
        if not self.operator:
            raise ValueError("UnaryExpression requires operator")


@dataclass
class NotExpression(UnaryExpression):
    """Logical NOT expression."""
    
    def __post_init__(self):
        self.operator = "NOT"
        self.is_prefix = True


@dataclass
class NegationExpression(UnaryExpression):
    """Numeric negation expression (-)."""
    
    def __post_init__(self):
        self.operator = "-"
        self.is_prefix = True


@dataclass
class IncrementExpression(UnaryExpression):
    """Increment expression (++)."""
    
    def __post_init__(self):
        self.operator = "++"


@dataclass
class DecrementExpression(UnaryExpression):
    """Decrement expression (--)."""
    
    def __post_init__(self):
        self.operator = "--"


# ─── Ternary Expression ───────────────────────────────────────────────────────


@dataclass
class TernaryExpression(ASTExpression):
    """Ternary/conditional expression (condition ? true_expr : false_expr)."""
    
    condition: Optional[Expression] = None
    true_expression: Optional[Expression] = None
    false_expression: Optional[Expression] = None
    
    @property
    def kind(self) -> ExpressionKind:
        return ExpressionKind.TERNARY
    
    def __post_init__(self):
        if not all([self.condition, self.true_expression, self.false_expression]):
            raise ValueError("TernaryExpression requires all three expressions")


# ─── Function/Method Call Expressions ─────────────────────────────────────────


@dataclass
class CallExpression(ASTExpression):
    """Base class for call expressions."""
    
    arguments: list[Expression] = field(default_factory=list)
    
    @property
    def kind(self) -> ExpressionKind:
        return ExpressionKind.FUNCTION_CALL


@dataclass
class FunctionCallExpression(CallExpression):
    """Function call expression."""
    
    function_name: str = ""
    
    def __post_init__(self):
        if not self.function_name:
            raise ValueError("FunctionCallExpression requires function_name")


@dataclass
class MethodCallExpression(CallExpression):
    """Method call expression."""
    
    object_expression: Optional[Expression] = None
    method_name: str = ""
    is_dynamic: bool = False  # For dynamic method calls
    
    @property
    def kind(self) -> ExpressionKind:
        return ExpressionKind.METHOD_CALL
    
    def __post_init__(self):
        if not self.method_name:
            raise ValueError("MethodCallExpression requires method_name")


@dataclass
class ConstructorCallExpression(CallExpression):
    """Constructor call expression (CREATE/NEW)."""
    
    class_name: str = ""
    
    def __post_init__(self):
        if not self.class_name:
            raise ValueError("ConstructorCallExpression requires class_name")


# ─── Array/Member Access Expressions ──────────────────────────────────────────


@dataclass
class ArrayAccessExpression(ASTExpression):
    """Array element access expression."""
    
    array_expression: Optional[Expression] = None
    indices: list[Expression] = field(default_factory=list)
    
    @property
    def kind(self) -> ExpressionKind:
        return ExpressionKind.ARRAY_ACCESS
    
    def __post_init__(self):
        if not self.array_expression:
            raise ValueError("ArrayAccessExpression requires array_expression")
        if not self.indices:
            raise ValueError("ArrayAccessExpression requires at least one index")


@dataclass
class MemberAccessExpression(ASTExpression):
    """Member access expression (dot notation)."""
    
    object_expression: Optional[Expression] = None
    member_name: str = ""
    
    @property
    def kind(self) -> ExpressionKind:
        return ExpressionKind.MEMBER_ACCESS
    
    def __post_init__(self):
        if not self.object_expression:
            raise ValueError("MemberAccessExpression requires object_expression")
        if not self.member_name:
            raise ValueError("MemberAccessExpression requires member_name")


# ─── Type Cast Expression ─────────────────────────────────────────────────────


@dataclass
class CastExpression(ASTExpression):
    """Type cast expression."""
    
    expression: Optional[Expression] = None
    target_type: Union[Type, str] = ""
    
    @property
    def kind(self) -> ExpressionKind:
        return ExpressionKind.CAST
    
    def __post_init__(self):
        if not self.expression:
            raise ValueError("CastExpression requires expression")
        if not self.target_type:
            raise ValueError("CastExpression requires target_type")


# ─── Parenthesized Expression ─────────────────────────────────────────────────


@dataclass
class ParenthesizedExpression(ASTExpression):
    """Parenthesized expression for grouping."""
    
    expression: Optional[Expression] = None
    
    @property
    def kind(self) -> ExpressionKind:
        return ExpressionKind.PARENTHESIZED
    
    def __post_init__(self):
        if not self.expression:
            raise ValueError("ParenthesizedExpression requires expression")
    
    def evaluate(self, context: Any = None) -> Any:
        if self.expression and hasattr(self.expression, 'evaluate'):
            return self.expression.evaluate(context)
        return None


# ─── Lambda Expression ────────────────────────────────────────────────────────


@dataclass
class LambdaExpression(ASTExpression):
    """Lambda/anonymous function expression."""
    
    parameters: list[str] = field(default_factory=list)
    body: Optional[Expression] = None
    
    @property
    def kind(self) -> ExpressionKind:
        return ExpressionKind.LAMBDA
    
    def __post_init__(self):
        if not self.body:
            raise ValueError("LambdaExpression requires body")


# ─── SQL-Related Expressions ──────────────────────────────────────────────────


@dataclass
class InExpression(ASTExpression):
    """SQL IN operator expression."""
    
    value_expression: Optional[Expression] = None
    in_list: list[Expression] = field(default_factory=list)
    is_not_in: bool = False
    
    @property
    def kind(self) -> ExpressionKind:
        return ExpressionKind.SQL
    
    def __post_init__(self):
        if not self.value_expression:
            raise ValueError("InExpression requires value_expression")
        if not self.in_list:
            raise ValueError("InExpression requires non-empty in_list")


@dataclass
class BetweenExpression(ASTExpression):
    """SQL BETWEEN operator expression."""
    
    value_expression: Optional[Expression] = None
    lower_bound: Optional[Expression] = None
    upper_bound: Optional[Expression] = None
    is_not_between: bool = False
    
    @property
    def kind(self) -> ExpressionKind:
        return ExpressionKind.SQL
    
    def __post_init__(self):
        if not all([self.value_expression, self.lower_bound, self.upper_bound]):
            raise ValueError("BetweenExpression requires all expressions")


@dataclass
class LikeExpression(ASTExpression):
    """SQL LIKE pattern matching expression."""
    
    value_expression: Optional[Expression] = None
    pattern: Optional[Expression] = None
    escape_char: Optional[str] = None
    is_not_like: bool = False
    
    @property
    def kind(self) -> ExpressionKind:
        return ExpressionKind.SQL
    
    def __post_init__(self):
        if not self.value_expression or not self.pattern:
            raise ValueError("LikeExpression requires value_expression and pattern")


@dataclass
class ExistsExpression(ASTExpression):
    """SQL EXISTS subquery expression."""
    
    subquery: Optional[Expression] = None  # Should be a SelectStatement
    is_not_exists: bool = False
    
    @property
    def kind(self) -> ExpressionKind:
        return ExpressionKind.SQL
    
    def __post_init__(self):
        if not self.subquery:
            raise ValueError("ExistsExpression requires subquery")


@dataclass
class CaseExpression(ASTExpression):
    """SQL CASE expression."""
    
    case_value: Optional[Expression] = None  # For simple CASE
    when_clauses: list[WhenClause] = field(default_factory=list)
    else_expression: Optional[Expression] = None
    
    @property
    def kind(self) -> ExpressionKind:
        return ExpressionKind.SQL
    
    def __post_init__(self):
        if not self.when_clauses:
            raise ValueError("CaseExpression requires at least one WHEN clause")


@dataclass
class WhenClause:
    """WHEN clause for CASE expression."""
    
    condition: Optional[Expression] = None
    result: Optional[Expression] = None
    
    def __post_init__(self):
        if not self.condition or not self.result:
            raise ValueError("WhenClause requires condition and result")


# ─── Special PowerBuilder Expressions ─────────────────────────────────────────


@dataclass
class CreateExpression(ASTExpression):
    """CREATE object expression."""
    
    class_name: str = ""
    using_expression: Optional[Expression] = None  # For CREATE USING
    
    @property
    def kind(self) -> ExpressionKind:
        return ExpressionKind.SPECIAL
    
    def __post_init__(self):
        if not self.class_name:
            raise ValueError("CreateExpression requires class_name")


@dataclass
class DataWindowExpression(ASTExpression):
    """DataWindow-related expression."""
    
    datawindow_name: str = ""
    operation: str = ""  # e.g., "Describe", "Modify", etc.
    arguments: list[Expression] = field(default_factory=list)
    
    @property
    def kind(self) -> ExpressionKind:
        return ExpressionKind.SPECIAL
    
    def __post_init__(self):
        if not self.datawindow_name or not self.operation:
            raise ValueError("DataWindowExpression requires datawindow_name and operation")


@dataclass
class EventExpression(ASTExpression):
    """Event triggering expression."""
    
    event_name: str = ""
    object_expression: Optional[Expression] = None
    arguments: list[Expression] = field(default_factory=list)
    is_post: bool = False  # POST vs immediate
    
    @property
    def kind(self) -> ExpressionKind:
        return ExpressionKind.SPECIAL
    
    def __post_init__(self):
        if not self.event_name:
            raise ValueError("EventExpression requires event_name")


@dataclass
class DynamicExpression(ASTExpression):
    """Dynamic property/method access expression."""
    
    object_expression: Optional[Expression] = None
    property_name: Optional[Expression] = None  # String expression
    
    @property
    def kind(self) -> ExpressionKind:
        return ExpressionKind.SPECIAL
    
    def __post_init__(self):
        if not self.object_expression or not self.property_name:
            raise ValueError("DynamicExpression requires object_expression and property_name")


# ─── Expression Factory ───────────────────────────────────────────────────────


class ExpressionFactory:
    """Factory for creating expression nodes."""
    
    @staticmethod
    def create_literal(value: Any, literal_type: Optional[str] = None) -> LiteralExpression:
        """Create appropriate literal expression based on value type."""
        if literal_type:
            type_map = {
                'integer': IntegerLiteral,
                'long': LongLiteral,
                'real': RealLiteral,
                'decimal': DecimalLiteral,
                'string': StringLiteral,
                'boolean': BooleanLiteral,
                'null': NullLiteral,
                'date': DateLiteral,
                'time': TimeLiteral,
                'datetime': DateTimeLiteral,
            }
            cls = type_map.get(literal_type, LiteralExpression)
            return cls(value=value)
        
        # Infer type from value
        if value is None:
            return NullLiteral()
        elif isinstance(value, bool):
            return BooleanLiteral(value=value)
        elif isinstance(value, int):
            return IntegerLiteral(value=value)
        elif isinstance(value, float):
            return RealLiteral(value=value)
        elif isinstance(value, str):
            return StringLiteral(value=value)
        else:
            return LiteralExpression(value=value)
    
    @staticmethod
    def create_binary(left: Expression, operator: str, right: Expression) -> BinaryExpression:
        """Create appropriate binary expression based on operator."""
        operator_upper = operator.upper()
        
        # Arithmetic operators
        if operator in ['+', '-', '*', '/', '^', '%', 'MOD']:
            return ArithmeticExpression(left=left, operator=operator, right=right)
        
        # Comparison operators
        elif operator in ['=', '<>', '<', '>', '<=', '>=']:
            return ComparisonExpression(left=left, operator=operator, right=right)
        
        # Logical operators
        elif operator_upper in ['AND', 'OR']:
            return LogicalExpression(left=left, operator=operator_upper, right=right)
        
        # Assignment operators
        elif operator == '=':
            return AssignmentExpression(left=left, operator=operator, right=right)
        
        # Compound assignment
        elif operator in ['+=', '-=', '*=', '/=']:
            return CompoundAssignmentExpression(left=left, operator=operator, right=right)
        
        else:
            return BinaryExpression(left=left, operator=operator, right=right)
    
    @staticmethod
    def create_unary(operator: str, operand: Expression, is_prefix: bool = True) -> UnaryExpression:
        """Create appropriate unary expression based on operator."""
        operator_upper = operator.upper()
        
        if operator_upper == 'NOT':
            return NotExpression(operand=operand)
        elif operator == '-':
            return NegationExpression(operand=operand)
        elif operator == '++':
            return IncrementExpression(operand=operand, is_prefix=is_prefix)
        elif operator == '--':
            return DecrementExpression(operand=operand, is_prefix=is_prefix)
        else:
            return UnaryExpression(operator=operator, operand=operand, is_prefix=is_prefix)
    
    @staticmethod
    def create_identifier(name: str) -> IdentifierExpression:
        """Create appropriate identifier expression."""
        name_lower = name.lower()
        
        if name_lower == 'this':
            return ThisExpression()
        elif name_lower == 'super':
            return SuperExpression()
        elif name_lower == 'parent':
            return ParentExpression()
        else:
            return IdentifierExpression(name=name)


# ─── Expression Utilities ─────────────────────────────────────────────────────


class ExpressionUtils:
    """Utility functions for working with expressions."""
    
    @staticmethod
    def is_constant(expr: Expression) -> bool:
        """Check if expression is a compile-time constant."""
        return isinstance(expr, LiteralExpression)
    
    @staticmethod
    def is_lvalue(expr: Expression) -> bool:
        """Check if expression can be assigned to (left-value)."""
        return isinstance(expr, (
            IdentifierExpression,
            MemberAccessExpression,
            ArrayAccessExpression,
        ))
    
    @staticmethod
    def extract_identifier(expr: Expression) -> Optional[str]:
        """Extract identifier name from expression if possible."""
        if isinstance(expr, IdentifierExpression):
            return expr.name
        elif isinstance(expr, MemberAccessExpression):
            return expr.member_name
        return None
    
    @staticmethod
    def simplify(expr: Expression) -> Expression:
        """Simplify expression if possible (constant folding, etc.)."""
        # Basic constant folding for binary expressions
        if isinstance(expr, BinaryExpression):
            if (isinstance(expr.left, LiteralExpression) and 
                isinstance(expr.right, LiteralExpression)):
                
                left_val = expr.left.value
                right_val = expr.right.value
                
                try:
                    if expr.operator == '+':
                        result = left_val + right_val
                    elif expr.operator == '-':
                        result = left_val - right_val
                    elif expr.operator == '*':
                        result = left_val * right_val
                    elif expr.operator == '/' and right_val != 0:
                        result = left_val / right_val
                    else:
                        return expr
                    
                    return ExpressionFactory.create_literal(result)
                except:
                    pass
        
        # Simplify parenthesized expressions with single literal
        elif isinstance(expr, ParenthesizedExpression):
            if isinstance(expr.expression, LiteralExpression):
                return expr.expression
        
        return expr


# ─── Export all expression classes ────────────────────────────────────────────


__all__ = [
    # Base classes
    'ExpressionKind',
    'ASTExpression',
    
    # Literal expressions
    'LiteralExpression',
    'IntegerLiteral',
    'LongLiteral',
    'RealLiteral',
    'DecimalLiteral',
    'StringLiteral',
    'BooleanLiteral',
    'NullLiteral',
    'DateLiteral',
    'TimeLiteral',
    'DateTimeLiteral',
    
    # Identifier expressions
    'IdentifierExpression',
    'ThisExpression',
    'SuperExpression',
    'ParentExpression',
    
    # Binary expressions
    'BinaryExpression',
    'ArithmeticExpression',
    'ComparisonExpression',
    'LogicalExpression',
    'AssignmentExpression',
    'CompoundAssignmentExpression',
    
    # Unary expressions
    'UnaryExpression',
    'NotExpression',
    'NegationExpression',
    'IncrementExpression',
    'DecrementExpression',
    
    # Other expression types
    'TernaryExpression',
    'CallExpression',
    'FunctionCallExpression',
    'MethodCallExpression',
    'ConstructorCallExpression',
    'ArrayAccessExpression',
    'MemberAccessExpression',
    'CastExpression',
    'ParenthesizedExpression',
    'LambdaExpression',
    
    # SQL expressions
    'InExpression',
    'BetweenExpression',
    'LikeExpression',
    'ExistsExpression',
    'CaseExpression',
    'WhenClause',
    
    # PowerBuilder-specific expressions
    'CreateExpression',
    'DataWindowExpression',
    'EventExpression',
    'DynamicExpression',
    
    # Utilities
    'ExpressionFactory',
    'ExpressionUtils',
]
