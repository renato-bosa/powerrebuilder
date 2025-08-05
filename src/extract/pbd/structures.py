"""PowerBuilder PBD file structures - header, node, entry, data block, and object definitions."""

import base64
import datetime
import logging
import os
import re
import struct
import zlib
from collections.abc import Callable
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, BinaryIO

from src.core.exceptions import HeaderError
from src.extract.pbd.constants import (
    DAT_DATA_LEN_FIELD_LEN,
    DAT_DATA_LEN_FIELD_OFFSET_ASCII,
    DAT_DATA_LEN_FIELD_OFFSET_UNICODE,
    DAT_HEADER_SIZE_ASCII,
    DAT_HEADER_SIZE_UNICODE,
    DAT_NEXT_BLOCK_OFFSET_FIELD_LEN,
    DAT_NEXT_BLOCK_OFFSET_FIELD_OFFSET_ASCII,
    DAT_NEXT_BLOCK_OFFSET_FIELD_OFFSET_UNICODE,
    SIGNATURES,
    UNICODE_SIGNATURES,
)
from src.extract.utils.binary import (
    binary_to_datetime,
    binary_to_int,
    calculate_content_hash,
    decode,
    decode_powerbuilder_name,
    extract_bytes_2_lst,
    extract_bytes_2_lst_original,
    extract_variable_fields,
    retrieve_bytes_from_file,
)

logger = logging.getLogger(__name__)

# ============================================================================
# Header structures and functions
# ============================================================================

# Header constants for non-Unicode files
HEADER_BLOCK_SIZES_NON_UNICODE = [4, 256, 1, 3, 10, 14, 4, 4, 4, 4]
HEADER_FUNCTORS_NON_UNICODE = [
    lambda x: decode(x, unicode=False, is_terminated=False),  # signature
    lambda x: decode(x, unicode=False, is_terminated=True),  # pbl_name
    lambda x: "",  # padding
    lambda x: decode(x, unicode=False, is_terminated=False),  # build_datetime
    lambda x: "",  # padding
    lambda x: binary_to_datetime(x),  # create_timestamp
    lambda x: binary_to_int(x),  # dep_lower_offset
    lambda x: binary_to_int(x),  # dep_upper_offset
    lambda x: binary_to_int(x),  # scc_data_offset
    lambda x: binary_to_int(x),  # reserved
]

# Header constants for Unicode files
HEADER_BLOCK_SIZES_UNICODE = [8, 512, 2, 6, 20, 14, 4, 4, 4, 4]
HEADER_FUNCTORS_UNICODE = [
    lambda x: decode(x, unicode=True, is_terminated=False),  # signature
    lambda x: decode(x, unicode=True, is_terminated=True),  # pbl_name
    lambda x: "",  # padding
    lambda x: decode(x, unicode=True, is_terminated=False),  # build_datetime
    lambda x: "",  # padding
    lambda x: binary_to_datetime(x),  # create_timestamp
    lambda x: binary_to_int(x),  # dep_lower_offset
    lambda x: binary_to_int(x),  # dep_upper_offset
    lambda x: binary_to_int(x),  # scc_data_offset
    lambda x: binary_to_int(x),  # reserved
]

# Header field names
HEADER_CLASS_ATTR_NAMES = [
    "hdr_str",
    "pbl_name_str",
    "padding1",
    "build_datetime_str",
    "padding2",
    "create_timestamp_dt",
    "dep_lower_offset_int",
    "dep_upper_offset_int",
    "scc_data_offset_int",
    "reserved_int",
]


@dataclass
class HeaderClass:
    """PowerBuilder file header information."""

    hdr_str: str
    pbl_name_str: str
    build_datetime_str: str
    create_timestamp_dt: datetime.datetime | None
    dep_lower_offset_int: int
    dep_upper_offset_int: int
    scc_data_offset_int: int
    reserved_int: int
    is_unicode: bool
    first_nod_offset: int
    file_signature_bytes: bytes | None
    file_size: int | None = None
    extract_resources: bool = True


def extract_pbl_header(
    file_input: BinaryIO | bytes,
    block_size: int,
    file_path_for_error_log: str | None = None,
) -> HeaderClass:
    """Extract the header information from PowerBuilder file bytes or a file handle.

    Args:
        file_input: Bytes content or an open binary file handle.
        block_size: The effective block size to use for calculations.
        file_path_for_error_log: Path to use in error messages, crucial if file_input is bytes.

    Returns:
        HeaderClass object with header information.
    """
    # Calculate required buffer size
    header_and_fre_check_len = max(
        sum(HEADER_BLOCK_SIZES_UNICODE), sum(HEADER_BLOCK_SIZES_NON_UNICODE)
    ) + (block_size * 2)

    # Prepare header bytes
    file_bytes_for_header, input_file_size, file_path_for_error_log = (
        _prepare_header_bytes(
            file_input, header_and_fre_check_len, file_path_for_error_log
        )
    )

    if not file_bytes_for_header or len(file_bytes_for_header) == 0:
        msg = f"No header bytes to process for {file_path_for_error_log}."
        raise HeaderError(msg)

    # Check buffer size
    min_buf_len_for_detection = max(
        sum(HEADER_BLOCK_SIZES_UNICODE), sum(HEADER_BLOCK_SIZES_NON_UNICODE)
    ) + (block_size * 2)

    if len(file_bytes_for_header) < min_buf_len_for_detection:
        logger.warning(
            f"Header data for {file_path_for_error_log} is short "
            f"({len(file_bytes_for_header)} bytes, need ~{min_buf_len_for_detection} for full check). "
            f"Some detections might be limited."
        )

    # Detect signature
    detected_signature_bytes, detected_signature_string, detected_is_unicode = (
        _detect_signature(file_bytes_for_header, file_path_for_error_log)
    )

    # Determine parsing parameters
    effective_is_unicode = detected_is_unicode
    header_block_sizes, base_functors, initial_nod_offset = (
        _determine_parsing_parameters(effective_is_unicode, block_size)
    )

    # Check for FRE* block
    final_first_nod_offset = _check_fre_block(
        file_bytes_for_header,
        detected_is_unicode,
        block_size,
        initial_nod_offset,
        file_path_for_error_log,
    )

    # Parse header fields
    parsed_header_fields = _parse_header_fields(
        file_bytes_for_header,
        header_block_sizes,
        base_functors,
        effective_is_unicode,
        file_path_for_error_log,
    )

    # Create and return header object
    return _create_header_object(
        parsed_header_fields,
        detected_signature_string,
        effective_is_unicode,
        final_first_nod_offset,
        detected_signature_bytes,
        input_file_size,
        file_path_for_error_log,
    )


