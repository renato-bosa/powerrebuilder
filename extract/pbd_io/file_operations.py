import base64
import json
import logging
import re
import unicodedata
from pathlib import Path

# Assuming get_mime_type_from_data and SOURCE_EXTENSIONS, RESOURCE_EXTENSIONS are in .utils
from .utils import get_mime_type_from_data

logger = logging.getLogger(__name__)


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
    else:
        # .sru, .srw, etc.
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

# save_to_file depends on PbEntryDefinition and DataClass from pbd_core
# and get_text_from_data from pbd_core.dat
# This suggests a tight coupling or a need to pass more primitive types
# For now, we will keep it in core or pass necessary components to it.
# Moving save_to_file would require significant refactoring or passing PbEntryDefinition, DataClass, get_text_from_data
# Or, it calls these new file_operations functions.
