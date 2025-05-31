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
from pathlib import Path

from extract.pbd_core import (
    PbdError,
    # Constants are also available, e.g., BLOCK_SIZE, but not explicitly listed here if not directly used by top-level functions in this file
    # Save functions like save_to_file are also available but likely called by extract_pbl or _extract_pbl_logic
    extract_pbl_header,
)
from extract.pbd_core.core import (
    _extract_pbl_logic,  # Import the new internal logic function
    extract_pbl,
)
from extract.pbd_io.progress import TqdmProgressTracker
from extract.pbd_io.utils import retrieve_bytes_from_file, BLOCK_SIZE as DEFAULT_BLOCK_SIZE  # MODIFIED

# Set up logging
logger = logging.getLogger(__name__)

# Data block structure
# DataClass = namedtuple("DataClass", "signature current_address next_block_offset payload_length payload_data")

# Node structure
# NodeClass = namedtuple("NodeClass", "nodetype address postfirst numberofentries offsetleft parentoffset offsetright spaceleft entry_defs")


def extract_with_recovery(f: str, output_path: str, show_progress: bool = True, enable_byte_recovery: bool = False) -> bool:
    """Extract a PBL/PBD file with recovery options for corrupted files.

    This function attempts to extract a PBL/PBD file with robust error handling,
    including multiple recovery strategies for corrupted files.

    Args:
        f: Path to the PBL/PBD file
        output_path: Directory to write extracted files
        show_progress: Whether to show progress information
        enable_byte_recovery: Whether to enable byte-level recovery (currently simplified)

    Returns:
        True if extraction was successful or recovery produced output, False otherwise.
    """
    file_path_obj = Path(f)
    file_size = file_path_obj.stat().st_size
    file_name = file_path_obj.name

    pbd_output_dir = Path(output_path) / file_name
    pbd_output_dir.mkdir(parents=True, exist_ok=True)

    if show_progress:
        logger.info(f"Starting extraction of {file_name} ({file_size:,} bytes) -> {pbd_output_dir}")

    try:
        logger.info(f"Attempt 1: Standard extraction for {file_name}")
        extract_pbl(str(file_path_obj), str(pbd_output_dir), show_progress=show_progress)
        logger.info(f"Attempt 1: Standard extraction for {file_name} SUCCEEDED.")
        return True
    except PbdError as pbd_e:
        logger.warning(f"Attempt 1: Standard extraction for {file_name} failed with PbdError: {pbd_e}")
        logger.info(f"Proceeding to recovery attempts for {file_name}.")
    except Exception as e:
        logger.error(f"Attempt 1: Standard extraction for {file_name} failed with an unexpected error: {e}", exc_info=True)
        logger.info(f"Proceeding to recovery attempts for {file_name}.")

    file_bytes = retrieve_bytes_from_file(file_path_obj, 0, -1)
    if not file_bytes:
        logger.error(f"CRITICAL: Could not read file {file_name} for recovery attempts. Aborting for this file.")
        return False

    recovery_unicode_flags = [False, True]

    for idx, unicode_attempt_flag in enumerate(recovery_unicode_flags):
        attempt_num = idx + 2
        logger.info(f"Attempt {attempt_num}: Recovery for {file_name} with explicit unicode_flag={unicode_attempt_flag} for header parsing.")
        try:
            header = extract_pbl_header(file_bytes, block_size=DEFAULT_BLOCK_SIZE, file_path_for_error_log=str(file_path_obj))
            logger.info(f"Attempt {attempt_num}: Header parsing for {file_name} (unicode_flag_override={unicode_attempt_flag}) SUCCEEDED. Header: unicode={header.is_unicode}, nod_offset={header.first_nod_offset}")

            _extract_pbl_logic(file_bytes, header, str(pbd_output_dir), show_progress=False, file_name_for_logging=file_name)
            logger.info(f"Attempt {attempt_num}: Recovery extraction for {file_name} (using unicode_flag_override={unicode_attempt_flag} for header) SUCCEEDED.")
            return True
        except PbdError as pbd_rec_e:
            logger.warning(f"Attempt {attempt_num}: Recovery for {file_name} (unicode_flag_override={unicode_attempt_flag} for header) failed: {pbd_rec_e}")
        except Exception as e_rec:
            logger.error(f"Attempt {attempt_num}: Recovery for {file_name} (unicode_flag_override={unicode_attempt_flag} for header) failed with unexpected error: {e_rec}", exc_info=True)

    logger.debug(f"RECOVERY_CHECK: In extract_with_recovery for {file_name}, enable_byte_recovery is {enable_byte_recovery}")
    if enable_byte_recovery:
        logger.warning(f"Attempt 4: Byte-level recovery for {file_name} (enable_byte_recovery=True) is currently a placeholder. Further specific byte searching logic would be needed here if the above attempts fail.")
        pass
    else:
        logger.info("Attempt 4: Byte-level recovery skipped (enable_byte_recovery=False).")

    logger.error(f"All extraction attempts for {file_name} failed.")
    return False


