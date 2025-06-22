"""Enhanced image extraction from PowerBuilder objects.

This module provides improved image extraction capabilities, including:
- Support for more object types beyond .srm files
- Better image boundary detection
- Support for additional image formats
- Image validation and metadata extraction
"""

import logging
import struct
from pathlib import Path
from typing import Any

from common.constants import BUFFER_SIZE, HEADER_SIZE, STRING_TABLE_OFFSET

logger = logging.getLogger(__name__)


class EnhancedImageExtractor:
    """Enhanced image extraction from PowerBuilder files."""

    # Extended image signatures
    IMAGE_SIGNATURES = {
        # Standard formats
        b"\x89PNG\r\n\x1a\n": ("png", 8), b"GIF87a": ("gif", 6), b"GIF89a": ("gif", 6), b"\xFF\xD8\xFF": ("jpg", 3), b"BM": ("bmp", 2), b"\x00\x00\x01\x00": ("ico", 4), b"\x00\x00\x02\x00": ("cur", 4), # Additional formats
        b"RIFF": ("webp", 4), # WebP images
        b"II*\x00": ("tiff", 4), # TIFF little-endian
        b"MM\x00*": ("tiff", 4), # TIFF big-endian
        b"\x00\x00\x00\x0C": ("jp2", 4), # JPEG 2000

        # PowerBuilder specific
        b"PBM\x00": ("pbm", 4), # PowerBuilder bitmap
        b"PBI\x00": ("pbi", 4), # PowerBuilder icon
    }

    # Object types to search for images
    SEARCHABLE_OBJECT_TYPES = [
        ".srm", # Static Resource Module (menus)
        ".sru", # User objects
        ".srw", # Windows
        ".srd", # DataWindows
        ".src", # Structure
        ".srf", # Functions
        ".udo", # User defined objects
        ".win", # Window objects
        ".men", # Menu objects
        ".dwo", # DataWindow objects
    ]

    def __init__(self) -> None:




        """Initialize the enhanced image extractor."""
        self.extracted_images: dict[str, list[dict[str, Any]]] = {}

    def extract_images_from_file(self, file_path: Path, output_dir: Path | None = None) -> list[dict[str, Any]]:




        """Extract all images from a PowerBuilder file.

        Args:
            file_path: Path to the file to extract images from
            output_dir: Optional directory to save extracted images

        Returns:
            List of dictionaries containing image metadata
        """
        # Check if file type should be searched
        if not any(str(file_path).endswith(ext) for ext in self.SEARCHABLE_OBJECT_TYPES):
            logger.debug("Skipping %s - not a searchable object type", file_path)
            return []

        try:
            with open(file_path, "rb") as f:
                data = f.read()

            images = self.find_images_in_data(data, str(file_path))

            # Save images if output directory provided
            if output_dir and images:
                output_dir.mkdir(parents=True, exist_ok=True)
                for i, image_info in enumerate(images):
                    image_path = output_dir / f"{file_path.stem}_image_{i}.{image_info["format"]}"
                    image_path.write_bytes(image_info["data"])
                    image_info["saved_path"] = str(image_path)
                    logger.info("Saved image to %s", image_path)

            return images

        except Exception as e:
            logger.error("Failed to extract images from %s: %s", file_path, e)
            return []

    def find_images_in_data(self, data: bytes, source: str) -> list[dict[str, Any]]:




        """Find all images in binary data.

        Args:
            data: Binary data to search
            source: Source identifier

        Returns:
            List of image information dictionaries
        """
        images = []

        # Search for each image signature
        for signature, (format_name, sig_len) in self.IMAGE_SIGNATURES.items():
            offset = 0
            while True:
                # Find next occurrence of signature
                offset = data.find(signature, offset)
                if offset == -1:
                    break

                # Try to extract image
                image_data = self._extract_image(data, offset, format_name)
                if image_data:
                    # Validate image
                    if self._validate_image(image_data, format_name):
                        # Extract metadata
                        metadata = self._extract_image_metadata(image_data, format_name)

                        images.append({
                            "format": format_name, "offset": offset, "size": len(image_data), "data": image_data, "metadata": metadata, "source": source,
                        })

                        logger.debug("Found %s image at offset %s in %s", format_name, offset, source)

                    # Skip past this image
                    offset += len(image_data) if image_data else 1
                else:
                    offset += 1

        # Store results
        if images:
            self.extracted_images[source] = images
            logger.info("Extracted %s images from %s", len(images), source)

        return images

    def _extract_image(self, data: bytes, offset: int, format_name: str) -> bytes | None:




        """Extract a complete image from data.

        Args:
            data: Binary data
            offset: Starting offset of image
            format_name: Image format

        Returns:
            Complete image data or None
        """
        try:
            if format_name == "bmp":
                return self._extract_bmp(data, offset)
            elif format_name == "ico":
                return self._extract_ico(data, offset)
            elif format_name == "cur":
                return self._extract_cursor(data, offset)
            elif format_name == "png":
                return self._extract_png(data, offset)
            elif format_name == "gif":
                return self._extract_gif(data, offset)
            elif format_name == "jpg":
                return self._extract_jpeg(data, offset)
            else:
                # For unknown formats, try to find end by searching for next signature
                return self._extract_by_next_signature(data, offset)

        except Exception as e:
            logger.debug("Failed to extract %s at offset %s: %s", format_name, offset, e)
            return None

    def _extract_bmp(self, data: bytes, offset: int) -> bytes | None:




        """Extract BMP image."""
        if offset + 14 > len(data):
            return None

        # Read BMP header
        file_size = struct.unpack("<I", data[offset+2:offset+6])[0]

        if file_size > 0 and offset + file_size <= len(data):
            return data[offset:offset+file_size]

        return None

    def _extract_ico(self, data: bytes, offset: int) -> bytes | None:




        """Extract ICO image."""
        if offset + 6 > len(data):
            return None

        # Read ICO header
        num_images = struct.unpack("<H", data[offset+4:offset+6])[0]

        if num_images == 0 or num_images > 100:
            return None

        # Calculate total size
        header_size = 6 + (16 * num_images)
        if offset + header_size > len(data):
            return None

        # Read directory entries to find total size
        total_size = header_size
        for i in range(num_images):
            entry_offset = offset + 6 + (16 * i)
            if entry_offset + 16 > len(data):
                return None

            size = struct.unpack("<I", data[entry_offset+8:entry_offset+12])[0]
            total_size = max(total_size, struct.unpack("<I", data[entry_offset+12:entry_offset+16])[0] + size)

        if offset + total_size <= len(data):
            return data[offset:offset+total_size]

        return None

    def _extract_cursor(self, data: bytes, offset: int) -> bytes | None:




        """Extract cursor file (similar to ICO)."""
        return self._extract_ico(data, offset)

    def _extract_png(self, data: bytes, offset: int) -> bytes | None:




        """Extract PNG image."""
        # PNG ends with IEND chunk
        end_marker = b"IEND\xAE\x42\x60\x82"
        end_offset = data.find(end_marker, offset)

        if end_offset != -1:
            return data[offset:end_offset + len(end_marker)]

        return None

    def _extract_gif(self, data: bytes, offset: int) -> bytes | None:




        """Extract GIF image."""
        # GIF ends with trailer byte 0x3B
        end_offset = data.find(b"\x3B", offset + 13)  # Skip header

        if end_offset != -1:
            return data[offset:end_offset + 1]

        return None

    def _extract_jpeg(self, data: bytes, offset: int) -> bytes | None:




        """Extract JPEG image."""
        # JPEG ends with EOI marker 0xFFD9
        end_marker = b"\xFF\xD9"
        end_offset = data.find(end_marker, offset + 2)

        if end_offset != -1:
            return data[offset:end_offset + len(end_marker)]

        return None

    def _extract_by_next_signature(self, data: bytes, offset: int) -> bytes | None:




        """Extract image by finding next image signature."""
        # Find the next image signature
        min_next_offset = len(data)

        for signature, _ in self.IMAGE_SIGNATURES.items():
            next_offset = data.find(signature, offset + len(signature))
            if next_offset != -1 and next_offset < min_next_offset:
                min_next_offset = next_offset

        # Extract up to next signature or max reasonable size
        max_size = min(min_next_offset - offset, 10 * 1024 * 1024)  # Max 10MB
        if max_size > 100:  # Minimum reasonable image size
            return data[offset:offset + max_size]

        return None

    def _validate_image(self, data: bytes, format_name: str) -> bool:




        """Validate that extracted data is a valid image.

        Args:
            data: Image data
            format_name: Expected format

        Returns:
            True if valid, False otherwise
        """
        if not data or len(data) < 10:
            return False

        # Basic size validation
        if len(data) > 50 * 1024 * 1024:  # Max 50MB
            return False

        # Format-specific validation
        if format_name == "bmp":
            return data[:2] == b"BM"
        elif format_name == "png":
            return data[:8] == b"\x89PNG\r\n\x1a\n"
        elif format_name == "gif":
            return data[:6] in [b"GIF87a", b"GIF89a"]
        elif format_name == "jpg":
            return data[:3] == b"\xFF\xD8\xFF" and data[-2:] == b"\xFF\xD9"

        return True

    def _extract_image_metadata(self, data: bytes, format_name: str) -> dict[str, Any]:




        """Extract metadata from image data.

        Args:
            data: Image data
            format_name: Image format

        Returns:
            Dictionary of metadata
        """
        metadata = {"format": format_name}

        try:
            if format_name == "bmp" and len(data) >= 26:
                # Extract BMP dimensions
                metadata["width"] = struct.unpack("<I", data[18:22])[0]
                metadata["height"] = struct.unpack("<I", data[22:26])[0]
                metadata["bits_per_pixel"] = struct.unpack("<H", data[28:30])[0]

            elif format_name == "png" and len(data) >= 24:
                # Extract PNG dimensions from IHDR chunk
                metadata["width"] = struct.unpack(">I", data[16:20])[0]
                metadata["height"] = struct.unpack(">I", data[20:24])[0]

            elif format_name == "gif" and len(data) >= 10:
                # Extract GIF dimensions
                metadata["width"] = struct.unpack("<H", data[6:8])[0]
                metadata["height"] = struct.unpack("<H", data[8:10])[0]

            elif format_name == "ico" and len(data) >= 22:
                # Extract first icon dimensions
                metadata["width"] = data[6] or 256
                metadata["height"] = data[7] or 256
                metadata["color_count"] = data[8]

        except Exception as e:
            logger.debug("Failed to extract metadata for %s: %s", format_name, e)

        return metadata

    def generate_image_catalog(self) -> dict[str, Any]:




        """Generate a catalog of all extracted images.

        Returns:
            Dictionary containing image statistics and inventory
        """
        catalog = {
            "total_sources": len(self.extracted_images), "total_images": sum(len(imgs) for imgs in self.extracted_images.values()), "format_counts": {}, "sources": {}, "images_by_format": {}, "size_statistics": {
                "min": float("inf"), "max": 0, "total": 0,
            },
        }

        # Process all extracted images
        for source, images in self.extracted_images.items():
            catalog["sources"][source] = {
                "count": len(images), "formats": list(set(img["format"] for img in images)), "total_size": sum(img["size"] for img in images),
            }

            for image in images:
                format_name = image["format"]

                # Count formats
                catalog["format_counts"][format_name] = \
                    catalog["format_counts"].get(format_name, 0) + 1

                # Group by format
                if format_name not in catalog["images_by_format"]:
                    catalog["images_by_format"][format_name] = []
                catalog["images_by_format"][format_name].append({
                    "source": source, "offset": image["offset"], "size": image["size"], "metadata": image.get("metadata", {}),
                })

                # Update size statistics
                catalog["size_statistics"]["min"] = \
                    min(catalog["size_statistics"]["min"], image["size"])
                catalog["size_statistics"]["max"] = \
                    max(catalog["size_statistics"]["max"], image["size"])
                catalog["size_statistics"]["total"] += image["size"]

        # Calculate average size
        if catalog["total_images"] > 0:
            catalog["size_statistics"]["average"] = \
                catalog["size_statistics"]["total"] / catalog["total_images"]
        else:
            catalog["size_statistics"]["min"] = 0
            catalog["size_statistics"]["average"] = 0

        return catalog
