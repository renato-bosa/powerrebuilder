"""Unified PowerBuilder opcode definitions and management.

This module consolidates all PowerBuilder opcode definitions, version handling,
and management into a single comprehensive reference. It includes:

- All known opcodes from PowerBuilder 6.0 through 12.0+
- Version-specific opcode filtering
- Unknown/undocumented opcode variants
- Opcode table management with caching

Version History:
- PB 6.0: Opcodes 0x00-0xFF (256 opcodes)
- PB 8.0: Opcodes 0x00-0x246 (594 opcodes) - added LongLong, Byte types
- PB 10.5+: Same as PB 8.0 (Unicode is at data representation level)
"""


import logging
from functools import lru_cache

from src.extract.utils.version import PowerBuilderVersion

logger = logging.getLogger(__name__)

# Main opcode table - PowerBuilder 8.0+ (most comprehensive)
# Format: opcode_byte -> (mnemonic, operand_byte_count, operand_interpretation_hint)
OPCODE_TABLE = {
    0x00: ("RETURN", 1, None), 0x01: ("STORE_RETURN_VAL", 2, "uint8"), 0x02: ("JUMPTRUE", 2, "relative_offset_byte"), 0x03: ("JUMPFALSE", 2, "relative_offset_byte"), 0x04: ("JUMP", 2, "relative_offset_byte"), 0x05: ("DBSTART", 1, None), 0x06: ("DBCOMMIT", 1, None), 0x07: ("DBROLLBACK", 1, None), 0x08: ("DBSTOP", 1, None), 0x09: ("DBCLOSE", 1, None), 0x0A: ("DBOPEN", 2, "uint16le"), 0x0B: ("DBDELETE", 4, "uint16le"), 0x0C: ("DBUPDATE", 4, "uint16le"), 0x0D: ("DBEXECUTE", 2, "uint16le"), 0x0E: ("DBFETCH", 4, "uint16le"), 0x0F: ("DBINSERT", 4, "uint16le"), 0x10: ("DBSELECT", 5, "uint16le"), 0x11: ("DESTROY", 1, None), 0x12: ("HALT", 1, None), 0x13: ("EVENTCALL", 6, "uint16le"), 0x14: ("LVALUE_EXPR", 1, None), 0x15: ("DBEXECUTEDYN", 4, "uint16le"), 0x16: ("DBPREPARE", 1, None), 0x17: ("DBOPENDYN", 4, "uint16le"), 0x18: ("DBEXECDYNPROC", 4, "uint16le"), 0x19: ("DBDESCRIBE", 1, None), 0x1A: ("DBSELECTBLOB", 5, "uint16le"), 0x1B: ("DBUPDATEBLOB", 4, "uint16le"), 0x1C: ("DBSELECTCLOB", 6, "uint16le"), 0x1D: ("DBUPDATECLOB", 5, "uint16le"), 0x1E: ("PUSH_LOCAL_VAR", 2, "uint8"), 0x1F: ("PUSH_SHARED_VAR", 2, "uint8"), 0x20: ("PUSH_CONST_REF", 3, "uint16le"), 0x21: ("PUSH_THIS", 1, None), 0x22: ("PUSH_PARENT", 1, None), 0x23: ("PUSH_PRIMARY", 1, None), 0x24: ("AND", 1, None), 0x25: ("OR", 1, None), 0x26: ("NOT", 1, None), 0x27: ("DOT", 2, "uint8"), 0x28: ("INDEX", 1, None), 0x29: ("GLOBFUNCCALL", 3, "uint16le"), 0x2A: ("CALL_FUNCTION", 2, "uint16le"), 0x2B: ("DLLFUNCCALL", 3, "uint16le"), 0x2C: ("DOTFUNCCALL", 3, "uint16le"), 0x2D: ("PUSH_GLOBAL_VAR", 3, "uint16le"), 0x2E: ("ARRAYLIST", 3, "uint16le"), 0x2F: ("PUSH_SHARED_VAR", 2, "uint8"), 0x30: ("PUSH_LOCAL_ARGREF", 2, "uint8"), 0x31: ("PUSH_SHARED_GLOBREF", 2, "uint8"), 0x32: ("PUSH_CONST_INT", 2, "uint16le"), 0x33: ("PUSH_CONST_UINT", 2, "uint16le"), 0x34: ("PUSH_CONST_LONG", 2, "uint16le"), 0x35: ("PUSH_CONST_ULONG", 2, "uint16le"), 0x36: ("PUSH_CONST_DEC", 2, "uint16le"), 0x37: ("PUSH_CONST_FLOAT", 2, "uint16le"), 0x38: ("PUSH_CONST_DOUBLE", 2, "uint16le"), 0x39: ("PUSH_CONST_TIME", 2, "uint16le"), 0x3A: ("PUSH_CONST_DATE", 2, "uint16le"), 0x3B: ("PUSH_CONST_STRING", 2, "uint16le"), 0x3C: ("PUSH_CONST_BOOL", 2, "uint16le"), 0x3D: ("PUSH_CONST_ENUM", 2, "uint16le"), 0x3E: ("CNV_INT_TO_UINT", 1, None), 0x3F: ("CNV_INT_TO_LONG", 1, None), 0x40: ("CNV_INT_TO_ULONG", 1, None), 0x41: ("CNV_INT_TO_DEC", 1, None), 0x42: ("CNV_INT_TO_FLOAT", 1, None), 0x43: ("CNV_INT_TO_DOUBLE", 1, None), 0x44: ("CNV_UINT_TO_LONG", 1, None), 0x45: ("CNV_UINT_TO_ULONG", 1, None), 0x46: ("CNV_UINT_TO_DEC", 1, None), 0x47: ("CNV_UINT_TO_FLOAT", 1, None), 0x48: ("CNV_UINT_TO_DOUBLE", 1, None), 0x49: ("CNV_LONG_TO_ULONG", 1, None), 0x4A: ("CNV_LONG_TO_DEC", 1, None), 0x4B: ("CNV_LONG_TO_FLOAT", 1, None), 0x4C: ("CNV_LONG_TO_DOUBLE", 1, None), 0x4D: ("CNV_ULONG_TO_DEC", 1, None), 0x4E: ("CNV_ULONG_TO_FLOAT", 1, None), 0x4F: ("CNV_ULONG_TO_DOUBLE", 1, None), 0x50: ("CNV_DEC_TO_FLOAT", 1, None), 0x51: ("CNV_DEC_TO_DOUBLE", 1, None), 0x52: ("CNV_FLOAT_TO_DOUBLE", 1, None), 0x53: ("ADD_INT", 1, None), 0x54: ("ADD_UINT", 1, None), 0x55: ("ADD_LONG", 1, None), 0x56: ("ADD_ULONG", 1, None), 0x57: ("ADD_DEC", 1, None), 0x58: ("ADD_FLOAT", 1, None), 0x59: ("ADD_DOUBLE", 1, None), 0x5A: ("SUB_INT", 1, None), 0x5B: ("SUB_UINT", 1, None), 0x5C: ("SUB_LONG", 1, None), 0x5D: ("SUB_ULONG", 1, None), 0x5E: ("SUB", 1, None), 0x5F: ("SUB_FLOAT", 1, None), 0x60: ("SUB_DOUBLE", 1, None), 0x61: ("MULT_INT", 1, None), 0x62: ("MULT_UINT", 1, None), 0x63: ("MULT_LONG", 1, None), 0x64: ("MULT_ULONG", 1, None), 0x65: ("MULT_DEC", 1, None), 0x66: ("MULT_FLOAT", 1, None), 0x67: ("MULT_DOUBLE", 1, None), 0x68: ("DIV_INT", 1, None), 0x69: ("DIV_UINT", 1, None), 0x6A: ("DIV_LONG", 1, None), 0x6B: ("DIV_ULONG", 1, None), 0x6C: ("DIV", 1, None), 0x6D: ("DIV_FLOAT", 1, None), 0x6E: ("DIV_DOUBLE", 1, None), 0x6F: ("POWER_INT", 1, None), 0x70: ("POWER_UINT", 1, None), 0x71: ("POWER_LONG", 1, None), 0x72: ("POWER_ULONG", 1, None), 0x73: ("POWER_DEC", 1, None), 0x74: ("POWER_FLOAT", 1, None), 0x75: ("POWER_DOUBLE", 1, None), 0x76: ("NEGATE_INT", 1, None), 0x77: ("NEGATE_UINT", 1, None), 0x78: ("NEGATE_LONG", 1, None), 0x79: ("NEGATE_ULONG", 1, None), 0x7A: ("NEGATE_DEC", 1, None), 0x7B: ("NEGATE_FLOAT", 1, None), 0x7C: ("ADD", 1, None), 0x7D: ("CAT_STRING", 1, None), 0x7E: ("CAT_BINARY", 1, None), 0x7F: ("ASSIGN_ARRAY", 1, None), 0x80: ("ASSIGN_INT", 2, "uint8"), 0x81: ("ASSIGN_UINT", 2, "uint8"), 0x82: ("ASSIGN_LONG", 2, "uint8"), 0x83: ("ASSIGN_ULONG", 2, "uint8"), 0x84: ("ASSIGN_DEC", 2, "uint8"), 0x85: ("ASSIGN_FLOAT", 2, "uint8"), 0x86: ("ASSIGN_DOUBLE", 2, "uint8"), 0x87: ("ASSIGN_BLOB", 2, "uint8"), 0x88: ("ASSIGN_STRING", 2, "uint8"), 0x89: ("ASSIGN_TIME", 2, "uint8"), 0x8A: ("ASSIGN_OBINST", 2, "uint8"), 0x8B: ("ASSIGN_ANCESTOR", 2, "uint8"), 0x8C: ("ASSIGN_ENUM", 2, "uint8"), 0x8D: ("CNV_UINT_TO_INT", 1, None), 0x8E: ("CNV_LONG_TO_INT", 1, None), 0x8F: ("CNV_ULONG_TO_INT", 1, None), 0x90: ("CNV_DEC_TO_INT", 1, None), 0x91: ("CNV_FLOAT_TO_INT", 1, None), 0x92: ("CNV_DOUBLE_TO_INT", 1, None), 0x93: ("CNV_LONG_TO_UINT", 1, None), 0x94: ("CNV_ULONG_TO_UINT", 1, None), 0x95: ("CNV_DEC_TO_UINT", 1, None), 0x96: ("CNV_FLOAT_TO_UINT", 1, None), 0x97: ("CNV_DOUBLE_TO_UINT", 1, None), 0x98: ("CNV_ULONG_TO_LONG", 1, None), 0x99: ("CNV_DEC_TO_LONG", 1, None), 0x9A: ("CNV_FLOAT_TO_LONG", 1, None), 0x9B: ("CNV_DOUBLE_TO_LONG", 1, None), 0x9C: ("CNV_DEC_TO_ULONG", 1, None), 0x9D: ("CNV_FLOAT_TO_ULONG", 1, None), 0x9E: ("CNV_DOUBLE_TO_ULONG", 1, None), 0x9F: ("CNV_FLOAT_TO_DEC", 1, None), 0xA0: ("CNV_DOUBLE_TO_DEC", 1, None), 0xA1: ("CNV_DOUBLE_TO_FLOAT", 1, None), 0xA2: ("CNV_STRING_TO_CHAR", 1, None), 0xA3: ("CNV_CHAR_TO_STRING", 1, None), 0xA4: ("CNV_STRING_TO_CHARARRAY", 1, None), 0xA5: ("CNV_CHARARRAY_TO_STRING", 1, None), 0xA6: ("EQ_INT", 1, None), 0xA7: ("EQ_UINT", 1, None), 0xA8: ("EQ_LONG", 1, None), 0xA9: ("EQ_ULONG", 1, None), 0xAA: ("EQ_DEC", 1, None), 0xAB: ("EQ_FLOAT", 1, None), 0xAC: ("EQ_DOUBLE", 1, None), 0xAD: ("EQ_STRING", 1, None), 0xAE: ("EQ_BOOL", 1, None), 0xAF: ("EQ_BINARY", 1, None), 0xB0: ("EQ_TIME", 1, None), 0xB1: ("EQ_DATE", 1, None), 0xB2: ("EQ_DATETIME", 1, None), 0xB3: ("EQ_CHAR", 1, None), 0xB4: ("EQ_OBINST", 1, None), 0xB5: ("EQ_ENUM", 1, None), 0xB6: ("NE_INT", 1, None), 0xB7: ("NE_UINT", 1, None), 0xB8: ("NE_LONG", 1, None), 0xB9: ("NE_ULONG", 1, None), 0xBA: ("NE_DEC", 1, None), 0xBB: ("NE_FLOAT", 1, None), 0xBC: ("NE_DOUBLE", 1, None), 0xBD: ("NE_STRING", 1, None), 0xBE: ("NE_BOOL", 1, None), 0xBF: ("NE_BINARY", 1, None), 0xC0: ("NE_TIME", 1, None), 0xC1: ("NE_DATE", 1, None), 0xC2: ("NE_DATETIME", 1, None), 0xC3: ("NE_CHAR", 1, None), 0xC4: ("NE_OBINST", 1, None), 0xC5: ("NE_ENUM", 1, None), 0xC6: ("GT_INT", 1, None), 0xC7: ("GT_UINT", 1, None), 0xC8: ("GT_LONG", 1, None), 0xC9: ("GT_ULONG", 1, None), 0xCA: ("GT_DEC", 1, None), 0xCB: ("GT_FLOAT", 1, None), 0xCC: ("GT_DOUBLE", 1, None), 0xCD: ("GT_STRING", 1, None), 0xCE: ("GT_TIME", 1, None), 0xCF: ("GT", 1, None), 0xD0: ("GT_DATETIME", 1, None), 0xD1: ("GT_CHAR", 1, None), 0xD2: ("LT_INT", 1, None), 0xD3: ("LT_UINT", 1, None), 0xD4: ("LT_LONG", 1, None), 0xD5: ("LT_ULONG", 1, None), 0xD6: ("LT_DEC", 1, None), 0xD7: ("LT_FLOAT", 1, None), 0xD8: ("LT_DOUBLE", 1, None), 0xD9: ("LT_STRING", 1, None), 0xDA: ("LT_TIME", 1, None), 0xDB: ("LT_DATE", 1, None), 0xDC: ("LT_DATETIME", 1, None), 0xDD: ("LT_CHAR", 1, None), 0xDE: ("GE_INT", 1, None), 0xDF: ("GE_UINT", 1, None), 0xE0: ("GE_LONG", 1, None), 0xE1: ("GE_ULONG", 1, None), 0xE2: ("GE_DEC", 1, None), 0xE3: ("GE_FLOAT", 1, None), 0xE4: ("GE_DOUBLE", 1, None), 0xE5: ("GE_STRING", 1, None), 0xE6: ("GE_TIME", 1, None), 0xE7: ("GE", 1, None), 0xE8: ("GE_DATETIME", 1, None), 0xE9: ("GE_CHAR", 1, None), 0xEA: ("LE_INT", 1, None), 0xEB: ("LE_UINT", 1, None), 0xEC: ("LE_LONG", 1, None), 0xED: ("LE_ULONG", 1, None), 0xEE: ("LE_DEC", 1, None), 0xEF: ("LE_FLOAT", 1, None), 0xF0: ("LE_DOUBLE", 1, None), 0xF1: ("LE_STRING", 1, None), 0xF2: ("LE_TIME", 1, None), 0xF3: ("LE", 1, None), 0xF4: ("LE_DATETIME", 1, None), 0xF5: ("LE_CHAR", 1, None), 0xF6: ("INCR_INT", 1, None), 0xF7: ("INCR_UINT", 1, None), 0xF8: ("INCR_LONG", 1, None), 0xF9: ("INCR_ULONG", 1, None), 0xFA: ("INCR_DEC", 1, None), 0xFB: ("INCR_FLOAT", 1, None), 0xFC: ("INCR_DOUBLE", 1, None), 0xFD: ("DECR_INT", 1, None), 0xFE: ("DECR_UINT", 1, None), 0xFF: ("DECR_LONG", 1, None), 0x100: ("DECR_ULONG", 1, None), 0x101: ("DECR_DEC", 1, None), 0x102: ("DECR_FLOAT", 1, None), 0x103: ("DECR_DOUBLE", 1, None), 0x104: ("ADDASSIGN_INT", 1, None), 0x105: ("ADDASSIGN_UINT", 1, None), 0x106: ("ADDASSIGN_LONG", 1, None), 0x107: ("ADDASSIGN_ULONG", 1, None), 0x108: ("ADDASSIGN_DEC", 1, None), 0x109: ("ADDASSIGN_FLOAT", 1, None), 0x10A: ("ADDASSIGN_DOUBLE", 1, None), 0x10B: ("SUBASSIGN_INT", 1, None), 0x10C: ("SUBASSIGN_UINT", 1, None), 0x10D: ("SUBASSIGN_LONG", 1, None), 0x10E: ("SUBASSIGN_ULONG", 1, None), 0x10F: ("ASSIGN", 1, None), 0x110: ("SUBASSIGN_FLOAT", 1, None), 0x111: ("SUBASSIGN_DOUBLE", 1, None), 0x112: ("MULTASSIGN_INT", 1, None), 0x113: ("MULTASSIGN_UINT", 1, None), 0x114: ("MULTASSIGN_LONG", 1, None), 0x115: ("MULTASSIGN_ULONG", 1, None), 0x116: ("MULTASSIGN_DEC", 1, None), 0x117: ("MULTASSIGN_FLOAT", 1, None), 0x118: ("MULTASSIGN_DOUBLE", 1, None), 0x119: ("DUP_STACKED_LVALUE", 1, None), 0x11A: ("EQ_ARRAY", 1, None), 0x11B: ("BEGIN_ASSIGN", 1, None), 0x11C: ("CONV_TO_LVALUE", 1, None), 0x11D: ("BEGIN_ASSIGN", 1, None), 0x11E: ("PUSH_SHARED_VAR_LV", 1, None), 0x11F: ("PUSH_LOCAL_GLOBREF_LV", 1, None), 0x120: ("PUSH_LOCAL_ARGREF_LV", 1, None), 0x121: ("PUSH_SHARED_GLOBREF_LV", 1, None), 0x122: ("DOT_LV", 1, None), 0x123: ("INDEX_LV", 1, None), 0x124: ("NOOP", 1, None), 0x125: ("POP", 1, None), 0x126: ("FREE", 1, None), 0x127: ("PUSH_RESULT", 1, None), 0x128: ("POP_POP", 1, None), 0x129: ("POP_FREE", 1, None), 0x12A: ("FREE_POP", 1, None), 0x12B: ("FREE_FREE", 1, None), 0x12C: ("COPY_ARRAY_INSTANCE", 1, None), 0x12D: ("COPY_STRUCTURE_INSTANCE", 1, None), 0x12E: ("COPY_CONST_DOUBLE", 1, None), 0x12F: ("COPY_CONST_DEC", 1, None), 0x130: ("COPY_CONST_DATE", 1, None), 0x131: ("COPY_CONST_TIME", 1, None), 0x132: ("COPY_CONST_DATETIME", 1, None), 0x133: ("COPY_CONST_STRING", 1, None), 0x134: ("COPY_LVALUE_DOUBLE", 1, None), 0x135: ("COPY_LVALUE_DEC", 1, None), 0x136: ("COPY_LVALUE_DATE", 1, None), 0x137: ("COPY_LVALUE_TIME", 1, None), 0x138: ("COPY_LVALUE_DATETIME", 1, None), 0x139: ("COPY_LVALUE_STRING", 1, None), 0x13A: ("COPY_LVALUE_BINARY", 1, None), 0x13B: ("POP_N_TIMES", 1, None), 0x13C: ("FREE_NODE_N", 1, None), 0x13D: ("CONV_DBL_RVALUE_TO_PTR", 1, None), 0x13E: ("COPY_EXPR_DOUBLE", 1, None), 0x13F: ("BREAKPOINT", 1, None), 0x140: ("INDEX_ERR_CHK", 1, None), 0x141: ("DOT_DOUBLE", 1, None), 0x142: ("DOT_DEC", 1, None), 0x143: ("INDEX_DOUBLE", 1, None), 0x144: ("INDEX_DEC", 1, None), 0x145: ("INDEX_ERR_CHK_DBL", 1, None), 0x146: ("INDEX_ERR_CHK_DEC", 1, None), 0x147: ("GLOBFUNCCALL_DOUBLE", 1, "uint16le"), 0x148: ("GLOBFUNCCALL_DEC", 1, "uint16le"), 0x149: ("SYSFUNCCALL_DOUBLE", 1, "uint16le"), 0x14A: ("SYSFUNCCALL_DEC", 1, "uint16le"), 0x14B: ("DLLFUNCCALL_DOUBLE", 1, "uint16le"), 0x14C: ("CALL_FUNCTION", 1, "uint16le"), 0x14D: ("DOTFUNCCALL_DOUBLE", 1, "uint16le"), 0x14E: ("DOTFUNCCALL_DEC", 1, "uint16le"), 0x14F: ("PUSH_LOCAL_VAR_DOUBLE", 1, "uint8"), 0x150: ("PUSH_LOCAL_VAR_DEC", 1, "uint8"), 0x151: ("PUSH_SHARED_VAR_DOUBLE", 1, None), 0x152: ("PUSH_SHARED_VAR_DEC", 1, None), 0x153: ("PUSH_LOCAL_GLOBREF_DOUBLE", 1, None), 0x154: ("PUSH_LOCAL_GLOBREF_DEC", 1, None), 0x155: ("PUSH_LOCAL_ARGREF_DOUBLE", 1, None), 0x156: ("PUSH_LOCAL_ARGREF_DEC", 1, None), 0x157: ("PUSH_SHARED_GLOBREF_DOUBLE", 1, None), 0x158: ("PUSH_SHARED_GLOBREF_DEC", 1, None), 0x159: ("ASSIGN_ANY", 1, None), 0x15A: ("CNV_ANY_TO_INT", 1, None), 0x15B: ("CNV_ANY_TO_UINT", 1, None), 0x15C: ("CNV_ANY_TO_LONG", 1, None), 0x15D: ("CNV_ANY_TO_ULONG", 1, None), 0x15E: ("CNV_ANY_TO_DEC", 1, None), 0x15F: ("CNV_ANY_TO_FLOAT", 1, None), 0x160: ("CNV_ANY_TO_DOUBLE", 1, None), 0x161: ("CNV_ANY_TO_STRING", 1, None), 0x162: ("CNV_ANY_TO_BOOL", 1, None), 0x163: ("CNV_ANY_TO_BINARY", 1, None), 0x164: ("CNV_ANY_TO_DATE", 1, None), 0x165: ("CNV_ANY_TO_TIME", 1, None), 0x166: ("CNV_ANY_TO_DATETIME", 1, None), 0x167: ("CNV_ANY_TO_CHAR", 1, None), 0x168: ("CNV_ANY_TO_HANDLE", 1, None), 0x169: ("CNV_ANY_TO_ENUM", 1, None), 0x16A: ("CNV_ANY_TO_OBJECT", 1, None), 0x16B: ("CONV_DEC_RVALUE_TO_PTR", 1, None), 0x16C: ("COPY_EXPR_DEC", 1, None), 0x16D: ("CREATE_EXT_OBJ", 1, None), 0x16E: ("GLOBFUNCCALL_ANY", 1, "uint16le"), 0x16F: ("SYSFUNCCALL_ANY", 1, "uint16le"), 0x170: ("DLLFUNCCALL_ANY", 1, "uint16le"), 0x171: ("DOTFUNCCALL_ANY", 1, "uint16le"), 0x172: ("PUSH_LOCAL_VAR_ANY", 1, "uint8"), 0x173: ("PUSH_SHARED_VAR_ANY", 1, None), 0x174: ("PUSH_LOCAL_GLOBREF_ANY", 1, None), 0x175: ("PUSH_LOCAL_ARGREF_ANY", 1, None), 0x176: ("PUSH_SHARED_GLOBREF_ANY", 1, None), 0x177: ("ADD_ANY", 1, None), 0x178: ("SUB_ANY", 1, None), 0x179: ("MULT_ANY", 1, None), 0x17A: ("DIV_ANY", 1, None), 0x17B: ("EQ", 1, None), 0x17C: ("NEGATE_ANY", 1, None), 0x17D: ("EQ_ANY", 1, None), 0x17E: ("NE_ANY", 1, None), 0x17F: ("GT_ANY", 1, None), 0x180: ("LT_ANY", 1, None), 0x181: ("GE_ANY", 1, None), 0x182: ("LE_ANY", 1, None), 0x183: ("AND_ANY", 1, None), 0x184: ("OR_ANY", 1, None), 0x185: ("NOT_ANY", 1, None), 0x186: ("DOT_ANY", 1, None), 0x187: ("INDEX_ANY", 1, None), 0x188: ("INDEX_ERR_CHK_ANY", 1, None), 0x189: ("INT", 1, None), 0x18A: ("ABS_LONG", 1, None), 0x18B: ("ABS_DOUBLE", 1, None), 0x18C: ("ASC", 1, None), 0x18D: ("BLOB", 1, None), 0x18E: ("CEILING", 1, None), 0x18F: ("COS", 1, None), 0x190: ("EXP", 1, None), 0x191: ("FACT", 1, None), 0x192: ("INTHIGH", 1, None), 0x193: ("INTLOW", 1, None), 0x194: ("ISDATE", 1, None), 0x195: ("ISNULL", 1, None), 0x196: ("ISNUMBER", 1, None), 0x197: ("ISTIME", 1, None), 0x198: ("ISVALID", 1, None), 0x199: ("LEN_STRING", 1, None), 0x19A: ("LEN_BINARY", 1, None), 0x19B: ("LOG", 1, None), 0x19C: ("LOGTEN", 1, None), 0x19D: ("LOWER", 1, None), 0x19E: ("PI", 1, None), 0x19F: ("RAND_LONG", 1, None), 0x1A0: ("RAND_DOUBLE", 1, None), 0x1A1: ("SIN", 1, None), 0x1A2: ("SQRT", 1, None), 0x1A3: ("TAN", 1, None), 0x1A4: ("UPPER", 1, None), 0x1A5: ("CONV_TO_REFPAK", 1, None), 0x1A6: ("PUSH_LOCAL_GLOBREF_RP", 1, None), 0x1A7: ("PUSH_LOCAL_ARGREF_RP", 1, None), 0x1A8: ("PUSH_SHARED_GLOBREF_RP", 1, None), 0x1A9: ("PUSH_LOCAL_VAR_RP", 1, "uint8"), 0x1AA: ("PUSH_LOCAL_VAR", 1, "uint8"), 0x1AB: ("PUSH_SHARED_VAR", 1, None), 0x1AC: ("TRANSFORM_BOUNDED_TO_UNBOUNDED", 1, None), 0x1AD: ("TRANSFORM_UNBOUNDED_TO_BOUNDED", 1, None), 0x1AE: ("TRANSFORM_UNBOUNDED_TO_UNBOUNDED", 1, None), 0x1AF: ("CALC_UNBOUNDED_ARRAY_BOUND", 1, None), 0x1B0: ("CALC_SIMPLE_ARRAY_BOUND", 1, None), 0x1B1: ("CALC_COMPLEX_ARRAY_BOUND", 1, None), 0x1B2: ("BUILD_UNBOUNDED_ARRAYLIST", 1, None), 0x1B3: ("BUILD_BOUNDED_ARRAYLIST", 1, None), 0x1B4: ("TRANSFORM_ARRAYLIST_TO_UNBOUNDED", 1, None), 0x1B5: ("TRANSFORM_ARRAYLIST_TO_BOUNDED", 1, None), 0x1B6: ("FREE_REF_PAK_N", 1, None), 0x1B7: ("ARRAY_BOUND_INFO", 1, None), 0x1B8: ("LOWERBOUND", 1, None), 0x1B9: ("UPPERBOUND", 1, None), 0x1BA: ("INCR_ANY", 1, None), 0x1BB: ("DECR_ANY", 1, None), 0x1BC: ("PUSH_FUNC_CLASS", 1, None), 0x1BD: ("CLASS_CALL", 1, "uint16le"), 0x1BE: ("CLASS_CALL_DEC", 1, "uint16le"), 0x1BF: ("CLASS_CALL_DOUBLE", 1, "uint16le"), 0x1C0: ("CLASS_CALL_ANY", 1, "uint16le"), 0x1C1: ("INDEX_RP", 1, None), 0x1C2: ("DBDELETEWITHCURS", 1, None), 0x1C3: ("DBEXECUTEIMMED", 1, None), 0x1C4: ("DBEXECDYNWITHDESC", 1, None), 0x1C5: ("DBFETCHWITHDESC", 1, None), 0x1C6: ("DBOPENDYNWITHDESC", 1, None), 0x1C7: ("DBUPDATEWITHCURS", 1, None), 0x1C8: ("CREATE_USING", 1, None), 0x1C9: ("TRANSFORM_ANY_TO_UNBOUNDED", 1, None), 0x1CA: ("TRANSFORM_ANY_TO_BOUNDED", 1, None), 0x1CB: ("FREE_INV_METH_ARGS", 1, None), 0x1CC: ("PUSH_NULL", 1, None), 0x1CD: ("COPY_LVALUE_ANY", 1, None), 0x1CE: ("ENTER_EMBEDDED", 1, None), 0x1CF: ("EXIT_EMBEDDED", 1, None), 0x1D0: ("DOT_FLD_UPDATE_INDEX_RP", 1, None), 0x1D1: ("CNV_STRING_TO_BOUNDED_CHARARRAY", 1, None), 0x1D2: ("PUSH_NTH_PARENT", 1, None), 0x1D3: ("MOD_LONG", 1, None), 0x1D4: ("MOD_ULONG", 1, None), 0x1D5: ("MOD_DOUBLE", 1, None), 0x1D6: ("MOD_DEC", 1, None), 0x1D7: ("MOD_ANY", 1, None), 0x1D8: ("ABS_DEC", 1, None), 0x1D9: ("ABS_ANY", 1, None), 0x1DA: ("CEILING_ANY", 1, None), 0x1DB: ("MIN_LONG", 1, None), 0x1DC: ("MIN_ULONG", 1, None), 0x1DD: ("MIN_DOUBLE", 1, None), 0x1DE: ("MIN_DEC", 1, None), 0x1DF: ("MIN_ANY", 1, None), 0x1E0: ("MAX_LONG", 1, None), 0x1E1: ("MAX_ULONG", 1, None), 0x1E2: ("MAX_DOUBLE", 1, None), 0x1E3: ("MAX_DEC", 1, None), 0x1E4: ("MAX_ANY", 1, None), 0x1E5: ("PUSH_TRY", 1, None), 0x1E6: ("POP_TRY", 1, None), 0x1E7: ("CATCH_EXCEPTION", 1, None), 0x1E8: ("THROW_EXCEPTION", 1, None), 0x1E9: ("GOSUB", 1, None), 0x1EA: ("RETURN_SUB", 1, None), 0x1EB: ("CNV_INT_TO_LONGLONG", 1, None), 0x1EC: ("CNV_UINT_TO_LONGLONG", 1, None), 0x1ED: ("CNV_LONG_TO_LONGLONG", 1, None), 0x1EE: ("CNV_ULONG_TO_LONGLONG", 1, None), 0x1EF: ("CNV_DEC_TO_LONGLONG", 1, None), 0x1F0: ("CNV_FLOAT_TO_LONGLONG", 1, None), 0x1F1: ("CNV_DOUBLE_TO_LONGLONG", 1, None), 0x1F2: ("CNV_LONGLONG_TO_INT", 1, None), 0x1F3: ("CNV_LONGLONG_TO_UINT", 1, None), 0x1F4: ("CNV_LONGLONG_TO_LONG", 1, None), 0x1F5: ("CNV_LONGLONG_TO_ULONG", 1, None), 0x1F6: ("CNV_LONGLONG_TO_DEC", 1, None), 0x1F7: ("CNV_LONGLONG_TO_FLOAT", 1, None), 0x1F8: ("CNV_LONGLONG_TO_DOUBLE", 1, None), 0x1F9: ("ADD_LONGLONG", 1, None), 0x1FA: ("ADD", 1, None), 0x1FB: ("SUB", 1, None), 0x1FC: ("DIV_LONGLONG", 1, None), 0x1FD: ("POWER_LONGLONG", 1, None), 0x1FE: ("POWER", 1, None), 0x1FF: ("NEGATE", 1, None), 0x200: ("PUSH_LOCAL_VAR_LONGLONG", 1, "uint8"), 0x201: ("PUSH_LOCAL_GLOBREF_LONGLONG", 1, None), 0x202: ("PUSH_LOCAL_ARGREF_LONGLONG", 1, None), 0x203: ("PUSH_SHARED_VAR_LONGLONG", 1, None), 0x204: ("PUSH_SHARED_GLOBREF_LONGLONG", 1, None), 0x205: ("ASSIGN_LONGLONG", 1, None), 0x206: ("COPY_CONST_LONGLONG", 1, None), 0x207: ("ADDASSIGN_LONGLONG", 1, None), 0x208: ("SUBASSIGN_LONGLONG", 1, None), 0x209: ("MULTASSIGN_LONGLONG", 1, None), 0x20A: ("ASSIGN", 1, None), 0x20B: ("DECR_LONGLONG", 1, None), 0x20C: ("COPY_LVALUE_LONGLONG", 1, None), 0x20D: ("ABS_LONGLONG", 1, None), 0x20E: ("RAND_LONGLONG", 1, None), 0x20F: ("EQ_LONGLONG", 1, None), 0x210: ("NE_LONGLONG", 1, None), 0x211: ("GT_LONGLONG", 1, None), 0x212: ("LT_LONGLONG", 1, None), 0x213: ("GE_LONGLONG", 1, None), 0x214: ("LE_LONGLONG", 1, None), 0x215: ("MOD_LONGLONG", 1, None), 0x216: ("MIN_LONGLONG", 1, None), 0x217: ("MAX_LONGLONG", 1, None), 0x218: ("GLOBFUNCCALL_LONGLONG", 1, "uint16le"), 0x219: ("SYSFUNCCALL_LONGLONG", 1, "uint16le"), 0x21A: ("DLLFUNCCALL_LONGLONG", 1, "uint16le"), 0x21B: ("DOTFUNCCALL_LONGLONG", 1, "uint16le"), 0x21C: ("CALL_FUNCTION", 1, "uint16le"), 0x21D: ("COPY_EXPR_LONGLONG", 1, None), 0x21E: ("DOT_LONGLONG", 1, None), 0x21F: ("INDEX_LONGLONG", 1, None), 0x220: ("CNV_ANY_TO_LONGLONG", 1, None), 0x221: ("CONV_LONGLONG_RVALUE_TO_PTR", 1, None), 0x222: ("INDEX_ERR_CHK_LONGLONG", 1, None), 0x223: ("PUSH_CONST_BYTE", 1, "uint16le"), 0x224: ("CNV_INT_TO_BYTE", 1, None), 0x225: ("CNV_UINT_TO_BYTE", 1, None), 0x226: ("CNV_LONG_TO_BYTE", 1, None), 0x227: ("CNV_ULONG_TO_BYTE", 1, None), 0x228: ("CNV_DEC_TO_BYTE", 1, None), 0x229: ("CNV_FLOAT_TO_BYTE", 1, None), 0x22A: ("CNV_DOUBLE_TO_BYTE", 1, None), 0x22B: ("CNV_ANY_TO_BYTE", 1, None), 0x22C: ("CNV_LONGLONG_TO_BYTE", 1, None), 0x22D: ("CNV_BYTE_TO_INT", 1, None), 0x22E: ("CNV_BYTE_TO_UINT", 1, None), 0x22F: ("CNV_BYTE_TO_LONG", 1, None), 0x230: ("CNV_BYTE_TO_ULONG", 1, None), 0x231: ("CNV_BYTE_TO_DEC", 1, None), 0x232: ("CNV_BYTE_TO_FLOAT", 1, None), 0x233: ("CNV_BYTE_TO_DOUBLE", 1, None), 0x234: ("CNV_BYTE_TO_LONGLONG", 1, None), 0x235: ("ADD_BYTE", 1, None), 0x236: ("SUB_BYTE", 1, None), 0x237: ("MULT_BYTE", 1, None), 0x238: ("DIV_BYTE", 1, None), 0x239: ("POWER_BYTE", 1, None), 0x23A: ("NEGATE_BYTE", 1, None), 0x23B: ("INCR_BYTE", 1, None), 0x23C: ("DECR_BYTE", 1, None), 0x23D: ("ASSIGN_BYTE", 1, None), 0x23E: ("ADDASSIGN_BYTE", 1, None), 0x23F: ("SUBASSIGN_BYTE", 1, None), 0x240: ("MULTASSIGN_BYTE", 1, None), 0x241: ("EQ_BYTE", 1, None), 0x242: ("NE_BYTE", 1, None), 0x243: ("GT_BYTE", 1, None), 0x244: ("LT_BYTE", 1, None), 0x245: ("GE_BYTE", 1, None), 0x246: ("LE_BYTE", 1, None), }

