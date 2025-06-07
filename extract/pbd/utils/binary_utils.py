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

from ..exceptions import PbdError  # Correct import for PbdError
from ..constants import (
    BLOCK_SIZE, DEFAULT_ENCODING, MAX_MMAP_SIZE, 
    RESOURCE_EXTENSIONS, SOURCE_EXTENSIONS, UNICODE_ENCODING
)

logger = logging.getLogger(__name__)

# Additional constants specific to this module
NODE_BLOCK_SIZE = BLOCK_SIZE * 8  # 4096 bytes

# Utility Functions


def safe_filename(name: str) -> str:
    """Sanitize a filename to be safe for the filesystem.

    - Strips control chars & reserved path chars
    - Normalizes Unicode to NFC
    - Collapses repeated underscores
    - Ensures non-empty result
    """
    # Strip control chars & reserved path chars
    name = re.sub(r'[<>:"/\\|?*\x00-\x1F]', '_', name)
    # Normalize Unicode → NFC to avoid duplicate forms
    name = unicodedata.normalize('NFC', name)
    # Collapse repeated underscores
    name = re.sub(r'_{2,}', '_', name)
    # Strip leading/trailing spaces and dots
    name = name.strip(' .')
    # Return underscore if empty
    return name or '_'


def calculate_content_hash(content: str | bytes) -> str:
    """Calculates the SHA-1 hash of the given content.
    If content is a string, it's encoded to UTF-8 before hashing.
    """
    sha1 = hashlib.sha1()
    if isinstance(content, str):
        sha1.update(content.encode('utf-8'))
    elif isinstance(content, bytes):
        sha1.update(content)
    else:
        raise TypeError(f"Content must be string or bytes, not {type(content)}")
    
    return sha1.hexdigest()


def decode(data: bytes, unicode: bool = False, is_terminated: bool = True) -> str:
    r"""Decode bytes to string, handling unicode and null termination.
    Tries 'utf-16-le' if unicode is True, otherwise 'latin1' (similar to ASCII for PBDs).
    Strips trailing null characters (\x00) if is_terminated is True.
    Uses 'replace' for errors to avoid crashing on unmappable bytes.
    """
    encoding = UNICODE_ENCODING if unicode else DEFAULT_ENCODING
    try:
        decoded_str = data.decode(encoding, errors='replace')
        if is_terminated:
            return decoded_str.rstrip('\x00')
        return decoded_str
    except Exception as e:
        logger.warning(f"Failed to decode bytes (unicode={unicode}, terminated={is_terminated}, encoding={encoding}) with data: {data[:32].hex()}... Error: {e}")
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
            logger.warning(f"binary_to_int: Unsupported byte length {length} for signed conversion. Returning 0.")
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
        # logger.warning(f"binary_to_int: Unsupported byte length {length} for unsigned. Returning 0.")
        return int.from_bytes(data, byteorder='little', signed=False)  # Fallback for other lengths
    except struct.error:
        # logger.warning(f"binary_to_int: struct.error for data {data.hex()} (len {len(data)}): {e}. Returning 0.")
        return 0  # Or raise a custom error


def binary_to_time(data: bytes) -> datetime.datetime:
    """Convert 4-byte little-endian integer timestamp to datetime object.
    Returns epoch (1970-01-01) on error.
    """
    if len(data) != 4:
        # logger.warning(f"binary_to_time: Expected 4 bytes, got {len(data)}. Data (hex): {data.hex()}. Returning epoch.")
        return datetime.datetime.fromtimestamp(0)
    try:
        timestamp = struct.unpack("<I", data)[0]
        return datetime.datetime.fromtimestamp(timestamp)
    except (struct.error, OSError, OverflowError):
        # logger.warning(f"binary_to_time: Error converting bytes to datetime: {e}. Data (hex): {data.hex()}. Returning epoch.")
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
        logger.warning("python-magic library not available. MIME type detection from data is limited.")
        return 'application/octet-stream'
    except Exception as e:  # other magic errors
        logger.warning(f"python-magic failed to determine mime type: {e}. Using 'application/octet-stream'.")
        return 'application/octet-stream'


def read_bytes_from_handle(file_handle: 'BinaryIO', offset: int, length: int) -> bytes | None:
    """Reads a specific number of bytes from a given offset in an already open binary file handle."""
    try:
        file_handle.seek(offset)
        data = file_handle.read(length)
        if length > 0 and len(data) < length:  # length > 0 check for when reading until EOF with -1
            logger.warning(f"read_bytes_from_handle: Requested {length} bytes from offset {offset}, but got only {len(data)} bytes (EOF likely).")
        return data
    except Exception as e:
        logger.error(f"read_bytes_from_handle: Failed to read bytes from handle at offset {offset} for length {length}: {e}")
        return None


