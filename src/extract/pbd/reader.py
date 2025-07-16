"""Unified PBD reader module combining file operations, PE scanning, and resource utilities.

This module merges functionality from:
- extract/pbd/io/file_operations.py - File saving operations
- extract/pbd/io/pe_scanner.py - PE file scanning and PBD extraction
- extract/pbd/io/resource_utils.py - Resource extraction utilities
"""

import base64
import json
import logging
import os
import struct
import tempfile
from pathlib import Path
from typing import TYPE_CHECKING, Any, AsyncIterator, BinaryIO, Dict, Iterator, List, Optional, Tuple, Union
import asyncio

from src.common.constants import BUFFER_SIZE, HEADER_SIZE
from src.common.streaming import StreamReader, AsyncStreamReader
from src.extract.pbd.constants import PE_SIGNATURES, SOURCE_EXTENSIONS
from src.extract.utils.binary import get_mime_type_from_data, safe_filename

logger = logging.getLogger(__name__)

# Avoid circular imports
if TYPE_CHECKING:
    from src.extract.pbd.structures.data_block import DataClass
    from src.extract.pbd.structures.entry import PbEntryDefinition


def detect_encoding(data: bytes, default: str = "latin1") -> str:
    """Detect the encoding of data by checking for BOMs and trying different encodings.
    
    Args:
        data: Binary data to check
        default: Default encoding to use if detection fails
        
    Returns:
        Detected encoding name
    """
    # Check for BOMs (Byte Order Marks)
    if data.startswith(b'\xff\xfe'):
        return "utf-16-le"
    elif data.startswith(b'\xfe\xff'):
        return "utf-16-be"
    elif data.startswith(b'\xff\xfe\x00\x00'):
        return "utf-32-le"
    elif data.startswith(b'\x00\x00\xfe\xff'):
        return "utf-32-be"
    elif data.startswith(b'\xef\xbb\xbf'):
        return "utf-8-sig"
    
    # Try to detect based on content patterns
    # Check for UTF-16 patterns (alternating nulls)
    if len(data) >= 100:
        sample = data[:200]
        null_count = sample.count(b'\x00')
        if null_count > len(sample) * 0.3:  # More than 30% nulls
            # Check if nulls are in even or odd positions (UTF-16 pattern)
            even_nulls = sum(1 for i in range(0, len(sample), 2) if i < len(sample) and sample[i] == 0)
            odd_nulls = sum(1 for i in range(1, len(sample), 2) if i < len(sample) and sample[i] == 0)
            if odd_nulls > even_nulls * 0.8:  # Mostly odd position nulls = UTF-16-LE
                return "utf-16-le"
            elif even_nulls > odd_nulls * 0.8:  # Mostly even position nulls = UTF-16-BE
                return "utf-16-be"
    
    # Try decoding with common encodings
    encodings_to_try = ["utf-8", "latin1", "cp1252", "iso-8859-1"]
    
    for encoding in encodings_to_try:
        try:
            # Try to decode a sample
            sample = data[:min(1000, len(data))]
            decoded = sample.decode(encoding)
            # Check if result looks reasonable (mostly printable characters)
            printable_ratio = sum(1 for c in decoded if c.isprintable() or c.isspace()) / len(decoded)
            if printable_ratio > 0.95:
                return encoding
        except (UnicodeDecodeError, UnicodeError):
            continue
    
    return default

# ============================================================================
# File Operations (from file_operations.py)
# ============================================================================

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
        output.write(f"HA$PBExportHeader${obj_name}\n")  # Use original name in header
        output.write("$PBExportComments$\n")
        output.write(text)
    logger.debug("Saved text file: %s", file_to_open)


def save_pcode_file(obj_name: str, data: bytes, output_path: str | Path) -> None:
    """Save P-code binary data to file.

    Args:
        obj_name: Object name
        data: Binary P-code data
        output_path: Output directory path
    """
    # Sanitize the base filename
    safe_base = safe_filename(obj_name)

    # Create pcode filename
    if safe_base.lower().endswith(".fun"):
        # Already a .fun file, keep the name
        pcode_name = safe_base
    elif safe_base.lower().endswith(".srf"):
        pcode_name = safe_base[:-4] + ".fun"
    elif safe_base.lower().endswith((".udo", ".win")):
        # Older formats: .udo → .fun, .win → .fun
        ext_len = 4 if safe_base.lower().endswith(".udo") else 4
        pcode_name = safe_base[:-ext_len] + ".fun"
    else:
        # Standard .sr* extensions: .sru → .srf, .srw → .srf, etc.
        pcode_name = safe_base[:-1] + "f"

    # Create output directory and file path
    output_path = Path(output_path)
    output_path.mkdir(parents=True, exist_ok=True)
    file_to_open = output_path / pcode_name

    # Write the file with export header for .fun files
    with file_to_open.open("wb") as output:
        if pcode_name.lower().endswith(".fun"):
            # Add PowerBuilder export header for .fun files
            header = f"HA$PBExportHeader${obj_name}\n$PBExportComments$\n".encode()
            output.write(header)
        output.write(data)
    logger.debug("Saved pcode file: %s", file_to_open)


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


