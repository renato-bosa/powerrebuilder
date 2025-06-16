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
) -> bool:
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
        logger.info(
            "Starting extraction of %s (%s bytes) -> %s", file_name, f"{file_size:,}", pbd_output_dir
        )

    try:
        logger.info("Attempt 1: Standard extraction for %s", file_name)
        extract_pbl(
            str(file_path_obj), str(pbd_output_dir), show_progress=show_progress
        )
        logger.info("Attempt 1: Standard extraction for %s SUCCEEDED.", file_name)
        return True
    except PbdError as pbd_e:
        logger.warning(
            "Attempt 1: Standard extraction for %s failed with PbdError: %s", file_name, pbd_e
        )
        logger.info("Proceeding to recovery attempts for %s.", file_name)
    except Exception as e:
        logger.error(
            "Attempt 1: Standard extraction for %s failed with an unexpected error: %s", file_name, e,
            exc_info=True,
        )
        logger.info("Proceeding to recovery attempts for %s.", file_name)

    try:
        file_bytes = retrieve_bytes_from_file(file_path_obj, 0, -1)
        if not file_bytes:
            logger.error(
                f"CRITICAL: Could not read file {file_name} for recovery attempts. Aborting for this file."
            )
            return False
    except OSError as e_io_fb:
        logger.error(
            f"CRITICAL: IOError reading file {file_name} for recovery: {e_io_fb}",
            exc_info=True,
        )
        return False
    except Exception as e_fb:
        logger.error(
            f"CRITICAL: Unexpected error reading file {file_name} for recovery: {e_fb}",
            exc_info=True,
        )
        return False

    recovery_unicode_flags = [False, True]

    for idx, unicode_attempt_flag in enumerate(recovery_unicode_flags):
        attempt_num = idx + 2
        logger.info(
            f"Attempt {attempt_num}: Recovery for {file_name} with explicit unicode_flag={unicode_attempt_flag} for header parsing."
        )
        try:
            # Import default block size
            DEFAULT_BLOCK_SIZE = 512  # Standard block size

            header = extract_pbl_header(
                file_bytes,
                block_size=DEFAULT_BLOCK_SIZE,
                file_path_for_error_log=str(file_path_obj),
            )
            logger.info(
                f"Attempt {attempt_num}: Header parsing for {file_name} (unicode_flag_override={unicode_attempt_flag}) SUCCEEDED. Header: unicode={header.is_unicode}, nod_offset={header.first_nod_offset}"
            )

            _extract_pbl_logic(
                file_bytes,
                header,
                str(pbd_output_dir),
                show_progress=False,
                file_name_for_logging=file_name,
            )
            logger.info(
                f"Attempt {attempt_num}: Recovery extraction for {file_name} (using unicode_flag_override={unicode_attempt_flag} for header) SUCCEEDED."
            )
            return True
        except PbdError as pbd_rec_e:
            logger.warning(
                f"Attempt {attempt_num}: Recovery for {file_name} (unicode_flag_override={unicode_attempt_flag} for header) failed: {pbd_rec_e}"
            )
        except Exception as e_rec:
            logger.error(
                f"Attempt {attempt_num}: Recovery for {file_name} (unicode_flag_override={unicode_attempt_flag} for header) failed with unexpected error: {e_rec}",
                exc_info=True,
            )

    # Attempt 4: Enhanced byte-level recovery
    if enable_byte_recovery:
        logger.info(
            f"Attempt 4: Enhanced byte-level recovery for {file_name}"
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
                    f"Attempt 4: Enhanced byte-level recovery for {file_name} SUCCEEDED."
                )
                return True
            else:
                logger.warning(
                    f"Attempt 4: Enhanced byte-level recovery for {file_name} found no recoverable data."
                )
        except Exception as e:
            logger.error(
                f"Attempt 4: Enhanced byte-level recovery for {file_name} failed with error: {e}",
                exc_info=True,
            )
    else:
        logger.info(
            "Attempt 4: Byte-level recovery skipped (enable_byte_recovery=False)."
        )

    logger.error(f"All extraction attempts for {file_name} failed.")
    return False


