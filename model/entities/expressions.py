"""PowerBuilder expression entities.

This module consolidates expression-related entities from pb_expression.py 
and pb_expression_impl.py.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Optional, Union

from ..ast.ast_nodes import (
    BinaryExpression,
    Expression,
    Literal,
    UnaryExpression,
    Variable,
)
from ..utils.base import PBNode


# Base Expression Classes
@dataclass
class PBExpression(PBNode):
    """Base class for PowerBuilder expressions."""
    name: str = ""
    
    def evaluate(self) -> Any:
        """Evaluate the expression."""
        raise NotImplementedError(f"evaluate not implemented for {self.__class__.__name__}")


# Literal Expressions
@dataclass 
class PBNumberLiteral(Literal):
    """Numeric literal expression."""
    
    def __init__(self, value: Union[int, float]):
        self.value = value
    
    def evaluate(self) -> Union[int, float]:
        return self.value


@dataclass
class PBStringLiteral(Literal):
    """String literal expression."""
    
    def __init__(self, value: str):
        self.value = value
    
    def evaluate(self) -> str:
        return self.value


@dataclass
class PBBooleanLiteral(Literal):
    """Boolean literal expression."""
    
    def __init__(self, value: bool):
        self.value = value
    
    def evaluate(self) -> bool:
        return self.value


@dataclass
class PBNullLiteral(Literal):
    """Null literal expression."""
    
    def __init__(self):
        pass
    
    @property
    def value(self) -> None:
        return None
    
    def evaluate(self) -> None:
        return None


# Variable References
@dataclass
class PBVariable(Variable):
    """Variable reference in PowerBuilder."""
    
    def evaluate(self) -> Any:
        # In a real implementation, this would look up the variable value
        raise NotImplementedError(f"Cannot evaluate variable {self.name} without context")


@dataclass
class PBFieldReference(Expression):
    """Field reference expression (object.field)."""
    object: Expression
    field_name: str
    
    def evaluate(self) -> Any:
        raise NotImplementedError("Field reference evaluation requires runtime context")


# Operators
@dataclass
class PBBinaryOperator(BinaryExpression):
    """Binary operator expression."""
    
    def evaluate(self) -> Any:
        left_val = self.left.evaluate() if hasattr(self.left, 'evaluate') else self.left
        right_val = self.right.evaluate() if hasattr(self.right, 'evaluate') else self.right
        
        # Basic operator implementations
        if self.operator == '+':
            return left_val + right_val
        elif self.operator == '-':
            return left_val - right_val
        elif self.operator == '*':
            return left_val * right_val
        elif self.operator == '/':
            return left_val / right_val
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
        elif self.operator.upper() == 'AND':
            return left_val and right_val
        elif self.operator.upper() == 'OR':
            return left_val or right_val
        else:
            raise NotImplementedError(f"Operator {self.operator} not implemented")


@dataclass
class PBUnaryOperator(UnaryExpression):
    """Unary operator expression."""
    
    def evaluate(self) -> Any:
        operand_val = self.operand.evaluate() if hasattr(self.operand, 'evaluate') else self.operand
        
        if self.operator == '-':
            return -operand_val
        elif self.operator == '+':
            return +operand_val
        elif self.operator.upper() == 'NOT':
            return not operand_val
        else:
            raise NotImplementedError(f"Unary operator {self.operator} not implemented")


# Complex Expressions
@dataclass
class PBArrayAccess(Expression):
    """Array access expression."""
    array: Expression
    indices: list[Expression]
    
    def evaluate(self) -> Any:
        raise NotImplementedError("Array access evaluation requires runtime context")


@dataclass
class PBFunctionCall(Expression):
    """Function call expression."""
    function_name: str
    arguments: list[Expression] = field(default_factory=list)
    object: Optional[Expression] = None  # For method calls
    
    def evaluate(self) -> Any:
        raise NotImplementedError("Function call evaluation requires runtime context")


@dataclass
class PBMethodCall(PBFunctionCall):
    """Method call expression (object.method())."""
    pass


@dataclass
class PBConstructorCall(Expression):
    """Constructor call expression."""
    class_name: str
    arguments: list[Expression] = field(default_factory=list)
    
    def evaluate(self) -> Any:
        raise NotImplementedError("Constructor call evaluation requires runtime context")


@dataclass
class PBCastExpression(Expression):
    """Type cast expression."""
    expression: Expression
    target_type: str
    
    def evaluate(self) -> Any:
        # In a real implementation, this would perform type conversion
        value = self.expression.evaluate() if hasattr(self.expression, 'evaluate') else self.expression
        # Simplified casting logic
        if self.target_type.lower() == 'string':
            return str(value)
        elif self.target_type.lower() == 'integer':
            return int(value)
        elif self.target_type.lower() == 'double':
            return float(value)
        elif self.target_type.lower() == 'boolean':
            return bool(value)
        else:
            raise NotImplementedError(f"Cast to {self.target_type} not implemented")


@dataclass
class PBTernaryExpression(Expression):
    """Ternary conditional expression (condition ? true_expr : false_expr)."""
    condition: Expression
    true_expression: Expression
    false_expression: Expression
    
    def evaluate(self) -> Any:
        cond_val = self.condition.evaluate() if hasattr(self.condition, 'evaluate') else self.condition
        if cond_val:
            return self.true_expression.evaluate() if hasattr(self.true_expression, 'evaluate') else self.true_expression
        else:
            return self.false_expression.evaluate() if hasattr(self.false_expression, 'evaluate') else self.false_expression


# Special PowerBuilder Expressions
@dataclass
class PBThisExpression(Expression):
    """'This' reference expression."""
    
    def evaluate(self) -> Any:
        raise NotImplementedError("'This' reference requires runtime context")


@dataclass
class PBParentExpression(Expression):
    """'Parent' reference expression."""
    
    def evaluate(self) -> Any:
        raise NotImplementedError("'Parent' reference requires runtime context")


@dataclass
class PBSuperExpression(Expression):
    """'Super' reference expression."""
    
    def evaluate(self) -> Any:
        raise NotImplementedError("'Super' reference requires runtime context")


# PowerBuilder-specific operators
@dataclass
class PBConcatenationOperator(BinaryExpression):
    """String concatenation operator (+)."""
    
    def __init__(self, left: Expression, right: Expression):
        super().__init__(left, '+', right)
    
    def evaluate(self) -> str:
        left_val = str(self.left.evaluate() if hasattr(self.left, 'evaluate') else self.left)
        right_val = str(self.right.evaluate() if hasattr(self.right, 'evaluate') else self.right)
        return left_val + right_val


@dataclass
class PBPowerOperator(BinaryExpression):
    """Power operator (^)."""
    
    def __init__(self, left: Expression, right: Expression):
        super().__init__(left, '^', right)
    
    def evaluate(self) -> Union[int, float]:
        left_val = self.left.evaluate() if hasattr(self.left, 'evaluate') else self.left
        right_val = self.right.evaluate() if hasattr(self.right, 'evaluate') else self.right
        return left_val ** right_val


# SQL-related expressions
@dataclass
class PBSqlVariableExpression(Expression):
    """SQL variable expression (:variable_name)."""
    variable_name: str
    
    def evaluate(self) -> Any:
        raise NotImplementedError("SQL variable evaluation requires database context")


@dataclass
class PBDynamicSqlExpression(Expression):
    """Dynamic SQL expression."""
    sql_parts: list[Union[str, Expression]]
    
    def evaluate(self) -> str:
        result = []
        for part in self.sql_parts:
            if isinstance(part, str):
                result.append(part)
            else:
                result.append(str(part.evaluate() if hasattr(part, 'evaluate') else part))
        return ''.join(result)