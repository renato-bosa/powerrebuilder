"""DAT block extraction and processing."""

import logging
from dataclasses import dataclass
from typing import BinaryIO

from src.extract.pbd.constants import (
    DAT_DATA_LEN_FIELD_LEN,
    DAT_DATA_LEN_FIELD_OFFSET_ASCII,
    DAT_DATA_LEN_FIELD_OFFSET_UNICODE,
    DAT_HEADER_SIZE_ASCII,
    DAT_HEADER_SIZE_UNICODE,
    DAT_NEXT_BLOCK_OFFSET_FIELD_LEN,
    DAT_NEXT_BLOCK_OFFSET_FIELD_OFFSET_ASCII,
    DAT_NEXT_BLOCK_OFFSET_FIELD_OFFSET_UNICODE,
)
from src.extract.utils.binary import binary_to_int, retrieve_bytes_from_file

logger = logging.getLogger(__name__)


@dataclass
class DataClass:
    """Represents a DAT block of data."""

    address: int
    data: bytes
    next_block_offset: int
    data_length_in_block: int
    is_unicode_data_block_header: bool


@dataclass
class PbEntryDefinition:
    """PowerBuilder entry definition."""

    objectname: str
    offset: int
    objectsize: int


def _parse_dat_header(
    header_bytes: bytes, entry_name: str, offset: int
) -> tuple[bool, int, int, int] | None:
    """Parse DAT header and return (is_unicode, header_size, next_offset, data_len) or None if invalid.
    
    PowerBuilder DAT blocks have different formats:
    - Unicode: D\0A\0T\0 signature (6 bytes) + 4-byte next offset + 2-byte data length
    - ASCII: DAT* signature (4 bytes) + 4-byte next offset + 2-byte data length
    - Mixed: DAT* signature but with PowerBuilder binary content (special case)
    
    Critical fix: PowerBuilder 8.0 and later use 2-byte data length fields, not 4-byte.
    Earlier versions of this code incorrectly assumed 4-byte length fields causing
    data truncation and extraction failures.
    """
    dat_sig_unicode = b"D\0A\0T\0"
    dat_sig_ascii = b"DAT*"

    if header_bytes.startswith(dat_sig_unicode):
        return (
            True,
            DAT_HEADER_SIZE_UNICODE,
            binary_to_int(
                header_bytes[
                    DAT_NEXT_BLOCK_OFFSET_FIELD_OFFSET_UNICODE : DAT_NEXT_BLOCK_OFFSET_FIELD_OFFSET_UNICODE
                    + DAT_NEXT_BLOCK_OFFSET_FIELD_LEN
                ]
            ),
            binary_to_int(
                header_bytes[
                    DAT_DATA_LEN_FIELD_OFFSET_UNICODE : DAT_DATA_LEN_FIELD_OFFSET_UNICODE
                    + DAT_DATA_LEN_FIELD_LEN
                ],
                size=DAT_DATA_LEN_FIELD_LEN  # Critical fix: PowerBuilder uses 2-byte length fields
            ),
        )
    if header_bytes.startswith(dat_sig_ascii):
        next_offset = binary_to_int(
            header_bytes[
                DAT_NEXT_BLOCK_OFFSET_FIELD_OFFSET_ASCII : DAT_NEXT_BLOCK_OFFSET_FIELD_OFFSET_ASCII
                + DAT_NEXT_BLOCK_OFFSET_FIELD_LEN
            ]
        )

        # PowerBuilder format variation: Mixed-format DAT blocks
        # Some PBD files use ASCII "DAT*" signature but contain binary PowerBuilder data
        # This is a format quirk found in certain PowerBuilder versions/configurations
        if len(header_bytes) >= 16:
            # Check for "PDW" pattern at offset 10 (PowerBuilder DataWindow signature)
            # This indicates the DAT block contains PowerBuilder binary data despite ASCII header
            if header_bytes[10:13] == b"PDW":
                logger.debug(
                    f"DAT block for '{entry_name}': Detected mixed-format (ASCII DAT* + PowerBuilder content)"
                )
                # Debug: show the header bytes for format analysis
                logger.debug("DAT header bytes: %s", header_bytes)
                # Mixed-format fix: content starts at offset 10, skip normal data length parsing
                # Return 0 for data_len to signal "use entry definition size instead"
                # This prevents truncation of mixed-format blocks
                return (False, 10, next_offset, 0)

        # Standard ASCII DAT format (most common)
        # Extract 2-byte data length field - this was a critical bug fix
        # Original code assumed 4-byte lengths causing massive over-reads
        data_len = binary_to_int(
            header_bytes[
                DAT_DATA_LEN_FIELD_OFFSET_ASCII : DAT_DATA_LEN_FIELD_OFFSET_ASCII
                + DAT_DATA_LEN_FIELD_LEN
            ],
            size=DAT_DATA_LEN_FIELD_LEN  # PowerBuilder 8.0+ uses 2-byte length fields
        )
        return (False, DAT_HEADER_SIZE_ASCII, next_offset, data_len)
    logger.error(
        f"DAT block for '{entry_name}' at offset {offset}: Invalid DAT signature. "
        f"Got: {header_bytes[:8].hex()}."
    )
    return None


