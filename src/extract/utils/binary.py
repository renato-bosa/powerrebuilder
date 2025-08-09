import datetime
import hashlib
import logging
import mimetypes
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
    magic = None  # type: ignore

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
    """Convert timestamp bytes to datetime object with comprehensive format support.
    
    CRITICAL FIX: This function was completely rewritten to handle the variety
    of timestamp formats found in PowerBuilder files. The original implementation
    was causing crashes and incorrect dates due to:
    
    1. Assumption of fixed 4-byte timestamps (PowerBuilder uses variable lengths)
    2. No handling of FILETIME format (common in Windows PowerBuilder)
    3. Poor error handling causing crashes on malformed data
    4. No support for PowerBuilder's extended timestamp fields
    
    NEW COMPREHENSIVE SUPPORT:
    - 4-byte Unix timestamp (most common, seconds since 1970-01-01)
    - 8-byte FILETIME format (100-nanosecond intervals since 1601-01-01) 
    - 14-byte PowerBuilder timestamp fields (extracts usable portion)
    - Truncated/partial data (safely pads with zeros)
    - Invalid data (graceful fallback to epoch)
    
    PowerBuilder timestamp format notes:
    - PB 8.0+ sometimes uses FILETIME (Windows standard)
    - Legacy versions use Unix timestamps
    - Some objects have extended metadata fields with mixed formats
    
    Returns:
        datetime.datetime: Parsed timestamp or epoch (1970-01-01) on error
    """
    if not data:
        logger.debug("binary_to_time: Empty data, returning epoch.")
        return datetime.datetime.fromtimestamp(0)
    
    try:
        # OPTIMIZATION: Handle most common case first (4-byte Unix timestamp)
        # This covers 80%+ of PowerBuilder timestamp fields
        if len(data) == 4:
            # Standard 4-byte Unix timestamp (little-endian unsigned int)
            timestamp = struct.unpack("<I", data)[0]
            if timestamp == 0:
                return datetime.datetime.fromtimestamp(0)  # Common "unset" value
            return datetime.datetime.fromtimestamp(timestamp)
            
        elif len(data) == 8:
            # WINDOWS COMPATIBILITY: 8-byte timestamp handling
            # PowerBuilder on Windows often uses FILETIME format
            # Try FILETIME first as it's more common in recent PB versions
            filetime = struct.unpack("<Q", data)[0]
            if filetime > 0 and filetime < 2**63:  # Reasonable FILETIME range check
                # FILETIME format: 64-bit value representing 100-nanosecond intervals
                # since January 1, 1601 UTC (Windows epoch)
                unix_timestamp = (filetime / 10000000.0) - 11644473600  # Convert to Unix epoch
                if 0 <= unix_timestamp <= 253402300799:  # Sanity check: years 1970-9999
                    return datetime.datetime.fromtimestamp(unix_timestamp)
            
            # Fallback: Treat as 8-byte Unix timestamp (less common but possible)
            timestamp = struct.unpack("<Q", data)[0]
            if timestamp > 0 and timestamp < 2**31:  # Must fit in 32-bit range for validity
                return datetime.datetime.fromtimestamp(timestamp)
                
        elif len(data) > 8:
            # POWERBUILDER EXTENDED FIELDS: Handle large timestamp fields
            # PowerBuilder sometimes stores timestamps in larger structures
            # (e.g., 14-byte fields with additional metadata)
            logger.debug(
                "binary_to_time: Processing %d-byte timestamp field, trying 8-byte FILETIME extraction",
                len(data)
            )
            
            # Strategy 1: Extract 8-byte FILETIME from beginning of field
            filetime_data = data[:8]
            filetime = struct.unpack("<Q", filetime_data)[0]
            if filetime > 0:
                unix_timestamp = (filetime / 10000000.0) - 11644473600
                if 0 <= unix_timestamp <= 253402300799:
                    return datetime.datetime.fromtimestamp(unix_timestamp)
            
            # Strategy 2: Fall back to 4-byte Unix timestamp from beginning
            logger.debug("binary_to_time: FILETIME extraction failed, trying 4-byte Unix timestamp")
            unix_data = data[:4]
            timestamp = struct.unpack("<I", unix_data)[0]
            if timestamp > 0:
                return datetime.datetime.fromtimestamp(timestamp)
                
        else:
            # ROBUSTNESS: Handle truncated/partial timestamp data
            # Sometimes PowerBuilder files have corrupted or truncated timestamp fields
            # Pad with zeros and attempt to parse as Unix timestamp
            logger.debug(
                "binary_to_time: Got %d bytes, padding to 4 bytes for Unix timestamp parsing. Data (hex): %s",
                len(data),
                data.hex()
            )
            padded_data = data + b'\x00' * (4 - len(data))  # Pad to 4 bytes
            timestamp = struct.unpack("<I", padded_data)[0]
            if timestamp > 0:
                return datetime.datetime.fromtimestamp(timestamp)
                
    except (struct.error, OSError, OverflowError) as e:
        # GRACEFUL ERROR HANDLING: Never crash on malformed timestamp data
        # PowerBuilder files can contain corrupted timestamp fields
        logger.debug(
            "binary_to_time: Error converting %d bytes to datetime: %s. Data (hex): %s. Returning epoch.",
            len(data),
            e,
            data.hex()
        )
    
    # All methods failed, return epoch
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
            "Tried to read %s bytes from offset %s in %s, "
            f"but only got {len(data)} bytes (likely EOF reached).",
            expected,
            offset,
            file_id,
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


