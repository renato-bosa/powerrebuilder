"""PowerBuilder DataWindow to Flutter converter.

Converts PowerBuilder DataWindow definitions to Flutter DataTable
or custom DataWindow widgets.
"""

import re
import logging
from typing import Any
from dataclasses import dataclass
from ...utils.type_converter import TypeConverter
from ...utils.expression_converter import ExpressionConverter
from ...data.blob_converter import BlobConverter
from ...data.relationship_extractor import RelationshipExtractor, Relationship
from .datawindow_enhancements import (
    ComputedField, ValidationRule, ComputedFieldProcessor, ValidationRuleProcessor
)

logger = logging.getLogger(__name__)


@dataclass
class DataWindowColumn:
    """Represents a DataWindow column."""
    name: str
    label: str
    data_type: str
    width: int | None = None
    alignment: str = "left"
    format: str | None = None
    editable: bool = False
    validation: str | None = None
    values: list[dict[str, str | None]] = None  # For dropdowns
    blob_metadata: dict[str, Any | None] = None  # For blob columns

    def to_dict(self) -> dict[str, Any]:




        """Convert to dictionary for template rendering."""
        result = {
            "name": self.name, "label": self.label, "data_type": self.data_type, "width": self.width, "alignment": f"TextAlign.{self.alignment}", "format": f'"{self.format}"' if self.format else "null", "editable": str(self.editable).lower(), "values": self.values
        }

        # Add blob metadata if present
        if self.blob_metadata:
            result["blob_metadata"] = self.blob_metadata
            result["is_blob"] = True
        else:
            result["is_blob"] = False

        return result


@dataclass
class DataWindowDefinition:
    """Represents a complete DataWindow definition."""
    name: str
    sql: str | None = None
    presentation_style: str = "grid"
    columns: list[DataWindowColumn] = None
    row_type: str = "Map<String, dynamic>"
    sorts: list[str] = None
    filters: list[str] = None
    groups: list[str] = None
    computed_fields: list[ComputedField] = None
    validation_rules: list[ValidationRule] = None
    relationships: list[Relationship] = None

    def __post_init__(self) -> None:


        if self.columns is None:
            self.columns = []
        if self.sorts is None:
            self.sorts = []
        if self.filters is None:
            self.filters = []
        if self.groups is None:
            self.groups = []
        if self.computed_fields is None:
            self.computed_fields = []
        if self.validation_rules is None:
            self.validation_rules = []
        if self.relationships is None:
            self.relationships = []

    def to_dict(self) -> dict[str, Any]:




        """Convert to dictionary for template rendering."""
        return {
            "name": self.name, "presentation_style": self.presentation_style, "columns": [col.to_dict() for col in self.columns], "row_type": self.row_type, "sql": self.sql, "has_sorting": len(self.sorts) > 0, "has_filtering": len(self.filters) > 0, "has_grouping": len(self.groups) > 0, "computed_fields": [cf.to_dict() for cf in self.computed_fields], "has_computed_fields": len(self.computed_fields) > 0, "validation_rules": [vr.to_dict() for vr in self.validation_rules], "has_validation": len(self.validation_rules) > 0, "relationships": [rel.to_dict() for rel in self.relationships], "has_relationships": len(self.relationships) > 0, "imports": self._get_imports()
        }

    def _get_imports(self) -> list[str]:




        """Get required imports for this DataWindow."""
        imports = [
            "import 'package:flutter/material.dart'",
            "import '../core/app_design_system.dart';"
        ]

        if self.presentation_style == "graph":
            imports.append("import 'package:charts_flutter/flutter.dart' as charts;")

        # Check for blob columns
        has_blob = any(col.blob_metadata is not None for col in self.columns)
        if has_blob:
            imports.extend([
                "import 'dart:typed_data';",
                "import 'dart:convert';",
                "import 'dart:io';",
                "import 'package:path_provider/path_provider.dart';"
            ])
            # Add specific blob display widgets
            for col in self.columns:
                if col.blob_metadata:
                    widget_name = col.blob_metadata.get("display_widget", "")
                    if widget_name:
                        imports.append(f"import '../widgets/{self._to_snake_case(widget_name)}.dart';")

        return imports

    def _to_snake_case(self, name: str) -> str:




        """Convert name to snake_case."""
        import re
        s1 = re.sub('(.)([A-Z][a-z]+)', r'\1_\2', name)
        return re.sub('([a-z0-9])([A-Z])', r'\1_\2', s1).lower()

    def get_blob_columns(self) -> list[DataWindowColumn]:




        """Get all blob columns in this DataWindow."""
        return [col for col in self.columns if col.blob_metadata is not None]

    def generate_blob_handling_code(self, blob_converter: 'BlobConverter') -> dict[str, Any]:




        """Generate blob handling code for all blob columns.

        Args:
            blob_converter: BlobConverter instance

        Returns:
            Dictionary with:
            - repository_methods: Blob repository methods
            - display_widgets: Blob display widget definitions
        """
        blob_columns = self.get_blob_columns()
        if not blob_columns:
            return {"repository_methods": "", "display_widgets": []}

        # Generate repository methods
        blob_fields = [{"name": col.name, "type": "blob"} for col in blob_columns]
        repository_methods = blob_converter.generate_blob_repository_methods(blob_fields)

        # Generate display widgets
        display_widgets = []
        for col in blob_columns:
            usage = col.blob_metadata.get("usage", "data")
            mime_type = "image/jpeg" if usage == "image" else None
            widget_code = blob_converter.generate_blob_widget(col.name, mime_type)
            display_widgets.append({
                "name": col.blob_metadata.get("display_widget", f"{col.name}_display"),
                "code": widget_code
            })

        return {
            "repository_methods": repository_methods,
            "display_widgets": display_widgets
        }


