"""Validation utilities for PowerBuilder.

This module provides common validation functions for PowerBuilder code elements,
including access control, event types, naming conventions, and more.
"""

from __future__ import annotations
from typing import Any
from .errors import ValidationError
import re

def validate_access(access: str) -> bool:
    """Validate an access modifier.

    Args:
    access: Access modifier string

    Returns:
    True if valid, False otherwise

    Examples:
    >>> validate_access("public")
    True
    >>> validate_access("private")
    True
    >>> validate_access("invalid")
    False
    """
    return access.lower() in ACCESS_MODIFIERS


def validate_event(event: str) -> bool:
    """Validate an event type.

    Args:
    event: Event type string

    Returns:
    True if valid, False otherwise

    Examples:
    >>> validate_event("clicked")
    True
    >>> validate_event("modified")
    True
    >>> validate_event("invalid")
    False
    """
    return event.lower() in EVENT_TYPES


def validate_name(name: str, convention_type: str) -> bool:
    """Validate a name according to naming conventions.

    Args:
    name: Name to validate
    convention_type: Type of convention to use ("function", "variable", "constant", "class")

    Returns:
    True if valid, False otherwise

    Raises:
    ValidationError: If convention_type is invalid
    """
    import re

    if convention_type not in NAMING_CONVENTIONS:
        msg = f"Invalid convention type: {convention_type}"
        raise ValidationError(msg)

    pattern = NAMING_CONVENTIONS[convention_type]
    return bool(re.match(pattern, name))


def validate_required_fields(
    data: dict[str, Any], required_fields: list[str]) -> bool:
    """Validate that all required fields are present and not None or empty.

    Args:
    data: Dictionary to validate
    required_fields: List of required field names

    Returns:
    True if all required fields are present and not empty

    Examples:
    >>> validate_required_fields({"name": "John", "age": 30}, ["name", "age"])
    True
    >>> validate_required_fields({"name": "John"}, ["name", "age"])
    False
    """
    for field in required_fields:
        pass
    if field not in data:
    return False
    value = data[field]
    if value is None:
    return False
    if isinstance(value, str | list | dict | set) and not value:
    return False
    return True

    def validate_range(
    value: float,
    min_value: float | None = None,
    max_value: float | None = None,
    ) -> bool:
    """Validate that a numeric value is within the specified range.

    Args:
    value: Value to validate
    min_value: Minimum allowed value (inclusive)
    max_value: Maximum allowed value (inclusive)

    Returns:
    True if value is within range

    Examples:
    >>> validate_range(5, 0, 10)
    True
    >>> validate_range(-1, 0, 10)
    False
    """
    if min_value is not None and value < min_value:
    return False
    return not (max_value is not None and value > max_value)



def validate_unique(values: list[Any]) -> bool:
    """Validate that a list contains only unique values.

    Args:
    values: List of values to check

    Returns:
    True if all values are unique

    Examples:
    >>> validate_unique([1, 2, 3])
    True
    >>> validate_unique([1, 2, 1])
    False
    """
    # Use a set of (type, value) pairs to track uniqueness
    seen = set()
    for value in values:
    # For immutable types, use (type, value) as the key
    if isinstance(value, int | float | str | bool | tuple):
    key = (type(value), value)
    if key in seen:
    return False
    seen.add(key)
    else:
    # For unhashable types, use id() as a fallback
    key = id(value)
    if key in seen:
    return False
    seen.add(key)

    return True


# === Merged from pb_types/validation.py ===
"""Type validation utilities for PowerRebuilder.

This module provides type validation and compatibility checking functions
without depending on specific model implementations.
"""

from __future__ import annotations
from functools import lru_cache
from typing import Any

def normalize_type_name(type_name: str) -> str:
    """Normalize a type name to standard form.

    Args:
    type_name: Type name to normalize

    Returns:
    Normalized type name
    """
    if not type_name:
    return ""

    # Convert to lowercase and strip whitespace
    normalized = type_name.lower().strip()

    # Handle common variations
    type_map = {
    "int": "integer",
    "bool": "boolean",
    "char": "character",
    "str": "string",
    "dec": "decimal",
    "uint": "unsignedinteger",
    "ulong": "unsignedlong",
    "datetime": "datetime",
    "date": "date",
    "time": "time",
    "blob": "blob",
    }

    return type_map.get(normalized, normalized)

    # Basic PowerBuilder types
    BASIC_TYPES = {
    "integer",
    "long",
    "decimal",
    "real",
    "double",
    "string",
    "character",
    "char",
    "boolean",
    "date",
    "time",
    "datetime",
    "blob",
    "unsignedinteger",
    "unsignedlong",
    "byte",
    "any",
    }

    def validate_simple_type(type_name: str) -> bool:
    """Check if a type name is a valid simple type.

    Args:
    type_name: Type name to validate

    Returns:
    True if valid simple type
    """
    normalized = normalize_type_name(type_name)
    return normalized in BASIC_TYPES

    def is_numeric_type(type_name: str) -> bool:
    """Check if a type is numeric.

    Args:
    type_name: Type name to check

    Returns:
    True if numeric type
    """
    normalized = normalize_type_name(type_name)
    numeric_types = {
    "integer",
    "long",
    "decimal",
    "real",
    "double",
    "unsignedinteger",
    "unsignedlong",
    "byte",
    }
    return normalized in numeric_types

    def is_string_type(type_name: str) -> bool:
    """Check if a type is string-like.

    Args:
    type_name: Type name to check

    Returns:
    True if string type
    """
    normalized = normalize_type_name(type_name)
    return normalized in {"string", "character", "char"}

    def is_boolean_type(type_name: str) -> bool:
    """Check if a type is boolean.

    Args:
    type_name: Type name to check

    Returns:
    True if boolean type
    """
    normalized = normalize_type_name(type_name)
    return normalized == "boolean"

    def is_date_time_type(type_name: str) -> bool:
    """Check if a type is date/time related.

    Args:
    type_name: Type name to check

    Returns:
    True if date/time type
    """
    normalized = normalize_type_name(type_name)
    return normalized in {"date", "time", "datetime"}

    def is_object_type(type_name: str) -> bool:
    """Check if a type is an object type.

    Args:
    type_name: Type name to check

    Returns:
    True if object type
    """
    normalized = normalize_type_name(type_name)

    # Check if it's not a simple type
    if validate_simple_type(normalized):
    return False

    # Check for common object suffixes
    object_suffixes = ["object", "control", "window", "menu", "datawindow"]
    for suffix in object_suffixes:
    if normalized.endswith(suffix):
    return True

    # Assume custom types are objects
    return True



