"""Enhanced PDW (Compiled PowerBuilder DataWindow) extractor.

This module extracts not just SQL but also metadata, column definitions,
and other structural information from compiled PDW files.
"""

import logging
import struct
from dataclasses import dataclass
from typing import Any

from decompile.analysis.pdw_sql_extractor import PDWSQLExtractor

logger = logging.getLogger(__name__)


@dataclass
class PDWColumn:
    """Represents a column definition extracted from PDW."""
    name: str
    type: str = ""
    width: int = 0
    position: int = 0
    display_name: str = ""


@dataclass
class PDWStructure:
    """Complete structure extracted from a PDW file."""
    version: str
    sql: str | None = None
    columns: list[PDWColumn] = None
    tables: list[str] = None
    properties: dict[str, Any] = None
    binary_regions: list[tuple[int, int, str]] = None  # (start, end, description)

    def __post_init__(self) -> None:
        """Initialize mutable default values."""
        if self.columns is None:
            self.columns = []
        if self.tables is None:
            self.tables = []
        if self.properties is None:
            self.properties = {}
        if self.binary_regions is None:
            self.binary_regions = []


class EnhancedPDWExtractor:
    """Extract comprehensive information from compiled PDW files."""

    # Known PDW structure offsets (based on analysis)
    HEADER_SIZE = 0x20

    # Structure markers
    STRING_TABLE_MARKER = 0x0b20  # Where UTF-16 strings often start

    @staticmethod
    def extract_pdw_structure(data: bytes, object_name: str = "") -> PDWStructure:
        """Extract complete structure from PDW file.

        Args:
            data: Raw PDW file data
            object_name: Name of the DataWindow object for logging

        Returns:
            PDWStructure with all extracted information
        """
        logger.info("Extracting enhanced structure from PDW file: %s", object_name)

        # Get version
        version = EnhancedPDWExtractor._extract_version(data)
        structure = PDWStructure(version=version)

        # Extract SQL using existing extractor
        sql = PDWSQLExtractor.extract_sql_from_pdw(data, object_name)
        if sql:
            structure.sql = sql
            # Parse tables and basic columns from SQL
            # Extract tables from SQL (using a custom implementation)
            structure.tables = EnhancedPDWExtractor._extract_tables_from_sql(sql)

        # Extract column definitions from binary structure
        columns = EnhancedPDWExtractor._extract_column_definitions(data)
        if columns:
            structure.columns = columns

        # Extract properties
        properties = EnhancedPDWExtractor._extract_properties(data)
        if properties:
            structure.properties = properties

        # Map binary regions
        structure.binary_regions = EnhancedPDWExtractor._map_binary_regions(data)

        return structure

    @staticmethod
    def _extract_tables_from_sql(sql: str) -> list[str]:
        """Extract table names from SQL text."""
        import re
        tables = []

        # Simple regex extraction
        from_pattern = r'FROM\s+(\w+)'
        matches = re.finditer(from_pattern, sql, re.IGNORECASE)
        tables.extend(match.group(1) for match in matches)

        # Also check for JOIN tables
        join_pattern = r'JOIN\s+(\w+)'
        matches = re.finditer(join_pattern, sql, re.IGNORECASE)
        tables.extend(match.group(1) for match in matches)

        return list(set(tables))

    @staticmethod
    def _extract_version(data: bytes) -> str:
        """Extract PDW version from header."""
        if len(data) < 8:
            return "Unknown"

        header = data[:8]
        if header.startswith(b"PDW"):
            # Version is in the signature itself
            return header.decode("ascii", errors="ignore").strip("\x00")

        return "Unknown"

    @staticmethod
    def _extract_column_definitions(data: bytes) -> list[PDWColumn]:
        """Extract column definitions from PDW binary structure."""
        columns = []

        # Look for column name patterns in UTF-16
        # Based on hex dump, column names appear around 0xb20
        if len(data) > 0xb20:
            # Try to parse string table
            strings = EnhancedPDWExtractor._extract_utf16_strings(data, 0xb20)

            # Column names often end with _id, _name, etc.
            column_patterns = ["_id", "_name", "_code", "_date", "_time", "_flag"]

            for s in strings:
                # Check if it looks like a column name
                s_lower = s.lower()
                if (any(pattern in s_lower for pattern in column_patterns) or "_" in s) and len(s) < 50 and s.replace("_", "").replace(" ", "").isalnum():
                        columns.append(PDWColumn(name=s))

        # Try to extract from SQL if available
        if not columns:
            logger.debug("No columns found in binary structure, trying SQL extraction")

        return columns

    @staticmethod
    def _extract_utf16_strings(data: bytes, start_offset: int = 0) -> list[str]:
        """Extract UTF-16 LE strings from data."""
        strings = []
        i = start_offset

        while i < len(data) - 4:
            # Look for null-terminated UTF-16 strings
            string_data = b""
            j = i

            # Collect bytes until double null (UTF-16 null terminator)
            while j < len(data) - 1:
                two_bytes = data[j:j+2]
                if two_bytes == b"\x00\x00":
                    break
                string_data += two_bytes
                j += 2

            if len(string_data) >= 4:  # At least 2 UTF-16 characters
                try:
                    decoded = string_data.decode("utf-16-le", errors="ignore")
                    # Filter printable strings
                    if decoded and sum(1 for c in decoded if c.isprintable()) > len(decoded) * 0.8:
                        strings.append(decoded.strip())
                        i = j + 2  # Skip past null terminator
                        continue
                except (UnicodeDecodeError, IndexError) as e:
                    logger.debug("Exception caught: %s", e)

            i += 2

        return strings

    @staticmethod
    def _extract_properties(data: bytes) -> dict[str, Any]:
        """Extract DataWindow properties from PDW structure."""
        properties = {}

        # Extract header properties
        if len(data) >= 0x40:
            # Based on analysis, there are often counts/sizes at specific offsets
            try:
                properties["header_value_0x08"] = struct.unpack("<I", data[0x08:0x0C])[0]
                properties["header_value_0x0C"] = struct.unpack("<I", data[0x0C:0x10])[0]

                # Offsets that often contain counts
                if len(data) > 0x34:
                    val = struct.unpack("<I", data[0x30:0x34])[0]
                    if 0 < val < 1000:  # Reasonable range
                        properties["possible_column_count"] = val

            except struct.error:
                pass

        # Look for font information (common in DataWindows)
        if b"Arial" in data:
            properties["has_font_info"] = True

        # Check for specific DataWindow properties
        property_markers = {
            b"[general]": "has_general_section", b"retrieve": "has_retrieve_info", b"update": "has_update_info", b"key": "has_key_definition",
        }

        for marker, prop_name in property_markers.items():
            if marker in data:
                properties[prop_name] = True

        return properties

    @staticmethod
    def _map_binary_regions(data: bytes) -> list[tuple[int, int, str]]:
        """Map the binary structure regions."""
        regions = []

        # Header region
        regions.append((0x00, 0x20, "PDW Header"))

        # Based on common patterns
        if len(data) > 0x100:
            regions.append((0x20, 0x100, "Header Extension/Metadata"))

        # String table region (if present)
        if len(data) > 0xb20:
            # Check if there are UTF-16 strings here
            test_data = data[0xb20:0xb40]
            if b"\x00" in test_data[::2]:  # Looks like UTF-16
                regions.append((0xb20, min(0x1000, len(data)), "String Table (UTF-16)"))

        # SQL region (if found)
        sql_markers = [b"SELECT", b"S\x00E\x00L\x00E\x00C\x00T\x00"]
        for marker in sql_markers:
            idx = data.find(marker)
            if idx >= 0:
                # Find end of SQL
                end_idx = idx + 200  # Default
                for end_marker in [b"\x00\x00\x00", b"FROM treatment"]:
                    end = data.find(end_marker, idx + 10)
                    if end > idx:
                        end_idx = end
                        break
                regions.append((idx, end_idx, "SQL Query"))
                break

        return sorted(regions)

    @staticmethod
    def format_structure_report(structure: PDWStructure) -> str:
        """Format a human-readable report of the extracted structure."""
        lines = []
        lines.append("PDW Structure Report")
        lines.append("=" * 60)
        lines.append(f"Version: {structure.version}")
        lines.append("")

        if structure.sql:
            lines.append("SQL Query:")
            lines.append("-" * 40)
            lines.append(structure.sql)
            lines.append("")

        if structure.tables:
            lines.append("Tables:")
            lines.append("-" * 40)
            lines.extend(f"  - {table}" for table in structure.tables)
            lines.append("")

        if structure.columns:
            lines.append("Columns:")
            lines.append("-" * 40)
            lines.extend(f"  - {col.name}" for col in structure.columns)
            lines.append("")

        if structure.properties:
            lines.append("Properties:")
            lines.append("-" * 40)
            for key, value in structure.properties.items():
                lines.append(f"  {key}: {value}")
            lines.append("")

        if structure.binary_regions:
            lines.append("Binary Structure:")
            lines.append("-" * 40)
            for start, end, desc in structure.binary_regions:
                lines.append(f"  0x{start:04X}-0x{end:04X}: {desc}")

        return "\n".join(lines)
