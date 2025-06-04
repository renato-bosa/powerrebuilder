"""PowerBuilder argument classes.

This module contains PowerBuilder-specific argument node classes used in function definitions.
"""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class PBArgumentNode:
    """PowerBuilder function argument node."""

    name: str
    start_position: int | None = None
    stop_position: int | None = None
    type: str | None = None
    default_value: str | None = None
    is_reference: bool = False
    is_output: bool = False
    source_file: str | None = None

    def accept_visitor(self, visitor):
        """Accept a visitor for the visitor pattern."""
        if hasattr(visitor, "visit_function_argument_node"):
            return visitor.visit_function_argument_node(self)
        return None


@dataclass
class PBArgumentOptionNode:
    """PowerBuilder argument option node (e.g., REF, READONLY)."""

    option_type: str  # REF, READONLY, etc.
    value: str | None = None
    start_position: int | None = None
    stop_position: int | None = None
    source_file: str | None = None


@dataclass
class PBArgumentsNode:
    """Container for multiple PowerBuilder function arguments."""

    arguments: list[PBArgumentNode] = field(default_factory=list)
    start_position: int | None = None
    stop_position: int | None = None
    source_file: str | None = None

    def add_argument(self, argument: PBArgumentNode) -> None:
        """Add an argument to the list."""
        self.arguments.append(argument)

    def get_argument_by_name(self, name: str) -> PBArgumentNode | None:
        """Get an argument by name."""
        for arg in self.arguments:
            if arg.name == name:
                return arg
        return None
