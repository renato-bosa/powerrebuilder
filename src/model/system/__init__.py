"""System functions and global variables for PowerBuilder.

This module provides classes and functions for representing PowerBuilder
system functions, system events, and global variables.
"""

from __future__ import annotations

from .events import PBSystemEvent, PBSystemEventType, get_system_event, register_system_event
from .functions import PBBuiltInFunction, PBSystemFunction, get_system_function, register_system_function
from .globals import PBGlobalVariable, get_global_variable, register_global_variable

__all__ = [
    "PBBuiltInFunction",
    "PBGlobalVariable",
    "PBSystemEvent",
    "PBSystemEventType",
    "PBSystemFunction",
    "get_global_variable",
    "get_system_event",
    "get_system_function",
    "register_global_variable",
    "register_system_event",
    "register_system_function",
]
