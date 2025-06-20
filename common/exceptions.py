"""Unified exception hierarchy for SIME Finch.

This module consolidates all exceptions from across the project into a single,
consistent hierarchy. All exceptions inherit from SimeFinchError.
"""

from __future__ import annotations

from typing import Any

# =============================================================================
# Base Exception Hierarchy
# =============================================================================


class SimeFinchError(Exception):
    """Base exception for all sime-finch errors.

    All exceptions in the project should inherit from this class to ensure
    consistent error handling and proper error hierarchy.
    """

    def __init__(self, message: str, **kwargs: object) -> None:
        """Initialize the error with a message and optional context.

        Args:
            message: Error message
            **kwargs: Additional context (e.g., line, column, filename)
        """
        super().__init__(message)
        self.message = message
        self.context = kwargs


# Backward compatibility alias
Error = SimeFinchError


class PowerBuilderError(SimeFinchError):
    """Base class for PowerBuilder-specific errors.

    Used for errors related to PowerBuilder language features, constructs,
    or runtime behavior.
    """


# =============================================================================
# Core Component Errors
# =============================================================================


class ParseError(SimeFinchError):
    """Error during parsing phase.

    Raised when parsing PowerBuilder source code or related formats fails.
    Includes position information when available.
    """

    def __init__(
        self,
        message: str,
        filename: str | None = None,
        line: int | None = None,
        column: int | None = None,
        **kwargs: object,
    ) -> None:
        """Initialize parse error with position information.

        Args:
            message: Error message
            filename: Source filename
            line: Line number (1-based)
            column: Column number (1-based)
            **kwargs: Additional context
        """
        super().__init__(message, filename=filename, line=line, column=column, **kwargs)
        self.filename = filename
        self.line = line
        self.column = column

    def __str__(self) -> str:
        """Return formatted error message with position."""
        parts = []

        if self.filename:
            parts.append(f"File '{self.filename}'")

        if self.line is not None:
            if self.column is not None:
                parts.append(f"line {self.line}:{self.column}")
            else:
                parts.append(f"line {self.line}")

        if parts:
            return f"{', '.join(parts)}: {self.message}"
        return self.message


class ExtractError(SimeFinchError):
    """Error during extraction phase.

    Raised when extracting source code from PBL/PBD files fails.
    """


class ModelError(SimeFinchError):
    """Error in model operations.

    Raised when model creation, manipulation, or validation fails.
    """


class DecompileError(SimeFinchError):
    """Error during decompilation phase.

    Raised when decompiling P-code to higher-level code fails.
    """


class GenerateError(SimeFinchError):
    """Error during code generation phase.

    Raised when generating target code (Python, Flutter, etc.) fails.
    """


class TransformError(SimeFinchError):
    """Error during AST transformation.

    Raised when transforming parse trees to AST nodes fails.
    """


# =============================================================================
# Validation and Type Errors
# =============================================================================


class ValidationError(SimeFinchError):
    """General validation error.

    Raised when data validation fails (e.g., invalid values, constraints).
    """


class TypeValidationError(ValidationError):
    """Type validation error.

    Raised when type checking or type validation fails.
    """

    def __init__(
        self,
        message: str,
        expected_type: str | None = None,
        actual_type: str | None = None,
        **kwargs: object,
    ) -> None:
        """Initialize type validation error.

        Args:
            message: Error message
            expected_type: Expected type name
            actual_type: Actual type name
            **kwargs: Additional context
        """
        super().__init__(
            message, expected_type=expected_type, actual_type=actual_type, **kwargs,
        )
        self.expected_type = expected_type
        self.actual_type = actual_type


# =============================================================================
# Configuration Errors
# =============================================================================


class ConfigurationError(SimeFinchError):
    """Configuration error.

    Raised when configuration is invalid or missing required values.
    """


# =============================================================================
# Parser-Specific Errors
# =============================================================================


class GrammarError(ParseError):
    """Base class for grammar-related errors."""


