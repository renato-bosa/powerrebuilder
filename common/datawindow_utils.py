"""Consolidated DataWindow detection and validation utilities.

This module consolidates DataWindow-related functionality from:
- extract/pbd_core/datawindow.py
- decompile/analysis/datawindow_extractor.py
"""

import logging
import re

logger = logging.getLogger(__name__)


class DataWindowDetector:
    """Unified DataWindow detection and validation logic."""

    # Binary signatures for DataWindow objects
    BINARY_SIGNATURES = [
        b"DWHD",  # DataWindow header
        b"\x00\x00\x00\x00DWHD",  # Alternative header format
        b"\xff\xfe",  # UTF-16 BOM
        b"\xfe\xff",  # UTF-16 BE BOM
    ]

    # Text signatures for exported DataWindows
    TEXT_SIGNATURES = [
        b"release ",
        b"HA$PBExportHeader$",
        b"$PBExportComments$",
        b"datawindow(",
        b"table(",
        b"column(",
    ]

    # DataWindow format patterns
    FORMAT_PATTERNS = {
        "grid": re.compile(r'processing="[01]"', re.IGNORECASE),
        "tabular": re.compile(r'processing="1"', re.IGNORECASE),
        "freeform": re.compile(r'processing="0"', re.IGNORECASE),
        "label": re.compile(r'processing="2"', re.IGNORECASE),
        "graph": re.compile(r"graph\s*\(", re.IGNORECASE),
        "crosstab": re.compile(r"crosstab\s*\(", re.IGNORECASE),
        "ole": re.compile(r"ole\s*\(", re.IGNORECASE),
        "richtext": re.compile(r"richtext\s*\(", re.IGNORECASE),
    }

    # Markers for DataWindow sections
    SECTION_MARKERS = {
        "header": b"$PBExportHeader$",
        "comments": b"$PBExportComments$",
        "start": b"Start of PowerBuilder Binary Data Section",
        "end": b"\x00\x00",
    }

    @classmethod
    def detect_format(cls, data: bytes, max_check_bytes: int = 4096) -> str | None:
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
                logger.debug(f"Detected binary DataWindow signature: {sig}")
                return "binary"

        # Check for text signatures
        for sig in cls.TEXT_SIGNATURES:
            if sig in check_data:
                logger.debug(f"Detected text DataWindow signature: {sig}")
                return "text"

        return None

    @classmethod
    def extract_metadata(cls, data: bytes) -> dict[str, any]:
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

        # Detect encoding from BOM
        if data.startswith(b"\xff\xfe"):
            metadata["encoding"] = "utf-16-le"
        elif data.startswith(b"\xfe\xff"):
            metadata["encoding"] = "utf-16-be"
        elif data.startswith(b"\xef\xbb\xbf"):
            metadata["encoding"] = "utf-8"

        # Try to extract type and other info from text
        try:
            # Decode based on detected encoding or try common ones
            if metadata["encoding"]:
                text = data.decode(metadata["encoding"], errors="ignore")
            else:
                # Try UTF-16 first (common for PB), then fallback
                for encoding in ["utf-16-le", "utf-8", "latin-1"]:
                    try:
                        text = data.decode(encoding, errors="strict")
                        metadata["encoding"] = encoding
                        break
                    except UnicodeDecodeError:
                        continue
                else:
                    text = data.decode("latin-1", errors="ignore")

            # Detect DataWindow type
            for dw_type, pattern in cls.FORMAT_PATTERNS.items():
                if pattern.search(text):
                    metadata["type"] = dw_type
                    break

            # Count tables and columns
            metadata["table_count"] = text.lower().count("table(")
            metadata["column_count"] = text.lower().count("column(")

            # Check for syntax section
            if "syntax=" in text.lower():
                metadata["has_syntax"] = True

        except Exception as e:
            logger.debug(f"Error extracting text metadata: {e}")

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

        for keyword in required_keywords:
            if keyword not in syntax_lower:
                issues.append(f"Missing required keyword: {keyword}")

        # Check for basic structure
        if syntax.count("(") != syntax.count(")"):
            issues.append("Mismatched parentheses")

        # Check for at least one table or external source
        if "table(" not in syntax_lower and "external(" not in syntax_lower:
            issues.append("No data source defined (table or external)")

        # Check for columns if table is defined
        if "table(" in syntax_lower and "column(" not in syntax_lower:
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
        # Look for retrieve attribute
        retrieve_match = re.search(
            r'retrieve\s*=\s*"([^"]+)"',
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
            r"_dw$",  # customer_dw
            r"_dwo$",  # customer_dwo
        ]

        return any(re.search(pattern, filename_lower) for pattern in dw_patterns)
