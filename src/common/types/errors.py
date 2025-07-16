"""Common error types shared across modules.

This module contains shared error and exception types to avoid circular imports.
"""

from dataclasses import dataclass, field
from pathlib import Path


@dataclass
class ParseError:
    """Represents a parse error with context."""

    line: int
    column: int
    message: str
    error_type: str
    context: str | None = None
    expected: list[str | None] = None
    found: str | None = None
    file_path: Path | None = None

    def __str__(self) -> str:
        """Format error for display."""
        location = f"{self.file_path}:" if self.file_path else ""
        location += f"{self.line}:{self.column}"

        msg = f"{location}: {self.error_type}: {self.message}"
        if self.context:
            msg += f"\n  Context: {self.context}"
        if self.expected:
            msg += f"\n  Expected: {", ".join(self.expected)}"
        if self.found:
            msg += f"\n  Found: {self.found}"
        return msg


@dataclass
class ErrorCollector:
    """Collects parse errors during parsing."""

    errors: list[ParseError] = field(default_factory=list)
    max_errors: int = 500  # Increased from 100 for better handling of complex files
    file_path: Path | None = None

    def add_error(self, error: ParseError) -> None:
        """Add an error to the collection."""
        if self.file_path and not error.file_path:
            error.file_path = self.file_path

        self.errors.append(error)

        if len(self.errors) >= self.max_errors:
            import logging
            logger = logging.getLogger(__name__)
            logger.warning("Maximum error count (%s) reached", self.max_errors)

    def has_errors(self) -> bool:
        """Check if any errors were collected."""
        return len(self.errors) > 0

    def get_error_count(self) -> int:
        """Get the number of errors collected."""
        return len(self.errors)

    def get_errors_by_type(self) -> dict[str, list[ParseError]]:
        """Group errors by type."""
        by_type: dict[str, list[ParseError]] = {}
        for error in self.errors:
            if error.error_type not in by_type:
                by_type[error.error_type] = []
            by_type[error.error_type].append(error)
        return by_type

    def clear(self) -> None:
        """Clear all collected errors."""
        self.errors.clear()