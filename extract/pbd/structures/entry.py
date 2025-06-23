import contextlib
import datetime
import logging
from dataclasses import dataclass
from typing import TYPE_CHECKING, Any, BinaryIO

from common.constants import BUFFER_SIZE, HEADER_SIZE, STRING_TABLE_OFFSET
from extract.pbd.structures.enhanced_entry_parser import EnhancedEntryParser
from extract.pbd.utils.binary_utils import (
    binary_to_int,
    binary_to_time,
    decode,
    extract_bytes_2_lst,
    retrieve_bytes_from_file,
)

if TYPE_CHECKING:
    from collections.abc import Callable

logger = logging.getLogger(__name__)

# Global enhanced parser instance
_enhanced_parser = None

def get_enhanced_parser() -> EnhancedEntryParser:






    """Get or create the global enhanced parser instance."""
    global _enhanced_parser
    if _enhanced_parser is None:
        _enhanced_parser = EnhancedEntryParser(enable_recovery=True)
    return _enhanced_parser


@dataclass(slots=True)
class PbEntryDefinition:
    objectname: str
    version: str
    offset: int
    objectsize: int
    moddatetime: datetime.datetime
    commentlen: int
    objnamelen: int


def extract_entry_def(arr: bytes) -> PbEntryDefinition | None: 




    FIXED_PART_LEN= 24
    try:
        if len(arr) < FIXED_PART_LEN:
            logger.debug(
                f"extract_entry_def: Data too short for fixed part ({len(arr)} < {FIXED_PART_LEN}).",
            )
            return None

        sig_bytes = arr[0:4]
        try:
            sig_str = sig_bytes.decode("ascii")
        except UnicodeDecodeError:
            logger.debug(
                f"extract_entry_def: ENT* signature not valid ASCII. Bytes (hex): {sig_bytes.hex()}",
            )
            # Potentially raise PbdEntryError("Invalid ASCII signature encoding") if this should halt further processing
            return None

        if sig_str != "ENT*":
            logger.debug(
                f"extract_entry_def: Invalid or missing ENT signature. Got '{sig_str}'. Bytes (hex): {sig_bytes.hex()}",
            )
            # Potentially raise PbdEntryError("Invalid ENT* signature")
            return None

        # Core parsing logic susceptible to data errors
        try:
            ver_str = decode(arr[4:8], unicode=False)
            offset_int = binary_to_int(arr[8:12])
            obj_size_int = binary_to_int(arr[12:16])
            mod_time_int_bytes = arr[16:20]
            mod_time_dt = binary_to_time(mod_time_int_bytes)
            comment_len_int = binary_to_int(arr[20:22])
            obj_name_actual_len = binary_to_int(arr[22:24])

            # Validate object name length - PowerBuilder object names are typically < 512 bytes
            MAX_REASONABLE_NAME_LEN = 512
            if obj_name_actual_len > MAX_REASONABLE_NAME_LEN:
                logger.warning(
                    f"extract_entry_def: Object name length ({obj_name_actual_len}) exceeds reasonable maximum ({MAX_REASONABLE_NAME_LEN}). "
                    f"This likely indicates corrupted entry data. First 64 bytes (hex): {arr[:64].hex()}",
                )
                return None  # Entry is corrupted

            name_start_offset = FIXED_PART_LEN
            if name_start_offset + obj_name_actual_len > len(arr):
                logger.warning(
                    f"extract_entry_def: Object name length ({obj_name_actual_len}) exceeds available data ({len(arr) - name_start_offset} bytes remain after fixed part). Data (hex): {arr.hex()}",
                )
                obj_name_bytes = arr[name_start_offset:]
                obj_name_str = decode(obj_name_bytes, unicode=False) + " <TRUNCATED>"
                # This is a data issue, could raise PbdEntryError for truncation if strict
            else:
                obj_name_bytes = arr[
                    name_start_offset : name_start_offset + obj_name_actual_len
                ]
                obj_name_str = decode(obj_name_bytes, unicode=False)
        except (
            ValueError, TypeError, IndexError, ) as e_parse:  # Catch specific parsing/conversion errors
            logger.exception(
                f"extract_entry_def: Error parsing entry field. Error: {e_parse}. Data (hex): {arr[: FIXED_PART_LEN + 10].hex()}",
            )
            # Optionally: raise PbdEntryError(f"Failed to parse entry field: {e_parse}") from e_parse
            return None

        return PbEntryDefinition(
            objectname=obj_name_str, version=ver_str, offset=offset_int, objectsize=obj_size_int, moddatetime=mod_time_dt, commentlen=comment_len_int, objnamelen=obj_name_actual_len, )
    except Exception:  # Catch any other unexpected errors
        logger.exception(
            f"extract_entry_def: Unexpected exception during parsing. Data (hex): {arr[: FIXED_PART_LEN + 10].hex()}",
        )
        # Optionally: raise PbdEntryError(f"Unexpected error: {e}") from e
        return None


