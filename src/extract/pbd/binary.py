"""Unified binary resource extractors combining string, image, and resource management.

This module merges functionality from:
- extract/pbd/extraction/string_extractor.py - String resource extraction
- extract/pbd/extraction/enhanced_image_extractor.py - Enhanced image extraction
- extract/pbd/extraction/resource_extraction_manager.py - Resource extraction management

Note: The standalone string_extractor.py file has been deprecated and its functionality
is now fully integrated into this module as the StringResourceExtractor class.
"""

import contextlib
import hashlib
import json
import logging
import pickle
import re
import struct
import time
from collections import defaultdict
from io import BytesIO
from pathlib import Path
from typing import Any, Dict

import chardet

logger = logging.getLogger(__name__)


class StringResourceExtractor:
    """Extracts string resources from PowerBuilder compiled objects."""

    # Minimum string length to consider (filters out noise)
    MIN_STRING_LENGTH = 3

    # Maximum string length (prevents memory issues with corrupted data)
    MAX_STRING_LENGTH = 10000

    # Common PowerBuilder string patterns (fixed regex syntax)
    STRING_PATTERNS = [
        # ASCII strings (printable characters, minimum 3 chars)
        rb"[\x20-\x7E]{3,}",
        # Unicode strings (UTF-16 LE with null bytes)
        rb"(?:[\x20-\x7E]\x00){3,}",
        # Unicode strings (UTF-16 BE with null bytes)
        rb"(?:\x00[\x20-\x7E]){3,}",
        # Windows-1252 extended ASCII
        rb"[\x20-\x7E\x80-\xFF]{3,}",
    ]

    # Patterns to exclude (reduce false positives)
    EXCLUDE_PATTERNS = [
        # Binary sequences that look like strings
        re.compile(rb"^[\x00]+$"),  # All nulls
        re.compile(rb"^[\xFF]+$"),  # All 0xFF
        re.compile(rb"^(?:[\x00-\x1F])+$"),  # All control characters
    ]

    def __init__(self) -> None:
        """Initialize the string resource extractor."""
        self.extracted_strings: dict[str, set[str]] = {}
        self.encoding_cache: dict[
            bytes, str | None
        ] = {}  # Cache for encoding detection
        self.extraction_stats = {
            "total_candidates": 0,
            "valid_strings": 0,
            "encoding_detections": 0,
            "cache_hits": 0,
        }

    def extract_strings_from_file(self, file_path: Path) -> list[str]:
        """Extract all string resources from a file.

        Args:
        file_path: Path to the file to extract strings from

        Returns:
        List of extracted strings
        """
        try:
            with file_path.open("rb") as f:
                data = f.read()

            return self.extract_strings_from_data(data, str(file_path))

        except Exception as e:
            logger.error("Failed to extract strings from %s: %s", file_path, e)
            return []

    def extract_strings_from_data(
        self, data: bytes, source: str = "unknown"
    ) -> list[str]:
        """Extract strings from binary data with improved accuracy.

        Args:
            data: Binary data to extract strings from
            source: Source identifier for logging

        Returns:
            List of extracted strings
        """
        strings = set()

        # Detect primary encoding of the data sample
        primary_encoding = self._detect_encoding(
            data[:8192]
        )  # Use first 8KB for detection

        # Extract using multiple methods for better coverage
        strings.update(self._extract_with_patterns(data, primary_encoding))
        strings.update(self._extract_null_terminated(data, primary_encoding))
        strings.update(self._extract_length_prefixed(data, primary_encoding))
        strings.update(self._extract_property_format(data))

        # Apply additional validation and filtering
        validated_strings = set()
        for string in strings:
            self.extraction_stats["total_candidates"] += 1
            if self._is_valid_string_enhanced(string):
                validated_strings.add(string)
                self.extraction_stats["valid_strings"] += 1

        # Store results
        if validated_strings:
            self.extracted_strings[source] = validated_strings
            logger.info(
                "Extracted %d strings from %s (primary encoding: %s)",
                len(validated_strings),
                source,
                primary_encoding,
            )

        return sorted(validated_strings)

    def _extract_with_patterns(
        self, data: bytes, primary_encoding: str | None
    ) -> set[str]:
        """Extract strings using regex patterns."""
        strings = set()

        for pattern in self.STRING_PATTERNS:
            matches = re.findall(pattern, data)
            for match in matches:
                decoded = self._decode_string_enhanced(match, primary_encoding)
                if decoded:
                    strings.add(decoded)

        return strings

    def _extract_null_terminated(
        self, data: bytes, primary_encoding: str | None
    ) -> set[str]:
        """Extract null-terminated strings."""
        strings = set()

        # Look for null-terminated strings
        for encoding in self._get_encoding_list(primary_encoding):
            try:
                if encoding in ["utf-16le", "utf-16be"]:
                    # For UTF-16, look for double null termination
                    null_pattern = b"\x00\x00"
                    start = 0
                    while True:
                        end = data.find(null_pattern, start)
                        if end == -1:
                            break

                        # Extract the string candidate
                        candidate = data[start:end]
                        if len(candidate) >= 6:  # Minimum meaningful UTF-16 string:
                            try:
                                decoded = candidate.decode(
                                    encoding, errors="ignore"
                                ).strip()
                                if self._is_valid_string_enhanced(decoded):
                                    strings.add(decoded)
                            except UnicodeDecodeError:
                                pass

                        start = end + 2
                else:
                    # For single-byte encodings, look for single null termination
                    parts = data.split(b"\x00")
                    for part in parts:
                        if len(part) >= self.MIN_STRING_LENGTH:
                            try:
                                decoded = part.decode(encoding, errors="ignore").strip()
                                if self._is_valid_string_enhanced(decoded):
                                    strings.add(decoded)
                            except UnicodeDecodeError:
                                pass
            except Exception:
                continue

        return strings

    def _extract_length_prefixed(
        self, data: bytes, primary_encoding: str | None
    ) -> set[str]:
        """Extract length-prefixed strings."""
        strings = set()
        offset = 0

        while offset < len(data) - 4:
            # Try 1-byte length prefix
            if offset + 1 < len(data):
                length = data[offset]
                if 3 <= length <= 255 and offset + 1 + length <= len(data):
                    string_data = data[offset + 1 : offset + 1 + length]
                    decoded = self._decode_string_enhanced(
                        string_data, primary_encoding
                    )
                    if decoded:
                        strings.add(decoded)
                    offset += 1 + length
                    continue

            # Try 2-byte length prefix (little endian)
            if offset + 2 < len(data):
                length = int.from_bytes(data[offset : offset + 2], "little")
                if 3 <= length <= 1000 and offset + 2 + length <= len(data):
                    string_data = data[offset + 2 : offset + 2 + length]
                    decoded = self._decode_string_enhanced(
                        string_data, primary_encoding
                    )
                    if decoded:
                        strings.add(decoded)
                    offset += 2 + length
                    continue

            # Try 4-byte length prefix (little endian)
            if offset + 4 < len(data):
                length = int.from_bytes(data[offset : offset + 4], "little")
                if 3 <= length <= 10000 and offset + 4 + length <= len(data):
                    string_data = data[offset + 4 : offset + 4 + length]
                    decoded = self._decode_string_enhanced(
                        string_data, primary_encoding
                    )
                    if decoded:
                        strings.add(decoded)
                    offset += 4 + length
                    continue

            offset += 1

        return strings

    def _extract_property_format(self, data: bytes) -> set[str]:
        """Extract strings in property format (key = value)."""
        strings = set()

        # Look for property patterns in the data
        property_patterns = [
            rb'([a-zA-Z_][a-zA-Z0-9_]*)\s*=\s*"([^"]+)"',  # quoted values
            rb"([a-zA-Z_][a-zA-Z0-9_]*)\s*=\s*([^\r\n\s]+)",  # unquoted values
        ]

        for pattern in property_patterns:
            matches = re.finditer(pattern, data)
            for match in matches:
                try:
                    # Extract property name and value
                    name = match.group(1).decode("ascii", errors="ignore")
                    value = match.group(2).decode("utf-8", errors="ignore")

                    if name and len(name) >= 2:
                        strings.add(name)
                    if value and len(value) >= 2:
                        strings.add(value)

                except Exception:
                    continue

        return strings

    def _detect_encoding(self, data: bytes) -> str | None:
        """Detect the most likely encoding for the data.

        Args:
            data: Binary data to analyze

        Returns:
            Most likely encoding or None if detection fails
        """
        if not data:
            return None

        # Check cache first
        if data in self.encoding_cache:
            self.extraction_stats["cache_hits"] += 1
            return self.encoding_cache[data]

        try:
            # Use chardet for automatic detection
            detection = chardet.detect(data)
            self.extraction_stats["encoding_detections"] += 1

            if detection and detection["encoding"]:
                encoding = detection["encoding"].lower()
                confidence = detection["confidence"]

                # Map common encoding variations
                encoding_map = {
                    "windows-1252": "cp1252",
                    "iso-8859-1": "latin1",
                    "utf-16": "utf-16le",  # Default to little endian
                }

                detected_encoding = encoding_map.get(encoding, encoding)

                # Only trust high-confidence detections for non-ASCII
                if detected_encoding != "ascii" and confidence < 0.7:
                    detected_encoding = None

                # Cache the result
                self.encoding_cache[data] = detected_encoding
                return detected_encoding

        except Exception as e:
            logger.debug("Encoding detection failed: %s", e)

        # Cache negative result
        self.encoding_cache[data] = None
        return None

    def _get_encoding_list(self, primary_encoding: str | None) -> list[str]:
        """Get prioritized list of encodings to try.

        Args:
            primary_encoding: Primary encoding detected

        Returns:
            List of encodings in priority order
        """
        encodings = []

        # Add primary encoding first if detected
        if primary_encoding:
            encodings.append(primary_encoding)

        # Add common PowerBuilder encodings
        common_encodings = [
            "utf-8",
            "cp1252",
            "utf-16le",
            "utf-16be",
            "latin1",
            "ascii",
        ]

        for encoding in common_encodings:
            if encoding not in encodings:
                encodings.append(encoding)

        return encodings

    def _decode_string_enhanced(
        self, data: bytes, primary_encoding: str | None
    ) -> str | None:
        """Enhanced string decoding with better encoding detection.

        Args:
            data: Binary data to decode
            primary_encoding: Primary encoding hint

        Returns:
            Decoded string or None if decoding fails
        """
        if not data:
            return None

        # Clean up data based on encoding
        cleaned_data = self._clean_string_data(data)
        if not cleaned_data:
            return None

        # Try encodings in priority order
        for encoding in self._get_encoding_list(primary_encoding):
            try:
                decoded = cleaned_data.decode(encoding, errors="ignore").strip()

                # Basic validation
                if decoded and len(decoded) >= self.MIN_STRING_LENGTH:
                    # Additional cleaning
                    decoded = self._clean_decoded_string(decoded)
                    if decoded and len(decoded) >= self.MIN_STRING_LENGTH:
                        return decoded

            except (UnicodeDecodeError, LookupError):
                continue

        return None

    def _clean_string_data(self, data: bytes) -> bytes:
        """Clean binary data before decoding.

        Args:
            data: Raw binary data

        Returns:
            Cleaned binary data
        """
        # Remove common binary noise patterns
        if len(data) < 2:
            return data

        # Check for UTF-16 patterns and clean accordingly
        if len(data) % 2 == 0:
            # Check if it looks like UTF-16LE (every other byte is null)
            if data[1::2].count(b"\x00"[0]) > len(data) // 4:
                # Remove null bytes from UTF-16LE
                return data[::2]
            # Check if it looks like UTF-16BE (every first byte is null)
            if data[::2].count(b"\x00"[0]) > len(data) // 4:
                # Remove null bytes from UTF-16BE
                return data[1::2]

        # Remove trailing nulls
        data = data.rstrip(b"\x00")

        # Remove non-printable control characters at start/end
        while data and data[0] < 0x20:
            data = data[1:]
        while data and data[-1] < 0x20:
            data = data[:-1]

        return data

    def _clean_decoded_string(self, s: str) -> str:
        """Clean decoded string of artifacts.

        Args:
        s: Decoded string

        Returns:
        Cleaned string
        """
        # Remove null characters
        s = s.replace("\x00", "")

        # Remove other control characters except tab, newline
        s = "".join(c for c in s if ord(c) >= 32 or c in "\t\n\r")

        # Strip whitespace
        s = s.strip()

        # Remove repeated whitespace
        return re.sub(r"\s+", " ", s)

    def _is_valid_string_enhanced(self, s: str) -> bool:
        """Enhanced string validation with better heuristics.

        Args:
            s: String to validate

        Returns:
            True if string appears to be valid content
        """
        if not s or len(s) < self.MIN_STRING_LENGTH or len(s) > self.MAX_STRING_LENGTH:
            return False

        # Must contain at least one letter or digit
        if not any(c.isalnum() for c in s):
            return False

        # Check printable character ratio
        printable_count = sum(1 for c in s if c.isprintable() or c in "\t\n\r")
        if printable_count / len(s) < 0.85:
            return False

        # Exclude strings that are mostly the same character
        if len(set(s.lower())) <= max(1, len(s) // 10):
            return False

        # Exclude pure numeric strings longer than reasonable
        if s.isdigit() and len(s) > 10:
            return False

        # Exclude pure hex strings (but allow mixed alphanumeric)
        if len(s) > 8 and all(c in "0123456789ABCDEFabcdef" for c in s):
            return False

        # Exclude binary-looking patterns
        if re.match(r"^[01]+$", s) and len(s) > 8:
            return False

        # Exclude strings with too many special characters
        special_chars = sum(
            1 for c in s if not c.isalnum() and c not in " \t\n\r.,;:!?-_"
        )
        if special_chars > len(s) // 3:
            return False

        # Check for common PowerBuilder string patterns (positive indicators)
        pb_indicators = [
            r"\b[a-z]+_[a-z]+\b",  # snake_case identifiers
            r"\b[A-Z][a-z]+[A-Z][a-z]+\b",  # PascalCase
            r"\$[A-Za-z_][A-Za-z0-9_]*\$",  # variable references
            r"^\w+\s*=",  # property assignments
        ]

        for pattern in pb_indicators:
            if re.search(pattern, s):
                return True

        # General validation passed
        return True

    def get_extraction_statistics(self) -> dict[str, Any]:
        """Get detailed extraction statistics.

        Returns:
        Dictionary containing extraction performance metrics
        """
        total_strings = sum(len(strings) for strings in self.extracted_strings.values())
        success_rate = (
            self.extraction_stats["valid_strings"]
            / max(self.extraction_stats["total_candidates"], 1)
            * 100
        )

        cache_hit_rate = (
            self.extraction_stats["cache_hits"]
            / max(
                self.extraction_stats["encoding_detections"]
                + self.extraction_stats["cache_hits"],
                1,
            )
            * 100
        )

        return {
            "sources_processed": len(self.extracted_strings),
            "total_strings_extracted": total_strings,
            "total_candidates_evaluated": self.extraction_stats["total_candidates"],
            "extraction_success_rate_percent": round(success_rate, 2),
            "encoding_detections_performed": self.extraction_stats[
                "encoding_detections"
            ],
            "encoding_cache_hits": self.extraction_stats["cache_hits"],
            "encoding_cache_hit_rate_percent": round(cache_hit_rate, 2),
            "average_strings_per_source": round(
                total_strings / max(len(self.extracted_strings), 1), 2
            ),
        }

    def clear_cache(self) -> None:
        """Clear encoding detection cache to free memory."""
        self.encoding_cache.clear()
        logger.info("Cleared encoding detection cache")

    def reset_statistics(self) -> None:
        """Reset extraction statistics."""
        self.extraction_stats = {
            "total_candidates": 0,
            "valid_strings": 0,
            "encoding_detections": 0,
            "cache_hits": 0,
        }
        logger.info("Reset extraction statistics")

    def extract_property_strings(self, data: bytes) -> dict[str, str]:
        """Extract property name/value pairs from binary data.

        Args:
        data: Binary data to analyze

        Returns:
        Dictionary of property name to value mappings
        """
        properties = {}

        # Look for common property patterns
        # Format: property_name = value or property_name="value"
        property_pattern = rb'([a-zA-Z_][a-zA-Z0-9_]*)\s*=\s*(?:"([^"]+)"|([^\r\n\s]+))'

        matches = re.finditer(property_pattern, data)
        for match in matches:
            try:
                name = match.group(1).decode("ascii", errors="ignore")
                # Get value from either quoted (group 2) or unquoted (group 3)
                value = match.group(2) or match.group(3)
                value = value.decode("utf-8", errors="ignore").strip()

                if name and value:
                    properties[name] = value

            except Exception:
                continue

        return properties

    def extract_string_table(self, data: bytes) -> list[tuple[int, str]]:
        """Extract string table entries from binary data.

        String tables often have format: [length][string data]

        Args:
        data: Binary data containing string table

        Returns:
        List of (index, string) tuples
        """
        strings = []
        offset = 0
        index = 0

        while offset < len(data) - 4:
            # Try different length encodings
            # 2-byte length (little endian)
            if offset + 2 < len(data):
                length = int.from_bytes(data[offset : offset + 2], "little")

                if 0 < length < 1000 and offset + 2 + length <= len(data):
                    string_data = data[offset + 2 : offset + 2 + length]
                    decoded = self._decode_string(string_data)

                    if decoded and self._is_valid_string(decoded):
                        strings.append((index, decoded))
                        index += 1
                        offset += 2 + length
                        continue

            # 4-byte length (little endian)
            if offset + 4 < len(data):
                length = int.from_bytes(data[offset : offset + 4], "little")

                if 0 < length < 10000 and offset + 4 + length <= len(data):
                    string_data = data[offset + 4 : offset + 4 + length]
                    decoded = self._decode_string(string_data)

                    if decoded and self._is_valid_string(decoded):
                        strings.append((index, decoded))
                        index += 1
                        offset += 4 + length
                        continue

            # No valid string found, move forward
            offset += 1

        return strings

    def generate_string_catalog(self) -> dict[str, Any]:
        """Generate a catalog of all extracted strings.

        Returns:
        Dictionary containing string statistics and mappings
        """
        catalog: Dict[str, Any] = {
            "total_sources": len(self.extracted_strings),
            "total_unique_strings": len(set().union(*self.extracted_strings.values())),
            "sources": {},
            "common_strings": {},
            "string_index": {},
        }

        # Count string occurrences across sources
        string_counts: dict[str, int] = {}
        for source, strings in self.extracted_strings.items():
            catalog["sources"][source] = len(strings)
            for string in strings:
                if string not in string_counts:
                    string_counts[string] = []
                string_counts[string].append(source)

        # Find common strings (appear in multiple sources)
        for string, sources in string_counts.items():
            if len(sources) > 1:
                catalog["common_strings"][string] = sources

        # Create string index
        all_strings = sorted(set().union(*self.extracted_strings.values()))
        catalog["string_index"] = dict(enumerate(all_strings))

        return catalog

        # Compatibility methods for older code

    def _decode_string(self, data: bytes) -> str | None:
        """Legacy decode method for compatibility."""
        return self._decode_string_enhanced(data, None)

    def _is_valid_string(self, s: str) -> bool:
        """Legacy validation method for compatibility."""
        return self._is_valid_string_enhanced(s)


# ============================================================================
# Enhanced Image Extractor (from enhanced_image_extractor.py)
# ============================================================================


class EnhancedImageExtractor:
    """Enhanced image extraction from PowerBuilder files."""

    # Extended image signatures
    IMAGE_SIGNATURES = {
        # Standard formats
        b"\x89PNG\r\n\x1a\n": ("png", 8),
        b"GIF87a": ("gif", 6),
        b"GIF89a": ("gif", 6),
        b"\xff\xd8\xff": ("jpg", 3),
        b"BM": ("bmp", 2),
        b"\x00\x00\x01\x00": ("ico", 4),
        b"\x00\x00\x02\x00": ("cur", 4),  # Additional formats
        b"RIFF": ("webp", 4),  # WebP images
        b"II*\x00": ("tiff", 4),  # TIFF little-endian
        b"MM\x00*": ("tiff", 4),  # TIFF big-endian
        b"\x00\x00\x00\x0c": ("jp2", 4),  # JPEG 2000
        # PowerBuilder specific
        b"PBM\x00": ("pbm", 4),  # PowerBuilder bitmap
        b"PBI\x00": ("pbi", 4),  # PowerBuilder icon
    }

    # Object types to search for images
    SEARCHABLE_OBJECT_TYPES = [
        ".srm",  # Static Resource Module (menus)
        ".sru",  # User objects
        ".srw",  # Windows
        ".srd",  # DataWindows
        ".src",  # Structure
        ".srf",  # Functions
        ".udo",  # User defined objects
        ".win",  # Window objects
        ".men",  # Menu objects
        ".dwo",  # DataWindow objects
    ]

    def __init__(self) -> None:
        """Initialize the enhanced image extractor."""
        self.extracted_images: dict[str, list[dict[str, Any]]] = {}

    def extract_images_from_file(
        self, file_path: Path, output_dir: Path | None = None
    ) -> list[dict[str, Any]]:
        """Extract all images from a PowerBuilder file.

        Args:
            file_path: Path to the file to extract images from
            output_dir: Optional directory to save extracted images

        Returns:
            List of dictionaries containing image metadata
        """
        # Check if file type should be searched
        if not any(
            str(file_path).endswith(ext) for ext in self.SEARCHABLE_OBJECT_TYPES
        ):
            logger.debug("Skipping %s - not a searchable object type", file_path)
            return []

        try:
            with file_path.open("rb") as f:
                data = f.read()

            images = self.find_images_in_data(data, str(file_path))

            # Save images if output directory provided
            if output_dir and images:
                output_dir.mkdir(parents=True, exist_ok=True)
                for i, image_info in enumerate(images):
                    image_path = (
                        output_dir
                        / f"{file_path.stem}_image_{i}.{image_info['format']}"
                    )
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
        for signature, (format_name, _sig_len) in self.IMAGE_SIGNATURES.items():
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

                        images.append(
                            {
                                "format": format_name,
                                "offset": offset,
                                "size": len(image_data),
                                "data": image_data,
                                "metadata": metadata,
                                "source": source,
                            }
                        )

                        logger.debug(
                            "Found %s image at offset %s in %s",
                            format_name,
                            offset,
                            source,
                        )

                    # Skip past this image
                    offset += len(image_data) if image_data else 1
                else:
                    offset += 1

        # Store results
        if images:
            self.extracted_images[source] = images
            logger.info("Extracted %s images from %s", len(images), source)

        return images

    def _extract_image(
        self, data: bytes, offset: int, format_name: str
    ) -> bytes | None:
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
            if format_name == "ico":
                return self._extract_ico(data, offset)
            if format_name == "cur":
                return self._extract_cursor(data, offset)
            if format_name == "png":
                return self._extract_png(data, offset)
            if format_name == "gif":
                return self._extract_gif(data, offset)
            if format_name == "jpg":
                return self._extract_jpeg(data, offset)
            # For unknown formats, try to find end by searching for next signature
            return self._extract_by_next_signature(data, offset)

        except Exception as e:
            logger.debug(
                "Failed to extract %s at offset %s: %s", format_name, offset, e
            )
            return None

    def _extract_bmp(self, data: bytes, offset: int) -> bytes | None:
        """Extract BMP image."""
        if offset + 14 > len(data):
            return None

        # Read BMP header
        file_size = struct.unpack("<I", data[offset + 2 : offset + 6])[0]

        if file_size > 0 and offset + file_size <= len(data):
            return data[offset : offset + file_size]

        return None

    def _extract_ico(self, data: bytes, offset: int) -> bytes | None:
        """Extract ICO image."""
        if offset + 6 > len(data):
            return None

        # Read ICO header
        num_images = struct.unpack("<H", data[offset + 4 : offset + 6])[0]

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

            size = struct.unpack("<I", data[entry_offset + 8 : entry_offset + 12])[0]
            total_size = max(
                total_size,
                struct.unpack("<I", data[entry_offset + 12 : entry_offset + 16])[0]
                + size,
            )

        if offset + total_size <= len(data):
            return data[offset : offset + total_size]

        return None

    def _extract_cursor(self, data: bytes, offset: int) -> bytes | None:
        """Extract cursor file (similar to ICO)."""
        return self._extract_ico(data, offset)

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
        # GIF ends with trailer byte 0x3B
        end_offset = data.find(b"\x3b", offset + 13)  # Skip header

        if end_offset != -1:
            return data[offset : end_offset + 1]

        return None

    def _extract_jpeg(self, data: bytes, offset: int) -> bytes | None:
        """Extract JPEG image."""
        # JPEG ends with EOI marker 0xFFD9
        end_marker = b"\xff\xd9"
        end_offset = data.find(end_marker, offset + 2)

        if end_offset != -1:
            return data[offset : end_offset + len(end_marker)]

        return None

    def _extract_by_next_signature(self, data: bytes, offset: int) -> bytes | None:
        """Extract image by finding next image signature."""
        # Find the next image signature
        min_next_offset = len(data)

        for signature in self.IMAGE_SIGNATURES:
            next_offset = data.find(signature, offset + len(signature))
            if next_offset != -1 and next_offset < min_next_offset:
                min_next_offset = next_offset

        # Extract up to next signature or max reasonable size
        max_size = min(min_next_offset - offset, 10 * 1024 * 1024)  # Max 10MB
        if max_size > 100:  # Minimum reasonable image size
            return data[offset : offset + max_size]

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
        if format_name == "png":
            return data[:8] == b"\x89PNG\r\n\x1a\n"
        if format_name == "gif":
            return data[:6] in [b"GIF87a", b"GIF89a"]
        if format_name == "jpg":
            return data[:3] == b"\xff\xd8\xff" and data[-2:] == b"\xff\xd9"

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
                metadata["width"] = str(data[6] or 256)
                metadata["height"] = str(data[7] or 256)
                metadata["color_count"] = str(data[8])

        except Exception as e:
            logger.debug("Failed to extract metadata for %s: %s", format_name, e)

        return metadata

    def generate_image_catalog(self) -> dict[str, Any]:
        """Generate a catalog of all extracted images.

        Returns:
        Dictionary containing image statistics and inventory
        """
        catalog: Dict[str, Any] = {
            "total_sources": len(self.extracted_images),
            "total_images": sum(len(imgs) for imgs in self.extracted_images.values()),
            "format_counts": {},
            "sources": {},
            "images_by_format": {},
            "size_statistics": {
                "min": float("inf"),
                "max": 0,
                "total": 0,
            },
        }

        # Process all extracted images
        for source, images in self.extracted_images.items():
            catalog["sources"][source] = {
                "count": len(images),
                "formats": list({img["format"] for img in images}),
                "total_size": sum(img["size"] for img in images),
            }

            for image in images:
                format_name = image["format"]

                # Count formats
                catalog["format_counts"][format_name] = (
                    catalog["format_counts"].get(format_name, 0) + 1
                )

                # Group by format
                if format_name not in catalog["images_by_format"]:
                    catalog["images_by_format"][format_name] = []
                catalog["images_by_format"][format_name].append(
                    {
                        "source": source,
                        "offset": image["offset"],
                        "size": image["size"],
                        "metadata": image.get("metadata", {}),
                    }
                )

                # Update size statistics
                catalog["size_statistics"]["min"] = min(
                    catalog["size_statistics"]["min"], image["size"]
                )
                catalog["size_statistics"]["max"] = max(
                    catalog["size_statistics"]["max"], image["size"]
                )
                catalog["size_statistics"]["total"] += image["size"]

        # Calculate average size
        if catalog["total_images"] > 0:
            catalog["size_statistics"]["average"] = (
                catalog["size_statistics"]["total"] / catalog["total_images"]
            )
        else:
            catalog["size_statistics"]["min"] = 0
            catalog["size_statistics"]["average"] = 0

        return catalog

    def convert_image_format(
        self, image_data: bytes, source_format: str, target_format: str
    ) -> bytes | None:
        """Convert image from one format to another.

        Args:
            image_data: Original image data
            source_format: Source format (e.g., 'bmp', 'ico')
            target_format: Target format (e.g., 'png', 'jpg')

        Returns:
            Converted image data or None if conversion failed
        """
        try:
            # Try using PIL if available
            try:
                from PIL import Image

                # Load image from bytes
                source_image = Image.open(BytesIO(image_data))

                # Convert format
                output_buffer = BytesIO()

                # Handle format-specific options
                save_kwargs = {}
                if target_format.lower() in ("jpg", "jpeg"):
                    # Convert to RGB for JPEG (no transparency)
                    if source_image.mode in ("RGBA", "LA", "P"):
                        background = Image.new(
                            "RGB", source_image.size, (255, 255, 255)
                        )
                        if source_image.mode == "P":
                            source_image = source_image.convert("RGBA")
                        background.paste(
                            source_image,
                            mask=source_image.split()[-1]
                            if source_image.mode == "RGBA"
                            else None,
                        )
                        source_image = background
                    save_kwargs["quality"] = 95
                    save_kwargs["optimize"] = True
                elif target_format.lower() == "png":
                    save_kwargs["optimize"] = True
                elif target_format.lower() == "webp":
                    save_kwargs["quality"] = 95
                    save_kwargs["method"] = 6

                # Save in target format
                source_image.save(
                    output_buffer, format=target_format.upper(), **save_kwargs
                )

                return output_buffer.getvalue()

            except ImportError:
                logger.warning("PIL not available, trying basic conversion")
                return self._basic_format_conversion(
                    image_data, source_format, target_format
                )

        except Exception as e:
            logger.error(
                "Failed to convert image from %s to %s: %s",
                source_format,
                target_format,
                e,
            )
            return None

    def _basic_format_conversion(
        self, image_data: bytes, source_format: str, target_format: str
    ) -> bytes | None:
        """Basic format conversion without external libraries.

        This provides minimal conversion capabilities for common cases.
        """
        # For now, only support BMP to basic formats
        if source_format.lower() == "bmp" and target_format.lower() == "png":
            return self._convert_bmp_to_png_basic(image_data)
        if source_format.lower() == "ico" and target_format.lower() == "png":
            return self._extract_ico_as_png(image_data)
        logger.warning(
            "Basic conversion from %s to %s not supported",
            source_format,
            target_format,
        )
        return None

    def _convert_bmp_to_png_basic(self, bmp_data: bytes) -> bytes | None:
        """Convert BMP to PNG using basic methods."""
        # This is a simplified conversion - in practice, you'd need full PNG encoding
        # For now, just return the original data (placeholder)
        logger.info("BMP to PNG conversion requested - returning original data")
        return bmp_data

    def _extract_ico_as_png(self, ico_data: bytes) -> bytes | None:
        """Extract first PNG image from ICO file."""
        try:
            # ICO files can contain PNG images directly
            # Look for PNG signature within ICO
            png_offset = ico_data.find(b"\x89PNG\r\n\x1a\n")
            if png_offset != -1:
                # Extract PNG data
                png_end = ico_data.find(b"IEND\xae\x42\x60\x82", png_offset)
                if png_end != -1:
                    return ico_data[png_offset : png_end + 8]

            logger.debug("No embedded PNG found in ICO file")
            return None

        except Exception as e:
            logger.error("Failed to extract PNG from ICO: %s", e)
            return None

    def batch_convert_images(
        self, source_dir: Path, target_dir: Path, target_format: str = "png"
    ) -> dict[str, Any]:
        """Convert all extracted images to a target format.

        Args:
            source_dir: Directory containing extracted images
            target_dir: Directory to save converted images
            target_format: Target format (default: png)

        Returns:
            Dictionary with conversion statistics
        """
        stats: Dict[str, Any] = {
            "total_files": 0,
            "converted": 0,
            "failed": 0,
            "skipped": 0,
            "errors": [],
        }

        target_dir.mkdir(parents=True, exist_ok=True)

        # Find all image files
        image_extensions = {
            ".bmp",
            ".ico",
            ".cur",
            ".jpg",
            ".jpeg",
            ".gif",
            ".png",
            ".webp",
            ".tiff",
            ".pbm",
            ".pbi",
        }

        for image_path in source_dir.rglob("*"):
            if image_path.suffix.lower() in image_extensions:
                stats["total_files"] += 1

                try:
                    # Read original image
                    image_data = image_path.read_bytes()
                    source_format = image_path.suffix[1:]  # Remove dot

                    # Skip if already in target format
                    if source_format.lower() == target_format.lower():
                        stats["skipped"] += 1
                        continue

                    # Convert image
                    converted_data = self.convert_image_format(
                        image_data, source_format, target_format
                    )

                    if converted_data:
                        # Save converted image
                        output_path = target_dir / f"{image_path.stem}.{target_format}"
                        output_path.write_bytes(converted_data)
                        stats["converted"] += 1
                        logger.debug("Converted %s to %s", image_path, output_path)
                    else:
                        stats["failed"] += 1
                        stats["errors"].append(f"Failed to convert {image_path}")

                except Exception as e:
                    stats["failed"] += 1
                    error_msg = f"Error converting {image_path}: {e}"
                    stats["errors"].append(error_msg)
                    logger.error(error_msg)

        logger.info(
            "Batch conversion completed: %d converted, %d failed, %d skipped",
            stats["converted"],
            stats["failed"],
            stats["skipped"],
        )

        return stats


# ============================================================================
# Resource Extraction Manager (from resource_extraction_manager.py)
# ============================================================================


class ResourceExtractionManager:
    """Manages resource extraction across multiple PowerBuilder files."""

    def __init__(self, base_output_dir: Path) -> None:
        """Initialize the resource extraction manager.

        Args:
            base_output_dir: Base directory for all output
        """
        self.base_output_dir = base_output_dir
        self.resources_dir = base_output_dir / "resources"
        self.resources_dir.mkdir(parents=True, exist_ok=True)

        # Initialize unified extractor
        # TODO: Fix circular import with UnifiedResourceExtractor
        # self.extractor = UnifiedResourceExtractor(base_output_dir)
        self.extractor = None

        # Global tracking
        self.all_resources: list[dict[str, Any]] = []
        self.resource_hashes: set[str] = set()
        self.source_file_map: dict[str, list[dict[str, Any]]] = defaultdict(list)
        self.duplicate_count = 0

        # Enhanced statistics
        self.stats: Dict[str, Any] = {
            "total_files_processed": 0,
            "files_with_resources": 0,
            "total_resources": 0,
            "unique_resources": 0,
            "duplicate_resources": 0,
            "resource_types": defaultdict(int),
            "resource_categories": defaultdict(int),
            "total_size": 0,
            "size_by_type": defaultdict(int),
            "size_by_category": defaultdict(int),
            "extraction_errors": 0,
        }

        # Caching infrastructure
        self.cache_dir = base_output_dir / "cache"
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self.cache_enabled = True
        self.cache_max_age = 3600 * 24  # 24 hours in seconds
        self.cache_stats = {
            "hits": 0,
            "misses": 0,
            "writes": 0,
            "evictions": 0,
        }

        # Resource management
        self.resource_registry: dict[
            str, dict[str, Any]
        ] = {}  # hash -> resource metadata
        self.resource_references: dict[str, int] = defaultdict(
            int
        )  # hash -> reference count
        # hash -> last access time
        self.resource_access_times: dict[str, float] = {}
        self.max_memory_usage = 500 * 1024 * 1024  # 500MB max memory usage
        self.current_memory_usage = 0

        # Load existing cache index if available
        self._load_cache_index()

    def extract_from_object(
        self, data: bytes, source_file: str, object_name: str, object_type: str
    ) -> list[dict[str, Any]]:
        """Extract resources from a PowerBuilder object.

        Args:
            data: Object data bytes
            source_file: Source PBL/PBD file name
            object_name: Name of the object
            object_type: Type of the object

        Returns:
            List of extracted resources
        """
        try:
            # Track file processing
            if source_file not in self.source_file_map:
                self.stats["total_files_processed"] += 1

            # Extract resources
            if self.extractor is not None:
                resources = self.extractor.extract_resources_from_data(
                    data,
                    object_name,
                    object_type,
                )
            else:
                resources: Any = []

            if resources:
                self.stats["files_with_resources"] += 1

            # Process each resource
            for resource in resources:
                # Add source file info
                resource["source_file"] = source_file

                # Check for duplicates globally
                if resource["hash"] in self.resource_hashes:
                    self.duplicate_count += 1
                    self.stats["duplicate_resources"] += 1
                    resource["is_duplicate"] = True
                else:
                    self.resource_hashes.add(resource["hash"])
                    self.stats["unique_resources"] += 1
                    resource["is_duplicate"] = False

                # Update statistics
                self.stats["total_resources"] += 1
                self.stats["resource_types"][resource["type"]] += 1

                category = self._get_resource_category(resource["type"])
                self.stats["resource_categories"][category] += 1
                self.stats["size_by_type"][resource["type"]] += resource["size"]
                self.stats["size_by_category"][category] += resource["size"]

                # Track by source file
                self.source_file_map[source_file].append(resource)
                self.all_resources.append(resource)

            return resources

        except Exception as e:
            logger.error("Failed to extract resources from %s: %s", object_name, e)
            self.stats["extraction_errors"] += 1
            return []

    def extract_from_object_cached(
        self, data: bytes, source_file: str, object_name: str, object_type: str
    ) -> list[dict[str, Any]]:
        """Extract resources with caching support.

        Args:
            data: Object data bytes
            source_file: Source PBL/PBD file name
            object_name: Name of the object
            object_type: Type of the object

        Returns:
            List of extracted resources
        """
        if not self.cache_enabled:
            return self.extract_from_object(data, source_file, object_name, object_type)

        # Generate cache key based on data hash and object metadata
        cache_key = self._generate_cache_key(
            data, source_file, object_name, object_type
        )

        # Try to load from cache
        cached_resources = self._load_from_cache(cache_key)
        if cached_resources is not None:
            self.cache_stats["hits"] += 1
            logger.debug("Cache hit for %s in %s", object_name, source_file)
            return cached_resources

        # Cache miss - perform extraction
        self.cache_stats["misses"] += 1
        resources = self.extract_from_object(
            data, source_file, object_name, object_type
        )

        # Cache the results
        if resources:
            self._save_to_cache(cache_key, resources)

        return resources

    def register_resource(self, resource_hash: str, metadata: dict[str, Any]) -> None:
        """Register a resource in the resource registry.

        Args:
        resource_hash: Unique hash of the resource
        metadata: Resource metadata
        """
        self.resource_registry[resource_hash] = {
            **metadata,
            "registered_at": time.time(),
            "last_accessed": time.time(),
        }
        self.resource_references[resource_hash] = 1
        self.resource_access_times[resource_hash] = time.time()

        # Update memory usage estimate
        size = metadata.get("size", 0)
        self.current_memory_usage += size

        # Check if memory cleanup is needed
        if self.current_memory_usage > self.max_memory_usage:
            self._cleanup_resources()

    def get_resource(self, resource_hash: str) -> dict[str, Any] | None:
        """Get resource metadata by hash.

        Args:
        resource_hash: Resource hash

        Returns:
        Resource metadata or None if not found
        """
        if resource_hash in self.resource_registry:
            # Update access time
            self.resource_access_times[resource_hash] = time.time()
            self.resource_registry[resource_hash]["last_accessed"] = time.time()
            return self.resource_registry[resource_hash]
        return None

    def reference_resource(self, resource_hash: str) -> None:
        """Increment reference count for a resource.

        Args:
            resource_hash: Resource hash
        """
        if resource_hash in self.resource_references:
            self.resource_references[resource_hash] += 1
            self.resource_access_times[resource_hash] = time.time()

    def dereference_resource(self, resource_hash: str) -> None:
        """Decrement reference count for a resource.

        Args:
            resource_hash: Resource hash
        """
        if resource_hash in self.resource_references:
            self.resource_references[resource_hash] -= 1
            if self.resource_references[resource_hash] <= 0:
                self._remove_resource(resource_hash)

    def cleanup_cache(self, max_age_seconds: int | None = None) -> int:
        """Clean up old cache entries.

        Args:
        max_age_seconds: Maximum age in seconds (defaults to cache_max_age)

        Returns:
        Number of entries removed
        """
        max_age = max_age_seconds or self.cache_max_age
        current_time = time.time()
        removed_count = 0

        for cache_file in self.cache_dir.glob("*.cache"):
            try:
                stat = cache_file.stat()
                if current_time - stat.st_mtime > max_age:
                    cache_file.unlink()
                    removed_count += 1
                    self.cache_stats["evictions"] += 1
            except Exception as e:
                logger.warning("Failed to remove cache file %s: %s", cache_file, e)

        logger.info("Cleaned up %s old cache entries", removed_count)
        return removed_count

    def get_cache_statistics(self) -> dict[str, Any]:
        """Get cache performance statistics.

        Returns:
        Dictionary of cache statistics
        """
        total_requests = self.cache_stats["hits"] + self.cache_stats["misses"]
        hit_rate = (
            (self.cache_stats["hits"] / total_requests * 100)
            if total_requests > 0
            else 0
        )

        cache_files = list(self.cache_dir.glob("*.cache"))
        cache_size = sum(f.stat().st_size for f in cache_files if f.exists())

        return {
            "enabled": self.cache_enabled,
            "hit_rate_percent": round(hit_rate, 2),
            "total_requests": total_requests,
            "cache_files": len(cache_files),
            "cache_size_bytes": cache_size,
            "cache_size_mb": round(cache_size / 1024 / 1024, 2),
            **self.cache_stats,
        }

    def get_resource_statistics(self) -> dict[str, Any]:
        """Get resource management statistics.

        Returns:
        Dictionary of resource statistics
        """
        total_resources = len(self.resource_registry)
        total_references = sum(self.resource_references.values())

        # Find most referenced resources
        most_referenced = sorted(
            self.resource_references.items(), key=lambda x: x[1], reverse=True
        )[:10]

        # Find recently accessed resources
        recently_accessed = sorted(
            self.resource_access_times.items(), key=lambda x: x[1], reverse=True
        )[:10]

        return {
            "total_resources_managed": total_resources,
            "total_references": total_references,
            "current_memory_usage_bytes": self.current_memory_usage,
            "current_memory_usage_mb": round(
                self.current_memory_usage / 1024 / 1024, 2
            ),
            "max_memory_usage_mb": round(self.max_memory_usage / 1024 / 1024, 2),
            "most_referenced": [(hash[:16], count) for hash, count in most_referenced],
            "recently_accessed": [
                (hash[:16], time.ctime(access_time))
                for hash, access_time in recently_accessed
            ],
        }

    def _generate_cache_key(
        self, data: bytes, source_file: str, object_name: str, object_type: str
    ) -> str:
        """Generate a cache key for the given parameters."""
        # Create a hash from the data and metadata
        hasher = hashlib.sha256()
        hasher.update(data)
        hasher.update(source_file.encode())
        hasher.update(object_name.encode())
        hasher.update(object_type.encode())

        return hasher.hexdigest()[:16]  # Use first 16 chars for filename

    def _load_from_cache(self, cache_key: str) -> list[dict[str, Any]] | None:
        """Load resources from cache."""
        cache_file = self.cache_dir / f"{cache_key}.cache"

        if not cache_file.exists():
            return None

        try:
            # Check if cache is too old
            stat = cache_file.stat()
            if time.time() - stat.st_mtime > self.cache_max_age:
                cache_file.unlink()  # Remove expired cache
                return None

            with Path(cache_file).open("rb") as f:
                return pickle.load(f)

        except Exception as e:
            logger.warning("Failed to load cache %s: %s", cache_key, e)
            # Remove corrupted cache file
            with contextlib.suppress(Exception):
                cache_file.unlink()
            return None

    def _save_to_cache(self, cache_key: str, resources: list[dict[str, Any]]) -> None:
        """Save resources to cache."""
        cache_file = self.cache_dir / f"{cache_key}.cache"

        try:
            with Path(cache_file).open("wb") as f:
                pickle.dump(resources, f, protocol=pickle.HIGHEST_PROTOCOL)

            self.cache_stats["writes"] += 1

        except Exception as e:
            logger.warning("Failed to save cache %s: %s", cache_key, e)

    def _load_cache_index(self) -> None:
        """Load cache index from disk."""
        index_file = self.cache_dir / "cache_index.json"

        if index_file.exists():
            try:
                with Path(index_file).open() as f:
                    data = json.load(f)
                self.cache_stats.update(data.get("stats", {}))
                logger.debug("Loaded cache index")
            except Exception as e:
                logger.warning("Failed to load cache index: %s", e)

    def _save_cache_index(self) -> None:
        """Save cache index to disk."""
        index_file = self.cache_dir / "cache_index.json"

        try:
            index_data = {
                "stats": self.cache_stats,
                "saved_at": time.time(),
            }

            with Path(index_file).open("w") as f:
                json.dump(index_data, f, indent=2)

        except Exception as e:
            logger.warning("Failed to save cache index: %s", e)

    def _cleanup_resources(self) -> None:
        """Clean up resources to free memory."""
        logger.info("Performing resource cleanup to free memory")

        # Sort by access time (oldest first) and low reference count
        candidates = []
        for resource_hash in self.resource_registry:
            access_time = self.resource_access_times.get(resource_hash, 0)
            ref_count = self.resource_references.get(resource_hash, 0)
            size = self.resource_registry[resource_hash].get("size", 0)

            # Score for cleanup (higher score = better candidate for removal)
            score = (time.time() - access_time) / max(ref_count, 1) * size
            candidates.append((resource_hash, score))

        # Sort by score (highest first) and remove resources
        candidates.sort(key=lambda x: x[1], reverse=True)

        target_reduction = self.current_memory_usage - (
            self.max_memory_usage * 0.8
        )  # Reduce to 80% of max
        freed_memory = 0
        removed_count = 0

        for resource_hash, _ in candidates:
            if freed_memory >= target_reduction:
                break

            size = self.resource_registry[resource_hash].get("size", 0)
            self._remove_resource(resource_hash)
            freed_memory += size
            removed_count += 1

        logger.info(
            "Cleaned up %d resources, freed %.2f MB",
            removed_count,
            freed_memory / 1024 / 1024,
        )

    def _remove_resource(self, resource_hash: str) -> None:
        """Remove a resource from the registry."""
        if resource_hash in self.resource_registry:
            size = self.resource_registry[resource_hash].get("size", 0)
            self.current_memory_usage -= size

            del self.resource_registry[resource_hash]
            del self.resource_references[resource_hash]
            del self.resource_access_times[resource_hash]

    def _get_resource_category(self, resource_type: str) -> str:
        """Get category for a resource type."""
        # Define resource categories
        category_map = {
            "image": ["png", "jpg", "jpeg", "gif", "bmp", "ico", "cur", "tiff", "webp"],
            "text": ["txt", "log", "md", "xml", "json", "yaml", "yml"],
            "code": ["pb", "sru", "srw", "srd", "srm", "srf", "src"],
            "binary": ["dll", "exe", "pbd", "pbl"],
            "data": ["csv", "dat", "db"],
        }

        for category, types in category_map.items():
            if resource_type.lower() in types:
                return category

        return "other"

    def generate_comprehensive_report(self) -> None:
        """Generate comprehensive extraction report and manifests."""
        # Update total size
        if self.extractor is not None:
            self.stats["total_size"] = self.extractor.stats["total_size"]
        else:
            self.stats["total_size"] = 0

        # Generate main manifest
        self._generate_main_manifest()

        # Generate detailed resource catalog
        self._generate_detailed_catalog()

        # Generate source file report
        self._generate_source_file_report()

        # Generate statistics report
        self._generate_statistics_report()

        # Generate caching and resource management reports
        self._generate_cache_report()
        self._generate_resource_management_report()

        # Let the extractor generate its own reports
        if self.extractor is not None:
            self.extractor.generate_manifest()

        # Save cache index for future sessions
        self._save_cache_index()

        logger.info(
            "Resource extraction complete: %d total resources "
            "(%d unique, %d duplicates) "
            "from %d files",
            self.stats["total_resources"],
            self.stats["unique_resources"],
            self.stats["duplicate_resources"],
            self.stats["total_files_processed"],
        )

    def _generate_main_manifest(self) -> None:
        """Generate the main resource manifest."""
        manifest_path = self.resources_dir / "extraction_manifest.json"

        manifest = {
            "extraction_summary": {
                "total_files_processed": self.stats["total_files_processed"],
                "files_with_resources": self.stats["files_with_resources"],
                "total_resources_found": self.stats["total_resources"],
                "unique_resources": self.stats["unique_resources"],
                "duplicate_resources": self.stats["duplicate_resources"],
                "total_size_bytes": self.stats["total_size"],
                "extraction_errors": self.stats["extraction_errors"],
            },
            "resource_types": dict(self.stats["resource_types"]),
            "resource_categories": dict(self.stats["resource_categories"]),
            "size_by_type": dict(self.stats["size_by_type"]),
            "size_by_category": dict(self.stats["size_by_category"]),
        }

        with Path(manifest_path).open("w") as f:
            json.dump(manifest, f, indent=2)

    def _generate_detailed_catalog(self) -> None:
        """Generate detailed resource catalog."""
        catalog_path = self.resources_dir / "detailed_resource_catalog.json"

        # Group resources by various criteria
        by_type = defaultdict(list)
        by_category = defaultdict(list)
        by_source = defaultdict(list)

        for resource in self.all_resources:
            # Simplified resource info for catalog
            resource_info = {
                "id": resource["id"],
                "type": resource["type"],
                "size": resource["size"],
                "source_object": resource["source_object"],
                "source_file": resource.get("source_file", "unknown"),
                "path": resource["path"],
                "is_duplicate": resource.get("is_duplicate", False),
                "metadata": resource.get("metadata", {}),
            }

            by_type[resource["type"]].append(resource_info)
            category = self._get_resource_category(resource["type"])
            by_category[category].append(resource_info)
            by_source[resource.get("source_file", "unknown")].append(resource_info)

        catalog: Dict[str, Any] = {
            "by_type": dict(by_type),
            "by_category": dict(by_category),
            "by_source": dict(by_source),
        }

        with Path(catalog_path).open("w") as f:
            json.dump(catalog, f, indent=2)

    def _generate_source_file_report(self) -> None:
        """Generate report grouped by source files."""
        report_path = self.resources_dir / "source_file_report.txt"

        with report_path.open("w") as f:
            f.write("PowerBuilder Resource Extraction - Source File Report\n")
            f.write("=" * 70 + "\n\n")

            for source_file, resources in sorted(self.source_file_map.items()):
                f.write(f"Source File: {source_file}\n")
                f.write(f"Resources Found: {len(resources)}\n")

                # Group by type
                type_counts: dict[str, int] = defaultdict(int)
                total_size = 0
                for resource in resources:
                    type_counts[resource["type"]] += 1
                    total_size += resource["size"]

                f.write(f"Total Size: {total_size:,} bytes\n")
                f.write("Resource Types:\n")
                for res_type, count in sorted(type_counts.items()):
                    f.write(f"  - {res_type}: {count}\n")
                f.write("\n")

    def _generate_statistics_report(self) -> None:
        """Generate detailed statistics report."""
        report_path = self.resources_dir / "extraction_statistics.txt"

        with report_path.open("w") as f:
            f.write("PowerBuilder Resource Extraction - Statistics Report\n")
            f.write("=" * 70 + "\n\n")

            f.write("Overall Statistics:\n")
            f.write(f"  Total Files Processed: {self.stats['total_files_processed']}\n")
            f.write(f"  Files with Resources: {self.stats['files_with_resources']}\n")
            f.write(f"  Total Resources Found: {self.stats['total_resources']}\n")
            f.write(f"  Unique Resources: {self.stats['unique_resources']}\n")
            f.write(f"  Duplicate Resources: {self.stats['duplicate_resources']}\n")
            f.write(
                f"  Total Size: {self.stats['total_size']:,} bytes ({self.stats['total_size'] / 1024 / 1024:.2f} MB)\n"
            )
            f.write(f"  Extraction Errors: {self.stats['extraction_errors']}\n\n")

            f.write("Resources by Category:\n")
            for category, count in sorted(self.stats["resource_categories"].items()):
                size = self.stats["size_by_category"][category]
                f.write(f"  {category}: {count} resources ({size:,} bytes)\n")

            f.write("\nResources by Type:\n")
            for res_type, count in sorted(self.stats["resource_types"].items()):
                size = self.stats["size_by_type"][res_type]
                f.write(f"  {res_type}: {count} resources ({size:,} bytes)\n")

            if self.stats["extraction_errors"] > 0:
                f.write(
                    f"\nWarning: {self.stats['extraction_errors']} extraction errors occurred.\n"
                )
                f.write("Check the log files for details.\n")

    def _generate_cache_report(self) -> None:
        """Generate cache performance report."""
        report_path = self.resources_dir / "cache_performance.txt"
        cache_stats = self.get_cache_statistics()

        with report_path.open("w") as f:
            f.write("PowerBuilder Resource Extraction - Cache Performance Report\n")
            f.write("=" * 70 + "\n\n")

            f.write(f"Cache Enabled: {cache_stats['enabled']}\n")
            f.write(f"Hit Rate: {cache_stats['hit_rate_percent']:.2f}%\n")
            f.write(f"Total Requests: {cache_stats['total_requests']}\n")
            f.write(f"Cache Hits: {cache_stats['hits']}\n")
            f.write(f"Cache Misses: {cache_stats['misses']}\n")
            f.write(f"Cache Writes: {cache_stats['writes']}\n")
            f.write(f"Cache Evictions: {cache_stats['evictions']}\n")
            f.write(f"Cache Files: {cache_stats['cache_files']}\n")
            f.write(f"Cache Size: {cache_stats['cache_size_mb']:.2f} MB\n\n")

            # Performance recommendations
            f.write("Performance Recommendations:\n")
            if cache_stats["hit_rate_percent"] < 50:
                f.write(
                    "- Low cache hit rate. Consider increasing cache retention time.\n"
                )
            if cache_stats["cache_size_mb"] > 100:
                f.write("- Large cache size. Consider periodic cleanup.\n")
            if cache_stats["evictions"] > cache_stats["writes"] * 0.1:
                f.write("- High eviction rate. Consider increasing cache storage.\n")

    def _generate_resource_management_report(self) -> None:
        """Generate resource management report."""
        report_path = self.resources_dir / "resource_management.txt"
        resource_stats = self.get_resource_statistics()

        with report_path.open("w") as f:
            f.write("PowerBuilder Resource Extraction - Resource Management Report\n")
            f.write("=" * 70 + "\n\n")

            f.write("Resource Registry Statistics:\n")
            f.write(
                f"  Total Resources Managed: {resource_stats['total_resources_managed']}\n"
            )
            f.write(f"  Total References: {resource_stats['total_references']}\n")
            f.write(
                f"  Current Memory Usage: {resource_stats['current_memory_usage_mb']:.2f} MB\n"
            )
            f.write(
                f"  Maximum Memory Limit: {resource_stats['max_memory_usage_mb']:.2f} MB\n"
            )

            memory_usage_percent = (
                resource_stats["current_memory_usage_mb"]
                / resource_stats["max_memory_usage_mb"]
                * 100
            )
            f.write(f"  Memory Usage: {memory_usage_percent:.1f}% of limit\n\n")

            f.write("Most Referenced Resources:\n")
            for hash_prefix, count in resource_stats["most_referenced"][:5]:
                f.write(f"  {hash_prefix}... : {count} references\n")

            f.write("\nRecently Accessed Resources:\n")
            for hash_prefix, access_time in resource_stats["recently_accessed"][:5]:
                f.write(f"  {hash_prefix}... : {access_time}\n")

            f.write("\nMemory Management:\n")
            if memory_usage_percent > 80:
                f.write("- High memory usage. Resource cleanup may be triggered.\n")
            elif memory_usage_percent < 20:
                f.write("- Low memory usage. Good resource efficiency.\n")
            else:
                f.write("- Normal memory usage levels.\n")

    def cleanup(self) -> None:
        """Cleanup resources and save state before shutdown."""
        logger.info("Cleaning up resource extraction manager")

        # Save cache index
        self._save_cache_index()

        # Optional: Clean up old cache files
        removed = self.cleanup_cache()
        if removed > 0:
            logger.info("Cleaned up %s old cache entries during shutdown", removed)

        # Clear in-memory resources
        self.resource_registry.clear()
        self.resource_references.clear()
        self.resource_access_times.clear()
        self.current_memory_usage = 0

        logger.info("Resource extraction manager cleanup complete")
