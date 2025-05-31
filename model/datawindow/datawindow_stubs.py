"""DataWindow stub classes for PowerBuilder AST.

This module contains stub classes for datawindow elements.
"""
from dataclasses import dataclass, field
from typing import Any

from ..utils.base import PBNode


@dataclass
class TableDefinition(PBNode):
    """Table definition in DataWindow."""
    name: str
    columns: list[Any] = field(default_factory=list)


@dataclass
class ColumnDefinition(PBNode):
    """Column definition in DataWindow."""
    name: str
    type: str
    width: int = 0


@dataclass
class ComputeDefinition(PBNode):
    """Compute expression definition in DataWindow."""
    name: str
    expression: str


@dataclass
class DisplayElement(PBNode):
    """Display element in DataWindow."""
    name: str
    element_type: str  # text, line, rectangle, etc.


@dataclass
class SummaryItem(PBNode):
    """Summary item in DataWindow."""
    name: str
    summary_type: str  # sum, avg, count, etc.
    column: str 