def extract_entry_def_unicode(arr: bytes) -> PbEntryDefinition | None: 




    FIXED_PART_LEN= 48
    try:
        if len(arr) < FIXED_PART_LEN:
            logger.debug(
                f"extract_entry_def_unicode: Data too short for fixed part ({len(arr)} < {FIXED_PART_LEN}).",
            )
            return None

        # Check for both Unicode and ASCII signatures
        # Some Unicode PBD files use ASCII signatures for entries
        sig_bytes = arr[0:8]
        sig_str = None

        # First try Unicode signature
        with contextlib.suppress(UnicodeDecodeError):
            sig_str = decode(sig_bytes, unicode=True)

        # If not Unicode signature, check if it's ASCII signature in first 4 bytes
        if sig_str != "ENT*":
            ascii_sig_bytes = arr[0:4]
            try:
                ascii_sig_str = ascii_sig_bytes.decode("ascii")
                if ascii_sig_str == "ENT*":
                    # This is ASCII signature with Unicode data format
                    # Call the appropriate handler
                    return extract_entry_def_ascii_sig_unicode_data(arr)
            except UnicodeDecodeError:
                pass

        if sig_str != "ENT*":
            logger.debug(
                f"extract_entry_def_unicode: Invalid or missing ENT signature. Got '{sig_str}'. Bytes (hex): {sig_bytes.hex()}",
            )
            return None

        # Core parsing logic susceptible to data errors
        try:
            ver_str = decode(arr[8:16], unicode=True)
            offset_int = binary_to_int(arr[16:24])
            obj_size_int = binary_to_int(arr[24:32])
            mod_time_int_bytes = arr[32:40]
            mod_time_dt = binary_to_time(mod_time_int_bytes)
            comment_len_int = binary_to_int(arr[40:44])
            obj_name_actual_len = binary_to_int(arr[44:48])

            # Validate object name length - PowerBuilder object names are typically < 512 characters
            MAX_REASONABLE_NAME_LEN_CHARS = 512
            if obj_name_actual_len > MAX_REASONABLE_NAME_LEN_CHARS:
                logger.warning(
                    f"extract_entry_def_unicode: Object name length ({obj_name_actual_len} chars) exceeds reasonable maximum ({MAX_REASONABLE_NAME_LEN_CHARS}). "
                    f"This likely indicates corrupted entry data. First 64 bytes (hex): {arr[:64].hex()}",
                )
                return None  # Entry is corrupted

            name_start_offset = FIXED_PART_LEN
            obj_name_bytes_len = obj_name_actual_len * 2

            if name_start_offset + obj_name_bytes_len > len(arr):
                logger.warning(
                    f"extract_entry_def_unicode: Object name length ({obj_name_actual_len} chars / {obj_name_bytes_len} bytes) exceeds available data ({len(arr) - name_start_offset} bytes remain). Data (hex): {arr.hex()}",
                )
                obj_name_bytes = arr[name_start_offset:]
                obj_name_str = decode(obj_name_bytes, unicode=True) + " <TRUNCATED>"
                # Potentially raise PbdEntryError for truncation
            else:
                obj_name_bytes = arr[
                    name_start_offset : name_start_offset + obj_name_bytes_len
                ]
                obj_name_str = decode(obj_name_bytes, unicode=True)
        except (
            ValueError, TypeError, IndexError, ) as e_parse:  # Catch specific parsing/conversion errors
            logger.exception(
                f"extract_entry_def_unicode: Error parsing entry field. Error: {e_parse}. Data (hex): {arr[: FIXED_PART_LEN + 10].hex()}",
            )
            # Optionally: raise PbdEntryError(f"Failed to parse entry field: {e_parse}") from e_parse
            return None

        return PbEntryDefinition(
            objectname=obj_name_str, version=ver_str, offset=offset_int, objectsize=obj_size_int, moddatetime=mod_time_dt, commentlen=comment_len_int, objnamelen=obj_name_actual_len, )
    except Exception:  # Catch any other unexpected errors
        logger.exception(
            f"extract_entry_def_unicode: Unexpected exception during parsing. Data (hex): {arr[: FIXED_PART_LEN + 10].hex()}",
        )
        # Optionally: raise PbdEntryError(f"Unexpected error: {e}") from e
        return None


