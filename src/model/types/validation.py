"""Validation utilities for PowerBuilder.

This module provides common validation functions for PowerBuilder code elements,
including access control, event types, naming conventions, and more.
"""

from __future__ import annotations
from typing import Any
from .errors import ValidationError
import re

# Valid access modifiers in PowerBuilder
VALID_ACCESS_MODIFIERS = {
    "public",
    "private",
    "protected",
    "global",
    "local",
}

# Naming conventions
NAMING_CONVENTIONS = {
    "variable": r"^[a-z_][a-z0-9_]*$",
    "function": r"^[a-z_][a-z0-9_]*$",
    "class": r"^[A-Z][a-zA-Z0-9_]*$",
    "constant": r"^[A-Z][A-Z0-9_]*$",
}


def validate_access(access: str) -> bool:
    """Validate an access modifier.
    
    access: Access modifier string
    
    True if valid, False otherwise
    
    >>> validate_access("public")
    True
    >>> validate_access("private")
    True
    >>> validate_access("invalid")
    False
    """
    return access.lower() in VALID_ACCESS_MODIFIERS


def validate_naming_convention(name: str, convention_type: str) -> bool:
    """Validate a name against PowerBuilder naming conventions.
    
    name: Name to validate
    convention_type: Type of naming convention ('variable', 'function', 'class', 'constant')
    
    True if name follows convention
    
    >>> validate_naming_convention("myVariable", "variable")
    True
    >>> validate_naming_convention("MyClass", "class")
    True
    >>> validate_naming_convention("MY_CONSTANT", "constant")
    True
    """
    if convention_type not in NAMING_CONVENTIONS:
        msg = f"Invalid convention type: {convention_type}"
        raise ValidationError(msg)
    
    pattern = NAMING_CONVENTIONS[convention_type]
    return bool(re.match(pattern, name))


def validate_required_fields(
    data: dict[str, Any], required_fields: list[str]
) -> bool:
    """Validate that all required fields are present and not None or empty.
    
    data: Dictionary to validate
    required_fields: List of required field names
    
    True if all required fields are present and not empty
    
    >>> validate_required_fields({"name": "John", "age": 30}, ["name", "age"])
    True
    >>> validate_required_fields({"name": "John"}, ["name", "age"])
    False
    """
    for field in required_fields:
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
    
    value: Value to validate
    min_value: Minimum allowed value (inclusive)
    max_value: Maximum allowed value (inclusive)
    
    True if value is within range
    
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
    
    values: List of values to check
    
    True if all values are unique
    
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


def normalize_type_name(type_name: str) -> str:
    """Normalize a type name to standard form.
    
    type_name: Type name to normalize
    
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
    }
    
    return type_map.get(normalized, normalized)