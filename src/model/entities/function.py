"""PowerBuilder function, argument, and variable entities.

This module consolidates function-related entities from pb_function.py,
pb_argument.py, and pb_variable.py.
"""

from __future__ import annotations
from dataclasses import dataclass, field
from typing import Any
from src.model.types.base import PBNode

class PBArgumentNode(PBNode):
    """Represents a function/event argument."""

    name: str
    type: str
    is_reference: bool = False
    is_readonly: bool = False
    default_value: Any | None = None


class PBArgumentOptionNode(PBNode):
    """Represents argument passing options."""

    by_reference: bool = False
    readonly: bool = False


class PBArgumentsNode(PBNode):
    """Container for multiple arguments."""

    arguments: list[PBArgumentNode] = field(default_factory=list)

    def add_argument(self, arg: PBArgumentNode) -> None:
        """Add an argument to the collection."""
        self.arguments.append(arg)

    def get_argument(self, name: str) -> PBArgumentNode | None:
        """Get an argument by name."""
        for arg in self.arguments:
            if arg.name == name:
                return arg
        return None


# Alias for backward compatibility
PBFunctionArgumentNode = PBArgumentNode

# Function-related Classes

class PBFunction(PBNode):
    """Represents a PowerBuilder function."""

    name: str
    return_type: str | None = None
    arguments: PBArgumentsNode = field(default_factory=PBArgumentsNode)
    visibility: str = "public"
    access_level: str = "public"  # Alias for visibility
    is_static: bool = False
    is_override: bool = False
    body: Any | None = None  # Function body (statements)

    def __post_init__(self):
        """Sync visibility and access_level."""
        if self.visibility != "public" and self.access_level == "public":
            self.access_level = self.visibility
        elif self.access_level != "public" and self.visibility == "public":
            self.visibility = self.access_level


class PBFunctionDeclaration(PBNode):
    """Function declaration (forward declaration)."""

    name: str
    return_type: str | None = None
    arguments: PBArgumentsNode = field(default_factory=PBArgumentsNode)
    visibility: str = "public"
    is_external: bool = False
    library_name: str | None = None  # For external functions
    alias: str | None = None  # For external functions

class PBFunctionCall(PBNode):
    """Function call."""

    function_name: str
    arguments: list[Any] = field(default_factory=list)
    object: str | None = None  # For method calls


# Variable-related Classes

class PBVariable(PBNode):
    """Represents a PowerBuilder variable."""

    name: str
    type: str
    initial_value: Any | None = None
    visibility: str = "public"
    access_level: str = "public"  # Alias for visibility
    is_constant: bool = False
    is_static: bool = False

    def __post_init__(self):
        """Sync visibility and access_level."""
        if self.visibility != "public" and self.access_level == "public":
            self.access_level = self.visibility
        elif self.access_level != "public" and self.visibility == "public":
            self.visibility = self.access_level


# Alias for backward compatibility
PBVariableNode = PBVariable

class PBDefaultVariableNode(PBVariable):
    """Variable with default value."""

    # Inherits everything from PBVariable


class PBInstanceVariable(PBVariable):
    """Instance variable declaration."""
    pass


class PBSharedVariable(PBVariable):
    """Shared (static) variable declaration."""

    is_static: bool = True


class PBGlobalVariable(PBVariable):
    """Global variable declaration."""

    visibility: str = "global"


class PBConstant(PBVariable):
    """Constant declaration."""

    is_constant: bool = True

    def __post_init__(self) -> None:
        """Ensure constants have initial values."""
        if self.initial_value is None:
            msg = f"Constant {self.name} must have an initial value"
            raise ValueError(msg)


# Parameter passing modifiers

class PBParameterModifier(PBNode):
    """Parameter passing modifier."""

    is_reference: bool = False
    is_readonly: bool = False
    is_optional: bool = False


# Function signature for type checking

class PBFunctionSignature(PBNode):
    """Function signature for type checking and validation."""

    name: str
    return_type: str | None
    parameter_types: list[str]
    parameter_names: list[str]
    parameter_modifiers: list[PBParameterModifier]

    def matches(self, other: PBFunctionSignature) -> bool:
        """Check if this signature matches another (for overloading)."""
        if self.name != other.name:
            return False
        if len(self.parameter_types) != len(
                other.parameter_types):
            return False
        # Check parameter types match
        for t1, t2 in zip(self.parameter_types, 
                         other.parameter_types, strict=False):
            if t1 != t2:
                return False
        return True

    def is_compatible_with_call(
        self, arg_types: list[str]) -> bool:
        """Check if a function call with given argument types is compatible."""
        if len(arg_types) != len(self.parameter_types):
            # Check for optional parameters
            required_params = sum(
                1 for mod in self.parameter_modifiers if not mod.is_optional )
            if len(arg_types) < required_params:
                return False

        # Check type compatibility for provided arguments
        for _i, (provided_type, expected_type) in enumerate(
                zip(arg_types, self.parameter_types, strict=False),
                ):
            if not self._is_type_compatible(
                    provided_type, expected_type):
                return False
        return True

    def _is_type_compatible(
        self, provided: str, expected: str) -> bool:
        """Check if provided type is compatible with expected type."""
        # Simple compatibility check - can be extended
        if provided == expected:
            return True
        # Check for numeric compatibility
        numeric_types = {
            "integer", "long", "decimal", "double", "real"}
        if provided.lower() in numeric_types and expected.lower() in numeric_types:
            return True
        # Check for string compatibility
        return bool(
            provided.lower() == "string" and expected.lower() == "string")
