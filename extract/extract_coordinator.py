"""PowerBuilder Binary File Extractor.

This module provides functionality for extracting source code from PowerBuilder binary files (PBL/PBD).
It implements a binary file parser that can read the proprietary format of PowerBuilder library (PBL)
and compiled module (PBD) files to extract their contents as text.

Key features:
- Extraction of source code (SRD, SRW, SRU, etc.) from PBL/PBD files
- Support for both ASCII and Unicode encodings
- Handling of library dependencies
- Extraction of metadata and resource information
- Robust error handling for corrupted files
- Progress reporting for large file extraction

The extraction process works by:
1. Reading the file header to determine format version and encoding
2. Parsing the node structure (NOD blocks) containing file entries
3. Following offset pointers to extract data blocks (DAT)
4. Reconstructing the original source files

This is the first step in the reverse engineering pipeline, providing raw text
that will be parsed by the grammar parser in the next stage.
"""

import logging
import os
from io import BytesIO
from pathlib import Path
from typing import BinaryIO

from extract.pbd.exceptions import PbdError
from extract.pbd.extraction.extractor import (
    _extract_pbl_logic,  # Import the new internal logic function
    extract_pbl,
)
from extract.pbd.io.progress import TqdmProgressTracker
from extract.pbd.structures.header import extract_pbl_header
from extract.pbd.utils.binary_utils import retrieve_bytes_from_file  # MODIFIED

# Set up logging
logger = logging.getLogger(__name__)

# Data block and node structures are defined in extract.pbd.structures module


def extract_with_recovery(
    f: str,
    output_path: str,
    *,
    show_progress: bool = True,
    enable_byte_recovery: bool = False,
    extract_resources: bool = True,
) -> bool:
    """Extract a PBL/PBD file with recovery options for corrupted files.

    This function attempts to extract a PBL/PBD file with robust error handling,
    including multiple recovery strategies for corrupted files.

    Args:
        f: Path to the PBL/PBD file
        output_path: Directory to write extracted files
        show_progress: Whether to show progress information
        enable_byte_recovery: Whether to enable byte-level recovery (currently simplified)
        extract_resources: Whether to extract embedded resources (images, audio, etc.)

    Returns:
        True if extraction was successful or recovery produced output, False otherwise.
    """
    file_path_obj = Path(f)
    file_size = file_path_obj.stat().st_size
    file_name = file_path_obj.name

    pbd_output_dir = Path(output_path) / file_name
    pbd_output_dir.mkdir(parents=True, exist_ok=True)

    if show_progress:
        logger.info(
            "Starting extraction of %s (%s bytes) -> %s", file_name, f"{file_size:,}", pbd_output_dir
        )

    try:
        logger.info("Attempt 1: Standard extraction for %s", file_name)
        extract_pbl(
            str(file_path_obj), str(pbd_output_dir), show_progress=show_progress,
            extract_resources=extract_resources
        )
        logger.info("Attempt 1: Standard extraction for %s SUCCEEDED.", file_name)
        return True
    except PbdError as pbd_e:
        logger.warning(
            "Attempt 1: Standard extraction for %s failed with PbdError: %s", file_name, pbd_e
        )
        logger.info("Proceeding to recovery attempts for %s.", file_name)
    except Exception as e:
        logger.exception(
            "Attempt 1: Standard extraction for %s failed with an unexpected error: %s", file_name, e
        )
        logger.info("Proceeding to recovery attempts for %s.", file_name)

    try:
        file_bytes = retrieve_bytes_from_file(file_path_obj, 0, -1)
        if not file_bytes:
            logger.error(
                "CRITICAL: Could not read file %s for recovery attempts. Aborting for this file.", file_name
            )
            return False
    except OSError as e_io_fb:
        logger.exception(
            "CRITICAL: IOError reading file %s for recovery: %s", file_name, e_io_fb
        )
        return False
    except Exception as e_fb:
        logger.exception(
            "CRITICAL: Unexpected error reading file %s for recovery: %s", file_name, e_fb
        )
        return False

    recovery_unicode_flags = [False, True]

    for idx, unicode_attempt_flag in enumerate(recovery_unicode_flags):
        attempt_num = idx + 2
        logger.info(
            "Attempt %d: Recovery for %s with explicit unicode_flag=%s for header parsing.",
            attempt_num, file_name, unicode_attempt_flag
        )
        try:
            # Import default block size
            DEFAULT_BLOCK_SIZE = 512  # Standard block size

            header = extract_pbl_header(
                file_bytes,
                block_size=DEFAULT_BLOCK_SIZE,
                file_path_for_error_log=str(file_path_obj),
            )
            # Add resource extraction flag to header
            header.extract_resources = extract_resources
            logger.info(
                "Attempt %d: Header parsing for %s (unicode_flag_override=%s) SUCCEEDED. Header: unicode=%s, nod_offset=%s",
                attempt_num, file_name, unicode_attempt_flag, header.is_unicode, header.first_nod_offset
            )

            _extract_pbl_logic(
                file_bytes,
                header,
                str(pbd_output_dir),
                show_progress=False,
                file_name_for_logging=file_name,
            )
            logger.info(
                "Attempt %d: Recovery extraction for %s (using unicode_flag_override=%s for header) SUCCEEDED.",
                attempt_num, file_name, unicode_attempt_flag
            )
            return True
        except PbdError as pbd_rec_e:
            logger.warning(
                "Attempt %d: Recovery for %s (unicode_flag_override=%s for header) failed: %s",
                attempt_num, file_name, unicode_attempt_flag, pbd_rec_e
            )
        except Exception as e_rec:
            logger.exception(
                "Attempt %d: Recovery for %s (unicode_flag_override=%s for header) failed with unexpected error: %s",
                attempt_num, file_name, unicode_attempt_flag, e_rec
            )

    # Attempt 4: Enhanced byte-level recovery
    if enable_byte_recovery:
        logger.info(
            "Attempt 4: Enhanced byte-level recovery for %s", file_name
        )
        try:
            # Try enhanced byte-level recovery with multiple strategies
            if _perform_enhanced_byte_recovery(
                file_bytes,
                str(pbd_output_dir),
                file_name,
                show_progress=show_progress
            ):
                logger.info(
                    "Attempt 4: Enhanced byte-level recovery for %s SUCCEEDED.", file_name
                )
                return True
            else:
                logger.warning(
                    "Attempt 4: Enhanced byte-level recovery for %s found no recoverable data.", file_name
                )
        except Exception as e:
            logger.exception(
                "Attempt 4: Enhanced byte-level recovery for %s failed with error: %s", file_name, e
            )
    else:
        logger.info(
            "Attempt 4: Byte-level recovery skipped (enable_byte_recovery=False)."
        )

    logger.error("All extraction attempts for %s failed.", file_name)
    return False