def retrieve_bytes_from_file(
    file_path_or_handle: str | Path | BinaryIO,
    offset: int,
    num_bytes: int,
    block_size_override: int | None = None,
) -> bytes:
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
    data = b""

    input_is_handle = hasattr(file_path_or_handle, 'seek') and hasattr(file_path_or_handle, 'read')
    file_to_log = str(file_path_or_handle) if not input_is_handle else f"<handle at {hex(id(file_path_or_handle))}>"
    original_handle_pos: int | None = None
    should_close_handle = False
    mm = None  # mmap object

    try:
        f: BinaryIO
        if input_is_handle:
            f = file_path_or_handle  # type: ignore
            if not f.seekable() or not f.readable():
                raise PbdError(f"Provided file handle for {file_to_log} is not seekable or readable.")
            original_handle_pos = f.tell()

            # For file handles, use seek/read as before
            # Using mmap with an arbitrary file handle is complex due to:
            # 1. Not all file-like objects have fileno()
            # 2. The handle might be for a non-regular file (pipe, socket)
            # 3. The handle might have been opened in a mode incompatible with mmap
            f.seek(offset)
            data = f.read(num_bytes)
        else:
            # For file paths, use memory mapping for better performance
            f = open(Path(file_path_or_handle), "rb")
            should_close_handle = True
            file_to_log = str(Path(file_path_or_handle))

            try:
                # Get file size for boundary checks
                file_size = os.fstat(f.fileno()).st_size

                # Special case: reading entire file or beyond EOF
                if num_bytes == -1 or offset + num_bytes > file_size:
                    if offset >= file_size:
                        logger.warning(f"Offset {offset} is beyond file size {file_size} in {file_to_log}")
                        return b""

                    effective_num_bytes = file_size - offset
                    logger.debug(f"Adjusting read request from {num_bytes} to {effective_num_bytes} bytes (EOF at {file_size})")
                    num_bytes = effective_num_bytes

                # Only use mmap if reading a substantial amount or file is large enough to benefit
                # Small files or small reads might be faster with direct read
                if file_size > 1024 * 1024 or num_bytes > 8192:  # 1MB+ file or reading 8KB+
                    # Memory map the file for efficient random access
                    mm = mmap.mmap(f.fileno(), 0, access=mmap.ACCESS_READ)
                    data = mm[offset:offset + num_bytes]
                else:
                    # For small files/reads, direct reading is fine
                    f.seek(offset)
                    data = f.read(num_bytes)
            except (ValueError, OSError) as e:
                # Fall back to normal file reading if mmap fails
                logger.warning(f"Failed to use mmap for {file_to_log}, falling back to standard read: {e}")
                f.seek(offset)
                data = f.read(num_bytes)

        if len(data) < num_bytes and num_bytes != -1:
            # This can happen if num_bytes extends beyond EOF.
            # For PBD structures, we often expect full blocks or specific sizes.
            # Log a warning, but return what was read. Higher-level functions will decide if it's an error.
            logger.warning(
                f"Tried to read {num_bytes} bytes from offset {offset} in {file_to_log}, "
                f"but only got {len(data)} bytes (likely EOF reached).",
            )
            # Optional: Pad with zeros if a full block was expected by the caller but EOF was hit?
            # For now, just return the partial data. Callers must be robust.

    except FileNotFoundError:
        raise PbdError(f"File not found: {file_to_log}") from None
    except Exception as e:
        raise PbdError(f"Error reading {num_bytes} from offset {offset} in file {file_to_log}: {e}") from e
    finally:
        # Clean up resources
        if mm is not None:
            try:
                mm.close()
            except Exception as e_mm:
                logger.error(f"Error closing mmap for {file_to_log}: {e_mm}")

        if input_is_handle and original_handle_pos is not None and f.seekable():
            try:
                f.seek(original_handle_pos)
            except Exception as e_seek_restore:
                logger.error(f"Could not restore original position of handle for {file_to_log} in retrieve_bytes: {e_seek_restore}")
        elif should_close_handle and 'f' in locals() and hasattr(f, 'closed') and not f.closed:
            try:
                f.close()
            except Exception as e_close:
                logger.error(f"Error closing file {file_to_log}: {e_close}")

    return data




def extract_bytes_2_lst(b: bytes, blocks: list[int], functors: list[Callable[[bytes], Any]]) -> list[Any]:
    """Extract a list of values from bytes using block sizes and functors.
    Logs errors with context if any functor fails.
    """
    out: list[Any] = []
    idx = 0
    for i, (size, fn) in enumerate(zip(blocks, functors, strict=False)):
        if idx + size > len(b):
            logger.error(f"extract_bytes_2_lst: Not enough bytes for block {i} (size {size}). Have {len(b) - idx}, current offset {idx}. Input bytes (first 64): {b[:64].hex()}")
            # Fill remaining expected outputs with None or a specific error marker
            for _ in range(len(blocks) - i):
                out.append(None)  # Or an error marker object
            break  # Stop processing further blocks
        chunk = b[idx:idx + size]
        try:
            out.append(fn(chunk))
        except Exception as e:
            logger.error(f"extract_bytes_2_lst: Functor {fn.__name__ if hasattr(fn, '__name__') else str(fn)} failed for block {i} (size {size}, offset {idx}) with error: {e}. Chunk (hex): {chunk.hex()}")
            out.append(None)  # Or an error marker object
        idx += size
    return out


def validate(lst: list[Any], name: str) -> bool:
    """Validate that all items in the list start with the specified name."""
    if not lst:
        return False
    first = lst[0]
    if first is None:
        return False
    if isinstance(first, str):
        return first.startswith(name)
    try:
        if hasattr(first, '__getitem__'):
            if len(first) > 0 and isinstance(first[0], str):
                return first[0].startswith(name)
    except (IndexError, TypeError, AttributeError):
        pass
    for item in lst:
        try:
            if item is None:
                return False
            if isinstance(item, str):
                if not item.startswith(name):
                    return False
            elif hasattr(item, '__getitem__') and len(item) > 0:
                if isinstance(item[0], str) and not item[0].startswith(name):
                    return False
        except (IndexError, TypeError, AttributeError):
            return False
    return True
