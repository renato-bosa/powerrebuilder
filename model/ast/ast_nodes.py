"""Consolidated AST node definitions.

This module combines the base AST node definitions from nodes.py and control.py,
eliminating duplicate definitions and providing a clear hierarchy.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any, Optional, Union

from model.utils.base import SourceAnchor
from .node_kind import NodeKind
from .types import Type


# Base AST Node Classes
@dataclass
class ASTNode(ABC):
    """Base class for all AST nodes."""
    source_anchor: Optional[SourceAnchor] = field(default=None, kw_only=True)
    
    @property
    @abstractmethod
    def node_kind(self) -> NodeKind:
        """Return the kind of this node."""
        pass


@dataclass
class Expression(ASTNode):
    """Base class for all expressions."""
    type: Optional[Type] = field(default=None, init=False)
    
    @property
    def node_kind(self) -> NodeKind:
        return NodeKind.EXPRESSION


@dataclass
class Statement(ASTNode):
    """Base class for all statements."""
    
    @property
    def node_kind(self) -> NodeKind:
        return NodeKind.STATEMENT


@dataclass
class Block(Statement):
    """A block of statements."""
    statements: list[Statement] = field(default_factory=list)
    
    @property
    def node_kind(self) -> NodeKind:
        return NodeKind.BLOCK


# Literal and Basic Expressions
@dataclass
class Literal(Expression):
    """Base class for literal values."""
    
    @property
    @abstractmethod
    def value(self) -> Any:
        """Return the literal value."""
        pass


@dataclass
class IntegerLiteral(Literal):
    """Integer literal."""
    value: int
    
    @property
    def node_kind(self) -> NodeKind:
        return NodeKind.INTEGER_LITERAL


@dataclass
class RealLiteral(Literal):
    """Real (floating-point) literal."""
    value: float
    
    @property
    def node_kind(self) -> NodeKind:
        return NodeKind.REAL_LITERAL


@dataclass
class StringLiteral(Literal):
    """String literal."""
    value: str
    
    @property
    def node_kind(self) -> NodeKind:
        return NodeKind.STRING_LITERAL


@dataclass
class BooleanLiteral(Literal):
    """Boolean literal."""
    value: bool
    
    @property
    def node_kind(self) -> NodeKind:
        return NodeKind.BOOLEAN_LITERAL


@dataclass
class NullLiteral(Literal):
    """Null literal."""
    
    @property
    def value(self) -> None:
        return None
    
    @property
    def node_kind(self) -> NodeKind:
        return NodeKind.NULL_LITERAL


# Variable-related Nodes
@dataclass
class Variable(Expression):
    """Variable reference."""
    name: str
    
    @property
    def node_kind(self) -> NodeKind:
        return NodeKind.VARIABLE


@dataclass
class VariableDeclaration(Statement):
    """Variable declaration."""
    name: str
    type: Type
    initial_value: Optional[Expression] = None
    is_constant: bool = False
    visibility: str = "public"
    
    @property
    def node_kind(self) -> NodeKind:
        return NodeKind.VARIABLE_DECLARATION


# Operators
@dataclass
class BinaryExpression(Expression):
    """Binary operation."""
    left: Expression
    operator: str
    right: Expression
    
    @property
    def node_kind(self) -> NodeKind:
        return NodeKind.BINARY_EXPRESSION


@dataclass
class UnaryExpression(Expression):
    """Unary operation."""
    operator: str
    operand: Expression
    prefix: bool = True
    
    @property
    def node_kind(self) -> NodeKind:
        return NodeKind.UNARY_EXPRESSION


@dataclass
class Assignment(Statement):
    """Assignment statement."""
    target: Expression
    value: Expression
    
    @property
    def node_kind(self) -> NodeKind:
        return NodeKind.ASSIGNMENT


# Control Flow Statements
@dataclass
class Condition(Expression):
    """Conditional expression."""
    expression: Expression
    
    @property
    def node_kind(self) -> NodeKind:
        return NodeKind.CONDITION


@dataclass
class BooleanOperation(Expression):
    """Boolean operation (AND, OR)."""
    operator: str  # "AND" or "OR"
    operands: list[Expression]
    
    @property
    def node_kind(self) -> NodeKind:
        return NodeKind.BOOLEAN_OPERATION


@dataclass
class IfStatement(Statement):
    """If-then-else statement."""
    condition: Expression
    then_branch: Statement
    else_branch: Optional[Statement] = None
    
    @property
    def node_kind(self) -> NodeKind:
        return NodeKind.IF_STATEMENT


@dataclass
class WhileLoop(Statement):
    """While loop."""
    condition: Expression
    body: Statement
    
    @property
    def node_kind(self) -> NodeKind:
        return NodeKind.WHILE_LOOP


@dataclass
class ForLoop(Statement):
    """For loop."""
    variable: str
    start: Expression
    end: Expression
    step: Optional[Expression] = None
    body: Statement = field(default_factory=Block)
    
    @property
    def node_kind(self) -> NodeKind:
        return NodeKind.FOR_LOOP


@dataclass
class DoWhileLoop(Statement):
    """Do-while loop."""
    body: Statement
    condition: Expression
    
    @property
    def node_kind(self) -> NodeKind:
        return NodeKind.DO_WHILE_LOOP


@dataclass
class BreakStatement(Statement):
    """Break statement."""
    
    @property
    def node_kind(self) -> NodeKind:
        return NodeKind.BREAK_STATEMENT


@dataclass
class ContinueStatement(Statement):
    """Continue statement."""
    
    @property
    def node_kind(self) -> NodeKind:
        return NodeKind.CONTINUE_STATEMENT


@dataclass
class ReturnStatement(Statement):
    """Return statement."""
    value: Optional[Expression] = None
    
    @property
    def node_kind(self) -> NodeKind:
        return NodeKind.RETURN_STATEMENT


@dataclass
class ExitStatement(Statement):
    """Exit statement."""
    
    @property
    def node_kind(self) -> NodeKind:
        return NodeKind.EXIT_STATEMENT


# Case/Switch Statement
@dataclass
class CaseExpression(ASTNode):
    """Case expression in a case statement."""
    values: list[Expression]
    body: Statement
    
    @property
    def node_kind(self) -> NodeKind:
        return NodeKind.CASE_EXPRESSION


@dataclass
class CaseStatement(Statement):
    """Case/switch statement."""
    expression: Expression
    cases: list[CaseExpression]
    default_case: Optional[Statement] = None
    
    @property
    def node_kind(self) -> NodeKind:
        return NodeKind.CASE_STATEMENT


# Goto Statement
@dataclass
class Label(Statement):
    """Label for goto statements."""
    name: str
    
    @property
    def node_kind(self) -> NodeKind:
        return NodeKind.LABEL


@dataclass
class GotoStatement(Statement):
    """Goto statement."""
    label: str
    
    @property
    def node_kind(self) -> NodeKind:
        return NodeKind.GOTO_STATEMENT


# Exception Handling (from exception_handling.py)
@dataclass
class ExceptionType(ASTNode):
    """Exception type specification."""
    type_name: str
    variable_name: Optional[str] = None
    
    @property
    def node_kind(self) -> NodeKind:
        return NodeKind.EXCEPTION_TYPE


@dataclass
class CatchBlock(ASTNode):
    """Catch block in try-catch statement."""
    exception_type: ExceptionType
    body: Statement
    
    @property
    def node_kind(self) -> NodeKind:
        return NodeKind.CATCH_BLOCK


@dataclass
class FinallyBlock(ASTNode):
    """Finally block in try-catch statement."""
    body: Statement
    
    @property
    def node_kind(self) -> NodeKind:
        return NodeKind.FINALLY_BLOCK


@dataclass
class ThrowStatement(Statement):
    """Throw statement."""
    exception: Expression
    
    @property
    def node_kind(self) -> NodeKind:
        return NodeKind.THROW_STATEMENT


@dataclass
class TryCatchStatement(Statement):
    """Try-catch-finally statement."""
    try_block: Statement
    catch_blocks: list[CatchBlock] = field(default_factory=list)
    finally_block: Optional[FinallyBlock] = None
    
    @property
    def node_kind(self) -> NodeKind:
        return NodeKind.TRY_CATCH_STATEMENT


# Events (from nodes.py)
@dataclass
class Event(ASTNode):
    """Event definition."""
    name: str
    parameters: list[Any] = field(default_factory=list)  # Will be Parameter from functions.py
    body: Optional[Statement] = None
    
    @property
    def node_kind(self) -> NodeKind:
        return NodeKind.EVENT


@dataclass
class EventTrigger(Statement):
    """Event trigger statement."""
    object_name: Optional[str]
    event_name: str
    arguments: list[Expression] = field(default_factory=list)
    
    @property
    def node_kind(self) -> NodeKind:
        return NodeKind.EVENT_TRIGGER


# Control Flow for Code Generation (from controlflow.py)
@dataclass
class ControlFlow:
    """Control flow information for code generation."""
    entry_points: list[str] = field(default_factory=list)
    exit_points: list[str] = field(default_factory=list)
    branches: dict[str, list[str]] = field(default_factory=dict)