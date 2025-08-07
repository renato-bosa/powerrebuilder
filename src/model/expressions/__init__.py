"""Unified expression module for PowerBuilder decompiler.

This module consolidates all expression-related functionality:
- AST expression nodes
- Expression evaluation
- Expression reconstruction from P-code
"""

from typing import TYPE_CHECKING

from .evaluator import EvaluationContext, ExpressionEvaluator
from .pb_expressions import (
    PBLiteral as LiteralExpression,
    PBBooleanLiteral as BooleanLiteral,
    PBStringLiteral as StringLiteral,
    PBNumberLiteral as IntegerLiteral,
    PBNumberLiteral as RealLiteral,
    PBNullLiteral as NullLiteral,
    PBVariable as IdentifierExpression,
    PBVariable as Variable,
    PBBinaryOperator as BinaryExpression,
    PBUnaryOperator as UnaryExpression,
    PBFunctionCall as CallExpression,
    PBMemberAccess as FieldAccessExpression,
)
from .reconstructor import ExpressionReconstructor

# Define some classes that may be needed for compatibility
class ExpressionKind:
    LITERAL = "LITERAL"
    IDENTIFIER = "IDENTIFIER"
    BINARY = "BINARY"
    UNARY = "UNARY"
    CALL = "CALL"
    MEMBER_ACCESS = "MEMBER_ACCESS"

# Base expression class alias
from src.model.ast.nodes.base import Expression as ASTExpression

# Make Expression available for __all__ 
Expression = ASTExpression

# Legacy aliases for backward compatibility
ThisExpression = IdentifierExpression
SuperExpression = IdentifierExpression  
ParentExpression = IdentifierExpression
ArithmeticExpression = BinaryExpression
ComparisonExpression = BinaryExpression
LogicalExpression = BinaryExpression
AssignmentExpression = BinaryExpression

# Use PBLiteral as base literal
Literal = PBLiteral = LiteralExpression

# Operator enums for compatibility
class BinaryOperator:
    ADD = "+"
    SUBTRACT = "-"
    MULTIPLY = "*"
    DIVIDE = "/"
    EQUAL = "=="
    NOT_EQUAL = "!="
    LESS_THAN = "<"
    GREATER_THAN = ">"

class UnaryOperator:
    NOT = "!"
    MINUS = "-"

# Expression type utilities
class ExpressionType:
    ARITHMETIC = "arithmetic"
    LOGICAL = "logical"
    COMPARISON = "comparison"

# Additional classes that may be needed
class StackExpression:
    def __init__(self, value=None):
        self.value = value

class StackValue:
    def __init__(self, value=None):
        self.value = value

class ConditionalExpression(ASTExpression):
    def __init__(self, condition=None, true_expr=None, false_expr=None):
        self.condition = condition
        self.true_expr = true_expr
        self.false_expr = false_expr

class AdvancedExpressionReconstructor:
    def __init__(self):
        pass

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