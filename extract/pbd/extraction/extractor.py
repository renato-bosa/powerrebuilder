
import logging
import time
from pathlib import Path
from typing import BinaryIO

from extract.pbd.constants import BLOCK_SIZE as DEFAULT_BLOCK_SIZE
from extract.pbd.exceptions import DataExtractionError, PbdError, HeaderError
from extract.pbd.io.file_operations import save_to_file

# import traceback # No longer needed directly
from extract.pbd.io.progress import TqdmProgressTracker
from extract.pbd.structures.data_block import extract_data_from_entry
from extract.pbd.structures.header import HeaderClass, extract_pbl_header
from extract.pbd.structures.node import extract_nods

logger: logging.Logger = logging.getLogger(__name__)


def extract_pbl_info(
    f: str | Path, unicode_from_header_obj: bool, first_nod_offset_from_header: int, block_size: int, ) -> dict:





    pbl_info: dict = {}
    # Header is assumed to be parsed by the caller and its info passed in
    # pbl_info["header"] = header_obj # No longer store full header, just use its results
    pbl_info["nods"] = extract_nods(
        f, unicode_from_header_obj, first_nod_offset_from_header, block_size,
    )
    return pbl_info


def _get_log_file_name(file_content: str | Path | bytes, file_name_for_logging: str | None) -> str:








    """Determine the file name for logging."""
    if isinstance(file_content, str | Path):
        return Path(file_content).name
    elif file_name_for_logging:
        return file_name_for_logging
    else:
        return "UnknownFile"


def _setup_output_directory(output_path: str, file_content: str | Path | bytes, log_file_name: str) -> Path:








    """Setup and return the output directory path."""
    output_file_path_base = Path(output_path)

    if output_file_path_base.is_dir():
        if isinstance(file_content, str | Path) and Path(file_content).is_file():
            pbd_specific_out_dir = output_file_path_base / Path(file_content).name
            pbd_specific_out_dir.mkdir(parents=True, exist_ok=True)
            return pbd_specific_out_dir
        elif log_file_name != "UnknownFile":
            pbd_specific_out_dir = output_file_path_base / log_file_name
            pbd_specific_out_dir.mkdir(parents=True, exist_ok=True)
            return pbd_specific_out_dir

    return output_file_path_base


def _validate_entry(entry_def_obj, log_file_name: str) -> bool:
    """Validate entry definition object.
    
    Returns:
        True if valid, False otherwise
    """
    if not entry_def_obj:
        logger.warning("Entry definition is None in %s", log_file_name)
        return False
        
    if not hasattr(entry_def_obj, 'objectname'):
        logger.warning("Entry definition missing objectname in %s", log_file_name)
        return False
        
    if not hasattr(entry_def_obj, 'offset'):
        logger.warning("Entry definition missing offset for %s in %s", 
                      entry_def_obj.objectname, log_file_name)
        return False
        
    return True

def _get_resource_manager(output_path: Path, header: HeaderClass) -> None:







    """Get or create resource manager if resource extraction is enabled."""
    if not hasattr(header, "extract_resources") or not header.extract_resources:
        return None

    if not hasattr(_extract_pbl_logic, "_resource_manager"):
        from extract.pbd.extraction.resource_extraction_manager import (
            ResourceExtractionManager,
        )
        _extract_pbl_logic._resource_manager = ResourceExtractionManager(output_path)

    return _extract_pbl_logic._resource_manager


