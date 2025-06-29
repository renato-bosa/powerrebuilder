"""Utilities for extracting embedded resources like images from PBD objects."""

import logging
import struct  # For parsing headers
from pathlib import Path

from src.common.constants import BUFFER_SIZE, HEADER_SIZE, STRING_TABLE_OFFSET

logger = logging.getLogger(__name__)

# Common image signatures
BMP_SIGNATURE = b"BM"
ICO_SIGNATURE = b"\x00\x00\x01\x00"  # Icon File Signature
# PNG_SIGNATURE = b"\x89PNG\r\n\x1a\n"
# JPG_SIGNATURE = b"\xFF\xD8\xFF"

# Simple map of signature to file extension and a rough idea of min/max size or how to find end
# This is highly heuristic and will need refinement.


def get_bmp_size(data: bytes, offset: int) -> int | None: 




    if offset + 6 <= len(data):  # Ensure header for size is present
        try:
            return struct.unpack_from("<I", data, offset + 2)[0]
        except struct.error:
            return None
    return None


def get_ico_size(data: bytes, offset: int) -> int | None: 




    if offset + 6 <= len(data):  # Initial header: 2 reserved, 2 type, 2 count
        try:
            num_images = struct.unpack_from("<H", data, offset + 4)[0]
            if num_images == 0 or num_images > 255:  # Sanity check
                return None

            current_dir_entry_offset = offset + 6
            max_end_offset = offset

            for _ in range(num_images):
                if current_dir_entry_offset + 16 > len(
                    data,
                ):  # ICONDIRENTRY is 16 bytes
                    return None  # Not enough data for all directory entries

                # entry_width = data[current_dir_entry_offset]
                # entry_height = data[current_dir_entry_offset+1]
                # entry_bpp = struct.unpack_from('<H', data, current_dir_entry_offset + 6)[0]
                img_size_bytes = struct.unpack_from(
                    "<I", data, current_dir_entry_offset + 8,
                )[0]
                img_offset_bytes = struct.unpack_from(
                    "<I", data, current_dir_entry_offset + 12,
                )[0]

                max_end_offset = max(
                    max_end_offset, offset + img_offset_bytes + img_size_bytes,
                )
                current_dir_entry_offset += 16

            if max_end_offset > offset and max_end_offset <= len(data):
                return max_end_offset - offset  # Total size of the ICO structure
            return None  # Could not determine a valid size
        except struct.error:
            return None
    return None


def get_png_size(data: bytes, offset: int) -> int | None: 




    # PNG ends with IEND chunk: 8 bytes (4 length (0), 4 type "IEND", 4 CRC)
    # A more robust way is to parse chunks, but find IEND is a good heuristic
    # A simpler search for just IEND, then go back for length and forward for CRC.
    # For now, just find IEND signature.

    # Find IEND chunk: 4 bytes length (should be 0), 4 bytes 'IEND'
    # The search should start from offset + 8 (after PNG signature)
    idx = offset + 8
    while idx + 8 <= len(data):  # Need at least 8 bytes for a chunk (length + type)
        try:
            chunk_len = struct.unpack_from(">I", data, idx)[0]
            chunk_type = data[idx + 4 : idx + 8]

            if chunk_type == b"IEND":
                return (
                    (idx + 8 + chunk_len + 4) - offset
                )  # Total size: offset to IEND + IEND_header (8) + chunk_data_len (0) + CRC (4)

            idx += (
                4 + 4 + chunk_len + 4
            )  # Move to next chunk: len_field + type_field + data + crc
        except struct.error:
            return None  # Malformed chunk
        except IndexError:
            return None  # Data ended unexpectedly
    return None  # IEND not found


def get_jpg_size(data: bytes, offset: int) -> int | None: 




    # JPG ends with EOI marker FFD9
    eoi_marker = b"\\xFF\\xD9"
    # Search for EOI starting from offset + 2 (after SOI marker FFD8)
    idx = data.find(eoi_marker, offset + 2)
    if idx != -1:
        return (idx + 2) - offset  # Size is from start of JPG to end of EOI marker
    return None