def extract_pbls(input_dir: str, output_dir: str, enable_byte_recovery: bool = False) -> None:
    """Extract content from all PBL/PBD files in a directory.

    Args:
        input_dir: Path to directory containing PBL/PBD files or a single PBL/PBD file.
        output_dir: Path to write extracted files.
        enable_byte_recovery: Whether to enable byte-level recovery for individual files.
    """
    input_path = Path(input_dir)
    output_path = Path(output_dir)

    # Ensure output directory exists
    output_path.mkdir(parents=True, exist_ok=True)

    logging.info(f"Extracting PBL/PBD files from {input_path} to {output_path}")

    # Initialize progress tracking
    overall_progress = None
    files_to_process = []

    # Check if input is a directory or a file
    if input_path.is_file():
        # Direct file processing
        files_to_process.append(input_path)
        if input_path.suffix.lower() in {'.win', '.srd', '.sru', '.srw', '.sra', '.srm', '.srs', '.men'}:
            # For source files, simply copy them
            try:
                # Create the destination file
                with open(input_path, encoding='utf-8', errors='ignore') as src:
                    content = src.read()

                # Extract just the filename
                filename = input_path.name
                dest_path = output_path / filename

                # Write the content with PB export header
                with open(dest_path, 'w', encoding='utf-8') as dst:
                    dst.write(f"HA$PBExportHeader${filename}\n")
                    dst.write("$PBExportComments$\n")
                    dst.write(content)

                logging.info(f"Copied source file {input_path} to {dest_path}")
            except Exception as e:
                logging.error(f"Error copying file {input_path}: {e}")
        else:
            try:
                logging.info(f"Extracting {input_path} to {output_path}")
                # This will be handled by the main loop now
            except Exception as e:
                logging.error(f"Error extracting {input_path}: {e}")
    else:
        # Directory processing - look for PBL/PBD files
        pb_files = [f for f in input_path.glob("**/*.p[bl][dl]") if f.is_file()]

        if not pb_files:
            # If no PBL/PBD files, try to find source files directly
            source_files = []
            for ext in ['.win', '.srd', '.sru', '.srw', '.sra', '.srm', '.srs', '.men']:
                source_files.extend(input_path.glob(f"**/*{ext}"))

            if source_files:
                logging.info(f"Found {len(source_files)} source files to copy")
                files_to_process.extend(source_files)
            else:
                logging.warning(f"No PBL/PBD files found in {input_path}")
                return
        else:
            logging.info(f"Found {len(pb_files)} PBL/PBD files to extract")
            files_to_process.extend(pb_files)

    total_files_to_process = len(files_to_process)
    if total_files_to_process == 0:
        logging.info("No files to process.")
        return

    overall_progress = TqdmProgressTracker(
        total=total_files_to_process,
        description="Overall Extraction Progress",
        unit="files",
    )

    successful_files = 0
    for i, file_to_process in enumerate(files_to_process):
        overall_progress.update(i, item_name=file_to_process.name)

        is_source_copy = file_to_process.suffix.lower() in {'.win', '.srd', '.sru', '.srw', '.sra', '.srm', '.srs', '.men'}

        try:
            if is_source_copy:
                # Determine relative path for copying
                if input_path.is_file():  # Single file input
                    rel_path = file_to_process.name
                    dest_path_parent = output_path
                else:  # Directory input
                    rel_path = file_to_process.relative_to(input_path)
                    dest_path_parent = output_path

                dest_path = dest_path_parent / rel_path
                dest_path.parent.mkdir(parents=True, exist_ok=True)

                with open(file_to_process, encoding='utf-8', errors='ignore') as src:
                    content = src.read()
                with open(dest_path, 'w', encoding='utf-8') as dst:
                    dst.write(f"HA$PBExportHeader${file_to_process.name}\n")
                    dst.write("$PBExportComments$\n")
                    dst.write(content)
                logging.info(f"Copied source file {file_to_process} to {dest_path}")
                successful_files += 1
            else:
                # Determine output path for PBL/PBD
                if input_path.is_file():  # Single file input
                    this_output_path = output_path
                else:  # Directory input
                    relative_path = file_to_process.relative_to(input_path)
                    this_output_path = output_path / relative_path.parent

                # Removed the block that created pbd_specific_out_dir and reassigned output_file_path_base here.
                # The logger.info and call to extract_with_recovery will now use this_output_path.

                logger.info(f"Dispatching extraction for {file_to_process.name} to output directory {this_output_path}")
                if extract_with_recovery(str(file_to_process), str(this_output_path), show_progress=True, enable_byte_recovery=enable_byte_recovery):
                    successful_files += 1
        except Exception as e:
            logging.error(f"Error processing file {file_to_process}: {e}")

    if overall_progress:
        overall_progress.finish()  # Main summary will be printed below

    success_rate = (successful_files / total_files_to_process) * 100 if total_files_to_process > 0 else 0
    logging.info(f"Extraction complete: {successful_files}/{total_files_to_process} files processed successfully ({success_rate:.1f}%)")


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
    logger.debug(f"BYTE_RECOVERY_PATHS: Received output_path: {output_path}")  # LOGGING ADDED

    # Create recovery output directory
    # Example: output_path = "output/extracted", f = "input/dcm.pbd"
    # recovery_dir = "output/extracted/recovery/dcm.pbd"
    recovery_dir = os.path.join(output_path, "recovery", os.path.basename(f))
    logger.debug(f"BYTE_RECOVERY_PATHS: Intended recovery_dir: {recovery_dir}")  # LOGGING ADDED

    try:  # LOGGING ADDED - try/except around makedirs
        os.makedirs(recovery_dir, exist_ok=True)
        logger.debug(f"BYTE_RECOVERY_PATHS: os.makedirs called for {recovery_dir}. Exists now: {os.path.exists(recovery_dir)}")  # LOGGING ADDED
    except Exception as e_mkdir:
        logger.error(f"BYTE_RECOVERY_PATHS: Exception during os.makedirs for {recovery_dir}: {e_mkdir}")
        return False  # Cannot proceed if directory creation fails critically

    # Open file in binary mode
    with open(f, "rb") as file:
        file_data = file.read()
        file_size = len(file_data)

        # Create progress tracker
        progress = TqdmProgressTracker(
            total=file_size,
            description="Byte-level recovery scan",
            unit="bytes",
        )

        # Search for DAT blocks
        recovered_count = 0
        for i in range(0, file_size - 8):
            # Update progress every 10MB
            if i % (10 * 1024 * 1024) == 0:
                progress.update(i)

            # Check for DAT marker
            if file_data[i:i + 4] == b'DAT\0' or file_data[i:i + 4] == b'DAT*':
                try:
                    # Try both ASCII and Unicode modes
                    unicode_mode = file_data[i:i + 4] == b'DAT*'

                    # Read size (assuming next 4 bytes are size)
                    size = int.from_bytes(file_data[i + 4:i + 8], byteorder='little')

                    # Sanity check on size
                    if 0 < size < 10 * 1024 * 1024:  # Max 10MB chunk
                        # Extract the data block
                        data_block = file_data[i:i + 8 + size]

                        # Save recovered block
                        recovery_file = os.path.join(recovery_dir, f"recovered_block_{i:08x}.dat")
                        with open(recovery_file, "wb") as out_file:
                            out_file.write(data_block)

                        # Try to detect content type
                        content = file_data[i + 8:i + 8 + size]
                        if len(content) > 0:
                            # Check if it's text
                            try:
                                if unicode_mode:
                                    text = content.decode('utf-16-le', errors='ignore')
                                else:
                                    text = content.decode('latin1', errors='ignore')

                                # If it looks like PowerBuilder source code, save it
                                if any(marker in text for marker in ["$PBExportHeader", "SQLCA", "global type", "type", "forward"]):
                                    text_file = os.path.join(recovery_dir, f"recovered_source_{i:08x}.txt")
                                    with open(text_file, "w", encoding="utf-8") as out_file:
                                        out_file.write(text)

                                    # Count as recovery
                                    recovered_count += 1
                            except:
                                pass

                except Exception:
                    # Silently continue on errors
                    pass

        # Finalize progress
        progress.update(file_size)
        progress.finish()

        logger.info(f"Byte-level recovery complete. Recovered {recovered_count} potential source files")
        return recovered_count > 0