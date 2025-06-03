"""Utility classes and functions for PowerBuilder model.

This module contains base classes, exceptions, and global variables.
Most functions have been moved to more specific modules like validation.py and common.py.
This module is kept for backward compatibility.
"""

from __future__ import annotations

import warnings
from dataclasses import dataclass
from typing import Any

from .errors import ParseError as ConsolidatedParseError

# Import the consolidated error classes from errors.py
from .errors import TransformError as ConsolidatedTransformError
from .errors import ValidationError as ConsolidatedValidationError

# Import type system functions
from .type_system import (
    normalize_type_name,
    validate_simple_type,
)

# Import consolidated validation functions
from .validation import (
    ACCESS_MODIFIERS as CONSOLIDATED_ACCESS_MODIFIERS,
)
from .validation import (
    EVENT_TYPES as CONSOLIDATED_EVENT_TYPES,
)
from .validation import (
    validate_access as consolidated_validate_access,
)
from .validation import (
    validate_event as consolidated_validate_event,
)


# ─── Base Classes ─────────────────────────────────────────────────────
@dataclass
class PBNode:
    """Base class for all PowerBuilder nodes."""

    start_position: int | None = None
    stop_position: int | None = None
    source_file: str | None = None

    def __eq__(self, other):
        if not isinstance(other, self.__class__):
            return False
        return self.__dict__ == other.__dict__

    def __hash__(self):
        return hash(tuple(sorted(self.__dict__.items())))


# ─── Exceptions ───────────────────────────────────────────────────────
# Deprecated Error Classes - kept for backward compatibility
class ParseError(ConsolidatedParseError):
    """Error during parsing.

    Deprecated: Use model.utils.errors.ParseError instead.
    """

    def __init__(
        self,
        message: str,
        line: int | None = None,
        column: int | None = None,
        source: str | None = None,
        details: dict[str, Any] | None = None,
    ) -> None:
        warnings.warn(
            "model.utils.utils.ParseError is deprecated. Use model.utils.errors.ParseError instead.",
            DeprecationWarning,
            stacklevel=2,
        )
        super().__init__(message, line, column, source, details)


class ValidationError(ConsolidatedValidationError):
    """Error during validation.

    Deprecated: Use model.utils.errors.ValidationError instead.
    """

    def __init__(
        self,
        message: str,
        field: str | None = None,
        value: Any | None = None,
        details: dict[str, Any] | None = None,
    ) -> None:
        warnings.warn(
            "model.utils.utils.ValidationError is deprecated. Use model.utils.errors.ValidationError instead.",
            DeprecationWarning,
            stacklevel=2,
        )
        super().__init__(message, field, value, details)


class TransformError(ConsolidatedTransformError):
    """Error during AST transformation.

    Deprecated: Use model.utils.errors.TransformError instead.
    """

    def __init__(
        self,
        message: str,
        node_type: str | None = None,
        details: dict[str, Any] | None = None,
    ) -> None:
        warnings.warn(
            "model.utils.utils.TransformError is deprecated. Use model.utils.errors.TransformError instead.",
            DeprecationWarning,
            stacklevel=2,
        )
        super().__init__(message, node_type, details)


# ─── Global Variables ──────────────────────────────────────────────────
# Deprecated constants - use the ones in type_system.py
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

# Deprecated constants - use the ones in validation.py
ACCESS_MODIFIERS = list(CONSOLIDATED_ACCESS_MODIFIERS.keys())

# Deprecated constants - use the ones in validation.py
EVENT_TYPES = list(CONSOLIDATED_EVENT_TYPES.keys())


# ─── Helper Functions ──────────────────────────────────────────────────
def normalize_type(type_name: str) -> str:
    """Normalize a type name to PowerBuilder standard.

    Deprecated: Use model.utils.type_system.normalize_type_name instead.
    """
    warnings.warn(
        "model.utils.utils.normalize_type is deprecated. Use model.utils.type_system.normalize_type_name instead.",
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
        "model.utils.utils.validate_type is deprecated. Use model.utils.type_system.validate_simple_type instead.",
        DeprecationWarning,
        stacklevel=2,
    )
    return validate_simple_type(type_info)


def validate_access(access: str) -> bool:
    """Validate an access modifier.

    Deprecated: Use model.utils.validation.validate_access instead.
    """
    warnings.warn(
        "model.utils.utils.validate_access is deprecated. Use model.utils.validation.validate_access instead.",
        DeprecationWarning,
        stacklevel=2,
    )
    return consolidated_validate_access(access)


def validate_event(event: str) -> bool:
    """Validate an event type.

    Deprecated: Use model.utils.validation.validate_event instead.
    """
    warnings.warn(
        "model.utils.utils.validate_event is deprecated. Use model.utils.validation.validate_event instead.",
        DeprecationWarning,
        stacklevel=2,
    )
    return consolidated_validate_event(event)
