"""Validation utilities for PowerBuilder.

This module provides common validation functions for PowerBuilder code elements,
including access control, event types, naming conventions, and more.
"""

from __future__ import annotations

from typing import Any

from .errors import ValidationError

# ─── Constants for Validation ──────────────────────────────────────────
ACCESS_MODIFIERS = {
    "public": "public", "private": "private", "protected": "protected", "global": "global", }

EVENT_TYPES = {
    "clicked": "clicked", "modified": "modified", "itemchanged": "itemchanged", "getfocus": "getfocus", "losefocus": "losefocus", "constructor": "constructor", "destructor": "destructor", "open": "open", "close": "close", }

NAMING_CONVENTIONS = {
    "function": r"^[a-z][a-zA-Z0-9_]*$", # camelCase
    "variable": r"^[a-z][a-zA-Z0-9_]*$", # camelCase
    "constant": r"^[A-Z][A-Z0-9_]*$", # UPPER_CASE
    "class": r"^[A-Z][a-zA-Z0-9_]*$", # PascalCase
}


# ─── Validation Functions ──────────────────────────────────────────────
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
        convention_type: Type of convention to use ('function', 'variable', 'constant', 'class')

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


def validate_required_fields(data: dict[str, Any], required_fields: list[str]) -> bool:



    
    


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
        if field not in data:
            return False
        value = data[field]
        if value is None:
            return False
        if isinstance(value, str | list | dict | set) and not value:
            return False
    return True


def validate_range(
    value: float, min_value: float | None = None, max_value: float | None = None, ) -> bool:



    
    


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


def validate_enum(
    value: Any, valid_values: list[Any] | set[Any] | dict[Any, Any], ) -> bool:



    
    


    """Validate that a value is one of the valid options.

    Args:
        value: Value to validate
        valid_values: List, set, or dict of valid values (for dict, keys are checked)

    Returns:
        True if value is valid

    Examples:
        >>> validate_enum("red", ["red", "green", "blue"])
        True
        >>> validate_enum("yellow", ["red", "green", "blue"])
        False
    """
    if isinstance(valid_values, dict):
        return value in valid_values
    return value in valid_values


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