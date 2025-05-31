"""Exception handling AST nodes for PowerBuilder.

This module contains nodes for exception handling constructs.
"""
from dataclasses import dataclass, field
from typing import Any

from .utils.base import PBNode


@dataclass
class ExceptionType(PBNode):
    """Exception type node."""
    name: str


@dataclass
class CatchBlock(PBNode):
    """Catch block in try-catch statement."""
    exception_type: ExceptionType
    variable_name: str
    statements: list[Any] = field(default_factory=list)


@dataclass
class FinallyBlock(PBNode):
    """Finally block in try-catch statement."""
    statements: list[Any] = field(default_factory=list)


@dataclass
class ThrowStatement(PBNode):
    """Throw statement."""
    expression: Any = None


@dataclass
class TryCatchStatement(PBNode):
    """Try-catch statement."""
    try_statements: list[Any] = field(default_factory=list)
    catch_blocks: list[CatchBlock] = field(default_factory=list)
    finally_block: FinallyBlock | None = None