def _prepare_header_bytes(
    file_input: BinaryIO | bytes,
    header_and_fre_check_len: int,
    file_path_for_error_log: str | None,
) -> tuple[bytes, int | None, str]:
    """Prepare header bytes from file input.

    Returns:
        Tuple of (header_bytes, file_size, log_path)
    """
    if (
        hasattr(file_input, "seek")
        and hasattr(file_input, "read")
        and hasattr(file_input, "tell")
    ):  # It's a BinaryIO handle
        handle = file_input
        original_pos = handle.tell()
        try:
            # Determine file size
            handle.seek(0, os.SEEK_END)
            input_file_size = handle.tell()
            handle.seek(original_pos)

            # Read enough bytes for header parsing
            handle.seek(0)
            file_bytes_for_header = handle.read(header_and_fre_check_len)
            handle.seek(original_pos)

            if not file_path_for_error_log:
                file_path_for_error_log = f"<handle at {hex(id(handle))}>"

            return file_bytes_for_header, input_file_size, file_path_for_error_log

        except Exception as e:
            log_path = file_path_for_error_log or f"<handle at {hex(id(handle))}>"
            msg = f"Error reading from file handle {log_path}: {e!s}"
            raise HeaderError(msg)

    elif isinstance(file_input, bytes):
        file_bytes_for_header = file_input[:header_and_fre_check_len]
        input_file_size = len(file_input)
        if not file_path_for_error_log:
            file_path_for_error_log = "provided bytes"
        return file_bytes_for_header, input_file_size, file_path_for_error_log

    else:
        msg = f"Unsupported file_input type: {type(file_input)}. Expected BinaryIO or bytes."
        raise HeaderError(msg)


def _detect_signature(
    file_bytes_for_header: bytes,
    file_path_for_error_log: str,
) -> tuple[bytes, str, bool]:
    """Detect and validate file signature.

    Returns:
        Tuple of (signature_bytes, signature_string, is_unicode)
    """
    if file_bytes_for_header.startswith(b"HDR\\0"):  # Non-unicode
        detected_signature_bytes = file_bytes_for_header[:4]
        detected_signature_string = decode(
            detected_signature_bytes, unicode=False, is_terminated=False
        )
        return detected_signature_bytes, detected_signature_string, False

    if file_bytes_for_header.startswith(b"HDR*"):  # Could be Unicode or mixed-format
        detected_signature_bytes = file_bytes_for_header[:8]

        # Check if this is actually a mixed-format file with ASCII FRE*
        for fre_offset in [1024, 2048, 4096]:  # Common block sizes * 2
            if (
                len(file_bytes_for_header) >= fre_offset + 4
                and file_bytes_for_header[fre_offset : fre_offset + 4] == b"FRE*"
            ):
                logger.debug(
                    f"HDR* file {file_path_for_error_log}: Found ASCII FRE* at offset {fre_offset}, treating as ASCII format"
                )
                return (
                    detected_signature_bytes,
                    "HDR*",
                    False,
                )  # ASCII format despite HDR* signature

        # No ASCII FRE* found, assume true Unicode
        return detected_signature_bytes, "HDR*", True

    peek_bytes = file_bytes_for_header[:8].hex()
    msg = f"Invalid PBL header signature for {file_path_for_error_log}. Expected HDR\\0 or HDR*. Got bytes: {peek_bytes}"
    raise HeaderError(msg)


def _determine_parsing_parameters(
    is_unicode: bool,
    block_size: int,
) -> tuple[list[int], list[Callable[[bytes], Any]], int]:
    """Determine parsing parameters based on unicode mode.

    Returns:
        Tuple of (header_block_sizes, functors, initial_nod_offset)
    """
    if is_unicode:
        return HEADER_BLOCK_SIZES_UNICODE, HEADER_FUNCTORS_UNICODE, block_size * 2
    return HEADER_BLOCK_SIZES_NON_UNICODE, HEADER_FUNCTORS_NON_UNICODE, block_size


def _check_fre_block(
    file_bytes_for_header: bytes,
    _is_unicode: bool,
    block_size: int,
    initial_nod_offset: int,
    file_path_for_error_log: str,
) -> int:
    """Check for FRE* block and adjust NOD offset if needed.

    Returns:
        Final first NOD offset
    """
    fre_check_offset = block_size * 2

    if len(file_bytes_for_header) >= fre_check_offset + 4:
        potential_fre_block_sig = file_bytes_for_header[
            fre_check_offset : fre_check_offset + 4
        ]
        if potential_fre_block_sig == b"FRE*":
            adjusted_nod_offset = fre_check_offset + block_size
            logger.info(
                f"HDR* file ({file_path_for_error_log}): ASCII FRE* signature found at offset {fre_check_offset}. "
                f"NOD offset adjusted to {adjusted_nod_offset} (FRE* + {block_size} bytes)."
            )
            return adjusted_nod_offset
        logger.info(
            f"HDR* file ({file_path_for_error_log}): No ASCII FRE* signature found at offset {fre_check_offset}. "
            f"Bytes found (first 4): {potential_fre_block_sig.hex() if potential_fre_block_sig else 'None'}"
        )
    else:
        logger.warning(
            f"HDR* file ({file_path_for_error_log}): Buffer too short (len {len(file_bytes_for_header)}) "
            f"to check for FRE* signature at offset {fre_check_offset}."
        )

    return initial_nod_offset


def _parse_header_fields(
    file_bytes_for_header: bytes,
    header_block_sizes: list[int],
    base_functors: list[Callable[[bytes], Any]],
    effective_is_unicode: bool,
    file_path_for_error_log: str,
) -> list[Any]:
    """Parse header fields from bytes.

    Returns:
        List of parsed header field values
    """
    required_header_len = sum(header_block_sizes)
    if len(file_bytes_for_header) < required_header_len:
        msg = f"File buffer for {file_path_for_error_log} too short for PBL header. "
        msg += f"Need {required_header_len}, have {len(file_bytes_for_header)} bytes."
        raise HeaderError(msg)

    # Adjust first functor for signature decoding
    actual_functors = list(base_functors)
    actual_functors[0] = lambda x_sig_bytes: decode(
        x_sig_bytes, unicode=effective_is_unicode, is_terminated=False
    )

    parsed_fields = extract_variable_fields(
        file_bytes_for_header[:required_header_len],
        header_block_sizes,
        actual_functors,
    )

    if len(parsed_fields) != len(HEADER_CLASS_ATTR_NAMES):
        msg = f"Header parsing for {file_path_for_error_log} failed, "
        msg += f"expected {len(HEADER_CLASS_ATTR_NAMES)} fields, "
        msg += f"got {len(parsed_fields)}: {parsed_fields}"
        raise HeaderError(msg)

    return parsed_fields


