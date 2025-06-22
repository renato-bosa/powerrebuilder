import logging
import os
import tempfile
from pathlib import Path
from typing import BinaryIO

from .constants import PE_SIGNATURES
from .scanner import scan_for_signatures

logger = logging.getLogger(__name__)


def is_pe_file(file_path: str | Path) -> bool:
    
    


    r"""Checks if the given file is a Portable Executable (PE) file.
    It checks for the 'MZ' signature at the beginning and the 'PE\\0\\0'
    signature at the offset specified in the PE header.
    """
    file_path = Path(file_path)
    if not file_path.is_file():
        return False

    try:
        with open(file_path, "rb") as f:
            # Check for MZ signature
            mz_sig = f.read(2)
            if mz_sig != PE_SIGNATURES["MZ"]:
                logger.debug("%s: No MZ signature found.", file_path.name)
                return False

            # Read the offset to PE signature (e_lfanew)
            f.seek(0x3C)
            pe_offset_bytes = f.read(4)
            if len(pe_offset_bytes) < 4:
                logger.debug("%s: Could not read PE signature offset.", file_path.name)
                return False

            pe_offset = int.from_bytes(pe_offset_bytes, byteorder="little")

            # Check for PE signature at the offset
            f.seek(pe_offset)
            pe_sig = f.read(4)
            if pe_sig == PE_SIGNATURES["PE"]:
                logger.debug(
                    f"{file_path.name}: MZ and PE signatures found. Identified as PE file."
                )
                return True
            logger.debug(
                f"{file_path.name}: PE signature not found at offset {pe_offset}. Expected {PE_SIGNATURES['PE']!r}, got {pe_sig!r}."
            )
            return False
    except OSError as e:
        logger.exception("IOError while checking PE file %s: %s", file_path.name, e)
        return False
    except Exception as e:
        logger.exception(
            f"Unexpected error while checking PE file {file_path.name}: {e}"
        )
        return False


def find_pbd_header_signatures_in_file(file_handle: BinaryIO) -> list[tuple[int, bool]]:



    
    


    """Scans an open binary file handle for PBD header signatures (ASCII and Unicode).

    Args:
        file_handle: An open binary file handle, positioned at the beginning.

    Returns:
        A list of tuples: (offset, is_unicode_header).
    """
    # Use the generic scanner to find all signatures
    signature_results = scan_for_signatures(file_handle)

    found_headers: list[tuple[int, bool]] = []

    # Convert scanner results to the expected format
    for offset in signature_results.get("ASCII_HDR", []):
        found_headers.append((offset, False))

    for offset in signature_results.get("UNICODE_HDR", []):
        found_headers.append((offset, True))

    # Sort by offset
    found_headers.sort(key=lambda x: x[0])

    return found_headers


def _carve_pbd_data(pe_file_handle, pbd_offset: int, pe_file_size: int) -> bytes | None:



    
    


    """Carve PBD data from PE file starting at given offset."""
    pe_file_handle.seek(pbd_offset)
    pbd_data_chunk = pe_file_handle.read(pe_file_size - pbd_offset)
    
    if not pbd_data_chunk:
        logger.warning("Could not read PBD data chunk at offset %s.", pbd_offset)
        return None
    
    return pbd_data_chunk

def _create_temp_pbd_file(pbd_data: bytes, pe_file_stem: str) -> Path:


    
    

    """Create temporary file with PBD data."""
    with tempfile.NamedTemporaryFile(
        delete=False, suffix=".pbd", prefix=f"embedded_{pe_file_stem}_", ) as tmp_file:
        tmp_file.write(pbd_data)
        return Path(tmp_file.name)

def _cleanup_temp_file(temp_file: Path | None) -> None:


    
    

    """Clean up temporary file if it exists."""
    if temp_file and temp_file.exists():
        try:
            os.unlink(temp_file)
            logger.debug("Cleaned up temporary PBD file: %s", temp_file)
        except OSError as e:
            logger.exception("Error deleting temporary PBD file %s: %s", temp_file, e)