def get_gif_size(data: bytes, offset: int) -> int | None: 




    # GIF ends with a trailer byte 0x3B
    # A more robust way is to parse blocks, but this is a common heuristic.
    # Search for trailer 0x3B, but need to ensure it's a valid GIF structure before that.
    # GIF header is 6 bytes ("GIF87a" or "GIF89a")
    # Logical Screen Descriptor is 7 bytes
    # Minimum size: 6 (header) + 7 (LSD) + ... + 1 (trailer)
    # This is tricky without more parsing. Let's assume if we find 0x3B, it's the end.
    # This needs to be cautious. A simple search for 0x3B might be too naive.
    # For now, we'll rely on the generic "next signature" capping.
    # A better GIF parser would read blocks (image descriptor, color table, data sub-blocks)
    # until the trailer 0x3B is encountered.

    # Heuristic: find 0x3B after a reasonable minimum size
    min_gif_body_size = 20  # GIF header(6) + LSD(7) + ImageDesc(9) + min LZW(2) = ~24
    if offset + min_gif_body_size > len(data):
        return None

    idx = offset + min_gif_body_size
    while idx < len(data):
        if data[idx] == 0x3B:  # GIF Trailer
            return (idx + 1) - offset
        idx += 1
    return None


SIGNATURE_MAP = {
    BMP_SIGNATURE: {
        "ext": ".bmp", "name": "BMP", "get_size": get_bmp_size, "min_size": 54, }, # Min BMP header size
    ICO_SIGNATURE: {
        "ext": ".ico", "name": "ICO", "get_size": get_ico_size, "min_size": 22, }, # 6 (header) + 16 (direntry)
    b"\\x89PNG\\r\\n\\x1a\\n": {
        "ext": ".png", "name": "PNG", "get_size": get_png_size, "min_size": 24, }, # 8 (sig) + IHDR chunk (12+header) + ...
    b"\\xFF\\xD8\\xFF": {
        "ext": ".jpg", "name": "JPG", "get_size": get_jpg_size, "min_size": 20, }, # SOI, APP0, ... EOI
    b"GIF87a": {
        "ext": ".gif", "name": "GIF", "get_size": get_gif_size, "min_size": 13, }, # Header + LSD
    b"GIF89a": {
        "ext": ".gif", "name": "GIF", "get_size": get_gif_size, "min_size": 13, }, # Header + LSD
}


def _find_image_signatures(data_bytes: bytes) -> list[tuple[int, dict, int]]:








    """Find all potential image signatures in data.

    Returns:
        List of (start_offset, image_info, signature_length) tuples
    """
    potential_images = []

    for sig_bytes, img_info in SIGNATURE_MAP.items():
        start_search_idx = 0
        while start_search_idx < len(data_bytes):
            found_at = data_bytes.find(sig_bytes, start_search_idx)
            if found_at == -1:
                break
            potential_images.append((found_at, img_info, len(sig_bytes)))
            start_search_idx = found_at + 1

    # Sort by start offset
    potential_images.sort(key=lambda x: x[0])
    return potential_images


def _extract_image_data(data_bytes: bytes, start_of_image: int, image_info: dict, potential_images: list[tuple[int, dict, int]]) -> bytes | None:








    """Extract image data from bytes.

    Args:
        data_bytes: Source data
        start_of_image: Start offset of image
        image_info: Image type information
        potential_images: List of all potential images for boundary detection

    Returns:
        Extracted image bytes or None
    """
    get_size_func = image_info.get("get_size")
    min_img_size = image_info.get("min_size", 1)
    image_name = image_info["name"]

    # Try to determine size using specific function
    if get_size_func:
        determined_size = get_size_func(data_bytes, start_of_image)
        if determined_size and _is_valid_image_size(data_bytes, start_of_image, determined_size, min_img_size):
            logger.debug(
                f"{image_name} at {start_of_image}: Determined size {determined_size} bytes.",
            )
            return data_bytes[start_of_image : start_of_image + determined_size]
        elif determined_size:
            logger.warning(
                f"{image_name} at {start_of_image}: Invalid size {determined_size}. Min expected {min_img_size}.",
            )

    # Fallback: use heuristic based on next signature
    return _extract_image_heuristic(data_bytes, start_of_image, image_info, potential_images)