def _parse_unicode_string(arr: bytes, offset: int) -> tuple[str, int] | None:








    """Parse a null-terminated UTF-16LE string."""
    for i in range(offset, len(arr) - 1, 2):
        if arr[i] == 0 and arr[i + 1] == 0:
            length = i - offset + 2
            string_bytes = arr[offset:offset + length]
            string_value = decode(string_bytes, unicode=True)
            return string_value, length
    return None

def _parse_ascii_signature(arr: bytes, offset: int) -> str | None:






    """Parse 4-byte ASCII signature."""
    if offset + 4 > len(arr):
        return None
    sig_bytes = arr[offset:offset + 4]
    try:
        return sig_bytes.decode("ascii")
    except UnicodeDecodeError:
        return None

def _parse_field(arr: bytes, offset: int, length: int, field_name: str, converter = None) -> tuple:



    """Parse a field with bounds checking and optional conversion."""
    if offset + length > len(arr):
        logger.debug("extract_entry_def_mixed_mode: EOF before %s (%s bytes expected at offset %s)", field_name, length, offset)
        return None, offset

    field_bytes = arr[offset:offset + length]
    field_value = converter(field_bytes) if converter else field_bytes
    logger.debug("extract_entry_def_mixed_mode: Parsed %s - Offset: %s, Value: %s", field_name, offset, field_value)
    return field_value, offset + length

def extract_entry_def_mixed_mode(arr: bytes) -> PbEntryDefinition | None: 



    logger.debug("extract_entry_def_mixed_mode: Input arr (first 128 bytes hex): %s", arr[:128].hex())

    try:
        current_offset = 0

        # Parse object name (UTF-16LE, null-terminated)
        result = _parse_unicode_string(arr, current_offset)
        if not result:
            logger.debug("extract_entry_def_mixed_mode: No UTF-16LE null terminator found for object name.")
            return None
        obj_name_str, obj_name_bytes_len = result
        current_offset += obj_name_bytes_len

        # Parse ENT* signature
        sig_str = _parse_ascii_signature(arr, current_offset)
        if sig_str != "ENT*":
            logger.debug("extract_entry_def_mixed_mode: Invalid signature. Found: '%s'", sig_str)
            return None
        current_offset += 4

        # Parse version (8 bytes, UTF-16LE)
        ver_str, current_offset = _parse_field(arr, current_offset, 8, "version", lambda b: decode(b, unicode=True))
        if ver_str is None:
            return None

        # Parse offset (4 bytes, integer)
        offset_int, current_offset = _parse_field(arr, current_offset, 4, "offset", binary_to_int)
        if offset_int is None:
            return None

        # Parse object size (4 bytes, integer)
        obj_size_int, current_offset = _parse_field(arr, current_offset, 4, "obj_size", binary_to_int)
        if obj_size_int is None:
            return None

        # Parse modification time (4 bytes, datetime)
        mod_time_dt, current_offset = _parse_field(arr, current_offset, 4, "mod_time", binary_to_time)
        if mod_time_dt is None:
            return None

        # Parse comment length (2 bytes, integer)
        comment_len_int, current_offset = _parse_field(arr, current_offset, 2, "comment_len", binary_to_int)
        if comment_len_int is None:
            return None

        logger.info("extract_entry_def_mixed_mode: Successfully parsed entry for '%s'. "
                   "Offset: %s, Content Size: %s, Version: '%s'", obj_name_str, offset_int, obj_size_int, ver_str,)

        return PbEntryDefinition(
            objectname=obj_name_str, version=ver_str, offset=offset_int, objectsize=obj_size_int, moddatetime=mod_time_dt, commentlen=comment_len_int, objnamelen=obj_name_bytes_len, )

    except (ValueError, TypeError, IndexError, UnicodeDecodeError) as e:
        logger.exception("extract_entry_def_mixed_mode: Error parsing entry field. Error: %s", e)
        return None
    except Exception as e:
        logger.exception("extract_entry_def_mixed_mode: Unexpected exception during parsing. Error: %s", e)
        return None


