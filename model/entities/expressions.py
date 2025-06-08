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
from .expression_evaluator import ExpressionEvaluator, EvaluationContext


# Base Expression Classes
@dataclass
class PBExpression(PBNode):
    """Base class for PowerBuilder expressions."""
    name: str = ""
    
    def evaluate(self, context: Optional[EvaluationContext] = None) -> Any:
        """Evaluate the expression.
        
        Args:
            context: Optional evaluation context with variable/function bindings
            
        Returns:
            Evaluated value
        """
        evaluator = ExpressionEvaluator(context)
        return evaluator.evaluate(self)


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
    
    def evaluate(self, context: Optional[EvaluationContext] = None) -> Any:
        """Evaluate variable by looking it up in context.
        
        Args:
            context: Evaluation context containing variable bindings
            
        Returns:
            Variable value from context
            
        Raises:
            ModelError: If variable not found in context
        """
        if context is None:
            from ..utils.errors import ModelError
            raise ModelError(f"Cannot evaluate variable {self.name} without context")
        return context.get_variable(self.name)


@dataclass
class PBFieldReference(Expression):
    """Field reference expression (object.field)."""
    object: Expression
    field_name: str
    
    def evaluate(self, context: Optional[EvaluationContext] = None) -> Any:
        """Evaluate field reference by evaluating object and accessing field.
        
        Args:
            context: Evaluation context
            
        Returns:
            Field value
        """
        evaluator = ExpressionEvaluator(context)
        return evaluator.visit_fieldreference(self)


# Operators
@dataclass
class PBBinaryOperator(BinaryExpression):
    """Binary operator expression."""
    
    def evaluate(self, context: Optional[EvaluationContext] = None) -> Any:
        """Evaluate binary expression using the evaluator.
        
        Args:
            context: Evaluation context
            
        Returns:
            Result of binary operation
        """
        evaluator = ExpressionEvaluator(context)
        # Map PowerBuilder operators to standard ones
        op = self.operator
        if op == '=':
            self.operator = '=='
        elif op == '<>':
            self.operator = '!='
        result = evaluator.visit_binaryexpression(self)
        self.operator = op  # Restore original
        return result


@dataclass
class PBUnaryOperator(UnaryExpression):
    """Unary operator expression."""
    
    def evaluate(self, context: Optional[EvaluationContext] = None) -> Any:
        """Evaluate unary expression using the evaluator.
        
        Args:
            context: Evaluation context
            
        Returns:
            Result of unary operation
        """
        evaluator = ExpressionEvaluator(context)
        return evaluator.visit_unaryexpression(self)


# Complex Expressions
@dataclass
class PBArrayAccess(Expression):
    """Array access expression."""
    array: Expression
    indices: list[Expression]
    
    def evaluate(self, context: Optional[EvaluationContext] = None) -> Any:
        """Evaluate array access.
        
        Args:
            context: Evaluation context
            
        Returns:
            Array element value
        """
        evaluator = ExpressionEvaluator(context)
        # For multi-dimensional arrays, evaluate each index
        arr = evaluator.evaluate(self.array)
        for index_expr in self.indices:
            index = evaluator.evaluate(index_expr)
            # PowerBuilder arrays are 1-based
            if isinstance(index, int) and index > 0:
                arr = arr[index - 1]
            else:
                arr = arr[index]
        return arr


@dataclass
class PBFunctionCall(Expression):
    """Function call expression."""
    function_name: str
    arguments: list[Expression] = field(default_factory=list)
    object: Optional[Expression] = None  # For method calls
    
    def evaluate(self, context: Optional[EvaluationContext] = None) -> Any:
        """Evaluate function call.
        
        Args:
            context: Evaluation context with function bindings
            
        Returns:
            Function return value
        """
        evaluator = ExpressionEvaluator(context)
        if self.object:
            # Method call: evaluate object first
            obj = evaluator.evaluate(self.object)
            if hasattr(obj, self.function_name):
                method = getattr(obj, self.function_name)
                args = [evaluator.evaluate(arg) for arg in self.arguments]
                return method(*args)
            else:
                from ..utils.errors import ModelError
                raise ModelError(f"Object has no method '{self.function_name}'")
        else:
            # Regular function call
            self.name = self.function_name  # For compatibility with visit_functioncall
            return evaluator.visit_functioncall(self)


@dataclass
class PBMethodCall(PBFunctionCall):
    """Method call expression (object.method())."""
    pass


@dataclass
class PBConstructorCall(Expression):
    """Constructor call expression."""
    class_name: str
    arguments: list[Expression] = field(default_factory=list)
    
    def evaluate(self, context: Optional[EvaluationContext] = None) -> Any:
        """Evaluate constructor call.
        
        Args:
            context: Evaluation context
            
        Returns:
            New instance (placeholder implementation)
        """
        from ..utils.errors import ModelError
        # In a full implementation, this would instantiate the class
        # For now, return a placeholder
        raise ModelError(f"Constructor calls not yet implemented for class '{self.class_name}'")


