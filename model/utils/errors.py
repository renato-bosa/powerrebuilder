"""Error classes for the sime-finch project.

This module provides a unified error hierarchy for all aspects of the PowerBuilder tooling.
All custom exceptions should inherit from either SimeFinchError or one of its subclasses.
"""

from __future__ import annotations

from typing import Any


class SimeFinchError(Exception):
    """Base exception for all sime-finch errors.

    This is the top-level exception class that all other custom exceptions
    in the project should inherit from, either directly or indirectly.
    """

    def __init__(self, message: str, details: dict[str, Any] | None = None) -> None:
        """Initialize the error with a message and optional details.

        Args:
            message: The error message
            details: Optional dictionary with additional error context
        """
        super().__init__(message)
        self.message = message
        self.details = details or {}


class Error(SimeFinchError):
    """Base error class for all sime-finch errors.

    This class exists for backward compatibility. New code should use SimeFinchError.
    """

    pass


class PowerBuilderError(Error):
    """Base class for PowerBuilder-specific errors."""

    pass


class PowerBuilderToolError(PowerBuilderError):
    """Base error class for high-level PowerBuilder tool errors."""

    def __init__(
        self,
        message: str,
        component: str | None = None,
        details: dict[str, Any] | None = None,
    ) -> None:
        """Initialize PowerBuilder tool error.

        Args:
            message: Error message
            component: Component that raised the error
            details: Additional error details
        """
        super().__init__(message, details)
        self.component = component


class ParseError(PowerBuilderError):
    """Raised when there is an error parsing PowerBuilder code.

    This consolidates parse errors from both errors.py and utils.py.
    """

    def __init__(
        self,
        message: str,
        line: int | None = None,
        column: int | None = None,
        source: str | None = None,
        details: dict[str, Any] | None = None,
    ) -> None:
        """Initialize parse error with location information.

        Args:
            message: Error message
            line: Line number where error occurred
            column: Column number where error occurred
            source: Source code snippet where error occurred
            details: Additional error details
        """
        super().__init__(message, details)
        self.line = line
        self.column = column
        self.source = source


class ModelError(PowerBuilderError):
    """Raised when there is an error in model operations."""

    def __init__(
        self,
        message: str,
        model_type: str | None = None,
        model_id: str | None = None,
        details: dict[str, Any] | None = None,
    ) -> None:
        """Initialize model error with type information.

        Args:
            message: Error message
            model_type: Type of model where error occurred
            model_id: ID of model where error occurred
            details: Additional error details
        """
        super().__init__(message, details)
        self.model_type = model_type
        self.model_id = model_id


class ValidationError(PowerBuilderError):
    """Raised when there is a validation error.

    This consolidates ValidationError from both errors.py and utils.py.
    """

    def __init__(
        self,
        message: str,
        field: str | None = None,
        value: Any | None = None,
        details: dict[str, Any] | None = None,
    ) -> None:
        """Initialize validation error with field information.

        Args:
            message: Error message
            field: Field that failed validation
            value: Invalid value
            details: Additional error details
        """
        super().__init__(message, details)
        self.field = field
        self.value = value


class TypeValidationError(ValidationError):
    """Raised when there is an error validating a type."""

    def __init__(
        self,
        message: str,
        type_name: str | None = None,
        details: dict[str, Any] | None = None,
    ) -> None:
        """Initialize type validation error.

        Args:
            message: Error message
            type_name: Name of the type being validated
            details: Additional error details
        """
        super().__init__(message, field="type", value=type_name, details=details)
        self.type_name = type_name


class TransformError(PowerBuilderError):
    """Raised when there is an error during transformation.

    This consolidates TransformError from both errors.py and utils.py.
    """

    def __init__(
        self,
        message: str,
        node_type: str | None = None,
        details: dict[str, Any] | None = None,
    ) -> None:
        """Initialize transform error.

        Args:
            message: Error message
            node_type: Type of node being transformed
            details: Additional error details
        """
        super().__init__(message, details)
        self.node_type = node_type


