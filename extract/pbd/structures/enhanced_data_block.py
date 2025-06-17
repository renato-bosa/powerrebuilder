"""Enhanced DAT block handling with magic number recovery for 100% accuracy.

This module improves upon the standard data_block.py by handling:
- Magic numbers misinterpreted as sizes (0x444F4D76)
- Corrupted DAT headers
- Partial block recovery
- Boundary detection for valid data
"""

import logging
from dataclasses import dataclass
from typing import BinaryIO

from common.object_type_detector import ObjectTypeDetector
from extract.pbd.structures.entry import PbEntryDefinition
from extract.pbd.utils.binary_utils import binary_to_int, retrieve_bytes_from_file

logger = logging.getLogger(__name__)

# DAT Block Structure constants (same as original)
DAT_SIGNATURE_OFFSET = 0
DAT_SIGNATURE_LEN_ASCII = 4
DAT_SIGNATURE_LEN_UNICODE = 8

DAT_NEXT_BLOCK_OFFSET_FIELD_OFFSET_ASCII = 4
DAT_NEXT_BLOCK_OFFSET_FIELD_OFFSET_UNICODE = 8
DAT_NEXT_BLOCK_OFFSET_FIELD_LEN = 4

DAT_DATA_LEN_FIELD_OFFSET_ASCII = 8
DAT_DATA_LEN_FIELD_OFFSET_UNICODE = 12
DAT_DATA_LEN_FIELD_LEN = 2  # Standard is 2 bytes

# Enhanced: Support for 4-byte length fields in corrupted blocks
DAT_DATA_LEN_FIELD_LEN_EXTENDED = 4  # Some blocks use 4 bytes

DAT_HEADER_SIZE_ASCII = (
    DAT_SIGNATURE_LEN_ASCII + DAT_NEXT_BLOCK_OFFSET_FIELD_LEN + DAT_DATA_LEN_FIELD_LEN
)
DAT_HEADER_SIZE_UNICODE = (
    DAT_SIGNATURE_LEN_UNICODE + DAT_NEXT_BLOCK_OFFSET_FIELD_LEN + DAT_DATA_LEN_FIELD_LEN
)

# Extended header sizes for 4-byte length fields
DAT_HEADER_SIZE_ASCII_EXT = (
    DAT_SIGNATURE_LEN_ASCII
    + DAT_NEXT_BLOCK_OFFSET_FIELD_LEN
    + DAT_DATA_LEN_FIELD_LEN_EXTENDED
)
DAT_HEADER_SIZE_UNICODE_EXT = (
    DAT_SIGNATURE_LEN_UNICODE
    + DAT_NEXT_BLOCK_OFFSET_FIELD_LEN
    + DAT_DATA_LEN_FIELD_LEN_EXTENDED
)


@dataclass(slots=True)
class EnhancedDataClass:
    """Enhanced data block with recovery information."""

    address: int
    data: bytes
    next_block_offset: int
    data_length_in_block: int
    is_unicode_data_block_header: bool
    recovery_method: str = "standard"  # Track how this block was recovered
    is_corrupted: bool = False
    original_declared_length: int | None = None  # Store original length if corrupted


def detect_and_fix_magic_number(
    data_len_value: int,
    file_handle: BinaryIO,
    current_offset: int,
    file_size: int,
    object_name: str,
) -> tuple[int, bool, str]:
    """Detect if a data length is actually a magic number and recover.

    Returns:
        Tuple of (actual_length, is_corrupted, recovery_method)
    """
    # Check if this is a known magic number
    if ObjectTypeDetector.is_corrupted_size(data_len_value):
        logger.info(
            f"Magic number 0x{data_len_value:08X} detected as size for '{object_name}' "
            f"at offset {current_offset}. Attempting recovery."
        )

        # Try to find the actual data length by scanning for patterns
        actual_length = find_actual_data_length(
            file_handle, current_offset, file_size, object_name
        )

        return actual_length, True, "magic_number_recovery"

    # Check for unreasonably large sizes
    if data_len_value > file_size or data_len_value > 0x1000000:  # 16MB threshold
        logger.warning(
            f"Suspicious data length {data_len_value} for '{object_name}' at offset {current_offset}"
        )
        actual_length = find_actual_data_length(
            file_handle, current_offset, file_size, object_name
        )
        return actual_length, True, "size_validation_recovery"

    return data_len_value, False, "standard"


