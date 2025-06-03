import logging
from pathlib import Path

from extract.pbd_core.dat import (
    DataClass,
    extract_data_from_entry,
    get_text_from_data,
)
from extract.pbd_core.entry import PbEntryDefinition
from extract.pbd_core.exceptions import DataExtractionError, PbdError
from extract.pbd_core.header import HeaderClass, extract_pbl_header
from extract.pbd_core.node import extract_nods
from extract.pbd_io.file_operations import (
    save_pcode_file,
    save_text_file,
)

# import traceback # No longer needed directly
from extract.pbd_io.progress import TqdmProgressTracker
from extract.pbd_io.utils import (
    BLOCK_SIZE as DEFAULT_BLOCK_SIZE,
)
from extract.pbd_io.utils import (
    SOURCE_EXTENSIONS,
)

logger: logging.Logger = logging.getLogger(__name__)


def save_to_file(entry: PbEntryDefinition, data: list[DataClass], output_path: str | Path, is_unicode: bool = False) -> None:
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


def extract_pbl_info(f: str | Path, unicode_from_header_obj: bool, first_nod_offset_from_header: int, block_size: int) -> dict:
    pbl_info: dict = {}
    # Header is assumed to be parsed by the caller and its info passed in
    # pbl_info["header"] = header_obj # No longer store full header, just use its results
    pbl_info["nods"] = extract_nods(f, unicode_from_header_obj, first_nod_offset_from_header, block_size)
    return pbl_info


def _extract_pbl_logic(
    file_content: str | Path | bytes,
    header: HeaderClass,
    output_path: str,
    show_progress: bool = True,
    file_name_for_logging: str | None = None,
) -> None:
    """Core logic for PBL extraction.
    Accepts file content (path or bytes), a parsed header, and output path.
    """
    is_unicode_from_header = header.is_unicode
    first_nod_offset_from_header = header.first_nod_offset

    # Determine the file name for logging and output directory creation
    if isinstance(file_content, str | Path):
        log_file_name = Path(file_content).name
    elif file_name_for_logging:
        log_file_name = file_name_for_logging
    else:
        log_file_name = "UnknownFile"  # Fallback, should ideally be provided

    # Get block size from header if available, otherwise use default
    block_size = getattr(header, 'effective_block_size', DEFAULT_BLOCK_SIZE)

    nodes = extract_nods(file_content, is_unicode_from_header, first_nod_offset_from_header, block_size)
    total_entries = sum(node.numberofentries for node in nodes if node and hasattr(node, 'numberofentries'))

    output_file_path_base = Path(output_path)

    # Adjust output path if input is a file and output_path is a directory
    # This logic is slightly different because we might be working with bytes
    if output_file_path_base.is_dir():
        if isinstance(file_content, str | Path) and Path(file_content).is_file():
            pbd_specific_out_dir = output_file_path_base / Path(file_content).name
            pbd_specific_out_dir.mkdir(parents=True, exist_ok=True)
            output_file_path_base = pbd_specific_out_dir
        elif file_name_for_logging:  # If we have bytes, use the provided file_name_for_logging
            pbd_specific_out_dir = output_file_path_base / log_file_name
            pbd_specific_out_dir.mkdir(parents=True, exist_ok=True)
            output_file_path_base = pbd_specific_out_dir
    # If output_path itself is intended to be the PBD-specific dir (e.g. output/extracted_legacy_test/dcm.pbd)
    # then output_file_path_base is already correct or will be made so by the caller of extract_pbl

    logger.info(f"Extracting {log_file_name} (unicode={is_unicode_from_header}) to {output_file_path_base}")

    progress = None
    if show_progress and total_entries > 0:
        progress = TqdmProgressTracker(
            total=total_entries,
            description=f"Extracting {log_file_name}",
            unit="entries",
        )

    extracted_count = 0
    failed_count = 0

    for node in nodes:
        if node and hasattr(node, 'entry_defs') and node.entry_defs:
            for entry_def_obj in node.entry_defs:  # Renamed to avoid conflict with module name
                if entry_def_obj:
                    try:
                        if progress:
                            progress.update(extracted_count + failed_count, item_name=str(entry_def_obj.objectname))

                        # Get file size from header
                        file_size = header.file_size if header.file_size is not None else 0
                        if file_size == 0:
                            logger.warning(f"File size not available in header for {log_file_name}. Data extraction may fail.")

                        data, is_partial = extract_data_from_entry(file_content, entry_def_obj, is_unicode_from_header, block_size, file_size)
                        if is_partial:
                            logger.warning(f"Data extraction for {entry_def_obj.objectname} in {log_file_name} was partial (truncated or corrupted).")
                        save_to_file(entry_def_obj, data, output_file_path_base, is_unicode_from_header)
                        extracted_count += 1
                    except (PbdError, DataExtractionError) as pbd_e:
                        failed_count += 1
                        logger.error(f"PBD Extraction error for {entry_def_obj.objectname if entry_def_obj else 'Unknown Entry'} in {log_file_name}: {pbd_e}")
                    except Exception as e:
                        failed_count += 1
                        logger.error(f"Unexpected error processing entry {entry_def_obj.objectname if entry_def_obj else 'Unknown Entry'} in {log_file_name}: {e}", exc_info=True)
                else:
                    logger.warning(f"Skipping None entry in node from {log_file_name}.")

    if progress:
        progress.finish()
    logger.info(f"Finished extraction for {log_file_name}: {extracted_count} succeeded, {failed_count} failed.")


def extract_pbl(f: str | Path, output_path: str, show_progress: bool = True) -> None:
    """Extracts entries from a PBD/PBL file.
    Opens the file, parses the header, and then calls the core extraction logic,
    passing the open file handle.
    """
    file_path = Path(f)
    log_file_name = file_path.name  # For consistent logging

    try:
        with open(file_path, 'rb') as pbd_file_handle:
            logger.debug(f"Attempting to extract header for {log_file_name} using open file handle.")
            # extract_pbl_header now expects BinaryIO or bytes.
            # We pass the handle and the file_path for logging context.
            header = extract_pbl_header(pbd_file_handle, block_size=DEFAULT_BLOCK_SIZE, file_path_for_error_log=str(file_path))

            logger.debug(f"Header extracted for {log_file_name}: unicode={header.is_unicode}, nod_offset={header.first_nod_offset}, file_size={header.file_size}")

            # Pass the open file_handle (pbd_file_handle) to _extract_pbl_logic
            # _extract_pbl_logic will use this handle for all subsequent reads.
            _extract_pbl_logic(pbd_file_handle, header, output_path, show_progress, file_name_for_logging=log_file_name)

    except FileNotFoundError:
        logger.error(f"File not found: {file_path}")
        raise  # Re-raise to be handled by the caller or higher-level error handling
    except PbdError as pbd_e_outer:
        logger.error(f"Failed to extract {log_file_name} due to PBD parsing error: {pbd_e_outer}", exc_info=True)
        # logger.error("FULL TRACEBACK (PBD Error):\n" + traceback.format_exc()) # Replaced by exc_info
        raise
    except Exception as e_outer:
        logger.error(f"Failed to extract {log_file_name} due to an unexpected error: {e_outer}", exc_info=True)
        # logger.error("FULL TRACEBACK (Unexpected Error):\n" + traceback.format_exc()) # Replaced by exc_info
        raise
