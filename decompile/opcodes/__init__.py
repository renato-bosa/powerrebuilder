"""PowerBuilder opcode definitions and management.

This package provides comprehensive opcode support for all PowerBuilder versions
through a unified interface.
"""

# For backwards compatibility
from .opcodes import (
    OPCODE_MAP_UNIFIED,
    OPCODE_TABLE,
    OPCODES,
    OpcodeManager,
    find_opcode_by_name,
    get_opcode_info,
    get_opcodes_for_version,
    get_variant_info,
    has_variants,
)

__all__ = [
    "OPCODES",  # backwards compat
    "OPCODE_MAP_UNIFIED",  # backwards compat
    "OPCODE_TABLE",
    "OpcodeManager",
    "find_opcode_by_name",
    "get_opcode_info",
    "get_opcodes_for_version",
    "get_variant_info",
    "has_variants",
]