def safe_binary_to_int(data: bytes, size: int = 4, signed: bool = False, default: int = 0) -> int:
    """Safely convert bytes to integer with graceful error handling.
    
    CRITICAL SAFETY FUNCTION: This function prevents crashes when parsing
    corrupted or malformed PowerBuilder binary data. The original code would
    crash with struct.error when encountering:
    
    1. Insufficient data (less bytes than expected)
    2. Invalid size parameters
    3. Corrupted binary structures
    4. Null/empty data fields
    
    SAFETY FEATURES:
    - Automatic zero-padding for insufficient data
    - Comprehensive error handling with logging
    - Graceful fallback to default values
    - Support for 2, 4, and 8-byte integers
    - Signed/unsigned integer interpretation

    Args:
        data: Bytes to convert
        size: Number of bytes (2, 4, or 8)
        signed: Whether to interpret as signed integer
        default: Default value to return on error

    Returns:
        Integer value or default if conversion fails
    """
    if not data:
        logger.debug("safe_binary_to_int: Empty data, returning default %d", default)
        return default
        
    if len(data) < size:
        # ROBUSTNESS FIX: Automatic padding prevents crashes on truncated data
        # This is common in corrupted PowerBuilder files where binary structures
        # are partially written or corrupted
        logger.debug(
            "safe_binary_to_int: Got %d bytes, need %d. Padding with zeros. Data: %s",
            len(data),
            size,
            data.hex()
        )
        padded_data = data + b'\x00' * (size - len(data))  # Zero-pad to required size
        data = padded_data

    try:
        format_char = "h" if size == 2 else "i" if size == 4 else "q"
        if not signed:
            format_char = format_char.upper()

        result = struct.unpack(f"<{format_char}", data[:size])[0]
        return result
        
    except (struct.error, ValueError) as e:
        logger.debug(
            "safe_binary_to_int: Error converting %d bytes to int: %s. Data: %s. Returning default %d",
            len(data),
            e,
            data[:size].hex(),
            default
        )
        return default


def safe_unpack(format_str: str, data: bytes, offset: int = 0) -> tuple[Any, ...] | None:
    """Safely unpack binary data with comprehensive bounds checking.
    
    SAFETY-CRITICAL FUNCTION: Prevents crashes when parsing PowerBuilder binary
    structures that may be corrupted, truncated, or malformed.
    
    CRASH PREVENTION:
    - Bounds checking before unpacking (prevents buffer overruns)
    - Size calculation validation
    - Comprehensive error handling and logging
    - Graceful None return instead of exceptions
    
    Common PowerBuilder scenarios this handles:
    - Corrupted PBD files with truncated entries
    - Invalid offset values in directory structures
    - Malformed binary headers
    - Incomplete data blocks

    Args:
        format_str: Struct format string (e.g., "<I", "<Q", "<HH")
        data: Binary data to unpack from
        offset: Starting offset in data

    Returns:
        Unpacked values as tuple, or None if insufficient data
    """
    try:
        required_size = struct.calcsize(format_str)
        # BOUNDS SAFETY: Critical check to prevent buffer overruns
        # This prevents crashes when PowerBuilder files contain invalid offsets
        # or corrupted directory entries pointing beyond file boundaries
        if offset + required_size > len(data):
            logger.debug(
                "safe_unpack: Insufficient data at offset %d. Need %d bytes, have %d. Format: %s",
                offset,
                required_size,
                len(data) - offset,
                format_str
            )
            return None

        return struct.unpack(format_str, data[offset:offset + required_size])
        
    except (struct.error, ValueError) as e:
        # COMPREHENSIVE ERROR HANDLING: Log details but don't crash
        # Provides debugging information while maintaining application stability
        logger.debug(
            "safe_unpack: Error unpacking data at offset %d: %s. Format: %s, Data: %s",
            offset,
            e,
            format_str,
            data[offset:offset + 16].hex() if offset < len(data) else "N/A"
        )
        return None


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