# Define source file extensions at module level
SOURCE_FILE_EXTENSIONS = {".win", ".srd", ".sru", ".srw", ".sra", ".srm", ".srs", ".men"}

def extract_pbls(
    input_dir: str, output_dir: str, *, enable_byte_recovery: bool = False, 
    extract_resources: bool = True, progress=None
) -> None:
    """Extract content from all PBL/PBD files in a directory.

    Args:
        input_dir: Path to directory containing PBL/PBD files or a single PBL/PBD file.
        output_dir: Path to write extracted files.
        enable_byte_recovery: Whether to enable byte-level recovery for individual files.
        extract_resources: Whether to extract embedded resources (images, audio, etc.)
    """
    input_path = Path(input_dir)
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)

    logging.info("Extracting PBL/PBD files from %s to %s", input_path, output_path)

    # Collect files to process
    files_to_process = _collect_files_to_process(input_path)
    if not files_to_process:
        logging.info("No files to process.")
        return

    # Process single source file immediately if that's all we have
    if len(files_to_process) == 1 and input_path.is_file() and _is_source_file(files_to_process[0]):
        _copy_source_file(files_to_process[0], output_path / files_to_process[0].name)
        return

    # Setup progress tracking
    overall_progress, file_task = _setup_progress_tracking(progress, len(files_to_process))

    # Process all files
    successful_files = _process_all_files(
        files_to_process, input_path, output_path, 
        enable_byte_recovery, extract_resources,
        progress, file_task, overall_progress
    )

    # Finalize progress and report results
    _finalize_progress(overall_progress, progress, file_task, len(files_to_process))
    _report_results(successful_files, len(files_to_process))


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
            "Extracting files", total=total_files
        )
        return None, file_task
    else:
        overall_progress = TqdmProgressTracker(
            total=total_files,
            description="Overall Extraction Progress",
            unit="files",
        )
        return overall_progress, None