def extract_pbls(
    input_dir: str, output_dir: str, *, enable_byte_recovery: bool = False, progress=None
) -> None:
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
        if input_path.suffix.lower() in {
            ".win",
            ".srd",
            ".sru",
            ".srw",
            ".sra",
            ".srm",
            ".srs",
            ".men",
        }:
            # For source files, simply copy them
            try:
                # Create the destination file
                with open(input_path, encoding="utf-8", errors="ignore") as src:
                    content = src.read()

                # Extract just the filename
                filename = input_path.name
                dest_path = output_path / filename

                # Write the content with PB export header
                with open(dest_path, "w", encoding="utf-8") as dst:
                    dst.write(f"HA$PBExportHeader${filename}\\n")
                    dst.write("$PBExportComments$\\n")
                    dst.write(content)

                logging.info(f"Copied source file {input_path} to {dest_path}")
            except OSError as e_io:
                logging.error(f"Error copying file {input_path}: {e_io}", exc_info=True)
            except Exception as e:
                logging.error(
                    f"Unexpected error copying file {input_path}: {e}", exc_info=True
                )
        else:
            try:
                logging.debug(
                    f"Single file input {input_path} is not a direct source file type. Will be processed by main loop."
                )
            except Exception as e:
                logging.error(
                    f"Error during pre-check of single file {input_path}: {e}",
                    exc_info=True,
                )
    else:
        # Directory processing - look for PBL/PBD files
        pb_files = [f for f in input_path.glob("**/*.p[bl][dl]") if f.is_file()]

        if not pb_files:
            # If no PBL/PBD files, try to find source files directly
            source_files = []
            for ext in [".win", ".srd", ".sru", ".srw", ".sra", ".srm", ".srs", ".men"]:
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

    # Use Rich progress if provided, otherwise fall back to TQDM
    if progress:
        file_task = progress.file_progress.add_task(
            "Extracting files", total=total_files_to_process
        )
        overall_progress = None
    else:
        overall_progress = TqdmProgressTracker(
            total=total_files_to_process,
            description="Overall Extraction Progress",
            unit="files",
        )

    successful_files = 0
    for i, file_to_process in enumerate(files_to_process):
        if progress:
            progress.file_progress.update(
                file_task,
                completed=i,
                description=f"Extracting: {file_to_process.name}",
            )
        else:
            overall_progress.update(i, item_name=file_to_process.name)

        is_source_copy = file_to_process.suffix.lower() in {
            ".win",
            ".srd",
            ".sru",
            ".srw",
            ".sra",
            ".srm",
            ".srs",
            ".men",
        }

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

                with open(file_to_process, encoding="utf-8", errors="ignore") as src:
                    content = src.read()
                with open(dest_path, "w", encoding="utf-8") as dst:
                    dst.write(f"HA$PBExportHeader${file_to_process.name}\\n")
                    dst.write("$PBExportComments$\\n")
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

                logger.info(
                    f"Dispatching extraction for {file_to_process.name} to output directory {this_output_path}"
                )
                if extract_with_recovery(
                    str(file_to_process),
                    str(this_output_path),
                    show_progress=True,
                    enable_byte_recovery=enable_byte_recovery,
                ):
                    successful_files += 1
        except PbdError as e_pbd_proc:
            logging.error(
                f"PBD Error processing file {file_to_process}: {e_pbd_proc}",
                exc_info=True,
            )
        except OSError as e_io_proc:
            logging.error(
                f"IO Error processing file {file_to_process}: {e_io_proc}",
                exc_info=True,
            )
        except Exception as e:
            logging.error(
                f"Unexpected error processing file {file_to_process}: {e}",
                exc_info=True,
            )

    if overall_progress:
        overall_progress.finish()  # Main summary will be printed below
    elif progress:
        progress.file_progress.update(
            file_task,
            completed=total_files_to_process,
            description="Extraction complete",
        )

    success_rate = (
        (successful_files / total_files_to_process) * 100
        if total_files_to_process > 0
        else 0
    )
    logging.info(
        f"Extraction complete: {successful_files}/{total_files_to_process} files processed successfully ({success_rate:.1f}%)"
    )