# Unknown opcodes with variants observed in real PBD files
# Format: opcode -> variant -> (mnemonic, length, hint)
UNKNOWN_OPCODES_WITH_VARIANTS = {
    0x0E: {  # Possibly DBFETCH variants
        0x00: ("DBFETCH_VAR_00", 4, "uint16le"), 0x02: ("DBFETCH_VAR_02", 4, "uint16le"), 0x1D: ("DBFETCH_VAR_1D", 4, "uint16le"), 0xC2: ("DBFETCH_VAR_C2", 4, "uint16le"), 0xC3: ("DBFETCH_VAR_C3", 4, "uint16le"), 0xC4: ("DBFETCH_VAR_C4", 4, "uint16le"), 0xC5: ("DBFETCH_VAR_C5", 4, "uint16le"), 0xC6: ("DBFETCH_VAR_C6", 4, "uint16le"), }, 0x0F: {  # Possibly DBINSERT variants
        0x00: ("DBINSERT_VAR_00", 4, "uint16le"), 0x01: ("DBINSERT_VAR_01", 4, "uint16le"), 0x04: ("DBINSERT_VAR_04", 4, "uint16le"), 0x2B: ("DBINSERT_VAR_2B", 4, "uint16le"), 0x3A: ("DBINSERT_VAR_3A", 4, "uint16le"), 0xC2: ("DBINSERT_VAR_C2", 4, "uint16le"), 0xC3: ("DBINSERT_VAR_C3", 4, "uint16le"), 0xC4: ("DBINSERT_VAR_C4", 4, "uint16le"), 0xC5: ("DBINSERT_VAR_C5", 4, "uint16le"), 0xC6: ("DBINSERT_VAR_C6", 4, "uint16le"), }, }

