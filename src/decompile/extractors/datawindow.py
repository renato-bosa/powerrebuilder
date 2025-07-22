"""Base DataWindow extraction logic.

This module provides the core functionality for extracting and parsing
PowerBuilder DataWindow objects from decompiled source.
"""

import logging
import re
from dataclasses import dataclass, field
from typing import Any, ClassVar

from src.decompile.datawindow_utils import DataWindowDetector

logger = logging.getLogger(__name__)


@dataclass
class ExtractedData:
    """Container for extracted data from decompilation."""

    type: str
    name: str
    success: bool
    data: Any = None
    metadata: dict[str, Any] = field(default_factory=dict)
    error: str | None = None


@dataclass
class DataWindowColumn:
    """Represents a DataWindow column definition."""

    id: int
    name: str
    dbname: str
    type: str
    updatewhereclause: bool = True
    values: dict[str, str] = field(default_factory=dict)
    band: str = "detail"
    alignment: str = "0"
    tabsequence: int = 32766
    format: str = "[general]"
    edit_style: str = "edit"
    edit_limit: int = 0
    edit_case: str = "any"
    visible: bool = True
    x: int = 0
    y: int = 0
    width: int = 0
    height: int = 0
    attributes: dict[str, Any] = field(default_factory=dict)


@dataclass
class DataWindowControl:
    """Represents a DataWindow control (text, compute, etc.)."""

    type: str  # text, compute, button, etc.
    band: str
    name: str | None = None
    text: str | None = None
    expression: str | None = None
    alignment: str = "0"
    x: int = 0
    y: int = 0
    width: int = 0
    height: int = 0
    visible: bool = True
    attributes: dict[str, Any] = field(default_factory=dict)


@dataclass
class DataWindowBand:
    """Represents a DataWindow band (header, detail, footer, etc.)."""

    type: str  # header, detail, footer, summary, etc.
    height: int = 0
    color: str = "536870912"
    attributes: dict[str, Any] = field(default_factory=dict)


@dataclass
class DataWindowDefinition:
    """Complete DataWindow definition."""

    release: str = ""
    processing_type: str = "1"  # 0=Form, 1=Tabular, 2=Label, 3=Graph, etc.
    units: int = 0
    bands: list[DataWindowBand] = field(default_factory=list)
    columns: list[DataWindowColumn] = field(default_factory=list)
    controls: list[DataWindowControl] = field(default_factory=list)
    table_name: str | None = None
    retrieve_sql: str | None = None
    arguments: list[tuple[str, str]] = field(default_factory=list)
    sort_order: str | None = None
    properties: dict[str, Any] = field(default_factory=dict)

    @property
    def presentation_style(self) -> str:
        """Get the presentation style based on processing type."""
        styles = {
            "0": "freeform",
            "1": "tabular",
            "2": "label",
            "3": "group",
            "4": "crosstab",
            "5": "composite",
            "6": "graph",
            "7": "ole",
            "8": "richtext",
            "9": "treeview",
            "10": "treelist",
        }
        return styles.get(self.processing_type, "tabular")