class GrammarLoadError(GrammarError):
    """Error loading grammar file."""


class GrammarParseError(GrammarError):
    """Error parsing grammar definition."""


class GrammarNotFoundError(GrammarError):
    """Error when a grammar file cannot be found."""


class PowerBuilderSyntaxError(ParseError):
    """Syntax error in PowerBuilder source code.

    Provides consistent error handling within our framework without
    shadowing Python's built-in SyntaxError.
    """


class PreprocessorError(ParseError):
    """Error during preprocessing phase."""


class MacroError(PreprocessorError):
    """Error processing macros."""


class IncludeError(PreprocessorError):
    """Error processing include directives."""


class ConditionalError(PreprocessorError):
    """Error processing conditional compilation."""


class TransformerError(TransformError):
    """Error during tree transformation."""


class VisitorError(TransformError):
    """Error during tree visitation."""


class ModelGenerationError(ModelError):
    """Error generating model from AST."""


# =============================================================================
# Extraction-Specific Errors
# =============================================================================


class PbdError(ExtractError):
    """Base class for PBD/PBL file errors."""


class DataExtractionError(PbdError):
    """General data extraction error from PBD/PBL files."""


class HeaderError(PbdError):
    """Error parsing PBL/PBD file header."""


class NodeError(PbdError):
    """Error parsing NOD block."""


class EntryError(PbdError):
    """Error parsing PbEntryDefinition."""


class DatError(PbdError):
    """Error parsing DAT block."""


class PfcExcludedError(PbdError):
    """Object excluded due to PFC hash match."""

    def __init__(self, object_name: str, hash_value: str, **kwargs: object) -> None:
        """Initialize PFC exclusion error.

        Args:
            object_name: Name of excluded object
            hash_value: Hash that matched PFC
            **kwargs: Additional context
        """
        message = f"Object '{object_name}' excluded (PFC hash: {hash_value})"
        super().__init__(
            message, object_name=object_name, hash_value=hash_value, **kwargs,
        )
        self.object_name = object_name
        self.hash_value = hash_value


# =============================================================================
# Transaction-Specific Errors
# =============================================================================


class TransactionError(PowerBuilderError):
    """Transaction-related error.

    Used for database transaction errors with optional SQL state codes.
    """

    def __init__(
        self,
        message: str,
        sql_state: str | None = None,
        error_code: int | None = None,
        **kwargs: object,
    ) -> None:
        """Initialize transaction error.

        Args:
            message: Error message
            sql_state: SQL state code (e.g., '23000')
            error_code: Database-specific error code
            **kwargs: Additional context
        """
        super().__init__(message, sql_state=sql_state, error_code=error_code, **kwargs)
        self.sql_state = sql_state
        self.error_code = error_code

    def __str__(self) -> str:
        """Return formatted error message with SQL state."""
        parts = [self.message]

        if self.sql_state:
            parts.append(f"SQLSTATE: {self.sql_state}")

        if self.error_code:
            parts.append(f"Error code: {self.error_code}")

        return " - ".join(parts)


# =============================================================================
# Tool-Level Errors (High-level pipeline errors)
# =============================================================================


class PowerBuilderToolError(SimeFinchError):
    """Base class for high-level tool errors.

    These represent failures at the pipeline/tool level rather than
    specific component failures.
    """


class ExtractionError(PowerBuilderToolError):
    """High-level extraction phase error."""


class ParsingError(PowerBuilderToolError):
    """High-level parsing phase error."""


class DecompilationError(PowerBuilderToolError):
    """High-level decompilation phase error."""


class GenerationError(PowerBuilderToolError):
    """High-level generation phase error."""


# =============================================================================
# Aliases for backward compatibility
# =============================================================================

# Parser aliases
ParserError = ParseError

# PBD-specific aliases
PBDError = PbdError
PBDHeaderError = HeaderError
PBDNodeError = NodeError
PBDEntryError = EntryError
PBDDataError = DatError

# Transaction aliases
PBTransactionError = TransactionError