class DataWindowConverter:
    """Converts PowerBuilder DataWindow to Flutter widgets."""

    def __init__(self, type_converter: TypeConverter | None = None,
                 expression_converter: ExpressionConverter | None = None,
                 blob_converter: BlobConverter | None = None,
                 relationship_extractor: RelationshipExtractor | None = None,
                 computed_field_processor: ComputedFieldProcessor | None = None,
                 validation_rule_processor: ValidationRuleProcessor | None = None):


        """Initialize the DataWindow converter.

        Args:
            type_converter: Type converter instance
            expression_converter: Expression converter instance
            blob_converter: Blob converter instance
            relationship_extractor: Relationship extractor instance
            computed_field_processor: Computed field processor instance
            validation_rule_processor: Validation rule processor instance
        """
        self.type_converter = type_converter or TypeConverter()
        self.expression_converter = expression_converter or ExpressionConverter(self.type_converter)
        self.blob_converter = blob_converter or BlobConverter()
        self.relationship_extractor = relationship_extractor or RelationshipExtractor()
        self.computed_field_processor = computed_field_processor or ComputedFieldProcessor(self.expression_converter)
        self.validation_rule_processor = validation_rule_processor or ValidationRuleProcessor()

        # Presentation style mappings
        self.style_map = {
            "grid": "DataTable",
            "freeform": "Form",
            "tabular": "ListView",
            "group": "GroupedListView",
            "crosstab": "CrossTab",
            "graph": "Chart",
            "composite": "Composite",
            "richtext": "RichText"
        }

    def convert_datawindow(self, dw_syntax: str, dw_name: str) -> DataWindowDefinition:




        """Convert DataWindow syntax to definition.

        Args:
            dw_syntax: PowerBuilder DataWindow syntax
            dw_name: Name of the DataWindow

        Returns:
            DataWindowDefinition object
        """
        definition = DataWindowDefinition(name=self._to_pascal_case(dw_name))

        # Extract SQL
        definition.sql = self._extract_sql(dw_syntax)

        # Extract presentation style
        definition.presentation_style = self._extract_presentation_style(dw_syntax)

        # Extract columns
        definition.columns = self._extract_columns(dw_syntax)

        # Extract sorting
        definition.sorts = self._extract_sorts(dw_syntax)

        # Extract filters
        definition.filters = self._extract_filters(dw_syntax)

        # Extract groups
        definition.groups = self._extract_groups(dw_syntax)

        # Extract computed fields with enhanced processing
        definition.computed_fields = self._extract_computed_fields(dw_syntax, definition.columns)

        # Extract validation rules from columns
        definition.validation_rules = self._extract_validation_rules(definition.columns)

        # Extract relationships from SQL
        if definition.sql:
            definition.relationships = self._extract_relationships(definition.sql)

        # Determine row type
        definition.row_type = self._determine_row_type(definition)

        return definition

    def _extract_sql(self, syntax: str) -> str | None:




        """Extract SQL from DataWindow syntax."""
        # Look for retrieve section
        retrieve_match = re.search(
            r'retrieve\s*=\s*"([^"]+)"', 
            syntax, 
            re.IGNORECASE | re.DOTALL
        )
        if retrieve_match:
            sql = retrieve_match.group(1)
            # Clean up escape sequences
            sql = sql.replace("~n", "\n")
            sql = sql.replace("~t", "\t")
            sql = sql.replace("~~", "~")
            sql = sql.replace('~"', '"')
            return sql.strip()

        # Look for PBSELECT
        pbselect_match = re.search(
            r'PBSELECT\s*\((.*?)\)\s*\)',
            syntax,
            re.IGNORECASE | re.DOTALL
        )
        if pbselect_match:
            return self._convert_pbselect(pbselect_match.group(0))

        return None

    def _convert_pbselect(self, pbselect: str) -> str:




        """Convert PBSELECT to standard SQL."""
        # Extract tables
        tables = []
        table_matches = re.findall(r'TABLE\s*\(\s*NAME\s*=\s*"([^"]+)"', pbselect)
        tables.extend(table_matches)

        # Extract columns
        columns = []
        column_matches = re.findall(r'COLUMN\s*\(\s*NAME\s*=\s*"([^"]+)"', pbselect)
        columns.extend(column_matches)

        # Extract WHERE clause
        where_clause = ""
        where_match = re.search(r'WHERE\s*\((.*?)\)\s*\)', pbselect, re.DOTALL)
        if where_match:
            where_clause = self._convert_where_clause(where_match.group(1))

        # Build SQL
        if not columns:
            columns = ["*"]

        sql = f"SELECT {', '.join(columns)}"
        if tables:
            sql += f" FROM {', '.join(tables)}"
        if where_clause:
            sql += f" WHERE {where_clause}"

        return sql

    def _convert_where_clause(self, where_expr: str) -> str:




        """Convert PBSELECT WHERE expression to SQL."""
        # Simple conversion - a full implementation would parse the expression tree
        result = where_expr

        # Convert EXP1, EXP2, OP pattern
        pattern = r'EXP1\s*=\s*"([^"]+)"\s+OP\s*=\s*"([^"]+)"\s+EXP2\s*=\s*"([^"]+)"'

        def replace_expr(match):


            exp1 = match.group(1)
            op = match.group(2)
            exp2 = match.group(3)
            return f"{exp1} {op} {exp2}"

        result = re.sub(pattern, replace_expr, result)

        # Convert LOGIC
        result = re.sub(r'LOGIC\s*=\s*"and"', 'AND', result, flags=re.IGNORECASE)
        result = re.sub(r'LOGIC\s*=\s*"or"', 'OR', result, flags=re.IGNORECASE)

        # Convert PowerBuilder parameters (:param) to SQL parameters (@param)
        result = re.sub(r':(\w+)', r'@\1', result)

        return result

    def _extract_presentation_style(self, syntax: str) -> str:




        """Extract presentation style from DataWindow syntax."""
        style_match = re.search(
            r'processing\s*=\s*["\']?(\d+)["\']?',
            syntax,
            re.IGNORECASE
        )

        if style_match:
            style_code = style_match.group(1)
            # PowerBuilder processing codes
            style_map = {
                "0": "grid",      # Grid (default)
                "1": "tabular",   # Tabular
                "2": "freeform",  # Freeform
                "3": "group",     # Group
                "4": "crosstab",  # Crosstab
                "5": "graph",     # Graph
                "6": "composite", # Composite
                "7": "richtext"   # RichText
            }
            return style_map.get(style_code, "grid")

        return "grid"

    def _extract_columns(self, syntax: str) -> list[DataWindowColumn]:




        """Extract column definitions from DataWindow syntax."""
        columns = []

        # Extract column definitions
        # Handle nested parentheses in type definitions like char(50)
        column_pattern = r'column\s*=\s*\(((?:[^()]|\([^)]*\))*)\)'
        column_matches = re.findall(column_pattern, syntax, re.IGNORECASE | re.DOTALL)

        for col_def in column_matches:
            column = self._parse_column_definition(col_def)
            if column:
                columns.append(column)

        # If no explicit columns, try to extract from SQL
        if not columns and self._extract_sql(syntax):
            columns = self._extract_columns_from_sql(self._extract_sql(syntax))

        return columns

    def _parse_column_definition(self, col_def: str) -> DataWindowColumn | None:




        """Parse a single column definition."""
        # Extract name - try quoted first, then unquoted
        # Use \b for word boundary to avoid matching "dbname"
        name_match = re.search(r'\bname\s*=\s*["\']([^"\']+)["\']', col_def)
        if not name_match:
            name_match = re.search(r'\bname\s*=\s*([^\s\)]+)', col_def)

        if not name_match:
            return None

        name = name_match.group(1)

        # Extract other properties with defaults
        label = self._extract_property(col_def, "label", name.split(".")[-1])
        data_type = self._extract_property(col_def, "type", "string")
        width = self._extract_numeric_property(col_def, "width")
        alignment = self._extract_property(col_def, "alignment", "left")
        format = self._extract_property(col_def, "format")
        editable = self._extract_property(col_def, "edit.style", "").lower() != "none"
        validation = self._extract_property(col_def, "validation")

        # Convert PowerBuilder type to Dart type
        dart_type = self.type_converter.convert_type(data_type)

        # Extract dropdown values if present
        values = None
        if "values" in col_def:
            values = self._extract_dropdown_values(col_def)

        # Check if this is a blob column and add blob-specific properties
        if data_type.lower() == "blob":
            # Try to determine blob usage from column name or properties
            usage = self._determine_blob_usage(name, col_def)
            # Add blob metadata to column
            column = DataWindowColumn(
                name=name,
                label=label,
                data_type=dart_type,
                width=width,
                alignment=alignment,
                format=format,
                editable=editable,
                validation=validation,
                values=values
            )
            # Store blob metadata for later use
            column.blob_metadata = {
                "usage": usage,
                "display_widget": f"{self._to_pascal_case(name)}BlobDisplay"
            }
            return column

        return DataWindowColumn(
            name=name,
            label=label,
            data_type=dart_type,
            width=width,
            alignment=alignment,
            format=format,
            editable=editable,
            validation=validation,
            values=values
        )

    def _extract_property(self, text: str, prop: str, default: str = None) -> str | None:




        """Extract a property value from text."""
        # Try quoted value first
        # Use \b for word boundary to avoid partial matches
        pattern = rf'\b{prop}\s*=\s*["\']([^"\']+)["\']'
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            return match.group(1)

        # Try unquoted value
        pattern = rf'\b{prop}\s*=\s*([^\s\)]+)'
        match = re.search(pattern, text, re.IGNORECASE)
        return match.group(1) if match else default

    def _extract_numeric_property(self, text: str, prop: str) -> int | None:




        """Extract a numeric property value from text."""
        pattern = rf'\b{prop}\s*=\s*["\']?(\d+)["\']?'
        match = re.search(pattern, text, re.IGNORECASE)
        return int(match.group(1)) if match else None

    def _extract_dropdown_values(self, col_def: str) -> list[dict[str, str]]:




        """Extract dropdown values from column definition."""
        values = []

        # Look for values pattern
        values_match = re.search(r'values\s*=\s*["\']([^"\']+)["\']', col_def)
        if values_match:
            values_str = values_match.group(1)
            # Parse tab-separated values
            pairs = values_str.split("\t")
            for i in range(0, len(pairs), 2):
                if i + 1 < len(pairs):
                    values.append({
                        "display": pairs[i],
                        "data": pairs[i + 1]
                    })

        return values

    def _extract_columns_from_sql(self, sql: str) -> list[DataWindowColumn]:




        """Extract columns from SQL statement."""
        columns = []

        # Simple extraction - a full implementation would use SQL parser
        select_match = re.search(r'SELECT\s+(.*?)\s+FROM', sql, re.IGNORECASE | re.DOTALL)
        if select_match:
            columns_str = select_match.group(1)

            # Split by comma (simplified - doesn't handle nested functions)
            col_names = [col.strip() for col in columns_str.split(',')]

            for col_name in col_names:
                # Extract alias if present
                alias_match = re.search(r'(\w+)\s+AS\s+(\w+)', col_name, re.IGNORECASE)
                if alias_match:
                    name = alias_match.group(2)
                else:
                    # Get last part after dot
                    name = col_name.split('.')[-1]

                columns.append(DataWindowColumn(
                    name=col_name,
                    label=name,
                    data_type="String",  # Default type
                    alignment="left",
                    editable=False
                ))

        return columns

    def _extract_sorts(self, syntax: str) -> list[str]:




        """Extract sort definitions."""
        sorts = []

        # Look for sort property
        sort_match = re.search(r'sort\s*=\s*["\']([^"\']+)["\']', syntax)
        if sort_match:
            sort_str = sort_match.group(1)
            # Parse sort string
            sorts = [s.strip() for s in sort_str.split(',')]

        return sorts

    def _extract_filters(self, syntax: str) -> list[str]:




        """Extract filter definitions."""
        filters = []

        # Look for filter property
        filter_match = re.search(r'filter\s*=\s*["\']([^"\']+)["\']', syntax)
        if filter_match:
            filter_str = filter_match.group(1)
            filters.append(filter_str)

        return filters

    def _extract_groups(self, syntax: str) -> list[str]:




        """Extract group definitions."""
        groups = []

        # Look for group properties
        group_pattern = r'group\s*\(\s*level\s*=\s*(\d+).*?by\s*=\s*["\']([^"\']+)["\']'
        group_matches = re.findall(group_pattern, syntax, re.IGNORECASE | re.DOTALL)

        for level, group_by in group_matches:
            groups.append(group_by)

        return groups

    def _extract_computed_fields(self, syntax: str, columns: list[DataWindowColumn]) -> list[ComputedField]:




        """Extract computed field definitions with enhanced processing."""
        computed_fields = []

        # Look for compute expressions
        compute_pattern = r'compute\s*\((.*?)\)'
        compute_matches = re.findall(compute_pattern, syntax, re.IGNORECASE | re.DOTALL)

        # Convert columns to dict format for processor
        column_dicts = [
            {"name": col.name, "data_type": col.data_type} 
            for col in columns
        ]

        for compute_def in compute_matches:
            name = self._extract_property(compute_def, "name")
            expression = self._extract_property(compute_def, "expression")

            if name and expression:
                # Use enhanced processor
                computed_field = self.computed_field_processor.process_computed_field(
                    name, expression, column_dicts
                )
                computed_fields.append(computed_field)

        return computed_fields

    def _extract_validation_rules(self, columns: list[DataWindowColumn]) -> list[ValidationRule]:




        """Extract validation rules from column definitions."""
        validation_rules = []

        for column in columns:
            if column.validation:
                # Process validation expression
                rule = self.validation_rule_processor.process_validation_rule(
                    column.name, column.validation
                )
                if rule:
                    validation_rules.append(rule)

        return validation_rules

    def _determine_row_type(self, definition: DataWindowDefinition) -> str:




        """Determine the row type for the DataWindow."""
        if definition.name:
            # Use a custom model class
            return f"{definition.name}Row"
        else:
            # Use generic map
            return "Map<String, dynamic>"

    def _to_pascal_case(self, name: str) -> str:




        """Convert name to PascalCase."""
        # Remove prefix if present
        if name.startswith("d_"):
            name = name[2:]
        if name.startswith("dw_"):
            name = name[3:]

        # Convert to PascalCase
        parts = name.split("_")
        return "".join(p.capitalize() for p in parts)

    def _determine_blob_usage(self, column_name: str, col_def: str) -> str:




        """Determine the usage type of a blob column based on name and properties.

        Args:
            column_name: Name of the column
            col_def: Column definition string

        Returns:
            Usage type: 'image', 'document', 'data'
        """
        name_lower = column_name.lower()

        # Check for image-related names
        image_keywords = ['photo', 'picture', 'image', 'icon', 'logo', 'avatar', 
                         'thumbnail', 'screenshot', 'jpg', 'jpeg', 'png', 'gif']
        if any(keyword in name_lower for keyword in image_keywords):
            return 'image'

        # Check for document-related names
        doc_keywords = ['document', 'doc', 'pdf', 'file', 'attachment', 'report',
                       'excel', 'word', 'spreadsheet', 'presentation']
        if any(keyword in name_lower for keyword in doc_keywords):
            return 'document'

        # Check column properties for hints
        if 'image' in col_def.lower() or 'picture' in col_def.lower():
            return 'image'

        # Default to generic data
        return 'data'

    def _extract_relationships(self, sql: str) -> list[Relationship]:




        """Extract relationships from SQL query.

        Args:
            sql: SQL query string

        Returns:
            List of extracted relationships
        """
        try:
            # Parse the SQL to get AST
            from src.parse.parsers.sql_parser import SQLParser

            parser = SQLParser()
            parsed_sql = parser.parse(sql)

            if parsed_sql:
                # Get the first statement (usually SELECT)
                stmt = parsed_sql[0] if isinstance(parsed_sql, list) else parsed_sql.statements[0]

                # Use relationship extractor if it's a SELECT statement
                from src.model.ast.nodes.sql import SelectStatement
                if isinstance(stmt, SelectStatement):
                    relationships = self.relationship_extractor.extract_from_select(stmt)

                    # Log extracted relationships
                    for rel in relationships:
                        logger.info("Extracted relationship: %s -> %s (%s)", rel.source_table, rel.target_table, rel.relationship_type.name)

                    return relationships

        except Exception as e:
            logger.warning("Failed to extract relationships from SQL: %s", e)

        return []