# Version-specific opcode ranges
VERSION_OPCODE_RANGES = {
    "pb6_0": (0x00, 0xFF), # PowerBuilder 6.0: Basic opcodes only
    "pb7_0": (0x00, 0xFF), # PowerBuilder 7.0: Same as 6.0
    "pb8_0": (0x00, 0x246), # PowerBuilder 8.0: Extended opcodes
    "pb9_0": (0x00, 0x246), # PowerBuilder 9.0: Same as 8.0
    "pb10_0": (0x00, 0x246), # PowerBuilder 10.0: Same as 8.0 (Unicode)
    "pb10_5": (0x00, 0x246), # PowerBuilder 10.5: Same as 8.0 (Unicode)
    "pb11_0": (0x00, 0x246), # PowerBuilder 11.0+: Same as 8.0
    "pb12_0": (0x00, 0x246), # PowerBuilder 12.0+: Same as 8.0
}

# Version aliases for compatibility
VERSION_ALIASES = {
    "pb10_5": "pb8_0", # PB 10.5 uses same opcodes as 8.0
    "pb9_0": "pb8_0", # PB 9.0 uses same opcodes as 8.0
    "pb11_0": "pb8_0", # PB 11.0+ uses same opcodes as 8.0
    "pb12_0": "pb8_0", # PB 12.0+ uses same opcodes as 8.0
    "pb7_0": "pb6_0", # PB 7.0 uses same opcodes as 6.0
}

