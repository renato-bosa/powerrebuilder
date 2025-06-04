"""Provides file scanning capabilities to find PBD/PBL structure signatures."""
import logging
from collections import Counter
from pathlib import Path
from typing import BinaryIO

from .constants import SIGNATURES as BASE_SIGNATURES

logger = logging.getLogger(__name__)

# Define known signatures as bytes - extending the base signatures with Unicode variants
SIGNATURES = {
    "ASCII_HDR": BASE_SIGNATURES['HDR'],
    "UNICODE_HDR": b"H\0D\0R\0*\0",  # Standard Unicode header signature 'HDR*'
    "ASCII_NOD": BASE_SIGNATURES['NOD'],
    "UNICODE_NOD": b"N\0O\0D\0*\0",
    "ASCII_DAT": BASE_SIGNATURES['DAT'],
    "UNICODE_DAT": b"D\0A\0T\0 \0",  # D\0A\0T\0 followed by space\0
    "ASCII_ENT": BASE_SIGNATURES['ENT'],
    "UNICODE_ENT": b"E\0N\0T\0*\0",
    "ASCII_FRE": BASE_SIGNATURES['FRE'],
    # Unicode FRE* might be more complex due to encoding of FRE*
}

EXPECTED_BLOCK_SIZES = {256, 512, 1024}  # Common PBD block sizes


def scan_for_signatures(file_path_or_handle: str | Path | BinaryIO, chunk_size: int = 1024 * 1024) -> dict[str, list[int]]:
    """Scans a file or an open file handle for known PBD/PBL signatures and returns their offsets.

    Args:
        file_path_or_handle: Path to the PBD/PBL file or an open BinaryIO handle.
        chunk_size: Size of chunks to read from the file (in bytes).

    Returns:
        A dictionary where keys are signature names (e.g., "ASCII_HDR")
        and values are lists of byte offsets where these signatures were found.
    """
    results: dict[str, list[int]] = {sig_name: [] for sig_name in SIGNATURES}

    input_is_handle = hasattr(file_path_or_handle, 'seek') and hasattr(file_path_or_handle, 'read')
    file_to_log = str(file_path_or_handle) if not input_is_handle else f"<handle at {hex(id(file_path_or_handle))}>"

    try:
        f: BinaryIO
        close_on_exit = False
        original_handle_pos: int | None = None

        if input_is_handle:
            f = file_path_or_handle  # type: ignore
            if not f.seekable() or not f.readable():
                logger.error(f"Provided file handle for {file_to_log} is not seekable or readable.")
                return results
            original_handle_pos = f.tell()
            f.seek(0)  # Start scanning from the beginning of the provided handle
        else:
            path_obj = Path(file_path_or_handle)
            if not path_obj.exists() or not path_obj.is_file():
                logger.error(f"File not found or is not a file: {path_obj}")
                return results
            f = open(path_obj, "rb")
            close_on_exit = True
            file_to_log = str(path_obj)  # Use actual path for logging if opened here

        file_offset = 0  # Relative to the start of scanning (which is start of handle/file)
        overlap_size = max(len(sig) for sig in SIGNATURES.values()) - 1
        overlap_size = max(overlap_size, 0)

        buffer = b""

        while True:
            current_chunk = f.read(chunk_size)
            if not current_chunk:
                break

            search_area = buffer + current_chunk

            for sig_name, sig_bytes in SIGNATURES.items():
                start_index_in_search_area = 0
                while True:
                    found_pos_in_search_area = search_area.find(sig_bytes, start_index_in_search_area)
                    if found_pos_in_search_area == -1:
                        break

                    # global_offset is from the start of where f is currently pointing (which is 0 if we seek(0))
                    # file_offset tracks how much we've read from f in total for chunks
                    # buffer comes from previous chunk
                    # global_signature_offset = (file_offset when buffer was formed) + found_pos_in_search_area
                    # simpler: the file_offset for the start of the search_area content is `file_offset - len(buffer)`
                    global_signature_offset = (file_offset - len(buffer)) + found_pos_in_search_area

                    if not results[sig_name] or results[sig_name][-1] != global_signature_offset:
                        results[sig_name].append(global_signature_offset)

                    start_index_in_search_area = found_pos_in_search_area + 1

            file_offset += len(current_chunk)  # file_offset is now the end of current_chunk relative to start of scan

            if len(search_area) >= overlap_size:  # search_area, not current_chunk for buffer source
                buffer = search_area[-overlap_size:]
            else:
                buffer = search_area  # Whole search_area becomes buffer if it's too small

        if input_is_handle and original_handle_pos is not None:
            f.seek(original_handle_pos)  # Restore original position if we used a provided handle
        if close_on_exit:
            f.close()

    except FileNotFoundError:  # Should be caught by pre-check if path_obj used
        logger.error(f"Scanner: File not found {file_to_log}")
    except Exception as e:
        logger.error(f"Error scanning file/handle {file_to_log}: {e}", exc_info=True)
        # If we opened the file, try to close it even on error
        if close_on_exit and 'f' in locals() and not f.closed:
            f.close()
        # If it was a passed handle, and we can still seek, try to restore original position
        elif input_is_handle and original_handle_pos is not None and 'f' in locals() and f.seekable():
            try:
                f.seek(original_handle_pos)
            except Exception as e_seek_restore:
                logger.error(f"Could not restore original position of handle for {file_to_log} after error: {e_seek_restore}")

    for sig_name in results:
        results[sig_name].sort()
        if results[sig_name]:
            unique_offsets = []
            last_offset = -1
            for offset in results[sig_name]:
                if offset != last_offset:
                    unique_offsets.append(offset)
                    last_offset = offset
            results[sig_name] = unique_offsets

    return results


