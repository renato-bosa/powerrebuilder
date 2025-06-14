"""Utilities for extracting embedded resources like images from PBD objects."""

import logging
import struct  # For parsing headers
from pathlib import Path

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
                    data
                ):  # ICONDIRENTRY is 16 bytes
                    return None  # Not enough data for all directory entries

                # entry_width = data[current_dir_entry_offset]
                # entry_height = data[current_dir_entry_offset+1]
                # entry_bpp = struct.unpack_from('<H', data, current_dir_entry_offset + 6)[0]
                img_size_bytes = struct.unpack_from(
                    "<I", data, current_dir_entry_offset + 8
                )[0]
                img_offset_bytes = struct.unpack_from(
                    "<I", data, current_dir_entry_offset + 12
                )[0]

                max_end_offset = max(
                    max_end_offset, offset + img_offset_bytes + img_size_bytes
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
        "ext": ".bmp",
        "name": "BMP",
        "get_size": get_bmp_size,
        "min_size": 54,
    },  # Min BMP header size
    ICO_SIGNATURE: {
        "ext": ".ico",
        "name": "ICO",
        "get_size": get_ico_size,
        "min_size": 22,
    },  # 6 (header) + 16 (direntry)
    b"\\x89PNG\\r\\n\\x1a\\n": {
        "ext": ".png",
        "name": "PNG",
        "get_size": get_png_size,
        "min_size": 24,
    },  # 8 (sig) + IHDR chunk (12+header) + ...
    b"\\xFF\\xD8\\xFF": {
        "ext": ".jpg",
        "name": "JPG",
        "get_size": get_jpg_size,
        "min_size": 20,
    },  # SOI, APP0, ... EOI
    b"GIF87a": {
        "ext": ".gif",
        "name": "GIF",
        "get_size": get_gif_size,
        "min_size": 13,
    },  # Header + LSD
    b"GIF89a": {
        "ext": ".gif",
        "name": "GIF",
        "get_size": get_gif_size,
        "min_size": 13,
    },  # Header + LSD
}


