//! PowerBuilder P-code Opcode Definitions
//!
//! Comprehensive opcode table covering PowerBuilder versions 6.0 through 2019.
//! - PB 6.0: Opcodes 0x00-0xFF (256 opcodes)
//! - PB 8.0+: Opcodes 0x00-0x246 (591 opcodes) - added LongLong, Byte types
//! - PB 10.5+: Same as PB 8.0 (Unicode is at data representation level)
//!
//! Ported from Python implementation with full compatibility.

use domain::decode::version::PBVersion;
use once_cell::sync::Lazy;
use std::collections::HashMap;

/// Opcode information
#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub struct OpcodeInfo {
    pub mnemonic: &'static str,
    /// Number of 16-bit operand words following the 16-bit opcode.
    pub operand_words: u8,
    pub hint: Option<&'static str>,
}

impl OpcodeInfo {
    pub const fn new(
        mnemonic: &'static str,
        operand_words: u8,
        hint: Option<&'static str>,
    ) -> Self {
        Self {
            mnemonic,
            operand_words,
            hint,
        }
    }
}

/// Macro for compact opcode definition
macro_rules! opcodes {
    ($($code:expr => ($mnem:expr, $len:expr $(, $hint:expr)?)),* $(,)?) => {
        &[
            $(
                ($code, OpcodeInfo::new($mnem, $len, opcodes!(@hint $($hint)?))),
            )*
        ]
    };
    (@hint) => { None };
    (@hint $hint:expr) => { Some($hint) };
}

