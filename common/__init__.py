"""Common utilities and shared functionality for SIME Finch.

This module contains shared components used across the project:
- Exception hierarchy
- File utilities
- Type system
- Common utilities
"""

from .exceptions import (
    ConfigurationError,
    DecompileError,
    ExtractError,
    GenerateError,
    GrammarError,
    ModelError,
    ParseError,
    PbdError,
    PowerBuilderError,
    SimeFinchError,
    TransactionError,
    TransformError,
    TypeValidationError,
    ValidationError,
)
from .types.types import (
    create_type_from_info,
    format_type_info,
    is_boolean_type,
    is_date_time_type,
    is_numeric_type,
    is_object_type,
    is_string_type,
    normalize_type_name,
    validate_simple_type,
    validate_type_compatibility,
    validate_value_type,
)

__all__ = [
    "ConfigurationError",
    "DecompileError",
    "ExtractError",
    "GenerateError",
    # Specialized exceptions
    "GrammarError",
    "ModelError",
    "ParseError",
    "PbdError",
    "PowerBuilderError",
    # Exceptions - re-export all
    "SimeFinchError",
    "TransactionError",
    "TransformError",
    "TypeValidationError",
    "ValidationError",
    "create_type_from_info",
    "format_type_info",
    "is_boolean_type",
    "is_date_time_type",
    "is_numeric_type",
    "is_object_type",
    "is_string_type",
    # Type utilities
    "normalize_type_name",
    "validate_simple_type",
    "validate_type_compatibility",
    "validate_value_type",
]
