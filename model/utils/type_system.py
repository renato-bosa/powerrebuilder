"""Type system for PowerBuilder.

This module provides a unified type system for PowerBuilder, including:
- Type validation
- Type conversion
- Type compatibility checks
- Type registry
"""

from __future__ import annotations

from typing import Any

from ..ast.types import (
    ArrayType,
    BasicType,
    CustomType,
    Type,
    TypeBounds,
    TypeCategory,
    TypeRegistry,
)
from .errors import TypeValidationError

# Basic types dictionary
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


def normalize_type_name(type_name: str) -> str:
    """Normalize a type name to PowerBuilder standard.

    Args:
        type_name: Raw type name

    Returns:
        Normalized type name

    Examples:
        >>> normalize_type_name('int')
        'integer'
        >>> normalize_type_name('str')
        'string'
        >>> normalize_type_name('MyType')
        'MyType'
    """
    return BASIC_TYPES.get(type_name.lower(), type_name)


def validate_simple_type(type_info: dict[str, Any]) -> bool:
    """Validate simple type information.

    Args:
        type_info: Type information dictionary

    Returns:
        True if type information is valid

    Raises:
        TypeValidationError: If type information is invalid

    Examples:
        >>> validate_simple_type({'name': 'integer', 'is_array': False, 'array_bounds': None})
        True
        >>> validate_simple_type({'name': 'string', 'is_array': True, 'array_bounds': [10]})
        True
    """
    try:
        if not isinstance(type_info.get("name"), str):
            raise TypeValidationError(
                "Invalid type name",
                type_name=str(type_info.get("name")),
            )

        # Validate array bounds first
        bounds = type_info.get("array_bounds")
        if bounds is not None:
            if not isinstance(bounds, list):
                raise TypeValidationError(
                    "Invalid array bounds",
                    type_name=type_info.get("name"),
                )
            if not all(isinstance(b, int) and b > 0 for b in bounds):
                raise TypeValidationError(
                    "Array bounds must be positive integers",
                    type_name=type_info.get("name"),
                )

        # Only check is_array if explicitly provided
        if "is_array" in type_info and not isinstance(type_info["is_array"], bool):
            raise TypeValidationError(
                "Invalid is_array value",
                type_name=type_info.get("name"),
            )

        return True
    except (KeyError, AttributeError) as e:
        raise TypeValidationError(
            f"Invalid type information: {e}",
            type_name=type_info.get("name"),
        ) from e


def validate_type_compatibility(source_type: Type, target_type: Type) -> bool:
    """Check if source_type is compatible with target_type.

    Args:
        source_type: Source type
        target_type: Target type

    Returns:
        True if source_type can be assigned to target_type
    """
    # Exact same type
    if (
        source_type.name == target_type.name
        and source_type.is_array == target_type.is_array
    ):
        return True

    # ANY type can accept any value
    if target_type.name == "ANY":
        return True

    # Numeric type conversions
    if (
        source_type.category == TypeCategory.NUMERIC
        and target_type.category == TypeCategory.NUMERIC
    ):
        return True

    # Array compatibility
    if source_type.is_array and target_type.is_array:
        if hasattr(source_type, "element_type") and hasattr(
            target_type,
            "element_type",
        ):
            return validate_type_compatibility(
                source_type.element_type,
                target_type.element_type,
            )

    # Custom type compatibility
    if isinstance(source_type, CustomType) and isinstance(target_type, CustomType):
        # Check if source_type inherits from target_type
        current = source_type
        while current:
            if current.name == target_type.name:
                return True
            current = current.parent_type

    return False


def validate_value_type(value: Any, expected_type: Type) -> bool:
    """Check if a value matches an expected type.

    Args:
        value: Value to check
        expected_type: Expected type

    Returns:
        True if value matches expected_type
    """
    # Check for None
    if value is None:
        return False

    # Check for arrays
    if expected_type.is_array:
        if not isinstance(value, list | tuple):
            return False

        # Check array bounds
        if expected_type.array_bounds:
            for bound in expected_type.array_bounds:
                if not bound.validate():
                    return False

        # Check array elements
        if isinstance(expected_type, ArrayType):
            for elem in value:
                if not validate_value_type(elem, expected_type.element_type):
                    return False

        return True

    # Basic type validation
    if expected_type.category == TypeCategory.NUMERIC:
        return isinstance(value, int | float)
    if expected_type.category == TypeCategory.TEXT:
        return isinstance(value, str)
    if expected_type.category == TypeCategory.LOGICAL:
        return isinstance(value, bool)
    if expected_type.name == "DATE":
        # Date validation would be more complex
        return True
    if expected_type.name == "TIME":
        # Time validation would be more complex
        return True

    # Custom type validation
    if isinstance(expected_type, CustomType):
        if not isinstance(value, dict):
            return False

        if not expected_type.fields:
            return True

        for field_name, field_type in expected_type.fields.items():
            if field_name not in value:
                return False
            if not validate_value_type(value[field_name], field_type):
                return False

        return True

    # Default case
    return True


def create_type_from_info(
    type_info: dict[str, Any],
    registry: TypeRegistry,
) -> Type | None:
    """Create a Type object from type information.

    Args:
        type_info: Type information dictionary
        registry: Type registry

    Returns:
        Type object or None if invalid
    """
    validate_simple_type(type_info)

    name = type_info["name"]

    # Try to get existing type
    existing_type = registry.get_type(name)
    if existing_type:
        # Handle array types
        if type_info.get("is_array"):
            bounds = []
            if type_info.get("array_bounds"):
                for bound in type_info["array_bounds"]:
                    bounds.append(TypeBounds(1, bound))
            return registry.create_array_type(name, bounds)
        return existing_type

    # Create new type based on category
    category = TypeCategory.CUSTOM  # Default
    for basic_type in BasicType:
        if basic_type.type_name.lower() == name.lower():
            category = basic_type.category
            break

    # Create new type
    new_type = Type(name=name, category=category)

    # Handle array types
    if type_info.get("is_array"):
        bounds = []
        if type_info.get("array_bounds"):
            for bound in type_info["array_bounds"]:
                bounds.append(TypeBounds(1, bound))
        return ArrayType(
            name=f"ARRAY OF {name}",
            category=TypeCategory.COMPOSITE,
            bounds=bounds,
            element_type=new_type,
        )

    return new_type


def format_type_info(type_info: dict[str, Any]) -> str:
    """Format type information as a string.

    Args:
        type_info: Type information dictionary

    Returns:
        Formatted type string
    """
    validate_simple_type(type_info)
    type_str = normalize_type_name(type_info["name"])

    if type_info.get("is_array"):
        bounds = type_info.get("array_bounds")
        if bounds:
            bounds_str = ",".join(str(b) for b in bounds)
            type_str += f"[{bounds_str}]"
        else:
            type_str += "[]"

    return type_str