class DecompileError(PowerBuilderError):
    """Raised when there is an error during decompilation."""

    def __init__(
        self,
        message: str,
        function: str | None = None,
        offset: int | None = None,
        details: dict[str, Any] | None = None,
    ) -> None:
        """Initialize decompile error with function information.

        Args:
            message: Error message
            function: Function being decompiled
            offset: Offset in bytecode where error occurred
            details: Additional error details
        """
        super().__init__(message, details)
        self.function = function
        self.offset = offset


class ExtractError(PowerBuilderError):
    """Raised when there is an error during extraction."""

    def __init__(
        self,
        message: str,
        file: str | None = None,
        encoding: str | None = None,
        details: dict[str, Any] | None = None,
    ) -> None:
        """Initialize extract error with file information.

        Args:
            message: Error message
            file: File being extracted
            encoding: File encoding being used
            details: Additional error details
        """
        super().__init__(message, details)
        self.file = file
        self.encoding = encoding


class GenerateError(PowerBuilderError):
    """Raised when there is an error during code generation."""

    def __init__(
        self,
        message: str,
        template: str | None = None,
        context: dict[str, Any] | None = None,
        details: dict[str, Any] | None = None,
    ) -> None:
        """Initialize generate error with template information.

        Args:
            message: Error message
            template: Template being used
            context: Template context
            details: Additional error details
        """
        super().__init__(message, details)
        self.template = template
        self.context = context or {}


class ConfigurationError(PowerBuilderError):
    """Raised when there is an error in configuration."""

    def __init__(
        self,
        message: str,
        config_key: str | None = None,
        config_value: Any | None = None,
        details: dict[str, Any] | None = None,
    ) -> None:
        """Initialize configuration error with key information.

        Args:
            message: Error message
            config_key: Configuration key that has an issue
            config_value: Configuration value that has an issue
            details: Additional error details
        """
        super().__init__(message, details)
        self.config_key = config_key
        self.config_value = config_value


class ParsingError(PowerBuilderToolError):
    """Raised when there is an error in the parsing phase."""

    def __init__(
        self,
        message: str,
        file: str | None = None,
        line: int | None = None,
        details: dict[str, Any] | None = None,
    ) -> None:
        """Initialize parsing error.

        Args:
            message: Error message
            file: File being parsed
            line: Line number where error occurred
            details: Additional error details
        """
        super().__init__(message, "parsing", details)
        self.file = file
        self.line = line


class DecompilationError(PowerBuilderToolError):
    """Raised when there is an error in the decompilation phase."""

    def __init__(
        self,
        message: str,
        file: str | None = None,
        function: str | None = None,
        details: dict[str, Any] | None = None,
    ) -> None:
        """Initialize decompilation error.

        Args:
            message: Error message
            file: File being decompiled
            function: Function being decompiled
            details: Additional error details
        """
        super().__init__(message, "decompilation", details)
        self.file = file
        self.function = function


class ExtractionError(PowerBuilderToolError):
    """Raised when there is an error in the extraction phase."""

    def __init__(
        self,
        message: str,
        file: str | None = None,
        details: dict[str, Any] | None = None,
    ) -> None:
        """Initialize extraction error.

        Args:
            message: Error message
            file: File being extracted
            details: Additional error details
        """
        super().__init__(message, "extraction", details)
        self.file = file


class GenerationError(PowerBuilderToolError):
    """Raised when there is an error in the code generation phase."""

    def __init__(
        self,
        message: str,
        template: str | None = None,
        output_file: str | None = None,
        details: dict[str, Any] | None = None,
    ) -> None:
        """Initialize generation error.

        Args:
            message: Error message
            template: Template being used
            output_file: Output file being generated
            details: Additional error details
        """
        super().__init__(message, "generation", details)
        self.template = template
        self.output_file = output_file


# Aliases for backward compatibility with parse/errors.py
ParserError = ParseError


def handle_error(
    error: Exception,
    error_cls: type[SimeFinchError] = SimeFinchError,
) -> SimeFinchError:
    """Convert any exception to a SimeFinchError with proper context.

    Args:
        error: The original exception
        error_cls: The specific SimeFinchError subclass to use

    Returns:
        A SimeFinchError instance with the original error details
    """
    if isinstance(error, SimeFinchError):
        return error

    return error_cls(
        str(error),
        details={
            "error_type": type(error).__name__,
            "original_error": str(error),
        },
    )
