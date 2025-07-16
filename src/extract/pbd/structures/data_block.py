import logging
from dataclasses import dataclass
from typing import BinaryIO

from src.extract.utils.binary import binary_to_int, retrieve_bytes_from_file

from .entry import (
    PbEntryDefinition, # For type hint in extract_data_from_entry
)

logger = logging.getLogger(__name__)

# DAT Block Structure (excluding the actual data of the block)
# These are offsets within a DAT block header, not sizes of fields themselves
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


@dataclass(slots=True)
class DataClass:
    address: int
    data: bytes
    next_block_offset: int
    data_length_in_block: int  # Actual length of data in this specific DAT block
    is_unicode_data_block_header: (
        bool  # True if this DAT block's header indicates Unicode (D\0A\0T\0)
    )


def _parse_dat_header(header_bytes: bytes, entry_name: str, offset: int) -> tuple[bool, int, int, int] | None:








    """Parse DAT header and return (is_unicode, header_size, next_offset, data_len) or None if invalid."""
    dat_sig_unicode = b"D\0A\0T\0"
    dat_sig_ascii = b"DAT*"

    if header_bytes.startswith(dat_sig_unicode):
        return (
            True, DAT_HEADER_SIZE_UNICODE, binary_to_int(header_bytes[DAT_NEXT_BLOCK_OFFSET_FIELD_OFFSET_UNICODE:DAT_NEXT_BLOCK_OFFSET_FIELD_OFFSET_UNICODE + DAT_NEXT_BLOCK_OFFSET_FIELD_LEN]), binary_to_int(header_bytes[DAT_DATA_LEN_FIELD_OFFSET_UNICODE:DAT_DATA_LEN_FIELD_OFFSET_UNICODE + DAT_DATA_LEN_FIELD_LEN])
        )
    elif header_bytes.startswith(dat_sig_ascii):
        next_offset = binary_to_int(header_bytes[DAT_NEXT_BLOCK_OFFSET_FIELD_OFFSET_ASCII:DAT_NEXT_BLOCK_OFFSET_FIELD_OFFSET_ASCII + DAT_NEXT_BLOCK_OFFSET_FIELD_LEN])

        # Check if this is a mixed-format DAT block (ASCII signature with UTF-16LE content)
        # Look for PowerBuilder content patterns starting at different offsets
        if len(header_bytes) >= 16:
            # Check for "PDW" pattern at offset 10 (mixed-format)
            if header_bytes[10:13] == b"PDW":
                logger.debug(f"DAT block for '{entry_name}': Detected mixed-format (ASCII DAT* + PowerBuilder content)")
                # Debug: show the header bytes
                logger.debug(f"DAT header bytes: {header_bytes[:20].hex()}")
                # For mixed-format, content starts at offset 10, use a minimal data length
                # The actual size should come from entry definition
                return (False, 10, next_offset, 0)  # Use 0 to signal "use entry size"

        # Standard ASCII format
        data_len = binary_to_int(header_bytes[DAT_DATA_LEN_FIELD_OFFSET_ASCII:DAT_DATA_LEN_FIELD_OFFSET_ASCII + DAT_DATA_LEN_FIELD_LEN])
        return (False, DAT_HEADER_SIZE_ASCII, next_offset, data_len)
    else:
        logger.error(
            f"DAT block for '{entry_name}' at offset {offset}: Invalid DAT signature. "
            f"Got: {header_bytes[:8].hex()}."
        )
        return None

def _read_dat_data(file_handle: BinaryIO, offset: int, length: int, block_size: int, file_size: int, entry_name: str) -> tuple[bytes, bool]:






    """Read DAT block data with validation."""
    is_partial = False

    # Validate data length
    if offset + length > file_size:
        available = file_size - offset
        logger.warning(
            f"DAT block for '{entry_name}': Declared data length {length} extends beyond file size. "
            f"Reading up to EOF."
        )
        length = max(0, available)
        is_partial = True

    if length == 0:
        return b"", is_partial

    data_bytes = retrieve_bytes_from_file(file_handle, offset, length, block_size_override=block_size)

    if not data_bytes or len(data_bytes) < length:
        logger.warning(
            f"DAT block for '{entry_name}': Failed to read full declared data length {length}. "
            f"Got {len(data_bytes) if data_bytes else 0} bytes."
        )
        is_partial = True
        data_bytes = data_bytes or b""

    return data_bytes, is_partial