def _perform_enhanced_byte_recovery(
    file_bytes: bytes,
    output_dir: str,
    file_name: str,
    show_progress: bool = True
) -> bool:
    """Perform enhanced byte-level recovery with multiple strategies.
    
    This implements several recovery strategies:
    1. Enhanced DAT block recovery with magic number detection
    2. Pattern-based object detection
    3. Header reconstruction
    4. Partial extraction of valid segments
    
    Args:
        file_bytes: The file content as bytes
        output_dir: Directory to write recovered files
        file_name: Name of the file being recovered
        show_progress: Whether to show progress
        
    Returns:
        True if any data was recovered, False otherwise
    """
    from extract.pbd.structures.enhanced_data_block import (
        extract_data_from_entry_enhanced,
        get_text_from_data,
    )
    from extract.pbd.structures.entry import PbEntryDefinition
    from extract.pbd.io.progress import ProgressTracker
    
    logger.info(f"Starting enhanced byte-level recovery for {file_name}")
    
    recovery_dir = Path(output_dir) / "recovery"
    recovery_dir.mkdir(parents=True, exist_ok=True)
    
    recovered_count = 0
    file_size = len(file_bytes)
    
    # Strategy 1: Try to recover individual DAT blocks
    logger.info("Strategy 1: Scanning for individual DAT blocks")
    dat_blocks_found = _scan_for_dat_blocks(file_bytes, recovery_dir, file_name)
    recovered_count += dat_blocks_found
    
    # Strategy 2: Pattern-based object detection
    logger.info("Strategy 2: Pattern-based PowerBuilder object detection")
    objects_found = _scan_for_pb_objects(file_bytes, recovery_dir, file_name)
    recovered_count += objects_found
    
    # Strategy 3: Try to reconstruct from ENT entries
    logger.info("Strategy 3: Scanning for ENT (entry) blocks")
    entries_found = _scan_for_ent_blocks(file_bytes, recovery_dir, file_name)
    recovered_count += entries_found
    
    # Strategy 4: Extract any remaining text segments
    logger.info("Strategy 4: Extracting remaining text segments")
    text_segments_found = _extract_text_segments(file_bytes, recovery_dir, file_name)
    recovered_count += text_segments_found
    
    if recovered_count > 0:
        logger.info(
            f"Enhanced byte-level recovery complete. "
            f"Recovered {recovered_count} objects/segments from {file_name}"
        )
        # Create a recovery summary
        summary_path = recovery_dir / "recovery_summary.txt"
        with open(summary_path, "w") as f:
            f.write(f"Recovery Summary for {file_name}\n")
            f.write(f"=" * 50 + "\n")
            f.write(f"Total objects/segments recovered: {recovered_count}\n")
            f.write(f"DAT blocks found: {dat_blocks_found}\n")
            f.write(f"PowerBuilder objects found: {objects_found}\n")
            f.write(f"ENT entries found: {entries_found}\n")
            f.write(f"Text segments found: {text_segments_found}\n")
        return True
    
    return False