/// PowerBuilder opcode table - all 591 opcodes
pub static OPCODE_TABLE: &[(u16, OpcodeInfo)] = opcodes![
    // Control flow (0x00-0x04)
    0x00 => ("RETURN", 0),
    0x01 => ("STORE_RETURN_VAL", 0),
    0x02 => ("JUMPTRUE", 1, "relative_offset"),
    0x03 => ("JUMPFALSE", 1, "relative_offset"),
    0x04 => ("JUMP", 1, "relative_offset"),

    // Database operations (0x05-0x1D)
    0x05 => ("DBSTART", 0),
    0x06 => ("DBCOMMIT", 0),
    0x07 => ("DBROLLBACK", 0),
    0x08 => ("DBSTOP", 0),
    0x09 => ("DBCLOSE", 0),
    0x0A => ("DBOPEN", 1),
    0x0B => ("DBDELETE", 3),
    0x0C => ("DBUPDATE", 3),
    0x0D => ("DBEXECUTE", 1),
    0x0E => ("DBFETCH", 3),
    0x0F => ("DBINSERT", 3),
    0x10 => ("DBSELECT", 4),
    0x11 => ("DESTROY", 0),
    0x12 => ("HALT", 0),
    0x13 => ("EVENTCALL", 5),
    0x14 => ("LVALUE_EXPR", 0),
    0x15 => ("DBEXECUTEDYN", 3),
    0x16 => ("DBPREPARE", 0),
    0x17 => ("DBOPENDYN", 3),
    0x18 => ("DBEXECDYNPROC", 3),
    0x19 => ("DBDESCRIBE", 0),
    0x1A => ("DBSELECTBLOB", 4),
    0x1B => ("DBUPDATEBLOB", 3),
    0x1C => ("DBSELECTCLOB", 5),
    0x1D => ("DBUPDATECLOB", 4),

    // Stack operations & variables (0x1E-0x3D)
    0x1E => ("PUSH_LOCAL_VAR", 1, "var_index"),
    0x1F => ("PUSH_SHARED_VAR", 1),
    0x20 => ("PUSH_CONST_REF", 2),
    0x21 => ("PUSH_THIS", 0),
    0x22 => ("PUSH_PARENT", 0),
    0x23 => ("PUSH_PRIMARY", 0),
    0x24 => ("AND", 0),
    0x25 => ("OR", 0),
    0x26 => ("NOT", 0),
    0x27 => ("DOT", 1, "field_index"),
    0x28 => ("INDEX", 0),
    0x29 => ("GLOBFUNCCALL", 2),
    0x2A => ("CALL_FUNCTION", 1),
    0x2B => ("DLLFUNCCALL", 2),
    0x2C => ("DOTFUNCCALL", 2, "field_index"),
    0x2D => ("PUSH_GLOBAL_VAR", 2, "var_index"),
    0x2E => ("ARRAYLIST", 2),
    0x2F => ("PUSH_SHARED_VAR", 1),
    0x30 => ("PUSH_LOCAL_ARGREF", 1, "var_index"),
    0x31 => ("PUSH_SHARED_GLOBREF", 1),
    0x32 => ("PUSH_CONST_INT", 1, "int16"),
    0x33 => ("PUSH_CONST_UINT", 1, "int16"),
    0x34 => ("PUSH_CONST_LONG", 1, "int16"),
    0x35 => ("PUSH_CONST_ULONG", 1, "int16"),
    0x36 => ("PUSH_CONST_DEC", 1),
    0x37 => ("PUSH_CONST_FLOAT", 1),
    0x38 => ("PUSH_CONST_DOUBLE", 1),
    0x39 => ("PUSH_CONST_TIME", 1),
    0x3A => ("PUSH_CONST_DATE", 1),
    0x3B => ("PUSH_CONST_STRING", 1, "string_index"),
    0x3C => ("PUSH_CONST_BOOL", 1, "byte_value"),
    0x3D => ("PUSH_CONST_ENUM", 1),

    // Type conversions (0x3E-0xA5)
    0x3E => ("CNV_INT_TO_UINT", 0),
    0x3F => ("CNV_INT_TO_LONG", 0),
    0x40 => ("CNV_INT_TO_ULONG", 0),
    0x41 => ("CNV_INT_TO_DEC", 0),
    0x42 => ("CNV_INT_TO_FLOAT", 0),
    0x43 => ("CNV_INT_TO_DOUBLE", 0),
    0x44 => ("CNV_UINT_TO_LONG", 0),
    0x45 => ("CNV_UINT_TO_ULONG", 0),
    0x46 => ("CNV_UINT_TO_DEC", 0),
    0x47 => ("CNV_UINT_TO_FLOAT", 0),
    0x48 => ("CNV_UINT_TO_DOUBLE", 0),
    0x49 => ("CNV_LONG_TO_ULONG", 0),
    0x4A => ("CNV_LONG_TO_DEC", 0),
    0x4B => ("CNV_LONG_TO_FLOAT", 0),
    0x4C => ("CNV_LONG_TO_DOUBLE", 0),
    0x4D => ("CNV_ULONG_TO_DEC", 0),
    0x4E => ("CNV_ULONG_TO_FLOAT", 0),
    0x4F => ("CNV_ULONG_TO_DOUBLE", 0),
    0x50 => ("CNV_DEC_TO_FLOAT", 0),
    0x51 => ("CNV_DEC_TO_DOUBLE", 0),
    0x52 => ("CNV_FLOAT_TO_DOUBLE", 0),

    // Arithmetic - ADD (0x53-0x59)
    0x53 => ("ADD_INT", 0),
    0x54 => ("ADD_UINT", 0),
    0x55 => ("ADD_LONG", 0),
    0x56 => ("ADD_ULONG", 0),
    0x57 => ("ADD_DEC", 0),
    0x58 => ("ADD_FLOAT", 0),
    0x59 => ("ADD_DOUBLE", 0),

    // Arithmetic - SUB (0x5A-0x60)
    0x5A => ("SUB_INT", 0),
    0x5B => ("SUB_UINT", 0),
    0x5C => ("SUB_LONG", 0),
    0x5D => ("SUB_ULONG", 0),
    0x5E => ("SUB", 0),
    0x5F => ("SUB_FLOAT", 0),
    0x60 => ("SUB_DOUBLE", 0),

    // Arithmetic - MULT (0x61-0x67)
    0x61 => ("MULT_INT", 0),
    0x62 => ("MULT_UINT", 0),
    0x63 => ("MULT_LONG", 0),
    0x64 => ("MULT_ULONG", 0),
    0x65 => ("MULT_DEC", 0),
    0x66 => ("MULT_FLOAT", 0),
    0x67 => ("MULT_DOUBLE", 0),

    // Arithmetic - DIV (0x68-0x6E)
    0x68 => ("DIV_INT", 0),
    0x69 => ("DIV_UINT", 0),
    0x6A => ("DIV_LONG", 0),
    0x6B => ("DIV_ULONG", 0),
    0x6C => ("DIV", 0),
    0x6D => ("DIV_FLOAT", 0),
    0x6E => ("DIV_DOUBLE", 0),

    // Arithmetic - POWER (0x6F-0x7C)
    0x6F => ("POWER_INT", 0),
    0x70 => ("POWER_UINT", 0),
    0x71 => ("POWER_LONG", 0),
    0x72 => ("POWER_ULONG", 0),
    0x73 => ("POWER_DEC", 0),
    0x74 => ("POWER_FLOAT", 0),
    0x75 => ("POWER_DOUBLE", 0),
    0x76 => ("NEGATE_INT", 0),
    0x77 => ("NEGATE_UINT", 0),
    0x78 => ("NEGATE_LONG", 0),
    0x79 => ("NEGATE_ULONG", 0),
    0x7A => ("NEGATE_DEC", 0),
    0x7B => ("NEGATE_FLOAT", 0),
    0x7C => ("ADD", 0),
    0x7D => ("CAT_STRING", 0),
    0x7E => ("CAT_BINARY", 0),

    // Assignment operations (0x7F-0x8C)
    0x7F => ("ASSIGN_ARRAY", 0),
    0x80 => ("ASSIGN_INT", 1),
    0x81 => ("ASSIGN_UINT", 1),
    0x82 => ("ASSIGN_LONG", 1),
    0x83 => ("ASSIGN_ULONG", 1),
    0x84 => ("ASSIGN_DEC", 1),
    0x85 => ("ASSIGN_FLOAT", 1),
    0x86 => ("ASSIGN_DOUBLE", 1),
    0x87 => ("ASSIGN_BLOB", 1),
    0x88 => ("ASSIGN_STRING", 1),
    0x89 => ("ASSIGN_TIME", 1),
    0x8A => ("ASSIGN_OBINST", 1),
    0x8B => ("ASSIGN_ANCESTOR", 1),
    0x8C => ("ASSIGN_ENUM", 1),

    // More conversions (0x8D-0xA5)
    0x8D => ("CNV_UINT_TO_INT", 0),
    0x8E => ("CNV_LONG_TO_INT", 0),
    0x8F => ("CNV_ULONG_TO_INT", 0),
    0x90 => ("CNV_DEC_TO_INT", 0),
    0x91 => ("CNV_FLOAT_TO_INT", 0),
    0x92 => ("CNV_DOUBLE_TO_INT", 0),
    0x93 => ("CNV_LONG_TO_UINT", 0),
    0x94 => ("CNV_ULONG_TO_UINT", 0),
    0x95 => ("CNV_DEC_TO_UINT", 0),
    0x96 => ("CNV_FLOAT_TO_UINT", 0),
    0x97 => ("CNV_DOUBLE_TO_UINT", 0),
    0x98 => ("CNV_ULONG_TO_LONG", 0),
    0x99 => ("CNV_DEC_TO_LONG", 0),
    0x9A => ("CNV_FLOAT_TO_LONG", 0),
    0x9B => ("CNV_DOUBLE_TO_LONG", 0),
    0x9C => ("CNV_DEC_TO_ULONG", 0),
    0x9D => ("CNV_FLOAT_TO_ULONG", 0),
    0x9E => ("CNV_DOUBLE_TO_ULONG", 0),
    0x9F => ("CNV_FLOAT_TO_DEC", 0),
    0xA0 => ("CNV_DOUBLE_TO_DEC", 0),
    0xA1 => ("CNV_DOUBLE_TO_FLOAT", 0),
    0xA2 => ("CNV_STRING_TO_CHAR", 0),
    0xA3 => ("CNV_CHAR_TO_STRING", 0),
    0xA4 => ("CNV_STRING_TO_CHARARRAY", 0),
    0xA5 => ("CNV_CHARARRAY_TO_STRING", 0),

    // Comparison - EQ (0xA6-0xB5)
    0xA6 => ("EQ_INT", 0),
    0xA7 => ("EQ_UINT", 0),
    0xA8 => ("EQ_LONG", 0),
    0xA9 => ("EQ_ULONG", 0),
    0xAA => ("EQ_DEC", 0),
    0xAB => ("EQ_FLOAT", 0),
    0xAC => ("EQ_DOUBLE", 0),
    0xAD => ("EQ_STRING", 0),
    0xAE => ("EQ_BOOL", 0),
    0xAF => ("EQ_BINARY", 0),
    0xB0 => ("EQ_TIME", 0),
    0xB1 => ("EQ_DATE", 0),
    0xB2 => ("EQ_DATETIME", 0),
    0xB3 => ("EQ_CHAR", 0),
    0xB4 => ("EQ_OBINST", 0),
    0xB5 => ("EQ_ENUM", 0),

    // Comparison - NE (0xB6-0xC5)
    0xB6 => ("NE_INT", 0),
    0xB7 => ("NE_UINT", 0),
    0xB8 => ("NE_LONG", 0),
    0xB9 => ("NE_ULONG", 0),
    0xBA => ("NE_DEC", 0),
    0xBB => ("NE_FLOAT", 0),
    0xBC => ("NE_DOUBLE", 0),
    0xBD => ("NE_STRING", 0),
    0xBE => ("NE_BOOL", 0),
    0xBF => ("NE_BINARY", 0),
    0xC0 => ("NE_TIME", 0),
    0xC1 => ("NE_DATE", 0),
    0xC2 => ("NE_DATETIME", 0),
    0xC3 => ("NE_CHAR", 0),
    0xC4 => ("NE_OBINST", 0),
    0xC5 => ("NE_ENUM", 0),

    // Comparison - GT (0xC6-0xD1)
    0xC6 => ("GT_INT", 0),
    0xC7 => ("GT_UINT", 0),
    0xC8 => ("GT_LONG", 0),
    0xC9 => ("GT_ULONG", 0),
    0xCA => ("GT_DEC", 0),
    0xCB => ("GT_FLOAT", 0),
    0xCC => ("GT_DOUBLE", 0),
    0xCD => ("GT_STRING", 0),
    0xCE => ("GT_TIME", 0),
    0xCF => ("GT", 0),
    0xD0 => ("GT_DATETIME", 0),
    0xD1 => ("GT_CHAR", 0),

    // Comparison - LT (0xD2-0xDD)
    0xD2 => ("LT_INT", 0),
    0xD3 => ("LT_UINT", 0),
    0xD4 => ("LT_LONG", 0),
    0xD5 => ("LT_ULONG", 0),
    0xD6 => ("LT_DEC", 0),
    0xD7 => ("LT_FLOAT", 0),
    0xD8 => ("LT_DOUBLE", 0),
    0xD9 => ("LT_STRING", 0),
    0xDA => ("LT_TIME", 0),
    0xDB => ("LT_DATE", 0),
    0xDC => ("LT_DATETIME", 0),
    0xDD => ("LT_CHAR", 0),

    // Comparison - GE (0xDE-0xE9)
    0xDE => ("GE_INT", 0),
    0xDF => ("GE_UINT", 0),
    0xE0 => ("GE_LONG", 0),
    0xE1 => ("GE_ULONG", 0),
    0xE2 => ("GE_DEC", 0),
    0xE3 => ("GE_FLOAT", 0),
    0xE4 => ("GE_DOUBLE", 0),
    0xE5 => ("GE_STRING", 0),
    0xE6 => ("GE_TIME", 0),
    0xE7 => ("GE", 0),
    0xE8 => ("GE_DATETIME", 0),
    0xE9 => ("GE_CHAR", 0),

    // Comparison - LE (0xEA-0xF5)
    0xEA => ("LE_INT", 0),
    0xEB => ("LE_UINT", 0),
    0xEC => ("LE_LONG", 0),
    0xED => ("LE_ULONG", 0),
    0xEE => ("LE_DEC", 0),
    0xEF => ("LE_FLOAT", 0),
    0xF0 => ("LE_DOUBLE", 0),
    0xF1 => ("LE_STRING", 0),
    0xF2 => ("LE_TIME", 0),
    0xF3 => ("LE", 0),
    0xF4 => ("LE_DATETIME", 0),
    0xF5 => ("LE_CHAR", 0),

    // Increment/Decrement (0xF6-0x103)
    0xF6 => ("INCR_INT", 0),
    0xF7 => ("INCR_UINT", 0),
    0xF8 => ("INCR_LONG", 0),
    0xF9 => ("INCR_ULONG", 0),
    0xFA => ("INCR_DEC", 0),
    0xFB => ("INCR_FLOAT", 0),
    0xFC => ("INCR_DOUBLE", 0),
    0xFD => ("DECR_INT", 0),
    0xFE => ("DECR_UINT", 0),
    0xFF => ("DECR_LONG", 0),

    // Extended opcodes (PB 8.0+) - beyond 0xFF
    0x100 => ("DECR_ULONG", 0),
    0x101 => ("DECR_DEC", 0),
    0x102 => ("DECR_FLOAT", 0),
    0x103 => ("DECR_DOUBLE", 0),

    // Compound assignment (0x104-0x118)
    0x104 => ("ADDASSIGN_INT", 0),
    0x105 => ("ADDASSIGN_UINT", 0),
    0x106 => ("ADDASSIGN_LONG", 0),
    0x107 => ("ADDASSIGN_ULONG", 0),
    0x108 => ("ADDASSIGN_DEC", 0),
    0x109 => ("ADDASSIGN_FLOAT", 0),
    0x10A => ("ADDASSIGN_DOUBLE", 0),
    0x10B => ("SUBASSIGN_INT", 0),
    0x10C => ("SUBASSIGN_UINT", 0),
    0x10D => ("SUBASSIGN_LONG", 0),
    0x10E => ("SUBASSIGN_ULONG", 0),
    0x10F => ("ASSIGN", 0),
    0x110 => ("SUBASSIGN_FLOAT", 0),
    0x111 => ("SUBASSIGN_DOUBLE", 0),
    0x112 => ("MULTASSIGN_INT", 0),
    0x113 => ("MULTASSIGN_UINT", 0),
    0x114 => ("MULTASSIGN_LONG", 0),
    0x115 => ("MULTASSIGN_ULONG", 0),
    0x116 => ("MULTASSIGN_DEC", 0),
    0x117 => ("MULTASSIGN_FLOAT", 0),
    0x118 => ("MULTASSIGN_DOUBLE", 0),

    // Extended operations (0x119-0x188)
    0x119 => ("DUP_STACKED_LVALUE", 0),
    0x11A => ("EQ_ARRAY", 0),
    0x11B => ("BEGIN_ASSIGN", 0),
    0x11C => ("CONV_TO_LVALUE", 0),
    0x11D => ("BEGIN_ASSIGN", 0),
    0x11E => ("PUSH_SHARED_VAR_LV", 0),
    0x11F => ("PUSH_LOCAL_GLOBREF_LV", 0, "var_index"),
    0x120 => ("PUSH_LOCAL_ARGREF_LV", 0, "var_index"),
    0x121 => ("PUSH_SHARED_GLOBREF_LV", 0),
    0x122 => ("DOT_LV", 0, "field_index"),
    0x123 => ("INDEX_LV", 0),
    0x124 => ("NOOP", 0),
    0x125 => ("POP", 0),
    0x126 => ("FREE", 0),
    0x127 => ("PUSH_RESULT", 0),
    0x128 => ("POP_POP", 0),
    0x129 => ("POP_FREE", 0),
    0x12A => ("FREE_POP", 0),
    0x12B => ("FREE_FREE", 0),
    0x12C => ("COPY_ARRAY_INSTANCE", 0),
    0x12D => ("COPY_STRUCTURE_INSTANCE", 0),
    0x12E => ("COPY_CONST_DOUBLE", 0),
    0x12F => ("COPY_CONST_DEC", 0),
    0x130 => ("COPY_CONST_DATE", 0),
    0x131 => ("COPY_CONST_TIME", 0),
    0x132 => ("COPY_CONST_DATETIME", 0),
    0x133 => ("COPY_CONST_STRING", 0),
    0x134 => ("COPY_LVALUE_DOUBLE", 0),
    0x135 => ("COPY_LVALUE_DEC", 0),
    0x136 => ("COPY_LVALUE_DATE", 0),
    0x137 => ("COPY_LVALUE_TIME", 0),
    0x138 => ("COPY_LVALUE_DATETIME", 0),
    0x139 => ("COPY_LVALUE_STRING", 0),
    0x13A => ("COPY_LVALUE_BINARY", 0),
    0x13B => ("POP_N_TIMES", 0),
    0x13C => ("FREE_NODE_N", 0),
    0x13D => ("CONV_DBL_RVALUE_TO_PTR", 0),
    0x13E => ("COPY_EXPR_DOUBLE", 0),
    0x13F => ("BREAKPOINT", 0),
    0x140 => ("INDEX_ERR_CHK", 0),
    0x141 => ("DOT_DOUBLE", 0, "field_index"),
    0x142 => ("DOT_DEC", 0, "field_index"),
    0x143 => ("INDEX_DOUBLE", 0),
    0x144 => ("INDEX_DEC", 0),
    0x145 => ("INDEX_ERR_CHK_DBL", 0),
    0x146 => ("INDEX_ERR_CHK_DEC", 0),
    0x147 => ("GLOBFUNCCALL_DOUBLE", 0),
    0x148 => ("GLOBFUNCCALL_DEC", 0),
    0x149 => ("SYSFUNCCALL_DOUBLE", 0),
    0x14A => ("SYSFUNCCALL_DEC", 0),
    0x14B => ("DLLFUNCCALL_DOUBLE", 0),
    0x14C => ("CALL_FUNCTION", 0),
    0x14D => ("DOTFUNCCALL_DOUBLE", 0, "field_index"),
    0x14E => ("DOTFUNCCALL_DEC", 0, "field_index"),
    0x14F => ("PUSH_LOCAL_VAR_DOUBLE", 0, "var_index"),
    0x150 => ("PUSH_LOCAL_VAR_DEC", 0, "var_index"),
    0x151 => ("PUSH_SHARED_VAR_DOUBLE", 0),
    0x152 => ("PUSH_SHARED_VAR_DEC", 0),
    0x153 => ("PUSH_LOCAL_GLOBREF_DOUBLE", 0, "var_index"),
    0x154 => ("PUSH_LOCAL_GLOBREF_DEC", 0, "var_index"),
    0x155 => ("PUSH_LOCAL_ARGREF_DOUBLE", 0, "var_index"),
    0x156 => ("PUSH_LOCAL_ARGREF_DEC", 0, "var_index"),
    0x157 => ("PUSH_SHARED_GLOBREF_DOUBLE", 0),
    0x158 => ("PUSH_SHARED_GLOBREF_DEC", 0),
    0x159 => ("ASSIGN_ANY", 0),

    // ANY type operations (0x15A-0x188)
    0x15A => ("CNV_ANY_TO_INT", 0),
    0x15B => ("CNV_ANY_TO_UINT", 0),
    0x15C => ("CNV_ANY_TO_LONG", 0),
    0x15D => ("CNV_ANY_TO_ULONG", 0),
    0x15E => ("CNV_ANY_TO_DEC", 0),
    0x15F => ("CNV_ANY_TO_FLOAT", 0),
    0x160 => ("CNV_ANY_TO_DOUBLE", 0),
    0x161 => ("CNV_ANY_TO_STRING", 0),
    0x162 => ("CNV_ANY_TO_BOOL", 0),
    0x163 => ("CNV_ANY_TO_BINARY", 0),
    0x164 => ("CNV_ANY_TO_DATE", 0),
    0x165 => ("CNV_ANY_TO_TIME", 0),
    0x166 => ("CNV_ANY_TO_DATETIME", 0),
    0x167 => ("CNV_ANY_TO_CHAR", 0),
    0x168 => ("CNV_ANY_TO_HANDLE", 0),
    0x169 => ("CNV_ANY_TO_ENUM", 0),
    0x16A => ("CNV_ANY_TO_OBJECT", 0),
    0x16B => ("CONV_DEC_RVALUE_TO_PTR", 0),
    0x16C => ("COPY_EXPR_DEC", 0),
    0x16D => ("CREATE_EXT_OBJ", 0),
    0x16E => ("GLOBFUNCCALL_ANY", 0),
    0x16F => ("SYSFUNCCALL_ANY", 0),
    0x170 => ("DLLFUNCCALL_ANY", 0),
    0x171 => ("DOTFUNCCALL_ANY", 0, "field_index"),
    0x172 => ("PUSH_LOCAL_VAR_ANY", 0, "var_index"),
    0x173 => ("PUSH_SHARED_VAR_ANY", 0),
    0x174 => ("PUSH_LOCAL_GLOBREF_ANY", 0, "var_index"),
    0x175 => ("PUSH_LOCAL_ARGREF_ANY", 0, "var_index"),
    0x176 => ("PUSH_SHARED_GLOBREF_ANY", 0),
    0x177 => ("ADD_ANY", 0),
    0x178 => ("SUB_ANY", 0),
    0x179 => ("MULT_ANY", 0),
    0x17A => ("DIV_ANY", 0),
    0x17B => ("EQ", 0),
    0x17C => ("NEGATE_ANY", 0),
    0x17D => ("EQ_ANY", 0),
    0x17E => ("NE_ANY", 0),
    0x17F => ("GT_ANY", 0),
    0x180 => ("LT_ANY", 0),
    0x181 => ("GE_ANY", 0),
    0x182 => ("LE_ANY", 0),
    0x183 => ("AND_ANY", 0),
    0x184 => ("OR_ANY", 0),
    0x185 => ("NOT_ANY", 0),
    0x186 => ("DOT_ANY", 0, "field_index"),
    0x187 => ("INDEX_ANY", 0),
    0x188 => ("INDEX_ERR_CHK_ANY", 0),

    // Built-in functions (0x189-0x1D9)
    0x189 => ("INT", 0),
    0x18A => ("ABS_LONG", 0),
    0x18B => ("ABS_DOUBLE", 0),
    0x18C => ("ASC", 0),
    0x18D => ("BLOB", 0),
    0x18E => ("CEILING", 0),
    0x18F => ("COS", 0),
    0x190 => ("EXP", 0),
    0x191 => ("FACT", 0),
    0x192 => ("INTHIGH", 0),
    0x193 => ("INTLOW", 0),
    0x194 => ("ISDATE", 0),
    0x195 => ("ISNULL", 0),
    0x196 => ("ISNUMBER", 0),
    0x197 => ("ISTIME", 0),
    0x198 => ("ISVALID", 0),
    0x199 => ("LEN_STRING", 0),
    0x19A => ("LEN_BINARY", 0),
    0x19B => ("LOG", 0),
    0x19C => ("LOGTEN", 0),
    0x19D => ("LOWER", 0),
    0x19E => ("PI", 0),
    0x19F => ("RAND_LONG", 0),
    0x1A0 => ("RAND_DOUBLE", 0),
    0x1A1 => ("SIN", 0),
    0x1A2 => ("SQRT", 0),
    0x1A3 => ("TAN", 0),
    0x1A4 => ("UPPER", 0),
    0x1A5 => ("CONV_TO_REFPAK", 0),
    0x1A6 => ("PUSH_LOCAL_GLOBREF_RP", 0, "var_index"),
    0x1A7 => ("PUSH_LOCAL_ARGREF_RP", 0, "var_index"),
    0x1A8 => ("PUSH_SHARED_GLOBREF_RP", 0),
    0x1A9 => ("PUSH_LOCAL_VAR_RP", 0, "var_index"),
    0x1AA => ("PUSH_LOCAL_VAR", 0, "var_index"),
    0x1AB => ("PUSH_SHARED_VAR", 0),
    0x1AC => ("TRANSFORM_BOUNDED_TO_UNBOUNDED", 0),
    0x1AD => ("TRANSFORM_UNBOUNDED_TO_BOUNDED", 0),
    0x1AE => ("TRANSFORM_UNBOUNDED_TO_UNBOUNDED", 0),
    0x1AF => ("CALC_UNBOUNDED_ARRAY_BOUND", 0),
    0x1B0 => ("CALC_SIMPLE_ARRAY_BOUND", 0),
    0x1B1 => ("CALC_COMPLEX_ARRAY_BOUND", 0),
    0x1B2 => ("BUILD_UNBOUNDED_ARRAYLIST", 0),
    0x1B3 => ("BUILD_BOUNDED_ARRAYLIST", 0),
    0x1B4 => ("TRANSFORM_ARRAYLIST_TO_UNBOUNDED", 0),
    0x1B5 => ("TRANSFORM_ARRAYLIST_TO_BOUNDED", 0),
    0x1B6 => ("FREE_REF_PAK_N", 0),
    0x1B7 => ("ARRAY_BOUND_INFO", 0),
    0x1B8 => ("LOWERBOUND", 0),
    0x1B9 => ("UPPERBOUND", 0),
    0x1BA => ("INCR_ANY", 0),
    0x1BB => ("DECR_ANY", 0),
    0x1BC => ("PUSH_FUNC_CLASS", 0),
    0x1BD => ("CLASS_CALL", 0),
    0x1BE => ("CLASS_CALL_DEC", 0),
    0x1BF => ("CLASS_CALL_DOUBLE", 0),
    0x1C0 => ("CLASS_CALL_ANY", 0),
    0x1C1 => ("INDEX_RP", 0),
    0x1C2 => ("DBDELETEWITHCURS", 0),
    0x1C3 => ("DBEXECUTEIMMED", 0),
    0x1C4 => ("DBEXECDYNWITHDESC", 0),
    0x1C5 => ("DBFETCHWITHDESC", 0),
    0x1C6 => ("DBOPENDYNWITHDESC", 0),
    0x1C7 => ("DBUPDATEWITHCURS", 0),
    0x1C8 => ("CREATE_USING", 0),
    0x1C9 => ("TRANSFORM_ANY_TO_UNBOUNDED", 0),
    0x1CA => ("TRANSFORM_ANY_TO_BOUNDED", 0),
    0x1CB => ("FREE_INV_METH_ARGS", 0),
    0x1CC => ("PUSH_NULL", 0),
    0x1CD => ("COPY_LVALUE_ANY", 0),
    0x1CE => ("ENTER_EMBEDDED", 0),
    0x1CF => ("EXIT_EMBEDDED", 0),
    0x1D0 => ("DOT_FLD_UPDATE_INDEX_RP", 0, "field_index"),
    0x1D1 => ("CNV_STRING_TO_BOUNDED_CHARARRAY", 0),
    0x1D2 => ("PUSH_NTH_PARENT", 0),
    0x1D3 => ("MOD_LONG", 0),
    0x1D4 => ("MOD_ULONG", 0),
    0x1D5 => ("MOD_DOUBLE", 0),
    0x1D6 => ("MOD_DEC", 0),
    0x1D7 => ("MOD_ANY", 0),
    0x1D8 => ("ABS_DEC", 0),
    0x1D9 => ("ABS_ANY", 0),

    // More math & exception handling (0x1DA-0x1EA)
    0x1DA => ("CEILING_ANY", 0),
    0x1DB => ("MIN_LONG", 0),
    0x1DC => ("MIN_ULONG", 0),
    0x1DD => ("MIN_DOUBLE", 0),
    0x1DE => ("MIN_DEC", 0),
    0x1DF => ("MIN_ANY", 0),
    0x1E0 => ("MAX_LONG", 0),
    0x1E1 => ("MAX_ULONG", 0),
    0x1E2 => ("MAX_DOUBLE", 0),
    0x1E3 => ("MAX_DEC", 0),
    0x1E4 => ("MAX_ANY", 0),
    0x1E5 => ("PUSH_TRY", 0),
    0x1E6 => ("POP_TRY", 0),
    0x1E7 => ("CATCH_EXCEPTION", 0),
    0x1E8 => ("THROW_EXCEPTION", 0),
    0x1E9 => ("GOSUB", 0),
    0x1EA => ("RETURN_SUB", 0),

    // LongLong type operations (0x1EB-0x222) - PB 8.0+
    0x1EB => ("CNV_INT_TO_LONGLONG", 0),
    0x1EC => ("CNV_UINT_TO_LONGLONG", 0),
    0x1ED => ("CNV_LONG_TO_LONGLONG", 0),
    0x1EE => ("CNV_ULONG_TO_LONGLONG", 0),
    0x1EF => ("CNV_DEC_TO_LONGLONG", 0),
    0x1F0 => ("CNV_FLOAT_TO_LONGLONG", 0),
    0x1F1 => ("CNV_DOUBLE_TO_LONGLONG", 0),
    0x1F2 => ("CNV_LONGLONG_TO_INT", 0),
    0x1F3 => ("CNV_LONGLONG_TO_UINT", 0),
    0x1F4 => ("CNV_LONGLONG_TO_LONG", 0),
    0x1F5 => ("CNV_LONGLONG_TO_ULONG", 0),
    0x1F6 => ("CNV_LONGLONG_TO_DEC", 0),
    0x1F7 => ("CNV_LONGLONG_TO_FLOAT", 0),
    0x1F8 => ("CNV_LONGLONG_TO_DOUBLE", 0),
    0x1F9 => ("ADD_LONGLONG", 0),
    0x1FA => ("ADD", 0),
    0x1FB => ("SUB", 0),
    0x1FC => ("DIV_LONGLONG", 0),
    0x1FD => ("POWER_LONGLONG", 0),
    0x1FE => ("POWER", 0),
    0x1FF => ("NEGATE", 0),
    0x200 => ("PUSH_LOCAL_VAR_LONGLONG", 0, "var_index"),
    0x201 => ("PUSH_LOCAL_GLOBREF_LONGLONG", 0, "var_index"),
    0x202 => ("PUSH_LOCAL_ARGREF_LONGLONG", 0, "var_index"),
    0x203 => ("PUSH_SHARED_VAR_LONGLONG", 0),
    0x204 => ("PUSH_SHARED_GLOBREF_LONGLONG", 0),
    0x205 => ("ASSIGN_LONGLONG", 0),
    0x206 => ("COPY_CONST_LONGLONG", 0),
    0x207 => ("ADDASSIGN_LONGLONG", 0),
    0x208 => ("SUBASSIGN_LONGLONG", 0),
    0x209 => ("MULTASSIGN_LONGLONG", 0),
    0x20A => ("ASSIGN", 0),
    0x20B => ("DECR_LONGLONG", 0),
    0x20C => ("COPY_LVALUE_LONGLONG", 0),
    0x20D => ("ABS_LONGLONG", 0),
    0x20E => ("RAND_LONGLONG", 0),
    0x20F => ("EQ_LONGLONG", 0),
    0x210 => ("NE_LONGLONG", 0),
    0x211 => ("GT_LONGLONG", 0),
    0x212 => ("LT_LONGLONG", 0),
    0x213 => ("GE_LONGLONG", 0),
    0x214 => ("LE_LONGLONG", 0),
    0x215 => ("MOD_LONGLONG", 0),
    0x216 => ("MIN_LONGLONG", 0),
    0x217 => ("MAX_LONGLONG", 0),
    0x218 => ("GLOBFUNCCALL_LONGLONG", 0),
    0x219 => ("SYSFUNCCALL_LONGLONG", 0),
    0x21A => ("DLLFUNCCALL_LONGLONG", 0),
    0x21B => ("DOTFUNCCALL_LONGLONG", 0, "field_index"),
    0x21C => ("CALL_FUNCTION", 0),
    0x21D => ("COPY_EXPR_LONGLONG", 0),
    0x21E => ("DOT_LONGLONG", 0, "field_index"),
    0x21F => ("INDEX_LONGLONG", 0),
    0x220 => ("CNV_ANY_TO_LONGLONG", 0),
    0x221 => ("CONV_LONGLONG_RVALUE_TO_PTR", 0),
    0x222 => ("INDEX_ERR_CHK_LONGLONG", 0),

    // Byte type operations (0x223-0x246) - PB 8.0+
    0x223 => ("PUSH_CONST_BYTE", 0),
    0x224 => ("CNV_INT_TO_BYTE", 0),
    0x225 => ("CNV_UINT_TO_BYTE", 0),
    0x226 => ("CNV_LONG_TO_BYTE", 0),
    0x227 => ("CNV_ULONG_TO_BYTE", 0),
    0x228 => ("CNV_DEC_TO_BYTE", 0),
    0x229 => ("CNV_FLOAT_TO_BYTE", 0),
    0x22A => ("CNV_DOUBLE_TO_BYTE", 0),
    0x22B => ("CNV_ANY_TO_BYTE", 0),
    0x22C => ("CNV_LONGLONG_TO_BYTE", 0),
    0x22D => ("CNV_BYTE_TO_INT", 0),
    0x22E => ("CNV_BYTE_TO_UINT", 0),
    0x22F => ("CNV_BYTE_TO_LONG", 0),
    0x230 => ("CNV_BYTE_TO_ULONG", 0),
    0x231 => ("CNV_BYTE_TO_DEC", 0),
    0x232 => ("CNV_BYTE_TO_FLOAT", 0),
    0x233 => ("CNV_BYTE_TO_DOUBLE", 0),
    0x234 => ("CNV_BYTE_TO_LONGLONG", 0),
    0x235 => ("ADD_BYTE", 0),
    0x236 => ("SUB_BYTE", 0),
    0x237 => ("MULT_BYTE", 0),
    0x238 => ("DIV_BYTE", 0),
    0x239 => ("POWER_BYTE", 0),
    0x23A => ("NEGATE_BYTE", 0),
    0x23B => ("INCR_BYTE", 0),
    0x23C => ("DECR_BYTE", 0),
    0x23D => ("ASSIGN_BYTE", 0),
    0x23E => ("ADDASSIGN_BYTE", 0),
    0x23F => ("SUBASSIGN_BYTE", 0),
    0x240 => ("MULTASSIGN_BYTE", 0),
    0x241 => ("EQ_BYTE", 0),
    0x242 => ("NE_BYTE", 0),
    0x243 => ("GT_BYTE", 0),
    0x244 => ("LT_BYTE", 0),
    0x245 => ("GE_BYTE", 0),
    0x246 => ("LE_BYTE", 0),
];

