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
from .pbd_core import (
    extract_data_from_entry,
    extract_entry_def,
    extract_entry_def_mixed_mode,
    extract_entry_def_unicode,
    extract_nod,
    extract_nods,
    extract_pbl_header,
)
from .pbd_core.core import (
    extract_pbl,
)
from .pbd_io.utils import (
    RESOURCE_EXTENSIONS,
    SOURCE_EXTENSIONS,
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
