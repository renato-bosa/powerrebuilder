"""Unified resource extraction from PowerBuilder files.

This module provides a comprehensive resource extraction system that combines
and enhances existing extractors for all resource types.
"""

import hashlib
import json
import logging
import struct
import time
from pathlib import Path
from typing import Any, Dict

from src.extract.pbd.catalog import ResourceCatalog

logger = logging.getLogger(__name__)


class ResourceType:
    """Resource type constants."""

    # Images
    IMAGE_PNG = "png"
    IMAGE_JPG = "jpg"
    IMAGE_GIF = "gif"
    IMAGE_BMP = "bmp"
    IMAGE_ICO = "ico"
    IMAGE_CUR = "cur"
    IMAGE_TIFF = "tiff"
    IMAGE_WEBP = "webp"

    # Audio
    AUDIO_WAV = "wav"
    AUDIO_MP3 = "mp3"
    AUDIO_OGG = "ogg"
    AUDIO_WMA = "wma"

    # Documents
    DOC_PDF = "pdf"
    DOC_RTF = "rtf"
    DOC_TXT = "txt"

    # Binary
    BINARY_DLL = "dll"
    BINARY_EXE = "exe"
    BINARY_OCX = "ocx"

    # Other
    DATA_XML = "xml"
    DATA_JSON = "json"
    DATA_CSV = "csv"
    UNKNOWN = "unknown"


class ResourceCategory:
    """Resource category constants."""

    IMAGE = "image"
    AUDIO = "audio"
    DOCUMENT = "document"
    BINARY = "binary"
    DATA = "data"
    OTHER = "other"


