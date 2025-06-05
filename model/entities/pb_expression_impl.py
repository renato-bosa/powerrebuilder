"""PowerBuilder expression implementations.

This module provides concrete expression classes for PowerBuilder AST.
These classes implement the expression types expected by tests and used
throughout the codebase.
"""

from dataclasses import dataclass, field
from typing import Any, List

from ..ast.nodes import Expression, BinaryExpression, UnaryExpression, Literal
from ..utils.base import PBNode


# Base expression class
@dataclass
class PBExpressionNode(Expression):
    """Base PowerBuilder expression node."""
    
    expression_type: str = ""
    expression: Any = None
    expression_action: Any = None


# Literal expressions
@dataclass
class PBNumberLiteral(Literal):
    """Number literal expression."""
    
    def __init__(self, value: int | float):
        super().__init__(value=str(value), type="number")
        self._numeric_value = value
    
    @property
    def value(self) -> int | float:
        """Get numeric value."""
        return self._numeric_value


@dataclass
class PBStringLiteral(Literal):
    """String literal expression."""
    
    def __init__(self, value: str):
        super().__init__(value=value, type="string")


@dataclass
class PBBooleanLiteral(Literal):
    """Boolean literal expression."""
    
    def __init__(self, value: bool):
        super().__init__(value=str(value).lower(), type="boolean")
        self._bool_value = value
    
    @property
    def value(self) -> bool:
        """Get boolean value."""
        return self._bool_value


@dataclass
class PBNullLiteral(Literal):
    """Null literal expression."""
    
    def __init__(self):
        super().__init__(value="null", type="null")
    
    @property
    def value(self):
        """Get null value."""
        return None


# Binary arithmetic expressions
@dataclass
class PBAdditionExpression(BinaryExpression):
    """Addition expression."""
    
    def __init__(self, left: Expression, right: Expression):
        super().__init__(left=left, operator="+", right=right)


@dataclass
class PBSubtractionExpression(BinaryExpression):
    """Subtraction expression."""
    
    def __init__(self, left: Expression, right: Expression):
        super().__init__(left=left, operator="-", right=right)


@dataclass
class PBMultiplicationExpression(BinaryExpression):
    """Multiplication expression."""
    
    def __init__(self, left: Expression, right: Expression):
        super().__init__(left=left, operator="*", right=right)


@dataclass
class PBDivisionExpression(BinaryExpression):
    """Division expression."""
    
    def __init__(self, left: Expression, right: Expression):
        super().__init__(left=left, operator="/", right=right)


@dataclass
class PBPowerExpression(BinaryExpression):
    """Power (exponentiation) expression."""
    
    def __init__(self, left: Expression, right: Expression):
        super().__init__(left=left, operator="^", right=right)


# Comparison expressions
@dataclass
class PBGreaterThanExpression(BinaryExpression):
    """Greater than expression."""
    
    def __init__(self, left: Expression, right: Expression):
        super().__init__(left=left, operator=">", right=right)


@dataclass
class PBLessThanExpression(BinaryExpression):
    """Less than expression."""
    
    def __init__(self, left: Expression, right: Expression):
        super().__init__(left=left, operator="<", right=right)


@dataclass
class PBEqualityExpression(BinaryExpression):
    """Equality expression."""
    
    def __init__(self, left: Expression, right: Expression):
        super().__init__(left=left, operator="=", right=right)


@dataclass
class PBInequalityExpression(BinaryExpression):
    """Inequality expression."""
    
    def __init__(self, left: Expression, right: Expression):
        super().__init__(left=left, operator="<>", right=right)


# Logical expressions
@dataclass
class PBAndExpression(BinaryExpression):
    """Logical AND expression."""
    
    def __init__(self, left: Expression, right: Expression):
        super().__init__(left=left, operator="AND", right=right)


@dataclass
class PBOrExpression(BinaryExpression):
    """Logical OR expression."""
    
    def __init__(self, left: Expression, right: Expression):
        super().__init__(left=left, operator="OR", right=right)


@dataclass
class PBNotExpression(UnaryExpression):
    """Logical NOT expression."""
    
    def __init__(self, operand: Expression):
        super().__init__(operator="NOT", operand=operand)


# Unary expressions
@dataclass
class PBNegationExpression(UnaryExpression):
    """Numeric negation expression."""
    
    def __init__(self, operand: Expression):
        super().__init__(operator="-", operand=operand)


# Complex expressions
@dataclass
class PBIdentifierExpression(Expression):
    """Identifier reference expression."""
    
    name: str


@dataclass
class PBFunctionCallExpression(Expression):
    """Function call expression."""
    
    function_name: str
    arguments: List[Expression] = field(default_factory=list)


@dataclass
class PBMethodCallExpression(Expression):
    """Method call expression."""
    
    object: Expression
    method_name: str
    arguments: List[Expression] = field(default_factory=list)


@dataclass
class PBMemberAccessExpression(Expression):
    """Member access expression."""
    
    object: Expression
    member_name: str


@dataclass
class PBArrayAccessExpression(Expression):
    """Array access expression."""
    
    array: Expression
    index: Expression


@dataclass
class PBTernaryExpression(Expression):
    """Ternary conditional expression."""
    
    condition: Expression
    true_expression: Expression
    false_expression: Expression


@dataclass
class PBCastExpression(Expression):
    """Type cast expression."""
    
    expression: Expression
    target_type: str


@dataclass
class PBCreateExpression(Expression):
    """Object creation expression."""
    
    type_name: str
    arguments: List[Expression] = field(default_factory=list)


@dataclass
class PBAssignmentExpression(Expression):
    """Assignment expression."""
    
    target: Expression
    value: Expression