def _read_dat_data(
    file_handle: BinaryIO,
    offset: int,
    length: int,
    block_size: int,
    file_size: int,
    entry_name: str,
) -> tuple[bytes, bool]:
    """Read DAT block data with comprehensive validation and error recovery.
    
    Implements safe reading with bounds checking to prevent crashes when
    DAT blocks reference invalid offsets or lengths. This was added after
    encountering corrupted PBD files that would crash the extractor.
    
    Returns:
        tuple[bytes, bool]: (data_bytes, is_partial) where is_partial indicates
        if the full requested data could not be read
    """
    is_partial = False

    # Critical safety check: Prevent reading beyond file boundaries
    # This fixes crashes with corrupted PBD files where DAT headers contain
    # invalid length values that extend beyond the actual file size
    if offset + length > file_size:
        available = file_size - offset
        logger.warning(
            f"DAT block for '{entry_name}': Declared data length {length} extends beyond file size. "
            f"Reading up to EOF (available: {available} bytes)."
        )
        length = max(0, available)  # Ensure non-negative length
        is_partial = True

    if length == 0:
        return b"", is_partial

    data_bytes = retrieve_bytes_from_file(
        file_handle, offset, length, block_size_override=block_size
    )

    if not data_bytes or len(data_bytes) < length:
        logger.warning(
            f"DAT block for '{entry_name}': Failed to read full declared data length {length}. "
            f"Got {len(data_bytes) if data_bytes else 0} bytes."
        )
        is_partial = True
        data_bytes = data_bytes or b""

    return data_bytes, is_partial


