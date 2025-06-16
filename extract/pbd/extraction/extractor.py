import logging
from pathlib import Path

from extract.pbd.constants import BLOCK_SIZE as DEFAULT_BLOCK_SIZE
from extract.pbd.exceptions import DataExtractionError, PbdError
from extract.pbd.io.file_operations import save_to_file

# import traceback # No longer needed directly
from extract.pbd.io.progress import TqdmProgressTracker
from extract.pbd.structures.data_block import extract_data_from_entry
from extract.pbd.structures.header import HeaderClass, extract_pbl_header
from extract.pbd.structures.node import extract_nods

logger: logging.Logger = logging.getLogger(__name__)


def extract_pbl_info(
    f: str | Path,
    unicode_from_header_obj: bool,
    first_nod_offset_from_header: int,
    block_size: int,
) -> dict:
    pbl_info: dict = {}
    # Header is assumed to be parsed by the caller and its info passed in
    # pbl_info["header"] = header_obj # No longer store full header, just use its results
    pbl_info["nods"] = extract_nods(
        f, unicode_from_header_obj, first_nod_offset_from_header, block_size
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


def _setup_output_directory(output_path: str, file_content: str | Path | bytes, 
                           log_file_name: str) -> Path:
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


def _get_resource_manager(output_path: Path, header: HeaderClass):
    """Get or create resource manager if resource extraction is enabled."""
    if not hasattr(header, 'extract_resources') or not header.extract_resources:
        return None
        
    if not hasattr(_extract_pbl_logic, '_resource_manager'):
        from extract.pbd.extraction.resource_extraction_manager import ResourceExtractionManager
        _extract_pbl_logic._resource_manager = ResourceExtractionManager(output_path)
    
    return _extract_pbl_logic._resource_manager


def _process_entry(entry_def_obj, file_content, header: HeaderClass, 
                  output_path: Path, log_file_name: str, block_size: int):
    """Process a single entry definition.
    
    Returns:
        Tuple of (success: bool, data: bytes)
    """
    # Get file size from header
    file_size = header.file_size if header.file_size is not None else 0
    if file_size == 0:
        logger.warning(
            f"File size not available in header for {log_file_name}. Data extraction may fail."
        )
    
    # Extract data
    data, is_partial = extract_data_from_entry(
        file_content,
        entry_def_obj,
        header.is_unicode,
        block_size,
        file_size,
    )
    
    if is_partial:
        logger.warning(
            f"Data extraction for {entry_def_obj.objectname} in {log_file_name} was partial (truncated or corrupted)."
        )
    
    # Save to file
    save_to_file(
        entry_def_obj,
        data,
        output_path,
        header.is_unicode,
    )
    
    return True, data


def _extract_resources_from_entry(data: bytes, entry_def_obj, log_file_name: str, 
                                 resource_manager):
    """Extract resources from entry data if resource manager is available."""
    if not resource_manager:
        return
        
    object_name = str(entry_def_obj.objectname)
    object_type = object_name.split('.')[-1] if '.' in object_name else 'unknown'
    
    resource_manager.extract_from_object(
        data,
        log_file_name,
        object_name,
        object_type
    )


def _process_all_entries(nodes, file_content, header: HeaderClass, output_path: Path,
                        log_file_name: str, block_size: int, progress):
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
                logger.warning(f"Skipping None entry in node from {log_file_name}.")
                continue
                
            try:
                if progress:
                    progress.update(
                        extracted_count + failed_count,
                        item_name=str(entry_def_obj.objectname),
                    )
                
                # Process the entry
                success, data = _process_entry(
                    entry_def_obj, file_content, header, 
                    output_path, log_file_name, block_size
                )
                
                if success:
                    extracted_count += 1
                    # Extract resources if enabled
                    _extract_resources_from_entry(
                        data, entry_def_obj, log_file_name, resource_manager
                    )
                    
            except (PbdError, DataExtractionError) as pbd_e:
                failed_count += 1
                logger.exception(
                    f"PBD Extraction error for {entry_def_obj.objectname} in {log_file_name}: {pbd_e}"
                )
            except Exception as e:
                failed_count += 1
                logger.error(
                    f"Unexpected error processing entry {entry_def_obj.objectname} in {log_file_name}: {e}",
                    exc_info=True,
                )
    
    return extracted_count, failed_count


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
    # Setup basic extraction parameters
    log_file_name = _get_log_file_name(file_content, file_name_for_logging)
    block_size = getattr(header, "effective_block_size", DEFAULT_BLOCK_SIZE)
    output_file_path_base = _setup_output_directory(output_path, file_content, log_file_name)
    
    logger.info(
        f"Extracting {log_file_name} (unicode={header.is_unicode}) to {output_file_path_base}"
    )
    
    # Extract nodes
    nodes = extract_nods(
        file_content, header.is_unicode, header.first_nod_offset, block_size
    )
    
    # Setup progress tracking
    total_entries = sum(
        node.numberofentries
        for node in nodes
        if node and hasattr(node, "numberofentries")
    )
    
    progress = None
    if show_progress and total_entries > 0:
        progress = TqdmProgressTracker(
            total=total_entries,
            description=f"Extracting {log_file_name}",
            unit="entries",
        )
    
    # Process all entries
    extracted_count, failed_count = _process_all_entries(
        nodes, file_content, header, output_file_path_base,
        log_file_name, block_size, progress
    )
    
    if progress:
        progress.finish()
    
    # Generate resource reports if resources were extracted
    if hasattr(header, 'extract_resources') and header.extract_resources:
        if hasattr(_extract_pbl_logic, '_resource_manager'):
            _extract_pbl_logic._resource_manager.generate_comprehensive_report()
            delattr(_extract_pbl_logic, '_resource_manager')
    
    logger.info(
        f"Finished extraction for {log_file_name}: {extracted_count} succeeded, {failed_count} failed."
    )


def extract_pbl(f: str | Path, output_path: str, show_progress: bool = True, extract_resources: bool = True) -> None:
    """Extracts entries from a PBD/PBL file.
    Opens the file, parses the header, and then calls the core extraction logic,
    passing the open file handle.
    """
    file_path = Path(f)
    log_file_name = file_path.name  # For consistent logging

    try:
        with open(file_path, "rb") as pbd_file_handle:
            logger.debug(
                f"Attempting to extract header for {log_file_name} using open file handle."
            )
            # extract_pbl_header now expects BinaryIO or bytes.
            # We pass the handle and the file_path for logging context.
            header = extract_pbl_header(
                pbd_file_handle,
                block_size=DEFAULT_BLOCK_SIZE,
                file_path_for_error_log=str(file_path),
            )

            logger.debug(
                f"Header extracted for {log_file_name}: unicode={header.is_unicode}, nod_offset={header.first_nod_offset}, file_size={header.file_size}"
            )
            
            # Add resource extraction flag to header
            header.extract_resources = extract_resources

            # Pass the open file_handle (pbd_file_handle) to _extract_pbl_logic
            # _extract_pbl_logic will use this handle for all subsequent reads.
            _extract_pbl_logic(
                pbd_file_handle,
                header,
                output_path,
                show_progress,
                file_name_for_logging=log_file_name,
            )

    except FileNotFoundError:
        logger.exception(f"File not found: {file_path}")
        raise  # Re-raise to be handled by the caller or higher-level error handling
    except PbdError as pbd_e_outer:
        logger.error(
            f"Failed to extract {log_file_name} due to PBD parsing error: {pbd_e_outer}",
            exc_info=True,
        )
        # logger.error("FULL TRACEBACK (PBD Error):\n" + traceback.format_exc()) # Replaced by exc_info
        raise
    except Exception as e_outer:
        logger.error(
            f"Failed to extract {log_file_name} due to an unexpected error: {e_outer}",
            exc_info=True,
        )
        # logger.error("FULL TRACEBACK (Unexpected Error):\n" + traceback.format_exc()) # Replaced by exc_info
        raise
