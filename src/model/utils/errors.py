"""PowerBuilder model error types.

This module re-exports the unified exception hierarchy from src.core.exceptions
for backward compatibility. All exceptions are now consolidated in the core module.

DEPRECATED: Import directly from src.core.exceptions instead.
"""

# Re-export all exceptions from core module for backward compatibility
from src.core.exceptions import (
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