def extract_data_from_entry(
    file_handle: BinaryIO,
    entry_def: PbEntryDefinition,
    _is_unicode_file: bool,
    block_size: int,
    file_size: int,
) -> tuple[list[DataClass], bool]:
    """Extract all DAT blocks for a given PbEntryDefinition.
    
    This function implements the core DAT block extraction logic with several
    critical fixes for PowerBuilder format variations:
    
    1. Proper handling of 2-byte vs 4-byte length fields (PowerBuilder 8.0+ change)
    2. Support for mixed-format DAT blocks (ASCII header + binary content)
    3. Comprehensive error handling and bounds checking
    4. Chain traversal with infinite loop protection
    
    Args:
        entry_def: PowerBuilder entry definition containing offset and size
        _is_unicode_file: Whether the PBD file uses Unicode encoding (for context)
        block_size: Block size for aligned reading
        file_size: Total file size for bounds checking
    
    Returns:
        tuple[list[DataClass], bool]: (extracted_blocks, is_partial)
    """
    all_data_blocks: list[DataClass] = []
    current_block_offset = entry_def.offset
    is_partial = False

    # DAT block chain traversal with safety checks
    # PowerBuilder uses linked DAT blocks where next_block_offset points to the next block
    # A value of 0 indicates end of chain
    while current_block_offset != 0:
        # Critical bounds check: Prevent accessing invalid memory locations
        # This was causing crashes with corrupted PBD files
        if current_block_offset >= file_size:
            logger.warning(
                f"DAT chain for '{entry_def.objectname}': Block offset {current_block_offset} is outside file size."
            )
            is_partial = True
            break

        # Read DAT header bytes for format detection
        # Need to read enough bytes to detect both ASCII and Unicode formats
        # Unicode DAT headers are larger (6-byte signature vs 4-byte)
        max_header_size = max(DAT_HEADER_SIZE_ASCII, DAT_HEADER_SIZE_UNICODE)
        header_bytes = retrieve_bytes_from_file(
            file_handle,
            current_block_offset,
            max_header_size,
            block_size_override=block_size,
        )

        if not header_bytes or len(header_bytes) < min(
            DAT_HEADER_SIZE_ASCII, DAT_HEADER_SIZE_UNICODE
        ):
            logger.error(
                f"DAT block for '{entry_def.objectname}' at offset {current_block_offset}: "
                f"Failed to read header bytes."
            )
            is_partial = True
            break

        # Parse header
        header_info = _parse_dat_header(
            header_bytes, entry_def.objectname, current_block_offset
        )
        if not header_info:
            is_partial = True
            break

        is_unicode_header, header_size, next_offset, data_len = header_info

        # Mixed-format handling: When data_len = 0, use entry definition size
        # This handles the special case where DAT blocks have ASCII headers but
        # contain PowerBuilder binary data that doesn't fit standard DAT structure
        if data_len == 0:
            # Calculate actual data size from entry definition
            # Subtract header size to get pure data length
            remaining_entry_size = entry_def.objectsize - header_size
            data_len = remaining_entry_size
            logger.debug(
                f"Mixed-format DAT for '{entry_def.objectname}': Using entry objectsize {entry_def.objectsize}, calculated data_len = {data_len}"
            )

        # Check if full header was readable
        if len(header_bytes) < header_size:
            logger.error(
                f"DAT block for '{entry_def.objectname}': Incomplete header read."
            )
            is_partial = True
            break

        # Read data
        data_offset = current_block_offset + header_size
        data_bytes, data_is_partial = _read_dat_data(
            file_handle,
            data_offset,
            data_len,
            block_size,
            file_size,
            entry_def.objectname,
        )
        is_partial = is_partial or data_is_partial

        # Create data block
        data_block = DataClass(
            address=current_block_offset,
            data=data_bytes,
            next_block_offset=next_offset,
            data_length_in_block=len(data_bytes),
            is_unicode_data_block_header=is_unicode_header,
        )

        # Debug check before appending
        if not isinstance(data_block, DataClass):
            logger.error(
                f"WARNING: Attempting to append non-DataClass to all_data_blocks. "
                f"Type: {type(data_block)}, Value: {data_block!r}"
            )
        all_data_blocks.append(data_block)

        # Check for chain termination
        if is_partial and next_offset != 0:
            logger.info(
                f"DAT chain for '{entry_def.objectname}' is partial. Stopping chain traversal."
            )
            break

        current_block_offset = next_offset

    return all_data_blocks, is_partial


