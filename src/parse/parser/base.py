"""PowerBuilder base parser module.

This module provides the abstract base class for all PowerBuilder parsers.
"""

from __future__ import annotations

import logging
from abc import ABC, abstractmethod
from functools import lru_cache
from pathlib import Path
from typing import TYPE_CHECKING, Any, ClassVar

from lark import Lark, Token, Tree
from lark.exceptions import (
    UnexpectedInput,
)

from src.core.constants import FILE_EXTENSIONS, FileType
from src.core.exceptions import ASTConstructionError, ParseError, ParseRecoveryError

if TYPE_CHECKING:
    from lark.visitors import Transformer

logger = logging.getLogger(__name__)


class PowerBuilderBaseParser(ABC):
    """Abstract base class for all PowerBuilder parsers.

    Provides common functionality for parsing PowerBuilder source files including:
    - Error handling and recovery
    - Position tracking
    - Parse tree to AST conversion
    - Integration with Lark parser

    Subclasses must implement:
    - parse(): Main parsing method
    - supports(): Check if parser can handle a file type
    """

    # Parser type identifier (override in subclasses)
    PARSER_TYPE: ClassVar[str] = "base"

    # Supported file extensions (override in subclasses)
    SUPPORTED_EXTENSIONS: ClassVar[set[str]] = set()

    # Default parser settings
    DEFAULT_PARSER_OPTIONS: ClassVar[dict[str, Any]] = {
        "parser": "earley",  # More robust for error recovery
        "propagate_positions": True,
        "maybe_placeholders": True,
        "lexer": "dynamic",
    }

    def __init__(self, base_path: Path | None = None, **parser_options: Any) -> None:
        """Initialize the base parser.

        Args:
            base_path: Base path for resolving includes and imports
            **parser_options: Additional options for Lark parser
        """
        self.base_path = base_path or Path.cwd()
        self.parser_options = {**self.DEFAULT_PARSER_OPTIONS, **parser_options}

        # Parse state
        self._current_file: Path | None = None
        self._parse_errors: list[dict[str, Any]] = []
        self._recovery_attempts: int = 0
        self._max_recovery_attempts: int = 3

        # Lark parser instance (lazily initialized)
        self._parser: Lark | None = None

        logger.debug(
            "Initialized %s parser with base_path=%s", self.PARSER_TYPE, self.base_path
        )

    @property
    def parser(self) -> Lark:
        """Get or create the Lark parser instance.

        Returns:
            Configured Lark parser

        Raises:
            ParseError: If parser creation fails
        """
        if self._parser is None:
            self._parser = self._create_parser()
        return self._parser

    @abstractmethod
    def _create_parser(self) -> Lark:
        """Create the Lark parser instance.

        Subclasses must implement this to create their specific parser.

        Returns:
            Configured Lark parser

        Raises:
            ParseError: If parser creation fails
        """

    @abstractmethod
    def parse(self, source: str | Path, **kwargs: Any) -> Tree | Any:
        """Parse PowerBuilder source code.

        Args:
            source: Source code string or file path
            **kwargs: Additional parsing options

        Returns:
            Parse tree or transformed AST

        Raises:
            ParseError: If parsing fails
        """

    def supports(self, file_path: Path) -> bool:
        """Check if this parser supports the given file.

        Args:
            file_path: Path to the file

        Returns:
            True if this parser can handle the file
        """
        extension = file_path.suffix.lstrip(".")
        return extension.lower() in self.SUPPORTED_EXTENSIONS

    def parse_with_error_recovery(
        self, source: str, filename: str | None = None
    ) -> Tree:
        """Parse with automatic error recovery.

        Args:
            source: Source code to parse
            filename: Optional filename for error reporting

        Returns:
            Parse tree (possibly partial)

        Raises:
            ParseError: If parsing fails after all recovery attempts
        """
        self._parse_errors.clear()
        self._recovery_attempts = 0

        try:
            # First attempt: normal parsing
            tree = self.parser.parse(source)
            logger.debug("Successfully parsed %s", filename or "source")
            return tree

        except UnexpectedInput as e:
            logger.warning(
                "Parse error in %s at line %d, col %d: %s",
                filename or "source",
                e.line,
                e.column,
                e,
            )

            # Store the error
            self._record_parse_error(e, filename)

            # Attempt recovery
            return self._recover_from_error(source, e, filename)

    def _recover_from_error(
        self, source: str, error: UnexpectedInput, filename: str | None = None
    ) -> Tree:
        """Attempt to recover from a parse error.

        Args:
            source: Original source code
            error: The parse error
            filename: Optional filename

        Returns:
            Partial parse tree

        Raises:
            ParseRecoveryError: If recovery fails
        """
        self._recovery_attempts += 1

        if self._recovery_attempts > self._max_recovery_attempts:
            raise ParseRecoveryError(
                self._recovery_attempts, str(error), filename=filename
            )

        # Strategy 1: Skip problematic line
        recovered_tree = self._skip_line_recovery(source, error)
        if recovered_tree:
            return recovered_tree

        # Strategy 2: Parse up to error
        partial_tree = self._partial_parse_recovery(source, error)
        if partial_tree:
            return partial_tree

        # Strategy 3: Create error node
        return self._create_error_tree(source, error)

    def _skip_line_recovery(self, source: str, error: UnexpectedInput) -> Tree | None:
        """Try to recover by skipping the problematic line.

        Args:
            source: Source code
            error: Parse error

        Returns:
            Parse tree if successful, None otherwise
        """
        lines = source.splitlines()
        error_line = error.line - 1  # Convert to 0-based

        if 0 <= error_line < len(lines):
            # Comment out the problematic line
            lines[error_line] = f"// PARSE ERROR: {lines[error_line]}"
            modified_source = "\n".join(lines)

            try:
                tree = self.parser.parse(modified_source)
                logger.info("Recovered by commenting line %d", error.line)
                return tree
            except UnexpectedInput:
                pass

        return None

    def _partial_parse_recovery(
        self, source: str, error: UnexpectedInput
    ) -> Tree | None:
        """Try to parse up to the error point.

        Args:
            source: Source code
            error: Parse error

        Returns:
            Partial parse tree if successful, None otherwise
        """
        lines = source.splitlines()
        error_line = error.line - 1  # Convert to 0-based

        if error_line > 0:
            partial_source = "\n".join(lines[:error_line])
            if partial_source.strip():
                try:
                    tree = self.parser.parse(partial_source)
                    logger.info("Partially parsed up to line %d", error_line)
                    return tree
                except UnexpectedInput:
                    pass

        return None

    def _create_error_tree(self, source: str, error: UnexpectedInput) -> Tree:
        """Create a minimal tree with error information.

        Args:
            source: Source code
            error: Parse error

        Returns:
            Error tree
        """
        logger.warning("Creating error tree for unrecoverable parse error")

        # Create error token with position info
        error_token = Token(
            "PARSE_ERROR", str(error), line=error.line, column=error.column
        )

        # Create error tree
        return Tree("error", [error_token])

    def _record_parse_error(
        self, error: UnexpectedInput, filename: str | None = None
    ) -> None:
        """Record a parse error for later retrieval.

        Args:
            error: The parse error
            filename: Optional filename
        """
        error_info = {
            "line": error.line,
            "column": error.column,
            "message": str(error),
            "filename": filename,
            "type": type(error).__name__,
        }

        # Add expected tokens if available
        if hasattr(error, "expected"):
            error_info["expected"] = list(error.expected)

        self._parse_errors.append(error_info)

    def get_parse_errors(self) -> list[dict[str, Any]]:
        """Get list of parse errors encountered.

        Returns:
            List of error dictionaries
        """
        return self._parse_errors.copy()

    def has_errors(self) -> bool:
        """Check if any parse errors were encountered.

        Returns:
            True if errors exist
        """
        return bool(self._parse_errors)

    def clear_errors(self) -> None:
        """Clear all recorded parse errors."""
        self._parse_errors.clear()
        self._recovery_attempts = 0

    def transform_tree(self, tree: Tree, transformer: Transformer | None = None) -> Any:
        """Transform parse tree to AST.

        Args:
            tree: Parse tree from Lark
            transformer: Optional transformer to use

        Returns:
            Transformed AST

        Raises:
            ASTConstructionError: If transformation fails
        """
        if transformer is None:
            # Subclasses should provide their own transformer
            return tree

        try:
            return transformer.transform(tree)
        except (ValueError, TypeError, AttributeError, KeyError) as e:
            raise ASTConstructionError(
                node_type=tree.data if hasattr(tree, "data") else "unknown",
                reason=str(e),
            )

    @lru_cache(maxsize=128)
    def _get_file_type(self, file_path: Path) -> FileType | None:
        """Get FileType enum for a file path.

        Args:
            file_path: Path to file

        Returns:
            FileType enum or None if not recognized
        """
        extension = file_path.suffix.lstrip(".").lower()
        return FILE_EXTENSIONS.get(extension)

    def _validate_source(self, source: str | Path) -> tuple[str, Path | None]:
        """Validate and normalize source input.

        Args:
            source: Source code or file path

        Returns:
            Tuple of (source_text, file_path)

        Raises:
            ParseError: If source is invalid
        """
        if isinstance(source, Path):
            if not source.exists():
                raise ParseError(
                    f"Source file not found: {source}", filename=str(source)
                )

            try:
                source_text = source.read_text(encoding="utf-8")
                return source_text, source
            except (OSError, IOError, UnicodeDecodeError, PermissionError) as e:
                raise ParseError(
                    f"Failed to read source file: {e}", filename=str(source)
                )

        elif isinstance(source, str):
            return source, None

        else:
            raise ParseError(
                f"Invalid source type: {type(source).__name__}. Expected str or Path"
            )

    def __repr__(self) -> str:
        """Return string representation of parser."""
        return (
            f"{self.__class__.__name__}("
            f"type={self.PARSER_TYPE}, "
            f"extensions={self.SUPPORTED_EXTENSIONS})"
        )
