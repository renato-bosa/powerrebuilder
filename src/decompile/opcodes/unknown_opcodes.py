"""Unknown opcodes documentation and enhanced definitions.

This module documents opcodes that have been observed in PowerBuilder code
but are not yet fully understood. Based on analysis of real PBD files and
context patterns, we provide improved definitions for graceful handling.
"""

# Unknown opcodes from extraction logs with context analysis
UNKNOWN_OPCODES = {
    # Data operations (0x19-0x1E range often appears in data contexts)
    0x19: "DBSELECTBLOB",      # Often seen with database operations
    0x1A: "DBSELECTBLOB",      # Database BLOB operations
    0x1B: "DBUPDATEBLOB",      # Database BLOB update
    0x1E: "PUSH_LOCAL_VAR",    # Local variable push (based on context)
    
    # Variable operations (0x8A-0x91 range)
    0x8A: "ASSIGN_OBINST",     # Object instance assignment
    0x8B: "ASSIGN_ANCESTOR",   # Ancestor assignment
    0x90: "CNV_DEC_TO_INT",    # Decimal to integer conversion
    0x91: "CNV_FLOAT_TO_INT",  # Float to integer conversion
    
    # Extended opcodes (0xC4-0xC7 are very common)
    0xC4: "NE_OBINST",         # Object instance not-equal comparison
    0xC5: "NE_ENUM",           # Enum not-equal comparison
    0xC6: "GT_INT",            # Integer greater-than comparison
    0xC7: "GT_UINT",           # Unsigned int greater-than
    
    # Less common extended opcodes
    0xDC: "LT_DATETIME",       # DateTime less-than comparison
    0xDE: "GE_INT",            # Integer greater-or-equal
    0xDF: "GE_UINT",           # Unsigned int greater-or-equal
    0xEA: "LE_INT",            # Integer less-or-equal
    0xEB: "LE_UINT",           # Unsigned int less-or-equal
    0xED: "LE_ULONG",          # Unsigned long less-or-equal
    
    # Very high opcodes (likely PowerBuilder 8.0+ extended set)
    0x95: "CNV_DEC_TO_UINT",   # Decimal to unsigned int conversion
    0x9F: "CNV_FLOAT_TO_DEC",  # Float to decimal conversion
    0xA7: "EQ_UINT",           # Unsigned int equality
    0xB5: "EQ_ENUM",           # Enum equality
    0xBD: "NE_STRING",         # String not-equal
}

# Enhanced opcode definitions based on pattern analysis
UNKNOWN_OPCODE_DEFINITIONS = {
    # Format: opcode: (mnemonic, operand_count, description)
    # Database BLOB operations (matching main opcode table pattern)
    0x19: ("DBSELECTBLOB", 5, "Select BLOB from database"),
    0x1A: ("DBSELECTBLOB_VAR", 5, "Select BLOB variant"),
    0x1B: ("DBUPDATEBLOB", 4, "Update BLOB in database"),
    0x1E: ("PUSH_LOCAL_VAR", 2, "Push local variable"),
    
    # Assignment operations
    0x8A: ("ASSIGN_OBINST", 2, "Assign object instance"),
    0x8B: ("ASSIGN_ANCESTOR", 2, "Assign ancestor reference"),
    0x90: ("CNV_DEC_TO_INT", 1, "Convert decimal to integer"),
    0x91: ("CNV_FLOAT_TO_INT", 1, "Convert float to integer"),
    
    # Comparison operations (C4-C7 very common in conditionals)
    0xC4: ("NE_OBINST", 1, "Object instance not equal"),
    0xC5: ("NE_ENUM", 1, "Enum not equal"),
    0xC6: ("GT_INT", 1, "Integer greater than"),
    0xC7: ("GT_UINT", 1, "Unsigned integer greater than"),
    
    # DateTime and extended comparisons
    0xDC: ("LT_DATETIME", 1, "DateTime less than"),
    0xDE: ("GE_INT", 1, "Integer greater or equal"),
    0xDF: ("GE_UINT", 1, "Unsigned integer greater or equal"),
    0xEA: ("LE_INT", 1, "Integer less or equal"),
    0xEB: ("LE_UINT", 1, "Unsigned integer less or equal"),
    0xED: ("LE_ULONG", 1, "Unsigned long less or equal"),
    
    # Type conversions
    0x95: ("CNV_DEC_TO_UINT", 1, "Convert decimal to unsigned int"),
    0x9F: ("CNV_FLOAT_TO_DEC", 1, "Convert float to decimal"),
    0xA7: ("EQ_UINT", 1, "Unsigned integer equal"),
    0xB5: ("EQ_ENUM", 1, "Enum equal"),
    0xBD: ("NE_STRING", 1, "String not equal"),
}

def get_unknown_opcode_info(opcode: int) -> tuple[str, int, str] | None:






    """Get information about an unknown opcode.

    Args:
        opcode: The opcode value

    Returns:
        Tuple of (mnemonic, operand_count, description) or None
    """
    return UNKNOWN_OPCODE_DEFINITIONS.get(opcode)

def is_known_unknown(opcode: int) -> bool:






    """Check if an opcode is a known unknown (documented but not implemented).

    Args:
        opcode: The opcode value

    Returns:
        True if the opcode is documented as unknown
    """
    return opcode in UNKNOWN_OPCODES