def _create_header_object(
    parsed_fields: list[Any],
    detected_signature_string: str,
    effective_is_unicode: bool,
    final_first_nod_offset: int,
    detected_signature_bytes: bytes,
    input_file_size: int | None,
    file_path_for_error_log: str,
) -> HeaderClass:
    """Create HeaderClass object from parsed data.

    Returns:
        HeaderClass instance
    """
    # Use detected signature string for first field
    parsed_fields[0] = detected_signature_string

    # Filter out padding fields
    header_values = []
    for i, field_name in enumerate(HEADER_CLASS_ATTR_NAMES):
        if not field_name.startswith("padding"):
            header_values.append(parsed_fields[i])

    final_header_values = [
        *header_values,
        effective_is_unicode,
        final_first_nod_offset,
        detected_signature_bytes,
        input_file_size,
    ]

    try:
        return HeaderClass(*final_header_values)
    except TypeError as e:
        expected_fields_info = (
            HeaderClass.__dataclass_fields__
            if hasattr(HeaderClass, "__dataclass_fields__")
            else "unknown (not a dataclass or no fields)"
        )
        logger.exception(
            f"TypeError during HeaderClass instantiation for {file_path_for_error_log}. "
            f"Values count: {len(final_header_values)}, "
            f"HeaderClass expects fields: {expected_fields_info}. Error: {e}"
        )
        logger.exception("Values provided: %s", final_header_values)
        msg = f"Failed to create HeaderClass object for {file_path_for_error_log}. "
        msg += f"Values: {final_header_values}. Error: {e}"
        raise HeaderError(msg)


# ============================================================================
# Node structures and functions
# ============================================================================


@dataclass
class PbNodeDefinition:
    """PowerBuilder node definition structure.

    Nodes contain references to entries (objects) in the PBD file.
    Each node can contain multiple entry definitions.
    """

    offset: int
    """Offset of this node in the file"""

    signature: bytes
    """Node signature (NOD*)"""

    is_unicode: bool
    """Whether this node uses Unicode encoding"""

    next_node_offset: int
    """Offset to the next node (0 if last)"""

    entry_count: int
    """Number of entries in this node"""

    entry_defs: list[Any] = field(default_factory=list)
    """List of entry definitions in this node"""

    metadata: dict[str, Any] = field(default_factory=dict)
    """Additional metadata for debugging"""


def extract_nods(
    arr: bytes | BinaryIO,
    is_unicode: bool,
    first_nod_offset: int,
    block_size: int = 512,
) -> list[PbNodeDefinition]:
    """Extract all nodes from a PBD file.

    Args:
        arr: File bytes or file-like object
        is_unicode: Whether the file uses Unicode encoding
        first_nod_offset: Offset to the first node
        block_size: Block size for alignment

    Returns:
        List of node definitions

    Raises:
        NodeError: If node extraction fails
    """
    # Handle both bytes and file-like objects
    if hasattr(arr, "read"):
        # It's a file-like object, read it
        arr.seek(0)
        file_bytes = arr.read()
    else:
        # It's already bytes
        file_bytes = arr

    nodes = []
    current_offset = first_nod_offset

    # Validate first node offset
    if current_offset < 0 or current_offset >= len(file_bytes):
        logger.warning(
            "Invalid first node offset %d (file size: %d)",
            current_offset,
            len(file_bytes),
        )
        return nodes

    # Maximum nodes to prevent infinite loops
    max_nodes = 10000
    node_count = 0

    while current_offset > 0 and node_count < max_nodes:
        try:
            # Extract node at current offset
            node = _extract_single_node(
                file_bytes, current_offset, is_unicode, block_size
            )

            if not node:
                logger.debug("No node found at offset %d", current_offset)
                break

            nodes.append(node)
            node_count += 1

            # Move to next node
            current_offset = node.next_node_offset

            # Validate next offset
            if current_offset > 0 and current_offset >= len(file_bytes):
                logger.warning(
                    "Next node offset %d exceeds file size %d",
                    current_offset,
                    len(file_bytes),
                )
                break

        except Exception as e:
            logger.warning(
                "Failed to extract node at offset %d: %s",
                current_offset,
                e,
            )
            break

    logger.info("Extracted %d nodes from PBD", len(nodes))
    return nodes


def _extract_single_node(
    file_bytes: bytes,
    offset: int,
    is_unicode: bool,
    block_size: int,
) -> PbNodeDefinition | None:
    """Extract a single node from the file.

    Args:
        file_bytes: Complete file bytes
        offset: Offset to the node
        is_unicode: Whether to expect Unicode encoding
        block_size: Block size for alignment

    Returns:
        Node definition or None if not found
    """
    # Check signature
    if offset + 4 > len(file_bytes):
        return None

    signature = file_bytes[offset : offset + 4]

    # Verify it's a NOD block
    expected_sig = UNICODE_SIGNATURES["NOD"] if is_unicode else SIGNATURES["NOD"]
    if signature != expected_sig[:4]:
        # Try the other encoding
        alt_sig = SIGNATURES["NOD"] if is_unicode else UNICODE_SIGNATURES["NOD"]
        if signature != alt_sig[:4]:
            logger.debug(
                "Invalid node signature at offset %d: %s",
                offset,
                signature.hex(),
            )
            return None

    # Create node structure
    node = PbNodeDefinition(
        offset=offset,
        signature=signature,
        is_unicode=is_unicode,
        next_node_offset=0,
        entry_count=0,
    )

    # Parse node header
    try:
        header_offset = offset + 4  # Skip signature

        if is_unicode:
            # Unicode node structure
            node_data = _parse_unicode_node_header(file_bytes, header_offset)
        else:
            # ASCII node structure
            node_data = _parse_ascii_node_header(file_bytes, header_offset)

        if not node_data:
            return None

        node.next_node_offset = node_data["next_offset"]
        node.entry_count = node_data["entry_count"]

        # Extract entries
        entries_offset = node_data["entries_offset"]
        node.entry_defs = _extract_node_entries(
            file_bytes,
            entries_offset,
            node.entry_count,
            is_unicode,
            offset,
        )

        # Store metadata
        node.metadata.update(node_data)

    except Exception as e:
        logger.warning("Failed to parse node at offset %d: %s", offset, e)
        return None

    return node


