"""Comprehensive PDW (Compiled PowerBuilder DataWindow) decompiler.

This module extracts all available information from compiled PDW files including:
- SQL queries
- Column definitions with properties
- Layout information (coordinates, sizes)
- Display properties (fonts, colors, alignment)
- DataWindow properties and metadata
"""

import logging
import re
import struct
from dataclasses import dataclass, field
from enum import Enum
from typing import Any

from common.constants import BUFFER_SIZE, HEADER_SIZE, STRING_TABLE_OFFSET

logger = logging.getLogger(__name__)


class Alignment(Enum):
    """Text alignment enumeration."""
    LEFT = 0
    CENTER = 1
    RIGHT = 2
    JUSTIFY = 3


@dataclass
class Rectangle:
    """Represents a rectangular area."""
    x: int
    y: int
    width: int
    height: int

    def __str__(self):


        return f"Rectangle(x={self.x}, y={self.y}, w={self.width}, h={self.height})"


@dataclass
class Color:
    """Represents an RGB color."""
    red: int
    green: int
    blue: int
    alpha: int = 255

    @classmethod
    def from_int(cls, value: int) -> "Color":


        """Create Color from integer value (0xAARRGGBB or 0x00RRGGBB)."""
        alpha = (value >> 24) & 0xFF
        if alpha == 0:
            alpha = 255  # Default to opaque
        red = (value >> 16) & 0xFF
        green = (value >> 8) & 0xFF
        blue = value & 0xFF
        return cls(red, green, blue, alpha)

    def __str__(self):


        if self.alpha == 255:
            return f"RGB({self.red}, {self.green}, {self.blue})"
        return f"RGBA({self.red}, {self.green}, {self.blue}, {self.alpha})"


@dataclass
class Font:
    """Represents font information."""
    name: str = "Arial"
    size: int = 10
    bold: bool = False
    italic: bool = False
    underline: bool = False

    def __str__(self):


        style = []
        if self.bold:
            style.append("Bold")
        if self.italic:
            style.append("Italic")
        if self.underline:
            style.append("Underline")
        style_str = " ".join(style) if style else "Regular"
        return f"{self.name} {self.size}pt {style_str}"


@dataclass
class PDWColumnProperties:
    """Complete column properties extracted from PDW."""
    name: str
    display_name: str | None = None
    db_name: str | None = None
    data_type: str | None = None
    position: int = 0
    bounds: Rectangle | None = None
    font: Font | None = None
    text_color: Color | None = None
    background_color: Color | None = None
    alignment: Alignment = Alignment.LEFT
    format: str | None = None
    visible: bool = True
    editable: bool = True

    def __str__(self):


        parts = [f"Column '{self.name}'"]
        if self.display_name and self.display_name != self.name:
            parts.append(f"Display: '{self.display_name}'")
        if self.bounds:
            parts.append(str(self.bounds))
        if self.font:
            parts.append(str(self.font))
        return ", ".join(parts)