def _scan_for_dat_blocks(file_bytes: bytes, recovery_dir: Path, file_name: str) -> int:
    """Scan for and recover individual DAT blocks."""
    count = 0
    dat_signatures = [b"DAT*", b"D\0A\0T\0"]
    
    for i in range(len(file_bytes) - 8):
        for sig in dat_signatures:
            if file_bytes[i:i+len(sig)] == sig:
                # Try to extract this DAT block
                try:
                    # Create a mock entry for the enhanced extractor
                    mock_entry = PbEntryDefinition(
                        objectname=f"recovered_dat_{i:08x}",
                        offset=i,
                        size=-1,  # Unknown size
                        raw_data=b""
                    )
                    
                    # Use enhanced extraction
                    from io import BytesIO
                    file_handle = BytesIO(file_bytes)
                    
                    blocks, is_partial = extract_data_from_entry_enhanced(
                        file_handle,
                        mock_entry,
                        is_unicode_file=(sig == b"D\0A\0T\0"),
                        block_size=512,
                        file_size=len(file_bytes)
                    )
                    
                    if blocks:
                        # Extract text content
                        text_content = get_text_from_data(
                            blocks, 
                            is_unicode_file=(sig == b"D\0A\0T\0")
                        )
                        
                        if text_content and len(text_content.strip()) > 10:
                            # Save recovered content
                            output_file = recovery_dir / f"dat_block_{i:08x}.txt"
                            with open(output_file, "w", encoding="utf-8") as f:
                                f.write(text_content)
                            count += 1
                            logger.debug(f"Recovered DAT block at offset 0x{i:08x}")
                            
                except Exception as e:
                    logger.debug(f"Failed to recover DAT block at 0x{i:08x}: {e}")
                    
                break  # Only process once per position
                
    return count


def _scan_for_pb_objects(file_bytes: bytes, recovery_dir: Path, file_name: str) -> int:
    """Scan for PowerBuilder object patterns."""
    count = 0
    
    # PowerBuilder object markers
    pb_markers = [
        b"$PBExportHeader$",
        b"global type",
        b"global function",
        b"forward prototypes",
        b"type variables",
        b"event variables",
        b"shared variables",
        b"instance variables",
        b"global variables",
    ]
    
    for marker in pb_markers:
        pos = 0
        while True:
            pos = file_bytes.find(marker, pos)
            if pos == -1:
                break
                
            # Try to extract a reasonable chunk around this marker
            start = max(0, pos - 100)  # Look back a bit
            end = min(len(file_bytes), pos + 10000)  # Look forward up to 10KB
            
            # Find the actual start/end of the object
            # Look for line boundaries
            while start > 0 and file_bytes[start] not in [b'\n'[0], b'\r'[0]]:
                start -= 1
            
            # Find end (look for next object or end patterns)
            object_end_markers = [
                b"$PBExportHeader$",
                b"\x00\x00\x00\x00",  # Null bytes often mark end
            ]
            
            actual_end = end
            for end_marker in object_end_markers:
                next_pos = file_bytes.find(end_marker, pos + len(marker), end)
                if next_pos != -1:
                    actual_end = min(actual_end, next_pos)
                    
            # Extract the segment
            segment = file_bytes[start:actual_end]
            
            # Try to decode
            text = None
            for encoding in ['utf-8', 'utf-16-le', 'latin1']:
                try:
                    text = segment.decode(encoding, errors='ignore')
                    # Basic validation
                    if text and len(text.strip()) > 50 and text.count('\x00') < len(text) // 10:
                        break
                    else:
                        text = None
                except:
                    text = None
                    
            if text:
                # Determine object type from content
                obj_type = "unknown"
                if "global type" in text:
                    obj_type = "datawindow" if "datawindow" in text else "window"
                elif "global function" in text:
                    obj_type = "function"
                elif "forward prototypes" in text:
                    obj_type = "object"
                    
                output_file = recovery_dir / f"pb_{obj_type}_{pos:08x}.txt"
                with open(output_file, "w", encoding="utf-8") as f:
                    f.write(text)
                count += 1
                logger.debug(f"Recovered PowerBuilder {obj_type} at offset 0x{pos:08x}")
                
            pos += 1
            
    return count


