"""Type-related AST nodes for PowerBuilder and Pseudocode.

This module contains AST nodes for representing types in both PowerBuilder and pseudocode.
Includes basic types (INTEGER, REAL, etc.) and complex types (arrays, custom types).

Note: For type validation and compatibility checks, prefer using the unified
type_system module in model.utils.type_system.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum, auto
from typing import Any

from ..utils.base import PBNode


class TypeCategory(Enum):
    """Categories of types."""

    NUMERIC = auto()
    TEXT = auto()
    LOGICAL = auto()
    COMPOSITE = auto()
    CUSTOM = auto()


class BasicType(Enum):
    """Basic type enumeration."""

    INTEGER = ("INTEGER", TypeCategory.NUMERIC)
    REAL = ("REAL", TypeCategory.NUMERIC)
    CHAR = ("CHAR", TypeCategory.TEXT)
    STRING = ("STRING", TypeCategory.TEXT)
    BOOLEAN = ("BOOLEAN", TypeCategory.LOGICAL)
    DATE = ("DATE", TypeCategory.COMPOSITE)
    TIME = ("TIME", TypeCategory.COMPOSITE)
    DECIMAL = ("DECIMAL", TypeCategory.NUMERIC)
    LONG = ("LONG", TypeCategory.NUMERIC)
    BLOB = ("BLOB", TypeCategory.COMPOSITE)
    ANY = ("ANY", TypeCategory.COMPOSITE)

    def __init__(self, name: str, category: TypeCategory) -> None:
        self.type_name = name
        self.category = category


@dataclass
class TypeBounds:
    """Array bounds or type constraints."""

    lower: int | str  # Can be variable name
    upper: int | str
    dimensions: list[TypeBounds] = None  # For multi-dimensional arrays

    def validate(self) -> bool:
        """Validate bounds are valid."""
        if isinstance(self.lower, int) and isinstance(self.upper, int):
            return self.lower <= self.upper
        return True  # Can't validate at compile time if variables

    @property
    def size(self) -> int | None:
        """Calculate size if bounds are numeric."""
        if isinstance(self.lower, int) and isinstance(self.upper, int):
            return self.upper - self.lower + 1
        return None


@dataclass
class Type(PBNode):
    """Base type reference.

    Note: For type validation and compatibility checks, prefer using the unified
    type_system module in model.utils.type_system.
    """

    name: str
    category: TypeCategory
    is_array: bool = False
    array_bounds: list[TypeBounds] | None = None
    constraints: dict[str, Any] | None = None

    def validate_value(self, value: Any) -> bool:
        """Validate a value matches this type.

        Note: Consider using model.utils.type_system.validate_value_type instead.
        """
        if self.is_array:
            if not isinstance(value, list | tuple):
                return False
            if self.array_bounds:
                for bound in self.array_bounds:
                    if not bound.validate():
                        return False
        return True

    def can_assign_from(self, other: Type) -> bool:
        """Check if this type can accept values of another type.

        Note: Consider using model.utils.type_system.validate_type_compatibility instead.
        """
        if self.name == other.name:
            return True
        if (
            self.category == TypeCategory.NUMERIC
            and other.category == TypeCategory.NUMERIC
        ):
            # Allow numeric type conversions
            return True
        return self.name == "ANY"


class ArrayType(Type):
    """Array type with bounds checking.

    Note: For array type validation and compatibility checks, prefer using the unified
    type_system module in model.utils.type_system.
    """

    def __init__(
        self,
        name: str,
        category: TypeCategory,
        bounds: list[TypeBounds],
        element_type: Type,
        is_array: bool = True,
        array_bounds: list[TypeBounds] | None = None,
        constraints: dict[str, Any] | None = None,
    ) -> None:
        super().__init__(
            name=name,
            category=category,
            is_array=True,
            array_bounds=bounds,
            constraints=constraints,
        )
        self.bounds = bounds
        self.element_type = element_type

    def validate_value(self, value: Any) -> bool:
        """Validate a value matches this array type.

        Note: Consider using model.utils.type_system.validate_value_type instead.
        """
        if not super().validate_value(value):
            return False
        # Check each element matches element_type
        return all(self.element_type.validate_value(elem) for elem in value)

    def validate_bounds(self, indices: list[int | str]) -> bool:
        """Validate array access indices."""
        if len(indices) != len(self.bounds):
            return False
        for idx, bound in zip(indices, self.bounds, strict=False):
            if isinstance(idx, int):
                if isinstance(bound.lower, int) and idx < bound.lower:
                    return False
                if isinstance(bound.upper, int) and idx > bound.upper:
                    return False
        return True


class CustomType(Type):
    """User-defined type.

    Note: For custom type validation and compatibility checks, prefer using the unified
    type_system module in model.utils.type_system.
    """

    def __init__(
        self,
        name: str,
        category: TypeCategory,
        namespace: str | None = None,
        fields: dict[str, Type] | None = None,
        parent_type: CustomType | None = None,
        is_array: bool = False,
        array_bounds: list[TypeBounds] | None = None,
        constraints: dict[str, Any] | None = None,
    ) -> None:
        super().__init__(
            name=name,
            category=category,
            is_array=is_array,
            array_bounds=array_bounds,
            constraints=constraints,
        )
        self.namespace = namespace
        self.fields = fields
        self.parent_type = parent_type
        self.category = TypeCategory.CUSTOM

    def validate_value(self, value: Any) -> bool:
        """Validate a value matches this custom type.

        Note: Consider using model.utils.type_system.validate_value_type instead.
        """
        if not isinstance(value, dict):
            return False
        if not self.fields:
            return True
        for field_name, field_type in self.fields.items():
            if field_name not in value:
                return False
            if not field_type.validate_value(value[field_name]):
                return False
        return True

    def get_field_type(self, field_name: str) -> Type | None:
        """Get type of a field, checking parent types if needed."""
        if self.fields and field_name in self.fields:
            return self.fields[field_name]
        if self.parent_type:
            return self.parent_type.get_field_type(field_name)
        return None


class TypeRegistry:
    """Registry of available types."""

    def __init__(
        self,
        basic_types: dict[str, Type] = None,
        custom_types: dict[str, CustomType] = None,
    ) -> None:
        self.basic_types = {} if basic_types is None else basic_types
        self.custom_types = {} if custom_types is None else custom_types

        # Register all basic types if we're starting with an empty registry
        if not self.basic_types:
            for basic_type in BasicType:
                self.basic_types[basic_type.type_name] = Type(
                    name=basic_type.type_name,
                    category=basic_type.category,
                )

    def get_type(self, type_name: str) -> Type | None:
        """Get a type by name."""
        if type_name in self.basic_types:
            return self.basic_types[type_name]
        if type_name in self.custom_types:
            return self.custom_types[type_name]
        return None

    def register_custom_type(self, type_def: CustomType) -> None:
        """Register a new custom type."""
        self.custom_types[type_def.name] = type_def

    def create_array_type(
        self,
        element_type_name: str,
        bounds: list[TypeBounds],
    ) -> ArrayType | None:
        """Create an array type with given element type and bounds."""
        element_type = self.get_type(element_type_name)
        if not element_type:
            return None
        return ArrayType(
            name=f"ARRAY OF {element_type_name}",
            category=TypeCategory.COMPOSITE,
            bounds=bounds,
            element_type=element_type,
        )
