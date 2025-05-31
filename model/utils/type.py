"""Type validation and normalization functions.

This module provides utilities for working with PowerBuilder types.

Deprecated: Use model.utils.type_system instead.
"""
from __future__ import annotations

import warnings
from typing import Any

from .type_system import normalize_type_name, validate_simple_type

# Basic types dictionary for backward compatibility
BASIC_TYPES = {
    "int": "integer",
    "str": "string",
    "bool": "boolean",
    "date": "date",
    "time": "time",
    "dec": "decimal",
    "real": "real",
    "char": "character",
    "blob": "blob",
    "any": "any",
}


def normalize_type(type_name: str) -> str:
    """Normalize a type name to PowerBuilder standard.

    Deprecated: Use model.utils.type_system.normalize_type_name instead.

    Args:
        type_name: Raw type name

    Returns:
        Normalized type name
    """
    warnings.warn(
        "model.utils.type.normalize_type is deprecated. Use model.utils.type_system.normalize_type_name instead.",
        DeprecationWarning,
        stacklevel=2,
    )
    return normalize_type_name(type_name)


def validate_type(type_info: dict[str, Any]) -> bool:
    """Validate type information.

    Deprecated: Use model.utils.type_system.validate_simple_type instead.

    Args:
        type_info: Type information dictionary

    Returns:
        True if type information is valid

    Raises:
        TypeValidationError: If type information is invalid
    """
    warnings.warn(
        "model.utils.type.validate_type is deprecated. Use model.utils.type_system.validate_simple_type instead.",
        DeprecationWarning,
        stacklevel=2,
    )
    return validate_simple_type(type_info)
