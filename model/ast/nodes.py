"""Abstract Syntax Tree nodes for PowerBuilder.

This module contains all AST node classes for representing PowerBuilder code structure.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from ..utils.base import PBNode
from .node_kind import NodeKind

# Import types that are used in this module but defined elsewhere
from .types import Type
from .functions import Function, Parameter


# ─── Base AST Nodes ─────────────────────────────────────────────────────
@dataclass
class Expression(PBNode):
    """Base class for all expressions."""

    @property
    def kind(self) -> NodeKind:
        """Get the node kind for expression."""
        return NodeKind.EXPRESSION


@dataclass
class Statement(PBNode):
    """Base class for all statements."""

    @property
    def kind(self) -> NodeKind:
        """Get the node kind for statement."""
        return NodeKind.STATEMENT


# ─── Event Nodes ───────────────────────────────────────────────────────
@dataclass
class Event(Statement):
    """Event declaration or trigger."""

    name: str
    parameters: list[Parameter] = field(default_factory=list)
    body: list[Statement] = field(default_factory=list)

    @property
    def kind(self) -> NodeKind:
        """Get the node kind for event."""
        return NodeKind.EVENT


@dataclass
class EventTrigger(Statement):
    """Event trigger statement."""

    event: Event
    arguments: list[Argument] = field(default_factory=list)

    @property
    def kind(self) -> NodeKind:
        """Get the node kind for event trigger."""
        return NodeKind.EVENT_TRIGGER


# ─── Expression Nodes ────────────────────────────────────────────────────
@dataclass
class Literal(Expression):
    """Literal value expression."""

    value: str
    type: str  # number, string, boolean, etc.

    @property
    def kind(self) -> NodeKind:
        """Get the node kind for literal."""
        type_map = {
            "number": NodeKind.INTEGER_LITERAL,
            "integer": NodeKind.INTEGER_LITERAL,
            "real": NodeKind.REAL_LITERAL,
            "float": NodeKind.REAL_LITERAL,
            "string": NodeKind.STRING_LITERAL,
            "boolean": NodeKind.BOOLEAN_LITERAL,
            "bool": NodeKind.BOOLEAN_LITERAL,
            "date": NodeKind.DATE_LITERAL,
            "time": NodeKind.TIME_LITERAL,
            "null": NodeKind.NULL_LITERAL,
        }
        return type_map.get(self.type.lower(), NodeKind.LITERAL_EXPRESSION)


@dataclass
class BinaryExpression(Expression):
    """Binary operator expression."""

    left: Expression
    operator: str
    right: Expression

    @property
    def kind(self) -> NodeKind:
        """Get the node kind for binary expression."""
        return NodeKind.BINARY_EXPRESSION


@dataclass
class UnaryExpression(Expression):
    """Unary operator expression."""

    operator: str
    operand: Expression

    @property
    def kind(self) -> NodeKind:
        """Get the node kind for unary expression."""
        return NodeKind.UNARY_EXPRESSION


# Note: Function, Parameter, and Argument classes are defined in ast/functions.py


# Note: Type and CustomType classes are defined in ast/types.py


# ─── Variable Nodes ─────────────────────────────────────────────────────
@dataclass
class Variable(Expression):
    """Variable reference."""

    name: str
    type: Type | None = None


@dataclass
class VariableDeclaration(Statement):
    """Variable declaration."""

    name: str
    type: Type
    initial_value: Expression | None = None


# Note: SQL nodes have been moved to ast/sql.py


# Note: Detailed SQL AST nodes have been moved to ast/sql.py


# Ensure all new nodes are available if this file is imported directly
# (This might be handled by an __all__ in __init__.py later)
