"""Entry structures for PowerBuilder extraction."""

import datetime
import logging
import struct
from dataclasses import dataclass, field
from typing import Any

from src.extract.utils.binary import decode_powerbuilder_name

logger = logging.getLogger(__name__)


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

    @property
    def commentlen(self) -> int:
        """Length of the comment string."""
        return len(self.comment) if self.comment else 0


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

    # If no signature, try parsing as entry data without signature
    # (entries within nodes don't have ENT* signatures)
    return extract_entry_def_no_signature(arr)


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
        # Check if this looks like a PowerBuilder entry with name at offset 28
        # This is common in some PB versions where the entry has a different structure
        if len(arr) >= 32 and arr[28:30] != b"\x00\x00":
            # Try parsing with name at offset 28 (special format)
            name_start = 28

            # Look for UTF-16 null terminator
            name_end = name_start
            while name_end < len(arr) - 1:
                if arr[name_end] == 0 and arr[name_end + 1] == 0:
                    break
                name_end += 2

            if name_end >= len(arr) - 1:
                return None

            object_name = decode_powerbuilder_name(
                arr[name_start:name_end], is_unicode_context=True
            )

            # For this format, extract what we can from the header
            # The exact structure varies but we can get some info
            data_offset = struct.unpack("<I", arr[4:8])[0] if len(arr) >= 8 else 0
            size = struct.unpack("<I", arr[8:12])[0] if len(arr) >= 12 else 0

            # Skip trying to parse timestamps for this format
            return PbEntryDefinition(
                offset=0,  # Will be set by caller
                object_name=object_name,
                object_type=_determine_object_type(object_name),
                data_offset=data_offset,
                size=size,
                comment="",
                creation_datetime=None,
                modification_datetime=None,
                is_unicode=True,
            )

        # Standard parsing path
        offset = 4  # Skip signature

        # Parse fixed header fields
        # Structure varies by PB version, but common fields:
        # - Data offset (4 bytes)
        # - Size (4 bytes)
        # - Type info (4 bytes)
        # - Timestamps (8 bytes each)

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

        object_name = decode_powerbuilder_name(
            arr[name_start:name_end], is_unicode_context=False
        )
        offset = name_end + 1

        # Parse comment if present
        comment = ""
        if offset < len(arr) - 1:
            comment_end = arr.find(b"\x00", offset)
            if comment_end > offset:
                comment = decode_powerbuilder_name(
                    arr[offset:comment_end], is_unicode_context=False
                )

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

        object_name = decode_powerbuilder_name(
            arr[name_start:name_end], is_unicode_context=True
        )
        offset = name_end + 2

        # Parse Unicode comment if present
        comment = ""
        if offset < len(arr) - 2:
            comment_end = arr.find(b"\x00\x00", offset)
            if comment_end > offset and comment_end % 2 == 0:
                comment = decode_powerbuilder_name(
                    arr[offset:comment_end], is_unicode_context=True
                )

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
            object_name = decode_powerbuilder_name(
                arr[offset:name_end], is_unicode_context=True
            )
        else:
            # Fall back to ASCII
            name_end = arr.find(b"\x00", offset)
            if name_end > offset:
                object_name = decode_powerbuilder_name(
                    arr[offset:name_end], is_unicode_context=False
                )
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


def extract_entry_def_no_signature(arr: bytes) -> PbEntryDefinition | None:
    """Extract entry definition from raw bytes without signature.

    This is used for entries within nodes, which don't have ENT* signatures.
    The data starts directly with the entry structure.

    Args:
        arr: Raw entry data without signature

    Returns:
        Entry definition or None if parsing fails
    """
    if len(arr) < 28:  # Minimum size without signature
        return None

    logger.debug(f"extract_entry_def_no_signature: First 32 bytes: {arr[:32].hex()}")

    try:
        offset = 0  # No signature to skip

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
            creation_raw = struct.unpack("<Q", arr[offset : offset + 8])[0]
            modification_raw = struct.unpack("<Q", arr[offset + 8 : offset + 16])[0]
            offset += 16

            if creation_raw > 0:
                creation_time = _filetime_to_datetime(creation_raw)
            if modification_raw > 0:
                modification_time = _filetime_to_datetime(modification_raw)

        # Parse object name
        name_start = offset
        logger.debug(
            f"Looking for name at offset {name_start}, data_offset={data_offset}, size={size}"
        )
        logger.debug(
            f"Name area (32 bytes from offset {name_start}): {arr[name_start : name_start + 32].hex()}"
        )
        name_end = arr.find(b"\x00", name_start)

        if name_end == -1 or name_end - name_start > 255:
            # Try as Unicode if ASCII fails
            name_end = arr.find(b"\x00\x00", name_start)
            if name_end == -1 or name_end - name_start > 510:
                return None
            object_name = decode_powerbuilder_name(
                arr[name_start:name_end], is_unicode_context=True
            )
            offset = name_end + 2
        else:
            object_name = decode_powerbuilder_name(
                arr[name_start:name_end], is_unicode_context=False
            )
            offset = name_end + 1

        # Parse comment if present
        comment = ""
        if offset < len(arr) - 1:
            comment_end = arr.find(b"\x00", offset)
            if comment_end > offset:
                comment = decode_powerbuilder_name(
                    arr[offset:comment_end], is_unicode_context=False
                )

        # Determine object type from name extension
        object_type = _determine_object_type(object_name)

        return PbEntryDefinition(
            offset=0,  # Will be set by caller
            object_name=object_name,
            object_type=object_type,
            data_offset=data_offset,
            size=size,
            comment=comment,
            creation_datetime=creation_time,
            modification_datetime=modification_time,
            is_unicode=False,
        )

    except Exception as e:
        logger.debug(f"Failed to parse entry without signature: {e}")
        return None
