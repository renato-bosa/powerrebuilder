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
) -> bytes:
    """Retrieve bytes from a file at a specific offset.

    Args:
        file_handle: File handle, path string, or Path object
        offset: Byte offset to start reading from
        num_bytes: Number of bytes to read (-1 for all)

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


def decode(data: bytes, encoding: str = "utf-8", unicode: bool = False, **kwargs) -> str:
    """Decode bytes to string with PowerBuilder-specific handling.

    Args:
        data: Bytes to decode
        encoding: Character encoding to use
        unicode: If True, use UTF-16 LE encoding
        **kwargs: Additional parameters (for compatibility)

    Returns:
        Decoded string with proper PowerBuilder Unicode handling
    """
    # Override encoding if unicode flag is set
    if unicode:
        encoding = "utf-16-le"
    
    # Handle null byte removal based on encoding
    if encoding == "utf-16-le":
        # For UTF-16LE, only remove null terminators (0x00 0x00), not individual null bytes
        while len(data) >= 2 and data.endswith(b"\x00\x00"):
            data = data[:-2]
    else:
        # For other encodings, remove trailing null bytes normally
        data = data.rstrip(b"\x00")
    
    if not data:
        return ""
    
    # Special handling for PowerBuilder UTF-16LE corruption
    if encoding == "utf-16-le":
        try:
            # First try standard UTF-16LE decoding
            result = data.decode("utf-16-le")
            
            # Check if the result contains suspicious high-unicode characters
            # that indicate byte-order corruption (Chinese characters in ASCII names)
            if _has_suspicious_unicode_corruption(result):
                logger.debug("Detected potential UTF-16LE byte-order corruption, attempting fix")
                
                # Try to fix by swapping byte pairs and decoding as UTF-16BE
                fixed_data = _fix_utf16_byte_order(data)
                if fixed_data:
                    fixed_result = fixed_data.decode("utf-16-le")
                    if _is_more_reasonable_result(fixed_result, result):
                        logger.debug("Successfully fixed UTF-16LE byte-order corruption")
                        return fixed_result
            
            return result
            
        except UnicodeDecodeError as e:
            logger.warning(f"UTF-16LE decoding failed: {e}, trying fallback methods")
            
            # Try byte-order fix as fallback
            try:
                fixed_data = _fix_utf16_byte_order(data)
                if fixed_data:
                    return fixed_data.decode("utf-16-le")
            except Exception:
                pass
            
            # Final fallback with error replacement
            return data.decode("utf-16-le", errors="replace")
    
    # For non-Unicode encodings, use standard decoding
    try:
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


def extract_bytes_2_lst_original(
    b: bytes, blocks: list[int], functors: list[Callable[[bytes], Any]]
) -> list[Any]:
    """Extract a list of values from bytes using block sizes and functors.
    
    This is the original implementation that matches the calling pattern
    in structures.py and header.py.
    
    Args:
        b: Source bytes
        blocks: List of block sizes
        functors: List of functions to convert each block
        
    Returns:
        List of extracted and converted values
    """
    out: list[Any] = []
    idx = 0
    for i, (size, fn) in enumerate(zip(blocks, functors, strict=False)):
        if idx + size > len(b):
            logger.error(
                f"extract_bytes_2_lst: Not enough bytes for block {i} (size {size}). "
                f"Have {len(b) - idx}, current offset {idx}. "
                f"Input bytes (first 64): {b[:64].hex()}"
            )
            # Fill remaining expected outputs with None
            for _ in range(len(blocks) - i):
                out.append(None)
            break
        chunk = b[idx : idx + size]
        try:
            out.append(fn(chunk))
        except Exception as e:
            logger.error(
                f"extract_bytes_2_lst: Functor {fn.__name__ if hasattr(fn, '__name__') else str(fn)} "
                f"failed for block {i} (size {size}, offset {idx}) with error: {e}. "
                f"Chunk (hex): {chunk.hex()}"
            )
            out.append(None)
        idx += size
    return out


def extract_variable_fields(
    data: bytes,
    field_sizes: list[int],
    converters: list[Callable[[bytes], Any]],
    offset: int = 0,
) -> list[Any]:
    """Extract variable-sized fields from bytes.

    Args:
        data: Source bytes
        field_sizes: List of sizes for each field
        converters: List of converter functions for each field
        offset: Starting offset

    Returns:
        List of extracted and converted values
    """
    if len(field_sizes) != len(converters):
        raise ValueError(
            f"Mismatch: {len(field_sizes)} field sizes but {len(converters)} converters"
        )

    result = []
    current_offset = offset

    for i, (size, converter) in enumerate(zip(field_sizes, converters)):
        if current_offset + size > len(data):
            logger.warning(
                f"Truncated extraction at field {i}/{len(field_sizes)}, "
                f"offset {current_offset} + size {size} exceeds data length {len(data)}"
            )
            break

        field_data = data[current_offset : current_offset + size]

        if converter:
            try:
                value = converter(field_data)
            except Exception as e:
                logger.warning(f"Error converting field {i}: {e}")
                value = field_data
        else:
            value = field_data

        result.append(value)
        current_offset += size

    return result


def _has_suspicious_unicode_corruption(text: str) -> bool:
    """Check if text contains patterns indicating UTF-16 byte-order corruption.
    
    Args:
        text: Decoded text to check
        
    Returns:
        True if corruption patterns are detected
    """
    if not text:
        return False
        
    # Check for high-frequency Chinese/Japanese/Korean characters in what should be ASCII names
    # PowerBuilder object names are typically ASCII with underscores, dots, etc.
    cjk_ranges = [
        (0x4E00, 0x9FFF),  # CJK Unified Ideographs
        (0x3400, 0x4DBF),  # CJK Extension A
        (0x2000, 0x206F),  # General Punctuation (includes some corruption patterns)
    ]
    
    cjk_count = 0
    for char in text:
        char_code = ord(char)
        for start, end in cjk_ranges:
            if start <= char_code <= end:
                cjk_count += 1
                break
    
    # If more than 30% are CJK characters, it's likely corruption
    return cjk_count > len(text) * 0.3


def _fix_utf16_byte_order(data: bytes) -> bytes | None:
    """Fix UTF-16 byte order corruption by swapping byte pairs.
    
    Args:
        data: Corrupted UTF-16LE data
        
    Returns:
        Fixed data or None if unfixable
    """
    if len(data) % 2 != 0:
        # Odd number of bytes, can't be valid UTF-16
        return None
    
    if len(data) == 0:
        return data
    
    # Swap each pair of bytes
    fixed = bytearray()
    for i in range(0, len(data), 2):
        if i + 1 < len(data):
            # Swap the byte pair: AB -> BA
            fixed.append(data[i + 1])
            fixed.append(data[i])
        else:
            # Odd byte at end, keep as-is
            fixed.append(data[i])
    
    return bytes(fixed)


def _is_more_reasonable_result(fixed_result: str, original_result: str) -> bool:
    """Check if the fixed result is more reasonable than the original.
    
    Args:
        fixed_result: Result after byte-order fix
        original_result: Original decode result
        
    Returns:
        True if fixed result seems more reasonable
    """
    # Count ASCII characters (more ASCII = more reasonable for PB object names)
    fixed_ascii = sum(1 for c in fixed_result if ord(c) < 128)
    original_ascii = sum(1 for c in original_result if ord(c) < 128)
    
    # Count typical PowerBuilder name characters
    pb_chars = set('abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789_.:()[]')
    fixed_pb = sum(1 for c in fixed_result if c in pb_chars)
    original_pb = sum(1 for c in original_result if c in pb_chars)
    
    # Prefer result with more ASCII and PowerBuilder-style characters
    fixed_score = fixed_ascii * 2 + fixed_pb
    original_score = original_ascii * 2 + original_pb
    
    return fixed_score > original_score


def decode_powerbuilder_name(data: bytes, is_unicode_context: bool = False) -> str:
    """Decode PowerBuilder object names with automatic corruption detection and fixing.
    
    This function specifically handles PowerBuilder object name decoding with built-in
    detection and correction of UTF-16 byte-order corruption.
    
    Args:
        data: Raw bytes of the object name
        is_unicode_context: Whether the file context is Unicode
        
    Returns:
        Properly decoded object name
    """
    if not data:
        return ""
        
    # Auto-detect encoding based on data characteristics
    if is_unicode_context or _looks_like_utf16(data):
        # Unicode context or data looks like UTF-16
        # For UTF-16, only remove null terminators, not null bytes that are part of the encoding
        # A UTF-16LE null terminator is 0x00 0x00
        while len(data) >= 2 and data.endswith(b"\x00\x00"):
            data = data[:-2]
        
        if not data:
            return ""
        
        # UTF-16 must have even number of bytes
        if len(data) % 2 != 0:
            # This shouldn't happen with proper UTF-16, but pad if needed
            logger.warning("Odd number of bytes in UTF-16 data, padding with null")
            data = data + b"\x00"
        
        return decode(data, unicode=True)
    else:
        # ASCII context - remove trailing nulls normally
        data = data.rstrip(b"\x00")
        
        if not data:
            return ""
        
        # Try ASCII/Latin-1 first
        try:
            result = data.decode("latin-1")
            # Check if result is reasonable
            if all(ord(c) < 256 for c in result):
                return result
        except UnicodeDecodeError:
            pass
        
        # Fallback to UTF-16 with correction
        # Ensure even number of bytes for UTF-16
        if len(data) % 2 != 0:
            data = data + b"\x00"
        return decode(data, unicode=True)


def _looks_like_utf16(data: bytes) -> bool:
    """Check if data looks like it might be UTF-16 encoded.
    
    Args:
        data: Bytes to check
        
    Returns:
        True if data appears to be UTF-16
    """
    if len(data) < 2:
        return False
        
    # Check for UTF-16 BOM
    if data.startswith(b'\xff\xfe') or data.startswith(b'\xfe\xff'):
        return True
        
    # Check if even number of bytes (UTF-16 requirement)
    if len(data) % 2 != 0:
        return False
        
    # Look for null bytes in even positions (UTF-16LE pattern for ASCII)
    null_in_even = sum(1 for i in range(1, len(data), 2) if data[i] == 0)
    
    # If more than 50% of odd positions are null, likely UTF-16LE
    if null_in_even > len(data) // 4:
        return True
        
    return False
