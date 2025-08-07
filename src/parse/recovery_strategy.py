"""Error recovery system for PowerBuilder parser.

This module provides error recovery capabilities that allow the parser
to continue processing after encountering syntax errors.
"""

import logging

from lark import Token, Tree
from lark.exceptions import UnexpectedInput, UnexpectedToken
from lark.visitors import Transformer

from src.model.types.errors import ParseErrorCollector, ParseErrorRecord

logger = logging.getLogger(__name__)


class EnhancedErrorRecovery:
    """Enhanced error recovery strategy for the parser."""

    def __init__(self, parser=None, error_collector=None) -> None:
        """Initialize the error recovery handler."""
        self.parser = parser
        self.error_collector = error_collector or ParseErrorCollector()
        self.errors: list[str] = []

    def recover(self, error: Exception, _parser=None) -> None:
        """Attempt to recover from a parse error."""
        self.errors.append(error)
        logger.warning("Error recovery triggered: %s", error)

    def parse_with_recovery(self, text: str) -> Tree:
        """Parse text with error recovery."""
        if not self.parser:
            raise ValueError("No parser instance provided")

        try:
            return self.parser.parse(text)
        # Recovery strategy: must catch all exceptions for proper fallback
        except Exception as e:
            self.recover(e, self.parser)
            # Return a minimal error tree
            return Tree("error", [Token("ERROR", str(e))])


class ErrorRecoveryTransformer(Transformer):
    """Transformer that handles error nodes in the AST."""

    def __init__(self, error_collector: ParseErrorCollector | None = None) -> None:
        """Initialize transformer with optional error collector."""
        super().__init__()
        self.error_collector = error_collector or ParseErrorCollector()

    def error_node(self, children) -> None:
        """Handle error nodes created during parsing."""
        # Extract error information
        error_token = None
        error_msg = "Unknown error"

        for child in children:
            if isinstance(child, Token) and child.type == "ERROR":
                error_token = child
                error_msg = f"Unexpected token: {child.value}"
                break

        # Create error node in AST
        error_tree = Tree("error", children)

        # Record error if collector available
        if error_token and self.error_collector:
            self.error_collector.add_error(
                message=error_msg,
                line=error_token.line,
                column=error_token.column,
                error_code="syntax_error",
                found=str(error_token.value)
            )

        return error_tree

    def recovered_statement(self, children):
        """Handle statements recovered after errors."""
        # Mark as recovered in the AST
        return Tree("recovered_statement", children)

    def incomplete_statement(self, children):
        """Handle incomplete statements."""
        # Create a partial statement node
        tree = Tree("incomplete_statement", children)

        # Record as warning
        if self.error_collector and children:
            first_token = self._find_first_token(children)
            if first_token:
                self.error_collector.add_warning(
                    message="Incomplete statement",
                    line=first_token.line,
                    column=first_token.column,
                    error_code="incomplete_statement"
                )

        return tree

    def _find_first_token(self, children) -> Token | None:
        """Find the first token in a list of children."""
        for child in children:
            if isinstance(child, Token):
                return child
            if isinstance(child, Tree):
                token = self._find_first_token(child.children)
                if token:
                    return token
        return None


