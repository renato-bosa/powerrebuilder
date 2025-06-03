"""Custom exceptions and error handling for the sime-finch project.

This module provides backward compatibility for the error hierarchy.
New code should import from model.utils.errors directly.
"""

import warnings
from typing import Any

from model.utils.errors import (
    DecompileError as ConsolidatedDecompileError,
)
from model.utils.errors import (
    Error as ConsolidatedError,
)
from model.utils.errors import (
    ExtractError as ConsolidatedExtractError,
)
from model.utils.errors import (
    GenerateError as ConsolidatedGenerateError,
)
from model.utils.errors import (
    ModelError as ConsolidatedModelError,
)
from model.utils.errors import (
    ParseError as ConsolidatedParseError,
)
from model.utils.errors import (
    PowerBuilderError as ConsolidatedPowerBuilderError,
)
from model.utils.errors import (
    PowerBuilderToolError as ConsolidatedPowerBuilderToolError,
)
from model.utils.errors import (
    SimeFinchError as ConsolidatedSimeFinchError,
)
from model.utils.errors import (
    TransformError as ConsolidatedTransformError,
)
from model.utils.errors import (
    TypeValidationError as ConsolidatedTypeValidationError,
)
from model.utils.errors import (
    ValidationError as ConsolidatedValidationError,
)
from model.utils.errors import (
    handle_error as consolidated_handle_error,
)


class SimeFinchError(ConsolidatedSimeFinchError):
    """Base exception for all sime-finch errors.

    Deprecated: Use model.utils.errors.SimeFinchError instead.
    """

    def __init__(self, message: str, details: dict[str, Any] | None = None) -> None:
        """Initialize the error with a message and optional details.

        Args:
            message: The error message
            details: Optional dictionary with additional error context
        """
        warnings.warn(
            "parse.errors.SimeFinchError is deprecated. Use model.utils.errors.SimeFinchError instead.",
            DeprecationWarning,
            stacklevel=2,
        )
        super().__init__(message, details)


class Error(ConsolidatedError):
    """Base error class for all sime-finch errors.

    Deprecated: Use model.utils.errors.Error instead.
    """

    def __init__(self, message: str, details: dict[str, Any] | None = None) -> None:
        warnings.warn(
            "parse.errors.Error is deprecated. Use model.utils.errors.Error instead.",
            DeprecationWarning,
            stacklevel=2,
        )
        super().__init__(message, details)


class PowerBuilderError(ConsolidatedPowerBuilderError):
    """Base class for PowerBuilder-specific errors.

    Deprecated: Use model.utils.errors.PowerBuilderError instead.
    """

    def __init__(self, message: str, details: dict[str, Any] | None = None) -> None:
        warnings.warn(
            "parse.errors.PowerBuilderError is deprecated. Use model.utils.errors.PowerBuilderError instead.",
            DeprecationWarning,
            stacklevel=2,
        )
        super().__init__(message, details)


class PowerBuilderToolError(ConsolidatedPowerBuilderToolError):
    """Base error class for high-level PowerBuilder tool errors.

    Deprecated: Use model.utils.errors.PowerBuilderToolError instead.
    """

    def __init__(
        self,
        message: str,
        component: str | None = None,
        details: dict[str, Any] | None = None,
    ) -> None:
        warnings.warn(
            "parse.errors.PowerBuilderToolError is deprecated. Use model.utils.errors.PowerBuilderToolError instead.",
            DeprecationWarning,
            stacklevel=2,
        )
        super().__init__(message, component, details)


class ParserError(ConsolidatedParseError):
    """Raised when there is an error parsing PowerBuilder code.

    Deprecated: Use model.utils.errors.ParseError instead.
    """

    def __init__(self, message: str, **kwargs) -> None:
        warnings.warn(
            "parse.errors.ParserError is deprecated. Use model.utils.errors.ParseError instead.",
            DeprecationWarning,
            stacklevel=2,
        )
        super().__init__(message, **kwargs)


