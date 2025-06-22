import datetime
import hashlib
import logging
import mimetypes
import mmap
import os
import re
import struct
import unicodedata
from collections.abc import Callable
from pathlib import Path
from typing import Any, BinaryIO

import magic

from extract.pbd.constants import (
    BLOCK_SIZE, DEFAULT_ENCODING, RESOURCE_EXTENSIONS, SOURCE_EXTENSIONS, UNICODE_ENCODING, )
from extract.pbd.exceptions import PbdError  # Correct import for PbdError

logger = logging.getLogger(__name__)

# Additional constants specific to this module
NODE_BLOCK_SIZE = BLOCK_SIZE * 8  # 4096 bytes

# Utility Functions


def safe_filename(name: str, max_length: int = 255) -> str:








    """Sanitize a filename to be safe for the filesystem.

    - Strips control chars & reserved path chars
    - Normalizes Unicode to NFC
    - Collapses repeated underscores
    - Ensures non-empty result
    - Truncates to max_length (default 255 for most filesystems)
    """
    # Strip control chars & reserved path chars
    name = re.sub(r'[<>:"/\\|?*\x00-\x1F]', "_", name)
    # Normalize Unicode → NFC to avoid duplicate forms
    name = unicodedata.normalize("NFC", name)
    # Collapse repeated underscores
    name = re.sub(r"_{2, }", "_", name)
    # Strip leading/trailing spaces and dots
    name = name.strip(" .")
    # Return underscore if empty
    name = name or "_"

    # Handle length limit
    if len(name) > max_length:
        # Try to preserve extension
        last_dot = name.rfind('.')
        if last_dot > 0 and last_dot > max_length - 20:  # Extension found and near end
            extension = name[last_dot:]
            # Reserve space for extension and "_TRUNCATED" suffix
            truncate_at = max_length - len(extension) - 10  # 10 for "_TRUNCATED"
            if truncate_at > 0:
                name = name[:truncate_at] + "_TRUNCATED" + extension
            else:
                # Extension too long or no room, just truncate
                name = name[:max_length - 10] + "_TRUNCATED"
        else:
            # No extension or extension too far back
            name = name[:max_length - 10] + "_TRUNCATED"

    return name


def calculate_content_hash(content: str | bytes) -> str:








    """Calculates the SHA-1 hash of the given content.
    If content is a string, it's encoded to UTF-8 before hashing.
    """
    sha1 = hashlib.sha1()
    if isinstance(content, str):
        sha1.update(content.encode("utf-8"))
    elif isinstance(content, bytes):
        sha1.update(content)
    else:
        msg = f"Content must be string or bytes, not {type(content)}"
        raise TypeError(msg)

    return sha1.hexdigest()


def decode(data: bytes, unicode: bool = False, is_terminated: bool = True) -> str:





    r"""Decode bytes to string, handling unicode and null termination.
    Tries 'utf-16-le' if unicode is True, otherwise 'latin1' (similar to ASCII for PBDs).
    Strips trailing null characters (\x00) if is_terminated is True.
    Uses 'replace' for errors to avoid crashing on unmappable bytes.
    """
    encoding = UNICODE_ENCODING if unicode else DEFAULT_ENCODING
    try:
        decoded_str = data.decode(encoding, errors="replace")
        if is_terminated:
            return decoded_str.rstrip("\x00")
        return decoded_str
    except Exception as e:
        logger.warning(
            f"Failed to decode bytes (unicode={unicode}, terminated={is_terminated}, encoding={encoding}) with data: {data[:32].hex()}... Error: {e}"
        )
        return "DECODE_ERROR"


