"""Shared constants for PowerBuilder I/O operations.

This module defines constants used across the pbd_io package to avoid duplication
and ensure consistency.
"""

# Block size for PBD files (usually 512 or 1024 bytes)
BLOCK_SIZE = 512

# PowerBuilder signature constants
SIGNATURES = {
    "HDR": b"HDR\x00",  # Header
    "NOD": b"NOD*",  # Node
    "DAT": b"DAT*",  # Data
    "ENT": b"ENT*",  # Entry
    "FRE": b"FRE*",  # Free block
}

# Unicode variants of signatures
UNICODE_SIGNATURES = {
    "HDR": b"H\0D\0R\0*\0",  # Unicode header signature "HDR*"
    "NOD": b"N\0O\0D\0*\0",  # Unicode node
    "DAT": b"D\0A\0T\0 \0",  # Unicode data (DAT followed by space)
    "ENT": b"E\0N\0T\0*\0",  # Unicode entry
    # Unicode FRE* might be more complex due to encoding
}

# PowerBuilder entry type signatures (for objects within PBD files)
ENTRY_TYPE_SIGNATURES = {
    # DataWindow signatures
    "PDW1": b"PDW1",  # PowerBuilder DataWindow Version 1
    "PDW2": b"PDW2",  # PowerBuilder DataWindow Version 2
    "PDW3": b"PDW3",  # PowerBuilder DataWindow Version 3
    # Window signatures
    "PWO1": b"PWO1",  # PowerBuilder Window Object Version 1
    "PWO2": b"PWO2",  # PowerBuilder Window Object Version 2
    # Structure signatures
    "PSO1": b"PSO1",  # PowerBuilder Structure Object Version 1
    # User Object signatures
    "PUO1": b"PUO1",  # PowerBuilder User Object Version 1
    # Menu signatures
    "PMN1": b"PMN1",  # PowerBuilder Menu Version 1
    # Application signatures
    "PAP1": b"PAP1",  # PowerBuilder Application Version 1
    # Function signatures
    "PFN1": b"PFN1",  # PowerBuilder Function Version 1
}

# Unicode variants of entry type signatures
UNICODE_ENTRY_TYPE_SIGNATURES = {
    "PDW1": b"P\x00D\x00W\x001\x00",  # Unicode PDW1
    "PDW2": b"P\x00D\x00W\x002\x00",  # Unicode PDW2
    "PWO1": b"P\x00W\x00O\x001\x00",  # Unicode PWO1
    "PSO1": b"P\x00S\x00O\x001\x00",  # Unicode PSO1
    "PUO1": b"P\x00U\x00O\x001\x00",  # Unicode PUO1
    "PMN1": b"P\x00M\x00N\x001\x00",  # Unicode PMN1
    "PAP1": b"P\x00A\x00P\x001\x00",  # Unicode PAP1
    "PFN1": b"P\x00F\x00N\x001\x00",  # Unicode PFN1
}

# All signatures combined for scanning
ALL_SIGNATURES = {
    "ASCII_HDR": SIGNATURES["HDR"],
    "UNICODE_HDR": UNICODE_SIGNATURES["HDR"],
    "ASCII_NOD": SIGNATURES["NOD"],
    "UNICODE_NOD": UNICODE_SIGNATURES["NOD"],
    "ASCII_DAT": SIGNATURES["DAT"],
    "UNICODE_DAT": UNICODE_SIGNATURES["DAT"],
    "ASCII_ENT": SIGNATURES["ENT"],
    "UNICODE_ENT": UNICODE_SIGNATURES["ENT"],
    "ASCII_FRE": SIGNATURES["FRE"],
}

# PE file signatures
PE_SIGNATURES = {
    "MZ": b"MZ",  # DOS header
    "PE": b"PE\0\0",  # PE header
}

# File extensions for PowerBuilder source files (as a set)
SOURCE_EXTENSIONS = {
    ".srd",
    ".srs",
    ".srw",
    ".sru",
    ".srf",
    ".srm",
    ".srx",
    ".srj",
    ".srp",
    ".srq",
    ".sra",
    ".udo",
    ".win",  # Older PowerBuilder formats
    ".str",
    ".men",
    ".apl",
    ".xxy",  # Additional formats with binary/mixed data
    ".fun",  # Function P-code files
}

# File extensions for resources (as a set)
RESOURCE_EXTENSIONS = {
    ".bmp",
    ".jpg",
    ".jpeg",
    ".gif",
    ".png",
    ".ico",
    ".cur",
    ".wav",
    ".mp3",
    ".bin",
}

# Mapping of extensions to file types (if needed)
SOURCE_TYPE_MAP = {
    "srw": "Window",
    "sru": "User Object",
    "srd": "DataWindow",
    "srm": "Menu",
    "srf": "Function",
    "srs": "Structure",
    "srq": "Query",
    "sra": "Application",
    "srp": "Project",
    "srj": "EAServer Component",
    "srn": ".NET Assembly",
    "src": "Unknown",
}

# Maximum size for various operations
MAX_FILE_SIZE = 2 * 1024 * 1024 * 1024  # 2GB
MAX_MMAP_SIZE = 100 * 1024 * 1024  # 100MB

# Encoding constants
DEFAULT_ENCODING = "latin1"
UNICODE_ENCODING = "utf-16-le"

# DAT Block Structure constants
DAT_SIGNATURE_OFFSET = 0
DAT_SIGNATURE_LEN_ASCII = 4
DAT_SIGNATURE_LEN_UNICODE = 8

DAT_NEXT_BLOCK_OFFSET_FIELD_OFFSET_ASCII = 4  # After 'DAT ' signature
DAT_NEXT_BLOCK_OFFSET_FIELD_OFFSET_UNICODE = 8  # After 'D\0A\0T\0' signature
DAT_NEXT_BLOCK_OFFSET_FIELD_LEN = 4  # Next block offset is a 4-byte integer

DAT_DATA_LEN_FIELD_OFFSET_ASCII = 8  # After next_block_offset field
DAT_DATA_LEN_FIELD_OFFSET_UNICODE = 12  # After next_block_offset field
DAT_DATA_LEN_FIELD_LEN = 2  # Data length is a 2-byte unsigned short (NOT 4 bytes!)

# The actual data starts after the DAT header (sig, next_offset, data_len)
DAT_HEADER_SIZE_ASCII = (
    DAT_SIGNATURE_LEN_ASCII + DAT_NEXT_BLOCK_OFFSET_FIELD_LEN + DAT_DATA_LEN_FIELD_LEN
)
DAT_HEADER_SIZE_UNICODE = (
    DAT_SIGNATURE_LEN_UNICODE + DAT_NEXT_BLOCK_OFFSET_FIELD_LEN + DAT_DATA_LEN_FIELD_LEN
)
