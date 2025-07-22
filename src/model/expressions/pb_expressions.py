"""PowerBuilder-specific expression nodes with PB prefix.

This module provides PowerBuilder-specific expression nodes that are used by the
decompiler's data flow analysis. These are aliases and specialized versions of
the base expression nodes.
"""

from dataclasses import dataclass, field
from typing import Any

from src.model.ast.nodes.base import Expression


@dataclass
class PBLiteral(Expression):
    """Base class for PowerBuilder literals."""
    
    value: Any = None
    
    @property
    def kind(self):
        return "LITERAL"
    
    def evaluate(self, context: Any = None) -> Any:
        return self.value


@dataclass
class PBBooleanLiteral(PBLiteral):
    """PowerBuilder boolean literal."""
    
    value: bool = False


@dataclass
class PBNullLiteral(PBLiteral):
    """PowerBuilder null literal."""
    
    value: None = None


@dataclass
class PBStringLiteral(PBLiteral):
    """PowerBuilder string literal."""
    
    value: str = ""


@dataclass
class PBNumberLiteral(PBLiteral):
    """PowerBuilder numeric literal that can be integer or real."""
    
    value: int | float = 0


@dataclass
class PBVariable(Expression):
    """PowerBuilder variable reference."""
    
    name: str = ""
    
    @property
    def kind(self):
        return "VARIABLE"
    
    def evaluate(self, context: Any = None) -> Any:
        if context and hasattr(context, 'get'):
            return context.get(self.name)
        return None


@dataclass
class PBBinaryOperator(Expression):
    """PowerBuilder binary operator expression."""
    
    left: Expression | None = None
    operator: str = ""
    right: Expression | None = None
    
    @property
    def kind(self):
        return "BINARY"
    
    def evaluate(self, context: Any = None) -> Any:
        if not self.left or not self.right:
            return None
        left_val = self.left.evaluate(context) if hasattr(self.left, 'evaluate') else self.left
        right_val = self.right.evaluate(context) if hasattr(self.right, 'evaluate') else self.right
        
        # Basic operator evaluation
        if self.operator == '+':
            return left_val + right_val
        elif self.operator == '-':
            return left_val - right_val
        elif self.operator == '*':
            return left_val * right_val
        elif self.operator == '/':
            return left_val / right_val if right_val != 0 else None
        elif self.operator == '=':
            return left_val == right_val
        elif self.operator == '<>':
            return left_val != right_val
        elif self.operator == '<':
            return left_val < right_val
        elif self.operator == '>':
            return left_val > right_val
        elif self.operator == '<=':
            return left_val <= right_val
        elif self.operator == '>=':
            return left_val >= right_val
        elif self.operator == 'AND':
            return left_val and right_val
        elif self.operator == 'OR':
            return left_val or right_val
        else:
            return None


@dataclass
class PBUnaryOperator(Expression):
    """PowerBuilder unary operator expression."""
    
    operator: str = ""
    operand: Expression | None = None
    
    @property
    def kind(self):
        return "UNARY"
    
    def evaluate(self, context: Any = None) -> Any:
        if not self.operand:
            return None
        val = self.operand.evaluate(context) if hasattr(self.operand, 'evaluate') else self.operand
        
        if self.operator == '-':
            return -val
        elif self.operator == '+':
            return +val
        elif self.operator == 'NOT':
            return not val
        else:
            return None


@dataclass
class PBFunctionCall(Expression):
    """PowerBuilder function call expression."""
    
    function_name: str = ""
    arguments: list[Expression] = field(default_factory=list)
    
    @property
    def kind(self):
        return "FUNCTION_CALL"
    
    def evaluate(self, context: Any = None) -> Any:
        # Function evaluation would require a function registry
        # For now, just return None
        return None


@dataclass
class PBArrayAccess(Expression):
    """PowerBuilder array access expression."""
    
    array: Expression | None = None
    indices: list[Expression] = field(default_factory=list)
    
    @property
    def kind(self):
        return "ARRAY_ACCESS"
    
    def evaluate(self, context: Any = None) -> Any:
        # Array access evaluation would require array value resolution
        # For now, just return None
        return None


@dataclass
class PBMemberAccess(Expression):
    """PowerBuilder member access expression (dot notation)."""
    
    object: Expression | None = None
    member: str = ""
    
    @property
    def kind(self):
        return "MEMBER_ACCESS"
    
    def evaluate(self, context: Any = None) -> Any:
        # Member access evaluation would require object resolution
        # For now, just return None
        return None