@dataclass
class PDWDataWindow:
    """Complete DataWindow structure extracted from PDW."""
    version: str
    name: str | None = None
    sql: str | None = None
    tables: list[str] = field(default_factory=list)
    columns: list[PDWColumnProperties] = field(default_factory=list)
    properties: dict[str, Any] = field(default_factory=dict)
    window_bounds: Rectangle | None = None
    background_color: Color | None = None

    def get_source_approximation(self) -> str:




        """Generate an approximation of the original DataWindow source."""
        lines = []
        lines.append(f"// Decompiled from {self.version} PDW format")
        lines.append(f"// Note: This is a reconstruction - original source not available")
        lines.append(f"// Extracted: SQL={bool(self.sql)}, Columns={len(self.columns)}, Properties={len(self.properties)}")
        lines.append("")

        # Release/version info
        lines.append(f"release {self.version.replace("PDW", "").strip()}")
        lines.append("")

        # DataWindow declaration
        if self.name:
            lines.append(f"datawindow(name='{self.name}')")
        else:
            lines.append("datawindow()")

        # Window properties
        if self.window_bounds:
            lines.append(f"datawindow.units=0 datawindow.width={self.window_bounds.width} datawindow.height={self.window_bounds.height}")

        if self.background_color:
            lines.append(f"datawindow.color={self._color_to_pb(self.background_color)}")

        # Header section
        lines.append("")
        lines.append("header(height=72 color=536870912)")

        # SQL section
        if self.sql:
            lines.append("")
            lines.append("// SQL Query")
            # Format SQL nicely
            sql_formatted = self.sql.replace("'", "''")
            lines.append(f"table(column=(type=char(1) updatewhereclause=yes name=dummy dbname=\"dummy\" )")
            lines.append(f" retrieve=\"{sql_formatted}\" )")

            if self.tables:
                lines.append(f"// Tables: {", ".join(self.tables)}")
            lines.append("")

        # Column specifications
        if self.columns:
            lines.append("// Column definitions")
            for i, col in enumerate(self.columns):
                lines.append(self._format_column_definition(col, i))
            lines.append("")

        # Text objects for column headers
        if self.columns:
            lines.append("// Column headers")
            for i, col in enumerate(self.columns):
                header_text = col.display_name or col.name
                if col.bounds:
                    lines.append(f"text(band=header alignment=\"{col.alignment.value}\" text=\"{header_text}\" "
                               f"x=\"{col.bounds.x}\" y=\"4\" height=\"64\" width=\"{col.bounds.width}\" "
                               f"name={col.name}_t font.face=\"Arial\" font.height=\"-10\" font.weight=\"700\")")

        # Data section
        lines.append("")
        lines.append("// Data columns")
        for i, col in enumerate(self.columns):
            if col.bounds:
                lines.append(f"column(band=detail id={i+1} alignment=\"{col.alignment.value}\" "
                           f"x=\"{col.bounds.x}\" y=\"4\" height=\"76\" width=\"{col.bounds.width}\" "
                           f"name={col.name} edit.limit=0 edit.case=any edit.autoselect=yes "
                           f"font.face=\"Arial\" font.height=\"-10\")")

        # Summary section
        lines.append("")
        lines.append("summary(height=0 color=536870912)")

        # Footer section
        lines.append("footer(height=0 color=536870912)")

        # Additional properties
        if self.properties:
            lines.append("")
            lines.append("// Additional extracted properties")
            for key, value in self.properties.items():
                lines.append(f"// {key}: {value}")

        return "\n".join(lines)

    def _color_to_pb(self, color: Color) -> int:




        """Convert Color object to PowerBuilder color integer."""
        # PowerBuilder uses BGR format
        return color.blue + (color.green << 8) + (color.red << 16)

    def _format_column_definition(self, col: PDWColumnProperties, index: int) -> str:




        """Format a single column definition."""
        parts = [f"column=(band=detail id={index + 1}"]

        parts.append(f" name=\"{col.name}\"")

        if col.db_name:
            parts.append(f" dbname=\"{col.db_name}\"")

        if col.data_type:
            # Map to PowerBuilder types
            pb_type_map = {
                "string": "char(255)",
                "integer": "number",
                "decimal": "decimal(2)",
                "date": "date",
                "datetime": "datetime",
                "numeric": "number",
            }
            pb_type = pb_type_map.get(col.data_type, col.data_type)
            parts.append(f" type={pb_type}")

        if col.bounds:
            parts.append(f" x=\"{col.bounds.x}\" y=\"{col.bounds.y}\"")
            parts.append(f" width=\"{col.bounds.width}\" height=\"{col.bounds.height}\"")

        if col.alignment != Alignment.LEFT:
            parts.append(f" alignment=\"{col.alignment.value}\"")

        if col.format:
            parts.append(f" format=\"{col.format}\"")

        if col.font:
            parts.append(f" font.face=\"{col.font.name}\" font.height=\"-{col.font.size}\"")
            if col.font.bold:
                parts.append(" font.weight=\"700\"")
            if col.font.italic:
                parts.append(" font.italic=\"1\"")

        if col.text_color:
            parts.append(f" color=\"{self._color_to_pb(col.text_color)}\"")

        if col.background_color:
            parts.append(f" background.color=\"{self._color_to_pb(col.background_color)}\"")

        if not col.visible:
            parts.append(" visible=\"0\"")

        if not col.editable:
            parts.append(" edit.displayonly=\"yes\"")

        parts.append(")")
        return "".join(parts)