def _is_valid_image_size(data_bytes: bytes, start: int, size: int, min_size: int) -> bool:








    """Check if image size is valid."""
    return (
        size >= min_size and
        (start + size) <= len(data_bytes)
    )


def _extract_image_heuristic(data_bytes: bytes, start_of_image: int, image_info: dict, potential_images: list[tuple[int, dict, int]]) -> bytes | None:








    """Extract image using heuristic (find next signature)."""
    min_img_size = image_info.get("min_size", 1)
    image_name = image_info["name"]

    # Find next signature as boundary
    end_of_image = len(data_bytes)
    for next_sig_start, _, _ in potential_images:
        if next_sig_start > start_of_image:
            end_of_image = min(end_of_image, next_sig_start)
            break

    size = end_of_image - start_of_image
    if size >= min_img_size:
        logger.debug(
            f"{image_name} at {start_of_image}: Using heuristic end at {end_of_image}. Size: {size}",
        )
        return data_bytes[start_of_image:end_of_image]

    logger.warning(
        f"{image_name} at {start_of_image}: Heuristic size {size} too small. Min expected {min_img_size}.",
    )
    return None


def _save_image_file(image_data: bytes, base_filename: str, image_info: dict, image_idx: int, output_dir: Path) -> Path | None:








    """Save image data to file.

    Returns:
        Path to saved file or None if failed
    """
    try:
        img_filename_base = Path(base_filename).stem
        image_name = image_info["name"]
        image_ext = image_info["ext"]

        image_filename = f"{img_filename_base}_res_{image_idx}_{image_name.lower()}{image_ext}"
        image_path = output_dir / image_filename

        with open(image_path, "wb") as f_img:
            f_img.write(image_data)

        logger.info(
            f"Extracted embedded {image_name} to {image_path} (bytes: {len(image_data)})",
        )
        return image_path

    except OSError as e:
        logger.exception("Failed to write extracted image: %s", e)
        return None
    except Exception as e:
        logger.exception("Unexpected error saving image: %s", e)
        return None


def extract_embedded_images(
    data_bytes: bytes, base_filename: str, output_resource_dir: Path, ) -> list[Path]:








    """Scans data_bytes for known image signatures and attempts to extract them
    by parsing their headers to determine size where possible.

    Args:
        data_bytes: The byte content to scan (e.g., raw_binary_content of a PbdObject).
        base_filename: A base name for the extracted files (e.g., object_name).
        output_resource_dir: The directory to save extracted image files.

    Returns:
        A list of paths to the successfully extracted image files.
    """
    if not data_bytes:
        return []

    output_resource_dir.mkdir(parents=True, exist_ok=True)

    # Find all potential images
    potential_images = _find_image_signatures(data_bytes)
    if not potential_images:
        return []

    extracted_files = []
    processed_offsets = set()
    image_file_idx = 0
    current_offset = 0

    # Process each potential image
    while current_offset < len(data_bytes):
        # Find next unprocessed image
        next_image = None
        for img_start, img_info, sig_len in potential_images:
            if img_start >= current_offset and img_start not in processed_offsets:
                next_image = (img_start, img_info, sig_len)
                break

        if not next_image:
            break

        start_offset, image_info, sig_len = next_image
        processed_offsets.add(start_offset)

        logger.debug(
            f"Potential {image_info["name"]} signature found at offset {start_offset}.",
        )

        # Extract image data
        image_data = _extract_image_data(data_bytes, start_offset, image_info, potential_images)

        if image_data:
            # Save image file
            saved_path = _save_image_file(image_data, base_filename, image_info, image_file_idx, output_resource_dir)
            if saved_path:
                extracted_files.append(saved_path)
                image_file_idx += 1
                current_offset = start_offset + len(image_data)
            else:
                current_offset = start_offset + sig_len
        else:
            logger.debug(
                f"Could not extract valid data for {image_info["name"]} at offset {start_offset}.",
            )
            current_offset = start_offset + sig_len

        # Ensure progress
        if current_offset <= start_offset:
            current_offset = start_offset + 1

    return extracted_files