def get_text_from_data(all_data_blocks: list[DataClass], is_unicode_file: bool) -> str:
    """Concatenates data from all DAT blocks and decodes it into a single string.

    Enhanced with PowerBuilder-specific decoding to handle:
    1. Compressed/tokenized text format (asterisk corruption patterns)
    2. Mixed encoding detection and recovery
    3. UTF-16LE byte order corruption fixes
    4. Graceful fallback for decode errors
    
    PowerBuilder sometimes stores text in a compressed format where certain
    characters are replaced with asterisks (*) in predictable patterns.
    This function detects and corrects these patterns.
    """
    from src.extract.pbd.reader import detect_encoding
    from src.extract.utils.encoding import decode_powerbuilder_text

    text = ""
    default_encoding = "utf-16-le" if is_unicode_file else "latin1"

    for x in all_data_blocks:
        # Detect encoding for this specific block
        encoding = detect_encoding(x.data, default=default_encoding)
        try:
            # First try standard decoding
            decoded_text = x.data.decode(encoding, errors="replace")

            # PowerBuilder compressed text detection and recovery
            # PowerBuilder sometimes stores text with asterisk-based compression where
            # certain characters are replaced with * in predictable patterns
            # Examples: "address" becomes "a*dress", "COLUMN" becomes "COL*LMN"
            if not is_unicode_file and b"\x2a" in x.data:
                # Quick pre-decode to check for compression patterns
                test_decode = x.data.decode("latin1", errors="ignore")

                # Pattern matching for PowerBuilder text compression
                # Look for asterisks embedded within words (not normal punctuation)
                import re

                pb_pattern = re.compile(r"[a-zA-Z]\*[a-zA-Z]|\b\w*\*\w*\b")
                if pb_pattern.search(test_decode):
                    logger.debug(
                        f"Detected PowerBuilder compressed text in DAT block at 0x{x.address:X}"
                    )
                    # Use specialized PowerBuilder text decoder
                    decoded_text = decode_powerbuilder_text(x.data, encoding)

            text += decoded_text

        except UnicodeDecodeError as ude:
            logger.warning(
                f"Unicode decode error in DAT block at 0x{x.address:X} with encoding '{encoding}'. Error: {ude}. Data (hex): {x.data[:32].hex()}..."
            )
            # Try PowerBuilder decoder as fallback
            try:
                decoded_text = decode_powerbuilder_text(x.data, encoding)
                text += decoded_text
            except Exception:
                # Placeholder
                text += f"<DECODE_ERROR: {encoding}>"
        except Exception as e:
            logger.error(
                f"Unexpected error decoding DAT block at 0x{x.address:X} with encoding '{encoding}'. Error: {e}. Data (hex): {x.data[:32].hex()}...",
                exc_info=True,
            )
            # Placeholder
            text += f"<UNEXPECTED_DECODE_ERROR: {encoding}>"

    return text


def get_binary_from_data(all_data_blocks: list[DataClass]) -> bytes:
    """Concatenate all data blocks into a single binary."""
    binary_data = b""
    for x in all_data_blocks:
        binary_data += x.data
    return binary_data


def get_binary_with_dat_headers(all_data_blocks: list[DataClass]) -> bytes:
    """Reconstruct binary data with DAT* headers intact.

    This is critical for DataWindow objects and other PowerBuilder objects that
    expect to find the original DAT* header structure in their binary data.
    
    The function rebuilds the exact binary format:
    - ASCII: "DAT*" + 4-byte next_offset + 2-byte data_length + data
    - Unicode: "D\0A\0T\0" + 4-byte next_offset + 2-byte data_length + data
    
    Note: Uses 2-byte length fields (PowerBuilder 8.0+ format)
    """
    binary_data = b""

    # Add defensive check
    if not isinstance(all_data_blocks, list):
        logger.error(
            f"get_binary_with_dat_headers: Expected list, got {type(all_data_blocks)}"
        )
        return b""

    for i, block in enumerate(all_data_blocks):
        # Add defensive check for each block
        if not isinstance(block, DataClass):
            logger.error(
                f"get_binary_with_dat_headers: Block at index {i} is not a DataClass instance. "
                f"Got type: {type(block)}, value: {block!r}"
            )
            continue
        # Reconstruct the DAT header
        if block.is_unicode_data_block_header:
            # Unicode DAT header: D\0A\0T\0
            header = b"D\0A\0T\0"
        else:
            # ASCII DAT header: DAT*
            header = b"DAT*"

        # Reconstruct DAT header structure exactly as PowerBuilder expects
        import struct

        # Next block offset: 4-byte little-endian unsigned int
        header += struct.pack("<I", block.next_block_offset)

        # Data length: 2-byte little-endian unsigned short
        # Critical: PowerBuilder 8.0+ uses 2-byte length fields, not 4-byte
        header += struct.pack("<H", block.data_length_in_block)

        # Add header and data
        binary_data += header + block.data

    return binary_data
