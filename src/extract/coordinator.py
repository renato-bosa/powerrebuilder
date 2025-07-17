"""PowerBuilder Binary File Extractor.

This module provides functionality for extracting P-code files from PowerBuilder 
binary files (PBL/PBD). It implements a binary file parser that can read the proprietary format 
of PowerBuilder library (PBL) and compiled module (PBD) files to extract their contents.

Key features:
- Extraction of P-code files (.fun) containing compiled bytecode
- Support for both ASCII and Unicode encodings
- Handling of library dependencies
- Extraction of metadata and resource information
- Robust error handling for corrupted files
- Progress reporting for large file extraction

The extraction process works by:
1. Reading the file header to determine format version and encoding
2. Parsing the node structure (NOD blocks) containing file entries
3. Following offset pointers to extract data blocks (DAT)
4. Extracting P-code files for decompilation

This is the first step in the sequential pipeline:
- Extract: Produces .fun files → for Decompile stage
- Decompile: Converts .fun to .sru → for Parse stage
- Parse: Converts .sru to AST → for Model stage
- Model: Builds semantic models → for Generate stage
- Generate: Produces modern code
"""

import logging
import os
import gc
from pathlib import Path
from typing import Optional

from src.common.security import (
    PathValidator,
    safe_create_directory,
    safe_join_path,
    safe_write_file,
    sanitize_filename,
)
from src.common.limits import ResourceMonitor, ResourceLimits, safe_read_file
from src.common.streaming import StreamReader
from src.common.exceptions import PbdError
from src.extract.pbd.extractors.base import (
    _extract_pbl_logic,  # Import the new internal logic function
    extract_pbl,
)
from src.extract.pbd.io.progress import TqdmProgressTracker
from src.extract.pbd.reader import StreamingPBDReader
from src.extract.pbd.structures.header import extract_pbl_header
from src.extract.utils.binary import retrieve_bytes_from_file  # MODIFIED

# Set up logging
logger = logging.getLogger(__name__)

# Data block and node structures are defined in extract.pbd.structures module

# Streaming threshold (4MB)
STREAMING_THRESHOLD = 4 * 1024 * 1024


def _attempt_standard_extraction(
    file_path_obj: Path, pbd_output_dir: Path, file_name: str, show_progress: bool, extract_resources: bool,
) -> bool:








    """Attempt standard extraction of PBL/PBD file.

    Returns:
        True if successful, False if failed
    """
    try:
        logger.info("Attempt 1: Standard extraction for %s", file_name)
        extract_pbl(
            str(file_path_obj), str(pbd_output_dir), show_progress=show_progress, extract_resources=extract_resources,
        )
        logger.info("Attempt 1: Standard extraction for %s SUCCEEDED.", file_name)
        return True
    except PbdError as pbd_e:
        logger.warning(
            "Attempt 1: Standard extraction for %s failed with PbdError: %s", file_name, pbd_e,
        )
        logger.info("Proceeding to recovery attempts for %s.", file_name)
    except Exception as e:
        logger.exception(
            "Attempt 1: Standard extraction for %s failed with an unexpected error: %s", file_name, e,
        )
        logger.info("Proceeding to recovery attempts for %s.", file_name)
    return False


