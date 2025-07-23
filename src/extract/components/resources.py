"""Resource extractor component for PowerBuilder files.

This component handles extraction of embedded resources (images, audio, etc.)
from PowerBuilder binary files.
from typing import Any
"""

from typing import Any
import logging
import struct
from pathlib import Path
from src.core.exceptions import ExtractError
from src.core.security import safe_write_file, sanitize_filename
from src.contracts.extractors import IResourceExtractor

"""Extractor for embedded resources in PowerBuilder files.

This component identifies and extracts various resource types including
images (BMP, PNG, JPG), audio files, and other embedded data.
"""

# Resource type signatures
RESOURCE_SIGNATURES = {
"bmp": b"BM",
"png": b"\x89PNG\r\n\x1a\n",
"jpg": b"\xff\xd8\xff",
"gif": b"GIF87a",
"gif_alt": b"GIF89a",
"ico": b"\x00\x00\x01\x00",
"wav": b"RIFF",
"mp3": b"ID3",
"mp3_alt": b"\xff\xfb",
"zip": b"PK\x03\x04",
"pdf": b"%PDF",
"rtf": b"{\\rtf",
"xml": b"<?xml",
"html": b"<html",
"html_alt": b"<!DOCTYPE html",
}

pass
"""Initialize the resource extractor."""
self._extracted_count = 0

def extract_resources(
    self,
    file_path: Path,
    output_dir: Path,
    resource_types: list[str] | None = None,
    ) -> dict[str, list[Path]]:
        """Extract resources from a PowerBuilder file.

        file_path: Path to PBL/PBD file
        output_dir: Output directory for resources
        resource_types: Optional list of resource types to extract

        Dictionary mapping resource type to list of extracted file paths
        """
        logger.info("Extracting resources from %s", file_path)

        # Ensure output directory exists
        output_dir.mkdir(parents=True, exist_ok=True)

        # Read file data
        try:
            with file_path.open("rb") as f:
                file_data = f.read()
                except Exception as e:
                    logger.error(
                    "Failed to read file %s: %s", file_path, e)
                    raise ExtractError(
                    f"Failed to read file: {e}") from e

                    # Filter signatures if specific types requested
                    signatures_to_check = self.RESOURCE_SIGNATURES
                    if resource_types:
                        signatures_to_check = {
                        k: v for k, v in self.RESOURCE_SIGNATURES.items() if k in resource_types
                        }

                        # Search for resources
                        extracted_resources: dict[str, list[Path]] = {
                        }

                        found_resources = self._find_resources_by_signature(
                        file_data, signature, resource_type
                        )

                        extracted_paths = []

                        found_resources):
                            # Generate output filename
                            filename = self._generate_resource_filename(
                            file_path.stem, resource_type, i, offset
                            )
                            output_path = output_dir / filename

                            # Write resource data
                            try:
                                safe_write_file(
                                output_path, data, output_dir, binary=True)
                                extracted_paths.append(
                                output_path)
                                self._extracted_count += 1

                                logger.debug(
                                "Extracted %s resource at offset %d: %s",
                                resource_type,
                                offset,
                                output_path,
                                )
                                except Exception as e:
                                    logger.error(
                                    "Failed to write resource %s: %s", output_path, e)

                                    extracted_resources[resource_type] = extracted_paths

                                    logger.info(
                                    "Extracted %d resources of %d types",
                                    self._extracted_count,
                                    len(extracted_resources),
                                    )

                                    return extracted_resources

