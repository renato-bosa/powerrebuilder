"""Base classes for PowerBuilder model.

This module contains base classes used throughout the model.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from model.ast.node_kind import NodeKind


@dataclass
class SourceAnchor:
    """Represents a position in source code."""

    line: int
    column: int
    offset: int | None = None
    file_path: str | None = None


@dataclass
class PBNode:
    """Base class for all PowerBuilder AST nodes."""

    # Source tracking fields with default values
    start_position: int | None = field(default=None, init=False)
    stop_position: int | None = field(default=None, init=False)
    source_file: str | None = field(default=None, init=False)

    @property
    def kind(self) -> NodeKind:
        """Get the node kind for this AST node.

        Subclasses should override this to return the appropriate NodeKind value.
        """
        from model.ast.node_kind import NodeKind

        return NodeKind.UNKNOWN

    def __eq__(self, other):
        if not isinstance(other, self.__class__):
            return False
        return self.__dict__ == other.__dict__

    def __hash__(self):
        return hash(tuple(sorted(self.__dict__.items())))

    def validate(self, context: dict[str, Any] | None = None) -> bool:
        """Validate this node in the given context.

        Args:
            context: Dictionary containing validation context, such as type_registry,
                    expected return type, parent scope, etc.

        Returns:
            bool: True if valid, False otherwise
        """
        # Base implementation always passes - subclasses should override
        return True
