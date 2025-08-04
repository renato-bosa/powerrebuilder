"""Position tracking utilities for AST transformers.

This module provides helper functions and mixins for consistently tracking
and propagating source position information from parse trees to AST nodes.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Any, Protocol, TypeVar, runtime_checkable

from lark import Token, Tree

from src.model.types.base import PBNode, Position, SourceLocation

from .visitor import PowerBuilderASTVisitor

logger = logging.getLogger(__name__)

T = TypeVar("T")
NodeType = TypeVar("NodeType", bound=PBNode)


@runtime_checkable
class PositionTrackable(Protocol):
    """Protocol for objects that can track source positions."""

    start_position: int | None
    stop_position: int | None
    source_file: str | None


@dataclass
class PositionRange:
    """Represents a range of positions in source code."""

    start_line: int
    start_column: int
    end_line: int
    end_column: int
    start_offset: int | None = None
    end_offset: int | None = None
    filename: str | None = None

    def to_source_location(self) -> SourceLocation:
        """Convert to a SourceLocation object."""
        start = Position(
            line=self.start_line, column=self.start_column, offset=self.start_offset
        )
        end = Position(
            line=self.end_line, column=self.end_column, offset=self.end_offset
        )
        return SourceLocation(start=start, end=end, filename=self.filename)


class PositionTrackerMixin:
    """Mixin to add position tracking capabilities to transformers and visitors."""

    def __init__(self, *args, **kwargs) -> None:
        """Initialize position tracking state."""
        super().__init__(*args, **kwargs)
        self._current_filename: str | None = None
        self._source_lines: list[str] = []
        self._position_stack: list[PositionRange] = []

    def set_source_context(
        self, filename: str | None, source: str | None = None
    ) -> None:
        """Set the current source file context.

        Args:
            filename: Name of the source file being processed
            source: Source code content (optional, for line tracking)
        """
        self._current_filename = filename
        if source:
            self._source_lines = source.splitlines(keepends=True)
        else:
            self._source_lines = []

    def extract_position_from_tree(self, tree: Tree) -> PositionRange | None:
        """Extract position information from a Lark Tree.

        Args:
            tree: Lark parse tree node

        Returns:
            PositionRange if position info is available, None otherwise
        """
        if not hasattr(tree, "meta") or not tree.meta:
            return None

        meta = tree.meta

        # Lark provides line, column, start_pos, end_pos
        if hasattr(meta, "line") and hasattr(meta, "column"):
            return PositionRange(
                start_line=meta.line,
                start_column=meta.column,
                end_line=meta.end_line if hasattr(meta, "end_line") else meta.line,
                end_column=meta.end_column
                if hasattr(meta, "end_column")
                else meta.column,
                start_offset=meta.start_pos if hasattr(meta, "start_pos") else None,
                end_offset=meta.end_pos if hasattr(meta, "end_pos") else None,
                filename=self._current_filename,
            )

        return None

    def extract_position_from_token(self, token: Token) -> PositionRange | None:
        """Extract position information from a Lark Token.

        Args:
            token: Lark token

        Returns:
            PositionRange if position info is available, None otherwise
        """
        if not hasattr(token, "line") or not hasattr(token, "column"):
            return None

        # Calculate end position based on token value
        end_line = token.line
        end_column = token.column + len(str(token.value))

        # Handle multi-line tokens
        if "\n" in str(token.value):
            lines = str(token.value).splitlines()
            end_line = token.line + len(lines) - 1
            end_column = len(lines[-1]) + 1 if len(lines) > 1 else end_column

        return PositionRange(
            start_line=token.line,
            start_column=token.column,
            end_line=end_line,
            end_column=end_column,
            start_offset=token.start_pos if hasattr(token, "start_pos") else None,
            end_offset=token.end_pos if hasattr(token, "end_pos") else None,
            filename=self._current_filename,
        )

    def extract_position(self, node: Tree | Token | Any) -> PositionRange | None:
        """Extract position information from any Lark node.

        Args:
            node: Lark tree, token, or other node

        Returns:
            PositionRange if position info is available, None otherwise
        """
        if isinstance(node, Tree):
            return self.extract_position_from_tree(node)
        if isinstance(node, Token):
            return self.extract_position_from_token(node)
        return None

    def annotate_node_with_position(
        self, ast_node: NodeType, position: PositionRange | None
    ) -> NodeType:
        """Annotate an AST node with position information.

        Args:
            ast_node: AST node to annotate
            position: Position information to attach

        Returns:
            The annotated AST node
        """
        if position and isinstance(ast_node, PBNode):
            # Use the existing position fields in PBNode
            ast_node.start_position = position.start_offset
            ast_node.stop_position = position.end_offset
            ast_node.source_file = position.filename

            # Also store detailed position info as metadata if the node supports it
            if hasattr(ast_node, "location"):
                ast_node.location = position.to_source_location()

        return ast_node

    def with_position_context(self, position: PositionRange | None):
        """Context manager for tracking nested positions.

        Args:
            position: Position to push onto the stack
        """

        class PositionContext:
            def __init__(
                self, tracker: PositionTrackerMixin, pos: PositionRange | None
            ) -> None:
                self.tracker = tracker
                self.position = pos

            def __enter__(self):
                if self.position:
                    self.tracker._position_stack.append(self.position)
                return self

            def __exit__(self, exc_type, exc_val, exc_tb):
                if self.position and self.tracker._position_stack:
                    self.tracker._position_stack.pop()

        return PositionContext(self, position)

    def get_current_position(self) -> PositionRange | None:
        """Get the current position from the stack.

        Returns:
            Current position or None if stack is empty
        """
        return self._position_stack[-1] if self._position_stack else None

    def get_line_content(self, line_number: int) -> str | None:
        """Get the content of a specific line.

        Args:
            line_number: 1-based line number

        Returns:
            Line content or None if out of range
        """
        if 0 < line_number <= len(self._source_lines):
            return self._source_lines[line_number - 1].rstrip("\n\r")
        return None

    def create_error_with_position(
        self, message: str, position: PositionRange | None = None
    ) -> dict[str, Any]:
        """Create an error message with position information.

        Args:
            message: Error message
            position: Position where error occurred (uses current if None)

        Returns:
            Error dictionary with position details
        """
        pos = position or self.get_current_position()
        error = {"message": message, "type": "parse_error"}

        if pos:
            error.update(
                {
                    "line": pos.start_line,
                    "column": pos.start_column,
                    "end_line": pos.end_line,
                    "end_column": pos.end_column,
                    "filename": pos.filename,
                }
            )

            # Add line content for better error reporting
            line_content = self.get_line_content(pos.start_line)
            if line_content:
                error["line_content"] = line_content
                # Add visual indicator
                if pos.start_column > 0:
                    indicator = " " * (pos.start_column - 1) + "^"
                    if (
                        pos.start_line == pos.end_line
                        and pos.end_column > pos.start_column
                    ):
                        indicator += "~" * (pos.end_column - pos.start_column - 1)
                    error["indicator"] = indicator

        return error


class PositionTrackingVisitor(PowerBuilderASTVisitor, PositionTrackerMixin):
    """Visitor that tracks and propagates position information through the AST.

    This visitor traverses the AST and ensures all nodes have proper position
    information attached. It can also validate that position information is
    consistent throughout the tree.
    """

    def __init__(self, validate: bool = False) -> None:
        """Initialize the position tracking visitor.

        Args:
            validate: Whether to validate position consistency
        """
        super().__init__()
        self.validate = validate
        self._errors: list[dict[str, Any]] = []
        self._nodes_without_position: list[PBNode] = []

    def visit(self, node: Any | None) -> Any:
        """Visit a node and track its position.

        Args:
            node: Node to visit

        Returns:
            Result of visiting the node
        """
        if node is None:
            return None

        # Track nodes without position information
        if isinstance(node, PBNode):
            if node.start_position is None or node.stop_position is None:
                self._nodes_without_position.append(node)
                logger.debug(
                    "Node %s at %s has no position information",
                    type(node).__name__,
                    id(node),
                )

        # Visit the node
        result = super().visit(node)

        # Validate position consistency if enabled
        if self.validate and isinstance(node, PBNode):
            self._validate_node_position(node)

        return result

    def _validate_node_position(self, node: PBNode) -> None:
        """Validate that a node's position information is consistent.

        Args:
            node: Node to validate
        """
        if node.start_position is not None and node.stop_position is not None:
            if node.start_position > node.stop_position:
                self._errors.append(
                    {
                        "type": "position_validation_error",
                        "message": f"Node {type(node).__name__} has invalid position range: "
                        f"start={node.start_position}, stop={node.stop_position}",
                        "node": node,
                    }
                )

    def get_report(self) -> dict[str, Any]:
        """Get a report of position tracking results.

        Returns:
            Dictionary with tracking statistics and errors
        """
        return {
            "nodes_without_position": len(self._nodes_without_position),
            "validation_errors": len(self._errors),
            "errors": self._errors,
            "unpositioned_node_types": self._get_unpositioned_node_types(),
        }

    def _get_unpositioned_node_types(self) -> dict[str, int]:
        """Get count of unpositioned nodes by type.

        Returns:
            Dictionary mapping node type names to counts
        """
        type_counts: dict[str, int] = {}
        for node in self._nodes_without_position:
            type_name = type(node).__name__
            type_counts[type_name] = type_counts.get(type_name, 0) + 1
        return type_counts

    # Implement required visitor methods with position tracking
    def visit_access(self, node) -> None:
        """Visit an access node."""
        self._track_node_position(node)
        super().visit_access(node)

    def visit_access_modifier(self, node) -> str:
        """Visit an access modifier node."""
        self._track_node_position(node)
        return super().visit_access_modifier(node)

    def visit_access_modifier_definer(self, node) -> None:
        """Visit an access modifier definer node."""
        self._track_node_position(node)
        super().visit_access_modifier_definer(node)

    def visit_access_or_type(self, node) -> None:
        """Visit an access or type node."""
        self._track_node_position(node)
        super().visit_access_or_type(node)

    def visit_argument(self, node) -> None:
        """Visit an argument node."""
        self._track_node_position(node)
        super().visit_argument(node)

    def visit_argument_option(self, node) -> str:
        """Visit an argument option node."""
        self._track_node_position(node)
        return super().visit_argument_option(node)

    def visit_arguments(self, node) -> None:
        """Visit an arguments node."""
        self._track_node_position(node)
        super().visit_arguments(node)

    def visit_array(self, node) -> None:
        """Visit an array node."""
        self._track_node_position(node)
        super().visit_array(node)

    def visit_array_designation(self, node) -> str:
        """Visit an array designation node."""
        self._track_node_position(node)
        return super().visit_array_designation(node)

    def visit_array_position(self, node) -> None:
        """Visit an array position node."""
        self._track_node_position(node)
        super().visit_array_position(node)

    def visit_array_with_size(self, node) -> None:
        """Visit an array with size node."""
        self._track_node_position(node)
        super().visit_array_with_size(node)

    def visit_assignation(self, node) -> None:
        """Visit an assignation node."""
        self._track_node_position(node)
        super().visit_assignation(node)

    def visit_assignation_statement(self, node) -> None:
        """Visit an assignation statement node."""
        self._track_node_position(node)
        super().visit_assignation_statement(node)

    def visit_basic_type(self, node) -> str:
        """Visit a basic type node."""
        self._track_node_position(node)
        return super().visit_basic_type(node)

    def visit_behavioral_alias(self, node) -> None:
        """Visit a behavioral alias node."""
        self._track_node_position(node)
        super().visit_behavioral_alias(node)

    def visit_behavioral_library(self, node) -> None:
        """Visit a behavioral library node."""
        self._track_node_position(node)
        super().visit_behavioral_library(node)

    def visit_behavioral_option(self, node) -> None:
        """Visit a behavioral option node."""
        self._track_node_position(node)
        super().visit_behavioral_option(node)

    def visit_boolean_value(self, node) -> str:
        """Visit a boolean value node."""
        self._track_node_position(node)
        return super().visit_boolean_value(node)

    def visit_call_statement(self, node) -> None:
        """Visit a call statement node."""
        self._track_node_position(node)
        super().visit_call_statement(node)

    def visit_case(self, node) -> None:
        """Visit a case node."""
        self._track_node_position(node)
        super().visit_case(node)

    def visit_case_else(self, node) -> None:
        """Visit a case else node."""
        self._track_node_position(node)
        super().visit_case_else(node)

    def visit_choose_case(self, node) -> None:
        """Visit a choose case node."""
        self._track_node_position(node)
        super().visit_choose_case(node)

    def visit_close_sql_cursor(self, node) -> None:
        """Visit a close SQL cursor node."""
        self._track_node_position(node)
        super().visit_close_sql_cursor(node)

    def visit_column(self, node) -> None:
        """Visit a column node."""
        self._track_node_position(node)
        super().visit_column(node)

    def visit_column_definition(self, node) -> None:
        """Visit a column definition node."""
        self._track_node_position(node)
        super().visit_column_definition(node)

    def visit_column_name_option(self, node) -> None:
        """Visit a column name option node."""
        self._track_node_position(node)
        super().visit_column_name_option(node)

    def visit_column_type_option(self, node) -> None:
        """Visit a column type option node."""
        self._track_node_position(node)
        super().visit_column_type_option(node)

    def visit_common_file(self, node) -> None:
        """Visit a common file node."""
        self._track_node_position(node)
        super().visit_common_file(node)

    def visit_condition(self, node) -> None:
        """Visit a condition node."""
        self._track_node_position(node)
        super().visit_condition(node)

    def visit_constant(self, node) -> str:
        """Visit a constant node."""
        self._track_node_position(node)
        return super().visit_constant(node)

    def visit_continue_statement(self, node) -> str:
        """Visit a continue statement node."""
        self._track_node_position(node)
        return super().visit_continue_statement(node)

    def visit_create_instruction(self, node) -> None:
        """Visit a create instruction node."""
        self._track_node_position(node)
        super().visit_create_instruction(node)

    def visit_create_using_instruction(self, node) -> None:
        """Visit a create using instruction node."""
        self._track_node_position(node)
        super().visit_create_using_instruction(node)

    def visit_custom_call_statement(self, node) -> None:
        """Visit a custom call statement node."""
        self._track_node_position(node)
        super().visit_custom_call_statement(node)

    def visit_custom_type(self, node) -> None:
        """Visit a custom type node."""
        self._track_node_position(node)
        super().visit_custom_type(node)

    def visit_data_window(self, node) -> None:
        """Visit a data window node."""
        self._track_node_position(node)
        super().visit_data_window(node)

    def visit_data_window_file(self, node) -> None:
        """Visit a data window file node."""
        self._track_node_position(node)
        super().visit_data_window_file(node)

    def visit_declare_cursor(self, node) -> None:
        """Visit a declare cursor node."""
        self._track_node_position(node)
        super().visit_declare_cursor(node)

    def visit_declare_procedure(self, node) -> None:
        """Visit a declare procedure node."""
        self._track_node_position(node)
        super().visit_declare_procedure(node)

    def visit_default_variable(self, node) -> str:
        """Visit a default variable node."""
        self._track_node_position(node)
        return super().visit_default_variable(node)

    def visit_descriptor(self, node) -> None:
        """Visit a descriptor node."""
        self._track_node_position(node)
        super().visit_descriptor(node)

    def visit_destroy_statement(self, node) -> None:
        """Visit a destroy statement node."""
        self._track_node_position(node)
        super().visit_destroy_statement(node)

    def visit_do_loop_until(self, node) -> None:
        """Visit a do loop until node."""
        self._track_node_position(node)
        super().visit_do_loop_until(node)

    def visit_do_loop_while(self, node) -> None:
        """Visit a do loop while node."""
        self._track_node_position(node)
        super().visit_do_loop_while(node)

    def visit_do_until_loop(self, node) -> None:
        """Visit a do until loop node."""
        self._track_node_position(node)
        super().visit_do_until_loop(node)

    def visit_do_while_loop(self, node) -> None:
        """Visit a do while loop node."""
        self._track_node_position(node)
        super().visit_do_while_loop(node)

    def visit_dynamic_method_invocation(self, node) -> None:
        """Visit a dynamic method invocation node."""
        self._track_node_position(node)
        super().visit_dynamic_method_invocation(node)

    def visit_else(self, node) -> None:
        """Visit an else node."""
        self._track_node_position(node)
        super().visit_else(node)

    def visit_else_if(self, node) -> None:
        """Visit an else if node."""
        self._track_node_position(node)
        super().visit_else_if(node)

    def visit_else_on_line(self, node) -> None:
        """Visit an else on line node."""
        self._track_node_position(node)
        super().visit_else_on_line(node)

    def visit_end_forward(self, node) -> str:
        """Visit an end forward node."""
        self._track_node_position(node)
        return super().visit_end_forward(node)

    def visit_event_attribute(self, node) -> None:
        """Visit an event attribute node."""
        self._track_node_position(node)
        super().visit_event_attribute(node)

    def visit_event_declaration(self, node) -> None:
        """Visit an event declaration node."""
        self._track_node_position(node)
        super().visit_event_declaration(node)

    def visit_event_invocation(self, node) -> None:
        """Visit an event invocation node."""
        self._track_node_position(node)
        super().visit_event_invocation(node)

    def visit_event_long(self, node) -> None:
        """Visit an event long node."""
        self._track_node_position(node)
        super().visit_event_long(node)

    def visit_event_name(self, node) -> None:
        """Visit an event name node."""
        self._track_node_position(node)
        super().visit_event_name(node)

    def visit_event_reference_name(self, node) -> None:
        """Visit an event reference name node."""
        self._track_node_position(node)
        super().visit_event_reference_name(node)

    def visit_event_triggering_or_posting(self, node) -> None:
        """Visit an event triggering or posting node."""
        self._track_node_position(node)
        super().visit_event_triggering_or_posting(node)

    def visit_event_type(self, node) -> None:
        """Visit an event type node."""
        self._track_node_position(node)
        super().visit_event_type(node)

    def visit_event_word(self, node) -> None:
        """Visit an event word node."""
        self._track_node_position(node)
        super().visit_event_word(node)

    def visit_execute_procedure(self, node) -> None:
        """Visit an execute procedure node."""
        self._track_node_position(node)
        super().visit_execute_procedure(node)

    def visit_exit_statement(self, node) -> str:
        """Visit an exit statement node."""
        self._track_node_position(node)
        return super().visit_exit_statement(node)

    def visit_export(self, node) -> None:
        """Visit an export node."""
        self._track_node_position(node)
        super().visit_export(node)

    def visit_expression(self, node) -> None:
        """Visit an expression node."""
        self._track_node_position(node)
        super().visit_expression(node)

    def visit_expression_action(self, node) -> None:
        """Visit an expression action node."""
        self._track_node_position(node)
        super().visit_expression_action(node)

    def visit_expression_list(self, node) -> None:
        """Visit an expression list node."""
        self._track_node_position(node)
        super().visit_expression_list(node)

    def visit_expression_operator(self, node) -> str:
        """Visit an expression operator node."""
        self._track_node_position(node)
        return super().visit_expression_operator(node)

    def _track_node_position(self, node: Any) -> None:
        """Track position information for a node.

        Args:
            node: Node to track position for
        """
        if isinstance(node, PBNode):
            if node.start_position is None or node.stop_position is None:
                self._nodes_without_position.append(node)
                logger.debug(
                    "Node %s at %s has no position information",
                    type(node).__name__,
                    id(node),
                )
            elif self.validate:
                self._validate_node_position(node)


def track_positions_in_transformer[T](transformer_class: type[T]) -> type[T]:
    """Decorator to add position tracking to a transformer class.

    Args:
        transformer_class: Transformer class to enhance

    Returns:
        Enhanced transformer class with position tracking
    """

    class PositionTrackingTransformer(PositionTrackerMixin, transformer_class):
        """Transformer with automatic position tracking."""

        def transform(self, tree: Tree) -> Any:
            """Transform tree with position tracking.

            Args:
                tree: Parse tree to transform

            Returns:
                Transformed result with position information
            """
            # Extract position from the tree
            position = self.extract_position_from_tree(tree)

            # Transform with position context
            with self.with_position_context(position):
                result = super().transform(tree)

                # Annotate result with position if it's an AST node
                if isinstance(result, PBNode):
                    self.annotate_node_with_position(result, position)

                return result

        def __default__(self, data, children, meta):
            """Default transformer method with position tracking.

            Args:
                data: Rule name
                children: Child nodes
                meta: Metadata including position info

            Returns:
                Transformed result
            """
            # Create position from meta
            position = None
            if meta:
                position = PositionRange(
                    start_line=meta.line,
                    start_column=meta.column,
                    end_line=getattr(meta, "end_line", meta.line),
                    end_column=getattr(meta, "end_column", meta.column),
                    start_offset=getattr(meta, "start_pos", None),
                    end_offset=getattr(meta, "end_pos", None),
                    filename=self._current_filename,
                )

            with self.with_position_context(position):
                result = super().__default__(data, children, meta)

                # Annotate result if it's an AST node
                if isinstance(result, PBNode):
                    self.annotate_node_with_position(result, position)

                return result

    # Preserve class metadata
    PositionTrackingTransformer.__name__ = transformer_class.__name__
    PositionTrackingTransformer.__qualname__ = transformer_class.__qualname__
    PositionTrackingTransformer.__module__ = transformer_class.__module__

    return PositionTrackingTransformer
