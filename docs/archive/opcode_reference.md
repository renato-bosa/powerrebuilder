# PowerBuilder P-code Opcode Reference

Version: 2.0

Comprehensive PowerBuilder P-code opcode reference from multiple sources

## Sources

- **pbdviewer**: https://github.com/hucxy/pbdviewer
- **powerbuilder-decompile**: https://github.com/sijms/powerbuilder-decompile
- **sime-finch**: Verified opcodes from reference extraction

## Statistics

- Total opcodes: 583
- Operation types: 1
- Type variants: 62

## Opcode Listing

| Opcode | Name | Length | Category | Stack Effect | Confidence |
|--------|------|--------|----------|--------------|------------|
| 0x00 | RETURN | 1 | sm | 0 -> 0 | high |
| 0x01 | STORE_RETURN_VAL | 2 | sm | 2 -> 0 | medium |
| 0x02 | JUMPTRUE | 2 | sm | 1 -> 0 | medium |
| 0x03 | JUMPFALSE | 2 | sm | 1 -> 0 | medium |
| 0x04 | JUMP | 2 | sm | 1 -> 0 | high |
| 0x05 | DBSTART | 1 | sm | 1 -> 0 | medium |
| 0x06 | DBCOMMIT | 1 | sm | 1 -> 0 | medium |
| 0x07 | DBROLLBACK | 1 | sm | 1 -> 0 | medium |
| 0x08 | DBSTOP | 1 | sm | 1 -> 0 | medium |
| 0x09 | DBCLOSE | 1 | sm | 3 -> 0 | medium |
| 0x0A | DBOPEN | 2 | sm | 3 -> 0 | medium |
| 0x0B | DBDELETE | 4 | sm | 2 -> 0 | medium |
| 0x0C | DBUPDATE | 4 | sm | 2 -> 0 | medium |
| 0x0D | DBEXECUTE | 2 | sm | - | medium |
| 0x0E | DBFETCH | 4 | sm | 3 -> 0 | medium |
| 0x0F | DBINSERT | 4 | sm | 2 -> 0 | medium |
| 0x10 | DBSELECT | 5 | sm | 3 -> 0 | medium |
| 0x11 | DESTROY | 1 | sm | 1 -> 0 | medium |
| 0x12 | HALT | 1 | sm | - | high |
| 0x13 | EVENTCALL | 6 | sm | 6 -> 10 | medium |
| 0x14 | LVALUE_EXPR | 1 | sm | 1 -> 0 | medium |
| 0x15 | DBEXECUTEDYN | 4 | sm | - | medium |
| 0x16 | DBPREPARE | 1 | sm | 5 -> 0 | medium |
| 0x17 | DBOPENDYN | 4 | sm | 2 -> 0 | medium |
| 0x18 | DBEXECDYNPROC | 4 | sm | - | medium |
| 0x19 | DBDESCRIBE | 1 | sm | - | medium |
| 0x1A | DBSELECTBLOB | 5 | sm | 3 -> 0 | medium |
| 0x1B | DBUPDATEBLOB | 4 | sm | 2 -> 0 | medium |
| 0x1C | DBSELECTCLOB | 6 | sm | 3 -> 0 | medium |
| 0x1D | DBUPDATECLOB | 5 | sm | 2 -> 0 | medium |
| 0x1E | PUSH_LOCAL_VAR | 2 | sm | 0 -> 4 | medium |
| 0x1F | PUSH_SHARED_VAR | 2 | sm | - | medium |
| 0x20 | PUSH_CONST_REF | 3 | sm | 0 -> 12 | medium |
| 0x21 | PUSH_THIS | 1 | sm | 0 -> 1 | medium |
| 0x22 | PUSH_PARENT | 1 | sm | 0 -> 1 | medium |
| 0x23 | PUSH_PRIMARY | 1 | sm | - | medium |
| 0x24 | AND | 1 | sm | 2 -> 1 | medium |
| 0x25 | OR | 1 | sm | 2 -> 1 | medium |
| 0x26 | NOT | 1 | sm | 1 -> 1 | medium |
| 0x27 | DOT | 2 | sm | 2 -> 1 | medium |
| 0x28 | INDEX | 1 | sm | 2 -> 1 | medium |
| 0x29 | GLOBFUNCCALL | 3 | sm | - | medium |
| 0x2A | CALL_FUNCTION | 2 | sm | - | medium |
| 0x2B | DLLFUNCCALL | 3 | sm | - | medium |
| 0x2C | DOTFUNCCALL | 3 | sm | 6 -> 10 | medium |
| 0x2D | PUSH_GLOBAL_VAR | 3 | sm | 0 -> 1 | medium |
| 0x2E | ARRAYLIST | 3 | sm | - | medium |
| 0x2F | PUSH_SHARED_VAR | 2 | sm | 0 -> 4 | medium |
| 0x30 | PUSH_LOCAL_ARGREF | 2 | sm | 0 -> 4 | medium |
| 0x31 | PUSH_SHARED_GLOBREF | 2 | sm | - | medium |
| 0x32 | PUSH_CONST_INT | 2 | sm | 0 -> 12 | medium |
| 0x33 | PUSH_CONST_UINT | 2 | sm | 0 -> 12 | medium |
| 0x34 | PUSH_CONST_LONG | 2 | sm | 0 -> 12 | medium |
| 0x35 | PUSH_CONST_ULONG | 2 | sm | 0 -> 12 | medium |
| 0x36 | PUSH_CONST_DEC | 2 | sm | 0 -> 12 | medium |
| 0x37 | PUSH_CONST_FLOAT | 2 | sm | - | medium |
| 0x38 | PUSH_CONST_DOUBLE | 2 | sm | 0 -> 12 | medium |
| 0x39 | PUSH_CONST_TIME | 2 | sm | - | medium |
| 0x3A | PUSH_CONST_DATE | 2 | sm | - | medium |
| 0x3B | PUSH_CONST_STRING | 2 | sm | 0 -> 12 | medium |
| 0x3C | PUSH_CONST_BOOL | 2 | sm | 0 -> 12 | medium |
| 0x3D | PUSH_CONST_ENUM | 2 | sm | 0 -> 1 | medium |
| 0x3E | CNV_INT_TO_UINT | 1 | sm | 0 -> 0 | medium |
| 0x3F | CNV_INT_TO_LONG | 1 | sm | 0 -> 0 | medium |
| 0x40 | CNV_INT_TO_ULONG | 1 | sm | 0 -> 0 | medium |
| 0x41 | CNV_INT_TO_DEC | 1 | sm | 0 -> 0 | medium |
| 0x42 | CNV_INT_TO_FLOAT | 1 | sm | 0 -> 0 | medium |
| 0x43 | CNV_INT_TO_DOUBLE | 1 | sm | 0 -> 0 | medium |
| 0x44 | CNV_UINT_TO_LONG | 1 | sm | 0 -> 0 | medium |
| 0x45 | CNV_UINT_TO_ULONG | 1 | sm | 0 -> 0 | medium |
| 0x46 | CNV_UINT_TO_DEC | 1 | sm | 0 -> 0 | medium |
| 0x47 | CNV_UINT_TO_FLOAT | 1 | sm | 0 -> 0 | medium |
| 0x48 | CNV_UINT_TO_DOUBLE | 1 | sm | 0 -> 0 | medium |
| 0x49 | CNV_LONG_TO_ULONG | 1 | sm | 0 -> 0 | medium |
| 0x4A | CNV_LONG_TO_DEC | 1 | sm | 0 -> 0 | medium |
| 0x4B | CNV_LONG_TO_FLOAT | 1 | sm | 0 -> 0 | medium |
| 0x4C | CNV_LONG_TO_DOUBLE | 1 | sm | 0 -> 0 | medium |
| 0x4D | CNV_ULONG_TO_DEC | 1 | sm | 0 -> 0 | medium |
| 0x4E | CNV_ULONG_TO_FLOAT | 1 | sm | 0 -> 0 | medium |
| 0x4F | CNV_ULONG_TO_DOUBLE | 1 | sm | 0 -> 0 | medium |
| 0x50 | CNV_DEC_TO_FLOAT | 1 | sm | 0 -> 0 | medium |
| 0x51 | CNV_DEC_TO_DOUBLE | 1 | sm | 0 -> 0 | medium |
| 0x52 | CNV_FLOAT_TO_DOUBLE | 1 | sm | 0 -> 0 | medium |
| 0x53 | ADD_INT | 1 | sm | 2 -> 1 | medium |
| 0x54 | ADD_UINT | 1 | sm | 2 -> 1 | medium |
| 0x55 | ADD_LONG | 1 | sm | 2 -> 1 | medium |
| 0x56 | ADD_ULONG | 1 | sm | 2 -> 1 | medium |
| 0x57 | ADD_DEC | 1 | sm | 2 -> 1 | medium |
| 0x58 | ADD_FLOAT | 1 | sm | 2 -> 1 | medium |
| 0x59 | ADD_DOUBLE | 1 | sm | 2 -> 1 | medium |
| 0x5A | SUB_INT | 1 | sm | 2 -> 1 | medium |
| 0x5B | SUB_UINT | 1 | sm | 2 -> 1 | medium |
| 0x5C | SUB_LONG | 1 | sm | 2 -> 1 | medium |
| 0x5D | SUB_ULONG | 1 | sm | 2 -> 1 | medium |
| 0x5E | SUB | 1 | sm | 2 -> 1 | medium |
| 0x5F | SUB_FLOAT | 1 | sm | 2 -> 1 | medium |
| 0x60 | SUB_DOUBLE | 1 | sm | 2 -> 1 | medium |
| 0x61 | MULT_INT | 1 | sm | 2 -> 1 | medium |
| 0x62 | MULT_UINT | 1 | sm | 2 -> 1 | medium |
| 0x63 | MULT_LONG | 1 | sm | 2 -> 1 | medium |
| 0x64 | MULT_ULONG | 1 | sm | 2 -> 1 | medium |
| 0x65 | MULT_DEC | 1 | sm | 2 -> 1 | medium |
| 0x66 | MULT_FLOAT | 1 | sm | 2 -> 1 | medium |
| 0x67 | MULT_DOUBLE | 1 | sm | 2 -> 1 | medium |
| 0x68 | DIV_INT | 1 | sm | 2 -> 1 | medium |
| 0x69 | DIV_UINT | 1 | sm | 2 -> 1 | medium |
| 0x6A | DIV_LONG | 1 | sm | 2 -> 1 | medium |
| 0x6B | DIV_ULONG | 1 | sm | 2 -> 1 | medium |
| 0x6C | DIV | 1 | sm | 2 -> 1 | medium |
| 0x6D | DIV_FLOAT | 1 | sm | 2 -> 1 | medium |
| 0x6E | DIV_DOUBLE | 1 | sm | 2 -> 1 | medium |
| 0x6F | POWER_INT | 1 | sm | 2 -> 1 | medium |
| 0x70 | POWER_UINT | 1 | sm | 2 -> 1 | medium |
| 0x71 | POWER_LONG | 1 | sm | 2 -> 1 | medium |
| 0x72 | POWER_ULONG | 1 | sm | 2 -> 1 | medium |
| 0x73 | POWER_DEC | 1 | sm | 2 -> 1 | medium |
| 0x74 | POWER_FLOAT | 1 | sm | 2 -> 1 | medium |
| 0x75 | POWER_DOUBLE | 1 | sm | 2 -> 1 | medium |
| 0x76 | NEGATE_INT | 1 | sm | 1 -> 3 | medium |
| 0x77 | NEGATE_UINT | 1 | sm | 1 -> 3 | medium |
| 0x78 | NEGATE_LONG | 1 | sm | 1 -> 3 | medium |
| 0x79 | NEGATE_ULONG | 1 | sm | 1 -> 3 | medium |
| 0x7A | NEGATE_DEC | 1 | sm | 1 -> 3 | medium |
| 0x7B | NEGATE_FLOAT | 1 | sm | 1 -> 3 | medium |
| 0x7C | ADD | 1 | sm | 1 -> 3 | medium |
| 0x7D | CAT_STRING | 1 | sm | 2 -> 1 | medium |
| 0x7E | CAT_BINARY | 1 | sm | 2 -> 1 | medium |
| 0x7F | ASSIGN_ARRAY | 1 | sm | 2 -> 0 | medium |
| 0x80 | ASSIGN_INT | 2 | sm | 2 -> 0 | medium |
| 0x81 | ASSIGN_UINT | 2 | sm | 2 -> 0 | medium |
| 0x82 | ASSIGN_LONG | 2 | sm | 2 -> 0 | medium |
| 0x83 | ASSIGN_ULONG | 2 | sm | 2 -> 0 | medium |
| 0x84 | ASSIGN_DEC | 2 | sm | 2 -> 0 | medium |
| 0x85 | ASSIGN_FLOAT | 2 | sm | 2 -> 0 | medium |
| 0x86 | ASSIGN_DOUBLE | 2 | sm | 2 -> 0 | medium |
| 0x87 | ASSIGN_BLOB | 2 | sm | 2 -> 0 | medium |
| 0x88 | ASSIGN_STRING | 2 | sm | 2 -> 0 | medium |
| 0x89 | ASSIGN_TIME | 2 | sm | 2 -> 0 | medium |
| 0x8A | ASSIGN_OBINST | 2 | sm | 2 -> 0 | medium |
| 0x8B | ASSIGN_ANCESTOR | 2 | sm | 2 -> 0 | medium |
| 0x8C | ASSIGN_ENUM | 2 | sm | 2 -> 0 | medium |
| 0x8D | CNV_UINT_TO_INT | 1 | sm | 0 -> 0 | medium |
| 0x8E | CNV_LONG_TO_INT | 1 | sm | 0 -> 0 | medium |
| 0x8F | CNV_ULONG_TO_INT | 1 | sm | 0 -> 0 | medium |
| 0x90 | CNV_DEC_TO_INT | 1 | sm | 1 -> 1 | medium |
| 0x91 | CNV_FLOAT_TO_INT | 1 | sm | 1 -> 1 | medium |
| 0x92 | CNV_DOUBLE_TO_INT | 1 | sm | 1 -> 1 | medium |
| 0x93 | CNV_LONG_TO_UINT | 1 | sm | 0 -> 0 | medium |
| 0x94 | CNV_ULONG_TO_UINT | 1 | sm | 0 -> 0 | medium |
| 0x95 | CNV_DEC_TO_UINT | 1 | sm | 1 -> 1 | medium |
| 0x96 | CNV_FLOAT_TO_UINT | 1 | sm | 1 -> 1 | medium |
| 0x97 | CNV_DOUBLE_TO_UINT | 1 | sm | 1 -> 1 | medium |
| 0x98 | CNV_ULONG_TO_LONG | 1 | sm | 0 -> 0 | medium |
| 0x99 | CNV_DEC_TO_LONG | 1 | sm | 1 -> 1 | medium |
| 0x9A | CNV_FLOAT_TO_LONG | 1 | sm | 1 -> 1 | medium |
| 0x9B | CNV_DOUBLE_TO_LONG | 1 | sm | 1 -> 1 | medium |
| 0x9C | CNV_DEC_TO_ULONG | 1 | sm | 1 -> 1 | medium |
| 0x9D | CNV_FLOAT_TO_ULONG | 1 | sm | 1 -> 1 | medium |
| 0x9E | CNV_DOUBLE_TO_ULONG | 1 | sm | 1 -> 1 | medium |
| 0x9F | CNV_FLOAT_TO_DEC | 1 | sm | 0 -> 0 | medium |
| 0xA0 | CNV_DOUBLE_TO_DEC | 1 | sm | 0 -> 0 | medium |
| 0xA1 | CNV_DOUBLE_TO_FLOAT | 1 | sm | 0 -> 0 | medium |
| 0xA2 | CNV_STRING_TO_CHAR | 1 | sm | 0 -> 0 | medium |
| 0xA3 | CNV_CHAR_TO_STRING | 1 | sm | 0 -> 0 | medium |
| 0xA4 | CNV_STRING_TO_CHARARRAY | 1 | sm | - | medium |
| 0xA5 | CNV_CHARARRAY_TO_STRING | 1 | sm | - | medium |
| 0xA6 | EQ_INT | 1 | sm | 2 -> 1 | medium |
| 0xA7 | EQ_UINT | 1 | sm | 2 -> 1 | medium |
| 0xA8 | EQ_LONG | 1 | sm | 2 -> 1 | medium |
| 0xA9 | EQ_ULONG | 1 | sm | 2 -> 1 | medium |
| 0xAA | EQ_DEC | 1 | sm | 2 -> 1 | medium |
| 0xAB | EQ_FLOAT | 1 | sm | 2 -> 1 | medium |
| 0xAC | EQ_DOUBLE | 1 | sm | 2 -> 1 | medium |
| 0xAD | EQ_STRING | 1 | sm | 2 -> 1 | medium |
| 0xAE | EQ_BOOL | 1 | sm | 2 -> 1 | medium |
| 0xAF | EQ_BINARY | 1 | sm | 2 -> 1 | medium |
| 0xB0 | EQ_TIME | 1 | sm | 2 -> 1 | medium |
| 0xB1 | EQ_DATE | 1 | sm | 2 -> 1 | medium |
| 0xB2 | EQ_DATETIME | 1 | sm | 2 -> 1 | medium |
| 0xB3 | EQ_CHAR | 1 | sm | 2 -> 1 | medium |
| 0xB4 | EQ_OBINST | 1 | sm | - | medium |
| 0xB5 | EQ_ENUM | 1 | sm | 2 -> 1 | medium |
| 0xB6 | NE_INT | 1 | sm | 2 -> 1 | medium |
| 0xB7 | NE_UINT | 1 | sm | 2 -> 1 | medium |
| 0xB8 | NE_LONG | 1 | sm | 2 -> 1 | medium |
| 0xB9 | NE_ULONG | 1 | sm | 2 -> 1 | medium |
| 0xBA | NE_DEC | 1 | sm | 2 -> 1 | medium |
| 0xBB | NE_FLOAT | 1 | sm | 2 -> 1 | medium |
| 0xBC | NE_DOUBLE | 1 | sm | 2 -> 1 | medium |
| 0xBD | NE_STRING | 1 | sm | 2 -> 1 | medium |
| 0xBE | NE_BOOL | 1 | sm | 2 -> 1 | medium |
| 0xBF | NE_BINARY | 1 | sm | 2 -> 1 | medium |
| 0xC0 | NE_TIME | 1 | sm | 2 -> 1 | medium |
| 0xC1 | NE_DATE | 1 | sm | 2 -> 1 | medium |
| 0xC2 | NE_DATETIME | 1 | sm | 2 -> 1 | medium |
| 0xC3 | NE_CHAR | 1 | sm | 2 -> 1 | medium |
| 0xC4 | NE_OBINST | 1 | sm | 2 -> 1 | medium |
| 0xC5 | NE_ENUM | 1 | sm | 2 -> 1 | medium |
| 0xC6 | GT_INT | 1 | sm | 2 -> 1 | medium |
| 0xC7 | GT_UINT | 1 | sm | 2 -> 1 | medium |
| 0xC8 | GT_LONG | 1 | sm | 2 -> 1 | medium |
| 0xC9 | GT_ULONG | 1 | sm | 2 -> 1 | medium |
| 0xCA | GT_DEC | 1 | sm | 2 -> 1 | medium |
| 0xCB | GT_FLOAT | 1 | sm | 2 -> 1 | medium |
| 0xCC | GT_DOUBLE | 1 | sm | 2 -> 1 | medium |
| 0xCD | GT_STRING | 1 | sm | 2 -> 1 | medium |
| 0xCE | GT_TIME | 1 | sm | 2 -> 1 | medium |
| 0xCF | GT | 1 | sm | 2 -> 1 | medium |
| 0xD0 | GT_DATETIME | 1 | sm | 2 -> 1 | medium |
| 0xD1 | GT_CHAR | 1 | sm | 2 -> 1 | medium |
| 0xD2 | LT_INT | 1 | sm | 2 -> 1 | medium |
| 0xD3 | LT_UINT | 1 | sm | 2 -> 1 | medium |
| 0xD4 | LT_LONG | 1 | sm | 2 -> 1 | medium |
| 0xD5 | LT_ULONG | 1 | sm | 2 -> 1 | medium |
| 0xD6 | LT_DEC | 1 | sm | 2 -> 1 | medium |
| 0xD7 | LT_FLOAT | 1 | sm | 2 -> 1 | medium |
| 0xD8 | LT_DOUBLE | 1 | sm | 2 -> 1 | medium |
| 0xD9 | LT_STRING | 1 | sm | 2 -> 1 | medium |
| 0xDA | LT_TIME | 1 | sm | 2 -> 1 | medium |
| 0xDB | LT_DATE | 1 | sm | 2 -> 1 | medium |
| 0xDC | LT_DATETIME | 1 | sm | 2 -> 1 | medium |
| 0xDD | LT_CHAR | 1 | sm | 2 -> 1 | medium |
| 0xDE | GE_INT | 1 | sm | 2 -> 1 | medium |
| 0xDF | GE_UINT | 1 | sm | 2 -> 1 | medium |
| 0xE0 | GE_LONG | 1 | sm | 2 -> 1 | medium |
| 0xE1 | GE_ULONG | 1 | sm | 2 -> 1 | medium |
| 0xE2 | GE_DEC | 1 | sm | 2 -> 1 | medium |
| 0xE3 | GE_FLOAT | 1 | sm | 2 -> 1 | medium |
| 0xE4 | GE_DOUBLE | 1 | sm | 2 -> 1 | medium |
| 0xE5 | GE_STRING | 1 | sm | 2 -> 1 | medium |
| 0xE6 | GE_TIME | 1 | sm | 2 -> 1 | medium |
| 0xE7 | GE | 1 | sm | 2 -> 1 | medium |
| 0xE8 | GE_DATETIME | 1 | sm | 2 -> 1 | medium |
| 0xE9 | GE_CHAR | 1 | sm | 2 -> 1 | medium |
| 0xEA | LE_INT | 1 | sm | 2 -> 1 | medium |
| 0xEB | LE_UINT | 1 | sm | 2 -> 1 | medium |
| 0xEC | LE_LONG | 1 | sm | 2 -> 1 | medium |
| 0xED | LE_ULONG | 1 | sm | 2 -> 1 | medium |
| 0xEE | LE_DEC | 1 | sm | 2 -> 1 | medium |
| 0xEF | LE_FLOAT | 1 | sm | 2 -> 1 | medium |
| 0xF0 | LE_DOUBLE | 1 | sm | 2 -> 1 | medium |
| 0xF1 | LE_STRING | 1 | sm | 2 -> 1 | medium |
| 0xF2 | LE_TIME | 1 | sm | 2 -> 1 | medium |
| 0xF3 | LE | 1 | sm | 2 -> 1 | medium |
| 0xF4 | LE_DATETIME | 1 | sm | 2 -> 1 | medium |
| 0xF5 | LE_CHAR | 1 | sm | 2 -> 1 | medium |
| 0xF6 | INCR_INT | 1 | sm | 1 -> 0 | medium |
| 0xF7 | INCR_UINT | 1 | sm | 1 -> 0 | medium |
| 0xF8 | INCR_LONG | 1 | sm | 1 -> 0 | medium |
| 0xF9 | INCR_ULONG | 1 | sm | 1 -> 0 | medium |
| 0xFA | INCR_DEC | 1 | sm | 1 -> 0 | medium |
| 0xFB | INCR_FLOAT | 1 | sm | 1 -> 0 | medium |
| 0xFC | INCR_DOUBLE | 1 | sm | 1 -> 0 | medium |
| 0xFD | DECR_INT | 1 | sm | 1 -> 0 | medium |
| 0xFE | DECR_UINT | 1 | sm | 1 -> 0 | medium |
| 0xFF | DECR_LONG | 1 | sm | 1 -> 0 | medium |
| 0x100 | DECR_ULONG | 1 | sm | 1 -> 0 | medium |
| 0x101 | DECR_DEC | 1 | sm | 1 -> 0 | medium |
| 0x102 | DECR_FLOAT | 1 | sm | 1 -> 0 | medium |
| 0x103 | DECR_DOUBLE | 1 | sm | 1 -> 0 | medium |
| 0x104 | ADDASSIGN_INT | 1 | sm | 2 -> 0 | medium |
| 0x105 | ADDASSIGN_UINT | 1 | sm | 2 -> 0 | medium |
| 0x106 | ADDASSIGN_LONG | 1 | sm | 2 -> 0 | medium |
| 0x107 | ADDASSIGN_ULONG | 1 | sm | 2 -> 0 | medium |
| 0x108 | ADDASSIGN_DEC | 1 | sm | 2 -> 0 | medium |
| 0x109 | ADDASSIGN_FLOAT | 1 | sm | 2 -> 0 | medium |
| 0x10A | ADDASSIGN_DOUBLE | 1 | sm | 2 -> 0 | medium |
| 0x10B | SUBASSIGN_INT | 1 | sm | 2 -> 0 | medium |
| 0x10C | SUBASSIGN_UINT | 1 | sm | 2 -> 0 | medium |
| 0x10D | SUBASSIGN_LONG | 1 | sm | 2 -> 0 | medium |
| 0x10E | SUBASSIGN_ULONG | 1 | sm | 2 -> 0 | medium |
| 0x10F | ASSIGN | 1 | sm | 2 -> 0 | medium |
| 0x110 | SUBASSIGN_FLOAT | 1 | sm | 2 -> 0 | medium |
| 0x111 | SUBASSIGN_DOUBLE | 1 | sm | 2 -> 0 | medium |
| 0x112 | MULTASSIGN_INT | 1 | sm | 2 -> 0 | medium |
| 0x113 | MULTASSIGN_UINT | 1 | sm | 2 -> 0 | medium |
| 0x114 | MULTASSIGN_LONG | 1 | sm | 2 -> 0 | medium |
| 0x115 | MULTASSIGN_ULONG | 1 | sm | 2 -> 0 | medium |
| 0x116 | MULTASSIGN_DEC | 1 | sm | 2 -> 0 | medium |
| 0x117 | MULTASSIGN_FLOAT | 1 | sm | 2 -> 0 | medium |
| 0x118 | MULTASSIGN_DOUBLE | 1 | sm | 2 -> 0 | medium |
| 0x119 | DUP_STACKED_LVALUE | 1 | sm | 0 -> 0 | medium |
| 0x11A | EQ_ARRAY | 1 | sm | 2 -> 1 | medium |
| 0x11B | BEGIN_ASSIGN | 1 | sm | 2 -> 1 | medium |
| 0x11C | CONV_TO_LVALUE | 1 | sm | 0 -> 0 | medium |
| 0x11D | BEGIN_ASSIGN | 1 | sm | 0 -> 4 | medium |
| 0x11E | PUSH_SHARED_VAR_LV | 1 | sm | 0 -> 4 | medium |
| 0x11F | PUSH_LOCAL_GLOBREF_LV | 1 | sm | 0 -> 4 | medium |
| 0x120 | PUSH_LOCAL_ARGREF_LV | 1 | sm | 0 -> 4 | medium |
| 0x121 | PUSH_SHARED_GLOBREF_LV | 1 | sm | - | medium |
| 0x122 | DOT_LV | 1 | sm | 2 -> 1 | medium |
| 0x123 | INDEX_LV | 1 | sm | 2 -> 1 | medium |
| 0x124 | NOOP | 1 | sm | - | medium |
| 0x125 | POP | 1 | sm | - | medium |
| 0x126 | FREE | 1 | sm | - | medium |
| 0x127 | PUSH_RESULT | 1 | sm | 0 -> 0 | medium |
| 0x128 | POP_POP | 1 | sm | 0 -> 0 | medium |
| 0x129 | POP_FREE | 1 | sm | 0 -> 0 | medium |
| 0x12A | FREE_POP | 1 | sm | 0 -> 0 | medium |
| 0x12B | FREE_FREE | 1 | sm | 0 -> 0 | medium |
| 0x12C | COPY_ARRAY_INSTANCE | 1 | sm | 0 -> 0 | medium |
| 0x12D | COPY_STRUCTURE_INSTANCE | 1 | sm | 0 -> 0 | medium |
| 0x12E | COPY_CONST_DOUBLE | 1 | sm | 0 -> 0 | medium |
| 0x12F | COPY_CONST_DEC | 1 | sm | 0 -> 0 | medium |
| 0x130 | COPY_CONST_DATE | 1 | sm | 0 -> 0 | medium |
| 0x131 | COPY_CONST_TIME | 1 | sm | 0 -> 0 | medium |
| 0x132 | COPY_CONST_DATETIME | 1 | sm | 0 -> 0 | medium |
| 0x133 | COPY_CONST_STRING | 1 | sm | 0 -> 0 | medium |
| 0x134 | COPY_LVALUE_DOUBLE | 1 | sm | 0 -> 0 | medium |
| 0x135 | COPY_LVALUE_DEC | 1 | sm | 2 -> 1 | medium |
| 0x136 | COPY_LVALUE_DATE | 1 | sm | 2 -> 1 | medium |
| 0x137 | COPY_LVALUE_TIME | 1 | sm | 2 -> 1 | medium |
| 0x138 | COPY_LVALUE_DATETIME | 1 | sm | 2 -> 1 | medium |
| 0x139 | COPY_LVALUE_STRING | 1 | sm | 0 -> 0 | medium |
| 0x13A | COPY_LVALUE_BINARY | 1 | sm | 2 -> 1 | medium |
| 0x13B | POP_N_TIMES | 1 | sm | 0 -> 0 | medium |
| 0x13C | FREE_NODE_N | 1 | sm | 0 -> 0 | medium |
| 0x13D | CONV_DBL_RVALUE_TO_PTR | 1 | sm | 0 -> 0 | medium |
| 0x13E | COPY_EXPR_DOUBLE | 1 | sm | 0 -> 0 | medium |
| 0x13F | BREAKPOINT | 1 | sm | - | medium |
| 0x140 | INDEX_ERR_CHK | 1 | sm | 2 -> 1 | medium |
| 0x141 | DOT_DOUBLE | 1 | sm | 2 -> 1 | medium |
| 0x142 | DOT_DEC | 1 | sm | 2 -> 1 | medium |
| 0x143 | INDEX_DOUBLE | 1 | sm | 2 -> 1 | medium |
| 0x144 | INDEX_DEC | 1 | sm | 2 -> 1 | medium |
| 0x145 | INDEX_ERR_CHK_DBL | 1 | sm | 2 -> 1 | medium |
| 0x146 | INDEX_ERR_CHK_DEC | 1 | sm | 2 -> 1 | medium |
| 0x147 | GLOBFUNCCALL_DOUBLE | 1 | sm | - | medium |
| 0x148 | GLOBFUNCCALL_DEC | 1 | sm | - | medium |
| 0x149 | SYSFUNCCALL_DOUBLE | 1 | sm | - | medium |
| 0x14A | SYSFUNCCALL_DEC | 1 | sm | - | medium |
| 0x14B | DLLFUNCCALL_DOUBLE | 1 | sm | - | medium |
| 0x14C | CALL_FUNCTION | 1 | sm | - | medium |
| 0x14D | DOTFUNCCALL_DOUBLE | 1 | sm | 6 -> 10 | medium |
| 0x14E | DOTFUNCCALL_DEC | 1 | sm | 6 -> 10 | medium |
| 0x14F | PUSH_LOCAL_VAR_DOUBLE | 1 | sm | 0 -> 4 | medium |
| 0x150 | PUSH_LOCAL_VAR_DEC | 1 | sm | 0 -> 4 | medium |
| 0x151 | PUSH_SHARED_VAR_DOUBLE | 1 | sm | 0 -> 4 | medium |
| 0x152 | PUSH_SHARED_VAR_DEC | 1 | sm | 0 -> 4 | medium |
| 0x153 | PUSH_LOCAL_GLOBREF_DOUBLE | 1 | sm | 0 -> 4 | medium |
| 0x154 | PUSH_LOCAL_GLOBREF_DEC | 1 | sm | 0 -> 4 | medium |
| 0x155 | PUSH_LOCAL_ARGREF_DOUBLE | 1 | sm | - | medium |
| 0x156 | PUSH_LOCAL_ARGREF_DEC | 1 | sm | - | medium |
| 0x157 | PUSH_SHARED_GLOBREF_DOUBLE | 1 | sm | - | medium |
| 0x158 | PUSH_SHARED_GLOBREF_DEC | 1 | sm | - | medium |
| 0x159 | ASSIGN_ANY | 1 | sm | 2 -> 0 | medium |
| 0x15A | CNV_ANY_TO_INT | 1 | sm | 0 -> 0 | medium |
| 0x15B | CNV_ANY_TO_UINT | 1 | sm | 0 -> 0 | medium |
| 0x15C | CNV_ANY_TO_LONG | 1 | sm | 0 -> 0 | medium |
| 0x15D | CNV_ANY_TO_ULONG | 1 | sm | 0 -> 0 | medium |
| 0x15E | CNV_ANY_TO_DEC | 1 | sm | 0 -> 0 | medium |
| 0x15F | CNV_ANY_TO_FLOAT | 1 | sm | 0 -> 0 | medium |
| 0x160 | CNV_ANY_TO_DOUBLE | 1 | sm | 0 -> 0 | medium |
| 0x161 | CNV_ANY_TO_STRING | 1 | sm | 0 -> 0 | medium |
| 0x162 | CNV_ANY_TO_BOOL | 1 | sm | 1 -> 1 | medium |
| 0x163 | CNV_ANY_TO_BINARY | 1 | sm | 1 -> 1 | medium |
| 0x164 | CNV_ANY_TO_DATE | 1 | sm | 1 -> 1 | medium |
| 0x165 | CNV_ANY_TO_TIME | 1 | sm | 1 -> 1 | medium |
| 0x166 | CNV_ANY_TO_DATETIME | 1 | sm | 1 -> 1 | medium |
| 0x167 | CNV_ANY_TO_CHAR | 1 | sm | 1 -> 1 | medium |
| 0x168 | CNV_ANY_TO_HANDLE | 1 | sm | 1 -> 1 | medium |
| 0x169 | CNV_ANY_TO_ENUM | 1 | sm | 1 -> 1 | medium |
| 0x16A | CNV_ANY_TO_OBJECT | 1 | sm | 0 -> 0 | medium |
| 0x16B | CONV_DEC_RVALUE_TO_PTR | 1 | sm | - | medium |
| 0x16C | COPY_EXPR_DEC | 1 | sm | 0 -> 0 | medium |
| 0x16D | CREATE_EXT_OBJ | 1 | sm | 0 -> 1 | medium |
| 0x16E | GLOBFUNCCALL_ANY | 1 | sm | - | medium |
| 0x16F | SYSFUNCCALL_ANY | 1 | sm | - | medium |
| 0x170 | DLLFUNCCALL_ANY | 1 | sm | - | medium |
| 0x171 | DOTFUNCCALL_ANY | 1 | sm | 6 -> 10 | medium |
| 0x172 | PUSH_LOCAL_VAR_ANY | 1 | sm | 0 -> 4 | medium |
| 0x173 | PUSH_SHARED_VAR_ANY | 1 | sm | - | medium |
| 0x174 | PUSH_LOCAL_GLOBREF_ANY | 1 | sm | - | medium |
| 0x175 | PUSH_LOCAL_ARGREF_ANY | 1 | sm | - | medium |
| 0x176 | PUSH_SHARED_GLOBREF_ANY | 1 | sm | - | medium |
| 0x177 | ADD_ANY | 1 | sm | 2 -> 1 | medium |
| 0x178 | SUB_ANY | 1 | sm | 2 -> 1 | medium |
| 0x179 | MULT_ANY | 1 | sm | 2 -> 1 | medium |
| 0x17A | DIV_ANY | 1 | sm | 2 -> 1 | medium |
| 0x17B | EQ | 1 | sm | 2 -> 1 | medium |
| 0x17C | NEGATE_ANY | 1 | sm | 1 -> 3 | medium |
| 0x17D | EQ_ANY | 1 | sm | 2 -> 1 | medium |
| 0x17E | NE_ANY | 1 | sm | 2 -> 1 | medium |
| 0x17F | GT_ANY | 1 | sm | 2 -> 1 | medium |
| 0x180 | LT_ANY | 1 | sm | 2 -> 1 | medium |
| 0x181 | GE_ANY | 1 | sm | 2 -> 1 | medium |
| 0x182 | LE_ANY | 1 | sm | 2 -> 1 | medium |
| 0x183 | AND_ANY | 1 | sm | 2 -> 1 | medium |
| 0x184 | OR_ANY | 1 | sm | 2 -> 1 | medium |
| 0x185 | NOT_ANY | 1 | sm | 1 -> 1 | medium |
| 0x186 | DOT_ANY | 1 | sm | - | medium |
| 0x187 | INDEX_ANY | 1 | sm | 2 -> 1 | medium |
| 0x188 | INDEX_ERR_CHK_ANY | 1 | sm | 2 -> 1 | medium |
| 0x189 | INT | 1 | sm | 0 -> 0 | medium |
| 0x18A | ABS_LONG | 1 | sm | 1 -> 1 | medium |
| 0x18B | ABS_DOUBLE | 1 | sm | 1 -> 1 | medium |
| 0x18C | ASC | 1 | sm | - | medium |
| 0x18D | BLOB | 1 | sm | 1 -> 1 | medium |
| 0x18E | CEILING | 1 | sm | 1 -> 1 | medium |
| 0x18F | COS | 1 | sm | 1 -> 1 | medium |
| 0x190 | EXP | 1 | sm | 1 -> 1 | medium |
| 0x191 | FACT | 1 | sm | - | medium |
| 0x192 | INTHIGH | 1 | sm | - | medium |
| 0x193 | INTLOW | 1 | sm | - | medium |
| 0x194 | ISDATE | 1 | sm | 1 -> 1 | medium |
| 0x195 | ISNULL | 1 | sm | 1 -> 1 | medium |
| 0x196 | ISNUMBER | 1 | sm | 1 -> 1 | medium |
| 0x197 | ISTIME | 1 | sm | 1 -> 1 | medium |
| 0x198 | ISVALID | 1 | sm | 1 -> 1 | medium |
| 0x199 | LEN_STRING | 1 | sm | 1 -> 1 | medium |
| 0x19A | LEN_BINARY | 1 | sm | 1 -> 1 | medium |
| 0x19B | LOG | 1 | sm | 1 -> 1 | medium |
| 0x19C | LOGTEN | 1 | sm | 1 -> 1 | medium |
| 0x19D | LOWER | 1 | sm | 1 -> 1 | medium |
| 0x19E | PI | 1 | sm | 1 -> 1 | medium |
| 0x19F | RAND_LONG | 1 | sm | 5 -> 3 | medium |
| 0x1A0 | RAND_DOUBLE | 1 | sm | 5 -> 3 | medium |
| 0x1A1 | SIN | 1 | sm | 1 -> 1 | medium |
| 0x1A2 | SQRT | 1 | sm | 1 -> 1 | medium |
| 0x1A3 | TAN | 1 | sm | 1 -> 1 | medium |
| 0x1A4 | UPPER | 1 | sm | 1 -> 1 | medium |
| 0x1A5 | CONV_TO_REFPAK | 1 | sm | - | medium |
| 0x1A6 | PUSH_LOCAL_GLOBREF_RP | 1 | sm | 0 -> 4 | medium |
| 0x1A7 | PUSH_LOCAL_ARGREF_RP | 1 | sm | - | medium |
| 0x1A8 | PUSH_SHARED_GLOBREF_RP | 1 | sm | - | medium |
| 0x1A9 | PUSH_LOCAL_VAR_RP | 1 | sm | 0 -> 4 | medium |
| 0x1AA | PUSH_LOCAL_VAR | 1 | sm | 0 -> 4 | medium |
| 0x1AB | PUSH_SHARED_VAR | 1 | sm | 0 -> 0 | medium |
| 0x1AC | TRANSFORM_BOUNDED_TO_UNBOUNDED | 1 | sm | 0 -> 0 | medium |
| 0x1AD | TRANSFORM_UNBOUNDED_TO_BOUNDED | 1 | sm | 0 -> 0 | medium |
| 0x1AE | TRANSFORM_UNBOUNDED_TO_UNBOUNDED | 1 | sm | 0 -> 0 | medium |
| 0x1AF | CALC_UNBOUNDED_ARRAY_BOUND | 1 | sm | 0 -> 0 | medium |
| 0x1B0 | CALC_SIMPLE_ARRAY_BOUND | 1 | sm | 0 -> 0 | medium |
| 0x1B1 | CALC_COMPLEX_ARRAY_BOUND | 1 | sm | 4 -> 1 | medium |
| 0x1B2 | BUILD_UNBOUNDED_ARRAYLIST | 1 | sm | 1 -> 1 | medium |
| 0x1B3 | BUILD_BOUNDED_ARRAYLIST | 1 | sm | - | medium |
| 0x1B4 | TRANSFORM_ARRAYLIST_TO_UNBOUNDED | 1 | sm | 0 -> 0 | medium |
| 0x1B5 | TRANSFORM_ARRAYLIST_TO_BOUNDED | 1 | sm | 0 -> 0 | medium |
| 0x1B6 | FREE_REF_PAK_N | 1 | sm | 0 -> 0 | medium |
| 0x1B7 | ARRAY_BOUND_INFO | 1 | sm | - | medium |
| 0x1B8 | LOWERBOUND | 1 | sm | 1 -> 1 | medium |
| 0x1B9 | UPPERBOUND | 1 | sm | 1 -> 1 | medium |
| 0x1BA | INCR_ANY | 1 | sm | 1 -> 0 | medium |
| 0x1BB | DECR_ANY | 1 | sm | 1 -> 0 | medium |
| 0x1BC | PUSH_FUNC_CLASS | 1 | sm | 6 -> 10 | medium |
| 0x1BD | CLASS_CALL | 1 | sm | 6 -> 10 | medium |
| 0x1BE | CLASS_CALL_DEC | 1 | sm | 6 -> 10 | medium |
| 0x1BF | CLASS_CALL_DOUBLE | 1 | sm | 6 -> 10 | medium |
| 0x1C0 | CLASS_CALL_ANY | 1 | sm | 6 -> 10 | medium |
| 0x1C1 | INDEX_RP | 1 | sm | 2 -> 1 | medium |
| 0x1C2 | DBDELETEWITHCURS | 1 | sm | - | medium |
| 0x1C3 | DBEXECUTEIMMED | 1 | sm | 2 -> 0 | medium |
| 0x1C4 | DBEXECDYNWITHDESC | 1 | sm | - | medium |
| 0x1C5 | DBFETCHWITHDESC | 1 | sm | - | medium |
| 0x1C6 | DBOPENDYNWITHDESC | 1 | sm | - | medium |
| 0x1C7 | DBUPDATEWITHCURS | 1 | sm | - | medium |
| 0x1C8 | CREATE_USING | 1 | sm | - | medium |
| 0x1C9 | TRANSFORM_ANY_TO_UNBOUNDED | 1 | sm | - | medium |
| 0x1CA | TRANSFORM_ANY_TO_BOUNDED | 1 | sm | - | medium |
| 0x1CB | FREE_INV_METH_ARGS | 1 | sm | 0 -> 0 | medium |
| 0x1CC | PUSH_NULL | 1 | sm | - | medium |
| 0x1CD | COPY_LVALUE_ANY | 1 | sm | 2 -> 1 | medium |
| 0x1CE | ENTER_EMBEDDED | 1 | sm | 0 -> 0 | medium |
| 0x1CF | EXIT_EMBEDDED | 1 | sm | 0 -> 0 | medium |
| 0x1D0 | DOT_FLD_UPDATE_INDEX_RP | 1 | sm | 0 -> 0 | medium |
| 0x1D1 | CNV_STRING_TO_BOUNDED_CHARARRAY | 1 | sm | - | medium |
| 0x1D2 | PUSH_NTH_PARENT | 1 | sm | - | medium |
| 0x1D3 | MOD_LONG | 1 | sm | 2 -> 1 | medium |
| 0x1D4 | MOD_ULONG | 1 | sm | 2 -> 1 | medium |
| 0x1D5 | MOD_DOUBLE | 1 | sm | 2 -> 1 | medium |
| 0x1D6 | MOD_DEC | 1 | sm | 2 -> 1 | medium |
| 0x1D7 | MOD_ANY | 1 | sm | 2 -> 1 | medium |
| 0x1D8 | ABS_DEC | 1 | sm | 1 -> 1 | medium |
| 0x1D9 | ABS_ANY | 1 | sm | 1 -> 1 | medium |
| 0x1DA | CEILING_ANY | 1 | sm | 1 -> 1 | medium |
| 0x1DB | MIN_LONG | 1 | sm | 5 -> 3 | medium |
| 0x1DC | MIN_ULONG | 1 | sm | 5 -> 3 | medium |
| 0x1DD | MIN_DOUBLE | 1 | sm | 5 -> 3 | medium |
| 0x1DE | MIN_DEC | 1 | sm | 5 -> 3 | medium |
| 0x1DF | MIN_ANY | 1 | sm | 5 -> 3 | medium |
| 0x1E0 | MAX_LONG | 1 | sm | 5 -> 3 | medium |
| 0x1E1 | MAX_ULONG | 1 | sm | 5 -> 3 | medium |
| 0x1E2 | MAX_DOUBLE | 1 | sm | 5 -> 3 | medium |
| 0x1E3 | MAX_DEC | 1 | sm | 5 -> 3 | medium |
| 0x1E4 | MAX_ANY | 1 | sm | 5 -> 3 | medium |
| 0x1E5 | PUSH_TRY | 1 | sm | - | medium |
| 0x1E6 | POP_TRY | 1 | sm | - | medium |
| 0x1E7 | CATCH_EXCEPTION | 1 | sm | - | medium |
| 0x1E8 | THROW_EXCEPTION | 1 | sm | - | medium |
| 0x1E9 | GOSUB | 1 | sm | - | medium |
| 0x1EA | RETURN_SUB | 1 | sm | - | medium |
| 0x1EB | CNV_INT_TO_LONGLONG | 1 | sm | 0 -> 0 | medium |
| 0x1EC | CNV_UINT_TO_LONGLONG | 1 | sm | 0 -> 0 | medium |
| 0x1ED | CNV_LONG_TO_LONGLONG | 1 | sm | 0 -> 0 | medium |
| 0x1EE | CNV_ULONG_TO_LONGLONG | 1 | sm | 0 -> 0 | medium |
| 0x1EF | CNV_DEC_TO_LONGLONG | 1 | sm | 1 -> 1 | medium |
| 0x1F0 | CNV_FLOAT_TO_LONGLONG | 1 | sm | 1 -> 1 | medium |
| 0x1F1 | CNV_DOUBLE_TO_LONGLONG | 1 | sm | 1 -> 1 | medium |
| 0x1F2 | CNV_LONGLONG_TO_INT | 1 | sm | 0 -> 0 | medium |
| 0x1F3 | CNV_LONGLONG_TO_UINT | 1 | sm | 0 -> 0 | medium |
| 0x1F4 | CNV_LONGLONG_TO_LONG | 1 | sm | 0 -> 0 | medium |
| 0x1F5 | CNV_LONGLONG_TO_ULONG | 1 | sm | 0 -> 0 | medium |
| 0x1F6 | CNV_LONGLONG_TO_DEC | 1 | sm | 0 -> 0 | medium |
| 0x1F7 | CNV_LONGLONG_TO_FLOAT | 1 | sm | 0 -> 0 | medium |
| 0x1F8 | CNV_LONGLONG_TO_DOUBLE | 1 | sm | 0 -> 0 | medium |
| 0x1F9 | ADD_LONGLONG | 1 | sm | 2 -> 1 | medium |
| 0x1FA | ADD | 1 | sm | 2 -> 1 | medium |
| 0x1FB | SUB | 1 | sm | 2 -> 1 | medium |
| 0x1FC | DIV_LONGLONG | 1 | sm | 2 -> 1 | medium |
| 0x1FD | POWER_LONGLONG | 1 | sm | 2 -> 1 | medium |
| 0x1FE | POWER | 1 | sm | 1 -> 3 | medium |
| 0x1FF | NEGATE | 1 | sm | 0 -> 12 | medium |
| 0x200 | PUSH_LOCAL_VAR_LONGLONG | 1 | sm | 0 -> 4 | medium |
| 0x201 | PUSH_LOCAL_GLOBREF_LONGLONG | 1 | sm | 0 -> 4 | medium |
| 0x202 | PUSH_LOCAL_ARGREF_LONGLONG | 1 | sm | 0 -> 4 | medium |
| 0x203 | PUSH_SHARED_VAR_LONGLONG | 1 | sm | 0 -> 4 | medium |
| 0x204 | PUSH_SHARED_GLOBREF_LONGLONG | 1 | sm | - | medium |
| 0x205 | ASSIGN_LONGLONG | 1 | sm | 2 -> 0 | medium |
| 0x206 | COPY_CONST_LONGLONG | 1 | sm | 0 -> 0 | medium |
| 0x207 | ADDASSIGN_LONGLONG | 1 | sm | 2 -> 0 | medium |
| 0x208 | SUBASSIGN_LONGLONG | 1 | sm | 2 -> 0 | medium |
| 0x209 | MULTASSIGN_LONGLONG | 1 | sm | 2 -> 0 | medium |
| 0x20A | ASSIGN | 1 | sm | 1 -> 0 | medium |
| 0x20B | DECR_LONGLONG | 1 | sm | 1 -> 0 | medium |
| 0x20C | COPY_LVALUE_LONGLONG | 1 | sm | 0 -> 0 | medium |
| 0x20D | ABS_LONGLONG | 1 | sm | 1 -> 1 | medium |
| 0x20E | RAND_LONGLONG | 1 | sm | 5 -> 3 | medium |
| 0x20F | EQ_LONGLONG | 1 | sm | 2 -> 1 | medium |
| 0x210 | NE_LONGLONG | 1 | sm | 2 -> 1 | medium |
| 0x211 | GT_LONGLONG | 1 | sm | 2 -> 1 | medium |
| 0x212 | LT_LONGLONG | 1 | sm | 2 -> 1 | medium |
| 0x213 | GE_LONGLONG | 1 | sm | 2 -> 1 | medium |
| 0x214 | LE_LONGLONG | 1 | sm | 2 -> 1 | medium |
| 0x215 | MOD_LONGLONG | 1 | sm | 2 -> 1 | medium |
| 0x216 | MIN_LONGLONG | 1 | sm | 5 -> 3 | medium |
| 0x217 | MAX_LONGLONG | 1 | sm | 5 -> 3 | medium |
| 0x218 | GLOBFUNCCALL_LONGLONG | 1 | sm | - | medium |
| 0x219 | SYSFUNCCALL_LONGLONG | 1 | sm | - | medium |
| 0x21A | DLLFUNCCALL_LONGLONG | 1 | sm | - | medium |
| 0x21B | DOTFUNCCALL_LONGLONG | 1 | sm | 6 -> 10 | medium |
| 0x21C | CALL_FUNCTION | 1 | sm | 6 -> 10 | medium |
| 0x21D | COPY_EXPR_LONGLONG | 1 | sm | 0 -> 0 | medium |
| 0x21E | DOT_LONGLONG | 1 | sm | 2 -> 1 | medium |
| 0x21F | INDEX_LONGLONG | 1 | sm | 2 -> 1 | medium |
| 0x220 | CNV_ANY_TO_LONGLONG | 1 | sm | 0 -> 0 | medium |
| 0x221 | CONV_LONGLONG_RVALUE_TO_PTR | 1 | sm | - | medium |
| 0x222 | INDEX_ERR_CHK_LONGLONG | 1 | sm | - | medium |
| 0x223 | PUSH_CONST_BYTE | 1 | sm | 0 -> 12 | medium |
| 0x224 | CNV_INT_TO_BYTE | 1 | sm | 0 -> 0 | medium |
| 0x225 | CNV_UINT_TO_BYTE | 1 | sm | 0 -> 0 | medium |
| 0x226 | CNV_LONG_TO_BYTE | 1 | sm | 0 -> 0 | medium |
| 0x227 | CNV_ULONG_TO_BYTE | 1 | sm | 0 -> 0 | medium |
| 0x228 | CNV_DEC_TO_BYTE | 1 | sm | 1 -> 1 | medium |
| 0x229 | CNV_FLOAT_TO_BYTE | 1 | sm | 1 -> 1 | medium |
| 0x22A | CNV_DOUBLE_TO_BYTE | 1 | sm | 1 -> 1 | medium |
| 0x22B | CNV_ANY_TO_BYTE | 1 | sm | 0 -> 0 | medium |
| 0x22C | CNV_LONGLONG_TO_BYTE | 1 | sm | 0 -> 0 | medium |
| 0x22D | CNV_BYTE_TO_INT | 1 | sm | 0 -> 0 | medium |
| 0x22E | CNV_BYTE_TO_UINT | 1 | sm | 0 -> 0 | medium |
| 0x22F | CNV_BYTE_TO_LONG | 1 | sm | 0 -> 0 | medium |
| 0x230 | CNV_BYTE_TO_ULONG | 1 | sm | 0 -> 0 | medium |
| 0x231 | CNV_BYTE_TO_DEC | 1 | sm | 0 -> 0 | medium |
| 0x232 | CNV_BYTE_TO_FLOAT | 1 | sm | 0 -> 0 | medium |
| 0x233 | CNV_BYTE_TO_DOUBLE | 1 | sm | 0 -> 0 | medium |
| 0x234 | CNV_BYTE_TO_LONGLONG | 1 | sm | 0 -> 0 | medium |
| 0x235 | ADD_BYTE | 1 | sm | 2 -> 1 | medium |
| 0x236 | SUB_BYTE | 1 | sm | 2 -> 1 | medium |
| 0x237 | MULT_BYTE | 1 | sm | 2 -> 1 | medium |
| 0x238 | DIV_BYTE | 1 | sm | 2 -> 1 | medium |
| 0x239 | POWER_BYTE | 1 | sm | 2 -> 1 | medium |
| 0x23A | NEGATE_BYTE | 1 | sm | 1 -> 3 | medium |
| 0x23B | INCR_BYTE | 1 | sm | 1 -> 0 | medium |
| 0x23C | DECR_BYTE | 1 | sm | 1 -> 0 | medium |
| 0x23D | ASSIGN_BYTE | 1 | sm | 2 -> 0 | medium |
| 0x23E | ADDASSIGN_BYTE | 1 | sm | 2 -> 0 | medium |
| 0x23F | SUBASSIGN_BYTE | 1 | sm | 2 -> 0 | medium |
| 0x240 | MULTASSIGN_BYTE | 1 | sm | 2 -> 0 | medium |
| 0x241 | EQ_BYTE | 1 | sm | 2 -> 1 | medium |
| 0x242 | NE_BYTE | 1 | sm | 2 -> 1 | medium |
| 0x243 | GT_BYTE | 1 | sm | 2 -> 1 | medium |
| 0x244 | LT_BYTE | 1 | sm | 2 -> 1 | medium |
| 0x245 | GE_BYTE | 1 | sm | 2 -> 1 | medium |
| 0x246 | LE_BYTE | 1 | sm | 2 -> 1 | medium |

## Operation Types

### SM (583 opcodes)
0x00, 0x01, 0x02, 0x03, 0x04, 0x05, 0x06, 0x07, 0x08, 0x09 ... and 573 more

