"""Provides file scanning capabilities to find PBD/PBL structure signatures."""

import logging
from pathlib import Path
from typing import BinaryIO, cast

from src.extract.pbd.constants import ALL_SIGNATURES as SIGNATURES

logger = logging.getLogger(__name__)


def _is_file_handle(obj: str | Path | BinaryIO) -> bool:
    """Check if object is a file handle."""
    return hasattr(obj, "seek") and hasattr(obj, "read")


def _get_file_handle(
    file_path_or_handle: str | Path | BinaryIO,
) -> tuple[BinaryIO, bool, int | None, str]:
    """Get file handle and metadata from path or handle.

    Returns:
    Tuple of (file_handle, should_close, original_position, log_name)
    """
    if _is_file_handle(file_path_or_handle):
        f = cast("BinaryIO", file_path_or_handle)
        log_name = f"<handle at {hex(id(f))}>"
        if not f.seekable() or not f.readable():
            raise ValueError(f"File handle {log_name} is not seekable or readable")
        original_pos = f.tell()
        f.seek(0)
        return f, False, original_pos, log_name
    path_obj = Path(file_path_or_handle)
    if not path_obj.exists() or not path_obj.is_file():
        raise FileNotFoundError(f"File not found or is not a file: {path_obj}")
    f = Path(path_obj).open("rb")
    return f, True, None, str(path_obj)


def _find_signature_in_buffer(
    search_area: bytes, sig_bytes: bytes, base_offset: int
) -> list[int]:
    """Find all occurrences of a signature in a buffer.

    Args:
    search_area: Buffer to search in
    sig_bytes: Signature bytes to find
    base_offset: Base offset to add to found positions

    Returns:
    List of global offsets where signature was found
    """
    offsets = []
    start_index = 0
    while True:
        found_pos = search_area.find(sig_bytes, start_index)
        if found_pos == -1:
            break
        offsets.append(base_offset + found_pos)
        start_index = found_pos + 1
    return offsets


def _scan_chunk_for_signatures(
    search_area: bytes, base_offset: int, results: dict[str, list[int]]
) -> None:
    """Scan a chunk for all signatures and update results.

    Args:
    search_area: Buffer to search in
    base_offset: Base offset for this chunk
    results: Results dictionary to update
    """
    for sig_name, sig_bytes in SIGNATURES.items():
        offsets = _find_signature_in_buffer(search_area, sig_bytes, base_offset)
        for offset in offsets:
            # Avoid duplicates
            if not results[sig_name] or results[sig_name][-1] != offset:
                results[sig_name].append(offset)


def _deduplicate_results(results: dict[str, list[int]]) -> None:
    """Remove duplicates and sort results in-place."""
    for sig_name in results:
        if results[sig_name]:
            # Sort and deduplicate
            results[sig_name].sort()
            unique_offsets = []
            last_offset = -1
            for offset in results[sig_name]:
                if offset != last_offset:
                    unique_offsets.append(offset)
                    last_offset = offset
            results[sig_name] = unique_offsets


def scan_for_signatures(
    file_path_or_handle: str | Path | BinaryIO, chunk_size: int = 1024 * 1024
) -> dict[str, list[int]]:
    """Scans a file or an open file handle for known PBD/PBL signatures and returns their offsets.

    Args:
        file_path_or_handle: Path to the PBD/PBL file or an open BinaryIO handle.
        chunk_size: Size of chunks to read from the file (in bytes).

    Returns:
        A dictionary where keys are signature names (e.g., "ASCII_HDR")
        and values are lists of byte offsets where these signatures were found.
    """
    results: dict[str, list[int]] = {sig_name: [] for sig_name in SIGNATURES}

    try:
        f, close_on_exit, original_pos, file_to_log = _get_file_handle(file_path_or_handle)
    except (FileNotFoundError, ValueError) as e:
        logger.error(str(e))
        return results

    try:
        # Calculate overlap size for chunk processing
        overlap_size = max(len(sig) for sig in SIGNATURES.values()) - 1
        overlap_size = max(overlap_size, 0)

        # Process file in chunks
        file_offset = 0
        buffer = b""

        while True:
            current_chunk = f.read(chunk_size)
            if not current_chunk:
                break

            search_area = buffer + current_chunk
            base_offset = file_offset - len(buffer)

            # Scan this chunk for all signatures
            _scan_chunk_for_signatures(search_area, base_offset, results)

            # Update file offset and buffer for next iteration
            file_offset += len(current_chunk)
            if len(search_area) >= overlap_size:
                buffer = search_area[-overlap_size:]
            else:
                buffer = search_area

    except Exception as e:
        logger.error("Error scanning file/handle %s: %s", file_to_log, e, exc_info=True)
    finally:
        # Clean up: restore position or close file
        try:
            if original_pos is not None and f.seekable():
                f.seek(original_pos)
            if close_on_exit:
                f.close()
        except Exception as e:
            logger.exception("Error during cleanup for %s: %s", file_to_log, e)

    # Deduplicate and sort results
    _deduplicate_results(results)

    return results