class PDWComprehensiveExtractor:
    """Extract all available information from compiled PDW files."""

    # Known structure offsets and patterns
    HEADER_SIZE = 0x20
    STRING_TABLE_START = STRING_TABLE_OFFSET  # Common location for string tables

    @classmethod
    def decompile_pdw(cls, data: bytes, filename: str = "") -> PDWDataWindow:


        """Decompile a PDW file to extract all available information.

        Args:
            data: Raw PDW file data
            filename: Optional filename for logging

        Returns:
            PDWDataWindow object with all extracted information
        """
        logger.info(f"Decompiling PDW file: {filename}")

        # Initialize result
        dw = PDWDataWindow(version=cls._extract_version(data))

        # Extract basic metadata
        cls._extract_metadata(data, dw)

        # Extract SQL
        dw.sql = cls._extract_sql(data)
        if dw.sql:
            dw.tables = cls._extract_tables_from_sql(dw.sql)

        # Extract column definitions with properties
        dw.columns = cls._extract_columns_with_properties(data)

        # Extract layout information
        cls._extract_layout_info(data, dw)

        # Extract display properties
        cls._extract_display_properties(data, dw)

        # Extract advanced structures
        advanced = cls.extract_advanced_structures(data)
        if advanced:
            dw.properties.update(advanced)

        return dw

    @classmethod
    def _extract_version(cls, data: bytes) -> str:


        """Extract PDW version from header."""
        if len(data) < 8:
            return "Unknown"

        header = data[:8]
        if header.startswith(b"PDW"):
            return header.decode("ascii", errors="ignore").strip("\x00")
        return "Unknown"

    @classmethod
    def _extract_metadata(cls, data: bytes, dw: PDWDataWindow) -> None:


        """Extract basic metadata from PDW header."""
        if len(data) < 0x20:
            return

        # Extract values from known offsets
        try:
            # Common header values
            val1 = struct.unpack("<I", data[0x08:0x0C])[0]
            val2 = struct.unpack("<I", data[0x0C:0x10])[0]

            dw.properties["header_field_0x08"] = val1
            dw.properties["header_field_0x0C"] = val2

            # Look for DataWindow name
            if len(data) > 0x10:
                name_candidate = data[0x10:0x20].rstrip(b"\x00")
                if name_candidate and b"\x00" not in name_candidate[:-1]:
                    try:
                        dw.name = name_candidate.decode("ascii", errors="ignore")
                    except Exception as e:
                        logger.debug("Exception caught: %s", e)
        except struct.error:
            pass

    @classmethod
    def _extract_sql(cls, data: bytes) -> str | None:


        """Extract SQL query from PDW data."""
        # Try multiple methods

        # Method 1: Look for UTF-16 SELECT
        select_utf16 = b"S\x00E\x00L\x00E\x00C\x00T\x00"
        idx = data.find(select_utf16)
        if idx >= 0:
            # Extract until we find a terminator
            end_idx = len(data)
            for terminator in [b"\x00\x00\x00\x00", b"\x00)\x00\x00", b"\x00;\x00\x00"]:
                term_idx = data.find(terminator, idx)
                if term_idx > idx:
                    end_idx = min(end_idx, term_idx)

            sql_data = data[idx:end_idx]
            try:
                sql = sql_data.decode("utf-16-le", errors="ignore")
                sql = cls._clean_sql(sql)
                if sql:
                    return sql
            except Exception as e:
                logger.debug("Exception caught: %s", e)

        # Method 2: ASCII SELECT
        idx = data.find(b"SELECT ")
        if idx >= 0:
            end_idx = data.find(b"\x00", idx)
            if end_idx > idx:
                sql = data[idx:end_idx].decode("ascii", errors="ignore")
                sql = cls._clean_sql(sql)
                if sql:
                    return sql

        return None

    @classmethod
    def _clean_sql(cls, sql: str) -> str:


        """Clean up extracted SQL."""
        # Remove control characters and normalize whitespace
        sql = re.sub(r"[\x00-\x1f\x7f-\x9f]", " ", sql)
        sql = re.sub(r"\s+", " ", sql)
        sql = sql.strip()

        # Remove trailing garbage
        sql = re.sub(r'[^\w\s\(\),\.=<>!\'";\-\*\+/]+$', "", sql)

        return sql

    @classmethod
    def _extract_tables_from_sql(cls, sql: str) -> list[str]:


        """Extract table names from SQL."""
        tables = set()

        # Look for FROM clause
        from_match = re.search(r"FROM\s+([^WHERE|GROUP|ORDER]+)", sql, re.IGNORECASE)
        if from_match:
            from_clause = from_match.group(1)
            # Extract table names and aliases
            parts = from_clause.split(",")
            for part in parts:
                # Handle "table alias" or just "table"
                match = re.match(r"^\s*(\w+)(?:\s+\w+)?\s*$", part)
                if match:
                    tables.add(match.group(1))

        return sorted(tables)

    @classmethod
    def _extract_columns_with_properties(cls, data: bytes) -> list[PDWColumnProperties]:


        """Extract column definitions with all their properties."""
        columns = []

        # Method 1: Extract from string table
        if len(data) > cls.STRING_TABLE_START:
            strings = cls._extract_utf16_strings(data, cls.STRING_TABLE_START, cls.STRING_TABLE_START + 0x500)

            # Look for column names (often have _id, _name suffixes or are in pairs)
            seen_names = set()
            for i, s in enumerate(strings):
                if cls._looks_like_column_name(s) and s not in seen_names:
                    seen_names.add(s)
                    col = PDWColumnProperties(name=s, position=len(columns))

                    # Try to find display name (often follows the db name)
                    if i + 1 < len(strings):
                        next_s = strings[i + 1]
                        if len(next_s) < 100 and not cls._looks_like_column_name(next_s):
                            col.display_name = next_s

                    # Extract db_name from column name pattern
                    if "." in s:
                        parts = s.split(".")
                        if len(parts) == 2:
                            col.db_name = s
                            col.name = parts[1]

                    columns.append(col)

        # Method 2: Extract from SQL if present
        if not columns:
            columns = cls._extract_columns_from_sql(data)

        # Method 3: Extract layout info for columns
        cls._extract_column_layouts(data, columns)

        # Method 4: Extract column properties (type, format, etc.)
        cls._extract_column_properties(data, columns)

        return columns

    @classmethod
    def _looks_like_column_name(cls, s: str) -> bool:


        """Check if string looks like a column name."""
        if not s or len(s) > 50:
            return False

        # Common patterns
        patterns = ["_id", "_name", "_code", "_date", "_time", "_no", "_type", "_flag"]
        s_lower = s.lower()

        # Check for patterns
        if any(pattern in s_lower for pattern in patterns):
            return True

        # Check for underscore-separated words
        if "_" in s and s.replace("_", "").replace(" ", "").isalnum():
            return True

        # Check for common column names
        common_names = ["id", "name", "description", "code", "status", "type", "date", "time"]
        if s_lower in common_names:
            return True

        return False

    @classmethod
    def _extract_columns_from_sql(cls, data: bytes) -> list[PDWColumnProperties]:


        """Extract columns from SQL query if no columns found in string table."""
        columns = []
        sql = cls._extract_sql(data)

        if sql:
            # Extract column names from SELECT clause
            select_match = re.search(r"SELECT\s+(.*?)\s+FROM", sql, re.IGNORECASE | re.DOTALL)
            if select_match:
                select_clause = select_match.group(1)
                # Split by comma but handle nested functions
                parts = []
                current = ""
                paren_depth = 0
                for char in select_clause:
                    if char == "(":
                        paren_depth += 1
                    elif char == ")":
                        paren_depth -= 1
                    elif char == "," and paren_depth == 0:
                        parts.append(current.strip())
                        current = ""
                        continue
                    current += char
                if current:
                    parts.append(current.strip())

                for part in parts:
                    # Extract column name and alias
                    # Handle: table.column AS alias, column alias, column
                    alias_match = re.search(r"(?:as\s+)?(\w+)\s*$", part, re.IGNORECASE)
                    if alias_match:
                        col_name = alias_match.group(1)
                        col = PDWColumnProperties(name=col_name, position=len(columns))

                        # Extract table.column pattern
                        table_col_match = re.search(r"(\w+)\.(\w+)", part)
                        if table_col_match:
                            col.db_name = f"{table_col_match.group(1)}.{table_col_match.group(2)}"

                        columns.append(col)

        return columns

    @classmethod
    def _extract_column_layouts(cls, data: bytes, columns: list[PDWColumnProperties]) -> None:


        """Extract layout information for columns."""
        # Look for coordinate patterns
        # Based on analysis, coordinates often appear in groups of 4 (x,y,w,h)

        # Try multiple known offsets where column layouts might be
        layout_offsets = [0x554, 0x400, 0x600, 0x800]

        for base_offset in layout_offsets:
            if len(data) > base_offset + len(columns) * 16:
                valid_layouts = 0
                for i, col in enumerate(columns):
                    offset = base_offset + i * 16
                    if offset + 16 <= len(data):
                        try:
                            x, y, w, h = struct.unpack("<IIII", data[offset:offset+16])
                            if all(0 < v < 10000 for v in [x, y, w, h]):  # Reasonable bounds
                                col.bounds = Rectangle(x, y, w, h)
                                valid_layouts += 1
                        except Exception as e:
                            logger.debug("Exception caught: %s", e)

                # If we found layouts for most columns, we likely found the right offset
                if valid_layouts >= len(columns) * 0.7:
                    break

        # Alternative method: scan for coordinate patterns
        if not any(col.bounds for col in columns):
            cls._scan_for_coordinate_patterns(data, columns)

    @classmethod
    def _scan_for_coordinate_patterns(cls, data: bytes, columns: list[PDWColumnProperties]) -> None:


        """Scan data for coordinate patterns that might belong to columns."""
        # Look for sequences of 4 integers that could be x,y,width,height
        for i in range(0, min(len(data) - 16, 0x2000), 4):
            try:
                vals = struct.unpack("<IIII", data[i:i+16])
                # Check if values are in reasonable range for coordinates
                if all(10 < v < 10000 for v in vals):
                    # Check if this could be a column layout
                    x, y, w, h = vals
                    # Columns usually have consistent Y positions or incremental Y
                    if 50 < h < 200:  # Reasonable column height
                        # Try to match to a column by position
                        for col in columns:
                            if not col.bounds:
                                col.bounds = Rectangle(x, y, w, h)
                                break
            except Exception as e:
                logger.debug("Exception caught: %s", e)

    @classmethod
    def _extract_column_properties(cls, data: bytes, columns: list[PDWColumnProperties]) -> None:


        """Extract additional column properties like data type, format, alignment."""
        # Look for data type indicators
        type_patterns = {
            b"char": "string",
            b"varchar": "string",
            b"int": "integer",
            b"decimal": "decimal",
            b"date": "date",
            b"datetime": "datetime",
            b"numeric": "numeric",
        }

        # Scan for type information near column names
        for col in columns:
            # Search for column name in data
            name_bytes = col.name.encode("utf-16-le")
            idx = data.find(name_bytes)
            if idx >= 0:
                # Look nearby for type information
                search_range = data[max(0, idx-100):min(len(data), idx+200)]
                for pattern, dtype in type_patterns.items():
                    if pattern in search_range:
                        col.data_type = dtype
                        break

                # Look for format strings
                cls._extract_column_format(data, idx, col)

                # Look for alignment values
                cls._extract_column_alignment(data, idx, col)

    @classmethod
    def _extract_layout_info(cls, data: bytes, dw: PDWDataWindow) -> None:


        """Extract general layout information."""
        # Look for window bounds (usually larger values)
        for offset in range(0, min(len(data) - 16, 0x200), 4):
            try:
                vals = struct.unpack("<IIII", data[offset:offset+16])
                # Window bounds are typically larger
                if all(100 < v < 50000 for v in vals):
                    dw.window_bounds = Rectangle(*vals)
                    dw.properties["window_bounds_offset"] = f"0x{offset:04X}"
                    break
            except Exception as e:
                logger.debug("Exception caught: %s", e)

    @classmethod
    def _extract_display_properties(cls, data: bytes, dw: PDWDataWindow) -> None:


        """Extract display properties like colors and fonts."""
        # Extract colors
        colors_found = []
        for offset in range(0, min(len(data) - 4, 0x1000), 4):
            val = struct.unpack("<I", data[offset:offset+4])[0]
            # Check for color pattern
            if (val & 0xFF000000) in [0, 0xFF000000]:
                color = Color.from_int(val)
                # Filter obvious non-colors
                if not (color.red == color.green == color.blue):
                    colors_found.append((offset, color))

        if colors_found:
            dw.properties["colors_found"] = len(colors_found)
            # First color might be background
            if colors_found:
                dw.background_color = colors_found[0][1]

            # Try to assign colors to columns
            if dw.columns and len(colors_found) > 1:
                for i, col in enumerate(dw.columns):
                    if i + 1 < len(colors_found):
                        col.text_color = colors_found[i + 1][1]

        # Extract font information
        cls._extract_font_info(data, dw)

        # Extract column-specific display properties
        cls._extract_column_display_properties(data, dw)

    @classmethod
    def _extract_font_info(cls, data: bytes, dw: PDWDataWindow) -> None:


        """Extract font information."""
        # Look for font names
        font_names = ["Arial", "Tahoma", "Courier New", "Times New Roman"]
        for name in font_names:
            if name.encode("ascii") in data or name.encode("utf-16-le") in data:
                dw.properties["default_font"] = name
                break

        # Look for font sizes
        font_sizes = []
        for offset in range(0, min(len(data) - 4, 0x1000), 4):
            val = struct.unpack("<I", data[offset:offset+4])[0]
            if 6 <= val <= 72:  # Common font size range
                font_sizes.append(val)

        if font_sizes:
            # Most common size is probably default
            from collections import Counter
            size_counts = Counter(font_sizes)
            most_common = size_counts.most_common(1)[0][0]
            dw.properties["default_font_size"] = most_common

    @classmethod
    def _extract_utf16_strings(cls, data: bytes, start: int, end: int) -> list[str]:


        """Extract UTF-16 LE strings from a data region."""
        strings = []
        i = start

        while i < min(end, len(data) - 2):
            # Look for null-terminated UTF-16 strings
            string_start = i
            while i < min(end, len(data) - 1):
                if data[i:i+2] == b"\x00\x00":
                    break
                i += 2

            if i > string_start:
                string_data = data[string_start:i]
                try:
                    decoded = string_data.decode("utf-16-le", errors="ignore")
                    if decoded and len(decoded.strip()) > 0:
                        strings.append(decoded.strip())
                except Exception as e:
                    logger.debug("Exception caught: %s", e)

            i += 2

        return strings

    @classmethod
    def extract_advanced_structures(cls, data: bytes) -> dict[str, Any]:


        """Extract advanced PDW structures like groups, computed fields, etc."""
        advanced = {}

        # Look for group definitions
        group_markers = [b"group(", b"g\x00r\x00o\x00u\x00p\x00("]
        for marker in group_markers:
            idx = data.find(marker)
            if idx >= 0:
                advanced["has_groups"] = True
                break

        # Look for computed field definitions
        compute_markers = [b"compute(", b"c\x00o\x00m\x00p\x00u\x00t\x00e\x00("]
        for marker in compute_markers:
            idx = data.find(marker)
            if idx >= 0:
                advanced["has_computed_fields"] = True
                break

        # Look for graph/chart definitions
        graph_markers = [b"graph(", b"g\x00r\x00a\x00p\x00h\x00("]
        for marker in graph_markers:
            idx = data.find(marker)
            if idx >= 0:
                advanced["has_graphs"] = True
                break

        # Look for crosstab definitions
        crosstab_markers = [b"crosstab(", b"c\x00r\x00o\x00s\x00s\x00t\x00a\x00b\x00("]
        for marker in crosstab_markers:
            idx = data.find(marker)
            if idx >= 0:
                advanced["has_crosstab"] = True
                break

        # Look for sort definitions
        sort_markers = [b"sort=", b"s\x00o\x00r\x00t\x00="]
        for marker in sort_markers:
            idx = data.find(marker)
            if idx >= 0:
                advanced["has_sort"] = True
                # Try to extract sort criteria
                end_idx = data.find(b"\x00", idx + len(marker))
                if end_idx > idx:
                    try:
                        sort_def = data[idx + len(marker):end_idx].decode("ascii", errors="ignore")
                        advanced["sort_definition"] = sort_def
                    except Exception as e:
                        logger.debug("Exception caught: %s", e)
                break

        # Look for filter definitions
        filter_markers = [b"filter=", b"f\x00i\x00l\x00t\x00e\x00r\x00="]
        for marker in filter_markers:
            idx = data.find(marker)
            if idx >= 0:
                advanced["has_filter"] = True
                break

        return advanced

    @classmethod
    def _extract_column_format(cls, data: bytes, near_idx: int, col: PDWColumnProperties) -> None:


        """Extract format string for a column."""
        # Common display formats
        format_patterns = [
            (b"[general]", "[general]"),
            (b"#,##0", "#,##0"),
            (b"$#,##0.00", "$#,##0.00"),
            (b"dd/mm/yyyy", "dd/mm/yyyy"),
            (b"mm/dd/yyyy", "mm/dd/yyyy"),
            (b"yyyy-mm-dd", "yyyy-mm-dd"),
            (b"hh:mm:ss", "hh:mm:ss"),
            (b"###-##-####", "###-##-####"),
            (b"(###) ###-####", "(###) ###-####"),
        ]

        # Search near the column name for format strings
        search_start = max(0, near_idx - 200)
        search_end = min(len(data), near_idx + 200)
        search_range = data[search_start:search_end]

        for pattern, format_str in format_patterns:
            if pattern in search_range:
                col.format = format_str
                break
            # Also check UTF-16 version
            utf16_pattern = pattern.decode("ascii").encode("utf-16-le")
            if utf16_pattern in search_range:
                col.format = format_str
                break

    @classmethod
    def _extract_column_alignment(cls, data: bytes, near_idx: int, col: PDWColumnProperties) -> None:


        """Extract alignment for a column."""
        # Look for alignment values (0=left, 1=center, 2=right)
        search_start = max(0, near_idx - 50)
        search_end = min(len(data), near_idx + 50)

        if search_end - search_start >= 4:
            for i in range(search_start, search_end - 4, 4):
                try:
                    val = struct.unpack("<I", data[i:i+4])[0]
                    if val in [0, 1, 2]:
                        # Verify it's likely an alignment value by checking context
                        if i >= 4 and i + 8 <= len(data):
                            prev_val = struct.unpack("<I", data[i-4:i])[0]
                            next_val = struct.unpack("<I", data[i+4:i+8])[0]
                            # Alignment values are often surrounded by other small values
                            if prev_val < 1000 and next_val < 1000:
                                col.alignment = Alignment(val)
                                break
                except Exception as e:
                    logger.debug("Exception caught: %s", e)

    @classmethod
    def _extract_column_display_properties(cls, data: bytes, dw: PDWDataWindow) -> None:


        """Extract display properties specific to columns."""
        # Look for font properties near column definitions
        for col in dw.columns:
            # If we have a column name, search for display properties near it
            if col.name:
                name_bytes = col.name.encode("utf-16-le")
                idx = data.find(name_bytes)
                if idx >= 0:
                    # Look for font information nearby
                    cls._extract_column_font(data, idx, col)

                    # Look for visibility flags
                    cls._extract_column_visibility(data, idx, col)

                    # Look for edit properties
                    cls._extract_column_edit_properties(data, idx, col)

    @classmethod
    def _extract_column_font(cls, data: bytes, near_idx: int, col: PDWColumnProperties) -> None:


        """Extract font information for a specific column."""
        # Search for font name near column
        font_names = ["Arial", "Tahoma", "Courier New", "Times New Roman", "MS Sans Serif"]
        search_start = max(0, near_idx - 100)
        search_end = min(len(data), near_idx + 100)
        search_range = data[search_start:search_end]

        for font_name in font_names:
            font_bytes = font_name.encode("utf-16-le")
            if font_bytes in search_range:
                if not col.font:
                    col.font = Font()
                col.font.name = font_name
                break

        # Look for font size (usually 8-72)
        for i in range(search_start, search_end - 4, 4):
            try:
                val = struct.unpack("<I", data[i:i+4])[0]
                if 8 <= val <= 72:
                    if not col.font:
                        col.font = Font()
                    col.font.size = val
                    break
            except Exception as e:
                logger.debug("Exception caught: %s", e)

    @classmethod
    def _extract_column_visibility(cls, data: bytes, near_idx: int, col: PDWColumnProperties) -> None:


        """Extract visibility settings for a column."""
        # Look for visible flag pattern
        search_start = max(0, near_idx - 50)
        search_end = min(len(data), near_idx + 50)

        # Common patterns for visibility
        if b'visible="0"' in data[search_start:search_end] or b'v\x00i\x00s\x00i\x00b\x00l\x00e\x00=\x00"\x000\x00"' in data[search_start:search_end]:
            col.visible = False

    @classmethod
    def _extract_column_edit_properties(cls, data: bytes, near_idx: int, col: PDWColumnProperties) -> None:


        """Extract edit properties for a column."""
        search_start = max(0, near_idx - 100)
        search_end = min(len(data), near_idx + 100)
        search_range = data[search_start:search_end]

        # Check for displayonly flag
        if b"displayonly" in search_range or b"d\x00i\x00s\x00p\x00l\x00a\x00y\x00o\x00n\x00l\x00y" in search_range:
            col.editable = False

        # Check for protect flag
        if b'protect="1"' in search_range or b'p\x00r\x00o\x00t\x00e\x00c\x00t\x00=\x00"\x001\x00"' in search_range:
            col.editable = False


