"""DataWindow stub classes for PowerBuilder AST.

This module provides backward compatibility aliases for DataWindow classes.
New code should use the classes from datawindow.py and related modules directly.
"""

from dataclasses import dataclass, field
from typing import Any

from ..utils.base import PBNode
from .table import PBTable as TableDefinition
from .column import PBColumn as ColumnDefinition
from .datawindow import PBComputeExpression as ComputeDefinition
from .datawindow import PBDisplayObject as DisplayElement


# SummaryItem doesn't have a direct equivalent, so we create a simple class
@dataclass
class SummaryItem(PBNode):
    """Summary item in DataWindow."""

    name: str
    summary_type: str  # sum, avg, count, etc.
    column: str
