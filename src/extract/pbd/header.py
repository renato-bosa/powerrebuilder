"""PowerBuilder file header parsing."""

import logging
import os
from collections.abc import Callable
from dataclasses import dataclass
from datetime import datetime
from typing import Any, BinaryIO

from src.core.exceptions import HeaderError
from src.extract.utils.binary import (
    binary_to_datetime,
    binary_to_int,
    decode,
    extract_variable_fields,
)

logger = logging.getLogger(__name__)

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
    create_timestamp_dt: datetime | None
    dep_lower_offset_int: int
    dep_upper_offset_int: int
    scc_data_offset_int: int
    reserved_int: int
    is_unicode: bool
    first_nod_offset: int
    file_signature_bytes: bytes | None
    file_size: int | None = None  # New field for file size
    extract_resources: bool = True  # Whether to extract embedded resources


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
            handle.seek(original_pos)  # Reset to original position

            # Read enough bytes for header parsing
            handle.seek(0)  # Go to start to read header
            file_bytes_for_header = handle.read(header_and_fre_check_len)
            # Restore position after reading header part
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
        # Look for ASCII FRE* signature at typical offsets (block_size * 2)
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
    # Check for FRE* block regardless of Unicode detection
    # Mixed-format files (HDR* with ASCII content) also need FRE* adjustment

    fre_check_offset = block_size * 2

    if len(file_bytes_for_header) >= fre_check_offset + 4:
        potential_fre_block_sig = file_bytes_for_header[
            fre_check_offset : fre_check_offset + 4
        ]
        if potential_fre_block_sig == b"FRE*":
            # NOD should be after the FRE* block, which is at fre_check_offset
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
