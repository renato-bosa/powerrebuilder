import base64
import json
import logging
from pathlib import Path

# Import utilities from .binary_utils
from extract.pbd.utils.binary_utils import get_mime_type_from_data, safe_filename

logger = logging.getLogger(__name__)


def save_text_file(obj_name: str, text: str, output_path: str | Path) -> None:
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
    with open(file_to_open, "w", encoding="utf-8") as output:
        output.write(f"HA$PBExportHeader${obj_name}\n")  # Use original name in header
        output.write("$PBExportComments$\n")
        output.write(text)
    logger.debug("Saved text file: %s", file_to_open)


def save_pcode_file(obj_name: str, data: bytes, output_path: str | Path) -> None:
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
    with open(file_to_open, "wb") as output:
        if pcode_name.lower().endswith(".fun"):
            # Add PowerBuilder export header for .fun files
            header = f"HA$PBExportHeader${obj_name}\n$PBExportComments$\n".encode()
            output.write(header)
        output.write(data)
    logger.debug("Saved pcode file: %s", file_to_open)


def save_binary_file(name: str, data: bytes, output_path: str | Path) -> None:
    data_folder = Path(output_path) / "resources"
    data_folder.mkdir(parents=True, exist_ok=True)
    file_to_open = data_folder / name
    with open(file_to_open, "wb") as output:
        output.write(data)
    meta_file = data_folder / f"{name}.meta.json"
    metadata = {
        "original_name": name,
        "size_bytes": len(data),
        "mime_type": get_mime_type_from_data(data),
        "extraction_date": str(Path(file_to_open).stat().st_mtime),
    }
    with open(meta_file, "w", encoding="utf-8") as meta_output:
        json.dump(metadata, meta_output, indent=2)
    logging.info("Saved binary resource: %s (%s bytes)", name, len(data))


def save_binary_as_base64(name: str, data: bytes, output_path: str | Path) -> None:
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
    with open(json_file, "w", encoding="utf-8") as output:
        json.dump(json_data, output)
    logging.info("Saved base64 resource: %s (%s chars)", name, len(base64_data))


# Avoiding circular imports - using TYPE_CHECKING
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from extract.pbd.structures.data_block import DataClass
    from extract.pbd.structures.entry import PbEntryDefinition

from common.object_type_detector import ObjectTypeDetector
from extract.pbd.constants import SOURCE_EXTENSIONS
from extract.pbd.formatters import DataWindowFormatter


def _get_object_type_info(entry_name: str) -> tuple[str, bool, bool, bool]:
    """Get object type information.
    
    Returns:
        Tuple of (obj_type_name, contains_pcode, is_datawindow, is_structure)
    """
    obj_type_name, contains_pcode = ObjectTypeDetector.get_object_info(entry_name)
    is_datawindow = ObjectTypeDetector.is_datawindow(entry_name)
    is_structure = ObjectTypeDetector.is_structure(entry_name)
    return obj_type_name, contains_pcode, is_datawindow, is_structure


def _extract_datawindow_syntax(binary_data: bytes, object_name: str) -> str | None:
    """Attempt to extract DataWindow syntax from binary data.
    
    Returns:
        Extracted syntax or None if extraction failed
    """
    try:
        # Try enhanced extraction first
        from decompile.analysis.enhanced_datawindow_integration import (
            extraction_manager,
        )

        syntax, success = extraction_manager.extract_from_pbd_object(
            binary_data, object_name
        )
        return syntax if success else None
    except ImportError:
        # Fallback to standard extraction
        try:
            from decompile.analysis.datawindow_extractor import (
                extract_datawindow_from_pbd,
            )

            return extract_datawindow_from_pbd(binary_data, object_name)
        except ImportError:
            logger.debug("DataWindow extractor not available - saving raw data")
        except Exception as e:
            logger.debug("DataWindow extraction failed: %s", e)
    except Exception as e:
        logger.debug("Enhanced DataWindow extraction failed: %s", e)
    
    return None


def _process_datawindow(
    entry: "PbEntryDefinition",
    data: list["DataClass"],
    output_path: str | Path,
) -> None:
    """Process and save DataWindow object."""
    logger.debug("Processing DataWindow object: %s", entry.objectname)
    
    # Use the function that preserves DAT* headers for DataWindow extraction
    from extract.pbd.structures.data_block import get_binary_with_dat_headers, get_binary_from_data

    binary_data: bytes = get_binary_with_dat_headers(data)

    # Try to extract DataWindow syntax
    syntax = _extract_datawindow_syntax(binary_data, entry.objectname)

    if syntax:
        # Use DataWindow formatter to save properly formatted files
        safe_name = safe_filename(entry.objectname)
        output_path_obj = Path(output_path)
        output_path_obj.mkdir(parents=True, exist_ok=True)

        # Save formatted DataWindow and SQL files
        main_file, sql_file = DataWindowFormatter.save_formatted_datawindow(
            safe_name, syntax, output_path_obj, save_sql=True
        )
    else:
        # Could not extract syntax - save raw binary data
        save_binary_file(entry.objectname, get_binary_from_data(data), output_path)
        logger.warning(
            f"Could not extract DataWindow syntax from {entry.objectname}, saved as binary"
        )


def _process_structure(
    entry: "PbEntryDefinition",
    data: list["DataClass"],
    output_path: str | Path,
    is_unicode: bool,
) -> None:
    """Process and save Structure object."""
    from extract.pbd.structures.data_block import get_text_from_data
    
    logger.debug("Processing Structure object: %s", entry.objectname)
    text: str = get_text_from_data(data, is_unicode)
    comment_len: int = entry.commentlen
    text_content_after_comment = text[comment_len:]

    # Save structure definition as text
    safe_name = safe_filename(entry.objectname)
    output_path_obj = Path(output_path)
    output_path_obj.mkdir(parents=True, exist_ok=True)
    struct_file = output_path_obj / safe_name

    with open(struct_file, "w", encoding="utf-8") as output:
        output.write(f"HA$PBExportHeader${entry.objectname}\n")
        output.write("$PBExportComments$\n")
        output.write(text_content_after_comment)
    logger.info("Saved Structure definition to: %s", struct_file)


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
        logger.info(
            f"Skipping text file creation for binary file: {entry_name}"
        )
        return True
    elif is_structure:
        # Structures (.str) might have text definitions we want to preserve
        return False
    
    return False


def _process_pcode(
    entry: "PbEntryDefinition",
    data: list["DataClass"],
    output_path: str | Path,
) -> None:
    """Process and save P-code object."""
    from extract.pbd.structures.data_block import get_binary_from_data
    
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


def save_to_file(
    entry: "PbEntryDefinition",
    data: list["DataClass"],
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
    from extract.pbd.structures.data_block import (
        get_text_from_data,
    )

    # Get object type information
    obj_type_name, contains_pcode, is_datawindow, is_structure = _get_object_type_info(
        entry.objectname
    )

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
