"""PowerBuilder opcode definitions and management.

This package provides comprehensive opcode support for all PowerBuilder versions
through a unified interface.
"""

# Import from the comprehensive definitions module
from ..pcode.opcodes.definitions import (
    OPCODE_TABLE,
    get_opcode_info,
    get_opcodes_for_version,
    find_opcode_by_name,
    has_variants,
    get_variant_info,
)

# Import backwards compatibility items from opcodes.py
from .opcodes import (
    OPCODES,
    OPCODE_MAP_UNIFIED,
    OpcodeManager,
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