def extract_from_file(file_path: str) -> PDWDataWindow:








    """Extract comprehensive information from a PDW file.

    Args:
        file_path: Path to the PDW file

    Returns:
        PDWDataWindow object with all extracted information
    """
    with open(file_path, "rb") as f:
        data = f.read()

    return PDWComprehensiveExtractor.decompile_pdw(data, file_path)


def main() -> None:







    """Main entry point for command-line usage."""
    import sys

    if len(sys.argv) < 2:
        print("Usage: pdw_comprehensive_extractor.py <pdw_file>")
        sys.exit(1)

    file_path = sys.argv[1]

    try:
        dw = extract_from_file(file_path)

        # Print summary
        print(f"PDW Extraction Results for: {file_path}")
        print("=" * 80)
        print(f"Version: {dw.version}")
        if dw.name:
            print(f"Name: {dw.name}")

        if dw.sql:
            print(f"\nSQL Query ({len(dw.sql)} chars):")
            print("-" * 40)
            print(dw.sql[:200] + "..." if len(dw.sql) > 200 else dw.sql)

        if dw.columns:
            print(f"\nColumns ({len(dw.columns)}):")
            print("-" * 40)
            for col in dw.columns:
                print(f"  {col}")

        if dw.window_bounds:
            print(f"\nWindow Bounds: {dw.window_bounds}")

        if dw.properties:
            print(f"\nProperties ({len(dw.properties)}):")
            print("-" * 40)
            for key, value in list(dw.properties.items())[:
                10]:
                print(f"  {key}: {value}")
            if len(dw.properties) > 10:
                print(f"  ... and {len(dw.properties) - 10} more")

        # Save the source approximation
        output_file = file_path.replace(".dwo", "_reconstructed.srd")
        output_file = output_file.replace(".pdw", "_reconstructed.srd")

        with open(output_file, "w") as f:
            f.write(dw.get_source_approximation())
        print(f"\nSource approximation saved to: {output_file}")

    except Exception as e:
        print(f"Error processing file: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
