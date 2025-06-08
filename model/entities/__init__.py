"""PowerBuilder entity models.

This module exports expression evaluation functionality and entity classes.
"""

from .expression_evaluator import (
    EvaluationContext,
    ExpressionEvaluator,
    evaluate_expression,
)
from .expressions import (
    PBExpression,
    PBNumberLiteral,
    PBStringLiteral,
    PBBooleanLiteral,
    PBNullLiteral,
    PBVariable,
    PBFieldReference,
    PBBinaryOperator,
    PBUnaryOperator,
    PBArrayAccess,
    PBFunctionCall,
    PBMethodCall,
    PBConstructorCall,
    PBCastExpression,
    PBTernaryExpression,
    PBThisExpression,
    PBParentExpression,
    PBSuperExpression,
    PBConcatenationOperator,
    PBPowerOperator,
    PBSqlVariableExpression,
    PBDynamicSqlExpression,
)

__all__ = [
    # Evaluator
    "EvaluationContext",
    "ExpressionEvaluator",
    "evaluate_expression",
    # Expression classes
    "PBExpression",
    "PBNumberLiteral",
    "PBStringLiteral",
    "PBBooleanLiteral",
    "PBNullLiteral",
    "PBVariable",
    "PBFieldReference",
    "PBBinaryOperator",
    "PBUnaryOperator",
    "PBArrayAccess",
    "PBFunctionCall",
    "PBMethodCall",
    "PBConstructorCall",
    "PBCastExpression",
    "PBTernaryExpression",
    "PBThisExpression",
    "PBParentExpression",
    "PBSuperExpression",
    "PBConcatenationOperator",
    "PBPowerOperator",
    "PBSqlVariableExpression",
    "PBDynamicSqlExpression",
]