def extract_embedded_images(
    data_bytes: bytes,
    base_filename: str,
    output_resource_dir: Path,
) -> list[Path]:
    """Scans data_bytes for known image signatures and attempts to extract them
    by parsing their headers to determine size where possible.

    Args:
        data_bytes: The byte content to scan (e.g., raw_binary_content of a PbdObject).
        base_filename: A base name for the extracted files (e.g., object_name).
        output_resource_dir: The directory to save extracted image files.

    Returns:
        A list of paths to the successfully extracted image files.
    """
    extracted_files: list[Path] = []
    if not data_bytes:
        return extracted_files

    output_resource_dir.mkdir(parents=True, exist_ok=True)
    processed_offsets = set()  # To avoid re-processing if signatures overlap

    # Iterate through the data to find all potential starting points of images
    # This allows handling of overlapping signatures if one is a false positive or part of another

    potential_images: list[
        tuple[int, dict, int]
    ] = []  # (start_offset, image_info, signature_length)

    # First pass: identify all signature occurrences
    # We search from the beginning each time for each signature type
    # This is less efficient than a single pass with Aho-Corasick or similar,
    # but simpler for a few signatures.
    for sig_bytes, img_info in SIGNATURE_MAP.items():
        start_search_idx = 0
        while start_search_idx < len(data_bytes):
            found_at = data_bytes.find(sig_bytes, start_search_idx)
            if found_at == -1:
                break
            potential_images.append((found_at, img_info, len(sig_bytes)))
            start_search_idx = (
                found_at + 1
            )  # Look for next occurrence of *this* signature

    # Sort potential images by their start offset
    potential_images.sort(key=lambda x: x[0])

    image_file_idx = 0

    # Second pass: attempt to carve and save valid images
    current_data_offset = 0
    while current_data_offset < len(data_bytes):
        next_image_to_process: tuple[int, dict, int] | None = None

        # Find the earliest potential image starting at or after current_data_offset
        for img_start, img_info, sig_len in potential_images:
            if img_start >= current_data_offset and img_start not in processed_offsets:
                next_image_to_process = (img_start, img_info, sig_len)
                break

        if not next_image_to_process:
            break  # No more images to process

        start_of_image, image_type_info, signature_len = next_image_to_process
        image_name = image_type_info["name"]
        image_ext = image_type_info["ext"]
        get_size_func = image_type_info.get("get_size")
        min_img_size = image_type_info.get("min_size", signature_len)

        logger.debug(
            f"Potential {image_name} signature found at offset {start_of_image}."
        )

        image_data = None
        determined_size = None

        if get_size_func:
            determined_size = get_size_func(data_bytes, start_of_image)
            if (
                determined_size
                and (start_of_image + determined_size) <= len(data_bytes)
                and determined_size >= min_img_size
            ):
                image_data = data_bytes[
                    start_of_image : start_of_image + determined_size
                ]
                logger.debug(
                    f"{image_name} at {start_of_image}: Determined size {determined_size} bytes."
                )
            elif determined_size:
                logger.warning(
                    f"{image_name} at {start_of_image}: Declared size {determined_size} is invalid or too small. Min expected {min_img_size}. Will skip or use fallback if any."
                )
                determined_size = None  # Invalidate to prevent using a bad size

        # Fallback or if no get_size_func: Try to cap by next known signature
        # This is a very rough heuristic.
        if not image_data:
            end_of_image_heuristic = len(data_bytes)
            # Find the *next different* signature to cap current image
            for next_sig_start, _, _ in potential_images:
                if (
                    next_sig_start > start_of_image
                ):  # Must be after current image's start
                    end_of_image_heuristic = min(end_of_image_heuristic, next_sig_start)
                    break  # Take the very next one as a boundary

            if (
                end_of_image_heuristic > start_of_image
                and (end_of_image_heuristic - start_of_image) >= min_img_size
            ):
                image_data = data_bytes[start_of_image:end_of_image_heuristic]
                logger.debug(
                    f"{image_name} at {start_of_image}: Using heuristic end at {end_of_image_heuristic}. Size: {len(image_data)}"
                )
            elif (
                not determined_size
            ):  # Only log if we didn't already warn about bad determined_size
                logger.warning(
                    f"{image_name} at {start_of_image}: Heuristic extraction resulted in too small size or no data. Min expected {min_img_size}. Skipping."
                )
                image_data = None

        if image_data:
            try:
                # Generate a unique filename
                img_filename_base = Path(base_filename).stem
                image_filename = f"{img_filename_base}_res_{image_file_idx}_{image_name.lower()}{image_ext}"
                image_path = output_resource_dir / image_filename

                with open(image_path, "wb") as f_img:
                    f_img.write(image_data)
                extracted_files.append(image_path)
                logger.info(
                    f"Extracted embedded {image_name} to {image_path} (bytes: {len(image_data)})"
                )
                image_file_idx += 1
                processed_offsets.add(start_of_image)  # Mark this offset as processed
                current_data_offset = start_of_image + len(
                    image_data
                )  # Continue scan from end of this image
            except OSError as e:
                logger.exception(
                    f"Failed to write extracted image {image_filename}: {e}"
                )
                processed_offsets.add(start_of_image)
                current_data_offset = (
                    start_of_image + signature_len
                )  # Try to skip problematic signature
            except Exception as e:  # General errors
                logger.exception(
                    f"Unexpected error extracting {image_name} from offset {start_of_image}: {e}"
                )
                processed_offsets.add(start_of_image)
                current_data_offset = start_of_image + signature_len
        else:
            # Could not extract this image, move past its signature to avoid infinite loops on bad sigs
            logger.debug(
                f"Could not extract valid data for {image_name} at offset {start_of_image}. Advancing past signature."
            )
            processed_offsets.add(start_of_image)
            current_data_offset = start_of_image + signature_len
            if current_data_offset <= start_of_image:  # Ensure progress
                current_data_offset = start_of_image + 1

    return extracted_files