def _scan_for_ent_blocks(file_bytes: bytes, recovery_dir: Path, file_name: str) -> int:
    """Scan for ENT (entry) blocks that might contain object metadata."""
    count = 0
    ent_signatures = [b"ENT*", b"E\0N\0T\0"]
    
    for i in range(len(file_bytes) - 32):  # ENT blocks need more space
        for sig in ent_signatures:
            if file_bytes[i:i+len(sig)] == sig:
                try:
                    # ENT blocks contain entry metadata
                    # Try to parse basic structure
                    is_unicode = (sig == b"E\0N\0T\0")
                    
                    # Read potential object name (simplified parsing)
                    name_start = i + len(sig) + 16  # Skip some header bytes
                    name_end = name_start + 256  # Max name length
                    
                    name_bytes = file_bytes[name_start:name_end]
                    
                    # Try to extract name
                    if is_unicode:
                        null_pos = name_bytes.find(b"\x00\x00")
                        if null_pos > 0 and null_pos % 2 == 0:
                            name = name_bytes[:null_pos].decode('utf-16-le', errors='ignore')
                        else:
                            name = None
                    else:
                        null_pos = name_bytes.find(b"\x00")
                        if null_pos > 0:
                            name = name_bytes[:null_pos].decode('latin1', errors='ignore')
                        else:
                            name = None
                            
                    if name and len(name) > 3 and name.replace('_', '').replace('-', '').isalnum():
                        # Save entry metadata
                        output_file = recovery_dir / f"ent_metadata_{i:08x}_{name}.txt"
                        with open(output_file, "w", encoding="utf-8") as f:
                            f.write(f"ENT Entry Found\n")
                            f.write(f"Offset: 0x{i:08x}\n")
                            f.write(f"Object Name: {name}\n")
                            f.write(f"Unicode: {is_unicode}\n")
                        count += 1
                        logger.debug(f"Found ENT entry '{name}' at offset 0x{i:08x}")
                        
                except Exception as e:
                    logger.debug(f"Failed to parse ENT block at 0x{i:08x}: {e}")
                    
                break
                
    return count


def _extract_text_segments(file_bytes: bytes, recovery_dir: Path, file_name: str) -> int:
    """Extract any remaining significant text segments."""
    count = 0
    min_segment_size = 200  # Minimum size for a text segment to be considered
    
    # Look for runs of printable text
    i = 0
    while i < len(file_bytes):
        # Skip non-text bytes
        while i < len(file_bytes) and file_bytes[i] < 32 and file_bytes[i] not in [9, 10, 13]:
            i += 1
            
        if i >= len(file_bytes):
            break
            
        # Found start of potential text
        start = i
        
        # Find end of text run
        while i < len(file_bytes) and (32 <= file_bytes[i] <= 126 or file_bytes[i] in [9, 10, 13]):
            i += 1
            
        # Check if segment is significant
        if i - start >= min_segment_size:
            segment = file_bytes[start:i]
            
            # Try to decode
            text = None
            try:
                text = segment.decode('utf-8', errors='ignore')
                # Validate it looks like code/text
                if _looks_like_pb_code(text):
                    output_file = recovery_dir / f"text_segment_{start:08x}.txt"
                    with open(output_file, "w", encoding="utf-8") as f:
                        f.write(text)
                    count += 1
                    logger.debug(f"Extracted text segment at offset 0x{start:08x}")
            except:
                pass
                
        i += 1
        
    return count


def _looks_like_pb_code(text: str) -> bool:
    """Check if text looks like PowerBuilder code."""
    # Count indicators of PowerBuilder code
    indicators = [
        'function', 'subroutine', 'event', 'type', 'end',
        'if', 'then', 'else', 'for', 'next', 'do', 'loop',
        'select', 'case', 'choose', 'return', 'call',
        'string', 'integer', 'long', 'boolean', 'decimal',
        'window', 'datawindow', 'menu', 'object'
    ]
    
    text_lower = text.lower()
    indicator_count = sum(1 for ind in indicators if ind in text_lower)
    
    # Also check for common patterns
    has_parentheses = '(' in text and ')' in text
    has_quotes = '"' in text or "'" in text
    has_newlines = '\n' in text
    
    # Decision: looks like code if it has several indicators
    return indicator_count >= 3 and (has_parentheses or has_quotes) and has_newlines


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