def binary_to_int(data: bytes, signed: bool = False) -> int:








    """Convert bytes to integer (little-endian). Supports 2, 4, or 8 byte inputs for unsigned.
    For signed, it typically expects 4 bytes for now based on PBD usage.
    """
    length = len(data)
    if not data:  # Handle empty byte string
        # logger.warning("binary_to_int received empty byte string. Returning 0.")
        return 0
    try:
        if signed:
            if length == 4:
                return struct.unpack("<i", data)[0]
            # Add other signed lengths if needed
            logger.warning(
                f"binary_to_int: Unsupported byte length {length} for signed conversion. Returning 0."
            )
            return 0
        # Unsigned
        if length == 8:
            return struct.unpack("<Q", data)[0]
        if length == 4:
            return struct.unpack("<I", data)[0]
        if length == 2:
            return struct.unpack("<H", data)[0]
        if length == 1:
            return struct.unpack("<B", data)[0]
        # logger.warning("binary_to_int: Unsupported byte length %s for unsigned. Returning 0.", length)
        return int.from_bytes(
            data, byteorder="little", signed=False
        )  # Fallback for other lengths
    except struct.error:
        # logger.warning("binary_to_int: struct.error for data %s (len %s): %s. Returning 0.", data.hex(), len(data), e)
        return 0  # Or raise a custom error


def binary_to_time(data: bytes) -> datetime.datetime:








    """Convert 4-byte little-endian integer timestamp to datetime object.
    Returns epoch (1970-01-01) on error.
    """
    if len(data) != 4:
        # logger.warning("binary_to_time: Expected 4 bytes, got %s. Data (hex): %s. Returning epoch.", len(data), data.hex())
        return datetime.datetime.fromtimestamp(0)
    try:
        timestamp = struct.unpack("<I", data)[0]
        return datetime.datetime.fromtimestamp(timestamp)
    except (struct.error, OSError, OverflowError):
        # logger.warning("binary_to_time: Error converting bytes to datetime: %s. Data (hex): %s. Returning epoch.", e, data.hex())
        return datetime.datetime.fromtimestamp(0)


def is_source_file(name: str) -> bool:



    return any(name.lower().endswith(ext) for ext in SOURCE_EXTENSIONS)


def is_resource_file(name: str) -> bool:



    return any(name.lower().endswith(ext) for ext in RESOURCE_EXTENSIONS)


def get_mime_type(filename: str) -> str: 




    mime_type, _ = mimetypes.guess_type(filename)
    return mime_type if mime_type else "application/octet-stream"


def get_mime_type_from_data(data: bytes) -> str:





    try:
        # Ensure magic is imported and available
        mime = magic.Magic(mime=True)
        return mime.from_buffer(data)
    except NameError:  # magic not imported
        logger.warning(
            "python-magic library not available. MIME type detection from data is limited."
        )
        return "application/octet-stream"
    except Exception as e:  # other magic errors
        logger.warning(
            f"python-magic failed to determine mime type: {e}. Using 'application/octet-stream'."
        )
        return "application/octet-stream"


def read_bytes_from_handle(
    file_handle: "BinaryIO", offset: int, length: int
) -> bytes | None:








    """Reads a specific number of bytes from a given offset in an already open binary file handle."""
    try:
        file_handle.seek(offset)
        data = file_handle.read(length)
        if (
            length > 0 and len(data) < length
        ):  # length > 0 check for when reading until EOF with -1
            logger.warning(
                f"read_bytes_from_handle: Requested {length} bytes from offset {offset}, but got only {len(data)} bytes (EOF likely)."
            )
        return data
    except Exception as e:
        logger.exception(
            f"read_bytes_from_handle: Failed to read bytes from handle at offset {offset} for length {length}: {e}"
        )
        return None


def _is_file_handle(obj: Any) -> bool:








    """Check if object is a file handle."""
    return hasattr(obj, "seek") and hasattr(obj, "read")


def _get_file_identifier(file_path_or_handle: str | Path | BinaryIO) -> str:








    """Get a string identifier for logging."""
    if _is_file_handle(file_path_or_handle):
        return f"<handle at {hex(id(file_path_or_handle))}>"
    return str(file_path_or_handle)


def _validate_file_handle(handle: BinaryIO, file_id: str) -> None:








    """Validate that a file handle is seekable and readable."""
    if not handle.seekable() or not handle.readable():
        msg = f"Provided file handle for {file_id} is not seekable or readable."
        raise PbdError(msg)