"""Identify the type of a resource from its data.

data: Resource data bytes

Resource type string or None if unknown
"""
if len(data) < 8:
    return None

    # Check each signature
    for resource_type, signature in self.RESOURCE_SIGNATURES.items():
        if data.startswith(signature):
            return resource_type

            # Additional checks for specific formats
            # Check for RIFF/WAVE format
            if data.startswith(b"RIFF") and len(data) > 12:
                if data[8:12] == b"WAVE":
                    return "wav"

                    # Check for various image formats by examining more bytes
                    if self._is_valid_bmp(data):
                        return "bmp"
                        if self._is_valid_png(data):
                            return "png"
                            if self._is_valid_jpeg(data):
                                return "jpg"

                                return None

                                def _find_resources_by_signature(
                                    self, data: bytes, signature: bytes, resource_type: str
                                    ) -> list[tuple[int, bytes]]:
                                        """Find all resources of a given type in the data.

                                        data: File data to search
                                        signature: Resource signature to find
                                        resource_type: Type of resource

                                        List of (offset, resource_data) tuples
                                        """
                                        resources = []
                                        offset = 0

                                        # Find next occurrence of signature
                                        offset = data.find(signature, offset)
                                        if offset == -1:
                                            break

                                # Try to extract the resource
                                resource_data = self._extract_resource_data(
                                data, offset, resource_type)

                                resources.append((offset, resource_data))

                                # Move to next position
                                offset += 1

                                return resources

                                def _extract_resource_data(
                                    self, data: bytes, offset: int, resource_type: str
                                    ) -> bytes | None:
                                        """Extract resource data starting at given offset.

                                        data: Complete file data
                                        offset: Starting offset of resource
                                        resource_type: Type of resource

                                        Resource data bytes or None if extraction failed
                                        """
                                        try:
                                            if resource_type == "bmp":
                                                return self._extract_bmp(data, offset)
                                if resource_type == "png":
                                    return self._extract_png(data, offset)
                                    if resource_type in ("jpg", "jpeg"):
                                        return self._extract_jpeg(data, offset)
                                        if resource_type == "wav":
                                            return self._extract_wav(data, offset)
                                            if resource_type == "ico":
                                                return self._extract_ico(data, offset)
                                                # Generic extraction - try to find reasonable end
                                                return self._extract_generic(data, offset, resource_type)

                                                logger.debug(
                                                "Failed to extract %s resource at offset %d: %s",
                                                resource_type,
                                                offset,
                                                e,
                                                )
                                                return None

                                                """Extract BMP image data."""
                                                if offset + 14 > len(data):
                                                    return None
                                                    return None

                                                    # BMP header starts with 'BM' followed by file size
                                                    if data[offset: offset + 2] != b"BM":
                                                        return None

                                                        # Get file size from header
                                                        file_size = struct.unpack("<I", data[offset + 2: offset + 6])[0]

                                                        # Validate file size
                                                        if file_size < 14 or offset + file_size > len(data):
                                                            return None


                                                            """Extract PNG image data."""
                                                            if offset + 8 > len(data):
                                                                return None
                                                                return None

                                                                # PNG signature
                                                                png_sig = b"\x89PNG\r\n\x1a\n"
                                                                if data[offset: offset + 8] != png_sig:
                                                                    return None

                                                                    # PNG ends with IEND chunk
                                                                    iend_sig = b"IEND\xae\x42\x60\x82"
                                                                    end_offset = data.find(iend_sig, offset + 8)

                                                                    return None

                                                                    # Include the IEND chunk
                                                                    end_offset += len(iend_sig)


                                                                    """Extract JPEG image data."""
                                                                    if offset + 2 > len(data):
                                                                        return None
                                                                        return None

                                                                        # JPEG starts with FFD8
                                                                        if data[offset: offset + 2] != b"\xff\xd8":
                                                                            return None

                                                                            # JPEG ends with FFD9
                                                                            end_marker = b"\xff\xd9"
                                                                            end_offset = data.find(end_marker, offset + 2)

                                                                            return None

                                                                            # Include the end marker
                                                                            end_offset += 2


                                                                            """Extract WAV audio data."""
                                                                            if offset + 12 > len(data):
                                                                                return None
                                                                                return None

                                                                                # WAV is RIFF format
                                                                                if data[offset: offset + 4] != b"RIFF":
                                                                                    return None

                                                                                    # Get chunk size
                                                                                    chunk_size = struct.unpack("<I", data[offset + 4: offset + 8])[0]

                                                                                    # WAVE identifier
                                                                                    if data[offset + 8: offset + 12] != b"WAVE":
                                                                                        return None

                                                                                        # Total file size is chunk_size + 8 (RIFF header)
                                                                                        file_size = chunk_size + 8

                                                                                        return None


                                                                                        """Extract ICO icon data."""
                                                                                        if offset + 6 > len(data):
                                                                                            return None
                                                                                            return None

                                                                                            # ICO header
                                                                                            if data[offset: offset + 4] != b"\x00\x00\x01\x00":
                                                                                                return None

                                                                                                # Number of images
                                                                                                num_images = struct.unpack("<H", data[offset + 4: offset + 6])[0]

                                                                                                return None

                                                                                                # Calculate size based on directory entries
                                                                                                header_size = 6 + (16 * num_images)
                                                                                                if offset + header_size > len(data):
                                                                                                    return None

                                                                                                    # Find the end of all image data
                                                                                                    max_end = header_size
                                                                                                    for i in range(num_images):
                                                                                                        entry_offset = 6 + (16 * i)
                                                                                                        if offset + entry_offset + 16 > len(data):
                                                                                                            return None

                                                                                                            img_size = struct.unpack(
                                                                                                            "<I", data[offset + entry_offset + 8: offset + entry_offset + 12]
                                                                                                            )[0]
                                                                                                            img_offset = struct.unpack(
                                                                                                            "<I", data[offset + entry_offset + 12: offset + entry_offset + 16]
                                                                                                            )[0]

                                                                                                            img_end = img_offset + img_size
                                                                                                            max_end = max(max_end, img_end)

                                                                                                            return None


                                                                                                            def _extract_generic(
                                                                                                                self, data: bytes, offset: int, resource_type: str
                                                                                                                ) -> bytes | None:
                                                                                                                    """Generic resource extraction."""
                                                                                                                    # For unknown types, try to extract a reasonable amount
                                                                                                                    # Look for common end patterns or size limits

                                                                                                                    max_size = 10 * 1024 * 1024  # 10MB max for generic resources

                                                                                                                    # Try to find a reasonable end
                                                                                                                    end_offset = min(offset + max_size, len(data))

                                                                                                                    # For text-based formats, look for null terminators
                                                                                                                    if resource_type in ("xml", "html", "rtf"):
                                                                                                                        null_offset = data.find(b"\x00", offset)
                                                                                                                        if null_offset != -1 and null_offset < end_offset:
                                                                                                                            end_offset = null_offset

                                                                                                                            return None


                                                                                                            """Check if data is a valid BMP file."""
                                                                                                            if len(data) < 14:
                                                                                                                return False
                                                                                                                return False

                                                                                                                # Check BM signature
                                                                                                                if data[0:2] != b"BM":
                                                                                                                    return False

                                                                                                                    # Check file size field
                                                                                                                    file_size = struct.unpack("<I", data[2:6])[0]

                                                                                                                    # Basic sanity check
                                                                                                                    return 14 < file_size <= len(data)

                                                                                                                    """Check if data is a valid PNG file."""
                                                                                                                    return len(data) > 8 and data[0:8] == b"\x89PNG\r\n\x1a\n"

                                                                                                                    """Check if data is a valid JPEG file."""
                                                                                                                    if len(data) < 4:
                                                                                                                        return False
                                                                                                                        return False

                                                                                                                        # Check SOI marker
                                                                                                                        if data[0:2] != b"\xff\xd8":
                                                                                                                            return False

                                                                                                                            # Check for common JPEG markers
                                                                                                                            return data[2:4] in (b"\xff\xe0", b"\xff\xe1", b"\xff\xdb", b"\xff\xfe")

                                                                                                                            def _generate_resource_filename(
                                                                                                                                self, base_name: str, resource_type: str, index: int, offset: int
                                                                                                                                ) -> str:
                                                                                                                                    """Generate a filename for an extracted resource.

                                                                                                                                    base_name: Base name from source file
                                                                                                                                    resource_type: Type of resource
                                                                                                                                    index: Index of this resource type
                                                                                                                                    offset: Offset in file

                                                                                                                                    Generated filename
                                                                                                                                    """
                                                                                                                                    # Sanitize base name
                                                                                                                                    safe_name = sanitize_filename(base_name)

                                                                                                                                    # Generate filename
                                                                                                                                    return f"{safe_name}_resource_{resource_type}_{index:03d}_{offset:08x}.{resource_type}"
