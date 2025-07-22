"""Example usage of the position tracking utilities.

This example shows how to use the position tracking utilities with Lark transformers
and the visitor pattern to ensure all AST nodes have proper position information.
"""

from lark import Lark, Transformer

from ....model.types.base import PBNode
from .positions import (
    PositionTrackerMixin,
    PositionTrackingVisitor,
    track_positions_in_transformer,
)


# Example 1: Using the mixin directly in a transformer
class MyTransformer(PositionTrackerMixin, Transformer):
    """Example transformer with position tracking."""

    def __init__(self, filename: str | None = None):
        """Initialize the transformer with source context."""
        super().__init__()
        if filename:
            self.set_source_context(filename)

    def identifier(self, items):
        """Transform an identifier with position tracking."""
        # Extract position from the token
        token = items[0]
        position = self.extract_position_from_token(token)

        # Create AST node
        node = IdentifierNode(name=str(token))

        # Annotate with position
        return self.annotate_node_with_position(node, position)

    def expression(self, items):
        """Transform an expression with position tracking."""
        # For tree nodes, extract position from meta
        position = self.get_current_position()

        # Create expression node
        expr = ExpressionNode(children=items)

        # Annotate with position
        return self.annotate_node_with_position(expr, position)


# Example 2: Using the decorator to automatically add position tracking
@track_positions_in_transformer
class SimpleTransformer(Transformer):
    """Transformer that automatically gets position tracking."""

    def number(self, items):
        """Transform a number literal."""
        return NumberNode(value=int(items[0]))

    def string(self, items):
        """Transform a string literal."""
        return StringNode(value=str(items[0]))

    def binary_op(self, items):
        """Transform a binary operation."""
        left, op, right = items
        return BinaryOpNode(left=left, operator=op, right=right)


# Example 3: Using the visitor to validate position information
def validate_positions_in_ast(ast_root: PBNode, filename: str | None = None) -> dict:
    """Validate that all nodes in the AST have position information.

    Args:
        ast_root: Root node of the AST
        filename: Source filename for context

    Returns:
        Report with validation results
    """
    visitor = PositionTrackingVisitor(validate=True)
    if filename:
        visitor.set_source_context(filename)

    # Visit the entire tree
    visitor.visit(ast_root)

    # Get the report
    report = visitor.get_report()

    # Log any issues
    if report["nodes_without_position"] > 0:
        print(
            f"Warning: {report['nodes_without_position']} nodes lack position information"
        )
        for node_type, count in report["unpositioned_node_types"].items():
            print(f"  - {node_type}: {count} instances")

    if report["validation_errors"] > 0:
        print(f"Error: {report['validation_errors']} position validation errors found")
        for error in report["errors"]:
            print(f"  - {error['message']}")

    return report


# Example 4: Using position information for error reporting
class ErrorReportingTransformer(PositionTrackerMixin, Transformer):
    """Transformer that uses position tracking for error reporting."""

    def __init__(self, source: str, filename: str | None = None):
        """Initialize with source code for error reporting."""
        super().__init__()
        self.set_source_context(filename, source)
        self.errors = []

    def invalid_syntax(self, items):
        """Handle invalid syntax with position-aware error."""
        error = self.create_error_with_position("Invalid syntax encountered")
        self.errors.append(error)

        # Return error node
        return ErrorNode(error=error)

    def undefined_variable(self, items):
        """Handle undefined variable with position context."""
        var_name = str(items[0])
        position = self.extract_position_from_token(items[0])

        error = self.create_error_with_position(
            f"Undefined variable: {var_name}", position
        )
        self.errors.append(error)

        return ErrorNode(error=error)

    def get_error_report(self) -> str:
        """Generate a formatted error report."""
        if not self.errors:
            return "No errors found"

        report = []
        for error in self.errors:
            report.append(
                f"{error['filename']}:{error['line']}:{error['column']}: {error['message']}"
            )
            if "line_content" in error:
                report.append(f"  {error['line_content']}")
                if "indicator" in error:
                    report.append(f"  {error['indicator']}")

        return "\n".join(report)


# Example stub node classes
class IdentifierNode(PBNode):
    def __init__(self, name: str):
        super().__init__()
        self.name = name


class ExpressionNode(PBNode):
    def __init__(self, children: list):
        super().__init__()
        self.children = children


class NumberNode(PBNode):
    def __init__(self, value: int):
        super().__init__()
        self.value = value


class StringNode(PBNode):
    def __init__(self, value: str):
        super().__init__()
        self.value = value


class BinaryOpNode(PBNode):
    def __init__(self, left, operator, right):
        super().__init__()
        self.left = left
        self.operator = operator
        self.right = right


class ErrorNode(PBNode):
    def __init__(self, error: dict):
        super().__init__()
        self.error = error


# Example usage
if __name__ == "__main__":
    # Example grammar
    grammar = """
    start: expression
    
    expression: term
              | expression "+" term -> add
              | expression "-" term -> subtract
    
    term: factor
        | term "*" factor -> multiply
        | term "/" factor -> divide
    
    factor: NUMBER -> number
          | "(" expression ")"
    
    %import common.NUMBER
    %import common.WS
    %ignore WS
    """

    # Create parser with position tracking
    parser = Lark(grammar, parser="lalr", propagate_positions=True)

    # Parse some code
    source = "42 + 3 * 7"
    tree = parser.parse(source)

    # Transform with position tracking
    transformer = SimpleTransformer()
    transformer.set_source_context("example.pb", source)
    ast = transformer.transform(tree)

    # Validate positions
    validate_positions_in_ast(ast, "example.pb")