def save_binary_as_base64(name: str, data: bytes, output_path: str | Path) -> None:
    """Save binary data as base64-encoded JSON.

    Args:
        name: Resource name
        data: Binary data
        output_path: Output directory path
    """
    data_folder = Path(output_path) / "resources_base64"
    data_folder.mkdir(parents=True, exist_ok=True)
    base64_data = base64.b64encode(data).decode("ascii")
    json_data = {
        "original_name": name,
        "mime_type": get_mime_type_from_data(data),
        "encoding": "base64",
        "data": base64_data,
    }
    json_file = data_folder / f"{Path(name).stem}.json"
    with json_file.open("w", encoding="utf-8") as output:
        json.dump(json_data, output)
    logging.info("Saved base64 resource: %s (%s chars)", name, len(base64_data))


def save_to_file(
    entry: "PbEntryDefinition",
    data: List["DataClass"],
    output_path: str | Path,
    is_unicode: bool = False,
) -> None:
    """Save extracted entry data to file(s) based on entry type.

    Args:
        entry: Entry definition with metadata
        data: List of data blocks
        output_path: Directory to save files to
        is_unicode: Whether the data is Unicode encoded
    """
    # Import here to avoid circular dependency
    from src.common.utils.object_type_detector import ObjectTypeDetector
    from src.extract.pbd.structures.data_block import get_text_from_data

    # Get object type information
    obj_type_name, contains_pcode = ObjectTypeDetector.get_object_info(entry.objectname)
    is_datawindow = ObjectTypeDetector.is_datawindow(entry.objectname)
    is_structure = ObjectTypeDetector.is_structure(entry.objectname)

    # Handle DataWindow objects
    if is_datawindow:
        _process_datawindow(entry, data, output_path)
        return

    # Handle Structure objects
    if is_structure:
        _process_structure(entry, data, output_path, is_unicode)
        return

    # Check if this object contains P-code
    is_potential_pcode: bool = contains_pcode and entry.objectname.lower().endswith(
        tuple(SOURCE_EXTENSIONS)
    )

    # Determine if we should skip text file creation
    should_skip_text_file = _should_skip_text_file(entry.objectname, is_structure)

    if not should_skip_text_file:
        # For non-binary files, proceed with text extraction
        text: str = get_text_from_data(data, is_unicode)
        comment_len: int = entry.commentlen
        text_content_after_comment = text[comment_len:]

        if is_potential_pcode:
            _log_pcode_info(entry, text_content_after_comment, comment_len)

        save_text_file(entry.objectname, text_content_after_comment, output_path)

    if is_potential_pcode:
        _process_pcode(entry, data, output_path)


# ============================================================================
# PE Scanner Functions (from pe_scanner.py) 
# ============================================================================