def _extract_with_streaming(
    file_path_obj: Path, pbd_output_dir: Path, file_name: str, 
    show_progress: bool, resource_monitor: ResourceMonitor
) -> bool:
    """Extract large PBL/PBD file using streaming for memory efficiency.
    
    Args:
        file_path_obj: Path to the PBL/PBD file
        pbd_output_dir: Output directory
        file_name: Name of the file
        show_progress: Whether to show progress
        resource_monitor: Resource monitor instance
        
    Returns:
        True if successful, False if failed
    """
    logger.info("Using streaming extraction for large file %s", file_name)
    
    try:
        file_size = file_path_obj.stat().st_size
        
        # Create compound progress tracker
        progress = None
        if show_progress:
            progress = TqdmProgressTracker(
                total=file_size,
                description=f"Streaming {file_name}",
                unit="B",
                unit_scale=True,
                unit_divisor=1024,
            )
        
        extracted_count = 0
        bytes_processed = 0
        
        def progress_callback(current, total):
            """Update progress with compound tracking."""
            nonlocal bytes_processed
            if progress:
                # Update with byte-level progress
                chunk_size = max(1, file_size // max(1, total))
                new_bytes = current * chunk_size
                progress.update(new_bytes)
                bytes_processed = new_bytes
                
                # Show transfer speed and ETA
                rate = progress.get_rate()
                eta = progress.get_eta_string()
                progress.pbar.set_postfix({
                    'entries': f"{current}/{total}",
                    'speed': f"{rate/1024/1024:.1f}MB/s",
                    'eta': eta,
                })
                
            # Check memory pressure periodically
            if current % 10 == 0:
                _check_memory_pressure(resource_monitor)
        
        # Use streaming reader
        with StreamingPBDReader(file_path_obj) as reader:
            reader.extract_all(pbd_output_dir, progress_callback)
            extracted_count = reader._header.entry_count if reader._header else 0
        
        if progress:
            progress.finish()
            progress.close()
            
        logger.info(
            "Streaming extraction complete for %s: %d entries extracted",
            file_name, extracted_count
        )
        return extracted_count > 0
        
    except MemoryError:
        logger.error("Out of memory during streaming extraction of %s", file_name)
        gc.collect()  # Force garbage collection
        return False
    except Exception as e:
        logger.exception(
            "Streaming extraction failed for %s: %s", file_name, e
        )
        return False


def _check_memory_pressure(resource_monitor: ResourceMonitor) -> None:
    """Check memory pressure and trigger GC if needed."""
    try:
        # Check current memory usage
        stats = resource_monitor.get_stats()
        memory_percent = stats['memory_percent']
        
        if memory_percent > 70:
            logger.debug("Memory usage at %.1f%%, triggering garbage collection", memory_percent)
            gc.collect()
            
            # Check again after GC
            new_stats = resource_monitor.get_stats()
            new_percent = new_stats['memory_percent']
            logger.debug("Memory usage after GC: %.1f%%", new_percent)
            
    except Exception as e:
        logger.debug("Error checking memory pressure: %s", e)


def _read_file_for_recovery(file_path_obj: Path, file_name: str) -> bytes | None:








    """Read file bytes for recovery attempts.

    Returns:
        File bytes or None if reading failed
    """
    try:
        file_bytes = retrieve_bytes_from_file(file_path_obj, 0, -1)
        if not file_bytes:
            logger.error(
                "CRITICAL: Could not read file %s for recovery attempts. Aborting for this file.", file_name,
            )
            return None
        return file_bytes
    except OSError as e_io_fb:
        logger.exception(
            "CRITICAL: IOError reading file %s for recovery: %s", file_name, e_io_fb,
        )
        return None
    except Exception as e_fb:
        logger.exception(
            "CRITICAL: Unexpected error reading file %s for recovery: %s", file_name, e_fb,
        )
        return None


def _attempt_recovery_with_unicode_flag(
    file_bytes: bytes, file_path_obj: Path, pbd_output_dir: Path, file_name: str, unicode_attempt_flag: bool, attempt_num: int, extract_resources: bool,
) -> bool:








    """Attempt recovery with specific unicode flag.

    Returns:
        True if successful, False if failed
    """
    logger.info(
        "Attempt %d: Recovery for %s with explicit unicode_flag=%s for header parsing.", attempt_num, file_name, unicode_attempt_flag,
    )
    try:
        # Import default block size
        DEFAULT_BLOCK_SIZE = 512  # Standard block size

        header = extract_pbl_header(
            file_bytes, block_size=DEFAULT_BLOCK_SIZE, file_path_for_error_log=str(file_path_obj), )
        # Note: extract_resources will be passed to _extract_pbl_logic instead
        logger.info(
            "Attempt %d: Header parsing for %s (unicode_flag_override=%s) SUCCEEDED. Header: unicode=%s, nod_offset=%s", attempt_num, file_name, unicode_attempt_flag, header.is_unicode, header.first_nod_offset,
        )

        _extract_pbl_logic(
            file_bytes, header, str(pbd_output_dir), show_progress=False, file_name_for_logging=file_name, )
        logger.info(
            "Attempt %d: Recovery extraction for %s (using unicode_flag_override=%s for header) SUCCEEDED.", attempt_num, file_name, unicode_attempt_flag,
        )
        return True
    except PbdError as pbd_rec_e:
        logger.warning(
            "Attempt %d: Recovery for %s (unicode_flag_override=%s for header) failed: %s", attempt_num, file_name, unicode_attempt_flag, pbd_rec_e,
        )
    except Exception as e_rec:
        logger.exception(
            "Attempt %d: Recovery for %s (unicode_flag_override=%s for header) failed with unexpected error: %s", attempt_num, file_name, unicode_attempt_flag, e_rec,
        )
    return False


def _perform_recovery_attempts(
    file_bytes: bytes, file_path_obj: Path, pbd_output_dir: Path, file_name: str, extract_resources: bool,
) -> bool:








    """Perform recovery attempts with different unicode flags.

    Returns:
        True if any attempt succeeded, False otherwise
    """
    recovery_unicode_flags = [False, True]

    for idx, unicode_attempt_flag in enumerate(recovery_unicode_flags):
        attempt_num = idx + 2
        if _attempt_recovery_with_unicode_flag(
            file_bytes, file_path_obj, pbd_output_dir, file_name, unicode_attempt_flag, attempt_num, extract_resources,
        ):
            return True
    return False


def _attempt_enhanced_byte_recovery(
    file_bytes: bytes, pbd_output_dir: str, file_name: str, show_progress: bool,
) -> bool:








    """Attempt enhanced byte-level recovery.

    Returns:
        True if successful, False otherwise
    """
    logger.info(
        "Attempt 4: Enhanced byte-level recovery for %s", file_name,
    )
    try:
        # Try enhanced byte-level recovery with multiple strategies
        if _perform_enhanced_byte_recovery(
            file_bytes, pbd_output_dir, file_name, show_progress=show_progress,
        ):
            logger.info(
                "Attempt 4: Enhanced byte-level recovery for %s SUCCEEDED.", file_name,
            )
            return True
        else:
            logger.warning(
                "Attempt 4: Enhanced byte-level recovery for %s found no recoverable data.", file_name,
            )
    except Exception as e:
        logger.exception(
            "Attempt 4: Enhanced byte-level recovery for %s failed with error: %s", file_name, e,
        )
    return False


def extract_with_recovery(
    f: str, output_path: str, *, show_progress: bool = True, enable_byte_recovery: bool = False, extract_resources: bool = True, ) -> bool:








    """Extract a PBL/PBD file with recovery options for corrupted files.

    This function attempts to extract a PBL/PBD file with robust error handling, including multiple recovery strategies for corrupted files.

    Args:
        f: Path to the PBL/PBD file
        output_path: Directory to write extracted files
        show_progress: Whether to show progress information
        enable_byte_recovery: Whether to enable byte-level recovery (currently simplified)
        extract_resources: Whether to extract embedded resources (images, audio, etc.)

    Returns:
        True if extraction was successful or recovery produced output, False otherwise.
    """
    # Initialize resource monitor
    resource_monitor = ResourceMonitor()
    resource_monitor.start_monitoring()

    try:
        file_path_obj = Path(f)
        file_size = file_path_obj.stat().st_size
        file_name = file_path_obj.name

        # Check file size limits
        resource_monitor.check_file_size(file_size, str(file_path_obj))

        # Validate and create output directory with security checks
        output_base = Path(output_path).resolve()
        sanitized_name = sanitize_filename(file_name)
        pbd_output_dir = safe_join_path(output_base, sanitized_name)
        safe_create_directory(pbd_output_dir, output_base)

        if show_progress:
            logger.info(
                "Starting extraction of %s (%s bytes) -> %s", file_name, f"{file_size:,}", pbd_output_dir,
            )

        # Register file with resource monitor
        resource_monitor.register_file(file_size)

        # Check if file is large enough to require streaming
        if file_size > STREAMING_THRESHOLD:
            logger.info(
                "File %s (%s bytes) exceeds streaming threshold (%s bytes)",
                file_name, f"{file_size:,}", f"{STREAMING_THRESHOLD:,}"
            )
            # Attempt streaming extraction for large files
            if _extract_with_streaming(file_path_obj, pbd_output_dir, file_name, show_progress, resource_monitor):
                return True
            # If streaming fails, fall back to standard extraction
            logger.warning("Streaming extraction failed for %s, attempting standard extraction", file_name)

        # Attempt 1: Standard extraction
        if _attempt_standard_extraction(file_path_obj, pbd_output_dir, file_name, show_progress, extract_resources):
            return True

        # Read file bytes for recovery
        file_bytes = _read_file_for_recovery(file_path_obj, file_name)
        if not file_bytes:
            return False

        # Attempts 2-3: Recovery with different unicode flags
        if _perform_recovery_attempts(file_bytes, file_path_obj, pbd_output_dir, file_name, extract_resources):
            return True

        # Attempt 4: Enhanced byte-level recovery
        if enable_byte_recovery:
            if _attempt_enhanced_byte_recovery(file_bytes, str(pbd_output_dir), file_name, show_progress):
                return True
        else:
            logger.info(
                "Attempt 4: Byte-level recovery skipped (enable_byte_recovery=False).",
            )

        logger.error("All extraction attempts for %s failed.", file_name)
        return False

    finally:
        resource_monitor.stop_monitoring()


# Define source file extensions at module level
SOURCE_FILE_EXTENSIONS = {".win", ".srd", ".sru", ".srw", ".sra", ".srm", ".srs", ".men"}

def extract_pbls(
    input_dir: str, output_dir: str, *, enable_byte_recovery: bool = False, extract_resources: bool = True, progress=None,
) -> None:






    """Extract content from all PBL/PBD files in a directory.

    Args:
        input_dir: Path to directory containing PBL/PBD files or a single PBL/PBD file.
        output_dir: Path to write extracted files.
        enable_byte_recovery: Whether to enable byte-level recovery for individual files.
        extract_resources: Whether to extract embedded resources (images, audio, etc.)
    """
    # Initialize resource monitor with custom limits
    limits = ResourceLimits(
        max_file_size=500 * 1024 * 1024,  # 500 MB per file
        max_total_size=5 * 1024 * 1024 * 1024,  # 5 GB total
        max_file_count=50000,  # Up to 50k files
    )
    resource_monitor = ResourceMonitor(limits)
    resource_monitor.start_monitoring()

    try:
        input_path = Path(input_dir).resolve()
        output_path = Path(output_dir).resolve()

        # Validate paths - use current directory as base
        base_path = Path.cwd()
        PathValidator.validate_path(input_path, base_path)
        safe_create_directory(output_path, base_path)

        logging.info("Extracting PBL/PBD files from %s to %s", input_path, output_path)

        # Collect files to process
        files_to_process = _collect_files_to_process(input_path)
        if not files_to_process:
            logging.info("No files to process.")
            return

        # Check file count limit
        resource_monitor.file_count = len(files_to_process)
        resource_monitor.check_file_count()

        # Process single source file immediately if that's all we have
        if len(files_to_process) == 1 and input_path.is_file() and _is_source_file(files_to_process[0]):
            _copy_source_file(files_to_process[0], safe_join_path(output_path, sanitize_filename(files_to_process[0].name)))
            return

        # Setup progress tracking
        overall_progress, file_task = _setup_progress_tracking(progress, len(files_to_process))

        # Process all files
        successful_files = _process_all_files(
            files_to_process, input_path, output_path, enable_byte_recovery, extract_resources, progress, file_task, overall_progress,
        )

        # Finalize progress and report results
        _finalize_progress(overall_progress, progress, file_task, len(files_to_process))
        _report_results(successful_files, len(files_to_process))

        # Log resource usage
        stats = resource_monitor.get_stats()
        logging.info(
            "Resource usage - Files: %d, Total size: %s, Memory: %s (%.1f%%), Time: %.1fs",
            stats['file_count'],
            f"{stats['total_size']:,}",
            f"{stats['memory_usage']:,}",
            stats['memory_percent'],
            stats['elapsed_time']
        )

    finally:
        resource_monitor.stop_monitoring()


def _collect_files_to_process(input_path: Path) -> list[Path]:








    """Collect all files that need to be processed."""
    if input_path.is_file():
        return [input_path]

    # Directory processing - look for PBL/PBD files
    pb_files = list(input_path.glob("**/*.p[bl][dl]"))
    if pb_files:
        logging.info("Found %d PBL/PBD files to extract", len(pb_files))
        return pb_files

    # If no PBL/PBD files, try to find source files
    source_files = []
    for ext in SOURCE_FILE_EXTENSIONS:
        source_files.extend(input_path.glob(f"**/*{ext}"))

    if source_files:
        logging.info("Found %d source files to copy", len(source_files))
        return source_files

    logging.warning("No PBL/PBD or source files found in %s", input_path)
    return []


def _is_source_file(file_path: Path) -> bool:








    """Check if a file is a PowerBuilder source file."""
    return file_path.suffix.lower() in SOURCE_FILE_EXTENSIONS


def _setup_progress_tracking(progress, total_files: int) -> tuple:








    """Setup progress tracking (Rich or TQDM)."""
    if progress:
        file_task = progress.file_progress.add_task(
            "Extracting files", total=total_files,
        )
        return None, file_task
    else:
        overall_progress = TqdmProgressTracker(
            total=total_files, description="Overall Extraction Progress", unit="files", )
        return overall_progress, None


def _process_all_files(
    files_to_process: list[Path], input_path: Path, output_path: Path, enable_byte_recovery: bool, extract_resources: bool, progress, file_task, overall_progress,
) -> int:








    """Process all collected files."""
    successful_files = 0

    for i, file_to_process in enumerate(files_to_process):
        _update_progress(progress, file_task, overall_progress, i, file_to_process.name)

        try:
            if _is_source_file(file_to_process):
                if _process_source_file(file_to_process, input_path, output_path):
                    successful_files += 1
            else:
                if _process_pbl_file(file_to_process, input_path, output_path, enable_byte_recovery, extract_resources):
                    successful_files += 1
        except Exception as e:
            _log_processing_error(file_to_process, e)

    return successful_files


def _update_progress(progress, file_task, overall_progress, index: int, file_name: str) -> None:







    """Update progress tracking."""
    if progress:
        progress.file_progress.update(
            file_task, completed=index, description=f"Extracting: {file_name}", )
    elif overall_progress:
        overall_progress.update(index, item_name=file_name)


def _process_source_file(file_to_process: Path, input_path: Path, output_path: Path) -> bool:








    """Process a PowerBuilder source file."""
    # Determine relative path for copying
    output_base = output_path.resolve()

    if input_path.is_file():
        sanitized_name = sanitize_filename(file_to_process.name)
        dest_path = safe_join_path(output_base, sanitized_name)
    else:
        rel_path = file_to_process.relative_to(input_path)
        # Sanitize each path component
        sanitized_parts = [sanitize_filename(part) for part in rel_path.parts]
        dest_path = safe_join_path(output_base, *sanitized_parts)

    safe_create_directory(dest_path.parent, output_base)
    _copy_source_file(file_to_process, dest_path)
    return True


def _copy_source_file(src_path: Path, dest_path: Path) -> None:







    """Copy a source file with PB export header."""
    try:
        # Read file with size limit
        content_bytes = safe_read_file(str(src_path))
        content = content_bytes.decode('utf-8', errors='ignore')

        # Prepare output content
        output_content = f"HA$PBExportHeader${src_path.name}\\n"
        output_content += "$PBExportComments$\\n"
        output_content += content

        # Get base directory for security validation
        base_dir = dest_path.parent.resolve()

        # Write file securely
        safe_write_file(dest_path, output_content, base_dir)

        logging.info("Copied source file %s to %s", src_path, dest_path)
    except Exception as e:
        logging.exception("Error copying file %s: %s", src_path, e)
        raise


def _process_pbl_file(
    file_to_process: Path, input_path: Path, output_path: Path, enable_byte_recovery: bool, extract_resources: bool,
) -> bool:








    """Process a PBL/PBD file."""
    # Determine output path
    if input_path.is_file():
        this_output_path = output_path
    else:
        relative_path = file_to_process.relative_to(input_path)
        this_output_path = output_path / relative_path.parent

    # Check file size and log streaming information
    file_size = file_to_process.stat().st_size
    if file_size > STREAMING_THRESHOLD:
        logger.info(
            f"Large file detected: {file_to_process.name} ({file_size:,} bytes) - will use streaming extraction"
        )
    
    logger.info(
        f"Dispatching extraction for {file_to_process.name} to output directory {this_output_path}",
    )

    return extract_with_recovery(
        str(file_to_process), str(this_output_path), show_progress=True, enable_byte_recovery=enable_byte_recovery, extract_resources=extract_resources, )


def _log_processing_error(file_to_process: Path, error: Exception) -> None:







    """Log processing errors with appropriate detail."""
    if isinstance(error, PbdError):
        logging.error(
            f"PBD Error processing file {file_to_process}: {error}", exc_info=True, )
    elif isinstance(error, OSError):
        logging.error(
            f"IO Error processing file {file_to_process}: {error}", exc_info=True, )
    else:
        logging.error(
            f"Unexpected error processing file {file_to_process}: {error}", exc_info=True, )


def _finalize_progress(overall_progress, progress, file_task, total_files: int) -> None:







    """Finalize progress tracking."""
    if overall_progress:
        overall_progress.finish()
    elif progress:
        progress.file_progress.update(
            file_task, completed=total_files, description="Extraction complete", )


def _report_results(successful_files: int, total_files: int) -> None:







    """Report extraction results."""
    success_rate = (successful_files / total_files) * 100 if total_files > 0 else 0
    logging.info(
        f"Extraction complete: {successful_files}/{total_files} files processed successfully ({success_rate:.1f}%)",
    )


def _perform_enhanced_byte_recovery(
    file_bytes: bytes, output_dir: str, file_name: str, show_progress: bool = True,
) -> bool:








    """Perform enhanced byte-level recovery with multiple strategies.

    This uses the EnhancedRecoveryEngine which implements:
    1. Corruption pattern fixes
    2. Block signature scanning (HDR, NOD, ENT, DAT, FRE)
    3. Header reconstruction
    4. NOD block recovery
    5. ENT-DAT block matching
    6. Orphaned block recovery
    7. FRE block analysis

    Args:
        file_bytes: The file content as bytes
        output_dir: Directory to write recovered files
        file_name: Name of the file being recovered
        show_progress: Whether to show progress

    Returns:
        True if any data was recovered, False otherwise
    """
    from src.extract.pbd.recovery.checkpoint import EnhancedRecoveryEngine

    logger.info("Starting enhanced byte-level recovery for %s", file_name)

    # Create output directory
    output_path = Path(output_dir)

    # Define progress callback if showing progress
    progress_callback = None
    if show_progress:
        def progress_callback(message: str, percent: float) -> None:

            logger.info("Recovery %s: %s (%.1f%%)", file_name, message, percent)

    # Initialize the enhanced recovery engine with progress callback
    engine = EnhancedRecoveryEngine(file_bytes, output_path, progress_callback)

    # Perform comprehensive recovery
    success = engine.recover_all()

    if success:
        logger.info(
            f"Enhanced recovery complete for {file_name}. "
            f"Objects recovered: {engine.stats["objects_recovered"]}, "
            f"Blocks recovered: {engine.stats["blocks_recovered"]}",
        )
    else:
        logger.warning("No data could be recovered from %s", file_name)

    return success




def _create_recovery_directory(output_path: str, filename: str) -> str | None:












    """Create recovery directory for byte-level recovery.

    Returns:
        Recovery directory path or None if creation failed
    """
    recovery_dir = os.path.join(output_path, "recovery", os.path.basename(filename))
    logger.debug(
        f"BYTE_RECOVERY_PATHS: Intended recovery_dir: {recovery_dir}",
    )

    try:
        os.makedirs(recovery_dir, exist_ok=True)
        logger.debug(
            f"BYTE_RECOVERY_PATHS: os.makedirs called for {recovery_dir}. Exists now: {os.path.exists(recovery_dir)}",
        )
        return recovery_dir
    except OSError as e_mkdir:
        logger.error(
            f"BYTE_RECOVERY_PATHS: OSError during os.makedirs for {recovery_dir}: {e_mkdir}", exc_info=True, )
        return None
    except Exception as e_mkdir_other:
        logger.error(
            f"BYTE_RECOVERY_PATHS: Unexpected exception during os.makedirs for {recovery_dir}: {e_mkdir_other}", exc_info=True, )
        return None


def _read_file_data(filename: str) -> bytes | None:








    """Read file data for byte recovery.

    Returns:
        File data bytes or None if reading failed
    """
    try:
        with open(filename, "rb") as file:
            return file.read()
    except OSError as e_read:
        logger.error(
            f"BYTE_RECOVERY_IO: Failed to read file {filename} for byte recovery: {e_read}", exc_info=True, )
        return None
    except Exception as e_read_other:
        logger.error(
            f"BYTE_RECOVERY_IO: Unexpected error reading file {filename} for byte recovery: {e_read_other}", exc_info=True, )
        return None


def _save_recovered_block(recovery_dir: str, offset: int, data_block: bytes) -> bool:








    """Save recovered data block to file.

    Returns:
        True if saved successfully, False otherwise
    """
    try:
        recovery_file = os.path.join(
            recovery_dir, f"recovered_block_{offset:08x}.dat",
        )
        with open(recovery_file, "wb") as out_file:
            out_file.write(data_block)
        return True
    except OSError as e_write_dat:
        logger.warning(
            f"Byte recovery: IOError writing recovered .dat file for block at {offset:08x}. Error: {e_write_dat}",
        )
        return False
    except Exception as e:
        logger.debug(
            f"Byte recovery: Unexpected error writing block at {offset:08x}. Error: {e}",
        )
        return False


def _decode_block_content(content: bytes, unicode_mode: bool) -> str | None:








    """Decode block content to text.

    Returns:
        Decoded text or None if decoding failed
    """
    try:
        if unicode_mode:
            return content.decode("utf-16-le", errors="ignore")
        else:
            return content.decode("latin1", errors="ignore")
    except UnicodeDecodeError as ude:
        logger.debug(
            f"Byte recovery: Unicode decode error. Error: {ude}",
        )
        return None
    except Exception as e:
        logger.debug(
            f"Byte recovery: Error decoding content. Error: {e}",
        )
        return None


def _is_powerbuilder_source(text: str) -> bool:








    """Check if text looks like PowerBuilder source code."""
    pb_markers = [
        "$PBExportHeader", "SQLCA", "global type", "type", "forward", ]
    return any(marker in text for marker in pb_markers)


def _save_recovered_source(recovery_dir: str, offset: int, text: str) -> bool:








    """Save recovered source text to file.

    Returns:
        True if saved successfully, False otherwise
    """
    try:
        text_file = os.path.join(
            recovery_dir, f"recovered_source_{offset:08x}.txt",
        )
        with open(text_file, "w", encoding="utf-8") as out_file:
            out_file.write(text)
        return True
    except OSError as e_write_text:
        logger.warning(
            f"Byte recovery: IOError writing recovered text file for block at {offset:08x}. Error: {e_write_text}",
        )
        return False
    except Exception as e_text_proc:
        logger.debug(
            f"Byte recovery: Error saving text block at {offset:08x}. Error: {e_text_proc}",
        )
        return False


def _process_dat_block(file_data: bytes, offset: int, recovery_dir: str) -> bool:








    """Process a potential DAT block at given offset.

    Returns:
        True if a valid PowerBuilder source was recovered, False otherwise
    """
    # Try both ASCII and Unicode modes
    unicode_mode = file_data[offset : offset + 4] == b"DAT*"

    try:
        # Read size (assuming next 4 bytes are size)
        size = int.from_bytes(file_data[offset + 4 : offset + 8], byteorder="little")

        # Sanity check on size
        if not (0 < size < 10 * 1024 * 1024):  # Max 10MB chunk
            return False

        # Extract the data block
        data_block = file_data[offset : offset + 8 + size]

        # Save recovered block
        if not _save_recovered_block(recovery_dir, offset, data_block):
            return False

        # Try to detect content type
        content = file_data[offset + 8 : offset + 8 + size]
        if len(content) == 0:
            return False

        # Check if it's text
        text = _decode_block_content(content, unicode_mode)
        if not text:
            return False

        # If it looks like PowerBuilder source code, save it
        if _is_powerbuilder_source(text):
            if _save_recovered_source(recovery_dir, offset, text):
                return True

    except ValueError as ve:
        logger.debug(
            f"Byte recovery: ValueError processing block at {offset:08x}. Likely malformed size. Error: {ve}",
        )
    except Exception as e:
        logger.debug(
            f"Byte recovery: Unexpected error processing block at {offset:08x}. Error: {e}",
        )

    return False


def extract_with_byte_recovery(f: str, output_path: str) -> bool:








    """Attempt byte-level recovery of a corrupted PBL/PBD file.

    This is a last-resort recovery method that scans the file byte-by-byte
    looking for data blocks and attempts to extract them.

    Args:
        f: Path to the PBL/PBD file
        output_path: Directory to write extracted files (e.g., "data/output/current/extracted")

    Returns:
        True if any data was recovered, False otherwise
    """
    logger.info("BYTE_RECOVERY_INIT: Starting byte-level recovery of %s", f)
    logger.debug(
        f"BYTE_RECOVERY_PATHS: Received output_path: {output_path}",
    )

    # Create recovery output directory
    recovery_dir = _create_recovery_directory(output_path, f)
    if not recovery_dir:
        return False

    # Read file data
    file_data = _read_file_data(f)
    if not file_data:
        return False

    file_size = len(file_data)

    # Create progress tracker
    progress = TqdmProgressTracker(
        total=file_size, description="Byte-level recovery scan", unit="bytes", )

    # Search for DAT blocks
    recovered_count = 0
    for i in range(file_size - 8):
        # Update progress every 10MB
        if i % (10 * 1024 * 1024) == 0:
            progress.update(i)

        # Check for DAT marker
        if file_data[i : i + 4] == b"DAT\\0" or file_data[i : i + 4] == b"DAT*":
            if _process_dat_block(file_data, i, recovery_dir):
                recovered_count += 1

    # Finalize progress
    progress.update(file_size)
    progress.finish()

    logger.info(
        f"Byte-level recovery complete. Recovered {recovered_count} potential source files",
    )
    return recovered_count > 0