class DataWindowExtractor:
    """Extracts DataWindow definitions from PowerBuilder source."""

    # Pattern to match DataWindow syntax sections
    SECTION_PATTERNS: ClassVar[dict[str, re.Pattern[str]]] = {
        "release": re.compile(r"release\s+(\d+(?:\.\d+)?);"),
        "datawindow": re.compile(r"datawindow\s*\(([^)]+)\)"),
        "band": re.compile(
            r"(header|detail|footer|summary|trailer|tree\.level\.\d+)\s*\(([^)]+)\)"
        ),
        "table": re.compile(r"table\s*\(([^)]+(?:\([^)]+\)[^)]*)*)\)", re.DOTALL),
        "column": re.compile(r"column\s*\(([^)]+)\)"),
        "text": re.compile(r"text\s*\(([^)]+)\)"),
        "compute": re.compile(r"compute\s*\(([^)]+)\)"),
        "retrieve": re.compile(r'retrieve\s*=\s*"([^"]+(?:~"[^"]+)*)"', re.DOTALL),
        "arguments": re.compile(r"arguments\s*=\s*\(([^)]+)\)"),
        "sort": re.compile(r'sort\s*=\s*"([^"]+)"'),
    }

    def __init__(self):
        """Initialize the extractor."""
        self.detector = DataWindowDetector()

    def extract(self, source: str, filename: str = "") -> ExtractedData:
        """Extract DataWindow definition from source.

        Args:
            source: PowerBuilder DataWindow source code
            filename: Optional filename for context

        Returns:
            ExtractedData containing the parsed DataWindow definition
        """
        try:
            # Check if this is a DataWindow file
            if not self._is_datawindow_source(source):
                return ExtractedData(
                    type="unknown",
                    name=filename,
                    success=False,
                    error="Not a DataWindow source file",
                )

            # Parse the DataWindow definition
            definition = self._parse_datawindow(source)

            # Extract additional metadata
            metadata = self._extract_metadata(definition, source)

            return ExtractedData(
                type="datawindow",
                name=filename or "unknown",
                success=True,
                data=definition,
                metadata=metadata,
            )

        except Exception as e:
            logger.error("Failed to extract DataWindow from %s: %s", filename, e)
            return ExtractedData(
                type="datawindow", name=filename, success=False, error=str(e)
            )

    def _is_datawindow_source(self, source: str) -> bool:
        """Check if source contains DataWindow definition."""
        # Look for key DataWindow indicators
        indicators = ["release", "datawindow(", "table(", "column("]
        source_lower = source.lower()
        return any(indicator in source_lower for indicator in indicators)

    def _parse_datawindow(self, source: str) -> DataWindowDefinition:
        """Parse DataWindow source into definition object."""
        definition = DataWindowDefinition()

        # Extract release version
        if match := self.SECTION_PATTERNS["release"].search(source):
            definition.release = match.group(1)

        # Extract DataWindow properties
        if match := self.SECTION_PATTERNS["datawindow"].search(source):
            props = self._parse_properties(match.group(1))
            definition.processing_type = props.get("processing", "1")
            definition.units = int(props.get("units", 0))
            definition.properties = props

        # Extract bands
        for match in self.SECTION_PATTERNS["band"].finditer(source):
            band_type = match.group(1)
            band_props = self._parse_properties(match.group(2))
            band = DataWindowBand(
                type=band_type,
                height=int(band_props.get("height", 0)),
                color=band_props.get("color", "536870912"),
                attributes=band_props,
            )
            definition.bands.append(band)

        # Extract table and columns
        if match := self.SECTION_PATTERNS["table"].search(source):
            table_content = match.group(1)
            self._parse_table_definition(table_content, definition)

        # Extract retrieve SQL
        if match := self.SECTION_PATTERNS["retrieve"].search(source):
            sql = match.group(1)
            # Unescape quotes
            definition.retrieve_sql = sql.replace('~"', '"')

        # Extract arguments
        if match := self.SECTION_PATTERNS["arguments"].search(source):
            args_str = match.group(1)
            definition.arguments = self._parse_arguments(args_str)

        # Extract sort order
        if match := self.SECTION_PATTERNS["sort"].search(source):
            definition.sort_order = match.group(1)

        # Extract controls (text, compute, etc.)
        self._extract_controls(source, definition)

        return definition

    def _parse_properties(self, props_str: str) -> dict[str, str]:
        """Parse property string into dictionary."""
        properties = {}

        # Handle nested parentheses and quotes
        prop_pattern = re.compile(r'(\w+)\s*=\s*(?:"([^"]+)"|(\S+))')

        for match in prop_pattern.finditer(props_str):
            key = match.group(1)
            # Use quoted value if present, otherwise unquoted
            value = match.group(2) if match.group(2) is not None else match.group(3)
            properties[key] = value

        return properties

    def _parse_table_definition(
        self, table_content: str, definition: DataWindowDefinition
    ):
        """Parse table definition including columns."""
        # Extract columns
        column_pattern = re.compile(r"column\s*=\s*\(([^)]+)\)")

        for i, match in enumerate(column_pattern.finditer(table_content)):
            col_props = self._parse_properties(match.group(1))

            column = DataWindowColumn(
                id=i + 1,
                name=col_props.get("name", f"column_{i + 1}"),
                dbname=col_props.get("dbname", ""),
                type=col_props.get("type", "char(1)"),
                updatewhereclause=col_props.get("updatewhereclause", "yes") == "yes",
            )

            # Parse values for dropdown columns
            if "values" in col_props:
                column.values = self._parse_column_values(col_props["values"])

            # Store other properties
            column.attributes = col_props

            definition.columns.append(column)

        # Extract table name from dbname if available
        if definition.columns and "." in definition.columns[0].dbname:
            definition.table_name = definition.columns[0].dbname.split(".")[0]

    def _parse_column_values(self, values_str: str) -> dict[str, str]:
        """Parse column values for dropdown lists."""
        values = {}
        # Format: "Active\tA/Inactive\tI/Hold\tH"
        pairs = values_str.split("/")
        for pair in pairs:
            parts = pair.split("\t")
            if len(parts) >= 2:
                values[parts[1]] = parts[0]
        return values

    def _parse_arguments(self, args_str: str) -> list[tuple[str, str]]:
        """Parse DataWindow arguments."""
        arguments = []
        # Format: ("as_status", string),("ad_min_balance", decimal)
        arg_pattern = re.compile(r'\("([^"]+)",\s*(\w+)\)')

        for match in arg_pattern.finditer(args_str):
            name = match.group(1)
            dtype = match.group(2)
            arguments.append((name, dtype))

        return arguments

    def _extract_controls(self, source: str, definition: DataWindowDefinition):
        """Extract visual controls from DataWindow."""
        # Extract text controls
        for match in self.SECTION_PATTERNS["text"].finditer(source):
            props = self._parse_properties(match.group(1))
            control = DataWindowControl(
                type="text",
                band=props.get("band", "detail"),
                name=props.get("name"),
                text=props.get("text", ""),
                alignment=props.get("alignment", "0"),
                x=int(props.get("x", 0)),
                y=int(props.get("y", 0)),
                width=int(props.get("width", 0)),
                height=int(props.get("height", 0)),
                visible=props.get("visible", "1") == "1",
                attributes=props,
            )
            definition.controls.append(control)

        # Extract compute controls
        for match in self.SECTION_PATTERNS["compute"].finditer(source):
            props = self._parse_properties(match.group(1))
            control = DataWindowControl(
                type="compute",
                band=props.get("band", "detail"),
                name=props.get("name"),
                expression=props.get("expression", ""),
                alignment=props.get("alignment", "0"),
                x=int(props.get("x", 0)),
                y=int(props.get("y", 0)),
                width=int(props.get("width", 0)),
                height=int(props.get("height", 0)),
                visible=props.get("visible", "1") == "1",
                attributes=props,
            )
            definition.controls.append(control)

        # Extract column controls
        column_control_pattern = re.compile(
            r"column\s*\(band=(\w+)[^)]+id=(\d+)[^)]+\)"
        )
        for match in column_control_pattern.finditer(source):
            band = match.group(1)
            col_id = int(match.group(2))

            # Find the column definition
            column = next((c for c in definition.columns if c.id == col_id), None)
            if column:
                # Parse column control properties
                col_match = re.search(
                    rf"column\s*\(band={band}[^)]+id={col_id}([^)]+)\)", source
                )
                if col_match:
                    props = self._parse_properties(col_match.group(1))
                    column.band = band
                    column.x = int(props.get("x", 0))
                    column.y = int(props.get("y", 0))
                    column.width = int(props.get("width", 0))
                    column.height = int(props.get("height", 0))
                    column.alignment = props.get("alignment", "0")
                    column.tabsequence = int(props.get("tabsequence", 32766))
                    column.format = props.get("format", "[general]")
                    column.visible = props.get("visible", "1") == "1"

                    # Determine edit style
                    if "ddlb" in props:
                        column.edit_style = "ddlb"
                    elif "checkbox" in props:
                        column.edit_style = "checkbox"
                    elif "radiobutton" in props:
                        column.edit_style = "radiobutton"
                    elif "editmask" in props:
                        column.edit_style = "editmask"

                    # Store all properties
                    column.attributes.update(props)

    def _extract_metadata(
        self, definition: DataWindowDefinition, source: str
    ) -> dict[str, Any]:
        """Extract additional metadata from DataWindow."""
        metadata = {
            "presentation_style": definition.presentation_style,
            "column_count": len(definition.columns),
            "band_count": len(definition.bands),
            "control_count": len(definition.controls),
            "has_sql": definition.retrieve_sql is not None,
            "has_arguments": len(definition.arguments) > 0,
            "has_sort": definition.sort_order is not None,
        }

        # Analyze SQL complexity if present
        if definition.retrieve_sql:
            sql_lower = definition.retrieve_sql.lower()
            metadata["sql_features"] = {
                "has_joins": " join " in sql_lower,
                "has_where": " where " in sql_lower,
                "has_group_by": " group by " in sql_lower,
                "has_order_by": " order by " in sql_lower,
                "has_union": " union " in sql_lower,
            }

        # Analyze column types
        type_counts = {}
        for column in definition.columns:
            base_type = column.type.split("(")[0]
            type_counts[base_type] = type_counts.get(base_type, 0) + 1
        metadata["column_types"] = type_counts

        # Analyze controls by band
        band_controls = {}
        for control in definition.controls:
            band = control.band
            if band not in band_controls:
                band_controls[band] = {"text": 0, "compute": 0, "other": 0}

            if control.type == "text":
                band_controls[band]["text"] += 1
            elif control.type == "compute":
                band_controls[band]["compute"] += 1
            else:
                band_controls[band]["other"] += 1
        metadata["controls_by_band"] = band_controls

        return metadata


# Module-level extraction manager instance
extraction_manager = DataWindowExtractor()