def is_pe_file(file_path: str | Path) -> bool:
    """Checks if the given file is a Portable Executable (PE) file.

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
        with open(file_path, "rb") as f:
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
                f"{file_path.name}: PE signature not found at offset {pe_offset}. Expected {PE_SIGNATURES['PE']!r}, got {pe_sig!r}.",
            )
            return False
    except OSError as e:
        logger.exception("IOError while checking PE file %s: %s", file_path.name, e)
        return False
    except Exception as e:
        logger.exception(
            f"Unexpected error while checking PE file {file_path.name}: {e}",
        )
        return False


def find_pbd_header_signatures_in_file(file_handle: BinaryIO) -> List[Tuple[int, bool]]:
    """Scans an open binary file handle for PBD header signatures (ASCII and Unicode).

    Args:
        file_handle: An open binary file handle, positioned at the beginning.

    Returns:
        A list of tuples: (offset, is_unicode_header).
    """
    # Import scanner locally to avoid circular imports
    from src.extract.pbd.scanner import scan_for_signatures

    # Use the generic scanner to find all signatures
    signature_results = scan_for_signatures(file_handle)

    found_headers: List[Tuple[int, bool]] = []

    # Convert scanner results to the expected format
    for offset in signature_results.get("ASCII_HDR", []):
        found_headers.append((offset, False))

    for offset in signature_results.get("UNICODE_HDR", []):
        found_headers.append((offset, True))

    # Sort by offset
    found_headers.sort(key=lambda x: x[0])

    return found_headers


def find_and_extract_pbds_from_pe(
    pe_file_path: str | Path,
    output_base_dir: str | Path,
    silent_progress: bool = True,
) -> int:
    """Detects and extracts embedded PBDs from a PE file.

    Args:
        pe_file_path: Path to the PE file.
        output_base_dir: Base directory where extracted PBDs will be saved
                         (in subdirectories named after the PE file and PBD offset).
        silent_progress: If True, suppress progress bars during extraction.

    Returns:
        The number of PBDs successfully found and extracted.
    """
    pe_file_path = Path(pe_file_path)
    output_base_dir = Path(output_base_dir)

    if not is_pe_file(pe_file_path):
        logger.info("%s is not a PE file or could not be read. Skipping.", pe_file_path.name)
        return 0

    logger.info("Scanning PE file %s for embedded PBDs...", pe_file_path.name)
    extracted_pbd_count = 0

    try:
        with open(pe_file_path, "rb") as pe_file_handle:
            pbd_header_infos = find_pbd_header_signatures_in_file(pe_file_handle)

            if not pbd_header_infos:
                logger.info("No PBD header signatures found in %s.", pe_file_path.name)
                return 0

            logger.info("Found %s potential PBD header(s) in %s.", len(pbd_header_infos), pe_file_path.name)

            pe_file_handle.seek(0, os.SEEK_END)
            pe_file_size = pe_file_handle.tell()

            for pbd_offset, is_unicode in pbd_header_infos:
                if _process_single_pbd(pe_file_handle, pe_file_path, pbd_offset, is_unicode, output_base_dir, pe_file_size, silent_progress):
                    extracted_pbd_count += 1

    except OSError as e:
        logger.exception("IOError while processing PE file %s: %s", pe_file_path.name, e)
    except Exception as e:
        logger.error("Unexpected error while processing PE file %s: %s", pe_file_path.name, e, exc_info=True)

    # Log summary
    if extracted_pbd_count > 0:
        logger.info("Successfully extracted %s embedded PBD(s) from %s.", extracted_pbd_count, pe_file_path.name)
    else:
        logger.info("No PBDs were successfully extracted from %s.", pe_file_path.name)

    return extracted_pbd_count


def validate_pe_structure(pe_file_path: str | Path) -> Tuple[bool, str]:
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

            if file_size < 64:  # Minimum DOS header size
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
                return False, f"PE offset beyond file size: {pe_offset} >= {file_size - 4}"

            # Check PE signature
            f.seek(pe_offset)
            pe_sig = f.read(4)
            if pe_sig != PE_SIGNATURES["PE"]:
                return False, f"Invalid PE signature at offset {pe_offset}: {pe_sig!r}"

            return True, f"Valid PE file: {file_size} bytes, PE header at offset {pe_offset}"

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
        "ext": ".bmp", "name": "BMP", "get_size": "get_bmp_size", "min_size": 54,
    },  # Min BMP header size
    ICO_SIGNATURE: {
        "ext": ".ico", "name": "ICO", "get_size": "get_ico_size", "min_size": 22,
    },  # 6 (header) + 16 (direntry)
    b"\x89PNG\r\n\x1a\n": {
        "ext": ".png", "name": "PNG", "get_size": "get_png_size", "min_size": 24,
    },  # 8 (sig) + IHDR chunk (12+header) + ...
    b"\xFF\xD8\xFF": {
        "ext": ".jpg", "name": "JPG", "get_size": "get_jpg_size", "min_size": 20,
    },  # SOI, APP0, ... EOI
    b"GIF87a": {
        "ext": ".gif", "name": "GIF", "get_size": "get_gif_size", "min_size": 13,
    },  # Header + LSD
    b"GIF89a": {
        "ext": ".gif", "name": "GIF", "get_size": "get_gif_size", "min_size": 13,
    },  # Header + LSD
}


def get_bmp_size(data: bytes, offset: int) -> Optional[int]:
    """Get the size of a BMP image from its header."""
    if offset + 6 <= len(data):  # Ensure header for size is present
        try:
            return struct.unpack_from("<I", data, offset + 2)[0]
        except struct.error:
            return None
    return None


def get_ico_size(data: bytes, offset: int) -> Optional[int]:
    """Get the size of an ICO file by parsing its directory."""
    if offset + 6 <= len(data):  # Initial header: 2 reserved, 2 type, 2 count
        try:
            num_images = struct.unpack_from("<H", data, offset + 4)[0]
            if num_images == 0 or num_images > 255:  # Sanity check
                return None

            current_dir_entry_offset = offset + 6
            max_end_offset = offset

            for _ in range(num_images):
                if current_dir_entry_offset + 16 > len(
                    data,
                ):  # ICONDIRENTRY is 16 bytes
                    return None  # Not enough data for all directory entries

                img_size_bytes = struct.unpack_from(
                    "<I", data, current_dir_entry_offset + 8,
                )[0]
                img_offset_bytes = struct.unpack_from(
                    "<I", data, current_dir_entry_offset + 12,
                )[0]

                max_end_offset = max(
                    max_end_offset, offset + img_offset_bytes + img_size_bytes,
                )
                current_dir_entry_offset += 16

            if max_end_offset > offset and max_end_offset <= len(data):
                return max_end_offset - offset  # Total size of the ICO structure
            return None  # Could not determine a valid size
        except struct.error:
            return None
    return None


def find_embedded_resources(data: bytes) -> List[Dict[str, Any]]:
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
                        resources.append({
                            "offset": found_at,
                            "size": size,
                            "type": img_info["name"],
                            "extension": img_info["ext"],
                            "data": data[found_at:found_at + size]
                        })

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
            f.write(resource['data'])

        logger.info(f"Extracted {resource['type']} resource: {filename} ({resource['size']} bytes)")

    return len(resources)


# ============================================================================
# Private Helper Functions
# ============================================================================

def _get_object_type_info(entry_name: str) -> Tuple[str, bool, bool, bool]:
    """Get object type information.

    Returns:
        Tuple of (obj_type_name, contains_pcode, is_datawindow, is_structure)
    """
    from src.common.utils.object_type_detector import ObjectTypeDetector

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
        ".udo", ".win", ".men", ".apl", ".xxy", ".cur", ".bin", ".fun", ".mef", ".apf",
    )

    if entry_name.lower().endswith(binary_only_extensions):
        logger.info(
            f"Skipping text file creation for binary file: {entry_name}"
        )
        return True
    elif is_structure:
        # Structures (.str) might have text definitions we want to preserve
        return False

    return False


def _process_datawindow(
    entry: "PbEntryDefinition", data: List["DataClass"], output_path: str | Path,
) -> None:
    """Process and save DataWindow object."""
    logger.info("Processing DataWindow object: %s", entry.objectname)

    # Add defensive check for data parameter
    if not isinstance(data, list):
        logger.error(
            f"_process_datawindow: Expected list of DataClass objects, got {type(data)} for {entry.objectname}"
        )
        # Try to recover by wrapping in a list if it's a single DataClass
        if hasattr(data, 'address') and hasattr(data, 'data'):
            data = [data]
        else:
            logger.error(f"Cannot process DataWindow {entry.objectname}: invalid data type")
            save_binary_file(entry.objectname, b'', output_path)
            return

    # Import here to avoid circular dependency
    from src.extract.pbd.structures.data_block import get_binary_with_dat_headers, get_binary_from_data
    from src.extract.pbd.formatters import DataWindowFormatter

    # First try with DAT headers intact
    try:
        binary_data: bytes = get_binary_with_dat_headers(data)
        logger.debug(f"Trying extraction with DAT headers for {entry.objectname} ({len(binary_data)} bytes)")
    except AttributeError as e:
        logger.error(
            f"AttributeError in get_binary_with_dat_headers for {entry.objectname}: {e}. "
            f"Data type: {type(data)}, Data length: {len(data) if hasattr(data, '__len__') else 'N/A'}"
        )
        if isinstance(data, list) and data:
            logger.error(f"First item in data list - Type: {type(data[0])}, Value: {data[0]!r}")
        # Try without DAT headers as fallback
        binary_data = b''

    # Try to extract DataWindow syntax
    syntax = _extract_datawindow_syntax(binary_data, entry.objectname)

    # If that fails, try without DAT headers
    if not syntax:
        logger.debug(f"DAT header extraction failed, trying raw data for {entry.objectname}")
        raw_data = get_binary_from_data(data)
        syntax = _extract_datawindow_syntax(raw_data, entry.objectname)

    if syntax:
        logger.info(f"Successfully extracted DataWindow syntax for {entry.objectname}")
        # Use DataWindow formatter to save properly formatted files
        safe_name = safe_filename(entry.objectname)
        output_path_obj = Path(output_path)
        output_path_obj.mkdir(parents=True, exist_ok=True)

        # Save formatted DataWindow and SQL files
        main_file, sql_file = DataWindowFormatter.save_formatted_datawindow(
            safe_name, syntax, output_path_obj, save_sql=True
        )
        logger.info(f"Saved DataWindow files: {main_file}, {sql_file}")
    else:
        # Could not extract syntax - save raw binary data
        save_binary_file(entry.objectname, get_binary_from_data(data), output_path)
        logger.warning(
            f"Could not extract DataWindow syntax from {entry.objectname}, saved as binary"
        )


def _process_structure(
    entry: "PbEntryDefinition", data: List["DataClass"], output_path: str | Path, is_unicode: bool,
) -> None:
    """Process and save Structure object."""
    from src.extract.pbd.structures.data_block import get_text_from_data

    logger.debug("Processing Structure object: %s", entry.objectname)
    text: str = get_text_from_data(data, is_unicode)
    comment_len: int = entry.commentlen
    text_content_after_comment = text[comment_len:]

    # Save structure definition as text
    safe_name = safe_filename(entry.objectname)
    output_path_obj = Path(output_path)
    output_path_obj.mkdir(parents=True, exist_ok=True)
    struct_file = output_path_obj / safe_name

    with struct_file.open("w", encoding="utf-8") as output:
        output.write(f"HA$PBExportHeader${entry.objectname}\n")
        output.write("$PBExportComments$\n")
        output.write(text_content_after_comment)
    logger.info("Saved Structure definition to: %s", struct_file)


def _process_pcode(
    entry: "PbEntryDefinition", data: List["DataClass"], output_path: str | Path,
) -> None:
    """Process and save P-code object."""
    from src.extract.pbd.structures.data_block import get_binary_from_data

    logger.info("Saving P-code for %s", entry.objectname)
    # For pcode files, we need to save the raw binary data, not decoded text
    binary_data: bytes = get_binary_from_data(data)
    logger.info(
        f"Binary data size for {entry.objectname}: {len(binary_data)} bytes"
    )

    # Skip the comment section if present
    comment_len: int = entry.commentlen
    if comment_len > 0 and len(binary_data) > comment_len:
        binary_content_after_comment = binary_data[comment_len:]
    else:
        binary_content_after_comment = binary_data

    if (
        entry.objectname.lower().endswith(".srf")
        and "pfcasads" in entry.version.lower()
    ):
        logger.info(
            f"PCODE_SAVE_INFO: Special SRF/pfcasads '{entry.objectname}'. Using full DAT content."
        )
        binary_content_after_comment = binary_data

    save_pcode_file(entry.objectname, binary_content_after_comment, output_path)


def _log_pcode_info(entry: "PbEntryDefinition", text_content: str, comment_len: int) -> None:
    """Log P-code debugging information."""
    logger.debug(
        f"PCODE_SAVE_INFO: Entry='{entry.objectname}', Version='{entry.version}'"
    )
    logger.debug("PCODE_SAVE_INFO:   entry.objectsize: %s", entry.objectsize)
    logger.debug("PCODE_SAVE_INFO:   entry.commentlen: %s", entry.commentlen)
    logger.debug(
        f"PCODE_SAVE_INFO:   len(text) (total before strip): {len(text_content) + comment_len}"
    )
    logger.debug(
        f"PCODE_SAVE_INFO:   len(text_content_after_comment): {len(text_content)}"
    )
    if 0 < len(text_content) < 200:
        logger.debug(
            f"PCODE_SAVE_INFO:   Content preview: '{text_content[:100]}'"
        )


def _extract_utf16_syntax(data: bytes, start_pos: int) -> Optional[str]:
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
            b'\x00\x00\x00\x00', # Four null bytes
            b'binary(', # Binary data section
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
                    char = utf16_data[i:i+2].decode('utf-16-le', errors='strict')
                    # Keep printable ASCII, whitespace, and specific Unicode characters that might be parameter placeholders
                    if (32 <= ord(char) < 127 or char in '\r\n\t' or 
                        char == 'Ā'):  # U+0100 - corrupted parameter placeholder
                        text_parts.append(char)
                    i += 2
                except Exception as e:
                    logger.debug("Exception caught: %s", e)
                    # Skip invalid UTF-16 sequences
                    i += 2
            else:
                i += 1

        syntax = ''.join(text_parts)

        # Validate that we got DataWindow syntax
        if len(syntax) > 50 and ('PBSELECT' in syntax or 'release' in syntax):
            logger.debug(f"Successfully extracted {len(syntax)} characters of DataWindow syntax")
            return syntax

    except Exception as e:
        logger.debug(f"Error extracting UTF-16 DataWindow: {e}")

    return None


def _extract_datawindow_syntax(binary_data: bytes, object_name: str) -> Optional[str]:
    """Attempt to extract DataWindow syntax from binary data.

    Returns:
        Extracted syntax or None if extraction failed
    """
    # First try direct extraction by looking for PBSELECT patterns
    logger.debug(f"Attempting direct DataWindow extraction for {object_name}")

    # Look for PBSELECT in UTF-16 LE (most common)
    pbselect_utf16 = b'P\x00B\x00S\x00E\x00L\x00E\x00C\x00T\x00'
    utf16_pos = binary_data.find(pbselect_utf16)

    if utf16_pos >= 0:
        logger.debug(f"Found UTF-16 PBSELECT at offset 0x{utf16_pos:08X} in {object_name}")
        # Extract UTF-16 encoded DataWindow syntax
        syntax = _extract_utf16_syntax(binary_data, utf16_pos)
        if syntax:
            return syntax

    # Look for 'release' statement which starts DataWindow definitions
    release_utf16 = b'r\x00e\x00l\x00e\x00a\x00s\x00e\x00'
    release_pos = binary_data.find(release_utf16)

    if release_pos >= 0:
        logger.debug(f"Found UTF-16 'release' at offset 0x{release_pos:08X} in {object_name}")
        syntax = _extract_utf16_syntax(binary_data, release_pos)
        if syntax:
            return syntax

    # Try the original extraction methods as fallback
    try:
        # Try enhanced extraction first
        from src.decompile.extractors.enhanced_datawindow_integration import extraction_manager

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
        except Exception as e:
            logger.debug("DataWindow extraction failed: %s", e)
    except Exception as e:
        logger.debug("Enhanced DataWindow extraction failed: %s", e)

    return None


def _process_single_pbd(
    pe_file_handle, pe_file_path: Path, pbd_offset: int, is_unicode: bool, 
    output_base_dir: Path, pe_file_size: int, silent_progress: bool
) -> bool:
    """Process a single PBD found at given offset."""
    logger.info("Processing potential PBD at offset %s (unicode: %s).", pbd_offset, is_unicode)

    # Create output directory
    pbd_out_dir_name = f"{pe_file_path.stem}_offset_{pbd_offset}"
    pbd_output_path = output_base_dir / pe_file_path.name / pbd_out_dir_name
    pbd_output_path.mkdir(parents=True, exist_ok=True)

    # Carve PBD data
    pbd_data = _carve_pbd_data(pe_file_handle, pbd_offset, pe_file_size)
    if not pbd_data:
        return False

    # Create temp file and extract
    temp_file = None
    try:
        temp_file = _create_temp_pbd_file(pbd_data, pe_file_path.stem)
        logger.debug("Carved PBD data to temporary file %s.", temp_file)

        if _extract_pbd_from_temp_file(temp_file, pbd_output_path, silent_progress):
            logger.info("Successfully extracted PBD from offset %s.", pbd_offset)
            return True
        return False
    finally:
        _cleanup_temp_file(temp_file)


def _carve_pbd_data(pe_file_handle, pbd_offset: int, pe_file_size: int) -> Optional[bytes]:
    """Carve PBD data from PE file starting at given offset."""
    pe_file_handle.seek(pbd_offset)
    pbd_data_chunk = pe_file_handle.read(pe_file_size - pbd_offset)

    if not pbd_data_chunk:
        logger.warning("Could not read PBD data chunk at offset %s.", pbd_offset)
        return None

    return pbd_data_chunk


def _create_temp_pbd_file(pbd_data: bytes, pe_file_stem: str) -> Path:
    """Create temporary file with PBD data."""
    with tempfile.NamedTemporaryFile(
        delete=False, suffix=".pbd", prefix=f"embedded_{pe_file_stem}_",
    ) as tmp_file:
        tmp_file.write(pbd_data)
        return Path(tmp_file.name)


def _cleanup_temp_file(temp_file: Optional[Path]) -> None:
    """Clean up temporary file if it exists."""
    if temp_file and temp_file.exists():
        try:
            os.unlink(temp_file)
            logger.debug("Cleaned up temporary PBD file: %s", temp_file)
        except OSError as e:
            logger.exception("Error deleting temporary PBD file %s: %s", temp_file, e)


def _extract_pbd_from_temp_file(temp_file: Path, output_path: Path, silent_progress: bool) -> bool:
    """Extract PBD contents from temporary file."""
    from src.extract.pbd.exceptions import PbdError
    from src.extract.pbd.extraction.library import Library

    try:
        with Library(temp_file) as lib:
            logger.info("Successfully initialized Library (temp file: %s).", temp_file.name)
            logger.info("Found %s entries. Extracting to %s", len(lib), output_path)
            lib.extract_all(output_dir=output_path, silent_progress=silent_progress)
            return True
    except PbdError as e:
        logger.warning("Failed to process PBD data: %s", e)
        return False
    except Exception as e:
        logger.error("Unexpected error processing PBD data: %s", e, exc_info=True)
        return False


# ============================================================================
# Streaming Support Functions
# ============================================================================

class StreamingPBDReader:
    """Streaming reader for large PBD files."""

    def __init__(self, file_path: Union[str, Path], chunk_size: int = BUFFER_SIZE):
        self.file_path = Path(file_path)
        self.chunk_size = chunk_size
        self._reader: Optional[StreamReader] = None
        self._header = None
        self._entries = []

    def __enter__(self):
        self._reader = StreamReader(self.file_path, self.chunk_size)
        self._reader.__enter__()
        self._read_header()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        if self._reader:
            self._reader.__exit__(exc_type, exc_val, exc_tb)

    def _read_header(self):
        """Read PBD header without loading entire file."""
        from src.extract.pbd.structures.header import extract_pbl_header
        from io import BytesIO

        # Read header bytes (need more than just HEADER_SIZE for full header parsing)
        header_data = self._reader.read_at(0, 512)  # Standard block size
        
        # Use the existing header extraction function
        with BytesIO(header_data) as header_stream:
            self._header = extract_pbl_header(
                header_stream, 
                block_size=512, 
                file_path_for_error_log=str(self.file_path)
            )

    def iter_entries(self) -> Iterator["PbEntryDefinition"]:
        """Iterate over entries without loading all at once."""
        from src.extract.pbd.structures.node import extract_nod, NODE_BLOCK_SIZES_NON_UNICODE
        from src.extract.utils.binary import binary_to_int
        from io import BytesIO

        if not self._header:
            return

        # Start reading NOD blocks from first_nod_offset
        current_nod_offset = self._header.first_nod_offset
        processed_offsets = set()
        block_size = 512  # Standard block size

        while current_nod_offset != 0 and current_nod_offset not in processed_offsets:
            # Read NOD block
            nod_data = self._reader.read_at(current_nod_offset, block_size)
            
            # Create a file-like object for the node parser
            with BytesIO(nod_data) as nod_stream:
                # Seek to start and extract the node
                nod_stream.seek(0)
                node = extract_nod(
                    nod_stream, self._header.is_unicode, 0, block_size, processed_offsets
                )
                
                if node:
                    # Yield entries from this node
                    for entry in node.entries:
                        yield entry
                    
                    processed_offsets.add(current_nod_offset)
                    # Move to next NOD block
                    current_nod_offset = node.next_nod_offset
                else:
                    logger.warning(f"Failed to extract NOD at offset {current_nod_offset}")
                    break

    def extract_entry(self, entry: "PbEntryDefinition", output_path: Union[str, Path]):
        """Extract a single entry using streaming."""
        from src.extract.pbd.structures.data_block import extract_data_from_entry, DataClass
        from io import BytesIO
        
        # Get file size for data extraction
        file_size = self.file_path.stat().st_size
        block_size = 512  # Standard block size
        
        # Create a custom file-like object that reads from our StreamReader
        class StreamReaderWrapper:
            def __init__(self, stream_reader, file_size):
                self.stream_reader = stream_reader
                self.file_size = file_size
                self.position = 0
            
            def seek(self, offset, whence=0):
                if whence == 0:  # SEEK_SET
                    self.position = offset
                elif whence == 1:  # SEEK_CUR
                    self.position += offset
                elif whence == 2:  # SEEK_END
                    self.position = self.file_size + offset
                return self.position
            
            def tell(self):
                return self.position
            
            def read(self, size=-1):
                if size == -1:
                    size = self.file_size - self.position
                data = self.stream_reader.read_at(self.position, size)
                self.position += len(data)
                return data
        
        # Use the wrapper to extract data
        wrapper = StreamReaderWrapper(self._reader, file_size)
        data_blocks, is_partial = extract_data_from_entry(
            wrapper, entry, self._header.is_unicode, block_size, file_size
        )
        
        if is_partial:
            logger.warning(f"Partial data extraction for entry {entry.objectname}")

        # Save extracted data
        save_to_file(entry, data_blocks, output_path, self._header.is_unicode)

    def extract_all(self, output_path: Union[str, Path], progress_callback=None):
        """Extract all entries using streaming."""
        # First count total entries for progress
        entry_list = list(self.iter_entries())
        total_entries = len(entry_list)
        
        for idx, entry in enumerate(entry_list):
            self.extract_entry(entry, output_path)
            if progress_callback:
                progress_callback(idx + 1, total_entries)

        logger.info(f"Extracted {total_entries} entries using streaming")


class AsyncStreamingPBDReader:
    """Async streaming reader for large PBD files."""

    def __init__(self, file_path: Union[str, Path], chunk_size: int = BUFFER_SIZE):
        self.file_path = Path(file_path)
        self.chunk_size = chunk_size
        self._reader: Optional[AsyncStreamReader] = None
        self._header = None

    async def __aenter__(self):
        self._reader = AsyncStreamReader(self.file_path, self.chunk_size)
        await self._reader.__aenter__()
        await self._read_header()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self._reader:
            await self._reader.__aexit__(exc_type, exc_val, exc_tb)

    async def _read_header(self):
        """Read PBD header asynchronously."""
        from src.extract.pbd.structures.header import extract_pbl_header
        from io import BytesIO

        # Read header bytes
        header_data = await self._reader.read_at(0, 512)
        
        # Use the existing header extraction function
        with BytesIO(header_data) as header_stream:
            self._header = extract_pbl_header(
                header_stream, 
                block_size=512, 
                file_path_for_error_log=str(self.file_path)
            )

    async def iter_entries(self) -> AsyncIterator["PbEntryDefinition"]:
        """Async iterate over entries."""
        from src.extract.pbd.structures.entry import PbEntryDefinition

        if not self._header:
            return

        offset = HEADER_SIZE

        for _ in range(self._header.entry_count):
            # Read entry size
            size_data = await self._reader.read_at(offset, 4)
            if len(size_data) < 4:
                break

            entry_size = struct.unpack("<I", size_data)[0]

            # Read full entry
            entry_data = await self._reader.read_at(offset, entry_size)
            if len(entry_data) < entry_size:
                break

            try:
                entry = PbEntryDefinition.from_binary(entry_data)
                yield entry
                offset += entry_size
            except Exception as e:
                logger.error(f"Failed to parse entry at offset {offset}: {e}")
                break

    async def extract_entry(self, entry: "PbEntryDefinition", output_path: Union[str, Path]):
        """Extract a single entry asynchronously."""
        from src.extract.pbd.structures.data_block import DataClass

        data_blocks = []
        offset = entry.data_offset

        for _ in range(entry.block_count):
            # Read block header
            block_header = await self._reader.read_at(offset, 8)
            if len(block_header) < 8:
                break

            block_size, block_type = struct.unpack("<II", block_header)

            # Read block data
            block_data = await self._reader.read_at(offset + 8, block_size - 8)

            data_block = DataClass(
                address=offset,
                data=block_data,
                size=block_size,
                type=block_type
            )
            data_blocks.append(data_block)
            offset += block_size

        # Save in thread pool to avoid blocking
        await asyncio.get_event_loop().run_in_executor(
            None, save_to_file, entry, data_blocks, output_path, self._header.is_unicode
        )

    async def extract_all(self, output_path: Union[str, Path], progress_callback=None):
        """Extract all entries asynchronously."""
        total = 0
        async for entry in self.iter_entries():
            await self.extract_entry(entry, output_path)
            total += 1
            if progress_callback:
                await progress_callback(total, self._header.entry_count)

        logger.info(f"Extracted {total} entries using async streaming")


def stream_extract_pbd(
    pbd_path: Union[str, Path], 
    output_path: Union[str, Path],
    use_async: bool = False
) -> int:
    """Extract PBD using streaming for memory efficiency.

    Args:
        pbd_path: Path to PBD file
        output_path: Output directory
        use_async: Whether to use async extraction

    Returns:
        Number of entries extracted
    """
    if use_async:
        return asyncio.run(_async_stream_extract(pbd_path, output_path))
    else:
        with StreamingPBDReader(pbd_path) as reader:
            reader.extract_all(output_path)
            return reader._header.entry_count if reader._header else 0


async def _async_stream_extract(pbd_path: Union[str, Path], output_path: Union[str, Path]) -> int:
    """Async helper for streaming extraction."""
    async with AsyncStreamingPBDReader(pbd_path) as reader:
        await reader.extract_all(output_path)
        return reader._header.entry_count if reader._header else 0


# Alias for compatibility
PBDReader = StreamingPBDReader