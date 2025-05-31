"""Array-related AST nodes for PowerBuilder and Pseudocode.

This module contains AST nodes for representing array operations, including:
- Array declarations
- Array access
- Array modification
- Bounds checking
- Multi-dimensional array support
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from ..utils.base import PBNode
from .types import ArrayType, Type, TypeBounds


@dataclass
class ArrayDeclaration(PBNode):
    """Array declaration node."""

    name: str
    element_type: Type
    bounds: list[TypeBounds]
    initial_value: list[Any] | None = None

    def validate(self) -> bool:
        """Validate array declaration."""
        # Check bounds are valid
        for bound in self.bounds:
            if not bound.validate():
                return False

        # If initial value provided, validate it
        if self.initial_value is not None:
            array_type = ArrayType(
                name=f"ARRAY OF {self.element_type.name}",
                category=self.element_type.category,
                element_type=self.element_type,
                bounds=self.bounds,
            )
            if not array_type.validate_value(self.initial_value):
                return False

        return True


@dataclass
class ArrayAccess(PBNode):
    """Array access node."""

    array_name: str
    indices: list[int | str]  # Can be variable names
    array_type: ArrayType | None = None  # Set during type checking

    def validate(self) -> bool:
        """Validate array access."""
        if not self.array_type:
            return False  # Must have type information

        # Check number of dimensions matches
        if len(self.indices) != len(self.array_type.bounds):
            return False

        # Validate bounds if indices are numeric
        return self.array_type.validate_bounds(self.indices)


@dataclass
class ArrayAssignment(PBNode):
    """Array element assignment node."""

    access: ArrayAccess
    value: Any

    def validate(self) -> bool:
        """Validate array assignment."""
        if not self.access.validate():
            return False

        # Check value type matches element type
        return self.access.array_type.element_type.validate_value(self.value)


@dataclass
class ArraySlice(PBNode):
    """Array slice operation node."""

    array_name: str
    start_indices: list[int | str]
    end_indices: list[int | str]
    array_type: ArrayType | None = None

    def validate(self) -> bool:
        """Validate array slice operation."""
        if not self.array_type:
            return False

        if len(self.start_indices) != len(self.end_indices):
            return False

        if len(self.start_indices) > len(self.array_type.bounds):
            return False

        # Validate each dimension's bounds
        for start, end, bound in zip(
            self.start_indices, self.end_indices, self.array_type.bounds, strict=False,
        ):
            if isinstance(start, int) and isinstance(end, int):
                if start > end:
                    return False
                if isinstance(bound.lower, int) and start < bound.lower:
                    return False
                if isinstance(bound.upper, int) and end > bound.upper:
                    return False

        return True


@dataclass
class ArrayOperation(PBNode):
    """Array operation node for common array functions."""

    class Operation:
        LENGTH = "LENGTH"
        COPY = "COPY"
        CONCAT = "CONCAT"
        RESIZE = "RESIZE"

    array_name: str
    operation: str
    parameters: list[Any] = None
    array_type: ArrayType | None = None

    def validate(self) -> bool:
        """Validate array operation."""
        if not self.array_type:
            return False

        if self.operation == self.Operation.LENGTH:
            return len(self.parameters or []) == 0

        if self.operation == self.Operation.COPY:
            return len(self.parameters or []) == 0

        if self.operation == self.Operation.CONCAT:
            if not self.parameters or len(self.parameters) != 1:
                return False
            # Check if parameter is compatible array
            other_array = self.parameters[0]
            if not isinstance(other_array, ArrayType):
                return False
            return self.array_type.element_type.can_assign_from(
                other_array.element_type,
            )

        if self.operation == self.Operation.RESIZE:
            if not self.parameters or len(self.parameters) != len(
                self.array_type.bounds,
            ):
                return False
            # Each parameter should be a new size
            return all(isinstance(param, int | str) for param in self.parameters)

        return False  # Unknown operation
