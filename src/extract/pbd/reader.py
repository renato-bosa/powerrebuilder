"""Unified PBD reader module combining file operations, PE scanning, and resource utilities.

This module merges functionality from:
- extract/pbd/io/file_operations.py - File saving operations
- extract/pbd/io/pe_scanner.py - PE file scanning and PBD extraction
- extract/pbd/io/resource_utils.py - Resource extraction utilities
"""

import json
import logging
import os
import struct
import tempfile
from pathlib import Path
from typing import Any, BinaryIO

from src.extract.pbd.constants import PE_SIGNATURES
from src.extract.pbd.scanner import scan_for_signatures
from src.extract.pbd.type_detection import ObjectTypeDetector
from src.extract.utils.binary import get_mime_type_from_data, safe_filename

logger = logging.getLogger(__name__)


def detect_encoding(data: bytes) -> str:
    """Detect encoding from BOM or by trying common encodings.

    Args:
        data: Binary data to analyze

    Returns:
        Detected encoding name
    """
    # Check for BOM markers
    if data.startswith(b"\xff\xfe"):
        return "utf-16-le"
    if data.startswith(b"\xfe\xff"):
        return "utf-16-be"
    if data.startswith(b"\xff\xfe\x00\x00"):
        return "utf-32-le"
    if data.startswith(b"\x00\x00\xfe\xff"):
        return "utf-32-be"
    if data.startswith(b"\xef\xbb\xbf"):
        return "utf-8-sig"

    # Try common encodings
    encodings = ["utf-8", "latin1", "cp1252", "ascii"]

    for encoding in encodings:
        try:
            data.decode(encoding)
            return encoding
        except (UnicodeDecodeError, LookupError):
            continue

    # Default to latin1 which can decode any byte sequence
    return "latin1"


def save_text_file(obj_name: str, text: str, output_path: str | Path) -> None:
    """Save extracted text to file with PowerBuilder export header.

    Args:
    obj_name: Object name
    text: Text content to save
    output_path: Output directory path
    """
    # Skip saving text files for DataWindow objects
    if obj_name.lower().endswith(".dwo"):
        logger.debug("Skipping text file save for DataWindow object: %s", obj_name)
        return

    # Sanitize the filename
    safe_name = safe_filename(obj_name)

    # Create output directory and file path
    output_path = Path(output_path)
    output_path.mkdir(parents=True, exist_ok=True)
    file_to_open = output_path / safe_name

    # Write the file with PBExportHeader
    with file_to_open.open("w", encoding="utf-8") as output:
        # Use original name in header
        output.write(f"HA$PBExportHeader${obj_name}\n")
        output.write("$PBExportComments$\n")
        output.write(text)
        logger.debug("Saved text file: %s", file_to_open)


def save_binary_file(name: str, data: bytes, output_path: str | Path) -> None:
    """Save binary resource data with metadata.

    Args:
    name: Resource name
    data: Binary data
    output_path: Output directory path
    """
    data_folder = Path(output_path) / "resources"
    data_folder.mkdir(parents=True, exist_ok=True)
    file_to_open = data_folder / name
    with file_to_open.open("wb") as output:
        output.write(data)
    meta_file = data_folder / f"{name}.meta.json"
    metadata = {
        "original_name": name,
        "size_bytes": len(data),
        "mime_type": get_mime_type_from_data(data),
        "extraction_date": str(Path(file_to_open).stat().st_mtime),
    }
    with meta_file.open("w", encoding="utf-8") as meta_output:
        json.dump(metadata, meta_output, indent=2)
    logging.info("Saved binary resource: %s (%s bytes)", name, len(data))


def is_pe_file(file_path: str | Path) -> bool:
    r"""Checks if the given file is a Portable Executable (PE) file.

    It checks for the "MZ" signature at the beginning and the "PE\\0\\0"
    signature at the offset specified in the PE header.

    Args:
    file_path: Path to the file to check

    Returns:
    True if file is a valid PE file, False otherwise
    """
    file_path = Path(file_path)
    if not file_path.is_file():
        return False

    try:
        with file_path.open("rb") as f:
            # Check for MZ signature
            mz_sig = f.read(2)
            if mz_sig != PE_SIGNATURES["MZ"]:
                logger.debug("%s: No MZ signature found.", file_path.name)
                return False

            # Read the offset to PE signature (e_lfanew)
            f.seek(0x3C)
            pe_offset_bytes = f.read(4)
            if len(pe_offset_bytes) < 4:
                logger.debug("%s: Could not read PE signature offset.", file_path.name)
                return False

            pe_offset = int.from_bytes(pe_offset_bytes, byteorder="little")

            # Check for PE signature at the offset
            f.seek(pe_offset)
            pe_sig = f.read(4)
            if pe_sig == PE_SIGNATURES["PE"]:
                logger.debug(
                    f"{file_path.name}: MZ and PE signatures found. Identified as PE file.",
                )
                return True
            logger.debug(
                "%s: PE signature not found at offset %s. Expected %r, got %r.",
                file_path.name,
                pe_offset,
                PE_SIGNATURES["PE"],
                pe_sig,
            )
            return False
    except OSError as e:
        logger.exception("IOError while checking PE file %s: %s", file_path.name, e)
        return False
    except Exception as e:
        logger.exception(
            "Unexpected error while checking PE file %s: %s",
            file_path.name,
            e,
        )
        return False