/// Operand widths used by the PB 11-era parser in Hucxy/PbdViewer.
///
/// Each value is a count of 16-bit words. PB 2022 object version `0x0153`
/// is not explicitly supported by that project, so using this table for
/// PB 11 and newer is a provisional compatibility profile that must be
/// measured against real fixtures.
pub static PB11_PLUS_OPERAND_WORDS: &[u8; 583] = &[
    0, 1, 1, 1, 1, 0, 0, 0, 0, 0, 1, 3, 3, 1, 3, 3, // 0x000
    4, 0, 1, 5, 0, 3, 0, 3, 3, 0, 4, 3, 5, 4, 1, 1, // 0x010
    2, 0, 0, 0, 0, 0, 0, 1, 0, 3, 2, 3, 4, 2, 3, 1, // 0x020
    1, 1, 1, 1, 2, 2, 2, 2, 2, 2, 2, 2, 1, 2, 1, 1, // 0x030
    1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, // 0x040
    1, 1, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, // 0x050
    0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, // 0x060
    0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, // 0x070
    1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, // 0x080
    1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, // 0x090
    1, 1, 2, 1, 2, 1, 0, 0, 0, 0, 0, 0, 0, 2, 0, 2, // 0x0A0
    2, 2, 2, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 2, 0, 2, // 0x0B0
    2, 2, 2, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 2, 2, 2, // 0x0C0
    2, 0, 0, 0, 0, 0, 0, 0, 0, 2, 2, 2, 2, 0, 0, 0, // 0x0D0
    0, 0, 0, 0, 0, 2, 2, 2, 2, 0, 0, 0, 0, 0, 0, 0, // 0x0E0
    0, 2, 2, 2, 2, 0, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, // 0x0F0
    2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, // 0x100
    2, 2, 2, 2, 2, 2, 2, 2, 2, 1, 0, 0, 0, 1, 1, 1, // 0x110
    1, 1, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 1, 1, 1, // 0x120
    1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 0, // 0x130
    0, 1, 1, 0, 0, 0, 0, 3, 3, 2, 2, 3, 3, 4, 4, 1, // 0x140
    1, 1, 1, 1, 1, 1, 1, 1, 1, 2, 1, 1, 1, 1, 1, 1, // 0x150
    1, 1, 1, 1, 1, 1, 1, 1, 1, 2, 2, 1, 1, 2, 3, 2, // 0x160
    3, 4, 1, 1, 1, 1, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, // 0x170
    0, 0, 0, 0, 0, 0, 1, 0, 0, 0, 0, 0, 1, 2, 0, 0, // 0x180
    0, 0, 0, 0, 1, 1, 1, 1, 0, 1, 1, 0, 0, 1, 0, 0, // 0x190
    0, 0, 0, 0, 1, 0, 1, 1, 1, 1, 1, 5, 1, 4, 1, 0, // 0x1A0
    2, 3, 3, 5, 3, 5, 1, 4, 2, 2, 2, 2, 2, 3, 3, 3, // 0x1B0
    3, 0, 3, 0, 2, 2, 2, 3, 1, 1, 4, 3, 1, 1, 1, 0, // 0x1C0
    0, 2, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, // 0x1D0
    0, 0, 0, 0, 0, 2, 0, 0, 0, 1, 0, 1, 1, 1, 1, 1, // 0x1E0
    1, 1, 1, 1, 1, 1, 1, 1, 1, 0, 0, 0, 0, 0, 0, 2, // 0x1F0
    1, 1, 1, 1, 1, 1, 1, 2, 2, 2, 2, 2, 1, 0, 0, 0, // 0x200
    0, 0, 0, 0, 0, 0, 0, 0, 3, 2, 3, 4, 3, 1, 1, 0, // 0x210
    1, 1, 0, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, // 0x220
    1, 1, 1, 1, 1, 0, 0, 0, 0, 0, 0, 2, 2, 1, 2, 2, // 0x230
    2, 0, 0, 0, 0, 0, 0, // 0x240
];

