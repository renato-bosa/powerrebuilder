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
# Constants
from .constants import (
    BLOCK_SIZE,
    RESOURCE_EXTENSIONS,
    SIGNATURES,
    SOURCE_EXTENSIONS,
    UNICODE_SIGNATURES,
)
from .exceptions import (
    DataExtractionError,
    HeaderError,
    PbdError,
    PfcExcludedError,
)

# High-level extraction API
from .extraction import Library

# Core extraction functions
from .extraction.extractor import extract_pbl

# Data structures
from .structures import (
    DataClass,
    HeaderClass,
    NodeClass,
    PbdObject,
    PbEntryDefinition,
)

# Utility functions
from .utils import (
    binary_to_readable_format,
    detect_pb_version,
    is_resource_file,
    is_source_file,
)

__all__ = [
    # Constants
    "BLOCK_SIZE",
    "RESOURCE_EXTENSIONS",
    "SIGNATURES",
    "SOURCE_EXTENSIONS",
    "UNICODE_SIGNATURES",
    "DataClass",
    "DataExtractionError",
    # Data structures
    "HeaderClass",
    "HeaderError",
    # High-level API
    "Library",
    "NodeClass",
    "PbEntryDefinition",
    # Exceptions
    "PbdError",
    "PbdObject",
    "PfcExcludedError",
    "binary_to_readable_format",
    "detect_pb_version",
    "extract_pbl",
    # Utilities
    "is_resource_file",
    "is_source_file",
]
