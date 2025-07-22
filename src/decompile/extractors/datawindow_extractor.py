"""Enhanced DataWindow extractor with advanced features.

This module provides enhanced DataWindow extraction capabilities including
support for complex DataWindow types, nested objects, and advanced properties.
"""

import logging
import re
from dataclasses import dataclass, field
from typing import Any, ClassVar

from src.decompile.extractors.datawindow import (
    DataWindowDefinition,
    DataWindowExtractor,
    ExtractedData,
)

logger = logging.getLogger(__name__)


@dataclass
class DataWindowGroup:
    """Represents a DataWindow group definition."""

    level: int
    by_columns: list[str]
    header_height: int = 0
    trailer_height: int = 0
    newpage: bool = False
    reset_page_number: bool = False
    suppress_duplicates: bool = False
    attributes: dict[str, Any] = field(default_factory=dict)


@dataclass
class DataWindowGraph:
    """Represents a DataWindow graph definition."""

    type: str  # pie, bar, line, scatter, etc.
    title: str = ""
    category_column: str | None = None
    value_columns: list[str] = field(default_factory=list)
    series_column: str | None = None
    x: int = 0
    y: int = 0
    width: int = 0
    height: int = 0
    attributes: dict[str, Any] = field(default_factory=dict)


@dataclass
class DataWindowCrosstab:
    """Represents a DataWindow crosstab definition."""

    row_columns: list[str] = field(default_factory=list)
    column_columns: list[str] = field(default_factory=list)
    value_columns: list[str] = field(default_factory=list)
    compute_expressions: dict[str, str] = field(default_factory=dict)
    attributes: dict[str, Any] = field(default_factory=dict)


@dataclass
class DataWindowTreeNode:
    """Represents a tree node in a TreeView DataWindow."""

    level: int
    label_column: str
    data_column: str | None = None
    state_icon_column: str | None = None
    image_column: str | None = None
    attributes: dict[str, Any] = field(default_factory=dict)


@dataclass
class EnhancedDataWindowDefinition(DataWindowDefinition):
    """Extended DataWindow definition with advanced features."""

    # Group definitions
    groups: list[DataWindowGroup] = field(default_factory=list)

    # Graph definitions
    graphs: list[DataWindowGraph] = field(default_factory=list)

    # Crosstab definition
    crosstab: DataWindowCrosstab | None = None

    # TreeView nodes
    tree_nodes: list[DataWindowTreeNode] = field(default_factory=list)

    # Composite DataWindow references
    composite_reports: list[str] = field(default_factory=list)

    # Update properties
    update_table: str | None = None
    update_key_columns: list[str] = field(default_factory=list)
    update_where_clause: str | None = None

    # Export/Import templates
    export_template: str | None = None
    import_template: str | None = None

    # Additional metadata
    data_source_type: str = "sql"  # sql, external, stored_procedure
    stored_procedure_name: str | None = None
    external_source: str | None = None

    # Print specifications
    print_specs: dict[str, Any] = field(default_factory=dict)

    # HTML generation settings
    html_settings: dict[str, Any] = field(default_factory=dict)