def decode(
    data: bytes, encoding: str = "utf-8", unicode: bool = False, **kwargs
) -> str:
    """Decode bytes to string with PowerBuilder-specific handling.
    
    POWERBUILDER ENCODING FIXES: This function includes critical fixes for
    PowerBuilder's non-standard encoding practices:
    
    1. UTF-16LE byte-order corruption detection and correction
    2. Proper null-terminator handling for different encodings
    3. Automatic fallback strategies for decode errors
    4. Detection of suspicious Unicode patterns (Chinese chars in ASCII names)
    
    PowerBuilder encoding issues:
    - Some versions corrupt UTF-16LE byte order
    - Mixed ASCII/Unicode files with inconsistent null termination
    - Object names sometimes stored with wrong encoding hints

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

    # ENCODING-AWARE NULL HANDLING: Critical fix for proper string termination
    # PowerBuilder uses different null termination patterns for different encodings
    if encoding == "utf-16-le":
        # UTF-16LE: Remove 2-byte null terminators (0x00 0x00), not single null bytes
        # Single null bytes are valid within UTF-16LE strings
        while len(data) >= 2 and data.endswith(b"\x00\x00"):
            data = data[:-2]
    else:
        # ASCII/Latin-1/UTF-8: Remove trailing single null bytes
        data = data.rstrip(b"\x00")

    if not data:
        return ""

    # POWERBUILDER UTF-16LE CORRUPTION DETECTION AND REPAIR
    # Some PowerBuilder versions have a bug where UTF-16LE byte order gets corrupted
    # resulting in Chinese characters appearing in what should be ASCII object names
    if encoding == "utf-16-le":
        try:
            # Standard UTF-16LE decode attempt
            result = data.decode("utf-16-le")

            # CORRUPTION DETECTION: Check for suspicious Unicode patterns
            # PowerBuilder object names should be mostly ASCII, not Chinese/Japanese
            if _has_suspicious_unicode_corruption(result):
                logger.debug(
                    "Detected potential UTF-16LE byte-order corruption, attempting fix"
                )

                # CORRUPTION REPAIR: Attempt byte-order fix
                fixed_data = _fix_utf16_byte_order(data)
                if fixed_data:
                    fixed_result = fixed_data.decode("utf-16-le")
                    # Validate that the fix actually improved the result
                    if _is_more_reasonable_result(fixed_result, result):
                        logger.debug(
                            "Successfully repaired UTF-16LE byte-order corruption"
                        )
                        return fixed_result

            return result

        except UnicodeDecodeError as e:
            logger.warning("UTF-16LE decoding failed: %s, trying fallback methods", e)

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
                "Truncated extraction at item %s/%s, "
                f"offset {item_offset} exceeds data length {len(data)}",
                i,
                count,
            )
            break

        item_data = data[item_offset : item_offset + size]

        if converter:
            try:
                value = converter(item_data)
            except Exception as e:
                logger.warning("Error converting item {i}: %s", e)
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
                "extract_bytes_2_lst: Not enough bytes for block %s (size %s). "
                f"Have {len(b) - idx}, current offset {idx}. "
                f"Input bytes (first 64): {b[:64].hex()}",
                i,
                size,
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

    for i, (size, converter) in enumerate(zip(field_sizes, converters, strict=False)):
        if current_offset + size > len(data):
            logger.warning(
                "Truncated extraction at field %s/%s, "
                f"offset {current_offset} + size {size} exceeds data length {len(data)}",
                i,
                len(field_sizes),
            )
            break

        field_data = data[current_offset : current_offset + size]

        try:
            value = converter(field_data)
        except Exception as e:
            logger.warning("Error converting field %s: %s", i, e)
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
    pb_chars = set(
        "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789_.:()[]"
    )
    fixed_pb = sum(1 for c in fixed_result if c in pb_chars)
    original_pb = sum(1 for c in original_result if c in pb_chars)

    # Prefer result with more ASCII and PowerBuilder-style characters
    fixed_score = fixed_ascii * 2 + fixed_pb
    original_score = original_ascii * 2 + original_pb

    return fixed_score > original_score


def decode_powerbuilder_name_simple(
    data: bytes, is_unicode_context: bool = False
) -> str:
    """Simple, reliable PowerBuilder name decoder without corruption 'fixes'.

    Args:
        data: Raw bytes of the object name
        is_unicode_context: Whether the file uses Unicode encoding

    Returns:
        Decoded object name
    """
    if not data:
        return ""

    # Remove trailing nulls
    if is_unicode_context:
        # UTF-16LE - remove pairs of null bytes from end
        while len(data) >= 2 and data[-2:] == b"\x00\x00":
            data = data[:-2]

        # Ensure even number of bytes for UTF-16
        if len(data) % 2 != 0:
            data = data[:-1]

        if data:
            try:
                return data.decode("utf-16le")
            except Exception:
                # Fallback to ASCII
                pass

    # ASCII mode or fallback
    data = data.rstrip(b"\x00")
    if data:
        try:
            return data.decode("ascii")
        except Exception:
            # Last resort - Latin-1 (accepts all bytes)
            return data.decode("latin-1", errors="replace")

    return ""


def decode_powerbuilder_name(data: bytes, is_unicode_context: bool = False) -> str:
    """Decode PowerBuilder object names with automatic corruption detection and fixing.

    ADVANCED POWERBUILDER NAME DECODER: This function implements sophisticated
    multi-strategy decoding to handle PowerBuilder's inconsistent naming conventions:
    
    STRATEGIES IMPLEMENTED:
    1. Context-aware decoding (Unicode hint from file metadata)
    2. Auto-detection based on data characteristics
    3. ASCII/Latin-1 fallback for legacy files
    4. UTF-8 support for modern files
    5. Byte-order corruption repair (disabled - was causing issues)
    
    CANDIDATE SELECTION:
    - Multiple decoding attempts with quality scoring
    - Best candidate selection based on ASCII content and PB patterns
    - Preference for reasonable object name patterns (w_, u_, etc.)
    
    This replaces simple decode() calls with intelligent format detection.

    Args:
        data: Raw bytes of the object name
        is_unicode_context: Whether the file context is Unicode (used as hint, not absolute)

    Returns:
        Properly decoded object name
    """
    # REMOVED: premature return that was causing encoding issues
    # return decode_powerbuilder_name_simple(data, is_unicode_context)
    if not data:
        return ""

    # Keep original data for fallback attempts

    # Try multiple decoding strategies and pick the most reasonable result
    candidates = []

    # Strategy 1: Use context hint first (but not exclusively)
    if is_unicode_context:
        try:
            # UTF-16LE with proper null terminator handling
            unicode_data = data
            while len(unicode_data) >= 2 and unicode_data.endswith(b"\x00\x00"):
                unicode_data = unicode_data[:-2]

            if unicode_data and len(unicode_data) % 2 == 0:
                result = decode(unicode_data, unicode=True)
                if result and _is_reasonable_object_name(result):
                    candidates.append(("unicode_context", result))
        except Exception as e:
            logger.debug("Unicode context decoding failed: %s", e)

    # Strategy 2: Auto-detect based on data characteristics
    if _looks_like_utf16(data):
        try:
            unicode_data = data
            while len(unicode_data) >= 2 and unicode_data.endswith(b"\x00\x00"):
                unicode_data = unicode_data[:-2]

            if unicode_data:
                # Ensure even number of bytes
                if len(unicode_data) % 2 != 0:
                    unicode_data = unicode_data + b"\x00"

                result = decode(unicode_data, unicode=True)
                if result and _is_reasonable_object_name(result):
                    candidates.append(("auto_unicode", result))
        except Exception as e:
            logger.debug("Auto-detect Unicode decoding failed: %s", e)

    # Strategy 3: ASCII/Latin-1 decoding
    try:
        ascii_data = data.rstrip(b"\x00")
        if ascii_data:
            result = ascii_data.decode("latin-1")
            if result and _is_reasonable_object_name(result):
                candidates.append(("latin1", result))
    except Exception as e:
        logger.debug("Latin-1 decoding failed: %s", e)

    # Strategy 4: Try UTF-8 (sometimes files have mixed encoding)
    try:
        utf8_data = data.rstrip(b"\x00")
        if utf8_data:
            result = utf8_data.decode("utf-8")
            if result and _is_reasonable_object_name(result):
                candidates.append(("utf8", result))
    except Exception as e:
        logger.debug("UTF-8 decoding failed: %s", e)

    # STRATEGY 5 DISABLED: Byte-order corrected UTF-16
    # This strategy was disabled because it was corrupting valid UTF-16LE data
    # The byte-order repair logic was too aggressive and "fixed" data that wasn't broken
    # Leaving the code commented for reference:
    # 
    # try:
    #     if len(data) >= 2 and len(data) % 2 == 0:
    #         fixed_data = _fix_utf16_byte_order(data)
    #         if fixed_data:
    #             fixed_data = fixed_data.rstrip(b"\x00\x00")
    #             if fixed_data and len(fixed_data) % 2 == 0:
    #                 result = decode(fixed_data, unicode=True)
    #                 if result and _is_reasonable_object_name(result):
    #                     candidates.append(("fixed_unicode", result))
    # except Exception as e:
    #     logger.debug("Fixed Unicode decoding failed: %s", e)

    # Choose the best candidate
    if not candidates:
        logger.warning("No valid decoding found for data: %s...", data[:20].hex())
        return f"<DECODE_ERROR_{data[:8].hex()}>"

    # If only one candidate, use it
    if len(candidates) == 1:
        method, result = candidates[0]
        logger.debug("PowerBuilder name decoded using {method}: '%s'", result)
        return result

    # Multiple candidates - choose the most reasonable one
    best_candidate = _choose_best_candidate(candidates)
    method, result = best_candidate

    if len(candidates) > 1:
        logger.debug(
            "Multiple decoding candidates found, chose %s: '%s' from %s",
            method,
            result,
            [c[0] for c in candidates],
        )

    return result


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
    if data.startswith((b"\xff\xfe", b"\xfe\xff")):
        return True

    # Check if even number of bytes (UTF-16 requirement)
    if len(data) % 2 != 0:
        return False

    # Look for null bytes in even positions (UTF-16LE pattern for ASCII)
    null_in_even = sum(1 for i in range(1, len(data), 2) if data[i] == 0)

    # If more than 50% of odd positions are null, likely UTF-16LE
    return null_in_even > len(data) // 4


def _is_reasonable_object_name(name: str) -> bool:
    """Check if a decoded name looks like a reasonable PowerBuilder object name.
    
    QUALITY FILTER: This function implements heuristics to distinguish
    between valid PowerBuilder object names and corrupted/garbage text.
    
    POWERBUILDER NAMING CONVENTIONS:
    - Typical prefixes: w_, u_, n_, d_, dw_, m_, f_, gf_, s_
    - Common characters: letters, numbers, underscores, dots, parentheses
    - Length: Usually 3-50 characters
    - Control characters indicate corruption
    - Excessive high Unicode suggests byte-order problems

    Args:
        name: Decoded name string

    Returns:
        True if the name appears reasonable for a PowerBuilder object
    """
    if not name or len(name) == 0:
        return False

    # Check for excessive control characters or null bytes (corruption indicators)
    control_chars = sum(1 for c in name if ord(c) < 32 and c not in "\t\n\r")
    if control_chars > len(name) * 0.1:  # More than 10% control chars is suspicious
        return False

    # Check for excessive high Unicode characters (corruption indicator)
    high_unicode = sum(1 for c in name if ord(c) > 255)
    if high_unicode > len(name) * 0.5:  # More than 50% high Unicode chars is suspicious
        return False

    # PowerBuilder names typically contain these characters
    reasonable_chars = set(
        "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789_.:()[]{}$-"
    )
    reasonable_count = sum(1 for c in name if c in reasonable_chars)

    # At least 50% of characters should be "reasonable" for PowerBuilder names
    if len(name) > 0 and reasonable_count / len(name) >= 0.5:
        return True

    # Special case: allow short names with some special characters (like extensions)
    return len(name) <= 5


def _choose_best_candidate(candidates: list[tuple[str, str]]) -> tuple[str, str]:
    """Choose the best decoding candidate from multiple options.

    Args:
        candidates: List of (method, decoded_name) tuples

    Returns:
        Best (method, decoded_name) tuple
    """
    if not candidates:
        return ("error", "<NO_CANDIDATES>")

    if len(candidates) == 1:
        return candidates[0]

    # Score each candidate
    scored_candidates = []
    for method, name in candidates:
        score = _score_object_name(name, method)
        scored_candidates.append((score, method, name))

    # Sort by score (highest first)
    scored_candidates.sort(reverse=True, key=lambda x: x[0])

    best_score, best_method, best_name = scored_candidates[0]
    return (best_method, best_name)


def _score_object_name(name: str, method: str) -> float:
    """Score a decoded object name for reasonableness.
    
    SOPHISTICATED SCORING ALGORITHM: This function implements a multi-factor
    scoring system to rank decoded name candidates by quality:
    
    SCORING FACTORS:
    1. Length appropriateness (3-50 chars optimal)
    2. ASCII character ratio (higher is better)
    3. PowerBuilder-style characters (letters, numbers, _, :, ., etc.)
    4. Control character penalty (corruption indicator)
    5. High Unicode penalty (byte-order corruption indicator)
    6. Method-specific bonuses (latin1 > unicode_context > auto_unicode)
    7. PowerBuilder naming pattern bonuses (w_, u_, etc.)
    8. Extension bonuses (.sru, .srw, etc.)
    
    This scoring system allows the decoder to choose the most plausible
    result when multiple decoding methods produce different outputs.

    Args:
        name: Decoded name
        method: Decoding method used

    Returns:
        Score (higher is better)
    """
    if not name:
        return 0.0

    score = 0.0

    # Base score for non-empty name
    score += 1.0

    # Bonus for reasonable length (PowerBuilder names are typically 3-50 characters)
    if 3 <= len(name) <= 50:
        score += 2.0
    elif len(name) <= 100:
        score += 1.0

    # Count character types
    ascii_chars = sum(1 for c in name if 32 <= ord(c) <= 126)
    control_chars = sum(1 for c in name if ord(c) < 32 and c not in "\t\n\r")
    high_chars = sum(1 for c in name if ord(c) > 255)
    pb_chars = sum(
        1
        for c in name
        if c
        in "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789_.:()[]{}$-"
    )

    # Heavily penalize control characters (corruption indicator)
    if control_chars > 0:
        score -= control_chars * 5.0

    # Penalize excessive high Unicode (corruption indicator)
    if high_chars > len(name) * 0.3:
        score -= high_chars * 2.0

    # Bonus for ASCII characters
    if ascii_chars > 0:
        score += (ascii_chars / len(name)) * 3.0

    # Big bonus for PowerBuilder-style characters
    if pb_chars > 0:
        score += (pb_chars / len(name)) * 5.0

    # Method-specific bonuses (prefer methods that typically work better)
    method_bonuses = {
        "latin1": 1.0,  # Often the most reliable for PB names
        "unicode_context": 0.8,  # Good when context is reliable
        "auto_unicode": 0.6,  # Auto-detection can be hit-or-miss
        "utf8": 0.4,  # Less common in PowerBuilder
        "fixed_unicode": 0.2,  # Last resort, corruption fix
    }
    score += method_bonuses.get(method, 0.0)

    # POWERBUILDER PATTERN RECOGNITION: Bonus for typical naming conventions
    name_lower = name.lower()
    # Common PowerBuilder object prefixes (windows, user objects, etc.)
    if name_lower.startswith(("w_", "u_", "n_", "d_", "dw_", "m_", "f_", "gf_", "s_")):
        score += 3.0  # Strong indicator of valid PowerBuilder name

    # EXTENSION RECOGNITION: Bonus for PowerBuilder file extensions
    pb_extensions = [".sru", ".srw", ".srd", ".srm", ".srf", ".srs", ".sra", ".fun"]
    if any(name_lower.endswith(ext) for ext in pb_extensions):
        score += 2.0  # Valid PowerBuilder extension

    return score
