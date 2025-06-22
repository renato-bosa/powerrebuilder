"""PowerBuilder array classes.

This module contains PowerBuilder-specific array node classes.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass
class PBArrayNode:
    """PowerBuilder array node."""

    name: str
    dimensions: list[int] | None = None
    element_type: str | None = None
    start_position: int | None = None
    stop_position: int | None = None
    source_file: str | None = None

    def accept_visitor(self, visitor) -> None:




        """Accept a visitor for the visitor pattern."""
        if hasattr(visitor, "visit_array_node"):
            return visitor.visit_array_node(self)
        return None


@dataclass
class PBArrayPositionNode:
    """PowerBuilder array position/index node."""

    position: Any  # Can be a literal value or expression
    start_position: int | None = None
    stop_position: int | None = None
    source_file: str | None = None

    def accept_visitor(self, visitor) -> None:




        """Accept a visitor for the visitor pattern."""
        if hasattr(visitor, "visit_array_position_node"):
            return visitor.visit_array_position_node(self)
        return None


@dataclass
class PBArrayWithSizeNode:
    """PowerBuilder array with size declaration node."""

    name: str
    size: Any  # Can be a literal value or expression
    element_type: str | None = None
    dimensions: list[Any] | None = None  # For multi-dimensional arrays
    start_position: int | None = None
    stop_position: int | None = None
    source_file: str | None = None

    def accept_visitor(self, visitor) -> None:




        """Accept a visitor for the visitor pattern."""
        if hasattr(visitor, "visit_array_with_size_node"):
            return visitor.visit_array_with_size_node(self)
        return None


@dataclass
class PBArray(PBArrayNode):
    """PowerBuilder array stub class alias for compatibility."""
