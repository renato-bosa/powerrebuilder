"""PowerBuilder function, argument, and variable entities.

This module consolidates function-related entities from pb_function.py,
pb_argument.py, and pb_variable.py.
"""

from __future__ import annotations
from dataclasses import field
from typing import Any
from src.model.types.base import PBNode

class PBArgumentNode(PBNode):
    """Represents a function/event argument."""

    type: str
    is_reference: bool = False
    is_readonly: bool = False
    default_value: Any | None = None

    def __init__(self, name: str, arg_type: str, is_reference: bool = False, is_readonly: bool = False, default_value: Any | None = None):
        super().__init__()
        self.name = name  # Use inherited property
        self.type = arg_type
        self.is_reference = is_reference
        self.is_readonly = is_readonly
        self.default_value = default_value


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

    return_type: str | None = None
    arguments: PBArgumentsNode = field(default_factory=PBArgumentsNode)
    visibility: str = "public"
    access_level: str = "public"  # Alias for visibility
    is_static: bool = False
    is_override: bool = False
    body: Any | None = None  # Function body (statements)

    def __init__(self, name: str, return_type: str | None = None, visibility: str = "public", is_static: bool = False, is_override: bool = False, body: Any | None = None):
        super().__init__()
        self.name = name  # Use inherited property
        self.return_type = return_type
        self.arguments = PBArgumentsNode()
        self.visibility = visibility
        self.access_level = visibility  # Sync visibility and access_level
        self.is_static = is_static
        self.is_override = is_override
        self.body = body


class PBFunctionDeclaration(PBNode):
    """Function declaration (forward declaration)."""

    return_type: str | None = None
    arguments: PBArgumentsNode = field(default_factory=PBArgumentsNode)
    visibility: str = "public"
    is_external: bool = False
    library_name: str | None = None  # For external functions
    alias: str | None = None  # For external functions

    def __init__(self, name: str, return_type: str | None = None, visibility: str = "public", is_external: bool = False, library_name: str | None = None, alias: str | None = None):
        super().__init__()
        self.name = name  # Use inherited property
        self.return_type = return_type
        self.arguments = PBArgumentsNode()
        self.visibility = visibility
        self.is_external = is_external
        self.library_name = library_name
        self.alias = alias

class PBFunctionCall(PBNode):
    """Function call."""

    function_name: str
    arguments: list[Any] = field(default_factory=list)
    object: str | None = None  # For method calls
    
    # Additional attributes accessed by various parts of the codebase
    def get_children(self) -> list[Any]:
        """Get children of this function call node."""
        return self.children


# Variable-related Classes

class PBVariable(PBNode):
    """Represents a PowerBuilder variable."""

    type: str
    initial_value: Any | None = None
    visibility: str = "public"
    access_level: str = "public"  # Alias for visibility
    is_constant: bool = False
    is_static: bool = False

    def __init__(self, name: str, var_type: str, initial_value: Any | None = None, visibility: str = "public", is_constant: bool = False, is_static: bool = False):
        super().__init__()
        self.name = name  # Use inherited property
        self.type = var_type
        self.initial_value = initial_value
        self.visibility = visibility
        self.access_level = visibility  # Sync visibility and access_level
        self.is_constant = is_constant
        self.is_static = is_static


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

    def __init__(self, name: str, var_type: str, initial_value: Any, **kwargs):
        if initial_value is None:
            msg = f"Constant {name} must have an initial value"
            raise ValueError(msg)
        super().__init__(name, var_type, initial_value=initial_value, is_constant=True, **kwargs)


# Parameter passing modifiers

class PBParameterModifier(PBNode):
    """Parameter passing modifier."""

    is_reference: bool = False
    is_readonly: bool = False
    is_optional: bool = False


# Function signature for type checking

class PBFunctionSignature(PBNode):
    """Function signature for type checking and validation."""

    return_type: str | None
    parameter_types: list[str]
    parameter_names: list[str]
    parameter_modifiers: list[PBParameterModifier]

    def __init__(self, name: str, return_type: str | None, parameter_types: list[str], parameter_names: list[str], parameter_modifiers: list[PBParameterModifier]):
        super().__init__()
        self.name = name  # Use inherited property
        self.return_type = return_type
        self.parameter_types = parameter_types
        self.parameter_names = parameter_names
        self.parameter_modifiers = parameter_modifiers

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