@dataclass
class PBCastExpression(Expression):
    """Type cast expression."""
    expression: Expression
    target_type: str
    
    def evaluate(self, context: Optional[EvaluationContext] = None) -> Any:
        """Evaluate cast expression.
        
        Args:
            context: Evaluation context
            
        Returns:
            Value cast to target type
        """
        evaluator = ExpressionEvaluator(context)
        value = evaluator.evaluate(self.expression)
        
        # Simplified casting logic
        target = self.target_type.lower()
        if target == 'string':
            return str(value)
        elif target in ('integer', 'int', 'long'):
            return int(value)
        elif target in ('double', 'real', 'decimal', 'float'):
            return float(value)
        elif target in ('boolean', 'bool'):
            return bool(value)
        else:
            from ..utils.errors import ModelError
            raise ModelError(f"Cast to {self.target_type} not implemented")


@dataclass
class PBTernaryExpression(Expression):
    """Ternary conditional expression (condition ? true_expr : false_expr)."""
    condition: Expression
    true_expression: Expression
    false_expression: Expression
    
    def evaluate(self, context: Optional[EvaluationContext] = None) -> Any:
        """Evaluate ternary expression.
        
        Args:
            context: Evaluation context
            
        Returns:
            Result of true or false expression based on condition
        """
        evaluator = ExpressionEvaluator(context)
        # Map to evaluator's conditional visitor
        self.then_expr = self.true_expression
        self.else_expr = self.false_expression
        return evaluator.visit_conditional(self)


# Special PowerBuilder Expressions
@dataclass
class PBThisExpression(Expression):
    """'This' reference expression."""
    
    def evaluate(self, context: Optional[EvaluationContext] = None) -> Any:
        """Evaluate 'this' reference.
        
        Args:
            context: Evaluation context
            
        Returns:
            Current object reference
        """
        if context and 'this' in context.variables:
            return context.variables['this']
        from ..utils.errors import ModelError
        raise ModelError("'This' reference requires runtime context with current object")


@dataclass
class PBParentExpression(Expression):
    """'Parent' reference expression."""
    
    def evaluate(self, context: Optional[EvaluationContext] = None) -> Any:
        """Evaluate 'parent' reference.
        
        Args:
            context: Evaluation context
            
        Returns:
            Parent object reference
        """
        if context and 'parent' in context.variables:
            return context.variables['parent']
        from ..utils.errors import ModelError
        raise ModelError("'Parent' reference requires runtime context with parent object")


@dataclass
class PBSuperExpression(Expression):
    """'Super' reference expression."""
    
    def evaluate(self, context: Optional[EvaluationContext] = None) -> Any:
        """Evaluate 'super' reference.
        
        Args:
            context: Evaluation context
            
        Returns:
            Super class reference
        """
        if context and 'super' in context.variables:
            return context.variables['super']
        from ..utils.errors import ModelError
        raise ModelError("'Super' reference requires runtime context with super class")


# PowerBuilder-specific operators
@dataclass
class PBConcatenationOperator(BinaryExpression):
    """String concatenation operator (+)."""
    
    def __init__(self, left: Expression, right: Expression):
        super().__init__(left, '+', right)
    
    def evaluate(self, context: Optional[EvaluationContext] = None) -> str:
        """Evaluate string concatenation.
        
        Args:
            context: Evaluation context
            
        Returns:
            Concatenated string
        """
        evaluator = ExpressionEvaluator(context)
        left_val = str(evaluator.evaluate(self.left))
        right_val = str(evaluator.evaluate(self.right))
        return left_val + right_val


@dataclass
class PBPowerOperator(BinaryExpression):
    """Power operator (^)."""
    
    def __init__(self, left: Expression, right: Expression):
        super().__init__(left, '^', right)
    
    def evaluate(self, context: Optional[EvaluationContext] = None) -> Union[int, float]:
        """Evaluate power operation.
        
        Args:
            context: Evaluation context
            
        Returns:
            Result of power operation
        """
        evaluator = ExpressionEvaluator(context)
        # Map ^ to ** for the evaluator
        self.operator = '**'
        result = evaluator.visit_binaryexpression(self)
        self.operator = '^'  # Restore
        return result


# SQL-related expressions
@dataclass
class PBSqlVariableExpression(Expression):
    """SQL variable expression (:variable_name)."""
    variable_name: str
    
    def evaluate(self, context: Optional[EvaluationContext] = None) -> Any:
        """Evaluate SQL variable.
        
        Args:
            context: Evaluation context
            
        Returns:
            Variable value or placeholder
        """
        if context and self.variable_name in context.variables:
            return context.variables[self.variable_name]
        # Return placeholder for SQL generation
        return f":{self.variable_name}"


@dataclass
class PBDynamicSqlExpression(Expression):
    """Dynamic SQL expression."""
    sql_parts: list[Union[str, Expression]]
    
    def evaluate(self, context: Optional[EvaluationContext] = None) -> str:
        """Evaluate dynamic SQL expression.
        
        Args:
            context: Evaluation context
            
        Returns:
            Constructed SQL string
        """
        evaluator = ExpressionEvaluator(context)
        result = []
        for part in self.sql_parts:
            if isinstance(part, str):
                result.append(part)
            else:
                result.append(str(evaluator.evaluate(part)))
        return ''.join(result)