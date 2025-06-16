"""PowerBuilder entity models.

This module exports expression evaluation functionality and entity classes.
"""

from .expression_evaluator import (
    EvaluationContext,
    ExpressionEvaluator,
    evaluate_expression,
)
from .pb_builtin_functions import create_builtin_functions
from .expressions import (
    PBArrayAccess,
    PBBinaryOperator,
    PBBooleanLiteral,
    PBCastExpression,
    PBConcatenationOperator,
    PBConstructorCall,
    PBDynamicSqlExpression,
    PBExpression,
    PBFieldReference,
    PBFunctionCall,
    PBMethodCall,
    PBNullLiteral,
    PBNumberLiteral,
    PBParentExpression,
    PBPowerOperator,
    PBSqlVariableExpression,
    PBStringLiteral,
    PBSuperExpression,
    PBTernaryExpression,
    PBThisExpression,
    PBUnaryOperator,
    PBVariable,
)

__all__ = [
    # Evaluator
    "EvaluationContext",
    "ExpressionEvaluator",
    "create_builtin_functions",
    "PBArrayAccess",
    "PBBinaryOperator",
    "PBBooleanLiteral",
    "PBCastExpression",
    "PBConcatenationOperator",
    "PBConstructorCall",
    "PBDynamicSqlExpression",
    # Expression classes
    "PBExpression",
    "PBFieldReference",
    "PBFunctionCall",
    "PBMethodCall",
    "PBNullLiteral",
    "PBNumberLiteral",
    "PBParentExpression",
    "PBPowerOperator",
    "PBSqlVariableExpression",
    "PBStringLiteral",
    "PBSuperExpression",
    "PBTernaryExpression",
    "PBThisExpression",
    "PBUnaryOperator",
    "PBVariable",
    "evaluate_expression",
]
