"""PowerBuilder opcode definitions and management.

This package provides comprehensive opcode support for all PowerBuilder versions
through a unified interface.
"""

from .opcodes import (
    OPCODE_TABLE,
    OpcodeManager,
    get_opcode_info,
    find_opcode_by_name,
    get_opcodes_for_version,
    has_variants,
    get_variant_info,
)

# For backwards compatibility
from .opcodes import OPCODE_MAP_UNIFIED, OPCODES

__all__ = [
    'OPCODE_TABLE',
    'OpcodeManager',
    'get_opcode_info',
    'find_opcode_by_name', 
    'get_opcodes_for_version',
    'has_variants',
    'get_variant_info',
    'OPCODE_MAP_UNIFIED',  # backwards compat
    'OPCODES',  # backwards compat
]