def find_pbd_header_signatures_in_file(file_handle: BinaryIO) -> list[tuple[int, bool]]:
    """Scans an open binary file handle for PBD header signatures (ASCII and Unicode).

    Args:
    file_handle: An open binary file handle, positioned at the beginning.

    Returns:
    A list of tuples: (offset, is_unicode_header).
    """
    # Import scanner locally to avoid circular imports

    # Use the generic scanner to find all signatures
    signature_results = scan_for_signatures(file_handle)

    found_headers: list[tuple[int, bool]] = []

    # Convert scanner results to the expected format
    for offset in signature_results.get("ASCII_HDR", []):
        found_headers.append((offset, False))

    for offset in signature_results.get("UNICODE_HDR", []):
        found_headers.append((offset, True))

    # Sort by offset
    found_headers.sort(key=lambda x: x[0])

    return found_headers


def validate_pe_structure(pe_file_path: str | Path) -> tuple[bool, str]:
    """Validate PE file structure and return detailed information.

    Args:
    pe_file_path: Path to the PE file to validate

    Returns:
    Tuple of (is_valid, validation_message)
    """
    pe_file_path = Path(pe_file_path)

    if not pe_file_path.exists():
        return False, f"File does not exist: {pe_file_path}"

    if not pe_file_path.is_file():
        return False, f"Path is not a file: {pe_file_path}"

    try:
        with pe_file_path.open("rb") as f:
            # Check file size
            f.seek(0, os.SEEK_END)
            file_size = f.tell()
            f.seek(0)

            if file_size < 64:  # Minimum DOS header size:
                return False, f"File too small to be a valid PE file: {file_size} bytes"

            # Check MZ signature
            mz_sig = f.read(2)
            if mz_sig != PE_SIGNATURES["MZ"]:
                return False, f"Invalid MZ signature: {mz_sig!r}"

            # Check PE offset
            f.seek(0x3C)
            pe_offset_bytes = f.read(4)
            if len(pe_offset_bytes) < 4:
                return False, "Could not read PE signature offset"

            pe_offset = int.from_bytes(pe_offset_bytes, byteorder="little")

            if pe_offset >= file_size - 4:
                return (
                    False,
                    f"PE offset beyond file size: {pe_offset} >= {file_size - 4}",
                )

            # Check PE signature
            f.seek(pe_offset)
            pe_sig = f.read(4)
            if pe_sig != PE_SIGNATURES["PE"]:
                return False, f"Invalid PE signature at offset {pe_offset}: {pe_sig!r}"

            return (
                True,
                f"Valid PE file: {file_size} bytes, PE header at offset {pe_offset}",
            )

    except OSError as e:
        return False, f"I/O error reading file: {e}"
    except Exception as e:
        return False, f"Unexpected error validating PE file: {e}"


# ============================================================================
# Resource Extraction Functions (from resource_utils.py)
# ============================================================================

# Common image signatures
BMP_SIGNATURE = b"BM"
ICO_SIGNATURE = b"\x00\x00\x01\x00"  # Icon File Signature

SIGNATURE_MAP = {
    BMP_SIGNATURE: {
        "ext": ".bmp",
        "name": "BMP",
        "get_size": "get_bmp_size",
        "min_size": 54,
    },  # Min BMP header size
    ICO_SIGNATURE: {
        "ext": ".ico",
        "name": "ICO",
        "get_size": "get_ico_size",
        "min_size": 22,
    },  # 6 (header) + 16 (direntry)
    b"\x89PNG\r\n\x1a\n": {
        "ext": ".png",
        "name": "PNG",
        "get_size": "get_png_size",
        "min_size": 24,
    },  # 8 (sig) + IHDR chunk (12+header) + ...
    b"\xff\xd8\xff": {
        "ext": ".jpg",
        "name": "JPG",
        "get_size": "get_jpg_size",
        "min_size": 20,
    },  # SOI, APP0, ... EOI
    b"GIF87a": {
        "ext": ".gif",
        "name": "GIF",
        "get_size": "get_gif_size",
        "min_size": 13,
    },  # Header + LSD
    b"GIF89a": {
        "ext": ".gif",
        "name": "GIF",
        "get_size": "get_gif_size",
        "min_size": 13,
    },  # Header + LSD
}


