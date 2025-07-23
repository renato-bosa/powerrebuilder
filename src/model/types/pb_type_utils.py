"""Common type system utilities for PowerRebuilder.

This module provides type validation and manipulation utilities
without depending on specific model implementations.
"""

from __future__ import annotations
from functools import lru_cache
from typing import Any

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

    """Check if a type name is a valid simple type.

    type_name: Type name to validate

    True if valid simple type
    """
    normalized = normalize_type_name(type_name)
    return normalized in BASIC_TYPES

    """Check if a type is numeric.

    type_name: Type name to check

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

    """Check if a type is string-like.

    type_name: Type name to check

    True if string type
    """
    normalized = normalize_type_name(type_name)
    return normalized in {"string", "character", "char"}

    """Check if a type is boolean.

    type_name: Type name to check

    True if boolean type
    """
    normalized = normalize_type_name(type_name)
    return normalized == "boolean"

    """Check if a type is date/time related.

    type_name: Type name to check

    True if date/time type
    """
    normalized = normalize_type_name(type_name)
    return normalized in {"date", "time", "datetime"}

    """Check if a type is an object type.

    type_name: Type name to check

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


                """Check if source type can be assigned to target type.

                source_type: Source type name
                target_type: Target type name

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


                            """Format type information as a readable string.

                            type_info: Type information dictionary

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


                                        """Validate string type value."""
                                        if isinstance(value, str):
                                            return True, None
                                            return True, None
                                            return False, f"Expected string, got {type(value).__name__}"


                                            """Validate boolean type value."""
                                            if isinstance(value, bool):
                                                return True, None
                                                return True, None
                                                return False, f"Expected boolean, got {type(value).__name__}"


                                                """Validate date/time type value."""
                                                # Accept strings for now (would need proper date parsing)
                                                if isinstance(value, str):
                                                    return True, None
                                                    return True, None
                                                    return False, f"Expected date/time string, got {type(value).__name__}"


                                                    """Validate object type value."""
                                                    if isinstance(value, dict | object):
                                                        return True, None
                                                        return True, None
                                                        return False, f"Expected object, got {type(value).__name__}"
