"""Unified expression module for PowerBuilder decompiler.

This module consolidates all expression-related functionality:
- AST expression nodes
- Expression evaluation
- Expression reconstruction from P-code
"""

from .evaluator import EvaluationContext, ExpressionEvaluator
from .ast_expressions import (
    ASTExpression,
    ExpressionKind,
    LiteralExpression,
    IdentifierExpression,
    ThisExpression,
    SuperExpression,
    ParentExpression,
    BinaryExpression,
    ArithmeticExpression,
    ComparisonExpression,
    LogicalExpression,
    AssignmentExpression,
)

__all__ = [
    # AST expression base classes
    "ASTExpression",
    "ExpressionKind",
    "LiteralExpression",
    "IdentifierExpression",
    "ThisExpression",
    "SuperExpression",
    "ParentExpression",
    "BinaryExpression",
    "ArithmeticExpression",
    "ComparisonExpression",
    "LogicalExpression",
    "AssignmentExpression",
    # AST nodes
    "Expression",
    "ExpressionKind",
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
    "StackExpression",
    "StackValue",
]