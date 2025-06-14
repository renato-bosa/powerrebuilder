import logging
import os
from dataclasses import dataclass
from typing import TYPE_CHECKING, Any, BinaryIO

from extract.pbd.exceptions import HeaderError
from extract.pbd.utils.binary_utils import (
    binary_to_int,
    binary_to_time,
    decode,
    extract_bytes_2_lst,
)

if TYPE_CHECKING:
    from collections.abc import Callable

logger = logging.getLogger(__name__)

# PBD/PBL Signature constants
PBD_SIGNATURE = b"PBD"
PBD_SIGNATURE_EXT = b"PBD\0"
PBL_SIGNATURE = b"PBL"
PBL_SIGNATURE_EXT = b"PBL\0"

# PBL/PBD Header structure
HEADER_CLASS_ATTR_NAMES = [
    "hdr_str",
    "pbl_name_str",
    "build_datetime_str",
    "create_timestamp_dt",
    "dep_lower_offset_int",
    "dep_upper_offset_int",
    "scc_data_offset_int",
    "reserved_int",
]

HEADER_BLOCK_SIZES_NON_UNICODE = [4, 64, 20, 4, 4, 4, 4, 4]
HEADER_BLOCK_SIZES_UNICODE = [8, 128, 40, 4, 4, 4, 4, 4]

HEADER_FUNCTORS_NON_UNICODE = [
    lambda x: decode(x, unicode=False, is_terminated=False),  # Signature string
    lambda x: decode(x, unicode=False, is_terminated=True),  # PBL Name/LibComment
    lambda x: decode(x, unicode=False, is_terminated=True),  # BuildDateTime
    binary_to_time,  # create_timestamp_dt
    binary_to_int,
    binary_to_int,
    binary_to_int,
    binary_to_int,
]

HEADER_FUNCTORS_UNICODE = [
    lambda x: decode(x, unicode=True, is_terminated=False),  # Signature string
    lambda x: decode(x, unicode=True, is_terminated=True),  # PBL Name/LibComment
    lambda x: decode(x, unicode=True, is_terminated=True),  # BuildDateTime
    binary_to_time,  # create_timestamp_dt
    binary_to_int,
    binary_to_int,
    binary_to_int,
    binary_to_int,
]


@dataclass(slots=True)
class HeaderClass:
    hdr_str: str
    pbl_name_str: str
    build_datetime_str: str
    create_timestamp_dt: (
        Any  # datetime.datetime, but Any for flexibility if parsing fails
    )
    dep_lower_offset_int: int
    dep_upper_offset_int: int
    scc_data_offset_int: int
    reserved_int: int
    is_unicode: bool
    first_nod_offset: int
    file_signature_bytes: bytes | None
    file_size: int | None = None  # New field for file size