def extract_entry_def_ascii_sig_unicode_data(arr: bytes) -> PbEntryDefinition | None:








    """Extract entry with ASCII ENT* signature but Unicode version and name.

    Structure:
    - 4 bytes: ASCII "ENT*" signature
    - 8 bytes: Unicode version string (e.g., "0.6.0.0")
    - 4 bytes: data_offset
    - 4 bytes: data_size
    - 4 bytes: timestamp
    - 2 bytes: comment_len (char count)
    - 2 bytes: name_len (char count)
    - Variable: comment (comment_len × 2 bytes for unicode)
    - Variable: name (name_len × 2 bytes for unicode)
    - Padding: 0-3 bytes to maintain 4-byte alignment
    """
    import struct

    try:
        if len(arr) < 28:  # Minimum header size (4+8+4+4+4+2+2)
            logger.debug(
                f"extract_entry_def_ascii_sig_unicode_data: Data too short ({len(arr)} < 28).",
            )
            return None

        # Check ASCII signature
        if arr[0:4] != b"ENT*":
            logger.debug(
                f"extract_entry_def_ascii_sig_unicode_data: Invalid signature. Got {arr[0:4].hex()}",
            )
            return None

        # Parse version string (Unicode)
        try:
            version_str = arr[4:12].decode("utf-16-le", errors="ignore").rstrip("\x00")
        except Exception as e:
            version_str = "0.6.0.0"

        # Parse fixed header fields
        pos = 12
        data_offset, data_size, timestamp, comment_len, name_len = struct.unpack_from(
            "<IIIHH", arr, pos,
        )
        pos += 16  # 4+4+4+2+2

        # Skip comment (we don't use it but need to advance position)
        comment_bytes = comment_len  # comment_len is already in bytes for this format
        if pos + comment_bytes > len(arr):
            logger.debug(
                f"extract_entry_def_ascii_sig_unicode_data: Comment extends beyond data at pos {pos}, comment_len={comment_len}.",
            )
            return None
        pos += comment_bytes

        # Read name
        name_bytes = name_len  # name_len is already in bytes for this format
        if pos + name_bytes > len(arr):
            logger.warning(
                "extract_entry_def_ascii_sig_unicode_data: Name extends beyond data.",
            )
            raw_name = arr[pos:]
            obj_name = raw_name.decode("utf-16-le", errors="ignore").rstrip("\x00")
        else:
            raw_name = arr[pos : pos + name_bytes]
            obj_name = raw_name.decode("utf-16-le", errors="ignore").rstrip("\x00")

        # Convert timestamp
        mod_time_dt = binary_to_time(struct.pack("<I", timestamp))

        return PbEntryDefinition(
            objectname=obj_name, version=version_str, offset=data_offset, objectsize=data_size, moddatetime=mod_time_dt, commentlen=comment_len, objnamelen=name_len // 2, # Store as character count for consistency
        )

    except Exception as e:
        logger.exception(
            f"extract_entry_def_ascii_sig_unicode_data: Unexpected error: {e}",
        )
        return None


def get_entry_size_ascii_sig_unicode(arr: bytes) -> int:








    """Calculate the total size of an entry including padding for 2-byte alignment."""
    import struct

    if len(arr) < 28 or arr[0:4] != b"ENT*":
        return 0

    # Get comment and name lengths
    _, _, _, comment_len, name_len = struct.unpack_from("<IIIHH", arr, 12)

    # Calculate position after name
    pos = 28  # Fixed header (4 + 8 + 4 + 4 + 4 + 2 + 2)
    pos += comment_len  # comment_len is already in bytes
    pos += name_len  # name_len is already in bytes

    # Align to 2-byte boundary (not 4-byte)
    return (pos + 1) & ~1


def extract_object_name_len_from_entry(entry: bytes) -> int:





    blocks = [4, 4, 4, 4, 4, 2, 2]
    functors: list[Callable[[bytes], Any]] = [
        decode, decode, binary_to_int, binary_to_int, binary_to_time, binary_to_int, binary_to_int, ]
    lst = extract_bytes_2_lst(entry, blocks, functors)
    return lst[len(lst) - 1]


# Constants for fixed part lengths and name length field offsets/sizes
ENTRY_FIXED_PART_LEN_ASCII = 24
ENTRY_NAME_LEN_FIELD_OFFSET_ASCII = 22
ENTRY_NAME_LEN_FIELD_SIZE_ASCII = 2

ENTRY_FIXED_PART_LEN_UNICODE = 48
ENTRY_NAME_LEN_FIELD_OFFSET_UNICODE = 44
ENTRY_NAME_LEN_FIELD_SIZE_UNICODE = 4


