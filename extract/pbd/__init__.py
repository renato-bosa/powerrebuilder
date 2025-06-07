"""PowerBuilder PBD/PBL extraction package.

This package provides comprehensive functionality for extracting and analyzing
PowerBuilder binary files (PBL/PBD).

Main components:
- structures: Core data structures (headers, nodes, entries, data blocks)
- io: I/O operations (file reading/writing, scanning, progress tracking)
- extraction: High-level extraction APIs (Library class, extract functions)
- analysis: Analysis tools (DataWindow detection, symbol tables, cross-references)
- utils: Utility functions (binary operations, text extraction, version detection)
"""

# Core exceptions
from .exceptions import (
    PbdError,
    HeaderError,
    DataExtractionError,
    PfcExcludedError,
)

# Constants
from .constants import (
    BLOCK_SIZE,
    SOURCE_EXTENSIONS,
    RESOURCE_EXTENSIONS,
    SIGNATURES,
    UNICODE_SIGNATURES,
)

# High-level extraction API
from .extraction import Library

# Core extraction functions
from .extraction.extractor import extract_pbl

# Data structures
from .structures import (
    HeaderClass,
    NodeClass,
    PbEntryDefinition,
    DataClass,
    PbdObject,
)

# Utility functions
from .utils import (
    is_resource_file,
    is_source_file,
    binary_to_readable_format,
    detect_pb_version,
)

__all__ = [
    # Exceptions
    'PbdError',
    'HeaderError', 
    'DataExtractionError',
    'PfcExcludedError',
    # Constants
    'BLOCK_SIZE',
    'SOURCE_EXTENSIONS',
    'RESOURCE_EXTENSIONS',
    'SIGNATURES',
    'UNICODE_SIGNATURES',
    # High-level API
    'Library',
    'extract_pbl',
    # Data structures
    'HeaderClass',
    'NodeClass',
    'PbEntryDefinition',
    'DataClass',
    'PbdObject',
    # Utilities
    'is_resource_file',
    'is_source_file',
    'binary_to_readable_format',
    'detect_pb_version',
]