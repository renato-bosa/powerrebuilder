"""Exceptions for the PowerBuilder parser.

This module provides custom exceptions for the PowerBuilder parser, making it
easier to handle and report specific error conditions.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from model.utils.errors import SimeFinchError


class ParseError(SimeFinchError):
    """Base class for all parser-related errors."""

    def __init__(
        self,
        message: str,
        file_path: str | Path | None = None,
        line: int | None = None,
        column: int | None = None,
        source_context: str | None = None,
        details: dict[str, Any] | None = None,
    ) -> None:
        self.file_path = Path(file_path) if file_path else None
        self.line = line
        self.column = column
        self.source_context = source_context
        self.details = details or {}

        # Build a more detailed error message if context is available
        detailed_message = message
        if self.file_path:
            detailed_message = f"{detailed_message}\nFile: {self.file_path}"
        if self.line is not None:
            line_info = f"Line: {self.line}"
            if self.column is not None:
                line_info = f"{line_info}, Column: {self.column}"
            detailed_message = f"{detailed_message}\n{line_info}"
        if self.source_context:
            detailed_message = f"{detailed_message}\n{self.source_context}"

        super().__init__(detailed_message)


class GrammarError(ParseError):
    """Base class for grammar-related errors."""

    pass


class GrammarLoadError(GrammarError):
    """Error loading a grammar file."""

    pass


class GrammarParseError(GrammarError):
    """Error parsing source with a grammar."""

    pass


class SyntaxError(ParseError):
    """Error in the syntax of the source code."""

    pass


class PreprocessorError(ParseError):
    """Error during preprocessing."""

    pass


class MacroError(PreprocessorError):
    """Error in macro processing."""

    pass


class IncludeError(PreprocessorError):
    """Error processing an include directive."""

    pass


class ConditionalError(PreprocessorError):
    """Error in conditional compilation."""

    pass


class TransformerError(ParseError):
    """Error during tree transformation."""

    pass


class VisitorError(ParseError):
    """Error during tree visitation."""

    pass


class ModelGenerationError(ParseError):
    """Error generating a model from a parse tree."""

    pass