def _process_entry(entry_def_obj, file_content, header: HeaderClass, output_path: Path, log_file_name: str, block_size: int) -> tuple:







    """Process a single entry definition with enhanced validation and error recovery.

    Returns:
        Tuple of (success: bool, data: bytes)
    """
    start_time = time.time()
    
    # Validate entry
    if not _validate_entry(entry_def_obj, log_file_name):
        return False, b''
    
    # Get file size from header with validation
    file_size = header.file_size if header.file_size is not None else 0
    if file_size == 0:
        logger.warning(
            "File size not available in header for %s. Data extraction may fail.", 
            log_file_name
        )
    elif file_size < 0:
        logger.error("Invalid negative file size %d in header for %s", 
                    file_size, log_file_name)
        return False, b''

    try:
        # Extract data with retry mechanism
        max_retries = 3
        data = None
        is_partial = False
        
        for attempt in range(max_retries):
            try:
                data, is_partial = extract_data_from_entry(
                    file_content, entry_def_obj, header.is_unicode, block_size, file_size
                )
                break  # Success
            except (DataExtractionError, PbdError) as e:
                if attempt == max_retries - 1:
                    raise  # Last attempt, re-raise the exception
                logger.warning(
                    "Attempt %d failed for %s in %s: %s. Retrying...", 
                    attempt + 1, entry_def_obj.objectname, log_file_name, e
                )
                time.sleep(0.1)  # Brief delay before retry

        if data is None:
            logger.error("Failed to extract data for %s in %s after %d attempts", 
                        entry_def_obj.objectname, log_file_name, max_retries)
            return False, b''
        
        # Convert data blocks to bytes if needed
        if isinstance(data, list) and data and hasattr(data[0], 'data'):
            # data is a list of DataClass objects, concatenate their data
            data_bytes = b''.join(block.data for block in data)
        else:
            # data is already bytes
            data_bytes = data

        if is_partial:
            logger.warning(
                "Data extraction for %s in %s was partial (truncated or corrupted).",
                entry_def_obj.objectname, log_file_name
            )

        # Validate extracted data
        if len(data_bytes) == 0:
            logger.warning("Extracted empty data for %s in %s", 
                          entry_def_obj.objectname, log_file_name)
        elif len(data_bytes) > 100 * 1024 * 1024:  # 100MB warning threshold
            logger.warning("Extracted unusually large data (%d bytes) for %s in %s", 
                          len(data_bytes), entry_def_obj.objectname, log_file_name)

        # Save to file with error handling
        try:
            save_to_file(entry_def_obj, data_bytes, output_path, header.is_unicode)
        except Exception as save_error:
            logger.error("Failed to save %s in %s: %s", 
                        entry_def_obj.objectname, log_file_name, save_error)
            return False, data_bytes  # Return data even if save failed

        # Log timing for performance monitoring
        elapsed = time.time() - start_time
        if elapsed > 5.0:  # Log slow extractions
            logger.info("Slow extraction: %s in %s took %.2f seconds", 
                       entry_def_obj.objectname, log_file_name, elapsed)

        return True, data_bytes

    except Exception as e:
        logger.error("Unexpected error processing %s in %s: %s", 
                    entry_def_obj.objectname, log_file_name, e, exc_info=True)
        return False, b''


def _extract_resources_from_entry(data: bytes, entry_def_obj, log_file_name: str, resource_manager) -> None:







    """Extract resources from entry data if resource manager is available."""
    if not resource_manager:
        return

    object_name = str(entry_def_obj.objectname)
    object_type = object_name.split(".")[-1] if "." in object_name else "unknown"

    resource_manager.extract_from_object(
        data, log_file_name, object_name, object_type,
    )


def _process_all_entries(nodes, file_content, header: HeaderClass, output_path: Path, log_file_name: str, block_size: int, progress) -> None:







    """Process all entries from all nodes.

    Returns:
        Tuple of (extracted_count, failed_count)
    """
    extracted_count = 0
    failed_count = 0
    resource_manager = _get_resource_manager(output_path, header)

    for node in nodes:
        if not node or not hasattr(node, "entry_defs") or not node.entry_defs:
            continue

        for entry_def_obj in node.entry_defs:
            if not entry_def_obj:
                logger.warning("Skipping None entry in node from %s.", log_file_name)
                continue

            try:
                if progress:
                    progress.update(
                        extracted_count + failed_count, item_name=str(entry_def_obj.objectname), )

                # Process the entry
                success, data = _process_entry(
                    entry_def_obj, file_content, header, output_path, log_file_name, block_size,
                )

                if success:
                    extracted_count += 1
                    # Extract resources if enabled
                    _extract_resources_from_entry(
                        data, entry_def_obj, log_file_name, resource_manager,
                    )

            except (PbdError, DataExtractionError) as pbd_e:
                failed_count += 1
                logger.exception(
                    f"PBD Extraction error for {entry_def_obj.objectname} in {log_file_name}: {pbd_e}",
                )
            except Exception as e:
                failed_count += 1
                logger.error(
                    f"Unexpected error processing entry {entry_def_obj.objectname} in {log_file_name}: {e}", exc_info=True, )

    return extracted_count, failed_count


def _validate_extraction_parameters(file_content, header: HeaderClass, output_path: str, log_file_name: str) -> bool:
    """Validate extraction parameters before starting extraction."""
    if not header:
        logger.error("Header is None for %s", log_file_name)
        return False
        
    if not hasattr(header, 'is_unicode'):
        logger.error("Header missing is_unicode property for %s", log_file_name)
        return False
        
    if not hasattr(header, 'first_nod_offset'):
        logger.error("Header missing first_nod_offset property for %s", log_file_name)
        return False
        
    if header.first_nod_offset < 0:
        logger.error("Invalid negative first_nod_offset %d for %s", 
                    header.first_nod_offset, log_file_name)
        return False
        
    if not output_path:
        logger.error("Output path is empty for %s", log_file_name)
        return False
        
    return True

