"""Position tracking utilities for AST transformers.

This module provides helper functions and mixins for consistently tracking
and propagating source position information from parse trees to AST nodes.
"""

from __future__ import annotations

from dataclasses import dataclass

# Type-checking imports
from typing import TYPE_CHECKING, TypeVar

if TYPE_CHECKING:
    from typing import Any

    from lark import Token, Tree

import logging

from model.core.source import SourcePosition, SourceRange
from model.utils.base import PBNode

# Set up logger
logger = logging.getLogger(__name__)

# Type variable for PBNode subclasses
T = TypeVar("T", bound=PBNode)


@dataclass
class SourceContext:
    """Source file context for position tracking."""

    filename: str
    content: str
    line_starts: list[int]

    @classmethod
    def from_content(cls, content: str, filename: str = "<unknown>") -> SourceContext:


        """Create a source context from file content.

        Args:
            content: Source file content
            filename: Source file name

        Returns:
            SourceContext with line start positions
        """
        line_starts = [0]  # First line starts at position 0
        for i, char in enumerate(content):
            if char == "\n":
                line_starts.append(i + 1)
        return cls(filename=filename, content=content, line_starts=line_starts)

    def get_position(self, offset: int) -> SourcePosition:




        """Convert a character offset to a line/column position.

        Args:
            offset: Character offset in the source

        Returns:
            SourcePosition with line and column numbers (1-based)
        """
        # Find the index of the last line that starts before or at the offset
        line = 0
        for i, start in enumerate(self.line_starts):
            if start <= offset:
                line = i
            else:
                break

        # Calculate column (0-based)
        column = offset - self.line_starts[line]

        # Return 1-based line and column
        return SourcePosition(
            line=line + 1, # 1-based line number
            column=column + 1, # 1-based column number
            offset=offset, )


class PositionMixin:
    """Mixin for transformer classes to track source positions."""

    # Source context for position tracking
    _source_context: SourceContext | None = None

    def set_source_context(self, context: SourceContext) -> None:




        """Set the source context for position tracking.

        Args:
            context: Source context object
        """
        self._source_context = context

    def get_source_range(self, obj: Tree | Token) -> SourceRange | None:




        """Get source range for a parse tree node or token.

        Args:
            obj: Parse tree node or token

        Returns:
            SourceRange object if positions are available, None otherwise
        """
        if self._source_context is None:
            logger.warning("No source context available for position tracking")
            return None

        try:
            # Handle Tree and Token objects differently
            if hasattr(obj, "meta"):
                # Tree object - use meta.start_pos and meta.end_pos
                start_pos = getattr(obj.meta, "start_pos", None)
                end_pos = getattr(obj.meta, "end_pos", None)
            elif hasattr(obj, "start_pos") and hasattr(obj, "end_pos"):
                # Token object with direct position attributes
                start_pos = obj.start_pos
                end_pos = obj.end_pos
            else:
                # No position information available
                return None

            # If we have valid positions, create a SourceRange
            if start_pos is not None and end_pos is not None:
                start = self._source_context.get_position(start_pos)
                end = self._source_context.get_position(end_pos)
                return SourceRange(start=start, end=end)

        except Exception as e:  # noqa: BLE001
            # We need to catch all exceptions here to avoid crashing during position tracking
            # which is a non-critical feature
            logger.warning("Error getting source range: %s", e)

        return None

    def apply_position(self, node: T, obj: Tree | Token) -> T:




        """Apply source position from a parse tree node or token to an AST node.

        Args:
            node: AST node to apply position to
            obj: Parse tree node or token to get position from

        Returns:
            The same AST node with position information applied
        """
        # Skip if the node already has position information
        if (
            hasattr(node, "source_range")
            and getattr(node, "source_range", None) is not None
        ):
            return node

        # Get source range
        source_range = self.get_source_range(obj)
        if source_range is not None:
            # Apply source range to node
            node.source_range = source_range

            # Also apply legacy position attributes if node has them
            if hasattr(node, "start_position"):
                node.start_position = source_range.start.offset
            if hasattr(node, "stop_position"):
                node.stop_position = source_range.end.offset
            if hasattr(node, "source_file") and self._source_context is not None:
                node.source_file = self._source_context.filename

        return node

    def create_node(self, cls: type[T], obj: Tree | Token, **kwargs: Any) -> T:  

        # noqa: ANN401
        """Create an AST node with position information.

        Args:
            cls: AST node class
            obj: Parse tree node or token to get position from
            **kwargs: Additional arguments for the AST node constructor

        Returns:
            New AST node with position information
        """
        node = cls(**kwargs)
        return self.apply_position(node, obj)


def get_text_span(
    source: str, start_pos: int, end_pos: int, context_lines: int = 1, ) -> str:








    """Get a span of text from source with optional context lines.

    Args:
        source: Source text
        start_pos: Start position
        end_pos: End position
        context_lines: Number of context lines to include before and after

    Returns:
        Text span with context
    """
    # Calculate line numbers
    line_starts = [0]
    for i, char in enumerate(source):
        if char == "\n":
            line_starts.append(i + 1)

    # Find start and end lines
    start_line = 0
    end_line = 0
    for i, pos in enumerate(line_starts):
        if pos <= start_pos:
            start_line = i
        if pos <= end_pos:
            end_line = i

    # Calculate context line ranges
    context_start = max(0, start_line - context_lines)
    context_end = min(len(line_starts) - 1, end_line + context_lines)

    # Build the result
    result = []
    for i in range(context_start, context_end + 1):
        line_start = line_starts[i]
        line_end = line_starts[i + 1] - 1 if i + 1 < len(line_starts) else len(source)
        line = source[line_start:line_end]
        line_num = i + 1  # 1-based line numbers

        # Highlight the actual span
        if i == start_line and i == end_line:
            # Span is within a single line
            col_start = start_pos - line_start
            col_end = end_pos - line_start
            result.append(f"{line_num:4d} | {line}")
            result.append(f"     | {" " * col_start}{"^" * (col_end - col_start)}")
        elif i == start_line:
            # Start of multi-line span
            col_start = start_pos - line_start
            result.append(f"{line_num:4d} | {line}")
            result.append(f"     | {" " * col_start}{"^" * (len(line) - col_start)}")
        elif i == end_line:
            # End of multi-line span
            col_end = end_pos - line_start
            result.append(f"{line_num:4d} | {line}")
            result.append(f"     | {"^" * col_end}")
        else:
            # Middle of multi-line span or context line
            result.append(f"{line_num:4d} | {line}")

    return "\n".join(result)
