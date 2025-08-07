"""String resource extraction from PowerBuilder compiled objects.

This module provides functionality to extract string resources from P-code files,
including literal strings, property values, and string tables.
"""

import logging
import re
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
