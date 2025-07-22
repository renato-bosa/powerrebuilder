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

try:
    import magic
except ImportError:
    magic = None

from src.core.exceptions import PbdError

logger = logging.getLogger(__name__)

# Define constants for file extensions
SOURCE_EXTENSIONS = [".sra", ".srw", ".sru", ".srm", ".srf", ".srd", ".srs"]

RESOURCE_EXTENSIONS = [
    ".bmp",
    ".jpg",
    ".jpeg",
    ".png",
    ".gif",
    ".ico",
    ".cur",
    ".wav",
    ".mp3",
    ".dll",
    ".exe",
    ".ocx",
]


def binary_to_time(data: bytes) -> datetime.datetime:
    """Convert 4-byte little-endian integer timestamp to datetime object.
    Returns epoch (1970-01-01) on error.
    """
    if len(data) != 4:
        logger.warning(
            "binary_to_time: Expected 4 bytes, got %s. Data (hex): %s. Returning epoch.",
            len(data),
            data.hex(),
        )
        return datetime.datetime.fromtimestamp(0)
    try:
        timestamp = struct.unpack("<I", data)[0]
        return datetime.datetime.fromtimestamp(timestamp)
    except (struct.error, OSError, OverflowError) as e:
        logger.warning(
            "binary_to_time: Error converting bytes to datetime: %s. Data (hex): %s. Returning epoch.",
            e,
            data.hex(),
        )
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
        if magic is None:
            raise NameError("magic not imported")
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


def _is_file_handle(obj: Any) -> bool:
    """Check if object is a file handle."""
    return hasattr(obj, "seek") and hasattr(obj, "read")


def _validate_file_handle(handle: BinaryIO, file_id: str) -> None:
    """Validate that a file handle is seekable and readable."""
    if not handle.seekable() or not handle.readable():
        msg = f"Provided file handle for {file_id} is not seekable or readable."
        raise PbdError(msg)


def _read_direct(file_handle: BinaryIO, offset: int, num_bytes: int) -> bytes:
    """Read bytes directly from file."""
    file_handle.seek(offset)
    return file_handle.read(num_bytes)


def _log_partial_read(data: bytes, expected: int, offset: int, file_id: str) -> None:
    """Log warning for partial reads."""
    if len(data) < expected and expected != -1:
        logger.warning(
            f"Tried to read {expected} bytes from offset {offset} in {file_id}, "
            f"but only got {len(data)} bytes (likely EOF reached)."
        )


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
    return all(_validate_single_item(item, name) for item in lst)


def binary_to_int(data: bytes, size: int = 4, signed: bool = False) -> int:
    """Convert bytes to integer.

    Args:
        data: Bytes to convert
        size: Number of bytes (2 or 4)
        signed: Whether to interpret as signed integer

    Returns:
        Integer value
    """
    if len(data) < size:
        raise ValueError(f"Expected {size} bytes, got {len(data)}")

    format_char = "h" if size == 2 else "i" if size == 4 else "q"
    if not signed:
        format_char = format_char.upper()

    return struct.unpack(f"<{format_char}", data[:size])[0]


def binary_to_datetime(data: bytes) -> datetime.datetime:
    """Alias for binary_to_time for consistency."""
    return binary_to_time(data)


def retrieve_bytes_from_file(
    file_handle: BinaryIO | str | Path,
    offset: int,
    num_bytes: int = -1,
    mmap_handle: mmap.mmap | None = None,
) -> bytes:
    """Retrieve bytes from a file at a specific offset.

    Args:
        file_handle: File handle, path string, or Path object
        offset: Byte offset to start reading from
        num_bytes: Number of bytes to read (-1 for all)
        mmap_handle: Optional memory-mapped file handle

    Returns:
        Bytes read from file
    """
    # Handle different input types
    if isinstance(file_handle, (str, Path)):
        with open(file_handle, "rb") as f:
            return _read_direct(f, offset, num_bytes)
    elif _is_file_handle(file_handle):
        return _read_direct(file_handle, offset, num_bytes)
    else:
        raise TypeError(f"Invalid file handle type: {type(file_handle)}")


def safe_filename(name: str, max_length: int = 255) -> str:
    """Create a safe filename from a string.

    Args:
        name: Original filename
        max_length: Maximum length for filename

    Returns:
        Safe filename string
    """
    # Remove or replace unsafe characters
    safe_chars = re.sub(r'[<>:"/\\|?*\x00-\x1f]', "_", name)

    # Normalize unicode
    safe_chars = unicodedata.normalize("NFKD", safe_chars)

    # Truncate if too long
    if len(safe_chars) > max_length:
        base, ext = os.path.splitext(safe_chars)
        max_base = max_length - len(ext)
        safe_chars = base[:max_base] + ext

    return safe_chars.strip(". ")


def calculate_content_hash(data: bytes) -> str:
    """Calculate SHA-256 hash of data.

    Args:
        data: Bytes to hash

    Returns:
        Hex string of hash
    """
    return hashlib.sha256(data).hexdigest()


def decode(data: bytes, encoding: str = "utf-8") -> str:
    """Decode bytes to string with error handling.

    Args:
        data: Bytes to decode
        encoding: Character encoding to use

    Returns:
        Decoded string
    """
    try:
        # Remove null bytes before decoding
        data = data.rstrip(b"\x00")
        return data.decode(encoding)
    except UnicodeDecodeError:
        # Try with error handling
        return data.decode(encoding, errors="replace")


def extract_bytes_2_lst(
    data: bytes,
    offset: int,
    count: int,
    size: int,
    converter: Callable[[bytes], Any] | None = None,
) -> list[Any]:
    """Extract a list of values from bytes.

    Args:
        data: Source bytes
        offset: Starting offset
        count: Number of items to extract
        size: Size of each item in bytes
        converter: Optional function to convert each item

    Returns:
        List of extracted values
    """
    result = []
    for i in range(count):
        item_offset = offset + (i * size)
        if item_offset + size > len(data):
            logger.warning(
                f"Truncated extraction at item {i}/{count}, "
                f"offset {item_offset} exceeds data length {len(data)}"
            )
            break

        item_data = data[item_offset : item_offset + size]

        if converter:
            try:
                value = converter(item_data)
            except Exception as e:
                logger.warning(f"Error converting item {i}: {e}")
                value = item_data
        else:
            value = item_data

        result.append(value)

    return result