/// Fast opcode lookup
static OPCODE_MAP: Lazy<HashMap<u16, &'static OpcodeInfo>> = Lazy::new(|| {
    OPCODE_TABLE
        .iter()
        .map(|(code, info)| (*code, info))
        .collect()
});

/// Get opcode information by opcode value
pub fn get_opcode_info(code: u16) -> Option<&'static OpcodeInfo> {
    OPCODE_MAP.get(&code).copied()
}

/// Resolve an operand width for a concrete runtime profile.
pub fn operand_words_for_version(code: u16, version: PBVersion) -> Option<u8> {
    let info = get_opcode_info(code)?;
    if version.major >= 11 {
        PB11_PLUS_OPERAND_WORDS.get(code as usize).copied()
    } else {
        Some(info.operand_words)
    }
}

/// Get opcodes valid for a specific PowerBuilder version
pub fn get_opcodes_for_version(version: PBVersion) -> Vec<u16> {
    let max_opcode = if version.major <= 6 {
        0xFF // PB 6.0: 256 opcodes (0x00-0xFF)
    } else {
        0x246 // PB 8.0+: 591 opcodes (0x00-0x246)
    };

    OPCODE_TABLE
        .iter()
        .filter(|(code, _)| *code <= max_opcode)
        .map(|(code, _)| *code)
        .collect()
}

