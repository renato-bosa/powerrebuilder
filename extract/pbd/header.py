import logging
from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from extract.pbd.exceptions import HeaderError
from extract.pbd.utils import (
    BLOCK_SIZE,
    bin2int,
    bin2time,
    decode,
    extract_bytes_2_lst,
    retrieve_bytes_from_file,
)

logger = logging.getLogger(__name__)

# PBL/PBD Header structure
HEADER_CLASS_ATTR_NAMES = [
    "hdr_str", "pbl_name_str", "build_datetime_str", "create_timestamp_dt",
    "dep_lower_offset_int", "dep_upper_offset_int", "scc_data_offset_int", "reserved_int",
]

HEADER_BLOCK_SIZES_NON_UNICODE = [4, 64, 20, 4, 4, 4, 4, 4]
HEADER_BLOCK_SIZES_UNICODE = [8, 128, 40, 4, 4, 4, 4, 4]

HEADER_FUNCTORS_NON_UNICODE = [
    lambda x: decode(x, unicode=False, is_terminated=False),  # Signature string
    lambda x: decode(x, unicode=False, is_terminated=True),  # PBL Name/LibComment
    lambda x: decode(x, unicode=False, is_terminated=True),  # BuildDateTime
    bin2time,  # create_timestamp_dt
    bin2int,
    bin2int,
    bin2int,
    bin2int,
]

HEADER_FUNCTORS_UNICODE = [
    lambda x: decode(x, unicode=True, is_terminated=False),  # Signature string
    lambda x: decode(x, unicode=True, is_terminated=True),   # PBL Name/LibComment
    lambda x: decode(x, unicode=True, is_terminated=True),   # BuildDateTime
    bin2time,  # create_timestamp_dt
    bin2int,
    bin2int,
    bin2int,
    bin2int,
]


@dataclass
class HeaderClass:
    hdr_str: str
    pbl_name_str: str
    build_datetime_str: str
    create_timestamp_dt: Any  # datetime.datetime, but Any for flexibility if parsing fails
    dep_lower_offset_int: int
    dep_upper_offset_int: int
    scc_data_offset_int: int
    reserved_int: int
    is_unicode: bool
    first_nod_offset: int
    file_signature_bytes: bytes | None


