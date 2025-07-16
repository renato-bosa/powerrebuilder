"""PowerBuilder model error types.

This module re-exports the unified exception hierarchy from src.common.exceptions
for backward compatibility. All exceptions are now consolidated in the common module.

DEPRECATED: Import directly from src.common.exceptions instead.
"""

# Re-export all exceptions from common module for backward compatibility
from src.common.exceptions import (
    ConfigurationError,
    DecompilationError,
    DecompileError,
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
    "ConfigurationError",
    "DecompilationError",
    "DecompileError",
    "Error",
    "ExtractError",
    "ExtractionError",
    "GenerateError",
    "GenerationError",
    "ModelError",
    "ParseError",
    "ParserError",
    "ParsingError",
    "PowerBuilderError",
    "PowerBuilderToolError",
    "SimeFinchError",
    "TransformError",
    "TypeValidationError",
    "ValidationError",
]
