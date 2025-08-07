"""Consolidated resource extraction functionality for PowerBuilder files.

This module combines functionality from:
- strings.py - String resource extraction
- images.py - Enhanced image extraction
- resources.py - Unified resource extraction
- text.py - Text extraction utilities
- binary.py - Binary resource extractors (already consolidated)
"""

import hashlib
import json
import logging
import re
import struct
import time
from io import BytesIO
from pathlib import Path
from typing import Any, Dict

import chardet

from src.extract.pbd.catalog import ResourceCatalog
from src.extract.pbd.text import (
    _extract_ascii_strings,
    _extract_pb_export_section,
    _extract_pb_patterns,
    _extract_utf16_strings,
)

logger = logging.getLogger(__name__)


# ============================================================================
# Text extraction utilities (from text.py) - functions imported above
# ============================================================================


def binary_to_readable_format(input_path: Path, output_path: Path) -> bool:
    """Convert PowerBuilder binary file to readable text format.

    Args:
        input_path: Path to binary file
        output_path: Path to save text output

    Returns:
        True if successful, False otherwise
    """
    try:
        # Read binary data
        with input_path.open("rb") as f:
            data = f.read()

        # Extract all readable text
        text_parts = []

        # Try to extract PowerBuilder export section first
        export_section = _extract_pb_export_section(data)
        if export_section:
            text_parts.append("=== PowerBuilder Export Section ===\n" + export_section)

        # Extract ASCII strings
        ascii_strings = _extract_ascii_strings(data)
        if ascii_strings:
            text_parts.append("\n=== ASCII Strings ===\n" + ascii_strings)

        # Extract UTF-16 strings
        utf16_strings = _extract_utf16_strings(data)
        if utf16_strings:
            text_parts.append(utf16_strings)

        # Extract PowerBuilder patterns
        pb_patterns = _extract_pb_patterns(data)
        if pb_patterns:
            text_parts.append(pb_patterns)

        # Write to output file
        output_text = "\n".join(text_parts)
        output_path.write_text(output_text, encoding="utf-8")

        return True

    except Exception as e:
        logging.error("Failed to convert binary to text: %s", e)
        return False


# ============================================================================
# String Resource Extractor (from strings.py)
# ============================================================================


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

        # Processing: catch specific exceptions when possible
        except (ValueError, TypeError, OSError, ImportError) as e:
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
                        if len(candidate) >= 6:  # Minimum meaningful UTF-16 string
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
        data_hash = hash(data)
        if data_hash in self.encoding_cache:
            self.extraction_stats["cache_hits"] += 1
            return self.encoding_cache[data_hash]

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
                self.encoding_cache[data_hash] = detected_encoding
                return detected_encoding

        except Exception as e:
            logger.debug("Encoding detection failed: %s", e)

        # Cache negative result
        self.encoding_cache[data_hash] = None
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
                    decoded = self._decode_string_enhanced(string_data, None)

                    if decoded and self._is_valid_string_enhanced(decoded):
                        strings.append((index, decoded))
                        index += 1
                        offset += 2 + length
                        continue

            # 4-byte length (little endian)
            if offset + 4 < len(data):
                length = int.from_bytes(data[offset : offset + 4], "little")

                if 0 < length < 10000 and offset + 4 + length <= len(data):
                    string_data = data[offset + 4 : offset + 4 + length]
                    decoded = self._decode_string_enhanced(string_data, None)

                    if decoded and self._is_valid_string_enhanced(decoded):
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
        string_counts = {}
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


# ============================================================================
# Enhanced Image Extractor (from images.py)
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
        b"\x00\x00\x02\x00": ("cur", 4),
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
# Resource Type and Category Constants (from resources.py)
# ============================================================================


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


# ============================================================================
# Unified Resource Extractor (from resources.py)
# ============================================================================


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
        self.stats = {
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
                metadata["width"] = data[6] or 256
                metadata["height"] = data[7] or 256
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

        manifest: Dict[str, Any] = {
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


# ============================================================================
# Helper function to extract embedded images (from structures.py)
# ============================================================================


def extract_embedded_images(
    data_bytes: bytes, base_filename: str, output_resource_dir: Path
) -> list[Path]:
    """Extract embedded images from binary data.

    Args:
        data_bytes: Binary data that may contain embedded images
        base_filename: Base name for extracted files (e.g., menu name)
        output_resource_dir: Directory to save extracted images

    Returns:
        List of paths to extracted image files
    """
    extractor = EnhancedImageExtractor()

    saved_files = []
    try:
        images = extractor.find_images_in_data(data_bytes, base_filename)

        for i, image_info in enumerate(images):
            # Generate filename based on format and index
            image_filename = (
                f"{Path(base_filename).stem}_image_{i}.{image_info['format']}"
            )
            image_path = output_resource_dir / image_filename

            # Save the image data
            image_path.write_bytes(image_info["data"])
            saved_files.append(image_path)

            logger.debug(
                "Extracted %s image (%d bytes) to %s",
                image_info["format"],
                image_info["size"],
                image_path,
            )

    except Exception as e:
        logger.error(
            "Failed to extract images from %s: %s", base_filename, e, exc_info=True
        )

    return saved_files