def extract_pbl_header(
    file_content: str | Path | bytes,
    unicode_flag_override: bool | None = None,
    file_path_for_error_log: str | None = None,
) -> HeaderClass:
    """Extract the header information from a PowerBuilder file.

    Args:
        file_content: File path, bytes, or file-like object.
        unicode_flag_override: If True/False, forces unicode mode for header parsing,
                               overriding signature-based detection.
        file_path_for_error_log: Path to use in error messages if file_content is bytes.

    Returns:
        HeaderClass object with header information.
    """
    actual_file_path_str = file_path_for_error_log
    file_bytes: bytes | None = None

    if isinstance(file_content, str | Path):
        if not actual_file_path_str:
            actual_file_path_str = str(file_content)
        try:
            file_bytes = retrieve_bytes_from_file(file_content, 0, -1)  # Read all bytes
            if not file_bytes:
                 raise HeaderError(f"Empty or unreadable file: {actual_file_path_str}")
        except FileNotFoundError:
            raise HeaderError(f"PBL file not found: {actual_file_path_str}")
        except Exception as e:
            raise HeaderError(f"Error reading file {actual_file_path_str}: {str(e)}")
    elif isinstance(file_content, bytes):
        file_bytes = file_content
        if not actual_file_path_str:
            actual_file_path_str = "provided bytes"  # Generic name if no path given
    else:
        raise HeaderError(f"Unsupported file_content type: {type(file_content)}")

    if not file_bytes:  # Should be caught earlier, but as a safeguard
        raise HeaderError(f"No file bytes to process for {actual_file_path_str}.")

    # Determine initial properties based on signature
    detected_signature_bytes: bytes | None = None
    detected_signature_string: str = ""
    detected_is_unicode: bool = False

    # Max possible header size + buffer for FRE* check
    min_buf_len_for_detection = max(sum(HEADER_BLOCK_SIZES_UNICODE), sum(HEADER_BLOCK_SIZES_NON_UNICODE)) + (BLOCK_SIZE * 2)

    if len(file_bytes) < min_buf_len_for_detection:
         logger.warning(f"File buffer for {actual_file_path_str} is short ({len(file_bytes)} bytes, need ~{min_buf_len_for_detection}). Some detections might be limited.")

    # Signature detection (always do this, even if overridden, for storing actual signature)
    if file_bytes.startswith(b"HDR\\0"):  # Non-unicode
        detected_signature_bytes = file_bytes[:4]
        detected_signature_string = decode(detected_signature_bytes, unicode=False, is_terminated=False)
        detected_is_unicode = False
    elif file_bytes.startswith(b"HDR*"):  # Unicode
        detected_signature_bytes = file_bytes[:8]  # Unicode signature is 8 bytes 'H\\0D\\0R\\0*\\0'
        # The HDR* text itself, for hdr_str field, is typically ASCII 'HDR*'
        # For consistency, let's store the bytes and decode the hdr_str field later based on chosen unicode mode.
        # For now, let's assume the 'HDR*' string for logging/debug is based on ASCII for this specific signature part
        detected_signature_string_for_log = "HDR*"
        detected_is_unicode = True
    else:
        peek_bytes = file_bytes[:8].hex()
        raise HeaderError(f"Invalid PBL header signature for {actual_file_path_str}. Expected HDR\\0 or HDR*. Got bytes: {peek_bytes}")

    # Determine effective unicode mode and corresponding parsing parameters
    effective_is_unicode: bool
    header_block_sizes_to_use: list[int]
    base_functors_to_use: list[Callable[[bytes], Any]]
    initial_nod_offset: int  # NOD offset before FRE* check

    if unicode_flag_override is not None:
        effective_is_unicode = unicode_flag_override
        if effective_is_unicode != detected_is_unicode:
            logger.warning(f"Unicode flag for {actual_file_path_str} overridden to {effective_is_unicode}, "
                           f"which differs from detected signature ('{detected_signature_string_for_log if detected_is_unicode else detected_signature_string}', implies unicode={detected_is_unicode}).")
    else:
        effective_is_unicode = detected_is_unicode

    if effective_is_unicode:
        header_block_sizes_to_use = HEADER_BLOCK_SIZES_UNICODE
        base_functors_to_use = HEADER_FUNCTORS_UNICODE
        initial_nod_offset = BLOCK_SIZE * 2
    else:  # Non-Unicode
        header_block_sizes_to_use = HEADER_BLOCK_SIZES_NON_UNICODE
        base_functors_to_use = HEADER_FUNCTORS_NON_UNICODE
        initial_nod_offset = BLOCK_SIZE

    # Adjust first_nod_offset for FRE* block if applicable (only for HDR* files)
    final_first_nod_offset = initial_nod_offset
    if detected_is_unicode:  # FRE* check only relevant for HDR* files
        fre_check_offset = BLOCK_SIZE * 2  # FRE* is expected after the Unicode header placeholder
        if len(file_bytes) >= fre_check_offset + 4:  # Need at least 4 bytes for 'FRE*'
            potential_fre_block_sig_ascii_bytes = file_bytes[fre_check_offset : fre_check_offset + 4]
            if potential_fre_block_sig_ascii_bytes == b'FRE*':
                logger.info(f"HDR* file ({actual_file_path_str}): ASCII FRE* signature found at offset {fre_check_offset}. Adjusting first NOD offset by +{BLOCK_SIZE} bytes.")
                final_first_nod_offset = initial_nod_offset + BLOCK_SIZE
            else:
                logger.info(f"HDR* file ({actual_file_path_str}): No ASCII FRE* signature found at offset {fre_check_offset}. Bytes found (first 4): {potential_fre_block_sig_ascii_bytes.hex() if potential_fre_block_sig_ascii_bytes else 'None'}")
        else:
            logger.warning(f"HDR* file ({actual_file_path_str}): Buffer too short (len {len(file_bytes)}) to check for FRE* signature at offset {fre_check_offset}.")

    # Parse the header fields
    required_header_len = sum(header_block_sizes_to_use)
    if len(file_bytes) < required_header_len:
        raise HeaderError(f"File buffer for {actual_file_path_str} too short for PBL header. Need {required_header_len}, have {len(file_bytes)} bytes.")

    # The first functor (for hdr_str) needs to use the effective_is_unicode to decode the signature string itself
    actual_functors = list(base_functors_to_use)
    # Use the first N bytes of file_bytes (sig length) for hdr_str, decoded with effective_is_unicode
    # This ensures hdr_str reflects the parsing mode, not necessarily the raw detected_signature_string
    # For example, if overriding an HDR* to be parsed as non-Unicode, hdr_str should be 'HDR*'.
    # If overriding HDR\\0 to be parsed as Unicode, it will likely be 'H\\0D\\0R\\0'.
    # The 'signature_bytes' field in HeaderClass stores the *actual* detected bytes.

    # Let's refine how hdr_str is set:
    # It should generally be the string representation of the *detected* signature.
    # If HDR*, hdr_str should be 'HDR*'. If HDR\\0, it should be 'HDR\\0'.
    # The effective_is_unicode then governs how pbl_name_str etc. are decoded.
    hdr_str_to_store = detected_signature_string  # This is 'HDR\\0' or the log version 'HDR*'
    if detected_is_unicode and hdr_str_to_store == "HDR*":  # ensure it's the unicode representation if detected as unicode
         pass  # detected_signature_string is already correct for unicode if it was "HDR*" (it's a placeholder name)
              # actual_functors[0] will decode it correctly based on effective_is_unicode

    actual_functors[0] = lambda x_sig_bytes: decode(x_sig_bytes, unicode=effective_is_unicode, is_terminated=False)

    # We need to ensure the signature bytes passed to the lambda are correct length for effective_is_unicode
    header_block_sizes_to_use[0]

    parsed_header_fields = extract_bytes_2_lst(file_bytes[:required_header_len], header_block_sizes_to_use, actual_functors)

    if len(parsed_header_fields) != len(HEADER_CLASS_ATTR_NAMES):  # Compares against the expected number of base fields
        raise HeaderError(f"Header parsing for {actual_file_path_str} failed, expected {len(HEADER_CLASS_ATTR_NAMES)} fields, got {len(parsed_header_fields)}: {parsed_header_fields}")

    # If the first field (parsed hdr_str) is different from detected_signature_string due to override, log it.
    # This is complex because decode(detected_signature_bytes, unicode=effective_is_unicode) is what gets stored.
    # The key is that `detected_signature_string` (from initial check) and `detected_signature_bytes` are ground truth of file.
    # `effective_is_unicode` is how we *interpret* the rest of the header.
    # `parsed_header_fields[0]` will be the signature string as decoded by `effective_is_unicode`.

    # Re-assigning hdr_str to be the string of the *detected* signature for clarity.
    # The parsing functions for other fields use effective_is_unicode.
    parsed_header_fields[0] = detected_signature_string

    final_header_values = parsed_header_fields + [effective_is_unicode, final_first_nod_offset, detected_signature_bytes]

    try:
        header_obj = HeaderClass(*final_header_values)
    except TypeError as e:
        # For dataclasses, field names are in __dataclass_fields__
        expected_fields_info = HeaderClass.__dataclass_fields__ if hasattr(HeaderClass, '__dataclass_fields__') else 'unknown (not a dataclass or no fields)'
        logger.error(f"TypeError during HeaderClass instantiation for {actual_file_path_str}. Values count: {len(final_header_values)}, HeaderClass expects fields: {expected_fields_info}. Error: {e}")
        logger.error(f"Values provided: {final_header_values}")
        raise HeaderError(f"Failed to create HeaderClass object for {actual_file_path_str}. Values: {final_header_values}. Error: {e}")

    return header_obj