class ParseError(ConsolidatedParseError):
    """Alias for ParserError for backward compatibility.

    Deprecated: Use model.utils.errors.ParseError instead.
    """

    def __init__(self, message: str, **kwargs) -> None:
        warnings.warn(
            "parse.errors.ParseError is deprecated. Use model.utils.errors.ParseError instead.",
            DeprecationWarning,
            stacklevel=2,
        )
        super().__init__(message, **kwargs)


class ValidationError(ConsolidatedValidationError):
    """Raised when there is a validation error.

    Deprecated: Use model.utils.errors.ValidationError instead.
    """

    def __init__(self, message: str, **kwargs) -> None:
        warnings.warn(
            "parse.errors.ValidationError is deprecated. Use model.utils.errors.ValidationError instead.",
            DeprecationWarning,
            stacklevel=2,
        )
        super().__init__(message, **kwargs)


class TypeValidationError(ConsolidatedTypeValidationError):
    """Raised when there is an error validating a type.

    Deprecated: Use model.utils.errors.TypeValidationError instead.
    """

    def __init__(self, message: str, **kwargs) -> None:
        warnings.warn(
            "parse.errors.TypeValidationError is deprecated. Use model.utils.errors.TypeValidationError instead.",
            DeprecationWarning,
            stacklevel=2,
        )
        super().__init__(message, **kwargs)


class ModelError(ConsolidatedModelError):
    """Raised when there is an error in the model operations.

    Deprecated: Use model.utils.errors.ModelError instead.
    """

    def __init__(self, message: str, **kwargs) -> None:
        warnings.warn(
            "parse.errors.ModelError is deprecated. Use model.utils.errors.ModelError instead.",
            DeprecationWarning,
            stacklevel=2,
        )
        super().__init__(message, **kwargs)


class TransformError(ConsolidatedTransformError):
    """Raised when there is an error during transformation.

    Deprecated: Use model.utils.errors.TransformError instead.
    """

    def __init__(self, message: str, **kwargs) -> None:
        warnings.warn(
            "parse.errors.TransformError is deprecated. Use model.utils.errors.TransformError instead.",
            DeprecationWarning,
            stacklevel=2,
        )
        super().__init__(message, **kwargs)


class DecompileError(ConsolidatedDecompileError):
    """Raised when there is an error during decompilation.

    Deprecated: Use model.utils.errors.DecompileError instead.
    """

    def __init__(self, message: str, **kwargs) -> None:
        warnings.warn(
            "parse.errors.DecompileError is deprecated. Use model.utils.errors.DecompileError instead.",
            DeprecationWarning,
            stacklevel=2,
        )
        super().__init__(message, **kwargs)


class ExtractError(ConsolidatedExtractError):
    """Raised when there is an error during extraction.

    Deprecated: Use model.utils.errors.ExtractError instead.
    """

    def __init__(self, message: str, **kwargs) -> None:
        warnings.warn(
            "parse.errors.ExtractError is deprecated. Use model.utils.errors.ExtractError instead.",
            DeprecationWarning,
            stacklevel=2,
        )
        super().__init__(message, **kwargs)


class GenerateError(ConsolidatedGenerateError):
    """Raised when there is an error during code generation.

    Deprecated: Use model.utils.errors.GenerateError instead.
    """

    def __init__(self, message: str, **kwargs) -> None:
        warnings.warn(
            "parse.errors.GenerateError is deprecated. Use model.utils.errors.GenerateError instead.",
            DeprecationWarning,
            stacklevel=2,
        )
        super().__init__(message, **kwargs)


def handle_error(
    error: Exception, error_cls: type[SimeFinchError] = SimeFinchError
) -> SimeFinchError:
    """Convert any exception to a SimeFinchError with proper context.

    Deprecated: Use model.utils.errors.handle_error instead.

    Args:
        error: The original exception
        error_cls: The specific SimeFinchError subclass to use

    Returns:
        A SimeFinchError instance with the original error details
    """
    warnings.warn(
        "parse.errors.handle_error is deprecated. Use model.utils.errors.handle_error instead.",
        DeprecationWarning,
        stacklevel=2,
    )
    return consolidated_handle_error(error, error_cls)