def extract_pbl_header(
    file_input: BinaryIO | bytes,
    block_size: int,  # Added block_size parameter
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
    file_bytes_for_header: bytes | None = None
    input_file_size: int | None = None

    # Max possible header size + buffer for FRE* check, using the passed block_size.
    header_and_fre_check_len = max(
        sum(HEADER_BLOCK_SIZES_UNICODE), sum(HEADER_BLOCK_SIZES_NON_UNICODE)
    ) + (block_size * 2)

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
            handle.seek(original_pos)  # Restore position after reading header part

            if not file_path_for_error_log:
                file_path_for_error_log = f"<handle at {hex(id(handle))}>"
        except Exception as e:
            log_path = file_path_for_error_log or f"<handle at {hex(id(handle))}>"
            msg = f"Error reading from file handle {log_path}: {e!s}"
            raise HeaderError(msg)
    elif isinstance(file_input, bytes):
        file_bytes_for_header = file_input[
            :header_and_fre_check_len
        ]  # Take only necessary part
        input_file_size = len(file_input)  # Full size of the provided bytes
        if not file_path_for_error_log:
            file_path_for_error_log = "provided bytes"  # Generic name if no path given
    else:
        msg = f"Unsupported file_input type: {type(file_input)}. Expected BinaryIO or bytes."
        raise HeaderError(msg)

    if not file_bytes_for_header or len(file_bytes_for_header) == 0:
        msg = f"No header bytes to process for {file_path_for_error_log}."
        raise HeaderError(msg)

    # Determine initial properties based on signature
    detected_signature_bytes: bytes | None = None
    detected_signature_string: str = ""
    detected_is_unicode: bool = False

    # Max possible header size + buffer for FRE* check
    min_buf_len_for_detection = max(
        sum(HEADER_BLOCK_SIZES_UNICODE), sum(HEADER_BLOCK_SIZES_NON_UNICODE)
    ) + (block_size * 2)

    if (
        len(file_bytes_for_header) < min_buf_len_for_detection
    ):  # Check against bytes read for header
        logger.warning(
            f"Header data for {file_path_for_error_log} is short ({len(file_bytes_for_header)} bytes, need ~{min_buf_len_for_detection} for full check). Some detections might be limited."
        )

    # Signature detection (always do this, even if overridden, for storing actual signature)
    if file_bytes_for_header.startswith(b"HDR\\0"):  # Non-unicode
        detected_signature_bytes = file_bytes_for_header[:4]
        detected_signature_string = decode(
            detected_signature_bytes, unicode=False, is_terminated=False
        )
        detected_is_unicode = False
    elif file_bytes_for_header.startswith(b"HDR*"):  # Unicode
        detected_signature_bytes = file_bytes_for_header[
            :8
        ]  # Unicode signature is 8 bytes 'H\\0D\\0R\\0*\\0'
        detected_is_unicode = True
    else:
        peek_bytes = file_bytes_for_header[:8].hex()
        msg = f"Invalid PBL header signature for {file_path_for_error_log}. Expected HDR\\0 or HDR*. Got bytes: {peek_bytes}"
        raise HeaderError(msg)

    # Determine effective unicode mode and corresponding parsing parameters
    effective_is_unicode: bool
    header_block_sizes_to_use: list[int]
    base_functors_to_use: list[Callable[[bytes], Any]]
    initial_nod_offset: int  # NOD offset before FRE* check

    # unicode_flag_override was removed, so effective_is_unicode is always detected_is_unicode
    effective_is_unicode = detected_is_unicode

    if effective_is_unicode:
        header_block_sizes_to_use = HEADER_BLOCK_SIZES_UNICODE
        base_functors_to_use = HEADER_FUNCTORS_UNICODE
        initial_nod_offset = block_size * 2
    else:  # Non-Unicode
        header_block_sizes_to_use = HEADER_BLOCK_SIZES_NON_UNICODE
        base_functors_to_use = HEADER_FUNCTORS_NON_UNICODE
        initial_nod_offset = block_size

    # Adjust first_nod_offset for FRE* block if applicable (only for HDR* files)
    final_first_nod_offset = initial_nod_offset
    if detected_is_unicode:  # FRE* check only relevant for HDR* files
        fre_check_offset = (
            block_size * 2
        )  # FRE* is expected after the Unicode header placeholder
        if (
            len(file_bytes_for_header) >= fre_check_offset + 4
        ):  # Need at least 4 bytes for 'FRE*'
            potential_fre_block_sig_ascii_bytes = file_bytes_for_header[
                fre_check_offset : fre_check_offset + 4
            ]
            if potential_fre_block_sig_ascii_bytes == b"FRE*":
                logger.info(
                    f"HDR* file ({file_path_for_error_log}): ASCII FRE* signature found at offset {fre_check_offset}. Adjusting first NOD offset by +{block_size} bytes."
                )
                final_first_nod_offset = initial_nod_offset + block_size
            else:
                logger.info(
                    f"HDR* file ({file_path_for_error_log}): No ASCII FRE* signature found at offset {fre_check_offset}. Bytes found (first 4): {potential_fre_block_sig_ascii_bytes.hex() if potential_fre_block_sig_ascii_bytes else 'None'}"
                )
        else:
            logger.warning(
                f"HDR* file ({file_path_for_error_log}): Buffer too short (len {len(file_bytes_for_header)}) to check for FRE* signature at offset {fre_check_offset}."
            )

    # Parse the header fields
    required_header_len = sum(header_block_sizes_to_use)
    if len(file_bytes_for_header) < required_header_len:
        msg = f"File buffer for {file_path_for_error_log} too short for PBL header. Need {required_header_len}, have {len(file_bytes_for_header)} bytes."
        raise HeaderError(msg)

    # The first functor (for hdr_str) needs to use the effective_is_unicode to decode the signature string itself
    actual_functors = list(base_functors_to_use)
    # Use the first N bytes of file_bytes_for_header (sig length) for hdr_str, decoded with effective_is_unicode
    # This ensures hdr_str reflects the parsing mode, not necessarily the raw detected_signature_string
    # For example, if overriding an HDR* to be parsed as non-Unicode, hdr_str should be 'HDR*'.
    # If overriding HDR\\0 to be parsed as Unicode, it will likely be 'H\\0D\\0R\\0'.
    # The 'signature_bytes' field in HeaderClass stores the *actual* detected bytes.

    # Let's refine how hdr_str is set:
    # It should generally be the string representation of the *detected* signature.
    # If HDR*, hdr_str should be 'HDR*'. If HDR\\0, it should be 'HDR\\0'.
    # The effective_is_unicode then governs how pbl_name_str etc. are decoded.
    hdr_str_to_store = (
        detected_signature_string  # This is 'HDR\\0' or the log version 'HDR*'
    )
    if (
        detected_is_unicode and hdr_str_to_store == "HDR*"
    ):  # ensure it's the unicode representation if detected as unicode
        pass  # detected_signature_string is already correct for unicode if it was "HDR*" (it's a placeholder name)
        # actual_functors[0] will decode it correctly based on effective_is_unicode

    actual_functors[0] = lambda x_sig_bytes: decode(
        x_sig_bytes, unicode=effective_is_unicode, is_terminated=False
    )

    # We need to ensure the signature bytes passed to the lambda are correct length for effective_is_unicode
    header_block_sizes_to_use[0]

    parsed_header_fields = extract_bytes_2_lst(
        file_bytes_for_header[:required_header_len],
        header_block_sizes_to_use,
        actual_functors,
    )

    if len(parsed_header_fields) != len(
        HEADER_CLASS_ATTR_NAMES
    ):  # Compares against the expected number of base fields
        msg = f"Header parsing for {file_path_for_error_log} failed, expected {len(HEADER_CLASS_ATTR_NAMES)} fields, got {len(parsed_header_fields)}: {parsed_header_fields}"
        raise HeaderError(msg)

    # If the first field (parsed hdr_str) is different from detected_signature_string due to override, log it.
    # This is complex because decode(detected_signature_bytes, unicode=effective_is_unicode) is what gets stored.
    # The key is that `detected_signature_string` (from initial check) and `detected_signature_bytes` are ground truth of file.
    # `effective_is_unicode` is how we *interpret* the rest of the header.
    # `parsed_header_fields[0]` will be the signature string as decoded by `effective_is_unicode`.

    # Re-assigning hdr_str to be the string of the *detected* signature for clarity.
    # The parsing functions for other fields use effective_is_unicode.
    parsed_header_fields[0] = detected_signature_string

    final_header_values = [
        *parsed_header_fields,
        effective_is_unicode,
        final_first_nod_offset,
        detected_signature_bytes,
        input_file_size,
    ]

    try:
        header_obj = HeaderClass(*final_header_values)
    except TypeError as e:
        # For dataclasses, field names are in __dataclass_fields__
        expected_fields_info = (
            HeaderClass.__dataclass_fields__
            if hasattr(HeaderClass, "__dataclass_fields__")
            else "unknown (not a dataclass or no fields)"
        )
        logger.exception(
            f"TypeError during HeaderClass instantiation for {file_path_for_error_log}. Values count: {len(final_header_values)}, HeaderClass expects fields: {expected_fields_info}. Error: {e}"
        )
        logger.exception(f"Values provided: {final_header_values}")
        msg = f"Failed to create HeaderClass object for {file_path_for_error_log}. Values: {final_header_values}. Error: {e}"
        raise HeaderError(msg)

    return header_obj
