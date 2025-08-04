"""Resource extractor component for PowerBuilder files.

This component handles extraction of embedded resources (images, audio, etc.)
from PowerBuilder binary files.
"""

import logging
import struct
from pathlib import Path
from typing import Any

from src.contracts.extractors import IResourceExtractor
from src.core.exceptions import ExtractError
from src.core.security import safe_write_file, sanitize_filename

logger = logging.getLogger(__name__)


class ResourceExtractor(IResourceExtractor):
    """Extractor for embedded resources in PowerBuilder files.

    This component identifies and extracts various resource types including
    images (BMP, PNG, JPG), audio files, and other embedded data.
    """

    # Common resource signatures
    RESOURCE_SIGNATURES = {
        "bmp": b"BM",
        "png": b"\x89PNG\r\n\x1a\n",
        "jpg": b"\xff\xd8\xff",
        "gif": b"GIF89a",
        "ico": b"\x00\x00\x01\x00",
        "wav": b"RIFF",
        "mp3": b"ID3",
    }

    def __init__(self) -> None:
        """Initialize the resource extractor."""
        self._extracted_count = 0
        self._total_size = 0

    def extract_resources(
        self,
        file_path: Path,
        output_dir: Path,
        resource_types: list[str] | None = None,
    ) -> dict[str, list[Path]]:
        """Extract resources from a PowerBuilder file.

        Args:
            file_path: Path to PBL/PBD file
            output_dir: Output directory for resources
            resource_types: Optional list of resource types to extract

        Returns:
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
            logger.error("Failed to read file %s: %s", file_path, e)
            raise ExtractError(f"Failed to read file: {e}") from e

        # Filter signatures if specific types requested
        signatures_to_check = self.RESOURCE_SIGNATURES
        if resource_types:
            signatures_to_check = {
                k: v for k, v in self.RESOURCE_SIGNATURES.items() if k in resource_types
            }

        # Search for resources
        extracted_resources: dict[str, list[Path]] = {}

        for resource_type, signature in signatures_to_check.items():
            found_resources = self._find_resources_by_signature(
                file_data, signature, resource_type
            )

            extracted_paths = []

            for i, (offset, data) in enumerate(found_resources):
                # Generate output filename
                filename = self._generate_resource_filename(
                    file_path.stem, resource_type, i, offset
                )
                output_path = output_dir / filename

                # Write resource data
                try:
                    safe_write_file(output_path, data, output_dir, binary=True)
                    extracted_paths.append(output_path)
                    self._extracted_count += 1

                    logger.debug(
                        "Extracted %s resource at offset %d: %s",
                        resource_type,
                        offset,
                        output_path,
                    )
                except Exception as e:
                    logger.error("Failed to write resource %s: %s", output_path, e)

            if extracted_paths:
                extracted_resources[resource_type] = extracted_paths

        logger.info(
            "Extracted %d resources of %d types",
            self._extracted_count,
            len(extracted_resources),
        )

        return extracted_resources

    def _identify_resource_type(self, data: bytes) -> str | None:
        """Identify the type of a resource from its data.

        Args:
            data: Resource data bytes

        Returns:
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

        Args:
            data: File data to search
            signature: Resource signature to find
            resource_type: Type of resource

        Returns:
            List of (offset, resource_data) tuples
        """
        resources = []
        offset = 0

        while True:
            # Find next occurrence of signature
            pos = data.find(signature, offset)
            if pos == -1:
                break

            # Try to extract the resource
            resource_data = self._extract_resource_data(data, pos, resource_type)
            if resource_data:
                resources.append((pos, resource_data))
                offset = pos + len(resource_data)
            else:
                offset = pos + 1

        return resources

    def _extract_resource_data(
        self, data: bytes, offset: int, resource_type: str
    ) -> bytes | None:
        """Extract resource data starting at the given offset.

        Args:
            data: Full file data
            offset: Starting offset of resource
            resource_type: Type of resource

        Returns:
            Resource data or None if extraction failed
        """
        if resource_type == "bmp":
            return self._extract_bmp(data, offset)
        if resource_type == "png":
            return self._extract_png(data, offset)
        if resource_type == "jpg":
            return self._extract_jpeg(data, offset)
        if resource_type == "wav":
            return self._extract_wav(data, offset)
        # Default extraction - try to find resource boundary
        return self._extract_generic(data, offset)

    def _extract_bmp(self, data: bytes, offset: int) -> bytes | None:
        """Extract BMP image data."""
        if offset + 14 > len(data):
            return None

        # Read BMP header
        if data[offset : offset + 2] != b"BM":
            return None

        # Get file size from header
        try:
            file_size = struct.unpack("<I", data[offset + 2 : offset + 6])[0]
            if file_size == 0 or offset + file_size > len(data):
                # Try to calculate from image dimensions
                return self._extract_bmp_by_dimensions(data, offset)

            return data[offset : offset + file_size]
        except struct.error:
            return None

    def _extract_bmp_by_dimensions(self, data: bytes, offset: int) -> bytes | None:
        """Extract BMP by calculating size from dimensions."""
        if offset + 54 > len(data):  # Minimum BMP header size
            return None

        try:
            # Get image dimensions
            width = struct.unpack("<I", data[offset + 18 : offset + 22])[0]
            height = struct.unpack("<I", data[offset + 22 : offset + 26])[0]
            bits_per_pixel = struct.unpack("<H", data[offset + 28 : offset + 30])[0]

            # Calculate image size
            row_size = ((width * bits_per_pixel + 31) // 32) * 4
            image_size = row_size * abs(height)

            # Get header size
            header_size = struct.unpack("<I", data[offset + 14 : offset + 18])[0]
            total_size = 14 + header_size + image_size

            if offset + total_size > len(data):
                return None

            return data[offset : offset + total_size]
        except struct.error:
            return None

    def _extract_png(self, data: bytes, offset: int) -> bytes | None:
        """Extract PNG image data."""
        if offset + 8 > len(data):
            return None

        # Verify PNG signature
        if data[offset : offset + 8] != b"\x89PNG\r\n\x1a\n":
            return None

        # Read chunks until IEND
        pos = offset + 8
        while pos + 12 <= len(data):
            # Read chunk length and type
            chunk_len = struct.unpack(">I", data[pos : pos + 4])[0]
            chunk_type = data[pos + 4 : pos + 8]

            # Move to next chunk
            pos += 12 + chunk_len  # length + type + data + CRC

            # Check for IEND chunk
            if chunk_type == b"IEND":
                return data[offset:pos]

            if pos > len(data):
                break

        return None

    def _extract_jpeg(self, data: bytes, offset: int) -> bytes | None:
        """Extract JPEG image data."""
        if offset + 2 > len(data):
            return None

        # Verify JPEG signature
        if data[offset : offset + 2] != b"\xff\xd8":
            return None

        # Find EOI marker (End of Image)
        pos = offset + 2
        while pos + 2 <= len(data):
            if data[pos : pos + 2] == b"\xff\xd9":
                return data[offset : pos + 2]
            pos += 1

        return None

    def _extract_wav(self, data: bytes, offset: int) -> bytes | None:
        """Extract WAV audio data."""
        if offset + 12 > len(data):
            return None

        # Verify RIFF header
        if data[offset : offset + 4] != b"RIFF":
            return None

        # Get file size
        try:
            chunk_size = struct.unpack("<I", data[offset + 4 : offset + 8])[0]
            total_size = chunk_size + 8

            if offset + total_size > len(data):
                return None

            # Verify WAVE format
            if data[offset + 8 : offset + 12] != b"WAVE":
                return None

            return data[offset : offset + total_size]
        except struct.error:
            return None

    def _extract_generic(self, data: bytes, offset: int) -> bytes | None:
        """Generic resource extraction - looks for common boundaries."""
        # This is a fallback for unknown resource types
        # Look for common end patterns or size indicators

        # For now, just extract a reasonable chunk
        max_size = 1024 * 1024  # 1MB max for unknown resources
        end_offset = min(offset + max_size, len(data))

        return data[offset:end_offset]

    def _is_valid_bmp(self, data: bytes) -> bool:
        """Check if data appears to be a valid BMP."""
        if len(data) < 14:
            return False

        # Check BM signature
        if data[:2] != b"BM":
            return False

        # Check file size is reasonable
        try:
            file_size = struct.unpack("<I", data[2:6])[0]
            return 14 <= file_size <= len(data)
        except struct.error:
            return False

    def _is_valid_png(self, data: bytes) -> bool:
        """Check if data appears to be a valid PNG."""
        return len(data) >= 8 and data[:8] == b"\x89PNG\r\n\x1a\n"

    def _is_valid_jpeg(self, data: bytes) -> bool:
        """Check if data appears to be a valid JPEG."""
        return len(data) >= 2 and data[:2] == b"\xff\xd8"

    def _generate_resource_filename(
        self, base_name: str, resource_type: str, index: int, offset: int
    ) -> str:
        """Generate a filename for an extracted resource."""
        # Sanitize the base name
        safe_name = sanitize_filename(base_name)

        # Create filename with type, index, and offset
        return f"{safe_name}_{resource_type}_{index:03d}_{offset:08x}.{resource_type}"

    def get_statistics(self) -> dict[str, Any]:
        """Get extraction statistics."""
        return {
            "extracted_count": self._extracted_count,
            "total_size": self._total_size,
        }