def _parse_ascii_node_header(file_bytes: bytes, offset: int) -> dict[str, Any] | None:
    """Parse ASCII node header.

    Args:
        file_bytes: Complete file bytes
        offset: Offset after signature

    Returns:
        Node header data or None
    """
    # Minimum header size
    if offset + 32 > len(file_bytes):
        return None

    try:
        # Common node structure:
        # - Next node offset (4 bytes)
        # - Unknown fields (12 bytes)
        # - Entry count (1 byte)
        # - Additional fields vary by version

        next_offset = struct.unpack("<I", file_bytes[offset : offset + 4])[0]
        # Skip unknown fields and read entry count at offset 16 (as single byte)
        if offset + 16 >= len(file_bytes):
            return None
        entry_count = file_bytes[offset + 16]

        # Sanity checks
        if entry_count > 10000:  # Unreasonable number of entries
            logger.warning("Suspicious entry count: %d", entry_count)
            return None

        # Entries typically start after the header
        entries_offset = offset + 32  # Basic header size

        return {
            "next_offset": next_offset,
            "entry_count": entry_count,
            "entries_offset": entries_offset,
            "header_size": 32,
        }

    except struct.error as e:
        logger.debug("Failed to unpack ASCII node header: %s", e)
        return None


def _parse_unicode_node_header(file_bytes: bytes, offset: int) -> dict[str, Any] | None:
    """Parse Unicode node header.

    Args:
        file_bytes: Complete file bytes
        offset: Offset after signature

    Returns:
        Node header data or None
    """
    # Unicode headers may be larger
    if offset + 20 > len(file_bytes):
        return None

    try:
        # Unicode node structure is similar but may have different alignment
        next_offset = struct.unpack("<I", file_bytes[offset : offset + 4])[0]
        entry_count = struct.unpack("<I", file_bytes[offset + 4 : offset + 8])[0]

        # Sanity checks
        if entry_count > 10000:
            logger.warning("Suspicious entry count: %d", entry_count)
            return None

        # Unicode entries may start at different offset
        entries_offset = offset + 20

        return {
            "next_offset": next_offset,
            "entry_count": entry_count,
            "entries_offset": entries_offset,
            "header_size": 20,
        }

    except struct.error as e:
        logger.debug("Failed to unpack Unicode node header: %s", e)
        return None


def _extract_node_entries(
    file_bytes: bytes,
    offset: int,
    entry_count: int,
    is_unicode: bool,
    node_offset: int,
) -> list[Any]:
    """Extract entries from a node.

    Args:
        file_bytes: Complete file bytes
        offset: Offset to first entry
        entry_count: Number of entries to extract
        is_unicode: Whether to use Unicode parsing
        node_offset: Offset of the containing node (for context)

    Returns:
        List of entry definitions
    """
    from src.extract.pbd.recovery import extract_entry_with_recovery

    entries = []
    current_offset = offset

    for i in range(entry_count):
        try:
            # Each entry reference in the node typically contains:
            # - Entry offset (4 bytes)
            # - Entry size or other metadata

            if current_offset + 8 > len(file_bytes):
                logger.debug(
                    "Insufficient data for entry %d at offset %d",
                    i,
                    current_offset,
                )
                break

            # Read entry reference
            entry_offset = struct.unpack(
                "<I", file_bytes[current_offset : current_offset + 4]
            )[0]

            # Skip to actual entry data
            if entry_offset > 0 and entry_offset < len(file_bytes):
                # Extract the actual entry definition
                entry_data = file_bytes[
                    entry_offset : entry_offset + 1024
                ]  # Read enough for header

                context = f"entry {i} in node at offset {node_offset}"
                entry_def = extract_entry_with_recovery(entry_data, is_unicode, context)

                if entry_def:
                    entries.append(entry_def)
                else:
                    logger.debug(
                        "Failed to extract entry %d at offset %d",
                        i,
                        entry_offset,
                    )

            # Move to next entry reference
            current_offset += 8  # Typical entry reference size

        except Exception as e:
            logger.debug(
                "Failed to extract entry %d: %s",
                i,
                e,
            )
            # Continue with next entry
            current_offset += 8

    return entries


# ============================================================================
# Entry structures and functions
# ============================================================================


@dataclass
class PbEntryDefinition:
    """PowerBuilder entry definition structure.

    Represents a single object/resource entry in a PBD file.
    """

    offset: int
    """Offset of this entry in the file"""

    object_name: str
    """Name of the object (e.g., 'w_main', 'n_datastore')"""

    object_type: str
    """Type of object (e.g., 'window', 'userobject', 'datawindow')"""

    size: int
    """Size of the entry data in bytes"""

    data_offset: int
    """Offset to the actual data (DAT block)"""

    comment: str = ""
    """Optional comment or description"""

    creation_datetime: datetime.datetime | None = None
    """Creation timestamp"""

    modification_datetime: datetime.datetime | None = None
    """Last modification timestamp"""

    is_unicode: bool = False
    """Whether this entry uses Unicode encoding"""

    metadata: dict[str, Any] = field(default_factory=dict)
    """Additional metadata for debugging"""

    # Legacy compatibility fields
    @property
    def objectname(self) -> str:
        """Legacy property for backward compatibility."""
        return self.object_name

    @property
    def objectsize(self) -> int:
        """Legacy property for backward compatibility."""
        return self.size

    @property
    def commentlen(self) -> int:
        """Legacy property for backward compatibility."""
        return len(self.comment) if self.comment else 0

    @property
    def moddatetime(self) -> datetime.datetime | None:
        """Legacy property for backward compatibility."""
        return self.modification_datetime

    @property
    def length(self) -> int:
        """Legacy property for backward compatibility."""
        return self.size

    @property
    def version(self) -> str:
        """Legacy property for backward compatibility."""
        return self.metadata.get("version", "unknown")


def extract_entry_def(arr: bytes) -> PbEntryDefinition | None:
    """Extract entry definition from raw bytes (auto-detect encoding).

    Args:
        arr: Raw entry data

    Returns:
        Entry definition or None if parsing fails
    """
    if len(arr) < 4:
        return None

    # Check signature to determine encoding
    if arr[:4] == b"ENT*":
        # ASCII signature
        return extract_entry_def_ascii(arr)
    if arr[:4] == b"E\x00N\x00":
        # Unicode signature
        return extract_entry_def_unicode(arr)
    logger.debug("Unknown entry signature: %s", arr[:4].hex())
    return None