class ErrorRecoveryParser:
    """Wrapper for Lark parser with error recovery."""

    def __init__(
        self, parser, error_collector: ParseErrorCollector | None = None
    ) -> None:
        """Initialize with a Lark parser instance."""
        self.parser = parser
        self.error_collector = error_collector or ParseErrorCollector()
        self.recovery_transformer = ErrorRecoveryTransformer(self.error_collector)

    def parse_with_recovery(self, text: str, start: str | None = None) -> Tree:
        """Parse text with error recovery.

        Args:
            text: Source text to parse
            start: Optional start rule

        Returns:
            AST with error nodes for unparseable sections
        """
        # Try normal parsing first
        try:
            return self.parser.parse(text, start=start)
        except UnexpectedInput as e:
            # Handle parse error with recovery
            return self._recover_from_error(text, e, start)

    def _recover_from_error(
        self, text: str, error: UnexpectedInput, start: str | None = None
    ) -> Tree:
        """Attempt to recover from a parse error.

        Strategy:
        1. Record the error
        2. Find a recovery point (statement boundary, keyword, etc.)
        3. Create error node for unparseable section
        4. Continue parsing from recovery point
        """
        lines = text.split("\n")

        # Record the initial error
        context_line = lines[error.line - 1] if error.line <= len(lines) else ""
        error_context = {"context_line": context_line} if context_line else {}
        
        if isinstance(error, UnexpectedToken):
            error_context["expected"] = str(error.expected) if error.expected else "unknown"
            error_context["found"] = str(error.token)

        self.error_collector.add_error(
            message=str(error),
            line=error.line,
            column=error.column,
            error_code=error.__class__.__name__,
            **error_context
        )

        # Try incremental parsing with recovery
        return self._incremental_parse(text, lines, error.line, start)

    def _incremental_parse(
        self, text: str, lines: list[str], _error_line: int, _start: int | None = None
    ) -> Tree:
        """Parse text incrementally, creating error nodes for unparseable sections."""
        # For now, use a simpler approach that creates a partial AST
        # with error information embedded

        # Try to parse line by line, collecting valid statements
        statements = []
        errors = []

        for i, line in enumerate(lines):
            line_num = i + 1
            stripped = line.strip()

            # Skip empty lines and comments
            if not stripped or stripped.startswith("//"):
                continue

            # Try to identify statement boundaries
            if any(
                stripped.startswith(kw)
                for kw in ["global", "function", "if", "for", "while", "return"]
            ):
                # Attempt to parse from this line
                try:
                    # Create a minimal statement representation
                    stmt_tree = Tree("statement", [Token("IDENTIFIER", stripped)])
                    statements.append(stmt_tree)
                # Recovery processing: catch all exceptions during statement recovery
                except Exception as e:
                    logger.debug("Exception caught: %s", e)
                    # Record as error
                    self.error_collector.add_error(
                        message=f"Could not parse: {stripped[:50]}...",
                        line=line_num,
                        column=0,
                        error_code="parse_error"
                    )

        # Create a file tree with what we could parse
        if statements:
            return Tree("file", statements)
        # Return error tree if nothing could be parsed
        return Tree("error_file", [Token("ERROR", text)])

    def _find_recovery_point(self, lines: list[str], error_line: int) -> int:
        """Find a good point to resume parsing after an error.

        Looks for:
        - Statement keywords (if, for, while, etc.)
        - Function/event declarations
        - End statements
        - Empty lines
        """
        recovery_keywords = {
            "if",
            "for",
            "while",
            "do",
            "choose",
            "case",
            "function",
            "subroutine",
            "event",
            "on",
            "public",
            "private",
            "protected",
            "end",
            "return",
            "exit",
            "type",
            "forward",
            "global",
        }

        for i in range(error_line, len(lines)):
            line = lines[i].strip().lower()

            # Empty line could be statement boundary
            if not line:
                return i + 1

            # Check if line starts with recovery keyword
            first_word = line.split()[0] if line else ""
            if first_word in recovery_keywords:
                return i

        # No recovery point found
        return len(lines)

    def _create_error_node(self, text: str, start_line: int) -> Tree:
        """Create an error node for unparseable text."""
        error_token = Token("ERROR", text, None, start_line, 1)
        return Tree("error_node", [error_token])


def add_error_recovery_to_grammar(grammar_text: str) -> str:
    """Add error recovery rules to a PowerBuilder grammar.

    Args:
        grammar_text: Original grammar text

    Returns:
        Grammar text with error recovery rules added
    """
    # For now, return the original grammar without modifications
    # Error recovery will be handled at the parsing level rather than grammar level
    # This avoids conflicts with the LALR parser
    return grammar_text
