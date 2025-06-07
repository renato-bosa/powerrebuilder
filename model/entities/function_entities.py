"""PowerBuilder function, argument, and variable entities.

This module consolidates function-related entities from pb_function.py, 
pb_argument.py, and pb_variable.py.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Optional

from ..utils.base import PBNode


# Argument-related Classes
@dataclass
class PBArgumentNode(PBNode):
    """Represents a function/event argument."""
    name: str
    type: str
    is_reference: bool = False
    is_readonly: bool = False
    default_value: Optional[Any] = None


@dataclass
class PBArgumentOptionNode(PBNode):
    """Represents argument passing options."""
    by_reference: bool = False
    readonly: bool = False


@dataclass
class PBArgumentsNode(PBNode):
    """Container for multiple arguments."""
    arguments: list[PBArgumentNode] = field(default_factory=list)
    
    def add_argument(self, arg: PBArgumentNode) -> None:
        """Add an argument to the collection."""
        self.arguments.append(arg)
    
    def get_argument(self, name: str) -> Optional[PBArgumentNode]:
        """Get an argument by name."""
        for arg in self.arguments:
            if arg.name == name:
                return arg
        return None


# Alias for backward compatibility
PBFunctionArgumentNode = PBArgumentNode


# Function-related Classes
@dataclass
class PBFunction(PBNode):
    """Represents a PowerBuilder function."""
    name: str
    return_type: Optional[str] = None
    arguments: PBArgumentsNode = field(default_factory=PBArgumentsNode)
    visibility: str = "public"
    is_static: bool = False
    is_override: bool = False
    body: Optional[Any] = None  # Function body (statements)


@dataclass
class PBFunctionDeclaration(PBNode):
    """Function declaration (forward declaration)."""
    name: str
    return_type: Optional[str] = None
    arguments: PBArgumentsNode = field(default_factory=PBArgumentsNode)
    visibility: str = "public"
    is_external: bool = False
    library_name: Optional[str] = None  # For external functions
    alias: Optional[str] = None  # For external functions


@dataclass
class PBFunctionCall(PBNode):
    """Function call."""
    function_name: str
    arguments: list[Any] = field(default_factory=list)
    object: Optional[str] = None  # For method calls


# Variable-related Classes
@dataclass
class PBVariable(PBNode):
    """Represents a PowerBuilder variable."""
    name: str
    type: str
    initial_value: Optional[Any] = None
    visibility: str = "public"
    is_constant: bool = False
    is_static: bool = False


@dataclass
class PBDefaultVariableNode(PBVariable):
    """Variable with default value."""
    pass  # Inherits everything from PBVariable


@dataclass
class PBInstanceVariable(PBVariable):
    """Instance variable declaration."""
    pass


@dataclass
class PBSharedVariable(PBVariable):
    """Shared (static) variable declaration."""
    is_static: bool = True


@dataclass
class PBGlobalVariable(PBVariable):
    """Global variable declaration."""
    visibility: str = "global"


@dataclass
class PBConstant(PBVariable):
    """Constant declaration."""
    is_constant: bool = True
    
    def __post_init__(self):
        """Ensure constants have initial values."""
        if self.initial_value is None:
            raise ValueError(f"Constant {self.name} must have an initial value")


# Parameter passing modifiers
@dataclass
class PBParameterModifier(PBNode):
    """Parameter passing modifier."""
    is_reference: bool = False
    is_readonly: bool = False
    is_optional: bool = False


# Function signature for type checking
@dataclass
class PBFunctionSignature(PBNode):
    """Function signature for type checking and validation."""
    name: str
    return_type: Optional[str]
    parameter_types: list[str]
    parameter_names: list[str]
    parameter_modifiers: list[PBParameterModifier]
    
    def matches(self, other: PBFunctionSignature) -> bool:
        """Check if this signature matches another (for overloading)."""
        if self.name != other.name:
            return False
        if len(self.parameter_types) != len(other.parameter_types):
            return False
        # Check parameter types match
        for t1, t2 in zip(self.parameter_types, other.parameter_types):
            if t1 != t2:
                return False
        return True
    
    def is_compatible_with_call(self, arg_types: list[str]) -> bool:
        """Check if a function call with given argument types is compatible."""
        if len(arg_types) != len(self.parameter_types):
            # Check for optional parameters
            required_params = sum(1 for mod in self.parameter_modifiers if not mod.is_optional)
            if len(arg_types) < required_params:
                return False
        
        # Check type compatibility for provided arguments
        for i, (provided_type, expected_type) in enumerate(zip(arg_types, self.parameter_types)):
            if not self._is_type_compatible(provided_type, expected_type):
                return False
        return True
    
    def _is_type_compatible(self, provided: str, expected: str) -> bool:
        """Check if provided type is compatible with expected type."""
        # Simple compatibility check - can be extended
        if provided == expected:
            return True
        # Check for numeric compatibility
        numeric_types = {'integer', 'long', 'decimal', 'double', 'real'}
        if provided.lower() in numeric_types and expected.lower() in numeric_types:
            return True
        # Check for string compatibility
        if provided.lower() == 'string' and expected.lower() == 'string':
            return True
        return False