def extract_entry_def_ascii(arr: bytes) -> PbEntryDefinition | None:
    """Extract ASCII entry definition.

    Args:
        arr: Raw entry data with ASCII encoding

    Returns:
        Entry definition or None if parsing fails
    """
    if len(arr) < 32:  # Minimum header size
        return None

    try:
        offset = 4  # Skip signature

        # Parse fixed header fields
        data_offset = struct.unpack("<I", arr[offset : offset + 4])[0]
        offset += 4

        size = struct.unpack("<I", arr[offset : offset + 4])[0]
        offset += 4

        # Skip type/flags field
        offset += 4

        # Parse timestamps (if present)
        creation_time = None
        modification_time = None

        if len(arr) >= offset + 16:
            # Timestamps are often stored as Windows FILETIME
            creation_raw = struct.unpack("<Q", arr[offset : offset + 8])[0]
            modification_raw = struct.unpack("<Q", arr[offset + 8 : offset + 16])[0]
            offset += 16

            # Convert from Windows FILETIME if non-zero
            if creation_raw > 0:
                creation_time = _filetime_to_datetime(creation_raw)
            if modification_raw > 0:
                modification_time = _filetime_to_datetime(modification_raw)

        # Parse object name (null-terminated string)
        name_start = offset
        name_end = arr.find(b"\x00", name_start)

        if name_end == -1 or name_end - name_start > 255:
            # Invalid or too long name
            return None

        # Use PowerBuilder-specific name decoder
        object_name = decode_powerbuilder_name(arr[name_start:name_end], is_unicode_context=False)
        offset = name_end + 1

        # Parse comment if present
        comment = ""
        if offset < len(arr) - 1:
            comment_end = arr.find(b"\x00", offset)
            if comment_end > offset:
                comment = arr[offset:comment_end].decode("ascii", errors="replace")

        # Determine object type from name extension
        object_type = _determine_object_type(object_name)

        return PbEntryDefinition(
            offset=0,  # Will be set by caller
            object_name=object_name,
            object_type=object_type,
            size=size,
            data_offset=data_offset,
            comment=comment,
            creation_datetime=creation_time,
            modification_datetime=modification_time,
            is_unicode=False,
        )

    except Exception as e:
        logger.debug("Failed to parse ASCII entry: %s", e)
        return None


def extract_entry_def_unicode(arr: bytes) -> PbEntryDefinition | None:
    """Extract Unicode entry definition.

    Args:
        arr: Raw entry data with Unicode encoding

    Returns:
        Entry definition or None if parsing fails
    """
    if len(arr) < 40:  # Minimum Unicode header size
        return None

    try:
        offset = 8  # Skip Unicode signature (wider)

        # Parse fixed header fields (similar to ASCII but aligned differently)
        data_offset = struct.unpack("<I", arr[offset : offset + 4])[0]
        offset += 4

        size = struct.unpack("<I", arr[offset : offset + 4])[0]
        offset += 4

        # Skip type/flags
        offset += 4

        # Parse timestamps
        creation_time = None
        modification_time = None

        if len(arr) >= offset + 16:
            creation_raw = struct.unpack("<Q", arr[offset : offset + 8])[0]
            modification_raw = struct.unpack("<Q", arr[offset + 8 : offset + 16])[0]
            offset += 16

            if creation_raw > 0:
                creation_time = _filetime_to_datetime(creation_raw)
            if modification_raw > 0:
                modification_time = _filetime_to_datetime(modification_raw)

        # Parse Unicode object name
        name_start = offset
        # Look for Unicode null terminator
        name_end = arr.find(b"\x00\x00", name_start)

        if name_end == -1 or name_end % 2 != 0:
            # Invalid Unicode string
            return None

        if name_end - name_start > 510:  # Max 255 Unicode chars
            return None

        # Use PowerBuilder-specific name decoder with Unicode context
        object_name = decode_powerbuilder_name(arr[name_start:name_end], is_unicode_context=True)
        offset = name_end + 2

        # Parse Unicode comment if present
        comment = ""
        if offset < len(arr) - 2:
            comment_end = arr.find(b"\x00\x00", offset)
            if comment_end > offset and comment_end % 2 == 0:
                comment = arr[offset:comment_end].decode("utf-16-le", errors="replace")

        object_type = _determine_object_type(object_name)

        return PbEntryDefinition(
            offset=0,
            object_name=object_name,
            object_type=object_type,
            size=size,
            data_offset=data_offset,
            comment=comment,
            creation_datetime=creation_time,
            modification_datetime=modification_time,
            is_unicode=True,
        )

    except Exception as e:
        logger.debug("Failed to parse Unicode entry: %s", e)
        return None


def extract_entry_def_mixed_mode(arr: bytes) -> PbEntryDefinition | None:
    """Extract entry with mixed ASCII/Unicode encoding.

    Some PB versions use ASCII signatures but Unicode data.

    Args:
        arr: Raw entry data

    Returns:
        Entry definition or None if parsing fails
    """
    # Try ASCII header with Unicode name
    if len(arr) < 32:
        return None

    try:
        # Parse as ASCII header first
        result = extract_entry_def_ascii(arr)
        if result:
            return result

        # If that fails, try parsing with Unicode name after ASCII header
        offset = 28  # Common ASCII header size

        # Look for Unicode name
        name_end = arr.find(b"\x00\x00", offset)
        if name_end > offset and name_end % 2 == 0:
            # Found Unicode string, re-parse
            return _parse_mixed_entry(arr)

    except Exception as e:
        logger.debug("Failed to parse mixed-mode entry: %s", e)

    return None


def extract_entry_def_ascii_sig_unicode_data(arr: bytes) -> PbEntryDefinition | None:
    """Extract entry with ASCII signature but Unicode data.

    Args:
        arr: Raw entry data

    Returns:
        Entry definition or None if parsing fails
    """
    return _parse_mixed_entry(arr)


def _parse_mixed_entry(arr: bytes) -> PbEntryDefinition | None:
    """Parse entry with mixed encoding.

    Args:
        arr: Raw entry data

    Returns:
        Entry definition or None
    """
    if len(arr) < 32:
        return None

    try:
        offset = 4  # Skip ASCII signature

        # Parse header as ASCII
        data_offset = struct.unpack("<I", arr[offset : offset + 4])[0]
        offset += 4

        size = struct.unpack("<I", arr[offset : offset + 4])[0]
        offset += 4

        # Skip to name area (after fixed fields)
        offset = 28

        # Try to find and parse Unicode name
        name_end = arr.find(b"\x00\x00", offset)
        if name_end > offset and name_end % 2 == 0:
            # Unicode name detected
            object_name = decode_powerbuilder_name(arr[offset:name_end], is_unicode_context=True)
        else:
            # Fall back to ASCII
            name_end = arr.find(b"\x00", offset)
            if name_end > offset:
                object_name = decode_powerbuilder_name(arr[offset:name_end], is_unicode_context=False)
            else:
                return None

        object_type = _determine_object_type(object_name)

        return PbEntryDefinition(
            offset=0,
            object_name=object_name,
            object_type=object_type,
            size=size,
            data_offset=data_offset,
            is_unicode=True,  # Mark as Unicode since name was Unicode
        )

    except Exception as e:
        logger.debug("Failed to parse mixed entry: %s", e)
        return None