def _adjust_read_size_for_eof(
    offset: int, num_bytes: int, file_size: int, file_id: str
) -> int:








    """Adjust read size if it would go beyond EOF.

    Returns:
        Adjusted number of bytes to read
    """
    if num_bytes == -1 or offset + num_bytes > file_size:
        if offset >= file_size:
            logger.warning(
                f"Offset {offset} is beyond file size {file_size} in {file_id}"
            )
            return 0

        effective_num_bytes = file_size - offset
        logger.debug(
            f"Adjusting read request from {num_bytes} to {effective_num_bytes} bytes (EOF at {file_size})"
        )
        return effective_num_bytes

    return num_bytes


def _read_with_mmap(
    file_handle: BinaryIO, offset: int, num_bytes: int, file_size: int
) -> bytes:








    """Read bytes using memory mapping.

    Returns:
        Bytes read from file
    """
    mm = None
    try:
        mm = mmap.mmap(file_handle.fileno(), 0, access=mmap.ACCESS_READ)
        return mm[offset : offset + num_bytes]
    finally:
        if mm is not None:
            try:
                mm.close()
            except Exception as e:
                logger.exception("Error closing mmap: %s", e)


def _read_direct(file_handle: BinaryIO, offset: int, num_bytes: int) -> bytes:








    """Read bytes directly from file."""
    file_handle.seek(offset)
    return file_handle.read(num_bytes)


def _read_from_file_path(
    file_path: str | Path, offset: int, num_bytes: int
) -> tuple[bytes, BinaryIO, bool]:








    """Read from a file path, using mmap for large reads.

    Returns:
        Tuple of (data, file_handle, should_close)
    """
    f = open(Path(file_path), "rb")
    file_id = str(Path(file_path))

    try:
        # Get file size for boundary checks
        file_size = os.fstat(f.fileno()).st_size

        # Adjust read size for EOF
        adjusted_bytes = _adjust_read_size_for_eof(offset, num_bytes, file_size, file_id)
        if adjusted_bytes == 0:
            return b"", f, True

        # Decide whether to use mmap
        use_mmap = file_size > 1024 * 1024 or adjusted_bytes > 8192  # 1MB+ file or reading 8KB+

        if use_mmap:
            try:
                data = _read_with_mmap(f, offset, adjusted_bytes, file_size)
            except (ValueError, OSError) as e:
                logger.warning(
                    f"Failed to use mmap for {file_id}, falling back to standard read: {e}"
                )
                data = _read_direct(f, offset, adjusted_bytes)
        else:
            data = _read_direct(f, offset, adjusted_bytes)

        return data, f, True

    except Exception:
        f.close()
        raise


def _read_from_handle(
    handle: BinaryIO, offset: int, num_bytes: int, file_id: str
) -> tuple[bytes, int | None]:








    """Read from an existing file handle.

    Returns:
        Tuple of (data, original_position)
    """
    _validate_file_handle(handle, file_id)
    original_pos = handle.tell()

    # For file handles, use direct read (mmap is complex with arbitrary handles)
    data = _read_direct(handle, offset, num_bytes)

    return data, original_pos


def _cleanup_file_resources(
    file_handle: BinaryIO | None, should_close: bool, original_pos: int | None, is_handle: bool, file_id: str
) -> None:








    """Clean up file resources after reading."""
    if not file_handle:
        return

    # Restore original position for handles
    if is_handle and original_pos is not None and file_handle.seekable():
        try:
            file_handle.seek(original_pos)
        except Exception as e:
            logger.exception(
                f"Could not restore original position of handle for {file_id}: {e}"
            )

    # Close file if we opened it
    if should_close and hasattr(file_handle, "closed") and not file_handle.closed:
        try:
            file_handle.close()
        except Exception as e:
            logger.exception("Error closing file %s: %s", file_id, e)