def read_and_parse_entry_def(
    file_handle: BinaryIO, entry_offset: int, is_unicode_entry: bool, block_size: int, file_size: int, # Added file_size for boundary checks
) -> PbEntryDefinition | None:








    """Reads an entry definition from a file handle at a specific offset and parses it.
    This is intended for use when brute-force scanning for ENT* signatures.

    Args:
        file_handle: Open binary file handle.
        entry_offset: The absolute offset in the file where the ENT* signature starts.
        is_unicode_entry: True if the ENT* signature and structure are expected to be Unicode.
        block_size: Effective block size for reading operations.
        file_size: Total size of the PBD file for boundary checks.

    Returns:
        A PbEntryDefinition if successful, otherwise None.
    """
    try:
        fixed_part_len = (
            ENTRY_FIXED_PART_LEN_UNICODE
            if is_unicode_entry
            else ENTRY_FIXED_PART_LEN_ASCII
        )
        name_len_field_offset = (
            ENTRY_NAME_LEN_FIELD_OFFSET_UNICODE
            if is_unicode_entry
            else ENTRY_NAME_LEN_FIELD_OFFSET_ASCII
        )
        name_len_field_size = (
            ENTRY_NAME_LEN_FIELD_SIZE_UNICODE
            if is_unicode_entry
            else ENTRY_NAME_LEN_FIELD_SIZE_ASCII
        )

        # Boundary check before reading fixed part
        if entry_offset + fixed_part_len > file_size:
            logger.debug(
                f"RnP_EntryDef at {entry_offset}: Offset + fixed part length ({fixed_part_len}) exceeds file size ({file_size}).",
            )
            return None

        # Read just the fixed part of the entry definition to get the object name length
        fixed_part_bytes = retrieve_bytes_from_file(
            file_handle, entry_offset, fixed_part_len, block_size_override=block_size, )

        if not fixed_part_bytes or len(fixed_part_bytes) < fixed_part_len:
            logger.debug(
                f"RnP_EntryDef at {entry_offset}: Failed to read fixed part ({fixed_part_len} bytes). Got {len(fixed_part_bytes) if fixed_part_bytes else 0}.",
            )
            return None

        # Verify signature within the fixed part again, just to be sure
        expected_sig_bytes = b"E\0N\0T\0*\0" if is_unicode_entry else b"ENT*"
        actual_sig_len = (
            ENTRY_SIGNATURE_LEN_UNICODE
            if is_unicode_entry
            else ENTRY_SIGNATURE_LEN_ASCII
        )
        if not fixed_part_bytes.startswith(expected_sig_bytes):
            logger.debug(
                f"RnP_EntryDef at {entry_offset}: Expected signature {expected_sig_bytes.decode(errors="ignore")} not found in read fixed part. Got: {fixed_part_bytes[:actual_sig_len].hex()}",
            )
            return None

        # Extract object name length (char count for unicode, byte length for ascii)
        obj_name_len_bytes = fixed_part_bytes[
            name_len_field_offset : name_len_field_offset + name_len_field_size
        ]
        obj_name_len_val = binary_to_int(obj_name_len_bytes)

        if (
            obj_name_len_val < 0 or obj_name_len_val > 2048
        ):  # Safety check for unreasonable length
            logger.warning(
                f"RnP_EntryDef at {entry_offset}: Unrealistic object name length: {obj_name_len_val}. Skipping entry.",
            )
            return None

        object_name_bytes_to_read = (
            obj_name_len_val * 2 if is_unicode_entry else obj_name_len_val
        )
        total_entry_def_length = fixed_part_len + object_name_bytes_to_read

        # Boundary check before reading the full entry definition
        if entry_offset + total_entry_def_length > file_size:
            logger.debug(
                f"RnP_EntryDef at {entry_offset}: Offset + total entry length ({total_entry_def_length}) exceeds file size ({file_size}).",
            )
            return None

        # Now read the complete entry definition bytes
        full_entry_bytes = retrieve_bytes_from_file(
            file_handle, entry_offset, total_entry_def_length, block_size_override=block_size, )

        if not full_entry_bytes or len(full_entry_bytes) < total_entry_def_length:
            logger.debug(
                f"RnP_EntryDef at {entry_offset}: Failed to read full entry def ({total_entry_def_length} bytes). Got {len(full_entry_bytes) if full_entry_bytes else 0}.",
            )
            return None

        # Parse using the existing functions
        if is_unicode_entry:
            return extract_entry_def_unicode(full_entry_bytes)
        return extract_entry_def(full_entry_bytes)

    except Exception as e:  # Main catch-all for this orchestrated function
        logger.exception(
            f"RnP_EntryDef at {entry_offset} (unicode: {is_unicode_entry}): Unexpected exception during processing: {e}",
        )
        # This function orchestrates calls that should handle PbdEntryErrors internally and return None.
        # If an exception reaches here, it's likely an unexpected issue (e.g., IO error from retrieve_bytes_from_file if not handled there, # or a bug in this function's logic).
        return None


# Constants for ENT* signature lengths (used by read_and_parse_entry_def)
ENTRY_SIGNATURE_LEN_ASCII = 4
ENTRY_SIGNATURE_LEN_UNICODE = 8
