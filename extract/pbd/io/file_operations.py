import base64
import json
import logging
from pathlib import Path

# Import utilities from .binary_utils
from ..utils.binary_utils import get_mime_type_from_data, safe_filename

logger = logging.getLogger(__name__)


def save_text_file(obj_name: str, text: str, output_path: str | Path) -> None:
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
    logger.debug(f"Saved text file: {file_to_open}")


def save_pcode_file(obj_name: str, text: str, output_path: str | Path) -> None:
    # Sanitize the base filename
    safe_base = safe_filename(obj_name)

    # Create pcode filename
    if safe_base.lower().endswith(".srf"):
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

    # Write the file
    with open(file_to_open, "w", encoding="utf-8") as output:
        output.write(text)
    logger.debug(f"Saved pcode file: {file_to_open}")


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
    logging.info(f"Saved binary resource: {name} ({len(data)} bytes)")


def save_binary_as_base64(name: str, data: bytes, output_path: str | Path) -> None:
    data_folder = Path(output_path) / "resources_base64"
    data_folder.mkdir(parents=True, exist_ok=True)
    base64_data = base64.b64encode(data).decode('ascii')
    json_data = {
        "original_name": name,
        "mime_type": get_mime_type_from_data(data),
        "encoding": "base64",
        "data": base64_data,
    }
    json_file = data_folder / f"{Path(name).stem}.json"
    with open(json_file, "w", encoding="utf-8") as output:
        json.dump(json_data, output)
    logging.info(f"Saved base64 resource: {name} ({len(base64_data)} chars)")

# Avoiding circular imports - using TYPE_CHECKING
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from ..structures.entry import PbEntryDefinition
    from ..structures.data_block import DataClass

from ..constants import SOURCE_EXTENSIONS


def save_to_file(entry: 'PbEntryDefinition', data: list['DataClass'], output_path: str | Path, is_unicode: bool = False) -> None:
    """Save extracted entry data to file(s) based on entry type.
    
    Args:
        entry: Entry definition with metadata
        data: List of data blocks
        output_path: Directory to save files to
        is_unicode: Whether the data is Unicode encoded
    """
    # Import here to avoid circular dependency
    from ..structures.data_block import get_text_from_data
    
    text: str = get_text_from_data(data, is_unicode)
    comment_len: int = entry.commentlen

    is_potential_pcode: bool = entry.objectname.lower().endswith(tuple(SOURCE_EXTENSIONS))

    if is_potential_pcode:
        logger.debug(f"PCODE_SAVE_INFO: Entry='{entry.objectname}', Version='{entry.version}'")
        logger.debug(f"PCODE_SAVE_INFO:   entry.objectsize: {entry.objectsize}")
        logger.debug(f"PCODE_SAVE_INFO:   entry.commentlen: {entry.commentlen}")
        logger.debug(f"PCODE_SAVE_INFO:   len(text) (total before strip): {len(text)}")

    text_content_after_comment = text[comment_len:]

    if is_potential_pcode:
        logger.debug(f"PCODE_SAVE_INFO:   len(text_content_after_comment): {len(text_content_after_comment)}")
        if len(text_content_after_comment) > 0 and len(text_content_after_comment) < 200:
             logger.debug(f"PCODE_SAVE_INFO:   Content preview: '{text_content_after_comment[:100]}'")

    save_text_file(entry.objectname, text_content_after_comment, output_path)

    if is_potential_pcode:
        content_for_fun_file = text_content_after_comment
        if entry.objectname.lower().endswith(".srf") and "pfcasads" in entry.version.lower():
            logger.info(f"PCODE_SAVE_INFO: Special SRF/pfcasads '{entry.objectname}'. Using full DAT content.")
            content_for_fun_file = text
        save_pcode_file(entry.objectname, content_for_fun_file, output_path)