def _log_partial_read(data: bytes, expected: int, offset: int, file_id: str) -> None:








    """Log warning for partial reads."""
    if len(data) < expected and expected != -1:
        logger.warning(
            f"Tried to read {expected} bytes from offset {offset} in {file_id}, "
            f"but only got {len(data)} bytes (likely EOF reached)."
        )


def retrieve_bytes_from_file(
    file_path_or_handle: str | Path | BinaryIO, offset: int, num_bytes: int, block_size_override: int | None = None, ) -> bytes:








    """Reads N bytes from a specific offset in a PBD file.

    Args:
        file_path_or_handle: Path to the PBD file or an open BinaryIO handle.
        offset: The offset from where to start reading.
        num_bytes: The number of bytes to read.
        block_size_override: Currently not used in implementation but kept for API compatibility.
                           May be used in future for block-aligned reads.

    Returns:
        The bytes read from the file.

    Raises:
        PbdError: If the file cannot be read or not enough bytes are found.
    """
    # Note: block_size_override is not currently used but is part of the API
    _ = block_size_override  # Acknowledge the parameter to avoid linter warnings

    is_handle = _is_file_handle(file_path_or_handle)
    file_id = _get_file_identifier(file_path_or_handle)

    file_handle = None
    should_close = False
    original_pos = None

    try:
        if is_handle:
            data, original_pos = _read_from_handle(
                file_path_or_handle, # type: ignore
                offset, num_bytes, file_id
            )
            file_handle = file_path_or_handle  # type: ignore
        else:
            data, file_handle, should_close = _read_from_file_path(
                file_path_or_handle, # type: ignore
                offset, num_bytes
            )

        _log_partial_read(data, num_bytes, offset, file_id)
        return data

    except FileNotFoundError:
        msg = f"File not found: {file_id}"
        raise PbdError(msg) from None
    except PbdError:
        raise
    except Exception as e:
        msg = f"Error reading {num_bytes} from offset {offset} in file {file_id}: {e}"
        raise PbdError(msg) from e
     finally:
        _cleanup_file_resources(file_handle, should_close, original_pos, is_handle, file_id)


def extract_bytes_2_lst(
    b: bytes, blocks: list[int], functors: list[Callable[[bytes], Any]]
) -> list[Any]:








    """Extract a list of values from bytes using block sizes and functors.
    Logs errors with context if any functor fails.
    """
    out: list[Any] = []
    idx = 0
    for i, (size, fn) in enumerate(zip(blocks, functors, strict=False)):
        if idx + size > len(b):
            logger.error(
                f"extract_bytes_2_lst: Not enough bytes for block {i} (size {size}). Have {len(b) - idx}, current offset {idx}. Input bytes (first 64): {b[:64].hex()}"
            )
            # Fill remaining expected outputs with None or a specific error marker
            for _ in range(len(blocks) - i):
                out.append(None)  # Or an error marker object
            break  # Stop processing further blocks
        chunk = b[idx : idx + size]
        try:
            out.append(fn(chunk))
        except Exception as e:
            logger.exception(
                f"extract_bytes_2_lst: Functor {fn.__name__ if hasattr(fn, '__name__') else str(fn)} failed for block {i} (size {size}, offset {idx}) with error: {e}. Chunk (hex): {chunk.hex()}"
            )
            out.append(None)  # Or an error marker object
        idx += size
    return out


def _validate_single_item(item: Any, name: str) -> bool:








    """Validate that a single item starts with the specified name.

    Returns:
        True if valid, False otherwise
    """
    if item is None:
        return False

    # Check if it's a string
    if isinstance(item, str):
        return item.startswith(name)

    # Check if it's a sequence with a string as first element
    try:
        if hasattr(item, "__getitem__") and len(item) > 0:
            if isinstance(item[0], str):
                return item[0].startswith(name)
    except (IndexError, TypeError, AttributeError):
        pass

    return False


def validate(lst: list[Any], name: str) -> bool:








    """Validate that all items in the list start with the specified name."""
    if not lst:
        return False

    # Validate all items
    for item in lst:
        if not _validate_single_item(item, name):
            return False

    return True