"""PowerBuilder model error types.

This module re-exports the unified exception hierarchy from common.exceptions
for backward compatibility. All exceptions are now consolidated in the common module.

DEPRECATED: Import directly from common.exceptions instead.
"""

# Re-export all exceptions from common module for backward compatibility
from common.exceptions import (
    ConfigurationError,
    DecompileError,
    DecompilationError,
    Error,
    ExtractError,
    ExtractionError,
    GenerateError,
    GenerationError,
    ModelError,
    ParseError,
    ParserError,
    ParsingError,
    PowerBuilderError,
    PowerBuilderToolError,
    SimeFinchError,
    TransformError,
    TypeValidationError,
    ValidationError,
)

__all__ = [
    "SimeFinchError",
    "Error",
    "PowerBuilderError",
    "PowerBuilderToolError",
    "ParseError",
    "ModelError",
    "ValidationError",
    "TypeValidationError",
    "TransformError",
    "DecompileError",
    "ExtractError",
    "GenerateError",
    "ConfigurationError",
    "ParsingError",
    "DecompilationError",
    "ExtractionError",
    "GenerationError",
    "ParserError",
]