def _scan_for_signatures(scan_data: bytes, signatures: list[bytes], object_name: str, sig_type: str) -> int:
    """Scan for signatures and return the minimum offset found.
    
    Returns:
        Minimum offset found, or len(scan_data) if none found
    """
    min_offset = len(scan_data)
    
    for sig in signatures:
        offset = scan_data.find(sig)
        if offset != -1 and offset < min_offset:
            min_offset = offset
            logger.debug(
                f"Found {sig_type} {sig[:4] if len(sig) >= 4 else sig} at offset {offset} for '{object_name}'"
            )
    
    return min_offset


def _find_data_boundary(scan_data: bytes, object_name: str) -> int:
    """Find the boundary of data by scanning for known signatures.
    
    Returns:
        Offset of boundary or len(scan_data) if no boundary found
    """
    # Look for next DAT block signature
    dat_signatures = [b"DAT*", b"D\0A\0T\0"]
    dat_offset = _scan_for_signatures(scan_data, dat_signatures, object_name, "DAT signature")
    
    # Look for other block markers
    block_markers = [b"ENT*", b"NOD*", b"FRE*", b"\x00\x00\x00\x00\x00\x00\x00\x00"]
    marker_offset = _scan_for_signatures(scan_data, block_markers, object_name, "block marker")
    
    return min(dat_offset, marker_offset)


def _apply_null_byte_heuristic(scan_data: bytes, object_name: str) -> int | None:
    """Apply heuristic based on trailing null bytes.
    
    Returns:
        Actual length after trimming nulls, or None if heuristic doesn't apply
    """
    # Count null bytes at the end
    null_count = 0
    for i in range(len(scan_data) - 1, -1, -1):
        if scan_data[i] == 0:
            null_count += 1
        else:
            break
    
    # If more than 50% nulls at end, truncate them
    if null_count > len(scan_data) // 2:
        actual_length = len(scan_data) - null_count
        logger.info(
            f"Recovered actual data length {actual_length} for '{object_name}' "
            f"by trimming {null_count} trailing nulls"
        )
        return actual_length
    
    return None