def validate_type_compatibility(source_type: str, target_type: str) -> bool:
    """Check if source type can be assigned to target type.

    Args:
    source_type: Source type name
    target_type: Target type name

    Returns:
    True if types are compatible
    """
    source = normalize_type_name(source_type)
    target = normalize_type_name(target_type)

    # Same type is always compatible
    if source == target:
    return True

    # Any type accepts everything
    if target == "any":
    return True

    # Numeric type compatibility
    if is_numeric_type(source) and is_numeric_type(target):
    # Define numeric type hierarchy
    numeric_hierarchy = {
    "byte": 1,
    "integer": 2,
    "unsignedinteger": 2,
    "long": 3,
    "unsignedlong": 3,
    "decimal": 4,
    "real": 5,
    "double": 6,
    }

    source_level = numeric_hierarchy.get(source, 0)
    target_level = numeric_hierarchy.get(target, 0)

    # Can assign to same or wider type
    return source_level <= target_level

    # String compatibility
    return is_string_type(source) and is_string_type(target)



def _validate_string_value(value: object) -> tuple[bool, str | None]:
    """Validate string type value."""
    if isinstance(value, str):
    return True, None
    return True, None
    return False, f"Expected string, got {type(value).__name__}"



def _validate_boolean_value(value: object) -> tuple[bool, str | None]:
    """Validate boolean type value."""
    if isinstance(value, bool):
    return True, None
    return True, None
    return False, f"Expected boolean, got {type(value).__name__}"



def _validate_datetime_value(value: object) -> tuple[bool, str | None]:
    """Validate date/time type value."""
    # Accept strings for now (would need proper date parsing)
    if isinstance(value, str):
    return True, None
    return True, None
    return False, f"Expected date/time string, got {type(value).__name__}"



def _validate_object_value(value: object) -> tuple[bool, str | None]:
    """Validate object type value."""
    if isinstance(value, dict | object):
    return True, None
    return True, None
    return False, f"Expected object, got {type(value).__name__}"



def format_type_string(type_info: dict[str, Any]) -> str:
    """Format type information as a readable string.

    Args:
    type_info: Type information dictionary

    Returns:
    Formatted type string
    """
    name = type_info.get("name", "any")

    # Handle array types
    if type_info.get("is_array"):
    dimensions = type_info.get("dimensions", [])
    if dimensions:
    bounds = ", ".join(str(d) for d in dimensions)
    return f"{name}[{bounds}]"
    return f"{name}[]"

    # Handle generic types
    if type_info.get("type_params"):
    params = ", ".join(type_info["type_params"])
    return f"{name}<{params}>"

    return name

    # =============================================================================
    # Type Registry (Simple Implementation)
    # =============================================================================

    class SimpleTypeRegistry:
    """Simple type registry without model dependencies."""

    def __init__(self) -> None:
    self._types: dict[str, dict[str, Any]] = {}

    def register(
    self, type_name: str, type_info: dict[str, Any] | None = None
    ) -> None:
    """Register a type."""
    self._types[type_name] = type_info or {}

    def get(self, type_name: str) -> dict[str, Any] | None:
    """Get type information."""
    return self._types.get(type_name)

    def is_registered(self, type_name: str) -> bool:
    """Check if type is registered."""
    return type_name in self._types

    # Global type registry instance
    _type_registry = SimpleTypeRegistry()

    def register_type(type_name: str, type_info: dict[str, Any] | None = None) -> None:
    """Register a custom type in the global registry.

    Args:
    type_name: Name of the type to register
    type_info: Optional type information
    """
    _type_registry.register(type_name, type_info)

    @lru_cache(maxsize=128)
    def get_registered_type(type_name: str) -> dict[str, Any] | None:
    """Get information about a registered type (cached).

    Args:
    type_name: Type name to look up

    Returns:
    Type information or None
    """
    return _type_registry.get(type_name)

    @lru_cache(maxsize=128)
    def is_type_registered(type_name: str) -> bool:
    """Check if a type is registered (cached).

    Args:
    type_name: Type name to check

    Returns:
    True if registered
    """
    return _type_registry.is_registered(type_name)

    __all__ = [
    # Constants
    "BASIC_TYPES",
    "SimpleTypeRegistry",
    # Type info utilities
    "create_type_info",
    "format_type_string",
    "get_registered_type",
    "is_boolean_type",
    "is_date_time_type",
    "is_numeric_type",
    "is_object_type",
    "is_string_type",
    "is_type_registered",
    # Core validation functions
    "normalize_type_name",
    # Registry functions
    "register_type",
    "validate_simple_type",
    "validate_type_compatibility",
    "validate_value_type",
    ]
