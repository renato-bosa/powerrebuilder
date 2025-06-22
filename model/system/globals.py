"""PowerBuilder global variables.

This module defines classes and functions for PowerBuilder global variables.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum, auto
from typing import Any

from model.utils.base import PBNode


class PBGlobalScope(Enum):
    """Scope of global variables."""

    GLOBAL = auto()  # Global to the entire application
    SHARED = auto()  # Shared between objects
    INSTANCE = auto()  # Instance variable
    LOCAL = auto()  # Local to a specific object


@dataclass
class PBGlobalVariable(PBNode):
    """PowerBuilder global variable.

    Attributes:
        name: Variable name
        type_name: Variable type
        scope: Variable scope
        default_value: Default value of the variable
        description: Description of the variable
        is_readonly: Whether the variable is read-only
        is_deprecated: Whether the variable is deprecated
        used_by: Object types that use this variable
    """

    name: str
    type_name: str
    scope: PBGlobalScope
    default_value: Any | None = None
    description: str | None = None
    is_readonly: bool = False
    is_deprecated: bool = False
    used_by: set[str] = field(default_factory=set)


# Registry for global variables
_GLOBAL_VARIABLES: dict[str, PBGlobalVariable] = {}


def register_global_variable(variable: PBGlobalVariable) -> PBGlobalVariable:



    
    


    """Register a global variable.

    Args:
        variable: The variable to register

    Returns:
        The registered variable

    Raises:
        ValueError: If a variable with the same name already exists
    """
    var_name_lower = variable.name.lower()
    if var_name_lower in _GLOBAL_VARIABLES:
        msg = f"Variable {variable.name} already registered"
        raise ValueError(msg)

    _GLOBAL_VARIABLES[var_name_lower] = variable
    return variable


def get_global_variable(name: str) -> PBGlobalVariable | None:



    
    


    """Get a global variable by name.

    Args:
        name: The name of the variable (case-insensitive)

    Returns:
        The variable, or None if not found
    """
    return _GLOBAL_VARIABLES.get(name.lower())


def get_global_variables_by_scope(scope: PBGlobalScope) -> list[PBGlobalVariable]:



    
    


    """Get all global variables of a specific scope.

    Args:
        scope: The scope to filter by

    Returns:
        List of variables of the specified scope
    """
    return [var for var in _GLOBAL_VARIABLES.values() if var.scope == scope]


def get_all_global_variables() -> list[PBGlobalVariable]:



    
    


    """Get all registered global variables.

    Returns:
        List of all global variables
    """
    return list(_GLOBAL_VARIABLES.values())


# Register common PowerBuilder global variables

# Global variables
register_global_variable(
    PBGlobalVariable(
        name="SQLCA", type_name="transaction", scope=PBGlobalScope.GLOBAL, description="Default database transaction object", used_by={"application", "window", "userobject", "datawindow"}, ), )

register_global_variable(
    PBGlobalVariable(
        name="Message", type_name="message", scope=PBGlobalScope.GLOBAL, description="Global message object for inter-window communication", used_by={"application", "window", "userobject"}, ), )

register_global_variable(
    PBGlobalVariable(
        name="Error", type_name="error", scope=PBGlobalScope.GLOBAL, description="Last error information", is_readonly=True, used_by={"application", "window", "userobject"}, ), )

register_global_variable(
    PBGlobalVariable(
        name="SQLErrText", type_name="string", scope=PBGlobalScope.GLOBAL, description="Last SQL error text", is_readonly=True, used_by={"application", "window", "userobject"}, ), )

register_global_variable(
    PBGlobalVariable(
        name="SQLDBCode", type_name="long", scope=PBGlobalScope.GLOBAL, description="Last SQL database error code", is_readonly=True, used_by={"application", "window", "userobject"}, ), )

# Application constants
register_global_variable(
    PBGlobalVariable(
        name="True", type_name="boolean", scope=PBGlobalScope.GLOBAL, default_value=True, description="Boolean constant true", is_readonly=True, used_by={"application", "window", "userobject", "datawindow"}, ), )

register_global_variable(
    PBGlobalVariable(
        name="False", type_name="boolean", scope=PBGlobalScope.GLOBAL, default_value=False, description="Boolean constant false", is_readonly=True, used_by={"application", "window", "userobject", "datawindow"}, ), )

register_global_variable(
    PBGlobalVariable(
        name="Null", type_name="any", scope=PBGlobalScope.GLOBAL, default_value=None, description="Null value", is_readonly=True, used_by={"application", "window", "userobject", "datawindow"}, ), )

# System constants
register_global_variable(
    PBGlobalVariable(
        name="TAB", type_name="char", scope=PBGlobalScope.GLOBAL, default_value="\t", description="Tab character", is_readonly=True, used_by={"application", "window", "userobject", "datawindow"}, ), )

register_global_variable(
    PBGlobalVariable(
        name="NEWLINE", type_name="char", scope=PBGlobalScope.GLOBAL, default_value="\n", description="Newline character", is_readonly=True, used_by={"application", "window", "userobject", "datawindow"}, ), )

# Button constants
register_global_variable(
    PBGlobalVariable(
        name="OK!", type_name="integer", scope=PBGlobalScope.GLOBAL, default_value=1, description="OK button constant", is_readonly=True, used_by={"application", "window", "userobject"}, ), )

register_global_variable(
    PBGlobalVariable(
        name="CANCEL!", type_name="integer", scope=PBGlobalScope.GLOBAL, default_value=2, description="Cancel button constant", is_readonly=True, used_by={"application", "window", "userobject"}, ), )

register_global_variable(
    PBGlobalVariable(
        name="YES!", type_name="integer", scope=PBGlobalScope.GLOBAL, default_value=1, description="Yes button constant", is_readonly=True, used_by={"application", "window", "userobject"}, ), )

register_global_variable(
    PBGlobalVariable(
        name="NO!", type_name="integer", scope=PBGlobalScope.GLOBAL, default_value=2, description="No button constant", is_readonly=True, used_by={"application", "window", "userobject"}, ), )

# Icon constants
register_global_variable(
    PBGlobalVariable(
        name="EXCLAMATION!", type_name="integer", scope=PBGlobalScope.GLOBAL, default_value=1, description="Exclamation icon constant", is_readonly=True, used_by={"application", "window", "userobject"}, ), )

register_global_variable(
    PBGlobalVariable(
        name="INFORMATION!", type_name="integer", scope=PBGlobalScope.GLOBAL, default_value=2, description="Information icon constant", is_readonly=True, used_by={"application", "window", "userobject"}, ), )

register_global_variable(
    PBGlobalVariable(
        name="QUESTION!", type_name="integer", scope=PBGlobalScope.GLOBAL, default_value=3, description="Question icon constant", is_readonly=True, used_by={"application", "window", "userobject"}, ), )

register_global_variable(
    PBGlobalVariable(
        name="STOPSIGN!", type_name="integer", scope=PBGlobalScope.GLOBAL, default_value=4, description="Stop sign icon constant", is_readonly=True, used_by={"application", "window", "userobject"}, ), )