def get_bmp_size(data: bytes, offset: int) -> int | None:
    """Get the size of a BMP image from its header."""
    if offset + 6 <= len(data):  # Ensure header for size is present:
        try:
            return struct.unpack_from("<I", data, offset + 2)[0]
        except struct.error:
            return None
    return None


def get_ico_size(data: bytes, offset: int) -> int | None:
    """Get the size of an ICO file by parsing its directory."""
    if offset + 6 <= len(data):  # Initial header: 2 reserved, 2 type, 2 count:
        try:
            num_images = struct.unpack_from("<H", data, offset + 4)[0]
            if num_images == 0 or num_images > 255:  # Sanity check:
                return None

            current_dir_entry_offset = offset + 6
            max_end_offset = offset

            for _ in range(num_images):
                if current_dir_entry_offset + 16 > len(
                    data,
                ):  # ICONDIRENTRY is 16 bytes
                    return None  # Not enough data for all directory entries

                img_size_bytes = struct.unpack_from(
                    "<I",
                    data,
                    current_dir_entry_offset + 8,
                )[0]
                img_offset_bytes = struct.unpack_from(
                    "<I",
                    data,
                    current_dir_entry_offset + 12,
                )[0]

                max_end_offset = max(
                    max_end_offset,
                    offset + img_offset_bytes + img_size_bytes,
                )
                current_dir_entry_offset += 16

            if max_end_offset > offset and max_end_offset <= len(data):
                return max_end_offset - offset  # Total size of the ICO structure
            return None  # Could not determine a valid size
        except struct.error:
            return None
    return None


def find_embedded_resources(data: bytes) -> list[dict[str, Any]]:
    """Find all embedded resources (images, etc.) in binary data.

    Args:
    data: Binary data to search

    Returns:
    List of dictionaries with resource information
    """
    resources = []

    for sig_bytes, img_info in SIGNATURE_MAP.items():
        start_search_idx = 0
        while start_search_idx < len(data):
            found_at = data.find(sig_bytes, start_search_idx)
            if found_at == -1:
                break

            # Get size based on image type
            size_func_name = img_info.get("get_size")
            if size_func_name:
                size_func = globals().get(size_func_name)
                if size_func:
                    size = size_func(data, found_at)
                    if size and size >= img_info.get("min_size", 1):
                        resources.append(
                            {
                                "offset": found_at,
                                "size": size,
                                "type": img_info["name"],
                                "extension": img_info["ext"],
                                "data": data[found_at : found_at + size],
                            }
                        )

            start_search_idx = found_at + 1

    return resources


def extract_and_save_resources(data: bytes, object_name: str, output_path: Path) -> int:
    """Extract and save all embedded resources from binary data.

    Args:
    data: Binary data containing resources
    object_name: Name of the source object
    output_path: Directory to save extracted resources

    Returns:
    Number of resources extracted
    """
    resources = find_embedded_resources(data)

    if not resources:
        return 0

    # Create resources subdirectory
    resources_dir = output_path / "embedded_resources" / safe_filename(object_name)
    resources_dir.mkdir(parents=True, exist_ok=True)

    for idx, resource in enumerate(resources):
        # Generate filename
        filename = f"{object_name}_{idx:03d}_{resource['type']}{resource['extension']}"
        file_path = resources_dir / filename

        # Save resource
        with file_path.open("wb") as f:
            f.write(resource["data"])

        logger.info(
            "Extracted %s resource: %s (%s bytes)",
            resource["type"],
            filename,
            resource["size"],
        )

    return len(resources)


# ============================================================================
# Private Helper Functions
# ============================================================================


def _get_object_type_info(entry_name: str) -> tuple[str, bool, bool, bool]:
    """Get object type information.

    Returns:
    Tuple of (obj_type_name, contains_pcode, is_datawindow, is_structure)
    """
    obj_type_name, contains_pcode = ObjectTypeDetector.get_object_info(entry_name)
    is_datawindow = ObjectTypeDetector.is_datawindow(entry_name)
    is_structure = ObjectTypeDetector.is_structure(entry_name)
    return obj_type_name, contains_pcode, is_datawindow, is_structure


def _should_skip_text_file(entry_name: str, is_structure: bool) -> bool:
    """Determine if text file creation should be skipped.

    Returns:
    True if text file should be skipped, False otherwise
    """
    # List of extensions that are purely binary or contain mixed data
    binary_only_extensions = (
        ".udo",
        ".win",
        ".men",
        ".apl",
        ".xxy",
        ".cur",
        ".bin",
        ".fun",
        ".mef",
        ".apf",
    )

    if entry_name.lower().endswith(binary_only_extensions):
        logger.info("Skipping text file creation for binary file: %s", entry_name)
        return True
    if is_structure:
        # Structures (.str) might have text definitions we want to preserve
        return False

    return False