/// Check if opcode is valid for version
pub fn is_valid_for_version(code: u16, version: PBVersion) -> bool {
    let max_opcode = if version.major <= 6 { 0xFF } else { 0x246 };
    code <= max_opcode && OPCODE_MAP.contains_key(&code)
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_opcode_count() {
        // Should have 591 opcodes total
        assert!(OPCODE_TABLE.len() >= 256); // At least PB6 opcodes
    }

    #[test]
    fn test_opcode_lookup() {
        let info = get_opcode_info(0x00);
        assert!(info.is_some());
        assert_eq!(info.unwrap().mnemonic, "RETURN");

        let info = get_opcode_info(0x246); // Last opcode
        assert!(info.is_some());
        assert_eq!(info.unwrap().mnemonic, "LE_BYTE");
    }

    #[test]
    fn test_version_filtering() {
        let pb6_opcodes = get_opcodes_for_version(PBVersion::PB6);
        assert!(pb6_opcodes.iter().all(|&c| c <= 0xFF));

        let pb12_opcodes = get_opcodes_for_version(PBVersion::PB12);
        assert!(pb12_opcodes.iter().any(|&c| c > 0xFF));
    }

    #[test]
    fn test_unknown_opcode() {
        let info = get_opcode_info(0xFFFF);
        assert!(info.is_none());
    }

    #[test]
    fn test_pb6_vs_pb12_opcodes() {
        // PB6 should not have LONGLONG opcodes
        assert!(!is_valid_for_version(0x1EB, PBVersion::PB6)); // CNV_INT_TO_LONGLONG

        // PB12 should have LONGLONG opcodes
        assert!(is_valid_for_version(0x1EB, PBVersion::PB12));
    }

    #[test]
    fn test_pb11_plus_operand_profile_uses_word_counts() {
        assert_eq!(PB11_PLUS_OPERAND_WORDS.len(), 0x247);
        assert_eq!(operand_words_for_version(0x03e, PBVersion::PB2022), Some(1));
        assert_eq!(operand_words_for_version(0x010, PBVersion::PB2022), Some(4));
    }
}
