"""Opcode table manager for version-specific loading.

This module manages loading the correct opcode table based on the detected
PowerBuilder version.
"""

import logging
from importlib import import_module

from extract.pbd_core.version_detector import PowerBuilderVersion

logger = logging.getLogger(__name__)


class OpcodeManager:
    """Manages version-specific opcode tables."""

    # Cache for loaded opcode tables
    _opcode_cache: dict[str, dict[int, tuple[str, int, str | None]]] = {}

    @classmethod
    def get_opcode_table(cls, version: PowerBuilderVersion) -> dict[int, tuple[str, int, str | None]]:
        """Get the opcode table for a specific PowerBuilder version.
        
        Args:
            version: PowerBuilder version
            
        Returns:
            Dictionary mapping opcode bytes to (mnemonic, operand_len, operand_hint)
        """
        version_str = str(version)

        # Check cache first
        if version_str in cls._opcode_cache:
            return cls._opcode_cache[version_str]

        # Try to load version-specific module
        try:
            module_name = f"decompile.opcode_tables.{version_str}"
            module = import_module(module_name)
            opcode_map = getattr(module, f"OPCODE_MAP_{version_str.upper()}")

            # Cache the loaded table
            cls._opcode_cache[version_str] = opcode_map
            logger.info(f"Loaded opcode table for {version}")
            return opcode_map

        except (ImportError, AttributeError) as e:
            logger.warning(f"No specific opcode table for {version}, using fallback: {e}")

            # Fallback to closest version
            return cls._get_fallback_table(version)

    @classmethod
    def _get_fallback_table(cls, version: PowerBuilderVersion) -> dict[int, tuple[str, int, str | None]]:
        """Get a fallback opcode table when exact version not found.
        
        Args:
            version: PowerBuilder version
            
        Returns:
            Fallback opcode table
        """
        # Try to load the unified/superset table
        try:
            from decompile.opcode_tables.unified import OPCODE_MAP_UNIFIED
            logger.info(f"Using unified opcode table as fallback for {version}")
            return OPCODE_MAP_UNIFIED

        except ImportError:
            # Last resort: return a minimal table
            logger.error("No unified opcode table found, using minimal fallback")
            return cls._get_minimal_table()

    @classmethod
    def _get_minimal_table(cls) -> dict[int, tuple[str, int, str | None]]:
        """Get a minimal opcode table with basic opcodes.
        
        Returns:
            Minimal opcode table
        """
        return {
            0x00: ("RETURN", 0, None),
            0x01: ("STORE_RETURN_VAL", 1, "byte_value"),
            0x02: ("JUMPTRUE", 1, "relative_offset_byte"),
            0x03: ("JUMPFALSE", 1, "relative_offset_byte"),
            0x04: ("JUMP", 1, "relative_offset_byte"),
            0x1E: ("PUSH_LOCAL_VAR", 1, "var_index"),
            0x21: ("PUSH_THIS", 0, None),
            0x24: ("AND", 0, None),
            0x25: ("OR", 0, None),
            0x26: ("NOT", 0, None),
            0x27: ("DOT", 1, "field_index"),
            0x32: ("PUSH_CONST_INT", 1, "int16_value"),
            0x3B: ("PUSH_CONST_STRING", 1, "string_index"),
            0x3C: ("PUSH_CONST_BOOL", 1, "byte_value"),
            # Add more as needed
        }