# Export all opcode names for easy lookup
OPCODE_NAMES = {code: info[0] for code, info in OPCODE_TABLE.items()}

# Opcode categories for analysis
OPCODE_CATEGORIES = {
    "control_flow": range(0x05), "database": range(0x05, 0x1E), "variables": range(0x1E, 0x3E), "conversions": range(0x3E, 0x9E), "arithmetic": range(0x9E, 0xE6), "comparison": range(0xE6, 0x100), "assignments": range(0x100, 0x120), "special": range(0x120, 0x247), }


def get_opcode_info(opcode: int) -> tuple[str, int, str | None] | None:








    """Get opcode information by opcode value.

    Args:
        opcode: Opcode byte value

    Returns:
        Tuple of (mnemonic, length, hint) or None if not found
    """
    return OPCODE_TABLE.get(opcode)


def find_opcode_by_name(name: str) -> int | None:








    """Find opcode value by mnemonic name.

    Args:
        name: Opcode mnemonic name

    Returns:
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

    Args:
        version: Version string like "pb6_0" or "pb10_5"

    Returns:
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

    Args:
        opcode: The base opcode value

    Returns:
        True if the opcode has variants
    """
    return opcode in UNKNOWN_OPCODES_WITH_VARIANTS


def get_variant_info(opcode: int, variant: int) -> tuple[str, int, str | None] | None:








    """Get information for a specific opcode variant.

    Args:
        opcode: The base opcode value
        variant: The variant byte value

    Returns:
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
        cls, version: PowerBuilderVersion,
    ) -> dict[int, tuple[str, int, str | None]]:


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

        # Get version-specific opcodes
        opcode_map = get_opcodes_for_version(version_str)

        # Cache the result
        cls._opcode_cache[version_str] = opcode_map
        logger.info("Loaded opcode table for %s (%s opcodes)", version, len(opcode_map))
        return opcode_map

    @classmethod
    def get_minimal_fallback(cls) -> dict[int, tuple[str, int, str | None]]:


        """Get a minimal opcode table with basic opcodes.

        Returns:
            Minimal opcode table for emergency fallback
        """
        return {
            0x00: ("RETURN", 0, None), 0x01: ("STORE_RETURN_VAL", 1, "byte_value"), 0x02: ("JUMPTRUE", 1, "relative_offset_byte"), 0x03: ("JUMPFALSE", 1, "relative_offset_byte"), 0x04: ("JUMP", 1, "relative_offset_byte"), 0x1E: ("PUSH_LOCAL_VAR", 1, "var_index"), 0x21: ("PUSH_THIS", 0, None), 0x24: ("AND", 0, None), 0x25: ("OR", 0, None), 0x26: ("NOT", 0, None), 0x27: ("DOT", 1, "field_index"), 0x32: ("PUSH_CONST_INT", 1, "int16_value"), 0x3B: ("PUSH_CONST_STRING", 1, "string_index"), 0x3C: ("PUSH_CONST_BOOL", 1, "byte_value"), }


# For backwards compatibility
OPCODE_MAP_UNIFIED = OPCODE_TABLE
OPCODES = OPCODE_TABLE