def _extract_pbl_logic(
    file_content: str | Path | bytes, header: HeaderClass, output_path: str, show_progress: bool = True, file_name_for_logging: str | None = None, ) -> None:








    """Core logic for PBL extraction with enhanced error handling and monitoring.
    Accepts file content (path or bytes), a parsed header, and output path.
    """
    extraction_start_time = time.time()
    
    # Setup basic extraction parameters
    log_file_name = _get_log_file_name(file_content, file_name_for_logging)
    
    # Validate parameters
    if not _validate_extraction_parameters(file_content, header, output_path, log_file_name):
        logger.error("Parameter validation failed for %s", log_file_name)
        return
    
    block_size = getattr(header, "effective_block_size", DEFAULT_BLOCK_SIZE)
    
    # Validate block size
    if block_size <= 0 or block_size > 1024 * 1024:  # Max 1MB block size
        logger.warning("Unusual block size %d for %s, using default", block_size, log_file_name)
        block_size = DEFAULT_BLOCK_SIZE
    
    output_file_path_base = _setup_output_directory(output_path, file_content, log_file_name)

    logger.info(
        "Extracting %s (unicode=%s, block_size=%d) to %s",
        log_file_name, header.is_unicode, block_size, output_file_path_base
    )

    try:
        # Extract nodes with validation
        nodes = extract_nods(
            file_content, header.is_unicode, header.first_nod_offset, block_size,
        )
        
        if not nodes:
            logger.warning("No nodes found in %s", log_file_name)
            return

        # Validate nodes
        valid_nodes = []
        for node in nodes:
            if node and hasattr(node, "entry_defs") and node.entry_defs:
                valid_nodes.append(node)
            elif node:
                logger.debug("Node without entry_defs found in %s", log_file_name)
                
        if not valid_nodes:
            logger.warning("No valid nodes with entries found in %s", log_file_name)
            return

        # Setup progress tracking
        total_entries = sum(
            getattr(node, "numberofentries", len(node.entry_defs) if hasattr(node, "entry_defs") else 0)
            for node in valid_nodes
        )

        if total_entries == 0:
            logger.warning("No entries found in nodes for %s", log_file_name)
            return

        progress = None
        if show_progress and total_entries > 0:
            progress = TqdmProgressTracker(
                total=total_entries, description=f"Extracting {log_file_name}", unit="entries"
            )

        # Process all entries with enhanced error handling
        extracted_count, failed_count = _process_all_entries(
            valid_nodes, file_content, header, output_file_path_base, log_file_name, block_size, progress,
        )

        if progress:
            progress.finish()

        # Generate resource reports if resources were extracted
        if hasattr(header, "extract_resources") and header.extract_resources:
            if hasattr(_extract_pbl_logic, "_resource_manager"):
                try:
                    _extract_pbl_logic._resource_manager.generate_comprehensive_report()
                except Exception as report_error:
                    logger.error("Failed to generate resource report for %s: %s", 
                               log_file_name, report_error)
                finally:
                    delattr(_extract_pbl_logic, "_resource_manager")

        # Log extraction statistics
        extraction_time = time.time() - extraction_start_time
        success_rate = (extracted_count / (extracted_count + failed_count)) * 100 if (extracted_count + failed_count) > 0 else 0
        
        logger.info(
            "Finished extraction for %s: %d succeeded, %d failed (%.1f%% success rate) in %.2f seconds",
            log_file_name, extracted_count, failed_count, success_rate, extraction_time
        )
        
    except Exception as extraction_error:
        logger.error("Critical error during extraction of %s: %s", 
                    log_file_name, extraction_error, exc_info=True)
        raise


def extract_pbl(f: str | Path, output_path: str, show_progress: bool = True, extract_resources: bool = True) -> None:








    """Extracts entries from a PBD/PBL file.
    Opens the file, parses the header, and then calls the core extraction logic, passing the open file handle.
    """
    file_path = Path(f)
    log_file_name = file_path.name  # For consistent logging

    try:
        with open(file_path, "rb") as pbd_file_handle:
            logger.debug(
                f"Attempting to extract header for {log_file_name} using open file handle.",
            )
            # extract_pbl_header now expects BinaryIO or bytes.
            # We pass the handle and the file_path for logging context.
            header = extract_pbl_header(
                pbd_file_handle, block_size=DEFAULT_BLOCK_SIZE, file_path_for_error_log=str(file_path), )

            logger.debug(
                f"Header extracted for {log_file_name}: unicode={header.is_unicode}, nod_offset={header.first_nod_offset}, file_size={header.file_size}",
            )

            # Add resource extraction flag to header
            header.extract_resources = extract_resources

            # Pass the open file_handle (pbd_file_handle) to _extract_pbl_logic
            # _extract_pbl_logic will use this handle for all subsequent reads.
            _extract_pbl_logic(
                pbd_file_handle, header, output_path, show_progress, file_name_for_logging=log_file_name, )

    except FileNotFoundError:
        logger.exception("File not found: %s", file_path)
        raise  # Re-raise to be handled by the caller or higher-level error handling
    except PbdError as pbd_e_outer:
        logger.error(
            f"Failed to extract {log_file_name} due to PBD parsing error: {pbd_e_outer}", exc_info=True, )
        # logger.error("FULL TRACEBACK (PBD Error):\n" + traceback.format_exc()) # Replaced by exc_info
        raise
    except Exception as e_outer:
        logger.error(
            f"Failed to extract {log_file_name} due to an unexpected error: {e_outer}", exc_info=True, )
        # logger.error("FULL TRACEBACK (Unexpected Error):\n" + traceback.format_exc()) # Replaced by exc_info
        raise