def _filetime_to_datetime(filetime: int) -> datetime.datetime | None:
    """Convert Windows FILETIME to Python datetime.

    Args:
        filetime: Windows FILETIME value (100-nanosecond intervals since 1601)

    Returns:
        datetime object or None if invalid
    """
    try:
        # Windows FILETIME epoch: January 1, 1601
        # Unix epoch: January 1, 1970
        # Difference in seconds: 11644473600

        if filetime == 0:
            return None

        # Convert to Unix timestamp
        unix_timestamp = (filetime / 10000000.0) - 11644473600

        if unix_timestamp < 0 or unix_timestamp > 253402300799:  # Year 9999
            return None

        return datetime.datetime.fromtimestamp(unix_timestamp, tz=datetime.UTC)

    except Exception:
        return None


def _determine_object_type(object_name: str) -> str:
    """Determine object type from name.

    Args:
        object_name: Object name (may include extension)

    Returns:
        Object type string
    """
    name_lower = object_name.lower()

    # Check common extensions
    if name_lower.endswith((".srw", ".win")):
        return "window"
    if name_lower.endswith((".sru", ".uo")):
        return "userobject"
    if name_lower.endswith((".srd", ".dwo")):
        return "datawindow"
    if name_lower.endswith((".srm", ".men")):
        return "menu"
    if name_lower.endswith((".srf", ".fun")):
        return "function"
    if name_lower.endswith((".srs", ".str")):
        return "structure"
    if name_lower.endswith((".sra", ".app")):
        return "application"
    if name_lower.endswith(".srq"):
        return "query"
    if name_lower.endswith(".srp"):
        return "project"

    # Check name prefixes
    if name_lower.startswith("w_"):
        return "window"
    if name_lower.startswith(("u_", "n_")):
        return "userobject"
    if name_lower.startswith(("d_", "dw_")):
        return "datawindow"
    if name_lower.startswith("m_"):
        return "menu"
    if name_lower.startswith(("f_", "gf_")):
        return "function"
    if name_lower.startswith("s_"):
        return "structure"

    return "unknown"


# ============================================================================
# Data block structures and functions
# ============================================================================


@dataclass
class DataClass:
    """Represents a DAT block of data."""

    address: int
    data: bytes
    next_block_offset: int
    data_length_in_block: int
    is_unicode_data_block_header: bool


def extract_data_from_entry(
    file_handle: BinaryIO,
    entry_def: PbEntryDefinition,
    _is_unicode_file: bool,
    block_size: int,
    file_size: int,
) -> tuple[list[DataClass], bool]:
    """Extract all DAT blocks for a given PbEntryDefinition."""
    all_data_blocks: list[DataClass] = []
    current_block_offset = entry_def.data_offset
    is_partial = False

    while current_block_offset != 0:
        # Validate offset
        if current_block_offset >= file_size:
            logger.warning(
                f"DAT chain for '{entry_def.object_name}': Block offset {current_block_offset} is outside file size."
            )
            is_partial = True
            break

        # Read header bytes
        max_header_size = max(DAT_HEADER_SIZE_ASCII, DAT_HEADER_SIZE_UNICODE)
        header_bytes = retrieve_bytes_from_file(
            file_handle,
            current_block_offset,
            max_header_size,
        )

        if not header_bytes or len(header_bytes) < min(
            DAT_HEADER_SIZE_ASCII, DAT_HEADER_SIZE_UNICODE
        ):
            logger.error(
                f"DAT block for '{entry_def.object_name}' at offset {current_block_offset}: "
                f"Failed to read header bytes."
            )
            is_partial = True
            break

        # Parse header
        header_info = _parse_dat_header(
            header_bytes, entry_def.object_name, current_block_offset
        )
        if not header_info:
            is_partial = True
            break

        is_unicode_header, header_size, next_offset, data_len = header_info

        # Handle mixed-format files where data_len = 0 means "use entry size"
        if data_len == 0:
            # For mixed-format, use the remaining size from entry definition
            remaining_entry_size = entry_def.size - header_size
            data_len = remaining_entry_size
            logger.debug(
                f"Mixed-format DAT for '{entry_def.object_name}': Using entry objectsize {entry_def.size}, calculated data_len = {data_len}"
            )

        # Check if full header was readable
        if len(header_bytes) < header_size:
            logger.error(
                f"DAT block for '{entry_def.object_name}': Incomplete header read."
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
            entry_def.object_name,
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
                f"DAT chain for '{entry_def.object_name}' is partial. Stopping chain traversal."
            )
            break

        current_block_offset = next_offset

    return all_data_blocks, is_partial


