"""Unified expression module for PowerBuilder decompiler.

This module consolidates all expression-related functionality:
- AST expression nodes
- Expression evaluation
- Expression reconstruction from P-code
"""

from .ast_expressions import (
    BinaryExpression,
    BinaryOperator,
    BooleanLiteral,
    CallExpression,
    ConditionalExpression,
    Expression,
    FieldAccessExpression,
    IntegerLiteral,
    Literal,
    NullLiteral,
    RealLiteral,
    StringLiteral,
    UnaryExpression,
    UnaryOperator,
    Variable,
)
from .evaluator import EvaluationContext, ExpressionEvaluator
from .reconstructor import (
    AdvancedExpressionReconstructor,
    ExpressionReconstructor,
    ExpressionType,
)

__all__ = [
    # AST nodes
    "Expression",
    "BinaryExpression",
    "UnaryExpression",
    "Literal",
    "BooleanLiteral",
    "IntegerLiteral",
    "NullLiteral",
    "RealLiteral",
    "StringLiteral",
    "Variable",
    "CallExpression",
    "FieldAccessExpression",
    "ConditionalExpression",
    "BinaryOperator",
    "UnaryOperator",
    # Evaluation
    "EvaluationContext",
    "ExpressionEvaluator",
    # Reconstruction
    "ExpressionReconstructor",
    "AdvancedExpressionReconstructor",
    "ExpressionType",
]