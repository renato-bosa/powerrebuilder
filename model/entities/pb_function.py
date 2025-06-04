"""PowerBuilder function classes.

This module contains PowerBuilder-specific function node classes.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass
class PBFunctionArgumentNode:
    """PowerBuilder function argument node.

    This is an alias/duplicate of PBArgumentNode for compatibility.
    """

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

    def __eq__(self, other):
        """Check equality of function argument nodes."""
        if not isinstance(other, PBFunctionArgumentNode):
            return False
        return (
            self.name == other.name
            and self.start_position == other.start_position
            and self.stop_position == other.stop_position
        )

    def __hash__(self):
        """Hash function for use in sets/dicts."""
        return hash((self.name, self.start_position, self.stop_position))
