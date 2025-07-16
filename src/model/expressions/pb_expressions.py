"""PowerBuilder-specific expression nodes with PB prefix.

This module provides PowerBuilder-specific expression nodes that are used by the
decompiler's data flow analysis. These are aliases and specialized versions of
the base expression nodes.
"""

from dataclasses import dataclass, field
from typing import Any

from src.model.ast.nodes.base import Expression
from src.model.expressions.ast_expressions import (
    BooleanLiteral,
    IntegerLiteral,
    NullLiteral,
    RealLiteral,
    StringLiteral,
    Variable,
    BinaryExpression as BaseBinaryExpression,
    UnaryExpression as BaseUnaryExpression,
    ConditionalExpression,
)


# PowerBuilder-specific literal nodes (aliases for consistency)
PBBooleanLiteral = BooleanLiteral
PBNullLiteral = NullLiteral
PBStringLiteral = StringLiteral
PBVariable = Variable


@dataclass
class PBNumberLiteral(Expression):
    """PowerBuilder numeric literal that can be integer or real."""
    
    value: int | float = 0
    
    @property
    def kind(self):
        return "LITERAL"
    
    def evaluate(self, context: Any = None) -> int | float:
        return self.value


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
        
        # Handle basic operators
        if self.operator == "+":
            return left_val + right_val
        elif self.operator == "-":
            return left_val - right_val
        elif self.operator == "*":
            return left_val * right_val
        elif self.operator == "/":
            return left_val / right_val if right_val != 0 else None
        elif self.operator == "=":
            return left_val == right_val
        elif self.operator == "<>":
            return left_val != right_val
        elif self.operator == "<":
            return left_val < right_val
        elif self.operator == "<=":
            return left_val <= right_val
        elif self.operator == ">":
            return left_val > right_val
        elif self.operator == ">=":
            return left_val >= right_val
        elif self.operator == "AND":
            return left_val and right_val
        elif self.operator == "OR":
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
        
        if self.operator == "-":
            return -val
        elif self.operator == "NOT":
            return not val
        else:
            return val


@dataclass
class PBConcatenationOperator(Expression):
    """PowerBuilder string concatenation operator (&)."""
    
    operands: list[Expression] = field(default_factory=list)
    
    @property
    def kind(self):
        return "CONCATENATION"
    
    def evaluate(self, context: Any = None) -> str:
        result = []
        for operand in self.operands:
            if hasattr(operand, 'evaluate'):
                result.append(str(operand.evaluate(context)))
            else:
                result.append(str(operand))
        return "".join(result)


@dataclass
class PBPowerOperator(Expression):
    """PowerBuilder power operator (^)."""
    
    base: Expression | None = None
    exponent: Expression | None = None
    
    @property  
    def kind(self):
        return "POWER"
    
    def evaluate(self, context: Any = None) -> float | None:
        if not self.base or not self.exponent:
            return None
        base_val = self.base.evaluate(context) if hasattr(self.base, 'evaluate') else self.base
        exp_val = self.exponent.evaluate(context) if hasattr(self.exponent, 'evaluate') else self.exponent
        try:
            return float(base_val) ** float(exp_val)
        except (ValueError, TypeError):
            return None


@dataclass
class PBTernaryExpression(Expression):
    """PowerBuilder ternary/conditional expression."""
    
    condition: Expression | None = None
    then_expr: Expression | None = None
    else_expr: Expression | None = None
    
    # Alternative attribute names used in data_flow.py
    @property
    def then_expression(self):
        return self.then_expr
    
    @property
    def else_expression(self):
        return self.else_expr
    
    @property
    def kind(self):
        return "CONDITIONAL"
    
    def evaluate(self, context: Any = None) -> Any:
        if not self.condition:
            return None
        cond_val = self.condition.evaluate(context) if hasattr(self.condition, 'evaluate') else self.condition
        if cond_val:
            return self.then_expr.evaluate(context) if self.then_expr and hasattr(self.then_expr, 'evaluate') else self.then_expr
        else:
            return self.else_expr.evaluate(context) if self.else_expr and hasattr(self.else_expr, 'evaluate') else self.else_expr


__all__ = [
    'PBBooleanLiteral',
    'PBNumberLiteral', 
    'PBStringLiteral',
    'PBNullLiteral',
    'PBVariable',
    'PBBinaryOperator',
    'PBUnaryOperator',
    'PBConcatenationOperator',
    'PBPowerOperator',
    'PBTernaryExpression',
]