"""PowerBuilder extraction package.

This package provides functionality for extracting raw data from PowerBuilder
binary files (PBL/PBD) into text format for further processing.

TODO: Missing Features
    - Resource extraction (images, icons, embedded resources) - Basic support exists, needs enhancement
    - Enhanced error recovery for corrupted files - Basic support exists, needs enhancement
    - Extraction of binary blobs in DataWindows - Basic support exists, needs enhancement
"""

from .extract_coordinator import (
    extract_pbls,
    extract_with_recovery,
)
from .pbd.structures.data_block import extract_data_from_entry
from .pbd.structures.entry import (
    extract_entry_def,
    extract_entry_def_mixed_mode,
    extract_entry_def_unicode,
)
from .pbd.structures.node import (
    extract_nod,
    extract_nods,
)
from .pbd.structures.header import extract_pbl_header
from .pbd.extraction.extractor import extract_pbl
from .pbd.constants import (
    RESOURCE_EXTENSIONS,
    SOURCE_EXTENSIONS,
)
from .pbd.utils.binary_utils import (
    is_resource_file,
    is_source_file,
)

__all__ = [
    'extract_pbls',
    'extract_pbl_header',
    'extract_pbl',
    'extract_nods',
    'extract_nod',
    'extract_entry_def',
    'extract_entry_def_unicode',
    'extract_entry_def_mixed_mode',
    'extract_data_from_entry',
    'extract_with_recovery',
    'RESOURCE_EXTENSIONS',
    'SOURCE_EXTENSIONS',
    'is_resource_file',
    'is_source_file',
]
