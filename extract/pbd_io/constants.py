"""Shared constants for PowerBuilder I/O operations.

This module defines constants used across the pbd_io package to avoid duplication
and ensure consistency.
"""

# Block size for PBD files (usually 512 or 1024 bytes)
BLOCK_SIZE = 512

# PowerBuilder signature constants
SIGNATURES = {
    'HDR': b'HDR\x00',  # Header
    'NOD': b'NOD\x00',  # Node
    'DAT': b'DAT\x00',  # Data
    'ENT': b'ENT\x00',  # Entry
    'FRE': b'FRE\x00',  # Free block
}

# File extensions for PowerBuilder source files (as a set)
SOURCE_EXTENSIONS = {
    '.srd', '.srs', '.srw', '.sru', '.srf', '.srm', '.srx', '.srj', '.srp', '.srq', '.sra',
    '.udo', '.win',  # Older PowerBuilder formats
}

# File extensions for resources (as a set)
RESOURCE_EXTENSIONS = {
    '.bmp', '.jpg', '.jpeg', '.gif', '.png', '.ico', '.cur', '.wav', '.mp3', '.bin',
}

# Mapping of extensions to file types (if needed)
SOURCE_TYPE_MAP = {
    'srw': 'Window',
    'sru': 'User Object',
    'srd': 'DataWindow',
    'srm': 'Menu',
    'srf': 'Function',
    'srs': 'Structure',
    'srq': 'Query',
    'sra': 'Application',
    'srp': 'Project',
    'srj': 'EAServer Component',
    'srn': '.NET Assembly',
    'src': 'Unknown'
}

# Maximum size for various operations
MAX_FILE_SIZE = 2 * 1024 * 1024 * 1024  # 2GB
MAX_MMAP_SIZE = 100 * 1024 * 1024      # 100MB

# Encoding constants
DEFAULT_ENCODING = 'latin1'
UNICODE_ENCODING = 'utf-16-le'