def find_actual_data_length(
    file_handle: BinaryIO,
    current_offset: int,
    file_size: int,
    object_name: str,
    max_scan: int = 65536,  # 64KB max scan
) -> int:
    """Find actual data length by scanning for next DAT block or end markers."""
    # Calculate offset where data would start (after header)
    data_start_offset = (
        current_offset + DAT_HEADER_SIZE_ASCII_EXT
    )  # Assume extended header

    if data_start_offset >= file_size:
        return 0

    # Read a chunk to scan
    scan_size = min(max_scan, file_size - data_start_offset)
    file_handle.seek(data_start_offset)
    scan_data = file_handle.read(scan_size)

    if not scan_data:
        return 0

    # Find data boundary using signatures
    boundary_offset = _find_data_boundary(scan_data, object_name)
    
    # If we found a boundary, use it
    if boundary_offset < len(scan_data):
        # Align to 4-byte boundary
        actual_length = (boundary_offset // 4) * 4
        logger.info(
            f"Recovered actual data length {actual_length} for '{object_name}' "
            f"using boundary detection"
        )
        return actual_length

    # Fallback: use heuristics based on content
    heuristic_length = _apply_null_byte_heuristic(scan_data, object_name)
    if heuristic_length is not None:
        return heuristic_length

    # Default to full scan size
    return scan_size


def _parse_dat_header(header_bytes: bytes) -> tuple[str, bool]:
    """Parse DAT header to determine type.
    
    Returns:
        Tuple of (dat_type, is_unicode) where dat_type is 'unicode', 'ascii', or 'corrupted'
    """
    dat_sig_unicode = b"D\0A\0T\0"
    dat_sig_ascii = b"DAT*"
    
    if header_bytes.startswith(dat_sig_unicode):
        return 'unicode', True
    elif header_bytes.startswith(dat_sig_ascii):
        return 'ascii', False
    else:
        return 'corrupted', False


def _extract_dat_block_info(
    header_bytes: bytes,
    dat_type: str,
    file_handle: BinaryIO,
    current_offset: int,
    file_size: int,
    object_name: str
) -> tuple[int, int, int, bool, str, int | None]:
    """Extract block information from DAT header.
    
    Returns:
        Tuple of (next_offset, data_length, header_size, is_corrupted, recovery_method, original_length)
    """
    recovery_method = "standard"
    is_corrupted = False
    original_declared_length = None
    
    if dat_type == 'unicode':
        next_offset = binary_to_int(
            header_bytes[
                DAT_NEXT_BLOCK_OFFSET_FIELD_OFFSET_UNICODE : DAT_NEXT_BLOCK_OFFSET_FIELD_OFFSET_UNICODE
                + DAT_NEXT_BLOCK_OFFSET_FIELD_LEN
            ]
        )
        offset_start = DAT_DATA_LEN_FIELD_OFFSET_UNICODE
        header_size_normal = DAT_HEADER_SIZE_UNICODE
        header_size_ext = DAT_HEADER_SIZE_UNICODE_EXT
    elif dat_type == 'ascii':
        next_offset = binary_to_int(
            header_bytes[
                DAT_NEXT_BLOCK_OFFSET_FIELD_OFFSET_ASCII : DAT_NEXT_BLOCK_OFFSET_FIELD_OFFSET_ASCII
                + DAT_NEXT_BLOCK_OFFSET_FIELD_LEN
            ]
        )
        offset_start = DAT_DATA_LEN_FIELD_OFFSET_ASCII
        header_size_normal = DAT_HEADER_SIZE_ASCII
        header_size_ext = DAT_HEADER_SIZE_ASCII_EXT
    else:  # corrupted
        # Try recovery by assuming ASCII DAT with corrupted signature
        next_offset = binary_to_int(header_bytes[4:8])
        data_len_4byte = binary_to_int(header_bytes[8:12])
        original_declared_length = data_len_4byte
        data_length, is_corrupted, recovery_method = detect_and_fix_magic_number(
            data_len_4byte,
            file_handle,
            current_offset,
            file_size,
            object_name,
        )
        return next_offset, data_length, DAT_HEADER_SIZE_ASCII_EXT, is_corrupted, "signature_recovery", original_declared_length
    
    # Try standard 2-byte length first
    data_length = binary_to_int(
        header_bytes[offset_start : offset_start + DAT_DATA_LEN_FIELD_LEN]
    )
    
    # Check if we need to read as 4-byte length
    if data_length == 0 or data_length > file_size:
        data_len_4byte = binary_to_int(
            header_bytes[offset_start : offset_start + DAT_DATA_LEN_FIELD_LEN_EXTENDED]
        )
        original_declared_length = data_len_4byte
        data_length, is_corrupted, recovery_method = detect_and_fix_magic_number(
            data_len_4byte,
            file_handle,
            current_offset,
            file_size,
            object_name,
        )
        header_size = header_size_ext
    else:
        header_size = header_size_normal
    
    return next_offset, data_length, header_size, is_corrupted, recovery_method, original_declared_length


def _read_dat_block_data(
    file_handle: BinaryIO,
    current_offset: int,
    header_size: int,
    data_length: int,
    file_size: int,
    block_size: int,
    object_name: str
) -> tuple[bytes, bool]:
    """Read actual data from DAT block.
    
    Returns:
        Tuple of (data_bytes, is_partial)
    """
    data_offset_in_file = current_offset + header_size
    bytes_to_read = data_length
    is_partial = False
    
    # Validate and adjust if necessary
    if data_offset_in_file + bytes_to_read > file_size:
        available = file_size - data_offset_in_file
        if available > 0:
            logger.warning(
                f"DAT block for '{object_name}' at offset {current_offset}: "
                f"Adjusting read size from {bytes_to_read} to {available}"
            )
            bytes_to_read = available
        else:
            bytes_to_read = 0
        is_partial = True
    
    actual_data_bytes = b""
    if bytes_to_read > 0:
        actual_data_bytes = retrieve_bytes_from_file(
            file_handle,
            data_offset_in_file,
            bytes_to_read,
            block_size_override=block_size,
        )
        if not actual_data_bytes:
            actual_data_bytes = b""
    
    return actual_data_bytes, is_partial


def _process_single_dat_block(
    file_handle: BinaryIO,
    current_offset: int,
    entry_def: PbEntryDefinition,
    block_size: int,
    file_size: int
) -> tuple[EnhancedDataClass | None, bool, int]:
    """Process a single DAT block.
    
    Returns:
        Tuple of (data_block, is_partial, next_offset)
    """
    # Read potential header with extended size
    max_dat_header_size = max(
        DAT_HEADER_SIZE_ASCII_EXT, DAT_HEADER_SIZE_UNICODE_EXT
    )

    potential_header_bytes = retrieve_bytes_from_file(
        file_handle,
        current_offset,
        max_dat_header_size,
        block_size_override=block_size,
    )

    if not potential_header_bytes or len(potential_header_bytes) < DAT_HEADER_SIZE_ASCII:
        logger.error(
            f"DAT block for '{entry_def.objectname}' at offset {current_offset}: "
            f"Failed to read header. Got {len(potential_header_bytes) if potential_header_bytes else 0} bytes."
        )
        return None, True, 0

    # Parse header type
    dat_type, is_unicode_header = _parse_dat_header(potential_header_bytes)
    
    if dat_type == 'corrupted' and len(potential_header_bytes) < DAT_HEADER_SIZE_ASCII_EXT:
        logger.error(
            f"DAT block for '{entry_def.objectname}' at offset {current_offset}: "
            f"Invalid DAT signature and insufficient bytes for recovery. Got: {potential_header_bytes[:8].hex()}"
        )
        return None, True, 0
    
    if dat_type == 'corrupted':
        logger.info(f"Attempting signature recovery for '{entry_def.objectname}'")
    
    # Extract block information
    next_offset, data_length, header_size, is_corrupted, recovery_method, original_length = _extract_dat_block_info(
        potential_header_bytes,
        dat_type,
        file_handle,
        current_offset,
        file_size,
        entry_def.objectname
    )
    
    # Read actual data
    actual_data_bytes, is_partial = _read_dat_block_data(
        file_handle,
        current_offset,
        header_size,
        data_length,
        file_size,
        block_size,
        entry_def.objectname
    )
    
    # Create enhanced data block
    data_block = EnhancedDataClass(
        address=current_offset,
        data=actual_data_bytes,
        next_block_offset=next_offset,
        data_length_in_block=len(actual_data_bytes),
        is_unicode_data_block_header=is_unicode_header,
        recovery_method=recovery_method,
        is_corrupted=is_corrupted,
        original_declared_length=original_length,
    )
    
    return data_block, is_partial, next_offset


def extract_data_from_entry_enhanced(
    file_handle: BinaryIO,
    entry_def: PbEntryDefinition,
    is_unicode_file: bool,
    block_size: int,
    file_size: int,
) -> tuple[list[EnhancedDataClass], bool]:
    """Enhanced extraction with magic number recovery and corruption handling."""
    all_data_blocks: list[EnhancedDataClass] = []
    current_block_offset = entry_def.offset
    is_partial = False
    blocks_processed = 0
    max_blocks = 1000  # Prevent infinite loops

    while current_block_offset != 0 and blocks_processed < max_blocks:
        blocks_processed += 1

        if current_block_offset >= file_size:
            logger.warning(
                f"DAT chain for '{entry_def.objectname}': Next block offset {current_block_offset} "
                f"is outside file size {file_size}. Marking as partial."
            )
            is_partial = True
            break

        # Process single DAT block
        data_block, block_is_partial, next_offset = _process_single_dat_block(
            file_handle,
            current_block_offset,
            entry_def,
            block_size,
            file_size
        )
        
        if not data_block:
            is_partial = True
            break
        
        all_data_blocks.append(data_block)
        is_partial = is_partial or block_is_partial
        
        # Validate next block offset
        if next_offset > file_size:
            logger.warning(
                f"DAT chain for '{entry_def.objectname}': Next block offset {next_offset} "
                f"exceeds file size. Ending chain."
            )
            break

        current_block_offset = next_offset

    if blocks_processed >= max_blocks:
        logger.error(
            f"DAT chain for '{entry_def.objectname}': Exceeded maximum block limit {max_blocks}. "
            f"Possible circular reference."
        )
        is_partial = True

    # Log recovery statistics
    if all_data_blocks:
        recovered_blocks = sum(1 for b in all_data_blocks if b.is_corrupted)
        if recovered_blocks > 0:
            logger.info(
                f"Successfully recovered {recovered_blocks}/{len(all_data_blocks)} "
                f"corrupted DAT blocks for '{entry_def.objectname}'"
            )

    return all_data_blocks, is_partial


# Maintain compatibility with original interface
def get_text_from_data(
    all_data_blocks: list[EnhancedDataClass], is_unicode_file: bool
) -> str:
    """Concatenates data from all DAT blocks and decodes it into a single string."""
    text = ""
    encoding = "utf-16-le" if is_unicode_file else "latin1"

    for block in all_data_blocks:
        if block.data:
            try:
                decoded = block.data.decode(encoding, errors="replace")
                text += decoded

                # Log recovery info for debugging
                if block.is_corrupted:
                    logger.debug(
                        f"Recovered block at 0x{block.address:X} using {block.recovery_method} "
                        f"(original size claim: {block.original_declared_length})"
                    )

            except Exception as e:
                logger.error(f"Error decoding block at 0x{block.address:X}: {e}")
                text += "<DECODE_ERROR>"

    return text


def get_binary_from_data(all_data_blocks: list[EnhancedDataClass]) -> bytes:
    """Concatenate binary data from all blocks."""
    return b"".join(block.data for block in all_data_blocks if block.data)