def _process_all_files(
    files_to_process: list[Path],
    input_path: Path,
    output_path: Path,
    enable_byte_recovery: bool,
    extract_resources: bool,
    progress,
    file_task,
    overall_progress
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
                if _process_pbl_file(file_to_process, input_path, output_path, 
                                   enable_byte_recovery, extract_resources):
                    successful_files += 1
        except Exception as e:
            _log_processing_error(file_to_process, e)
    
    return successful_files


def _update_progress(progress, file_task, overall_progress, index: int, file_name: str):
    """Update progress tracking."""
    if progress:
        progress.file_progress.update(
            file_task,
            completed=index,
            description=f"Extracting: {file_name}",
        )
    elif overall_progress:
        overall_progress.update(index, item_name=file_name)


def _process_source_file(file_to_process: Path, input_path: Path, output_path: Path) -> bool:
    """Process a PowerBuilder source file."""
    # Determine relative path for copying
    if input_path.is_file():
        dest_path = output_path / file_to_process.name
    else:
        rel_path = file_to_process.relative_to(input_path)
        dest_path = output_path / rel_path
    
    dest_path.parent.mkdir(parents=True, exist_ok=True)
    _copy_source_file(file_to_process, dest_path)
    return True


def _copy_source_file(src_path: Path, dest_path: Path):
    """Copy a source file with PB export header."""
    try:
        with open(src_path, encoding="utf-8", errors="ignore") as src:
            content = src.read()
        
        with open(dest_path, "w", encoding="utf-8") as dst:
            dst.write(f"HA$PBExportHeader${src_path.name}\\n")
            dst.write("$PBExportComments$\\n")
            dst.write(content)
        
        logging.info("Copied source file %s to %s", src_path, dest_path)
    except Exception as e:
        logging.exception("Error copying file %s: %s", src_path, e)
        raise


def _process_pbl_file(
    file_to_process: Path, 
    input_path: Path, 
    output_path: Path,
    enable_byte_recovery: bool,
    extract_resources: bool
) -> bool:
    """Process a PBL/PBD file."""
    # Determine output path
    if input_path.is_file():
        this_output_path = output_path
    else:
        relative_path = file_to_process.relative_to(input_path)
        this_output_path = output_path / relative_path.parent
    
    logger.info(
        f"Dispatching extraction for {file_to_process.name} to output directory {this_output_path}"
    )
    
    return extract_with_recovery(
        str(file_to_process),
        str(this_output_path),
        show_progress=True,
        enable_byte_recovery=enable_byte_recovery,
        extract_resources=extract_resources,
    )


def _log_processing_error(file_to_process: Path, error: Exception):
    """Log processing errors with appropriate detail."""
    if isinstance(error, PbdError):
        logging.error(
            f"PBD Error processing file {file_to_process}: {error}",
            exc_info=True,
        )
    elif isinstance(error, OSError):
        logging.error(
            f"IO Error processing file {file_to_process}: {error}",
            exc_info=True,
        )
    else:
        logging.error(
            f"Unexpected error processing file {file_to_process}: {error}",
            exc_info=True,
        )


def _finalize_progress(overall_progress, progress, file_task, total_files: int):
    """Finalize progress tracking."""
    if overall_progress:
        overall_progress.finish()
    elif progress:
        progress.file_progress.update(
            file_task,
            completed=total_files,
            description="Extraction complete",
        )


def _report_results(successful_files: int, total_files: int):
    """Report extraction results."""
    success_rate = (successful_files / total_files) * 100 if total_files > 0 else 0
    logging.info(
        f"Extraction complete: {successful_files}/{total_files} files processed successfully ({success_rate:.1f}%)"
    )


def _perform_enhanced_byte_recovery(
    file_bytes: bytes,
    output_dir: str,
    file_name: str,
    show_progress: bool = True
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
    from extract.pbd.recovery.enhanced_recovery import EnhancedRecoveryEngine
    
    logger.info(f"Starting enhanced byte-level recovery for {file_name}")
    
    # Create output directory
    output_path = Path(output_dir)
    
    # Initialize the enhanced recovery engine
    engine = EnhancedRecoveryEngine(file_bytes, output_path)
    
    # Perform comprehensive recovery
    success = engine.recover_all()
    
    if success:
        logger.info(
            f"Enhanced recovery complete for {file_name}. "
            f"Objects recovered: {engine.stats['objects_recovered']}, "
            f"Blocks recovered: {engine.stats['blocks_recovered']}"
        )
    else:
        logger.warning(f"No data could be recovered from {file_name}")
    
    return success




def extract_with_byte_recovery(f: str, output_path: str) -> bool:
    """Attempt byte-level recovery of a corrupted PBL/PBD file.

    This is a last-resort recovery method that scans the file byte-by-byte
    looking for data blocks and attempts to extract them.

    Args:
        f: Path to the PBL/PBD file
        output_path: Directory to write extracted files (e.g., "output/extracted")

    Returns:
        True if any data was recovered, False otherwise
    """
    logger.info(f"BYTE_RECOVERY_INIT: Starting byte-level recovery of {f}")
    logger.debug(
        f"BYTE_RECOVERY_PATHS: Received output_path: {output_path}"
    )  # LOGGING ADDED

    # Create recovery output directory
    # Example: output_path = "output/extracted", f = "input/dcm.pbd"
    # recovery_dir = "output/extracted/recovery/dcm.pbd"
    recovery_dir = os.path.join(output_path, "recovery", os.path.basename(f))
    logger.debug(
        f"BYTE_RECOVERY_PATHS: Intended recovery_dir: {recovery_dir}"
    )  # LOGGING ADDED

    try:  # LOGGING ADDED - try/except around makedirs
        os.makedirs(recovery_dir, exist_ok=True)
        logger.debug(
            f"BYTE_RECOVERY_PATHS: os.makedirs called for {recovery_dir}. Exists now: {os.path.exists(recovery_dir)}"
        )  # LOGGING ADDED
    except OSError as e_mkdir:  # More specific for os.makedirs
        logger.error(
            f"BYTE_RECOVERY_PATHS: OSError during os.makedirs for {recovery_dir}: {e_mkdir}",
            exc_info=True,
        )
        return False  # Cannot proceed if directory creation fails critically
    except Exception as e_mkdir_other:  # General fallback
        logger.error(
            f"BYTE_RECOVERY_PATHS: Unexpected exception during os.makedirs for {recovery_dir}: {e_mkdir_other}",
            exc_info=True,
        )
        return False

    # Open file in binary mode
    try:
        with open(f, "rb") as file:
            file_data = file.read()
    except OSError as e_read:
        logger.error(
            f"BYTE_RECOVERY_IO: Failed to read file {f} for byte recovery: {e_read}",
            exc_info=True,
        )
        return False
    except Exception as e_read_other:  # General fallback for file read
        logger.error(
            f"BYTE_RECOVERY_IO: Unexpected error reading file {f} for byte recovery: {e_read_other}",
            exc_info=True,
        )
        return False

    file_size = len(file_data)

    # Create progress tracker
    progress = TqdmProgressTracker(
        total=file_size,
        description="Byte-level recovery scan",
        unit="bytes",
    )

    # Search for DAT blocks
    recovered_count = 0
    for i in range(file_size - 8):
        # Update progress every 10MB
        if i % (10 * 1024 * 1024) == 0:
            progress.update(i)

        # Check for DAT marker
        if file_data[i : i + 4] == b"DAT\0" or file_data[i : i + 4] == b"DAT*":
            try:
                # Try both ASCII and Unicode modes
                unicode_mode = file_data[i : i + 4] == b"DAT*"

                # Read size (assuming next 4 bytes are size)
                size = int.from_bytes(file_data[i + 4 : i + 8], byteorder="little")

                # Sanity check on size
                if 0 < size < 10 * 1024 * 1024:  # Max 10MB chunk
                    # Extract the data block
                    data_block = file_data[i : i + 8 + size]

                    # Save recovered block
                    recovery_file = os.path.join(
                        recovery_dir, f"recovered_block_{i:08x}.dat"
                    )
                    with open(recovery_file, "wb") as out_file:
                        out_file.write(data_block)

                    # Try to detect content type
                    content = file_data[i + 8 : i + 8 + size]
                    if len(content) > 0:
                        # Check if it's text
                        try:  # Inner try for text processing
                            if unicode_mode:
                                text = content.decode("utf-16-le", errors="ignore")
                            else:
                                text = content.decode("latin1", errors="ignore")

                            # If it looks like PowerBuilder source code, save it
                            if any(
                                marker in text
                                for marker in [
                                    "$PBExportHeader",
                                    "SQLCA",
                                    "global type",
                                    "type",
                                    "forward",
                                ]
                            ):
                                text_file = os.path.join(
                                    recovery_dir, f"recovered_source_{i:08x}.txt"
                                )
                                with open(text_file, "w", encoding="utf-8") as out_file:
                                    out_file.write(text)

                                    # Count as recovery
                                    recovered_count += 1
                        except UnicodeDecodeError as ude:
                            logger.debug(
                                f"Byte recovery: Unicode decode error for block at {i:08x}. Error: {ude}"
                            )
                        except OSError as e_write_text:
                            logger.warning(
                                f"Byte recovery: IOError writing recovered text file for block at {i:08x}. Error: {e_write_text}"
                            )
                        except Exception as e_text_proc:
                            logger.debug(
                                f"Byte recovery: Error processing potential text block at {i:08x}. Error: {e_text_proc}"
                            )

            except ValueError as ve:
                logger.debug(
                    f"Byte recovery: ValueError processing block at {i:08x}. Likely malformed size. Error: {ve}"
                )
            except OSError as e_write_dat:
                logger.warning(
                    f"Byte recovery: IOError writing recovered .dat file for block at {i:08x}. Error: {e_write_dat}"
                )
            except Exception as e:
                logger.debug(
                    f"Byte recovery: Unexpected error processing block at {i:08x}. Error: {e}"
                )

    # Finalize progress
    progress.update(file_size)
    progress.finish()

    logger.info(
        f"Byte-level recovery complete. Recovered {recovered_count} potential source files"
    )
    return recovered_count > 0