class EnhancedDataWindowExtractor(DataWindowExtractor):
    """Enhanced DataWindow extractor with support for complex features."""

    # Additional pattern definitions
    ENHANCED_PATTERNS: ClassVar[dict[str, re.Pattern[str]]] = {
        "group": re.compile(r"group\s*\(level=(\d+)([^)]+)\)"),
        "graph": re.compile(r"graph\s*\(([^)]+)\)"),
        "crosstab": re.compile(r"crosstab\s*\(([^)]+)\)"),
        "tree": re.compile(r"tree\.level\.(\d+)\s*\(([^)]+)\)"),
        "composite": re.compile(r"report\s*\(([^)]+)\)"),
        "update": re.compile(r'update\s*=\s*"([^"]+)"'),
        "updatewhere": re.compile(r'updatewhere\s*=\s*"([^"]+)"'),
        "updatekeyinplace": re.compile(r'updatekeyinplace\s*=\s*"([^"]+)"'),
        "stored_procedure": re.compile(r'procedure\s*=\s*"([^"]+)"'),
        "external": re.compile(r"external\s*\(([^)]+)\)"),
        "export": re.compile(r"export\.([a-z]+)\s*\(([^)]+)\)"),
        "import": re.compile(r"import\.([a-z]+)\s*\(([^)]+)\)"),
        "print": re.compile(r'print\.([a-z.]+)\s*=\s*"?([^"\s]+)"?'),
        "htmlgen": re.compile(r"htmlgen\s*\(([^)]+)\)"),
        "htmltable": re.compile(r"htmltable\s*\(([^)]+)\)"),
    }

    def extract(self, source: str, filename: str = "") -> ExtractedData:
        """Extract enhanced DataWindow definition from source.

        Args:
            source: PowerBuilder DataWindow source code
            filename: Optional filename for context

        Returns:
            ExtractedData containing the parsed DataWindow definition
        """
        # First run base extraction
        result = super().extract(source, filename)

        if not result.success or not isinstance(result.data, DataWindowDefinition):
            return result

        # Enhance the base definition
        enhanced_def = self._enhance_definition(result.data, source)

        # Update metadata
        enhanced_metadata = self._extract_enhanced_metadata(enhanced_def, source)
        result.metadata.update(enhanced_metadata)

        # Replace data with enhanced definition
        result.data = enhanced_def

        return result

    def _enhance_definition(
        self, base_def: DataWindowDefinition, source: str
    ) -> EnhancedDataWindowDefinition:
        """Enhance base definition with advanced features."""
        # Create enhanced definition from base
        enhanced = EnhancedDataWindowDefinition(
            release=base_def.release,
            processing_type=base_def.processing_type,
            units=base_def.units,
            bands=base_def.bands,
            columns=base_def.columns,
            controls=base_def.controls,
            table_name=base_def.table_name,
            retrieve_sql=base_def.retrieve_sql,
            arguments=base_def.arguments,
            sort_order=base_def.sort_order,
            properties=base_def.properties,
        )

        # Extract groups
        self._extract_groups(source, enhanced)

        # Extract graphs
        self._extract_graphs(source, enhanced)

        # Extract crosstab
        self._extract_crosstab(source, enhanced)

        # Extract tree nodes
        self._extract_tree_nodes(source, enhanced)

        # Extract composite reports
        self._extract_composite_reports(source, enhanced)

        # Extract update properties
        self._extract_update_properties(source, enhanced)

        # Extract data source details
        self._extract_data_source(source, enhanced)

        # Extract export/import templates
        self._extract_templates(source, enhanced)

        # Extract print specifications
        self._extract_print_specs(source, enhanced)

        # Extract HTML settings
        self._extract_html_settings(source, enhanced)

        return enhanced

    def _extract_groups(self, source: str, definition: EnhancedDataWindowDefinition):
        """Extract group definitions."""
        for match in self.ENHANCED_PATTERNS["group"].finditer(source):
            level = int(match.group(1))
            props = self._parse_properties(match.group(2))

            # Parse by columns
            by_str = props.get("by", "")
            by_columns = [
                col.strip() for col in by_str.strip("()").split(",") if col.strip()
            ]

            group = DataWindowGroup(
                level=level,
                by_columns=by_columns,
                header_height=int(props.get("header.height", 0)),
                trailer_height=int(props.get("trailer.height", 0)),
                newpage=props.get("newpage", "no") == "yes",
                reset_page_number=props.get("reset_page_number", "no") == "yes",
                suppress_duplicates=props.get("suppress_duplicates", "no") == "yes",
                attributes=props,
            )
            definition.groups.append(group)

    def _extract_graphs(self, source: str, definition: EnhancedDataWindowDefinition):
        """Extract graph definitions."""
        for match in self.ENHANCED_PATTERNS["graph"].finditer(source):
            props = self._parse_properties(match.group(1))

            # Parse value columns
            values_str = props.get("values", "")
            value_columns = [
                col.strip() for col in values_str.strip("()").split(",") if col.strip()
            ]

            graph = DataWindowGraph(
                type=props.get("graphtype", "column"),
                title=props.get("title", ""),
                category_column=props.get("category"),
                value_columns=value_columns,
                series_column=props.get("series"),
                x=int(props.get("x", 0)),
                y=int(props.get("y", 0)),
                width=int(props.get("width", 0)),
                height=int(props.get("height", 0)),
                attributes=props,
            )
            definition.graphs.append(graph)

    def _extract_crosstab(self, source: str, definition: EnhancedDataWindowDefinition):
        """Extract crosstab definition."""
        if match := self.ENHANCED_PATTERNS["crosstab"].search(source):
            props = self._parse_properties(match.group(1))

            # Parse column lists
            row_cols = self._parse_column_list(props.get("rows", ""))
            col_cols = self._parse_column_list(props.get("cols", ""))
            val_cols = self._parse_column_list(props.get("values", ""))

            # Parse compute expressions
            compute_exprs = {}
            for key, value in props.items():
                if key.startswith("compute_"):
                    compute_name = key.replace("compute_", "")
                    compute_exprs[compute_name] = value

            definition.crosstab = DataWindowCrosstab(
                row_columns=row_cols,
                column_columns=col_cols,
                value_columns=val_cols,
                compute_expressions=compute_exprs,
                attributes=props,
            )

    def _extract_tree_nodes(
        self, source: str, definition: EnhancedDataWindowDefinition
    ):
        """Extract tree node definitions."""
        for match in self.ENHANCED_PATTERNS["tree"].finditer(source):
            level = int(match.group(1))
            props = self._parse_properties(match.group(2))

            node = DataWindowTreeNode(
                level=level,
                label_column=props.get("label", ""),
                data_column=props.get("data"),
                state_icon_column=props.get("state_icon"),
                image_column=props.get("image"),
                attributes=props,
            )
            definition.tree_nodes.append(node)

    def _extract_composite_reports(
        self, source: str, definition: EnhancedDataWindowDefinition
    ):
        """Extract composite report references."""
        for match in self.ENHANCED_PATTERNS["composite"].finditer(source):
            props = self._parse_properties(match.group(1))
            if report_name := props.get("dataobject"):
                definition.composite_reports.append(report_name)

    def _extract_update_properties(
        self, source: str, definition: EnhancedDataWindowDefinition
    ):
        """Extract update-related properties."""
        # Extract update table
        if match := self.ENHANCED_PATTERNS["update"].search(source):
            definition.update_table = match.group(1)

        # Extract update where clause
        if match := self.ENHANCED_PATTERNS["updatewhere"].search(source):
            definition.update_where_clause = match.group(1)

        # Extract update key columns
        if match := self.ENHANCED_PATTERNS["updatekeyinplace"].search(source):
            key_spec = match.group(1)
            if key_spec.lower() != "no":
                # Parse key columns from table definition
                for column in definition.columns:
                    if column.attributes.get("key", "no") == "yes":
                        definition.update_key_columns.append(column.name)

    def _extract_data_source(
        self, source: str, definition: EnhancedDataWindowDefinition
    ):
        """Extract data source type and details."""
        # Check for stored procedure
        if match := self.ENHANCED_PATTERNS["stored_procedure"].search(source):
            definition.data_source_type = "stored_procedure"
            definition.stored_procedure_name = match.group(1)

        # Check for external data source
        elif match := self.ENHANCED_PATTERNS["external"].search(source):
            definition.data_source_type = "external"
            props = self._parse_properties(match.group(1))
            definition.external_source = props.get("source", "")

    def _extract_templates(self, source: str, definition: EnhancedDataWindowDefinition):
        """Extract export and import templates."""
        # Extract export templates
        for match in self.ENHANCED_PATTERNS["export"].finditer(source):
            format_type = match.group(1)
            template = match.group(2)
            if format_type in ["xml", "json", "csv"]:
                definition.export_template = f"{format_type}:{template}"

        # Extract import templates
        for match in self.ENHANCED_PATTERNS["import"].finditer(source):
            format_type = match.group(1)
            template = match.group(2)
            if format_type in ["xml", "json", "csv"]:
                definition.import_template = f"{format_type}:{template}"

    def _extract_print_specs(
        self, source: str, definition: EnhancedDataWindowDefinition
    ):
        """Extract print specifications."""
        for match in self.ENHANCED_PATTERNS["print"].finditer(source):
            key = match.group(1)
            value = match.group(2)
            definition.print_specs[key] = value

    def _extract_html_settings(
        self, source: str, definition: EnhancedDataWindowDefinition
    ):
        """Extract HTML generation settings."""
        # Extract htmlgen settings
        if match := self.ENHANCED_PATTERNS["htmlgen"].search(source):
            props = self._parse_properties(match.group(1))
            definition.html_settings["htmlgen"] = props

        # Extract htmltable settings
        if match := self.ENHANCED_PATTERNS["htmltable"].search(source):
            props = self._parse_properties(match.group(1))
            definition.html_settings["htmltable"] = props

    def _parse_column_list(self, col_str: str) -> list[str]:
        """Parse a column list string."""
        # Remove parentheses and split by comma
        col_str = col_str.strip("()")
        return [col.strip().strip('"') for col in col_str.split(",") if col.strip()]

    def _extract_enhanced_metadata(
        self, definition: EnhancedDataWindowDefinition, source: str
    ) -> dict[str, Any]:
        """Extract enhanced metadata."""
        metadata = {
            "has_groups": len(definition.groups) > 0,
            "group_count": len(definition.groups),
            "has_graphs": len(definition.graphs) > 0,
            "graph_count": len(definition.graphs),
            "has_crosstab": definition.crosstab is not None,
            "has_treeview": len(definition.tree_nodes) > 0,
            "is_composite": len(definition.composite_reports) > 0,
            "composite_count": len(definition.composite_reports),
            "data_source_type": definition.data_source_type,
            "has_update_properties": definition.update_table is not None,
            "has_export_template": definition.export_template is not None,
            "has_import_template": definition.import_template is not None,
        }

        # Add graph types if present
        if definition.graphs:
            graph_types = list(set(g.type for g in definition.graphs))
            metadata["graph_types"] = graph_types

        # Add group levels if present
        if definition.groups:
            metadata["group_levels"] = sorted(set(g.level for g in definition.groups))

        # Add tree depth if present
        if definition.tree_nodes:
            metadata["tree_depth"] = max(n.level for n in definition.tree_nodes)

        return metadata


# Module-level enhanced extractor instance
enhanced_extraction_manager = EnhancedDataWindowExtractor()