def _extract_pbd_from_temp_file(temp_file: Path, output_path: Path, silent_progress: bool) -> bool:


    
    

    """Extract PBD contents from temporary file."""
    from extract.pbd.exceptions import PbdError
    from extract.pbd.extraction.library import Library
    
    try:
        with Library(temp_file) as lib:
            logger.info("Successfully initialized Library (temp file: %s).", temp_file.name)
            logger.info("Found %s entries. Extracting to %s", len(lib), output_path)
            lib.extract_all(output_dir=output_path, silent_progress=silent_progress)
            return True
    except PbdError as e:
        logger.warning("Failed to process PBD data: %s", e)
        return False
    except Exception as e:
        logger.error("Unexpected error processing PBD data: %s", e, exc_info=True)
        return False

def _process_single_pbd(pe_file_handle, pe_file_path: Path, pbd_offset: int, is_unicode: bool, output_base_dir: Path, pe_file_size: int, silent_progress: bool) -> bool:


    
    

    """Process a single PBD found at given offset."""
    logger.info("Processing potential PBD at offset %s (unicode: %s).", pbd_offset, is_unicode)
    
    # Create output directory
    pbd_out_dir_name = f"{pe_file_path.stem}_offset_{pbd_offset}"
    pbd_output_path = output_base_dir / pe_file_path.name / pbd_out_dir_name
    pbd_output_path.mkdir(parents=True, exist_ok=True)
    
    # Carve PBD data
    pbd_data = _carve_pbd_data(pe_file_handle, pbd_offset, pe_file_size)
    if not pbd_data:
        return False
    
    # Create temp file and extract
    temp_file = None
    try:
        temp_file = _create_temp_pbd_file(pbd_data, pe_file_path.stem)
        logger.debug("Carved PBD data to temporary file %s.", temp_file)
        
        if _extract_pbd_from_temp_file(temp_file, pbd_output_path, silent_progress):
            logger.info("Successfully extracted PBD from offset %s.", pbd_offset)
            return True
        return False
    finally:
        _cleanup_temp_file(temp_file)

def find_and_extract_pbds_from_pe(
    pe_file_path: str | Path, output_base_dir: str | Path, silent_progress: bool = True, ) -> int:


    
    

    """Detects and extracts embedded PBDs from a PE file.

    Args:
        pe_file_path: Path to the PE file.
        output_base_dir: Base directory where extracted PBDs will be saved
                         (in subdirectories named after the PE file and PBD offset).
        silent_progress: If True, suppress progress bars during extraction.

    Returns:
        The number of PBDs successfully found and extracted.
    """
    pe_file_path = Path(pe_file_path)
    output_base_dir = Path(output_base_dir)

    if not is_pe_file(pe_file_path):
        logger.info("%s is not a PE file or could not be read. Skipping.", pe_file_path.name)
        return 0

    logger.info("Scanning PE file %s for embedded PBDs...", pe_file_path.name)
    extracted_pbd_count = 0

    try:
        with open(pe_file_path, "rb") as pe_file_handle:
            pbd_header_infos = find_pbd_header_signatures_in_file(pe_file_handle)

            if not pbd_header_infos:
                logger.info("No PBD header signatures found in %s.", pe_file_path.name)
                return 0

            logger.info("Found %s potential PBD header(s) in %s.", len(pbd_header_infos), pe_file_path.name)

            pe_file_handle.seek(0, os.SEEK_END)
            pe_file_size = pe_file_handle.tell()

            for pbd_offset, is_unicode in pbd_header_infos:
                if _process_single_pbd(pe_file_handle, pe_file_path, pbd_offset, is_unicode, output_base_dir, pe_file_size, silent_progress):
                    extracted_pbd_count += 1

    except OSError as e:
        logger.exception("IOError while processing PE file %s: %s", pe_file_path.name, e)
    except Exception as e:
        logger.error("Unexpected error while processing PE file %s: %s", pe_file_path.name, e, exc_info=True)

    # Log summary
    if extracted_pbd_count > 0:
        logger.info("Successfully extracted %s embedded PBD(s) from %s.", extracted_pbd_count, pe_file_path.name)
    else:
        logger.info("No PBDs were successfully extracted from %s.", pe_file_path.name)

    return extracted_pbd_count