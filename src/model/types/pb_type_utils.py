"""Common type system utilities for PowerRebuilder.

This module provides type validation and manipulation utilities
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
