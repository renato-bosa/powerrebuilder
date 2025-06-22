"""Global variables AST nodes for PowerBuilder.

This module contains nodes for global variable declarations.
"""

from dataclasses import dataclass, field
from typing import Any

from ..utils.base import PBNode


@dataclass
class GlobalVariable(PBNode):
    """Global variable declaration."""

    name: str
    type_name: str
    default_value: Any = None


@dataclass
class GlobalVariables(PBNode):
    """Container for global variables."""

    declarations: list[GlobalVariable] = field(default_factory=list)