def _extract_utf16_syntax(data: bytes, start_pos: int) -> str | None:
    """Extract UTF-16 LE encoded DataWindow syntax.

    Args:
    data: Binary data containing UTF-16 text
    start_pos: Starting position of the text

    Returns:
    Extracted syntax string or None
    """
    try:
        # Find a reasonable end position
        end_markers = [
            b"\x00\x00\x00\x00",  # Four null bytes
            b"binary(",  # Binary data section
        ]

        end_pos = len(data)
        for marker in end_markers:
            pos = data.find(marker, start_pos)
            if pos > start_pos:
                end_pos = min(end_pos, pos)

        # Extract the UTF-16 data
        utf16_data = data[start_pos:end_pos]

        # Decode UTF-16 LE - process character by character to handle corruption
        text_parts = []
        i = 0

        while i < len(utf16_data) - 1:
            if i + 1 < len(utf16_data):
                try:
                    char = utf16_data[i : i + 2].decode("utf-16-le", errors="strict")
                    # Keep printable ASCII, whitespace, and specific Unicode characters that might be parameter placeholders
                    if (
                        32 <= ord(char) < 127 or char in "\r\n\t" or char == "Ā"
                    ):  # U+0100 - corrupted parameter placeholder
                        text_parts.append(char)
                        i += 2
                except OSError as e:
                    logger.debug("Exception caught: %s", e)
                    # Skip invalid UTF-16 sequences
                    i += 2
            else:
                i += 1

        syntax = "".join(text_parts)

        # Validate that we got DataWindow syntax
        if len(syntax) > 50 and ("PBSELECT" in syntax or "release" in syntax):
            logger.debug(
                f"Successfully extracted {len(syntax)} characters of DataWindow syntax"
            )
            return syntax

    except OSError as e:
        logger.debug("Error extracting UTF-16 DataWindow: %s", e)

    return None


def _extract_datawindow_syntax(binary_data: bytes, object_name: str) -> str | None:
    """Attempt to extract DataWindow syntax from binary data.

    Returns:
    Extracted syntax or None if extraction failed
    """
    # First try direct extraction by looking for PBSELECT patterns
    logger.debug("Attempting direct DataWindow extraction for %s", object_name)

    # Look for PBSELECT in UTF-16 LE (most common)
    pbselect_utf16 = b"P\x00B\x00S\x00E\x00L\x00E\x00C\x00T\x00"
    utf16_pos = binary_data.find(pbselect_utf16)

    if utf16_pos >= 0:
        logger.debug(
            "Found UTF-16 PBSELECT at offset 0x%08X in %s", utf16_pos, object_name
        )
        # Extract UTF-16 encoded DataWindow syntax
        syntax = _extract_utf16_syntax(binary_data, utf16_pos)
        if syntax:
            return syntax

    # Look for 'release' statement which starts DataWindow definitions
    release_utf16 = b"r\x00e\x00l\x00e\x00a\x00s\x00e\x00"
    release_pos = binary_data.find(release_utf16)

    if release_pos >= 0:
        logger.debug(
            "Found UTF-16 'release' at offset 0x%08X in %s", release_pos, object_name
        )
        syntax = _extract_utf16_syntax(binary_data, release_pos)
        if syntax:
            return syntax

    # Try the original extraction methods as fallback
    try:
        # Try enhanced extraction first
        from src.decompile.extractors.datawindow import extraction_manager

        syntax, success = extraction_manager.extract_from_pbd_object(
            binary_data, object_name
        )
        return syntax if success else None
    except ImportError:
        # Fallback to standard extraction
        try:
            from src.decompile.extractors.datawindow import extract_datawindow_from_pbd

            return extract_datawindow_from_pbd(binary_data, object_name)
        except ImportError:
            logger.debug("DataWindow extractor not available - saving raw data")
        except OSError as e:
            logger.debug("DataWindow extraction failed: %s", e)
    except OSError as e:
        logger.debug("Enhanced DataWindow extraction failed: %s", e)

    return None


def _create_temp_pbd_file(pbd_data: bytes, pe_file_stem: str) -> Path:
    """Create temporary file with PBD data."""
    with tempfile.NamedTemporaryFile(
        delete=False,
        suffix=".pbd",
        prefix=f"embedded_{pe_file_stem}_",
    ) as tmp_file:
        tmp_file.write(pbd_data)
        return Path(tmp_file.name)


def _cleanup_temp_file(temp_file: Path | None) -> None:
    """Clean up temporary file if it exists."""
    if temp_file and temp_file.exists():
        try:
            os.unlink(temp_file)
            logger.debug("Cleaned up temporary PBD file: %s", temp_file)
        except OSError as e:
            logger.exception("Error deleting temporary PBD file %s: %s", temp_file, e)
