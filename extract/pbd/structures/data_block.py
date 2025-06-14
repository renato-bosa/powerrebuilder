import logging
from dataclasses import dataclass
from typing import BinaryIO

from extract.pbd.utils.binary_utils import binary_to_int, retrieve_bytes_from_file

from .entry import (
    PbEntryDefinition,  # For type hint in extract_data_from_entry
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


def extract_data_from_entry(
    file_handle: BinaryIO,
    entry_def: PbEntryDefinition,
    is_unicode_file: bool,  # Overall unicode status of the PBD file (from HDR)
    block_size: int,  # Effective block size for reads
    file_size: int,  # Total size of the PBD file
) -> tuple[list[DataClass], bool]:  # Returns (data_blocks, is_partial)
    """Extract all DAT blocks for a given PbEntryDefinition."""
    all_data_blocks: list[DataClass] = []
    current_block_offset = entry_def.offset
    is_partial = False

    while current_block_offset != 0:
        if current_block_offset >= file_size:
            logger.warning(
                f"DAT chain for '{entry_def.objectname}': Next block offset {current_block_offset} is outside file size {file_size}. "
                f"Marking as partial. Entry data offset was {entry_def.offset}.",
            )
            is_partial = True
            break

        # Determine max possible DAT header size to read enough bytes initially
        max_dat_header_size = max(DAT_HEADER_SIZE_ASCII, DAT_HEADER_SIZE_UNICODE)

        # Read enough bytes for the largest possible DAT header to check its signature
        # Pass the effective block_size to retrieve_bytes_from_file
        potential_header_bytes = retrieve_bytes_from_file(
            file_handle,
            current_block_offset,
            max_dat_header_size,
            block_size_override=block_size,
        )

        if not potential_header_bytes or len(potential_header_bytes) < min(
            DAT_HEADER_SIZE_ASCII, DAT_HEADER_SIZE_UNICODE
        ):
            logger.error(
                f"DAT block for '{entry_def.objectname}' at offset {current_block_offset}: Failed to read enough bytes for DAT header. "
                f"Got {len(potential_header_bytes) if potential_header_bytes else 0} bytes. Marking as partial.",
            )
            is_partial = True
            break

        # Determine if this specific DAT block has a Unicode or ASCII signature
        dat_sig_unicode = b"D\0A\0T\0"
        dat_sig_ascii = b"DAT*"  # DAT blocks use asterisk, not space

        actual_dat_header_size: int
        data_starts_after_header_offset: int
        next_block_offset_in_header: int
        data_len_in_header: int
        is_current_dat_unicode_header = False

        if potential_header_bytes.startswith(dat_sig_unicode):
            is_current_dat_unicode_header = True
            actual_dat_header_size = DAT_HEADER_SIZE_UNICODE
            next_block_offset_in_header = binary_to_int(
                potential_header_bytes[
                    DAT_NEXT_BLOCK_OFFSET_FIELD_OFFSET_UNICODE : DAT_NEXT_BLOCK_OFFSET_FIELD_OFFSET_UNICODE
                    + DAT_NEXT_BLOCK_OFFSET_FIELD_LEN
                ]
            )
            data_len_in_header = binary_to_int(
                potential_header_bytes[
                    DAT_DATA_LEN_FIELD_OFFSET_UNICODE : DAT_DATA_LEN_FIELD_OFFSET_UNICODE
                    + DAT_DATA_LEN_FIELD_LEN
                ]
            )
        elif potential_header_bytes.startswith(dat_sig_ascii):
            is_current_dat_unicode_header = False  # Redundant but clear
            actual_dat_header_size = DAT_HEADER_SIZE_ASCII
            next_block_offset_in_header = binary_to_int(
                potential_header_bytes[
                    DAT_NEXT_BLOCK_OFFSET_FIELD_OFFSET_ASCII : DAT_NEXT_BLOCK_OFFSET_FIELD_OFFSET_ASCII
                    + DAT_NEXT_BLOCK_OFFSET_FIELD_LEN
                ]
            )
            data_len_in_header = binary_to_int(
                potential_header_bytes[
                    DAT_DATA_LEN_FIELD_OFFSET_ASCII : DAT_DATA_LEN_FIELD_OFFSET_ASCII
                    + DAT_DATA_LEN_FIELD_LEN
                ]
            )
            
        else:
            logger.error(
                f"DAT block for '{entry_def.objectname}' at offset {current_block_offset}: Invalid DAT signature. "
                f"Expected '{dat_sig_ascii.decode(errors='ignore')}' or '{dat_sig_unicode.decode(errors='ignore')}'. Got: {potential_header_bytes[:8].hex()}. Marking as partial.",
            )
            is_partial = True
            break

        # Check if the full DAT header was readable based on determined type
        if len(potential_header_bytes) < actual_dat_header_size:
            logger.error(
                f"DAT block for '{entry_def.objectname}' at offset {current_block_offset}: Read only {len(potential_header_bytes)} bytes, but DAT header (type: {'unicode' if is_current_dat_unicode_header else 'ascii'}) requires {actual_dat_header_size}. Marking as partial.",
            )
            is_partial = True
            break

        # Now read the actual data content of this DAT block
        data_offset_in_file = current_block_offset + actual_dat_header_size
        bytes_to_read_for_data = data_len_in_header

        # Validate data length
        if data_offset_in_file + bytes_to_read_for_data > file_size:
            available = file_size - data_offset_in_file
            logger.warning(
                f"DAT block for '{entry_def.objectname}' at offset {current_block_offset}: "
                f"Declared data length {bytes_to_read_for_data} extends beyond file size "
                f"{file_size} (ends at {data_offset_in_file + bytes_to_read_for_data}). "
                f"Reading up to EOF."
            )
            bytes_to_read_for_data = max(0, available)
            is_partial = True

        actual_data_bytes = b""
        if bytes_to_read_for_data > 0:
            actual_data_bytes = retrieve_bytes_from_file(
                file_handle,
                data_offset_in_file,
                bytes_to_read_for_data,
                block_size_override=block_size,
            )
            if not actual_data_bytes or len(actual_data_bytes) < bytes_to_read_for_data:
                logger.warning(
                    f"DAT block for '{entry_def.objectname}' at offset {current_block_offset}: Failed to read full declared data length {bytes_to_read_for_data} "
                    f"from data offset {data_offset_in_file}. Got {len(actual_data_bytes) if actual_data_bytes else 0} bytes. Marking as partial.",
                )
                is_partial = True  # Data is truncated or missing
                if not actual_data_bytes:
                    actual_data_bytes = b""  # Ensure it's bytes

        data_block = DataClass(
            address=current_block_offset,
            data=actual_data_bytes,
            next_block_offset=next_block_offset_in_header,
            data_length_in_block=len(
                actual_data_bytes
            ),  # Store actual bytes read for this block
            is_unicode_data_block_header=is_current_dat_unicode_header,
        )
        all_data_blocks.append(data_block)

        current_block_offset = next_block_offset_in_header
        if is_partial and current_block_offset != 0:
            logger.info(
                f"DAT chain for '{entry_def.objectname}' is partial, but next_block_offset is {current_block_offset}. Stopping chain to prevent further errors."
            )
            break  # If already marked partial due to EOF or bad offset, don't try to follow next pointer even if non-zero.

    return all_data_blocks, is_partial


def get_text_from_data(all_data_blocks: list[DataClass], is_unicode_file: bool) -> str:
    """Concatenates data from all DAT blocks and decodes it into a single string."""
    text = ""
    encoding = "utf-16-le" if is_unicode_file else "latin1"
    for x in all_data_blocks:
        try:
            text += x.data.decode(encoding, errors="replace")
        except UnicodeDecodeError as ude:
            logger.warning(
                f"Unicode decode error in DAT block at 0x{x.address:X} with encoding '{encoding}'. Error: {ude}. Data (hex): {x.data[:32].hex()}..."
            )
            text += f"<DECODE_ERROR: {encoding}>"  # Placeholder
        except Exception as e:
            logger.error(
                f"Unexpected error decoding DAT block at 0x{x.address:X} with encoding '{encoding}'. Error: {e}. Data (hex): {x.data[:32].hex()}...",
                exc_info=True,
            )
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

    for block in all_data_blocks:
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

        # Add data length (4 bytes)
        header += struct.pack("<I", block.data_length_in_block)

        # Add header and data
        binary_data += header + block.data

    return binary_data