class UnifiedResourceExtractor:
    """Unified resource extraction for all resource types."""

    # Resource signatures mapping
    RESOURCE_SIGNATURES = {
        # Image formats
        b"\x89PNG\r\n\x1a\n": (ResourceType.IMAGE_PNG, 8),
        b"GIF87a": (ResourceType.IMAGE_GIF, 6),
        b"GIF89a": (ResourceType.IMAGE_GIF, 6),
        b"\xff\xd8\xff": (ResourceType.IMAGE_JPG, 3),
        b"BM": (ResourceType.IMAGE_BMP, 2),
        b"\x00\x00\x01\x00": (ResourceType.IMAGE_ICO, 4),
        b"\x00\x00\x02\x00": (ResourceType.IMAGE_CUR, 4),
        b"II*\x00": (ResourceType.IMAGE_TIFF, 4),
        b"MM\x00*": (ResourceType.IMAGE_TIFF, 4),
        # Audio formats (RIFF handled specially - could be WAV or WebP)
        b"RIFF": (ResourceType.AUDIO_WAV, 4),  # Default to WAV, check further for WebP
        b"ID3": (ResourceType.AUDIO_MP3, 3),
        b"\xff\xfb": (ResourceType.AUDIO_MP3, 2),  # MP3 without ID3
        b"OggS": (ResourceType.AUDIO_OGG, 4),
        # Document formats
        b"%PDF": (ResourceType.DOC_PDF, 4),
        b"{\\rtf": (ResourceType.DOC_RTF, 5),
        # Binary formats
        b"MZ": (ResourceType.BINARY_EXE, 2),  # DOS/Windows executable
        # Data formats
        b"<?xml": (ResourceType.DATA_XML, 5),
        b"<xml": (ResourceType.DATA_XML, 4),
    }

    # Category mapping
    TYPE_TO_CATEGORY = {
        ResourceType.IMAGE_PNG: ResourceCategory.IMAGE,
        ResourceType.IMAGE_JPG: ResourceCategory.IMAGE,
        ResourceType.IMAGE_GIF: ResourceCategory.IMAGE,
        ResourceType.IMAGE_BMP: ResourceCategory.IMAGE,
        ResourceType.IMAGE_ICO: ResourceCategory.IMAGE,
        ResourceType.IMAGE_CUR: ResourceCategory.IMAGE,
        ResourceType.IMAGE_TIFF: ResourceCategory.IMAGE,
        ResourceType.IMAGE_WEBP: ResourceCategory.IMAGE,
        ResourceType.AUDIO_WAV: ResourceCategory.AUDIO,
        ResourceType.AUDIO_MP3: ResourceCategory.AUDIO,
        ResourceType.AUDIO_OGG: ResourceCategory.AUDIO,
        ResourceType.AUDIO_WMA: ResourceCategory.AUDIO,
        ResourceType.DOC_PDF: ResourceCategory.DOCUMENT,
        ResourceType.DOC_RTF: ResourceCategory.DOCUMENT,
        ResourceType.DOC_TXT: ResourceCategory.DOCUMENT,
        ResourceType.BINARY_DLL: ResourceCategory.BINARY,
        ResourceType.BINARY_EXE: ResourceCategory.BINARY,
        ResourceType.BINARY_OCX: ResourceCategory.BINARY,
        ResourceType.DATA_XML: ResourceCategory.DATA,
        ResourceType.DATA_JSON: ResourceCategory.DATA,
        ResourceType.DATA_CSV: ResourceCategory.DATA,
    }

    def __init__(self, output_dir: Path) -> None:
        """Initialize the unified resource extractor.

        Args:
            output_dir: Base output directory for resources
        """
        self.output_dir = output_dir
        self.resources_dir = output_dir / "resources"
        self.resources_dir.mkdir(parents=True, exist_ok=True)

        # Initialize resource catalog
        self.catalog = ResourceCatalog()

        # Statistics tracking
        self.stats: dict[str, Any] = {
            "total_objects_scanned": 0,
            "objects_with_resources": 0,
            "total_resources": 0,
            "total_size": 0,
            "resource_types": {},
            "resource_categories": {},
            "extraction_errors": 0,
        }

        # Resource tracking
        self.extracted_resources: dict[str, list[dict[str, Any]]] = {}
        self.resource_hashes: set[str] = set()

    def extract_resources_from_data(
        self,
        data: bytes,
        object_name: str,
        object_type: str,
    ) -> list[dict[str, Any]]:
        """Extract all resources from object data.

        Args:
            data: Binary data to scan for resources
            object_name: Name of the source object
            object_type: Type of the source object (e.g., 'srw', 'sru')

        Returns:
            List of extracted resource metadata
        """
        resources = []
        self.stats["total_objects_scanned"] += 1

        try:
            # Scan for all known resource signatures
            found_resources = self._scan_for_resources(data, object_name, object_type)

            if found_resources:
                self.stats["objects_with_resources"] += 1

                # Process and save each resource
                for resource_info in found_resources:
                    saved_resource = self._save_resource(resource_info)
                    if saved_resource:
                        resources.append(saved_resource)

                        # Update catalog
                        self._add_to_catalog(saved_resource)

                        # Update statistics
                        self._update_statistics(saved_resource)

                # Track by object
                self.extracted_resources[object_name] = resources

            return resources

        except Exception as e:
            logger.error("Failed to extract resources from %s: %s", object_name, e)
            self.stats["extraction_errors"] += 1
            return []

    def _scan_for_resources(
        self,
        data: bytes,
        object_name: str,
        object_type: str,
    ) -> list[dict[str, Any]]:
        """Scan data for all resource signatures.

        Args:
            data: Binary data to scan
            object_name: Source object name
            object_type: Source object type

        Returns:
            List of found resources with metadata
        """
        resources = []
        scanned_offsets = set()

        # Check for each signature type
        for signature, (resource_type, _sig_len) in self.RESOURCE_SIGNATURES.items():
            offset = 0
            while True:
                # Find next occurrence
                offset = data.find(signature, offset)
                if offset == -1:
                    break

                # Skip if we already extracted a resource at this offset
                if offset in scanned_offsets:
                    offset += 1
                    continue

                # Special handling for RIFF (could be WAV or WebP)
                if signature == b"RIFF" and offset + 12 < len(data):
                    # Check RIFF type
                    if data[offset + 8 : offset + 12] == b"WAVE":
                        resource_type = ResourceType.AUDIO_WAV
                    elif data[offset + 8 : offset + 12] == b"WEBP":
                        resource_type = ResourceType.IMAGE_WEBP

                # Extract the resource
                resource_data = self._extract_resource(data, offset, resource_type)

                if resource_data:
                    # Calculate hash for deduplication
                    resource_hash = hashlib.sha256(resource_data).hexdigest()

                    # Create resource info
                    resource_info = {
                        "type": resource_type,
                        "category": self.TYPE_TO_CATEGORY.get(
                            resource_type, ResourceCategory.OTHER
                        ),
                        "offset": offset,
                        "size": len(resource_data),
                        "data": resource_data,
                        "hash": resource_hash,
                        "source_object": object_name,
                        "source_type": object_type,
                        "metadata": self._extract_metadata(
                            resource_data, resource_type
                        ),
                    }

                    resources.append(resource_info)
                    scanned_offsets.add(offset)

                    logger.debug(
                        "Found %s resource at offset %d in %s",
                        resource_type,
                        offset,
                        object_name,
                    )

                    # Move past this resource
                    offset += len(resource_data)
                else:
                    offset += 1

        return resources

    def _extract_resource(
        self,
        data: bytes,
        offset: int,
        resource_type: str,
    ) -> bytes | None:
        """Extract a complete resource from data.

        Args:
            data: Binary data
            offset: Starting offset
            resource_type: Type of resource

        Returns:
            Complete resource data or None
        """
        try:
            # Use type-specific extraction methods
            if resource_type == ResourceType.IMAGE_BMP:
                return self._extract_bmp(data, offset)
            if resource_type == ResourceType.IMAGE_ICO:
                return self._extract_ico(data, offset)
            if resource_type == ResourceType.IMAGE_PNG:
                return self._extract_png(data, offset)
            if resource_type == ResourceType.IMAGE_GIF:
                return self._extract_gif(data, offset)
            if resource_type == ResourceType.IMAGE_JPG:
                return self._extract_jpeg(data, offset)
            if resource_type == ResourceType.AUDIO_WAV:
                return self._extract_wav(data, offset)
            if resource_type == ResourceType.AUDIO_MP3:
                return self._extract_mp3(data, offset)
            if resource_type == ResourceType.DOC_PDF:
                return self._extract_pdf(data, offset)
            if resource_type == ResourceType.BINARY_EXE:
                return self._extract_exe(data, offset)
            # Generic extraction by finding next signature
            return self._extract_generic(data, offset)

        except Exception as e:
            logger.debug(
                "Failed to extract %s at offset %d: %s", resource_type, offset, e
            )
            return None

    def _extract_bmp(self, data: bytes, offset: int) -> bytes | None:
        """Extract BMP image."""
        if offset + 14 > len(data):
            return None

        # Read file size from BMP header
        file_size = struct.unpack("<I", data[offset + 2 : offset + 6])[0]

        if file_size > 0 and offset + file_size <= len(data):
            return data[offset : offset + file_size]

        return None

    def _extract_ico(self, data: bytes, offset: int) -> bytes | None:
        """Extract ICO/CUR file."""
        if offset + 6 > len(data):
            return None

        # Read number of images
        num_images = struct.unpack("<H", data[offset + 4 : offset + 6])[0]

        if num_images == 0 or num_images > 100:
            return None

        # Calculate total size
        header_size = 6 + (16 * num_images)
        if offset + header_size > len(data):
            return None

        # Find the end of all image data
        total_size = header_size
        for i in range(num_images):
            entry_offset = offset + 6 + (16 * i)
            if entry_offset + 16 > len(data):
                return None

            img_size = struct.unpack("<I", data[entry_offset + 8 : entry_offset + 12])[
                0
            ]
            img_offset = struct.unpack(
                "<I", data[entry_offset + 12 : entry_offset + 16]
            )[0]
            total_size = max(total_size, img_offset + img_size - offset)

        if offset + total_size <= len(data):
            return data[offset : offset + total_size]

        return None

    def _extract_png(self, data: bytes, offset: int) -> bytes | None:
        """Extract PNG image."""
        # PNG ends with IEND chunk
        end_marker = b"IEND\xae\x42\x60\x82"
        end_offset = data.find(end_marker, offset)

        if end_offset != -1:
            return data[offset : end_offset + len(end_marker)]

        return None

    def _extract_gif(self, data: bytes, offset: int) -> bytes | None:
        """Extract GIF image."""
        # GIF ends with trailer byte
        end_offset = data.find(b"\x3b", offset + 13)

        if end_offset != -1:
            return data[offset : end_offset + 1]

        return None

    def _extract_jpeg(self, data: bytes, offset: int) -> bytes | None:
        """Extract JPEG image."""
        # JPEG ends with EOI marker
        end_marker = b"\xff\xd9"
        end_offset = data.find(end_marker, offset + 2)

        if end_offset != -1:
            return data[offset : end_offset + len(end_marker)]

        return None

    def _extract_wav(self, data: bytes, offset: int) -> bytes | None:
        """Extract WAV audio file."""
        if offset + 44 > len(data):  # Minimum WAV header size
            return None

        # Check RIFF header
        if data[offset : offset + 4] != b"RIFF":
            return None

        # Get file size from RIFF header
        file_size = struct.unpack("<I", data[offset + 4 : offset + 8])[0] + 8

        if offset + file_size <= len(data):
            # Verify it's a WAVE file
            if data[offset + 8 : offset + 12] == b"WAVE":
                return data[offset : offset + file_size]

        return None

    def _extract_mp3(self, data: bytes, offset: int) -> bytes | None:
        """Extract MP3 audio file."""
        # MP3 files can have ID3 tags or start with sync bytes
        # This is a simplified extraction - look for next MP3 sync or end

        # If it starts with ID3, find the tag size
        if data[offset : offset + 3] == b"ID3" and offset + 10 <= len(data):
            # ID3v2 tag size calculation
            size_bytes = data[offset + 6 : offset + 10]
            tag_size = (
                (size_bytes[0] & 0x7F) << 21
                | (size_bytes[1] & 0x7F) << 14
                | (size_bytes[2] & 0x7F) << 7
                | (size_bytes[3] & 0x7F)
            ) + 10

            # Now find the actual MP3 data after the tag
            mp3_start = offset + tag_size
        else:
            mp3_start = offset

        # Find the end (next resource or max size)
        max_size = min(10 * 1024 * 1024, len(data) - mp3_start)  # Max 10MB

        # Simple approach: extract up to next known signature or max size
        end_offset = mp3_start + max_size

        for sig in self.RESOURCE_SIGNATURES:
            next_offset = data.find(sig, mp3_start + 100)  # Skip at least 100 bytes
            if next_offset != -1 and next_offset < end_offset:
                end_offset = next_offset

        if end_offset > mp3_start + 100:  # Minimum reasonable MP3 size
            return data[offset:end_offset]

        return None

    def _extract_pdf(self, data: bytes, offset: int) -> bytes | None:
        """Extract PDF document."""
        # PDF ends with %%EOF
        end_marker = b"%%EOF"
        end_offset = data.find(end_marker, offset)

        if end_offset != -1:
            # Include the end marker and possible trailing bytes
            return data[offset : end_offset + len(end_marker) + 2]

        return None

    def _extract_exe(self, data: bytes, offset: int) -> bytes | None:
        """Extract Windows executable."""
        if offset + 64 > len(data):  # Minimum DOS header size
            return None

        # Check MZ signature
        if data[offset : offset + 2] != b"MZ":
            return None

        # Get PE header offset
        pe_offset_pos = offset + 0x3C
        if pe_offset_pos + 4 > len(data):
            return None

        struct.unpack("<I", data[pe_offset_pos : pe_offset_pos + 4])[0]

        # This is complex - for now just extract a reasonable amount
        # Real implementation would parse PE headers properly
        max_size = min(50 * 1024 * 1024, len(data) - offset)  # Max 50MB

        return data[offset : offset + max_size]

    def _extract_generic(self, data: bytes, offset: int) -> bytes | None:
        """Generic extraction by finding next resource signature."""
        # Find the next signature
        min_next_offset = len(data)

        for signature in self.RESOURCE_SIGNATURES:
            next_offset = data.find(signature, offset + len(signature))
            if next_offset != -1 and next_offset < min_next_offset:
                min_next_offset = next_offset

        # Extract up to next signature or reasonable size
        max_size = min(min_next_offset - offset, 10 * 1024 * 1024)  # Max 10MB

        if max_size > 100:  # Minimum reasonable size
            return data[offset : offset + max_size]

        return None

    def _extract_metadata(self, data: bytes, resource_type: str) -> dict[str, Any]:
        """Extract metadata from resource data.

        Args:
            data: Resource data
            resource_type: Type of resource

        Returns:
            Dictionary of metadata
        """
        metadata = {"type": resource_type}

        try:
            if resource_type == ResourceType.IMAGE_BMP and len(data) >= 26:
                metadata["width"] = struct.unpack("<I", data[18:22])[0]
                metadata["height"] = struct.unpack("<I", data[22:26])[0]
                metadata["bits_per_pixel"] = struct.unpack("<H", data[28:30])[0]

            elif resource_type == ResourceType.IMAGE_PNG and len(data) >= 24:
                metadata["width"] = struct.unpack(">I", data[16:20])[0]
                metadata["height"] = struct.unpack(">I", data[20:24])[0]

            elif resource_type == ResourceType.IMAGE_GIF and len(data) >= 10:
                metadata["width"] = struct.unpack("<H", data[6:8])[0]
                metadata["height"] = struct.unpack("<H", data[8:10])[0]

            elif resource_type == ResourceType.IMAGE_ICO and len(data) >= 22:
                metadata["width"] = str(data[6] or 256)
                metadata["height"] = str(data[7] or 256)
                metadata["num_images"] = struct.unpack("<H", data[4:6])[0]

            elif resource_type == ResourceType.AUDIO_WAV and len(data) >= 44:
                # Basic WAV metadata from header
                metadata["channels"] = struct.unpack("<H", data[22:24])[0]
                metadata["sample_rate"] = struct.unpack("<I", data[24:28])[0]
                metadata["bits_per_sample"] = struct.unpack("<H", data[34:36])[0]

        except Exception as e:
            logger.debug("Failed to extract metadata for %s: %s", resource_type, e)

        return metadata

    def _save_resource(self, resource_info: dict[str, Any]) -> dict[str, Any] | None:
        """Save resource to disk.

        Args:
            resource_info: Resource information dictionary

        Returns:
            Updated resource info with file path, or None if save failed
        """
        try:
            # Create category directory
            category = resource_info["category"]
            category_dir = self.resources_dir / category
            category_dir.mkdir(exist_ok=True)

            # Generate unique filename
            resource_type = resource_info["type"]
            resource_hash = resource_info["hash"][:8]
            source_name = Path(resource_info["source_object"]).stem

            filename = f"{source_name}_{resource_hash}.{resource_type}"
            file_path = category_dir / filename

            # Check if already exists (deduplication)
            if not file_path.exists():
                file_path.write_bytes(resource_info["data"])
                logger.info("Saved %s resource to %s", resource_type, file_path)
                # Track unique resource hash
                self.resource_hashes.add(resource_info["hash"])
            else:
                logger.debug("Resource already exists: %s", file_path)

            # Update resource info
            resource_info["path"] = str(file_path.relative_to(self.output_dir))
            resource_info["filename"] = filename

            # Generate unique ID
            resource_info["id"] = f"{resource_type}_{resource_hash}"

            # Remove raw data to save memory
            del resource_info["data"]

            return resource_info

        except Exception as e:
            logger.error("Failed to save resource: %s", e)
            return None

    def _add_to_catalog(self, resource_info: dict[str, Any]) -> None:
        """Add resource to catalog.

        Args:
            resource_info: Resource information
        """
        if resource_info["category"] == ResourceCategory.IMAGE:
            self.catalog.add_image_resource(
                resource_info["source_object"],
                {
                    "format": resource_info["type"],
                    "size": resource_info["size"],
                    "offset": resource_info["offset"],
                    "path": resource_info["path"],
                    "metadata": resource_info.get("metadata", {}),
                },
            )
        elif resource_info["category"] == ResourceCategory.BINARY:
            self.catalog.add_binary_resource(
                resource_info["source_object"],
                resource_info["type"],
                {
                    "size": resource_info["size"],
                    "offset": resource_info["offset"],
                    "path": resource_info["path"],
                },
            )
        else:
            # Generic resource
            self.catalog.add_resource(resource_info["category"], resource_info)

    def _update_statistics(self, resource_info: dict[str, Any]) -> None:
        """Update extraction statistics.

        Args:
            resource_info: Resource information
        """
        self.stats["total_resources"] += 1
        self.stats["total_size"] += resource_info["size"]

        # Count by type
        resource_type = resource_info["type"]
        if resource_type not in self.stats["resource_types"]:
            self.stats["resource_types"][resource_type] = 0
        self.stats["resource_types"][resource_type] += 1

        # Count by category
        category = resource_info["category"]
        if category not in self.stats["resource_categories"]:
            self.stats["resource_categories"][category] = 0
        self.stats["resource_categories"][category] += 1

    def generate_manifest(self) -> None:
        """Generate resource extraction manifest."""
        manifest_path = self.resources_dir / "manifest.json"

        # Flatten all resources from all objects
        all_resources = []
        for resources_list in self.extracted_resources.values():
            all_resources.extend(resources_list)

        manifest = {
            "extraction_time": time.strftime("%Y-%m-%d %H:%M:%S"),
            "statistics": self.stats,
            "resources": all_resources,
            "summary": {
                "total_objects": self.stats["total_objects_scanned"],
                "objects_with_resources": self.stats["objects_with_resources"],
                "total_resources": self.stats["total_resources"],
                "total_size_mb": round(self.stats["total_size"] / 1024 / 1024, 2),
                "unique_resources": len(self.resource_hashes),
                "extraction_errors": self.stats["extraction_errors"],
            },
        }

        with manifest_path.open("w") as f:
            json.dump(manifest, f, indent=2, default=str)

        # Save catalog
        self.catalog.save_catalog(self.resources_dir)

        logger.info(
            "Resource extraction complete: %d resources from %d objects",
            self.stats["total_resources"],
            self.stats["objects_with_resources"],
        )
