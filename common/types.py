"""Common type system utilities for SIME Finch.

This module consolidates type validation and manipulation utilities
that were previously scattered across multiple modules.
"""

from __future__ import annotations

from functools import lru_cache
from typing import Any

# Import type definitions from AST module
from model.ast import (
    ArrayType,
    BasicType,
    CustomType,
    Type,
    TypeCategory,
    TypeRegistry,
)

# =============================================================================
# Type Validation and Conversion
# =============================================================================


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
        "int": "integer", "bool": "boolean", "char": "character", "str": "string", "dec": "decimal", "uint": "unsignedinteger", "ulong": "unsignedlong", "datetime": "datetime", "date": "date", "time": "time", "blob": "blob", }

    return type_map.get(normalized, normalized)


def validate_simple_type(type_name: str) -> bool:
    """Check if a type name is a valid simple type.

    Args:
        type_name: Type name to validate

    Returns:
        True if valid simple type
    """
    normalized = normalize_type_name(type_name)

    # Check against BasicType enum
    try:
        BasicType(normalized)
    except ValueError:
        return False
    else:
        return True


def is_numeric_type(type_name: str) -> bool:
    """Check if a type is numeric.

    Args:
        type_name: Type name to check

    Returns:
        True if numeric type
    """
    normalized = normalize_type_name(type_name)
    numeric_types = {
        "integer", "long", "decimal", "real", "double", "unsignedinteger", "unsignedlong", "byte", }
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
            "byte": 1, "integer": 2, "unsignedinteger": 2, "long": 3, "unsignedlong": 3, "decimal": 4, "real": 5, "double": 6, }

        source_level = numeric_hierarchy.get(source, 0)
        target_level = numeric_hierarchy.get(target, 0)

        # Can assign to same or wider type
        return source_level <= target_level

    # String compatibility
    return is_string_type(source) and is_string_type(target)


def create_type_from_info(type_info: dict[str, Any]) -> Type:
    """Create a Type object from type information dictionary.

    Args:
        type_info: Dictionary with type information

    Returns:
        Type object
    """
    type_name = type_info.get("name", "any")

    # Handle array types
    if type_info.get("is_array"):
        dimensions = type_info.get("dimensions", [])
        element_type = create_type_from_info(
            {
                "name": type_name, "is_array": False, },
        )
        return ArrayType(
            element_type=element_type, bounds=dimensions, )

    # Handle custom types
    if not validate_simple_type(type_name):
        return CustomType(
            name=type_name, module=type_info.get("module"), type_params=type_info.get("type_params", []), )

    # Simple type
    return Type(
        name=type_name, category=TypeCategory.BASIC, )


def _validate_string_value(value: object) -> tuple[bool, str | None]:
    """Validate string type value."""
    if isinstance(value, str):
        return True, None
    return False, f"Expected string, got {type(value).__name__}"


def _validate_numeric_value(value: object, normalized_type: str) -> tuple[bool, str | None]:
    """Validate numeric type value."""
    if isinstance(value, int | float):
        # Check specific numeric constraints
        if normalized_type in {"integer", "long", "unsignedinteger", "unsignedlong"}:
            if not isinstance(value, int):
                return False, f"Expected integer, got {type(value).__name__}"

            # Check unsigned constraint
            if normalized_type.startswith("unsigned") and value < 0:
                return False, f"Expected unsigned value, got {value}"

        return True, None
    return False, f"Expected numeric type, got {type(value).__name__}"


def _validate_boolean_value(value: object) -> tuple[bool, str | None]:
    """Validate boolean type value."""
    if isinstance(value, bool):
        return True, None
    return False, f"Expected boolean, got {type(value).__name__}"


def _validate_datetime_value(value: object) -> tuple[bool, str | None]:
    """Validate date/time type value."""
    # Accept strings for now (would need proper date parsing)
    if isinstance(value, str):
        return True, None
    return False, f"Expected date/time string, got {type(value).__name__}"


def _validate_object_value(value: object) -> tuple[bool, str | None]:
    """Validate object type value."""
    if isinstance(value, dict | object):
        return True, None
    return False, f"Expected object, got {type(value).__name__}"


def validate_value_type(value: object, expected_type: str) -> tuple[bool, str | None]:
    """Validate that a value matches expected type.

    Args:
        value: Value to validate
        expected_type: Expected type name

    Returns:
        Tuple of (is_valid, error_message)
    """
    normalized_type = normalize_type_name(expected_type)

    # None is valid for any type (null value)
    if value is None:
        return True, None

    # Dispatch to specific validators
    if is_string_type(normalized_type):
        return _validate_string_value(value)

    if is_numeric_type(normalized_type):
        return _validate_numeric_value(value, normalized_type)

    if is_boolean_type(normalized_type):
        return _validate_boolean_value(value)

    if is_date_time_type(normalized_type):
        return _validate_datetime_value(value)

    if is_object_type(normalized_type):
        return _validate_object_value(value)

    # Default: assume valid
    return True, None


def format_type_info(type_obj: Type | ArrayType | CustomType) -> str:
    """Format type information as a readable string.

    Args:
        type_obj: Type object to format

    Returns:
        Formatted type string
    """
    if isinstance(type_obj, ArrayType):
        base = format_type_info(type_obj.element_type)
        bounds_str = ""
        if type_obj.bounds:
            bounds = ", ".join(str(b) for b in type_obj.bounds)
            bounds_str = f"[{bounds}]"
        return f"{base}{bounds_str}"

    if isinstance(type_obj, CustomType):
        if type_obj.type_params:
            params = ", ".join(format_type_info(p) for p in type_obj.type_params)
            return f"{type_obj.name}<{params}>"
        return type_obj.name

    return type_obj.name


# =============================================================================
# Type System Configuration
# =============================================================================

# Global type registry instance
_type_registry = TypeRegistry()


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