def _parse_dat_header(
    header_bytes: bytes, entry_name: str, offset: int
) -> tuple[bool, int, int, int] | None:
    """Parse DAT header and return (is_unicode, header_size, next_offset, data_len) or None if invalid."""
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
                ]
            ),
        )
    if header_bytes.startswith(dat_sig_ascii):
        next_offset = binary_to_int(
            header_bytes[
                DAT_NEXT_BLOCK_OFFSET_FIELD_OFFSET_ASCII : DAT_NEXT_BLOCK_OFFSET_FIELD_OFFSET_ASCII
                + DAT_NEXT_BLOCK_OFFSET_FIELD_LEN
            ]
        )

        # Check if this is a mixed-format DAT block (ASCII signature with UTF-16LE content)
        if len(header_bytes) >= 16:
            # Check for "PDW" pattern at offset 10 (mixed-format)
            if header_bytes[10:13] == b"PDW":
                logger.debug(
                    f"DAT block for '{entry_name}': Detected mixed-format (ASCII DAT* + PowerBuilder content)"
                )
                # For mixed-format, content starts at offset 10, use a minimal data length
                return (False, 10, next_offset, 0)

        # Standard ASCII format
        data_len = binary_to_int(
            header_bytes[
                DAT_DATA_LEN_FIELD_OFFSET_ASCII : DAT_DATA_LEN_FIELD_OFFSET_ASCII
                + DAT_DATA_LEN_FIELD_LEN
            ]
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

    data_bytes = retrieve_bytes_from_file(
        file_handle, offset, length
    )

    if not data_bytes or len(data_bytes) < length:
        logger.warning(
            f"DAT block for '{entry_name}': Failed to read full declared data length {length}. "
            f"Got {len(data_bytes) if data_bytes else 0} bytes."
        )
        is_partial = True
        data_bytes = data_bytes or b""

    return data_bytes, is_partial


def get_text_from_data(all_data_blocks: list[DataClass], is_unicode_file: bool) -> str:
    """Concatenates data from all DAT blocks and decodes it into a single string.

    Now includes PowerBuilder-specific decoding for compressed/tokenized text.
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

            # Check if the decoded text contains control sequences
            if not is_unicode_file and b"\x2a" in x.data:
                # Analyze if this looks like PowerBuilder compressed text
                test_decode = x.data.decode("latin1", errors="ignore")

                # Simple heuristic: if we see * within words (position-based corruption)
                pb_pattern = re.compile(r"[a-zA-Z]\*[a-zA-Z]|\b\w*\*\w*\b")
                if pb_pattern.search(test_decode):
                    logger.debug(
                        f"Detected potential PowerBuilder compressed text in DAT block at 0x{x.address:X}"
                    )
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

    This is needed for DataWindow objects which expect the DAT* header format.
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

        # Add next block offset (4 bytes)
        header += struct.pack("<I", block.next_block_offset)

        # Add data length (2 bytes - unsigned short)
        header += struct.pack("<H", block.data_length_in_block)

        # Add header and data
        binary_data += header + block.data

    return binary_data


# ============================================================================
# Object structures and functions
# ============================================================================


@dataclass
class PbdObject:
    """Represents a single object (entry) extracted from a PowerBuilder PBD file."""

    entry_definition: PbEntryDefinition
    is_unicode_file_context: bool = field(repr=False)
    data_blocks: list[DataClass] = field(repr=False)  # Avoid excessively long repr
    is_partial: bool = False  # Added to indicate potentially incomplete data
    raw_text_content: str | None = field(init=False, default=None)
    raw_binary_content: bytes | None = field(init=False, default=None)
    raw_pcode: str | None = field(init=False, default=None)

    def _try_inflate_datawindow_syntax(self, text_content: str) -> str:
        """Attempts to find and decompress zlib-compressed DataWindow syntax within text_content.
        Looks for patterns like Syntax=(1)"base64_encoded_zlib_data".
        """
        # Only attempt for objects that typically contain DataWindow syntax
        if not self.name.lower().endswith((".srd", ".srw", ".sru")):
            return text_content

        # Define the regex pattern
        DW_SYNTAX_REGEX = re.compile(r'Syntax=\((\d)\)"([^"]+)"', re.DOTALL)

        match = DW_SYNTAX_REGEX.search(text_content)
        if not match:
            return text_content

        compression_flag = match.group(1)
        syntax_data_b64 = match.group(2)

        if compression_flag == "1":
            logger.debug(
                f"Found compressed DataWindow syntax (Syntax=(1)) in {self.name}. Attempting to inflate.",
            )
            try:
                # The syntax_data_b64 might have escaped quotes like \", convert them back.
                syntax_data_b64_cleaned = syntax_data_b64.replace('\\"', '"')

                # Ensure it's bytes for b64decode
                compressed_data = base64.b64decode(
                    syntax_data_b64_cleaned.encode("ascii"),
                )

                # Decompress
                decompressed_syntax_bytes = zlib.decompress(compressed_data)

                # The decompressed syntax is usually text
                encoding = "utf-16-le" if self.is_unicode_file_context else "latin1"
                try:
                    decompressed_syntax_str = decompressed_syntax_bytes.decode(encoding)
                except UnicodeDecodeError:
                    logger.warning(
                        f"Failed to decode inflated DataWindow syntax for {self.name} with {encoding}. Trying 'cp1252'.",
                    )
                    try:
                        decompressed_syntax_str = decompressed_syntax_bytes.decode(
                            "cp1252",
                        )
                    except UnicodeDecodeError:
                        logger.exception(
                            f"Failed to decode inflated DataWindow syntax for {self.name} with cp1252 as well. Storing as bytes repr.",
                        )
                        decompressed_syntax_str = f"<DECOMPRESSION_DECODE_ERROR: {decompressed_syntax_bytes!r}>"

                logger.info(
                    "Successfully inflated DataWindow syntax for %s.", self.name
                )

                # Replace the original Syntax=(1)"base64_data" with Syntax=(0)"inflated_data"
                escaped_decompressed_syntax = decompressed_syntax_str.replace(
                    '"',
                    '\\"',
                )

                # Reconstruct the full text content with the decompressed syntax
                new_syntax_block = f'Syntax=(0)"{escaped_decompressed_syntax}"'
                return text_content.replace(match.group(0), new_syntax_block, 1)

            except base64.binascii.Error as b64e:
                logger.exception(
                    f"Base64 decoding failed for DataWindow syntax in {self.name}: {b64e}. Content: '{syntax_data_b64[:100]}...'",
                )
            except zlib.error as ze:
                logger.exception(
                    f"Zlib decompression failed for DataWindow syntax in {self.name}: {ze}",
                )
            except Exception as e:
                logger.error(
                    f"Unexpected error during DataWindow syntax inflation for {self.name}: {e}",
                    exc_info=True,
                )
            # If any error, return original content
            return text_content
        # Syntax=(0) means it's already uncompressed
        logger.debug(
            f"DataWindow syntax in {self.name} is marked as uncompressed (Syntax=(0)).",
        )
        return text_content

    def __post_init__(self) -> None:
        # Process data_blocks to populate raw_text_content and raw_pcode
        full_text = get_text_from_data(self.data_blocks, self.is_unicode_file_context)

        # Validate total declared length against extracted text length
        declared_length = self.entry_definition.length
        if full_text is not None:
            actual_chars = len(full_text)
            expected_min_bytes = 0
            expected_max_bytes = 0

            if self.is_unicode_file_context:
                # For UTF-16LE, each char is 2 bytes. Null terminator is 2 bytes.
                expected_min_bytes = actual_chars * 2
                expected_max_bytes = actual_chars * 2 + 2
            else:
                # For ANSI (e.g., latin1, cp1252), each char is 1 byte
                expected_min_bytes = actual_chars
                expected_max_bytes = actual_chars + 1

            # Allow a small tolerance for block padding or minor discrepancies
            length_tolerance = 0
            if self.is_partial:
                length_tolerance = 16

            if not (
                expected_min_bytes
                <= declared_length
                <= expected_max_bytes + length_tolerance
            ):
                # If it's an SRD, the declared_length might be for the original compressed data
                is_srd_or_similar = self.name.lower().endswith((".srd", ".srw", ".sru"))
                DW_SYNTAX_REGEX = re.compile(r'Syntax=\((\d)\)"([^"]+)"', re.DOTALL)
                syntax_match_for_inflation_check = (
                    DW_SYNTAX_REGEX.search(full_text) if full_text else None
                )
                was_likely_inflated = (
                    is_srd_or_similar
                    and syntax_match_for_inflation_check
                    and syntax_match_for_inflation_check.group(1) == "0"
                )

                if not was_likely_inflated:
                    logger.warning(
                        f"Object '{self.name}': Declared length ({declared_length} bytes) vs. extracted text length "
                        f"({actual_chars} chars) discrepancy. "
                        f"Context: Unicode={self.is_unicode_file_context}, Partial={self.is_partial}. "
                        f"Expected byte range for {actual_chars} chars: [{expected_min_bytes} - {expected_max_bytes}]. "
                        f"Tolerance applied if partial: {length_tolerance if self.is_partial else 0} bytes.",
                    )
        elif declared_length > 0:
            logger.warning(
                f"Object '{self.name}': Declared length is {declared_length} bytes, but extracted text is None. "
                f"Context: Unicode={self.is_unicode_file_context}, Partial={self.is_partial}.",
            )

        # Attempt to inflate DataWindow syntax if present
        if full_text:
            full_text = self._try_inflate_datawindow_syntax(full_text)

        self.raw_text_content = full_text

        # Basic p-code extraction logic
        if (
            self.raw_text_content
            and self.entry_definition.commentlen > 0
            and len(self.raw_text_content) >= self.entry_definition.commentlen
        ):
            # Ensure commentlen does not exceed actual content length
            comment_len_safe = min(
                self.entry_definition.commentlen,
                len(self.raw_text_content),
            )
            self.raw_pcode = self.raw_text_content[comment_len_safe:]
        elif self.raw_text_content:
            self.raw_pcode = self.raw_text_content
        else:
            self.raw_pcode = ""  # Default to empty string

    @property
    def name(self) -> str:
        return self.entry_definition.object_name

    @property
    def version(self) -> str:
        return self.entry_definition.version

    @property
    def timestamp(self) -> Any:
        # datetime.datetime
        return self.entry_definition.moddatetime

    @property
    def comment(self) -> str | None:
        if self.raw_text_content and self.entry_definition.commentlen > 0:
            return self.raw_text_content[: self.entry_definition.commentlen]
        return None

    def extract_and_save_embedded_resources(
        self,
        output_dir: Path,
        resource_subdir_name: str = "resources",
    ) -> list[Path]:
        """Attempts to find and save embedded resources (like images) from this PBD object.
        Currently targets .srm (menu) objects by heuristic.

        Args:
            output_dir: The base directory where the object's primary content is saved.
            resource_subdir_name: The name of the subdirectory for resources.

        Returns:
            A list of paths to the saved resource files.
        """
        saved_resources: list[Path] = []
        # Heuristic: only attempt for .srm files for now
        if not self.name.lower().endswith(".srm"):
            return saved_resources

        # Ensure raw_binary_content is populated
        if self.raw_binary_content is None:
            self.raw_binary_content = get_binary_from_data(self.data_blocks)

        if not self.raw_binary_content:
            logger.debug(
                f"No raw binary content available to extract resources from {self.name}",
            )
            return saved_resources

        resource_path = output_dir / resource_subdir_name
        try:
            resource_path.mkdir(parents=True, exist_ok=True)
            logger.debug("Ensured resource directory exists: %s", resource_path)

            # Extract embedded images
            extracted = extract_embedded_images(
                data_bytes=self.raw_binary_content,
                base_filename=self.name,
                output_resource_dir=resource_path,
            )
            saved_resources.extend(extracted)
            if extracted:
                logger.info(
                    f"Found and saved {len(extracted)} resource(s) for {self.name} in {resource_path}",
                )

        except Exception as e:
            logger.error(
                f"Error creating resource directory or extracting resources for {self.name}: {e}",
                exc_info=True,
            )

        return saved_resources

    def get_content_hash(self) -> str | None:
        """Calculates and returns the SHA-1 hash of the object's primary content.
        Prefers raw_text_content (UTF-8 encoded) if available, otherwise uses raw_binary_content.
        Returns None if no content is available.
        """
        content_to_hash: str | bytes | None = None
        if self.raw_text_content is not None:
            content_to_hash = self.raw_text_content
        elif self.raw_binary_content is not None:
            content_to_hash = self.raw_binary_content
        elif self.data_blocks:
            # Fallback: try to get binary data if not already populated
            logger.debug(
                f"get_content_hash: raw_text/binary not set for {self.name}, trying get_binary_from_data.",
            )
            temp_binary_content = get_binary_from_data(self.data_blocks)
            if temp_binary_content:
                content_to_hash = temp_binary_content

        if content_to_hash is None:
            logger.warning(
                f"No content available to calculate hash for object: {self.name}",
            )
            return None

        return calculate_content_hash(content_to_hash)


def extract_embedded_images(
    data_bytes: bytes, base_filename: str, output_resource_dir: Path
) -> list[Path]:
    """Extract embedded images from binary data.

    Args:
        data_bytes: Binary data that may contain embedded images
        base_filename: Base name for extracted files (e.g., menu name)
        output_resource_dir: Directory to save extracted images

    Returns:
        List of paths to extracted image files
    """
    from src.extract.pbd.extraction import EnhancedImageExtractor

    saved_files = []
    try:
        extractor = EnhancedImageExtractor()
        images = extractor.find_images_in_data(data_bytes, base_filename)

        for i, image_info in enumerate(images):
            # Generate filename based on format and index
            image_filename = (
                f"{Path(base_filename).stem}_image_{i}.{image_info['format']}"
            )
            image_path = output_resource_dir / image_filename

            # Save the image data
            image_path.write_bytes(image_info["data"])
            saved_files.append(image_path)

            logger.debug(
                "Extracted %s image (%d bytes) to %s",
                image_info["format"],
                image_info["size"],
                image_path,
            )

    except Exception as e:
        logger.error(
            "Failed to extract images from %s: %s", base_filename, e, exc_info=True
        )

    return saved_files
