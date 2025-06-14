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
                logger.debug(f"{file_path.name}: No MZ signature found.")
                return False

            # Read the offset to PE signature (e_lfanew)
            f.seek(0x3C)
            pe_offset_bytes = f.read(4)
            if len(pe_offset_bytes) < 4:
                logger.debug(f"{file_path.name}: Could not read PE signature offset.")
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
        logger.exception(f"IOError while checking PE file {file_path.name}: {e}")
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


def find_and_extract_pbds_from_pe(
    pe_file_path: str | Path,
    output_base_dir: str | Path,
    silent_progress: bool = True,
) -> int:
    """Detects and extracts embedded PBDs from a PE file.

    Args:
        pe_file_path: Path to the PE file.
        output_base_dir: Base directory where extracted PBDs will be saved
                         (in subdirectories named after the PE file and PBD offset).
        silent_progress: If True, suppress progress bars during extraction.

    Returns:
        The number of PBDs successfully found and extracted.
    """
    # Lazy import to avoid circular dependency
    from extract.pbd.exceptions import PbdError
    from extract.pbd.extraction.library import Library

    pe_file_path = Path(pe_file_path)
    output_base_dir = Path(output_base_dir)

    if not is_pe_file(pe_file_path):
        logger.info(
            f"{pe_file_path.name} is not a PE file or could not be read. Skipping."
        )
        return 0

    logger.info(f"Scanning PE file {pe_file_path.name} for embedded PBDs...")
    extracted_pbd_count = 0

    try:
        with open(pe_file_path, "rb") as pe_file_handle:
            pbd_header_infos = find_pbd_header_signatures_in_file(pe_file_handle)

            if not pbd_header_infos:
                logger.info(f"No PBD header signatures found in {pe_file_path.name}.")
                return 0

            logger.info(
                f"Found {len(pbd_header_infos)} potential PBD header(s) in {pe_file_path.name}."
            )

            pe_file_handle.seek(0, os.SEEK_END)
            pe_file_size = pe_file_handle.tell()

            for pbd_offset, is_unicode in pbd_header_infos:
                logger.info(
                    f"Attempting to process potential PBD at offset {pbd_offset} (unicode: {is_unicode}) in {pe_file_path.name}."
                )

                # Create a subdirectory for this specific embedded PBD
                pbd_out_dir_name = f"{pe_file_path.stem}_offset_{pbd_offset}"
                pbd_output_path = output_base_dir / pe_file_path.name / pbd_out_dir_name
                pbd_output_path.mkdir(parents=True, exist_ok=True)

                temp_pbd_file: Path | None = None
                try:
                    # Carve out the PBD data from the PE file
                    # From pbd_offset to the end of the PE file
                    # This is a simplification; ideally, we'd parse PE sections to find PBD end
                    pe_file_handle.seek(pbd_offset)
                    pbd_data_chunk = pe_file_handle.read(pe_file_size - pbd_offset)

                    if not pbd_data_chunk:
                        logger.warning(
                            f"Could not read PBD data chunk at offset {pbd_offset} in {pe_file_path.name}."
                        )
                        continue

                    # Save the chunk to a temporary file to be processed by Library
                    with tempfile.NamedTemporaryFile(
                        delete=False,
                        suffix=".pbd",
                        prefix=f"embedded_{pe_file_path.stem}_",
                    ) as tmp_file:
                        tmp_file.write(pbd_data_chunk)
                        temp_pbd_file = Path(tmp_file.name)

                    logger.debug(
                        f"Carved PBD data from offset {pbd_offset} of {pe_file_path.name} to temporary file {temp_pbd_file}."
                    )

                    # Attempt to initialize Library with the temporary PBD file
                    try:
                        with Library(temp_pbd_file) as lib:
                            logger.info(
                                f"Successfully initialized Library for PBD data from offset {pbd_offset} in {pe_file_path.name} (temp file: {temp_pbd_file.name})."
                            )
                            logger.info(
                                f"Found {len(lib)} entries. Extracting to {pbd_output_path}"
                            )
                            lib.extract_all(
                                output_dir=pbd_output_path,
                                silent_progress=silent_progress,
                            )
                            extracted_pbd_count += 1
                            logger.info(
                                f"Successfully extracted PBD from offset {pbd_offset} of {pe_file_path.name} to {pbd_output_path}."
                            )
                    except PbdError as e:
                        logger.warning(
                            f"Failed to process PBD data from offset {pbd_offset} in {pe_file_path.name} (using temp file {temp_pbd_file.name if temp_pbd_file else 'N/A'}). Error: {e}"
                        )
                    except Exception as e:
                        logger.error(
                            f"Unexpected error processing PBD data from offset {pbd_offset} in {pe_file_path.name} (using temp file {temp_pbd_file.name if temp_pbd_file else 'N/A'}). Error: {e}",
                            exc_info=True,
                        )

                finally:
                    if temp_pbd_file and temp_pbd_file.exists():
                        try:
                            os.unlink(temp_pbd_file)
                            logger.debug(
                                f"Cleaned up temporary PBD file: {temp_pbd_file}"
                            )
                        except OSError as e_unlink:
                            logger.exception(
                                f"Error deleting temporary PBD file {temp_pbd_file}: {e_unlink}"
                            )

    except OSError as e:
        logger.exception(
            f"IOError while processing PE file {pe_file_path.name} for embedded PBDs: {e}"
        )
        return extracted_pbd_count  # Return count so far
    except Exception as e:
        logger.error(
            f"Unexpected error while processing PE file {pe_file_path.name} for embedded PBDs: {e}",
            exc_info=True,
        )
        return extracted_pbd_count  # Return count so far

    if extracted_pbd_count > 0:
        logger.info(
            f"Successfully extracted {extracted_pbd_count} embedded PBD(s) from {pe_file_path.name}."
        )
    else:
        logger.info(
            f"No PBDs were successfully extracted from {pe_file_path.name} (though headers might have been found)."
        )

    return extracted_pbd_count
