"""Consolidated DataWindow detection and validation utilities.

This module consolidates DataWindow-related functionality from:
- extract/pbd_core/datawindow.py
- decompile/analysis/datawindow_extractor.py
"""

import logging
import re
from typing import Any, ClassVar

from src.core.constants import BUFFER_SIZE

logger = logging.getLogger(__name__)


class DataWindowDetector:
    """Unified DataWindow detection and validation logic."""

    # Binary signatures for DataWindow objects
    BINARY_SIGNATURES: ClassVar[list[bytes]] = [
        b"DWHD",  # DataWindow header
        b"\x00\x00\x00\x00DWHD",  # Alternative header format
        b"\xff\xfe",  # UTF-16 BOM
        b"\xfe\xff",  # UTF-16 BE BOM
    ]

    # Text signatures for exported DataWindows
    TEXT_SIGNATURES: ClassVar[list[bytes]] = [
        b"release ",
        b"HA$PBExportHeader$",
        b"$PBExportComments$",
        b"datawindow(",
        b"table(",
        b"column(",
    ]

    # DataWindow format patterns
    FORMAT_PATTERNS: ClassVar[dict[str, re.Pattern[str]]] = {
        "grid": re.compile(r'processing="1".*grid\.', re.IGNORECASE | re.DOTALL),
        "tabular": re.compile(r'processing="1"', re.IGNORECASE),
        "freeform": re.compile(r'processing="0"', re.IGNORECASE),
        "label": re.compile(r'processing="2"', re.IGNORECASE),
        "graph": re.compile(r"graph\s*\(", re.IGNORECASE),
        "crosstab": re.compile(r"crosstab\s*\(", re.IGNORECASE),
        "ole": re.compile(r"ole\s*\(", re.IGNORECASE),
        "richtext": re.compile(r"richtext\s*\(", re.IGNORECASE),
    }

    # Markers for DataWindow sections
    SECTION_MARKERS: ClassVar[dict[str, bytes]] = {
        "header": b"$PBExportHeader$",
        "comments": b"$PBExportComments$",
        "start": b"Start of PowerBuilder Binary Data Section",
        "end": b"\x00\x00",
    }

    @classmethod
    def detect_format(
        cls, data: bytes, max_check_bytes: int = BUFFER_SIZE
    ) -> str | None:
        """Detect DataWindow format from binary data.

        Args:
            data: Binary data to check
            max_check_bytes: Maximum bytes to examine

        Returns:
            Format type ('binary', 'text', or None if not detected)
        """
        # Check only the beginning of the data for efficiency
        check_data = data[:max_check_bytes]

        # Check for binary signatures
        for sig in cls.BINARY_SIGNATURES:
            if sig in check_data:
                logger.debug("Detected binary DataWindow signature: %s", sig)
                return "binary"

        # Check for text signatures
        for sig in cls.TEXT_SIGNATURES:
            if sig in check_data:
                logger.debug("Detected text DataWindow signature: %s", sig)
                return "text"

        return None

    @classmethod
    def _detect_encoding(cls, data: bytes) -> tuple[str | None, str | None]:
        """Detect encoding from BOM or by trying common encodings.

        Returns:
            Tuple of (encoding, decoded_text)
        """
        # Detect encoding from BOM
        if data.startswith(b"\xff\xfe"):
            return "utf-16-le", None
        if data.startswith(b"\xfe\xff"):
            return "utf-16-be", None
        if data.startswith(b"\xef\xbb\xbf"):
            return "utf-8", None

        # Try common encodings
        for encoding in ["utf-8", "utf-16-le", "latin-1"]:
            try:
                text = data.decode(encoding, errors="strict")
            except UnicodeDecodeError:
                continue
            else:
                return encoding, text

        # Fallback
        text = data.decode("latin-1", errors="ignore")
        return "latin-1", text

    @classmethod
    def _extract_text_metadata(cls, text: str) -> dict[str, any]:
        """Extract metadata from decoded text.

        Returns:
            Dictionary with type, table_count, column_count, has_syntax
        """
        result = {
            "type": None,
            "table_count": 0,
            "column_count": 0,
            "has_syntax": False,
        }

        # Detect DataWindow type
        for dw_type, pattern in cls.FORMAT_PATTERNS.items():
            if pattern.search(text):
                result["type"] = dw_type
                break

        # Count tables and columns
        text_lower = text.lower()
        result["table_count"] = text_lower.count("table(")
        result["column_count"] = text_lower.count("column(")

        # Check for syntax section
        if "syntax=" in text_lower:
            result["has_syntax"] = True

        return result

    @classmethod
    def extract_metadata(cls, data: bytes) -> dict[str, Any]:
        """Extract metadata from DataWindow data.

        Args:
            data: DataWindow data (binary or text)

        Returns:
            Dictionary containing extracted metadata
        """
        metadata = {
            "format": cls.detect_format(data),
            "type": None,
            "has_syntax": False,
            "has_header": False,
            "encoding": None,
            "table_count": 0,
            "column_count": 0,
        }

        if not metadata["format"]:
            return metadata

        # Check for header markers
        if cls.SECTION_MARKERS["header"] in data:
            metadata["has_header"] = True

        # Detect encoding and decode text
        try:
            encoding, text = cls._detect_encoding(data)
            metadata["encoding"] = encoding

            # If we couldn't decode in the helper, try with the detected encoding
            if text is None and encoding:
                text = data.decode(encoding, errors="ignore")

            # Extract text-based metadata
            if text:
                text_metadata = cls._extract_text_metadata(text)
                metadata.update(text_metadata)

        except (UnicodeDecodeError, AttributeError) as e:
            logger.debug("Error extracting text metadata: %s", e)

        return metadata

    @classmethod
    def validate_syntax(cls, syntax: str) -> tuple[bool, list[str]]:
        """Validate DataWindow syntax.

        Args:
            syntax: DataWindow syntax string

        Returns:
            Tuple of (is_valid, list_of_issues)
        """
        issues = []

        # Check for required keywords
        required_keywords = ["release", "datawindow"]
        syntax_lower = syntax.lower()

        issues.extend(
            f"Missing required keyword: {keyword}"
            for keyword in required_keywords
            if keyword not in syntax_lower
        )

        # Check for basic structure
        if syntax.count("(") != syntax.count(")"):
            issues.append("Mismatched parentheses")

        # Check for at least one table or external source
        if "table(" not in syntax_lower and "external(" not in syntax_lower:
            issues.append("No data source defined (table or external)")

        # Check for columns if table is defined
        if "table(" in syntax_lower and "column=" not in syntax_lower:
            issues.append("Table defined but no columns")

        return len(issues) == 0, issues

    @classmethod
    def extract_sql(cls, syntax: str) -> str | None:
        """Extract SQL statement from DataWindow syntax.

        Args:
            syntax: DataWindow syntax string

        Returns:
            SQL statement if found, None otherwise
        """
        # Look for retrieve attribute (handle escaped quotes)
        retrieve_match = re.search(
            r'retrieve\s*=\s*"((?:[^"~]|~.)*)"',
            syntax,
            re.IGNORECASE | re.DOTALL,
        )

        if retrieve_match:
            sql = retrieve_match.group(1)
            # Unescape quotes
            sql = sql.replace('~"', '"')
            return sql.strip()

        return None

    @classmethod
    def is_datawindow_file(cls, filename: str) -> bool:
        """Check if filename indicates a DataWindow file.

        Args:
            filename: File name to check

        Returns:
            True if likely a DataWindow file
        """
        filename_lower = filename.lower()

        # Check extension
        if filename_lower.endswith(".srd"):
            return True

        # Check for DataWindow naming patterns
        dw_patterns = [
            r"^d_\w+",  # d_customer
            r"^dw_\w+",  # dw_customer
            r"^dwo_\w+",  # dwo_customer
            r"_dw(?:\.\w+)?$",  # customer_dw or customer_dw.psr
            r"_dwo(?:\.\w+)?$",  # customer_dwo or customer_dwo.psr
        ]

        # Use list comprehension for better performance
        matches = [bool(re.search(pattern, filename_lower)) for pattern in dw_patterns]
        return any(matches)