def extract_data_from_entry(
    file_handle: BinaryIO, entry_def: PbEntryDefinition, is_unicode_file: bool, block_size: int, file_size: int, ) -> tuple[list[DataClass], bool]:






    """Extract all DAT blocks for a given PbEntryDefinition."""
    all_data_blocks: list[DataClass] = []
    current_block_offset = entry_def.offset
    is_partial = False

    while current_block_offset != 0:
        # Validate offset
        if current_block_offset >= file_size:
            logger.warning(
                f"DAT chain for '{entry_def.objectname}': Block offset {current_block_offset} is outside file size."
            )
            is_partial = True
            break

        # Read header bytes
        max_header_size = max(DAT_HEADER_SIZE_ASCII, DAT_HEADER_SIZE_UNICODE)
        header_bytes = retrieve_bytes_from_file(
            file_handle, current_block_offset, max_header_size, block_size_override=block_size
        )

        if not header_bytes or len(header_bytes) < min(DAT_HEADER_SIZE_ASCII, DAT_HEADER_SIZE_UNICODE):
            logger.error(
                f"DAT block for '{entry_def.objectname}' at offset {current_block_offset}: "
                f"Failed to read header bytes."
            )
            is_partial = True
            break

        # Parse header
        header_info = _parse_dat_header(header_bytes, entry_def.objectname, current_block_offset)
        if not header_info:
            is_partial = True
            break

        is_unicode_header, header_size, next_offset, data_len = header_info

        # Handle mixed-format files where data_len=0 means "use entry size"
        if data_len == 0:
            # For mixed-format, use the remaining size from entry definition
            # minus the header size we've already accounted for
            remaining_entry_size = entry_def.objectsize - header_size
            data_len = remaining_entry_size
            logger.debug(f"Mixed-format DAT for '{entry_def.objectname}': Using entry objectsize {entry_def.objectsize}, calculated data_len = {data_len}")

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
            file_handle, data_offset, data_len, block_size, file_size, entry_def.objectname
        )
        is_partial = is_partial or data_is_partial

        # Create data block
        data_block = DataClass(
            address=current_block_offset, data=data_bytes, next_block_offset=next_offset, data_length_in_block=len(data_bytes), is_unicode_data_block_header=is_unicode_header, )

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

    Now includes PowerBuilder-specific decoding for compressed/tokenized text.
    """
    from src.extract.utils.encoding import decode_powerbuilder_text
    from src.extract.pbd.reader import detect_encoding

    text = ""
    default_encoding = "utf-16-le" if is_unicode_file else "latin1"

    for x in all_data_blocks:
        # Detect encoding for this specific block
        encoding = detect_encoding(x.data, default=default_encoding)
        try:
            # First try standard decoding
            decoded_text = x.data.decode(encoding, errors="replace")

            # Check if the decoded text contains control sequences (asterisks in unexpected places)
            # This is a heuristic to detect PowerBuilder compressed format
            if not is_unicode_file and b'\x2A' in x.data:
                # Analyze if this looks like PowerBuilder compressed text
                # Look for patterns like "a*dress", "COL*LMN", etc.
                test_decode = x.data.decode("latin1", errors="ignore")

                # Simple heuristic: if we see * within words (position-based corruption)
                import re
                pb_pattern = re.compile(r'[a-zA-Z]\*[a-zA-Z]|\b\w*\*\w*\b')
                if pb_pattern.search(test_decode):
                    logger.debug(f"Detected potential PowerBuilder compressed text in DAT block at 0x{x.address:X}")
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
            except:
                text += f"<DECODE_ERROR: {encoding}>"  # Placeholder
        except Exception as e:
            logger.error(
                f"Unexpected error decoding DAT block at 0x{x.address:X} with encoding '{encoding}'. Error: {e}. Data (hex): {x.data[:32].hex()}...", exc_info=True, )
            text += f"<UNEXPECTED_DECODE_ERROR: {encoding}>"  # Placeholder

    return text


def get_binary_from_data(all_data_blocks: list[DataClass]) -> bytes:





    binary_data = b""
    for x in all_data_blocks:
        binary_data += x.data
    return binary_data


def get_binary_with_dat_headers(all_data_blocks: list[DataClass]) -> bytes:








    """Reconstruct binary data with DAT* headers intact.

    This is needed for DataWindow objects which expect the DAT* header format.
    """
    binary_data = b""

    # Add defensive check
    if not isinstance(all_data_blocks, list):
        logger.error(f"get_binary_with_dat_headers: Expected list, got {type(all_data_blocks)}")
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

        # Add next block offset (4 bytes)
        import struct

        header += struct.pack("<I", block.next_block_offset)

        # Add data length (2 bytes - unsigned short)
        header += struct.pack("<H", block.data_length_in_block)

        # Add header and data
        binary_data += header + block.data

    return binary_data