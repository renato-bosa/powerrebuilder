"""PowerBuilder opcode definitions and management.

This package provides comprehensive opcode support for all PowerBuilder versions
through a unified interface.
"""

# Import from the comprehensive definitions module
from .opcodes import (
    OPCODE_MAP_UNIFIED,
    OPCODE_TABLE,
    OPCODES,
    OpcodeManager,
    UnknownOpcodeHandler,
    find_opcode_by_name,
    get_opcode_info,
    get_opcodes_for_version,
    get_unknown_opcode_info,
    get_variant_info,
    has_variants,
    is_known_unknown,
)

__all__ = [
    "OPCODES",  # backwards compat
    "OPCODE_MAP_UNIFIED",  # backwards compat
    "OPCODE_TABLE",
    "OpcodeManager",
    "UnknownOpcodeHandler",
    "find_opcode_by_name",
    "get_opcode_info",
    "get_opcodes_for_version",
    "get_unknown_opcode_info",
    "get_variant_info",
    "has_variants",
    "is_known_unknown",
]
