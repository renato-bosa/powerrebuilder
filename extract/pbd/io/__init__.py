"""PowerBuilder I/O operations package.

This package provides low-level I/O operations for reading and writing
PowerBuilder binary files (PBL/PBD).
"""

from extract.pbd.utils.binary_utils import (
    BLOCK_SIZE,
    binary_to_int,
    binary_to_time,
    calculate_content_hash,
    decode,
    extract_bytes_2_lst,
    get_mime_type,
    get_mime_type_from_data,
    is_resource_file,
    is_source_file,
    retrieve_bytes_from_file,
    safe_filename,
)

from .file_operations import (
    save_binary_as_base64,
    save_binary_file,
    save_pcode_file,
    save_text_file,
    save_to_file,
)
from .progress import (
    BaseProgressTracker,
    SilentProgressTracker,
    TqdmProgressTracker,
)
from .scanner import (
    EXPECTED_BLOCK_SIZES,
    detect_block_size_from_dat_spacing,
    scan_for_signatures,
)

__all__ = [
    # Binary utilities
    "BLOCK_SIZE",
    # Scanner functions
    "EXPECTED_BLOCK_SIZES",
    # Progress tracking
    "BaseProgressTracker",
    "SilentProgressTracker",
    "TqdmProgressTracker",
    "binary_to_int",
    "binary_to_time",
    "calculate_content_hash",
    "decode",
    "detect_block_size_from_dat_spacing",
    "extract_bytes_2_lst",
    "get_mime_type",
    "get_mime_type_from_data",
    "is_resource_file",
    "is_source_file",
    "retrieve_bytes_from_file",
    "safe_filename",
    "save_binary_as_base64",
    "save_binary_file",
    "save_pcode_file",
    # File operations
    "save_text_file",
    "save_to_file",
    "scan_for_signatures",
]
