"""Version-specific PowerBuilder opcode tables.

This package contains opcode definitions for different PowerBuilder versions.
Each module defines an OPCODE_MAP dictionary for that specific version.
"""

from .opcode_manager import OpcodeManager

__all__ = ['OpcodeManager']