def detect_block_size_from_dat_spacing(
    file_path_or_handle: str | Path | BinaryIO,
    min_occurrences_for_mode: int = 3,  # Minimum times a spacing must occur to be considered reliable
) -> int | None:
    """Attempts to detect the PBD block size by analyzing the modal spacing
    between DAT* signatures.

    Args:
        file_path_or_handle: Path to the PBD/PBL file or an open BinaryIO handle.
        min_occurrences_for_mode: The minimum number of times a spacing must be observed
                                   to be considered a reliable mode.

    Returns:
        The detected block size (e.g., 256, 512, 1024) if a reliable mode is found
        among expected sizes, otherwise None.
    """
    logger.debug(f"Attempting to detect block size from DAT spacing for {file_path_or_handle}")

    # It's important that scan_for_signatures correctly uses the handle or path
    # The current implementation of scan_for_signatures handles this.
    signatures_found = scan_for_signatures(file_path_or_handle)

    dat_offsets = sorted(
        set(signatures_found.get("ASCII_DAT", []) + signatures_found.get("UNICODE_DAT", [])),
    )

    if len(dat_offsets) < min_occurrences_for_mode + 1:  # Need at least min_occurrences + 1 DAT blocks to get min_occurrences spacings
        logger.debug(f"Not enough DAT signatures found ({len(dat_offsets)}) to reliably determine block size.")
        return None

    spacings = []
    for i in range(len(dat_offsets) - 1):
        spacing = dat_offsets[i + 1] - dat_offsets[i]
        if spacing > 0:  # Only consider positive spacings
            spacings.append(spacing)

    if not spacings:
        logger.debug("No valid spacings found between DAT signatures.")
        return None

    spacing_counts = Counter(spacings)
    if not spacing_counts:
        logger.debug("Could not count DAT spacings.")
        return None

    # Get the most common spacing and its count
    most_common_spacing, count = spacing_counts.most_common(1)[0]

    logger.debug(f"Most common DAT spacing: {most_common_spacing} (occurred {count} times)")

    if count >= min_occurrences_for_mode and most_common_spacing in EXPECTED_BLOCK_SIZES:
        logger.info(f"Detected block size: {most_common_spacing} based on DAT signature spacing.")
        return most_common_spacing
    if count < min_occurrences_for_mode:
        logger.debug(f"Most common spacing {most_common_spacing} occurred {count} times, which is less than minimum threshold {min_occurrences_for_mode}.")
    if most_common_spacing not in EXPECTED_BLOCK_SIZES:
        logger.debug(f"Most common spacing {most_common_spacing} is not one of the expected block sizes: {EXPECTED_BLOCK_SIZES}.")
    logger.info(f"Could not reliably determine block size from DAT spacing. Most common was {most_common_spacing} (x{count}).")
    return None


if __name__ == '__main__':
    # Example Usage (for testing this module directly)
    logging.basicConfig(level=logging.DEBUG)
    # Create a dummy PBD-like file for testing
    dummy_file_path = Path("dummy_test.pbd")
    with open(dummy_file_path, "wb") as f:
        f.write(b"\0" * 100)  # Padding
        f.write(b"HDR\0")  # ASCII HDR at 100
        f.write(b"\0" * 500)  # Padding
        f.write(b"N\0O\0D\0*\0")  # Unicode NOD at 604 (100+4+500)
        f.write(b"123NOD*abc")  # ASCII NOD at 612 (604+8)
        f.write(b"\0" * 1000)
        f.write(b"DAT \0\0\0")  # ASCII DAT at 1624 (612+7+1000)
        f.write(b"H\0D\0R\0*\0")  # Unicode HDR at 1631
        f.write(b"\0" * 2000)  # More padding to test chunking
        f.write(b"N\0O\0D\0*\0")  # Unicode NOD at 3639 (1631+8+2000)

    found_signatures = scan_for_signatures(dummy_file_path)
    for _sig_type, offsets in found_signatures.items():
        if offsets:
            pass

    detected_bs = detect_block_size_from_dat_spacing(dummy_file_path)

    # Test with a handle
    with open(dummy_file_path, "rb") as f_handle:
        detected_bs_handle = detect_block_size_from_dat_spacing(f_handle)

    dummy_file_path.unlink()  # Clean up dummy file
