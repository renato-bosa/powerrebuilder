"""Common utilities and shared functionality for SIME Finch.

This module contains shared components used across the project:
- Exception hierarchy
- File utilities
- Type system
- Common utilities
"""

from .exceptions import *
from .types import *

__all__ = [
    # Exceptions - re-export all
    "SimeFinchError",
    "PowerBuilderError",
    "ParseError",
    "ModelError",
    "ValidationError",
    "TypeValidationError",
    "TransformError",
    "DecompileError",
    "ExtractError",
    "GenerateError",
    "ConfigurationError",
    # Specialized exceptions
    "GrammarError",
    "PbdError",
    "TransactionError",
    # Type utilities
    "normalize_type_name",
    "validate_simple_type",
    "is_numeric_type",
    "is_string_type",
    "is_boolean_type",
    "is_date_time_type",
    "is_object_type",
    "validate_type_compatibility",
    "create_type_from_info",
    "validate_value_type",
    "format_type_info",
]