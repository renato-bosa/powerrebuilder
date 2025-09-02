import logging

logger = logging.getLogger(__name__)

"""Unified PowerBuilder opcode definitions and management.

This module consolidates all PowerBuilder opcode definitions, version handling,
and management into a single comprehensive reference. It includes:

    - All known opcodes from PowerBuilder 6.0 through 12.0+
    - Version-specific opcode filtering
    - Unknown/undocumented opcode variants
    - Opcode table management with caching

    - PB 6.0: Opcodes 0x00-0xFF (256 opcodes)
    - PB 8.0: Opcodes 0x00-0x246 (594 opcodes) - added LongLong, Byte types
    - PB 10.5+: Same as PB 8.0 (Unicode is at data representation level)
"""

from functools import lru_cache

from src.extract.pbd.version_detection import PowerBuilderVersion

from .opcodes import OPCODE_TABLE

# Version aliases - map common version names to canonical ones
VERSION_ALIASES = {
    "pb6": "pb6_0",
    "pb8": "pb8_0",
    "pb10": "pb10_5",
    "pb11": "pb11_0",
    "pb12": "pb12_0",
}

# Version-specific opcode ranges
VERSION_OPCODE_RANGES = {
    "pb6_0": (0x00, 0xFF),  # PB 6.0: 256 opcodes
    "pb8_0": (0x00, 0x246),  # PB 8.0: 594 opcodes
    "pb10_5": (0x00, 0x246),  # PB 10.5+: Same as PB 8.0
}

# Unknown opcodes with variant handling (imported from variants module if needed)
UNKNOWN_OPCODES_WITH_VARIANTS: dict[int, dict[int, tuple[str, int, str | None]]] = {}


def get_opcode_info(opcode: int) -> tuple[str, int, str] | None:
    """Get opcode information by opcode value.

    opcode: Opcode byte value

    Tuple of (mnemonic, length, hint) or None if not found
    """
    return OPCODE_TABLE.get(opcode)


def find_opcode_by_name(name: str) -> int | None:
    """Find opcode value by mnemonic name.

    name: Opcode mnemonic name

    Opcode value or None if not found
    """
    name_upper = name.upper()
    for code, (mnemonic, _, _) in OPCODE_TABLE.items():
        if mnemonic == name_upper:
            return code
    return None


@lru_cache(maxsize=8)
def get_opcodes_for_version(version: str) -> dict[int, tuple[str, int, str | None]]:
    """Get opcodes available for a specific PowerBuilder version (cached).

    version: Version string like "pb6_0" or "pb10_5"

    Dictionary of opcodes available in that version
    """
    # Resolve aliases
    actual_version = VERSION_ALIASES.get(version, version)

    # Get version range
    if actual_version in VERSION_OPCODE_RANGES:
        min_op, max_op = VERSION_OPCODE_RANGES[actual_version]
        return {k: v for k, v in OPCODE_TABLE.items() if min_op <= k <= max_op}

    # Default to full set
    return OPCODE_TABLE


def has_variants(opcode: int) -> bool:
    """Check if an opcode has known variants.

    opcode: The base opcode value

    True if the opcode has variants
    """
    return opcode in UNKNOWN_OPCODES_WITH_VARIANTS


def get_variant_info(opcode: int, variant: int) -> tuple[str, int, str | None] | None:
    """Get information for a specific opcode variant.

    opcode: The base opcode value
    variant: The variant byte value

    Tuple of (mnemonic, length, hint) or None if not found
    """
    if opcode in UNKNOWN_OPCODES_WITH_VARIANTS:
        variants = UNKNOWN_OPCODES_WITH_VARIANTS[opcode]
        if variant in variants:
            return variants[variant]
    return None


class OpcodeManager:
    """Manages version-specific opcode tables."""

    # Cache for loaded opcode tables
    _opcode_cache: dict[str, dict[int, tuple[str, int, str | None]]] = {}

    @classmethod
    def get_opcode_table(
        cls,
        version: PowerBuilderVersion,
    ) -> dict[int, tuple[str, int, str | None]]:
        """Get the opcode table for a specific PowerBuilder version.

        version: PowerBuilder version

        Dictionary mapping opcode bytes to (mnemonic, operand_len, operand_hint)
        """
        version_str = str(version)

        # Check cache first
        if version_str in cls._opcode_cache:
            return cls._opcode_cache[version_str]

        # Get version-specific opcodes
        opcode_map = get_opcodes_for_version(version_str)

        # Cache the result
        cls._opcode_cache[version_str] = opcode_map
        logger.info("Loaded opcode table for %s (%s opcodes)", version, len(opcode_map))
        return opcode_map

    @classmethod
    def get_minimal_fallback(cls) -> dict[int, tuple[str, int, str | None]]:
        """Get a minimal opcode table with basic opcodes.

        Minimal opcode table for emergency fallback
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
        }


# For backwards compatibility
OPCODE_MAP_UNIFIED = OPCODE_TABLE
OPCODES = OPCODE_TABLE
