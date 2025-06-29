"""Code generation module for converting PowerBuilder models to modern code.

This module forms the final stage in the PowerBuilder reverse engineering pipeline,
generating modern web application code by COMBINING outputs from BOTH the Parse and 
Decompile stages (which run in PARALLEL).

INPUTS:
- From Parse stage: ASTs containing UI definitions, data models, structure
- From Decompile stage: High-level code containing business logic, functions

OUTPUTS:
- Backend: Python/Litestar APIs, SQLModel models, Pydantic schemas
- Frontend: Flutter/Dart UI, screens, widgets, state management

Key components:
- CodeGenerator: Base class providing template rendering functionality
- ModelGenerator: Generates SQLModel models from parsed database schema
- ServiceGenerator: Converts decompiled business logic into service layer classes
- FlutterGenerator: Transforms parsed UI definitions into Flutter/Dart widgets

The code generation relies on Jinja2 templates to merge:
- UI structure and data models from Parse output
- Business logic and functions from Decompile output

Each generator handles a specific aspect of the application and is orchestrated
through the main entry points: generate_models(), generate_services(), and generate_flutter().
"""

import logging
from pathlib import Path
from typing import Any

from jinja2 import Environment, FileSystemLoader

from model.utils.errors import GenerateError
from parse.parsers.sql_parser import SQLParser
from generate.converters.data.relationship_extractor import RelationshipExtractor
from generate.converters.utils.ast_converter import ASTConverter
from src.generate.converters.flutter.ui.widget_converter import UIConverter
from src.generate.converters.flutter.state.event_converter import EventConverter
from src.generate.converters.flutter.ui.datawindow_converter import DataWindowConverter
from generate.converters.utils.expression_converter import ExpressionConverter
from src.generate.converters.flutter.state.model_converter import TypeConverter
from src.generate.converters.flutter.business.logic_converter import MethodBodyConverter
from generate.converters.logic.event_wiring import EventWiringSystem
from src.generate.converters.flutter.ui.layout_converter import LayoutConverter, LayoutStrategy
from generate.python_ui_generator import PythonUIGenerator
from generate.base_generator import CodeGenerator

from .jinja_filters import register_filters
from .template_schemas import validate_template_context
from .template_validator import TemplateValidator

import re

logger = logging.getLogger(__name__)


class GenerateCoordinator:
    """Coordinator class that wraps generation functions for pipeline integration."""

    def __init__(self, input_dir: str, output_dir: str, framework: str = 'flutter', null_safety: bool = True, generate_tests: bool = False) -> None:


        """Initialize the generate coordinator.

        Args:
            input_dir: Directory containing parsed AST files
            output_dir: Directory for generated code
            framework: Target framework (default: 'flutter')
            null_safety: Enable null safety (default: True)
            generate_tests: Generate test files (default: False)
        """
        self.input_dir = Path(input_dir)
        self.output_dir = Path(output_dir)
        self.framework = framework
        self.null_safety = null_safety
        self.generate_tests = generate_tests

        # Create output directories
        self.output_dir.mkdir(parents=True, exist_ok=True)

        # Initialize generators (disable validation temporarily for converter integration)
        self.model_generator = ModelGenerator(
            str(Path(__file__).parent.parent / "templates"), str(self.output_dir / "backend"), validate_templates=False
        )
        self.service_generator = ServiceGenerator(
            str(Path(__file__).parent.parent / "templates"), str(self.output_dir / "backend"), validate_templates=False
        )
        self.flutter_generator = FlutterGenerator(
            str(Path(__file__).parent / "templates" / "flutter"), str(self.output_dir / "flutter"), validate_templates=False
        )

        # Pass the layout converter to the Flutter generator
        self.flutter_generator.layout_converter = None  # Will set after initialization

        # Initialize Python UI generator
        self.python_ui_generator = PythonUIGenerator(
            str(Path(__file__).parent / "templates" / "python"), str(self.output_dir / "python"), validate_templates=False
        )

        # Initialize converters
        self.type_converter = TypeConverter()
        self.ast_converter = ASTConverter()
        self.ui_converter = UIConverter(design_theme="liquid_glass")  # Enable Liquid Glass aesthetic
        # Event converter expects type_converter and expression_converter
        # For now, initialize with minimal setup
        # self.event_converter = EventConverter()
        # Note: These converters expect different parameters, so we'll use them carefully
        # self.datawindow_converter = DataWindowConverter()
        # self.expression_converter = ExpressionConverter()

        # Initialize layout converter with absolute positioning by default
        # This preserves the exact PowerBuilder layout
        # Pass the event wiring system from flutter generator
        self.layout_converter = LayoutConverter(
            LayoutStrategy.ABSOLUTE, ui_converter=self.ui_converter, event_wiring_system=self.flutter_generator.event_wiring_system
        )

        # Pass layout converter and UI converter to generators
        self.flutter_generator.layout_converter = self.layout_converter
        self.flutter_generator.ui_converter = self.ui_converter
        self.python_ui_generator.layout_converter = self.layout_converter

    def generate_from_object(self, object_type: str, object_name: str, ast_file: str) -> dict:




        """Generate code from a parsed object.

        Args:
            object_type: Type of PowerBuilder object
            object_name: Name of the object
            ast_file: Path to AST JSON file

        Returns:
            Dictionary with generation results
        """
        try:
            import json

            # Load AST data
            ast_path = Path(ast_file)
            if not ast_path.exists():
                # Try relative to input dir
                ast_path = self.input_dir / ast_file

            if not ast_path.exists():
                logger.error(f"AST file not found: {ast_file}")
                return {'success': False, 'error': 'AST file not found'}

            with open(ast_path) as f:
                ast_data = json.load(f)

            generated_files = []

            # Route to appropriate generator based on object type
            if object_type in ['window', 'w']:
                # Try to use converters for better conversion
                try:
                    window_model = self._convert_window_with_converters(ast_data, object_name)
                    if self.framework == 'flutter':
                        result = self.flutter_generator.generate_screen_from_model(window_model)
                        generated_files.append(f"flutter/screens/{object_name}_screen.dart")
                    else:
                        # Generate Python UI
                        self.python_ui_generator.generate_window(window_model)
                        generated_files.append(f"python/windows/{object_name.lower()}.py")
                except Exception as e:
                    logger.warning(f"Converter failed, falling back to extraction: {e}")
                    # Fallback to original extraction method
                    window_info = extract_window_from_ast(ast_data)
                    result = self.flutter_generator.generate_screen(
                        name=object_name, route_name=f"/{object_name.lower()}", params=window_info.get("params", {}), controllers=window_info.get("controllers", []), services=window_info.get("services", [])
                    )
                    generated_files.append(f"flutter/screens/{object_name}_screen.dart")

            elif object_type in ['datawindow', 'dw', 'd']:
                # Generate model from DataWindow
                dw_data = extract_datawindow_from_ast(ast_data)
                if dw_data:
                    result = self.model_generator.generate_model(
                        object_name, dw_data.get("columns", []), dw_data.get("relationships", [])
                    )
                    generated_files.append(f"backend/models/{object_name}.py")

            elif object_type in ['userobject', 'uo', 'u']:
                # Check if it's a visual or non-visual object
                if any(prefix in object_name.lower() for prefix in ["uo_", "u_"]):
                    # Generate Flutter widget
                    widget_info = extract_widget_from_ast(ast_data)
                    result = self.flutter_generator.generate_widget(
                        name=object_name, properties=widget_info.get("properties", {}), methods=widget_info.get("methods", [])
                    )
                    generated_files.append(f"flutter/widgets/{object_name}_widget.dart")
                else:
                    # Generate service
                    methods = extract_methods_from_ast(ast_data)
                    result = self.service_generator.generate_service(
                        object_name, methods
                    )
                    generated_files.append(f"backend/services/{object_name}_service.py")

            elif object_type in ['structure', 's']:
                # Generate model from structure
                # Extract structure fields as columns
                columns = []
                if 'fields' in ast_data:
                    for field in ast_data['fields']:
                        columns.append({
                            'name': field.get('name', ''), 'type': field.get('type', 'string'), 'nullable': field.get('nullable', True)
                        })

                result = self.model_generator.generate_model(
                    object_name, columns, []
                )
                generated_files.append(f"backend/models/{object_name}.py")

            else:
                logger.warning(f"Unsupported object type: {object_type}")
                return {'success': False, 'error': f'Unsupported object type: {object_type}'}

            return {
                'success': True, 'files': generated_files, 'object_type': object_type, 'object_name': object_name
            }

        except Exception as e:
            logger.error(f"Failed to generate code for {object_name}: {e}")
            return {
                'success': False, 'error': str(e), 'object_type': object_type, 'object_name': object_name
            }

    def _convert_window_with_converters(self, ast_data: dict, object_name: str) -> dict:




        """Convert window AST data using converters.

        Args:
            ast_data: JSON AST data
            object_name: Name of the window

        Returns:
            Window model suitable for template generation
        """
        # Extract basic window information
        window_model = {
            'name': object_name, 'title': ast_data.get('title', object_name), 'controls': [], 'events': [], 'variables': [], 'methods': []
        }

        # Convert controls using UI converter
        if 'controls' in ast_data:
            for control_data in ast_data['controls']:
                try:
                    control_type = control_data.get('type', 'unknown')
                    control_props = control_data.get('properties', {})

                    # Use UI converter to convert PowerBuilder control to Flutter widget
                    flutter_control = self.ui_converter.convert_control(
                        control_type, control_data.get('name', ''), control_props
                    )
                    if flutter_control:
                        control_model = {
                            'name': control_data.get('name', ''), 'type': control_type, 'flutter_widget': flutter_control, 'position': control_data.get('position', {}), 'size': control_data.get('size', {})
                        }
                        window_model['controls'].append(control_model)
                    else:
                        # Even if converter fails, preserve the control with position
                        control_model = {
                            'name': control_data.get('name', ''), 'type': control_type, 'flutter_widget': {'widget': 'Container'}, # Default
                            'position': control_data.get('position', {}), 'size': control_data.get('size', {})
                        }
                        window_model['controls'].append(control_model)
                except Exception as e:
                    logger.warning(f"Failed to convert control: {e}")

        # Extract events (simplified for now without full converter)
        if 'events' in ast_data:
            for event_data in ast_data['events']:
                try:
                    event_model = {
                        'name': event_data.get('name', ''), 'body': event_data.get('body', [])
                    }
                    window_model['events'].append(event_model)
                except Exception as e:
                    logger.warning(f"Failed to process event: {e}")

        # Extract variables
        if 'variables' in ast_data:
            for var in ast_data['variables']:
                var_model = {
                    'name': var.get('name', ''), 'type': var.get('type', 'any'), 'dart_type': self.type_converter.convert_type(var.get('type', 'any')), 'initial_value': var.get('initial_value')
                }
                window_model['variables'].append(var_model)

        # Extract methods
        methods = extract_methods_from_ast(ast_data)
        window_model['methods'] = methods

        return window_model

    def _convert_control_properties(self, pb_props: dict, widget_info: dict) -> dict:




        """Convert PowerBuilder control properties to Flutter widget properties."""
        flutter_props = {}

        # Map common properties
        if 'text' in pb_props:
            flutter_props['text'] = pb_props['text']
        if 'enabled' in pb_props:
            flutter_props['enabled'] = pb_props['enabled']
        if 'visible' in pb_props:
            flutter_props['visible'] = pb_props['visible']

        # Add widget-specific property mappings from widget_info
        if 'property_mappings' in widget_info:
            for pb_prop, flutter_prop in widget_info['property_mappings'].items():
                if pb_prop in pb_props:
                    flutter_props[flutter_prop] = pb_props[pb_prop]

        return flutter_props

    def generate_flutter_project(self, app_info: dict = None) -> dict:




        """Generate a complete Flutter project structure.

        Args:
            app_info: Application information (name, description, features, etc.)

        Returns:
            Dictionary with generation results
        """
        try:
            # Default app info if not provided
            if app_info is None:
                app_info = {
                    "name": "pb_app", "display_name": "PowerBuilder App", "description": "Flutter application converted from PowerBuilder", "has_database": False, "has_charts": False, "has_file_operations": False, "has_printing": False, "initial_window": None, "variables": [], "events": []
                }

            # Generate the project structure
            self.flutter_generator.generate_project_structure(app_info)

            # Return success
            return {
                'success': True, 'message': 'Flutter project structure generated successfully', 'project_path': str(self.output_dir / "flutter")
            }

        except Exception as e:
            logger.error(f"Failed to generate Flutter project: {e}")
            return {'success': False, 'error': str(e)}


def _infer_foreign_key_from_column_name(column_name: str) -> dict | None:








    """Infer foreign key relationship from column name patterns.

    Args:
        column_name: Name of the column to analyze

    Returns:
        Dictionary with target_table and target_column if pattern matches, None otherwise
    """
    if not column_name:
        return None

    # Common foreign key naming patterns
    patterns = [
        # Pattern: table_id or table_code
        (r'^(\w+?)_(id|code|key|fk)$', lambda m: (m.group(1), m.group(2) if m.group(2) != 'fk' else 'id')), # Pattern: fk_table or fk_table_id
        (r'^fk_(\w+?)(?:_id)?$', lambda m: (m.group(1), 'id')), # Pattern: tableid (no underscore)
        (r'^(\w+?)id$', lambda m: (m.group(1), 'id')), # Pattern: parent_table_id for hierarchical relationships
        (r'^parent_(\w+?)_id$', lambda m: (m.group(1), 'id')), # Pattern: ref_table or reference_table
        (r'^(?:ref|reference)_(\w+)$', lambda m: (m.group(1), 'id')), ]

    column_lower = column_name.lower()

    for pattern, extractor in patterns:
        match = re.match(pattern, column_lower)
        if match:
            target_table, target_column = extractor(match)

            # Handle common abbreviations and pluralization
            table_mappings = {
                'cust': 'customer', 'prod': 'product', 'emp': 'employee', 'dept': 'department', 'ord': 'order', 'cat': 'category', 'addr': 'address', 'acct': 'account', 'inv': 'invoice', 'doc': 'document', 'usr': 'user', 'grp': 'group', 'org': 'organization', 'loc': 'location', 'proj': 'project', 'mgr': 'manager', 'suppl': 'supplier', 'cmpny': 'company', 'pers': 'person'
            }

            # Expand abbreviations
            expanded_table = table_mappings.get(target_table, target_table)

            # Check for plural forms (simple heuristic)
            possible_tables = [
                expanded_table, expanded_table + 's', # Simple plural
                expanded_table + 'es', # -es plural
                expanded_table.rstrip('y') + 'ies' if expanded_table.endswith('y') else None, # -y to -ies
            ]

            # Return the first valid option
            for table_name in possible_tables:
                if table_name:
                    return {
                        "target_table": table_name, "target_column": target_column
                    }

    # Special cases for common relationship patterns
    special_cases = {
        'created_by': {'target_table': 'user', 'target_column': 'id'}, 'updated_by': {'target_table': 'user', 'target_column': 'id'}, 'modified_by': {'target_table': 'user', 'target_column': 'id'}, 'assigned_to': {'target_table': 'user', 'target_column': 'id'}, 'owner_id': {'target_table': 'user', 'target_column': 'id'}, 'manager_id': {'target_table': 'employee', 'target_column': 'id'}, 'supervisor_id': {'target_table': 'employee', 'target_column': 'id'}, 'parent_id': {'target_table': None, 'target_column': 'id'}, # Self-referential
        'status_id': {'target_table': 'status', 'target_column': 'id'}, 'type_id': {'target_table': 'type', 'target_column': 'id'}, 'category_id': {'target_table': 'category', 'target_column': 'id'}, 'country_id': {'target_table': 'country', 'target_column': 'id'}, 'state_id': {'target_table': 'state', 'target_column': 'id'}, 'city_id': {'target_table': 'city', 'target_column': 'id'}, }

    if column_lower in special_cases:
        return special_cases[column_lower]

    return None


def extract_datawindow_from_ast(ast_data: dict) -> dict | None:








    """Extract DataWindow information from parsed AST.

    Args:
        ast_data: Parsed AST data from JSON

    Returns:
        Dictionary with columns, relationships, and SQL info
    """
    if not isinstance(ast_data, dict):
        return None

    # Look for DataWindow node in the AST
    if (
        ast_data.get("node_type") == "DataWindow"
        or ast_data.get("type") == "datawindow"
    ):
        columns = []
        relationships = []
        sql_info = {}
        primary_keys = []

        # Extract columns with foreign key information
        if "columns" in ast_data:
            for col in ast_data["columns"]:
                col_name = col.get("name", col.get("column_name", ""))
                col_type = col.get("column_type", col.get("type", "string"))

                column_info = {
                    "name": col_name, "type": col_type, "nullable": col.get("is_nullable", True), "length": col.get("length"), "precision": col.get("precision"), "scale": col.get("scale"), }

                # Extract foreign key information if present
                if col.get("foreign_key"):
                    column_info["foreign_key"] = col["foreign_key"]
                    # Create a relationship entry
                    relationships.append({
                        "type": "foreign_key", "source_column": column_info["name"], "target_table": col.get("foreign_table"), "target_column": col.get("foreign_column", "id"), })
                # Infer foreign key from column name patterns
                else:
                    fk_info = _infer_foreign_key_from_column_name(col_name)
                    if fk_info:
                        column_info["foreign_key"] = True
                        relationships.append({
                            "type": "foreign_key", "source_column": col_name, "target_table": fk_info["target_table"], "target_column": fk_info["target_column"], "inferred_from_name": True
                        })

                # Check if this column is a primary key
                if col.get("is_primary_key") or col.get("primary_key"):
                    primary_keys.append(column_info["name"])
                    column_info["primary_key"] = True

                # Add blob metadata if this is a blob column
                if col_type.lower() == "blob":
                    # Determine blob usage based on column name
                    blob_usage = _determine_blob_usage(col_name)
                    column_info["blob_metadata"] = {
                        "usage": blob_usage, "display_widget": f"{_to_pascal_case(col_name)}BlobDisplay", "mime_type": _guess_mime_type(blob_usage, col_name), "expected_size": col.get("blob_size", "medium")  # small, medium, large
                    }

                columns.append(column_info)

        # Extract SQL statements
        for sql_type in ["retrieve_sql", "update_sql", "insert_sql", "delete_sql"]:
            if ast_data.get(sql_type):
                sql_info[sql_type] = ast_data[sql_type]

        # Extract foreign keys from SQL
        if sql_info.get("retrieve_sql"):
            try:
                # Parse the SQL to get AST
                sql_parser = SQLParser()
                parsed_sql = sql_parser.parse(sql_info["retrieve_sql"])

                if parsed_sql and isinstance(parsed_sql, list) and len(parsed_sql) > 0:
                    sql_stmt = parsed_sql[0]

                    # Use RelationshipExtractor to find relationships
                    rel_extractor = RelationshipExtractor()
                    sql_relationships = rel_extractor.extract_from_select(sql_stmt)

                    # Convert relationships to our format
                    for rel in sql_relationships:
                        # Extract column mappings from the relationship
                        for mapping in rel.column_mappings:
                            # Check if we already have this relationship from explicit foreign keys
                            existing = False
                            for existing_rel in relationships:
                                if (existing_rel.get("source_column") == mapping.source_column and
                                    existing_rel.get("target_table") == mapping.target_table):
                                    existing = True
                                    break

                            if not existing:
                                relationships.append({
                                    "type": "foreign_key", "source_table": mapping.source_table, "source_column": mapping.source_column, "target_table": mapping.target_table, "target_column": mapping.target_column, "join_type": rel.join_type.value, "inferred_from_sql": True
                                })

                    logger.debug("Extracted %s relationships from SQL", len(sql_relationships))

            except Exception as e:
                logger.warning("Failed to extract relationships from SQL: %s", e)

        # Extract table information with primary keys
        table_info = ast_data.get("table", {})
        if isinstance(table_info, dict):
            # Use table name if available
            table_name = table_info.get("name", "")

            # Extract primary keys from table definition
            if "primary_key" in table_info:
                pk = table_info["primary_key"]
                if isinstance(pk, list):
                    primary_keys.extend(pk)
                elif isinstance(pk, str):
                    primary_keys.append(pk)
        else:
            # Try to parse from SQL
            table_name = extract_table_from_sql(sql_info.get("retrieve_sql", ""))

        # Extract nested DataWindow relationships
        if ast_data.get("datawindow_type") == "nested" or "nested_datawindow" in ast_data:
            nested_info = ast_data.get("nested_datawindow", {})
            if nested_info:
                relationships.append({
                    "type": "nested", "parent_columns": nested_info.get("parent_columns", []), "child_datawindow": nested_info.get("child_datawindow"), "linkage_columns": nested_info.get("linkage_columns", []), })

        # Extract any explicit relationships in the AST
        if "relationships" in ast_data:
            for rel in ast_data["relationships"]:
                relationships.append({
                    "type": rel.get("type", "unknown"), "source_table": rel.get("source_table", table_name), "source_column": rel.get("source_column"), "target_table": rel.get("target_table"), "target_column": rel.get("target_column"), "join_type": rel.get("join_type", "inner"), })

        # Enhanced cross-table column analysis
        if sql_info.get("retrieve_sql") and len(columns) > 0:
            try:
                # Extract all tables from SQL
                tables_in_sql = _extract_tables_from_sql(sql_info["retrieve_sql"])

                # For each column, check if it references another table
                for col in columns:
                    col_name = col["name"]

                    # Skip if already has a foreign key
                    if col.get("foreign_key"):
                        continue

                    # Check against each table name
                    for table in tables_in_sql:
                        # Skip self-references unless it's a parent_id pattern
                        if table == table_name and not col_name.lower().startswith("parent"):
                            continue

                        # Check if column name matches table pattern
                        if (_column_matches_table(col_name, table) and 
                            not any(r["source_column"] == col_name for r in relationships)):

                            relationships.append({
                                "type": "foreign_key", "source_table": table_name, "source_column": col_name, "target_table": table, "target_column": "id", # Default assumption
                                "inferred_from_column_pattern": True
                            })
                            logger.debug("Inferred FK: %s.%s -> %s.id", table_name, col_name, table)

            except Exception as e:
                logger.debug("Cross-table analysis failed: %s", e)

        return {
            "columns": columns, "relationships": relationships, # Now includes extracted relationships
            "sql": sql_info, "table_name": table_name, "primary_keys": list(set(primary_keys)), # Deduplicated primary keys
        }

    # Recursively search for DataWindow nodes
    for value in ast_data.values():
        if isinstance(value, dict):
            result = extract_datawindow_from_ast(value)
            if result:
                return result
        elif isinstance(value, list):
            for item in value:
                if isinstance(item, dict):
                    result = extract_datawindow_from_ast(item)
                    if result:
                        return result

    return None


def extract_table_from_sql(sql: str) -> str:








    """Extract table name from SQL statement.

    Args:
        sql: SQL statement

    Returns:
        Table name or empty string
    """
    if not sql:
        return ""

    # Simple extraction - look for FROM clause
    sql_upper = sql.upper()
    from_idx = sql_upper.find("FROM")
    if from_idx != -1:
        # Extract text after FROM
        after_from = sql[from_idx + 4 :].strip()
        # Get first word (table name)
        parts = after_from.split()
        if parts:
            return parts[0].strip('"').strip("'").strip("`")

    return ""


def _extract_tables_from_sql(sql: str) -> list[str]:








    """Extract all table names from SQL statement.

    Args:
        sql: SQL statement

    Returns:
        List of table names found in the SQL
    """
    if not sql:
        return []

    tables = []
    sql_upper = sql.upper()

    # Extract from FROM clause
    from_match = re.search(r'\bFROM\s+([^WHERE|JOIN|GROUP|ORDER|HAVING]+)', sql_upper)
    if from_match:
        from_text = from_match.group(1)
        # Extract table names and aliases
        table_parts = from_text.split(', ')
        for part in table_parts:
            # Handle "table alias" or just "table"
            words = part.strip().split()
            if words:
                table_name = sql[from_match.start(1):from_match.end(1)].split(', ')[table_parts.index(part)].strip().split()[0]
                tables.append(table_name.strip('"').strip("'").strip("`").lower())

    # Extract from JOIN clauses
    join_pattern = r'\b(?:INNER|LEFT|RIGHT|FULL|CROSS)?\s*JOIN\s+(\w+)'
    join_matches = re.finditer(join_pattern, sql, re.IGNORECASE)
    for match in join_matches:
        table_name = match.group(1)
        tables.append(table_name.strip('"').strip("'").strip("`").lower())

    # Remove duplicates and return
    return list(set(tables))


def _column_matches_table(column_name: str, table_name: str) -> bool:








    """Check if a column name suggests a foreign key to the given table.

    Args:
        column_name: Name of the column
        table_name: Name of the potential target table

    Returns:
        True if column name suggests FK to table
    """
    col_lower = column_name.lower()
    table_lower = table_name.lower()

    # Direct patterns
    patterns = [
        f"{table_lower}_id", f"{table_lower}_code", f"{table_lower}_key", f"{table_lower}id", f"fk_{table_lower}", f"{table_lower}_fk", ]

    # Check direct patterns
    if col_lower in patterns:
        return True

    # Check if table is singular and column uses plural (or vice versa)
    if table_lower.endswith('s'):
        # Table is plural, check singular
        singular = table_lower[:-1]
        if col_lower in [f"{singular}_id", f"{singular}id", f"{singular}_code"]:
            return True
    else:
        # Table is singular, check plural
        plural = table_lower + 's'
        if col_lower in [f"{plural}_id", f"{plural}id", f"{plural}_code"]:
            return True

    # Check for table abbreviations
    table_abbrevs = {
        'customer': ['cust'], 'product': ['prod'], 'employee': ['emp'], 'department': ['dept'], 'order': ['ord'], 'category': ['cat'], 'address': ['addr'], 'account': ['acct'], 'invoice': ['inv'], 'document': ['doc'], }

    # Check if column matches abbreviation
    for full_name, abbrevs in table_abbrevs.items():
        if table_lower == full_name:
            for abbrev in abbrevs:
                if col_lower in [f"{abbrev}_id", f"{abbrev}id", f"{abbrev}_code"]:
                    return True

    return False


def _determine_blob_usage(column_name: str) -> str:








    """Determine the usage type of a blob column based on name.

    Args:
        column_name: Name of the column

    Returns:
        Usage type: 'image', 'document', 'data'
    """
    name_lower = column_name.lower()

    # Check for image-related names
    image_keywords = ['photo', 'picture', 'image', 'icon', 'logo', 'avatar', 'thumbnail', 'screenshot', 'jpg', 'jpeg', 'png', 'gif']
    if any(keyword in name_lower for keyword in image_keywords):
        return 'image'

    # Check for document-related names
    doc_keywords = ['document', 'doc', 'pdf', 'file', 'attachment', 'report', 'excel', 'word', 'spreadsheet', 'presentation']
    if any(keyword in name_lower for keyword in doc_keywords):
        return 'document'

    # Default to generic data
    return 'data'


def _to_pascal_case(name: str) -> str:








    """Convert name to PascalCase."""
    # Remove common prefixes
    if name.startswith("d_"):
        name = name[2:]
    if name.startswith("dw_"):
        name = name[3:]

    # Convert to PascalCase
    parts = name.split("_")
    return "".join(p.capitalize() for p in parts)


def _guess_mime_type(usage: str, column_name: str) -> str:








    """Guess MIME type based on usage and column name.

    Args:
        usage: Usage type ('image', 'document', 'data')
        column_name: Name of the column

    Returns:
        Guessed MIME type
    """
    name_lower = column_name.lower()

    if usage == 'image':
        if 'jpg' in name_lower or 'jpeg' in name_lower:
            return 'image/jpeg'
        elif 'png' in name_lower:
            return 'image/png'
        elif 'gif' in name_lower:
            return 'image/gif'
        elif 'bmp' in name_lower:
            return 'image/bmp'
        else:
            return 'image/jpeg'  # Default for images
    elif usage == 'document':
        if 'pdf' in name_lower:
            return 'application/pdf'
        elif 'excel' in name_lower or 'xls' in name_lower:
            return 'application/vnd.ms-excel'
        elif 'word' in name_lower or 'doc' in name_lower:
            return 'application/msword'
        else:
            return 'application/octet-stream'
    else:
        return 'application/octet-stream'


def extract_methods_from_ast(ast_data: dict) -> list[dict]:








    """Extract method information from parsed AST.

    Args:
        ast_data: Parsed AST data from JSON

    Returns:
        List of method dictionaries
    """
    methods = []

    if not isinstance(ast_data, dict):
        return methods

    # Look for function/event nodes
    if ast_data.get("node_type") in ["Function", "Event", "Method"] or ast_data.get(
        "type"
    ) in ["function", "event", "method"]:
        method_info = {
            "name": ast_data.get("name", ""), "return_type": ast_data.get("return_type", "void"), "visibility": ast_data.get("visibility", "public"), "parameters": [], }

        # Extract parameters
        if "arguments" in ast_data:
            args = ast_data["arguments"]
            if isinstance(args, dict) and "arguments" in args:
                args = args["arguments"]

            for arg in args if isinstance(args, list) else []:
                param = {
                    "name": arg.get("name", ""), "type": arg.get("type", "any"), "is_reference": arg.get("is_reference", False), "is_readonly": arg.get("is_readonly", False), "default_value": arg.get("default_value"), }
                method_info["parameters"].append(param)

        methods.append(method_info)

    # Recursively search for method nodes
    for value in ast_data.values():
        if isinstance(value, dict):
            methods.extend(extract_methods_from_ast(value))
        elif isinstance(value, list):
            for item in value:
                if isinstance(item, dict):
                    methods.extend(extract_methods_from_ast(item))

    return methods


def parse_decompiled_functions(fun_file: Path) -> dict[str, str]:








    """Parse decompiled function file to extract implementations.

    Args:
        fun_file: Path to .fun file

    Returns:
        Dictionary mapping function names to implementations
    """
    functions = {}

    try:
        with open(fun_file) as f:
            content = f.read()

        # Simple parsing - look for function boundaries
        lines = content.split("\n")
        current_function = None
        current_impl = []

        for line in lines:
            # Check for function start
            if line.strip().startswith("function ") or line.strip().startswith(
                "subroutine "
            ):
                # Save previous function
                if current_function:
                    functions[current_function] = "\n".join(current_impl)

                # Start new function
                parts = line.strip().split()
                if len(parts) >= 2:
                    current_function = parts[1].split("(")[0]
                    current_impl = [line]
            elif line.strip().startswith("end function") or line.strip().startswith(
                "end subroutine"
            ):
                # End current function
                if current_function:
                    current_impl.append(line)
                    functions[current_function] = "\n".join(current_impl)
                    current_function = None
                    current_impl = []
            elif current_function:
                # Add to current function
                current_impl.append(line)

        # Save last function if any
        if current_function:
            functions[current_function] = "\n".join(current_impl)

    except Exception as e:
        logger.warning("Failed to parse %s: %s", fun_file, e)

    return functions


def extract_window_from_ast(ast_data: dict) -> dict:








    """Extract window information from parsed AST.

    Args:
        ast_data: Parsed AST data from JSON

    Returns:
        Dictionary with window parameters, controllers, and services
    """
    window_info = {
        "params": {}, "controllers": [], "services": [], }

    if not isinstance(ast_data, dict):
        return window_info

    # Look for window node
    if ast_data.get("node_type") == "Window" or ast_data.get("type") == "window":
        # Extract window parameters (instance variables)
        if "variables" in ast_data:
            for var in ast_data["variables"]:
                if var.get("visibility") == "public":
                    window_info["params"][var.get("name", "")] = {
                        "type": var.get("type", "any"), "default": var.get("initial_value"), }

        # Extract events that act as controllers
        if "events" in ast_data:
            for event in ast_data["events"]:
                window_info["controllers"].append(
                    {
                        "name": event.get("name", ""), "type": "event", }
                )

        # Extract referenced services (functions)
        methods = extract_methods_from_ast(ast_data)
        for method in methods:
            if method.get("visibility") == "public":
                window_info["services"].append(method["name"])

    # Recursively search
    for value in ast_data.values():
        if isinstance(value, dict):
            result = extract_window_from_ast(value)
            # Merge results
            window_info["params"].update(result["params"])
            window_info["controllers"].extend(result["controllers"])
            window_info["services"].extend(result["services"])
        elif isinstance(value, list):
            for item in value:
                if isinstance(item, dict):
                    result = extract_window_from_ast(item)
                    window_info["params"].update(result["params"])
                    window_info["controllers"].extend(result["controllers"])
                    window_info["services"].extend(result["services"])

    # Remove duplicates
    window_info["controllers"] = list(
        {c["name"]: c for c in window_info["controllers"]}.values()
    )
    window_info["services"] = list(set(window_info["services"]))

    return window_info


def extract_widget_from_ast(ast_data: dict) -> dict:








    """Extract widget information from parsed AST.

    Args:
        ast_data: Parsed AST data from JSON

    Returns:
        Dictionary with widget properties, state, and children
    """
    widget_info = {
        "props": {}, "is_stateful": False, "children": [], }

    if not isinstance(ast_data, dict):
        return widget_info

    # Look for user object node
    if (
        ast_data.get("node_type") == "UserObject"
        or ast_data.get("type") == "userobject"
    ):
        # Extract properties (public variables)
        if "variables" in ast_data:
            for var in ast_data["variables"]:
                if var.get("visibility") == "public":
                    widget_info["props"][var.get("name", "")] = {
                        "type": var.get("type", "any"), "default": var.get("initial_value"), }

        # Check if stateful (has instance variables or events)
        if "variables" in ast_data or "events" in ast_data:
            widget_info["is_stateful"] = True

        # Extract child controls
        if "controls" in ast_data:
            for control in ast_data["controls"]:
                widget_info["children"].append(
                    {
                        "type": control.get("type", "unknown"), "name": control.get("name", ""), "properties": control.get("properties", {}), }
                )

    # Recursively search
    for value in ast_data.values():
        if isinstance(value, dict):
            result = extract_widget_from_ast(value)
            # Merge results
            widget_info["props"].update(result["props"])
            widget_info["is_stateful"] = (
                widget_info["is_stateful"] or result["is_stateful"]
            )
            widget_info["children"].extend(result["children"])
        elif isinstance(value, list):
            for item in value:
                if isinstance(item, dict):
                    result = extract_widget_from_ast(item)
                    widget_info["props"].update(result["props"])
                    widget_info["is_stateful"] = (
                        widget_info["is_stateful"] or result["is_stateful"]
                    )
                    widget_info["children"].extend(result["children"])

    return widget_info


class ModelGenerator(CodeGenerator):
    """Generate SQLModel models from PowerBuilder schema."""

    def __init__(self, template_dir: str, output_dir: str, validate_templates: bool = True) -> None:




        """Initialize model generator.

        Args:
            template_dir: Directory containing templates
            output_dir: Directory for generated code
            validate_templates: Whether to validate templates before rendering
        """
        super().__init__(template_dir, output_dir, validate_templates)

    def generate_model(
        self, table_name: str, columns: list[dict[str, Any]], relationships: list[dict[str, Any]] | None = None, ) -> None:




        """Generate a SQLModel model for a table.

        Args:
            table_name: Name of the table
            columns: List of column definitions
            relationships: Optional list of relationship definitions
        """
        context = {
            "table_name": table_name, "columns": columns, "relationships": relationships or [], }
        content = self.render_template("sqlmodel_model.jinja2", context)
        self.write_file(f"models/{table_name.lower()}.py", content)


class ServiceGenerator(CodeGenerator):
    """Generate service layer from PowerBuilder business logic."""

    def __init__(self, template_dir: str, output_dir: str, validate_templates: bool = True) -> None:




        """Initialize service generator.

        Args:
            template_dir: Directory containing templates
            output_dir: Directory for generated code
            validate_templates: Whether to validate templates before rendering
        """
        super().__init__(template_dir, output_dir, validate_templates)

    def generate_service(self, name: str, methods: list[dict[str, Any]]) -> None:




        """Generate a service class.

        Args:
            name: Service name
            methods: List of method definitions
        """
        context = {
            "service_name": name, "methods": methods, }
        content = self.render_template("service.jinja2", context)
        self.write_file(f"services/{name.lower()}_service.py", content)


class FlutterGenerator(CodeGenerator):
    """Generate Flutter widgets and screens from PowerBuilder UI."""

    def __init__(self, template_dir: str, output_dir: str, validate_templates: bool = True) -> None:




        """Initialize Flutter generator.

        Args:
            template_dir: Directory containing templates
            output_dir: Directory for generated code
            validate_templates: Whether to validate templates before rendering
        """
        super().__init__(template_dir, output_dir, validate_templates)
        self.layout_converter = None  # Will be set by coordinator
        self.ui_converter = None  # Will be set by coordinator
        self.method_body_converter = MethodBodyConverter()
        self.event_wiring_system = EventWiringSystem()

    def generate_widget(
        self, name: str, props: list[dict[str, Any]], is_stateful: bool = False, children: list[dict[str, Any]] | None = None, ) -> None:




        """Generate a Flutter widget.

        Args:
            name: Widget name
            props: List of widget properties
            is_stateful: Whether the widget should be stateful
            children: Optional list of child widgets
        """
        # Determine if glassmorphism should be used
        use_glassmorphism = (
            hasattr(self, 'ui_converter') and 
            self.ui_converter and 
            self.ui_converter.design_system.design_theme == 'liquid_glass'
        )

        context = {
            "widget": {
                "name": name, "props": props, "has_state": is_stateful, "children": children or [], "use_glassmorphism": use_glassmorphism, "controls": [], # For compatibility with template
                "state": [], "controllers": [], "methods": [], "imports": []
            }
        }
        content = self.render_template("widget.dart.jinja2", context)
        self.write_file(f"widgets/{name.lower()}.dart", content)

    def generate_screen(
        self, name: str, route_name: str, params: list[dict[str, Any]] | None = None, controllers: list[dict[str, Any]] | None = None, services: list[str] | None = None, ) -> None:




        """Generate a Flutter screen.

        Args:
            name: Screen name
            route_name: Route name for navigation
            params: Optional list of screen parameters
            controllers: Optional list of controllers (TextEditingController, etc.)
            services: Optional list of service dependencies
        """
        context = {
            "screen": {
                "name": name, "route_name": route_name, "description": f"Screen for {name}", "params": params or [], "controllers": controllers or [], "services": services or [], "imports": [], "state": [], "methods": [], "app_bar": {"actions": []}, "body": "Center(child: Text('Generated screen'))", "title": name
            }
        }
        content = self.render_template("screen.dart.jinja2", context)
        self.write_file(f"screens/{name.lower()}_screen.dart", content)

    def generate_model(
        self, name: str, fields: list[dict[str, Any]], methods: list[dict[str, Any]] | None = None, ) -> None:




        """Generate a Flutter data model.

        Args:
            name: Model name
            fields: List of model fields
            methods: Optional list of model methods
        """
        context = {
            "model_name": name, "fields": fields, "methods": methods or [], }
        content = self.render_template("model.dart.jinja2", context)
        self.write_file(f"models/{name.lower()}.dart", content)

    def generate_datawindow_widget(
        self, name: str, columns: list[dict[str, Any]], data_source: str, presentation_style: str = "grid", row_type: str = "Map<String, dynamic>", ) -> None:




        """Generate a Flutter widget for PowerBuilder DataWindow.

        Args:
            name: Widget name
            columns: List of DataWindow columns
            data_source: Data source for the DataWindow
            presentation_style: DataWindow presentation style (grid, freeform, etc.)
            row_type: Dart type for row data
        """
        context = {
            "datawindow": {
                "name": name, "columns": columns, "presentation_style": presentation_style, "row_type": row_type, "imports": []
            }, "widget_name": name, "columns": columns, "data_source": data_source, }
        content = self.render_template("datawindow_widget.dart.jinja2", context)
        self.write_file(f"widgets/{name.lower()}_datawindow.dart", content)

    def generate_screen_from_model(self, window_model: dict) -> None:




        """Generate a Flutter screen from a converted window model.

        Args:
            window_model: Window model from converters containing controls, events, etc.
        """
        # Store current window context for method body conversion
        self._current_window_controls = {
            control.get("name"): control 
            for control in window_model.get("controls", [])
        }
        self._current_window_variables = {
            var.get("name"): var 
            for var in window_model.get("variables", [])
        }

        # Transform the window model into the format expected by the template
        parameters = []
        controllers = []
        state_vars = []

        # Extract parameters from public variables
        for var in window_model.get("variables", []):
            if var.get("visibility") == "public" or var.get("access") == "public":
                parameters.append({
                    "name": var.get("name"), "type": var.get("dart_type", "dynamic"), "required": True, "default": var.get("initial_value")
                })
            else:
                # Private variables become state
                state_vars.append({
                    "name": var.get("name"), "type": var.get("dart_type", "dynamic"), "nullable": True, "initial": var.get("initial_value")
                })

        # Extract controllers from controls that need them
        for control in window_model.get("controls", []):
            flutter_widget = control.get("flutter_widget", {})
            if flutter_widget.get("requires_controller"):
                controllers.append({
                    "name": f"{control['name']}Controller", "type": flutter_widget.get("controller_type", "TextEditingController")
                })

        # Wire up events
        event_wiring_result = self.event_wiring_system.wire_events(window_model)
        wirings = event_wiring_result.get("wirings", [])
        focus_nodes = event_wiring_result.get("focus_nodes", [])
        gesture_detectors = event_wiring_result.get("gesture_detectors", [])
        wired_event_handlers = event_wiring_result.get("event_handlers", [])
        event_state_vars = event_wiring_result.get("state_variables", [])

        # Add event state variables to state
        state_vars.extend(event_state_vars)

        # Build the screen body from controls with event wiring
        body_content = self._build_screen_body(window_model.get("controls", []), wirings)

        # Create screen context for template
        context = {
            "screen": {
                "name": window_model.get("name", "UnknownScreen"), "route_name": window_model.get('name', 'unknown').lower(), "title": window_model.get("title", window_model.get("name", "Unknown")), "description": f"Generated from PowerBuilder window {window_model.get('name', 'Unknown')}", "params": parameters, "state": state_vars, "controllers": controllers, "services": self._extract_service_dependencies(window_model), "app_bar": {
                    "actions": self._extract_toolbar_actions(window_model.get("controls", []))
                }, "body": body_content, "imports": [], "methods": self._convert_methods(window_model.get("methods", [])) + wired_event_handlers, "load_data": self._extract_load_data_code(window_model), "init_code": self._extract_init_code(window_model, focus_nodes), "dispose_code": self._extract_dispose_code(focus_nodes), "focus_nodes": focus_nodes, "event_wirings": wirings
            }
        }

        # Generate the screen file with direct template rendering (bypass validation)
        try:
            template = self.env.get_template("screen.dart.jinja2")
            content = template.render(**context)
            self.write_file(f"screens/{window_model.get('name', 'unknown').lower()}_screen.dart", content)
        except Exception as e:
            logger.debug("Exception caught: %s", e)
            # If template rendering fails, log error and re-raise
            logger.error(f"Failed to render screen template: {e}")
            raise
        finally:
            # Clear window context
            self._current_window_controls = {}
            self._current_window_variables = {}

    def _build_screen_body(self, controls: list, wirings: list = None) -> str:




        """Build the Flutter widget tree from PowerBuilder controls with event wiring.

        Args:
            controls: List of control dictionaries
            wirings: List of EventWiring objects
        """
        if not controls:
            return "Center(child: Text('No controls defined'))"

        # Pass wirings to layout converter if available
        if hasattr(self, 'layout_converter') and self.layout_converter:
            # Ensure each control has glassmorphism properties if needed
            if hasattr(self, 'ui_converter') and self.ui_converter:
                for control in controls:
                    if 'flutter_widget' in control and control['flutter_widget'].get('needs_glass_wrapper'):
                        # Ensure glassmorphic properties are set
                        if 'glassmorphic' not in control['flutter_widget']:
                            control['flutter_widget']['glassmorphic'] = True

            # Pass wirings to layout converter
            if wirings and hasattr(self.layout_converter, 'set_event_wirings'):
                self.layout_converter.set_event_wirings(wirings)

            return self.layout_converter.convert_layout(controls)
        else:
            # Fallback to simple column layout with event wiring
            logger.warning("Layout converter not available, using simple column layout")
            widget_code = "        Column(\n          children: [\n"

            if wirings and self.event_wiring_system:
                # Generate controls with events
                for control in controls:
                    control_wirings = [w for w in wirings if w.control_name == control.get("name", "")]
                    if control_wirings:
                        widget_code += f"            {self.event_wiring_system.generate_control_with_events(control, control_wirings)}, \n"
                    else:
                        widget_code += f"            Container(), // {control.get('name', 'unknown')}\n"
            else:
                for control in controls:
                    widget_code += f"            Container(), // {control.get('name', 'unknown')}\n"

            widget_code += "          ], \n        )"
            return widget_code

    def _extract_toolbar_actions(self, controls: list) -> list:




        """Extract toolbar actions from controls that should appear in app bar.

        Args:
            controls: List of control dictionaries

        Returns:
            List of toolbar actions
        """
        actions = []

        for control in controls:
            control_type = control.get("type", "").lower()
            control_name = control.get("name", "")

            # Check for toolbar buttons or menu-like controls
            if control_type in ["commandbutton", "picturebutton", "picture"]:
                # Check if it's positioned at the top of the window (toolbar area)
                y_pos = control.get("y", 0)
                if y_pos < 100:  # Likely in toolbar area
                    # Determine icon based on control name or text
                    icon = self._determine_action_icon(control)
                    actions.append({
                        "icon": icon, "tooltip": control.get("text", control_name), "onPressed": f"_{control_name}_clicked"
                    })

            # Check for specific action patterns in control names
            elif any(action in control_name.lower() for action in ["save", "print", "refresh", "search", "filter", "export"]):
                icon = self._determine_action_icon(control)
                actions.append({
                    "icon": icon, "tooltip": control.get("text", control_name), "onPressed": f"_{control_name}_clicked"
                })

        return actions

    def _determine_action_icon(self, control: dict) -> str:




        """Determine appropriate Flutter icon for a control.

        Args:
            control: Control dictionary

        Returns:
            Flutter Icons class reference
        """
        control_name = control.get("name", "").lower()
        control_text = control.get("text", "").lower()

        # Map common action names to Flutter icons
        icon_map = {
            "save": "Icons.save", "print": "Icons.print", "refresh": "Icons.refresh", "search": "Icons.search", "filter": "Icons.filter_list", "export": "Icons.file_download", "import": "Icons.file_upload", "add": "Icons.add", "new": "Icons.add_circle", "delete": "Icons.delete", "remove": "Icons.remove", "edit": "Icons.edit", "settings": "Icons.settings", "help": "Icons.help", "info": "Icons.info", "close": "Icons.close", "exit": "Icons.exit_to_app"
        }

        # Check control name and text for keywords
        for keyword, icon in icon_map.items():
            if keyword in control_name or keyword in control_text:
                return icon

        # Default icon for unknown actions
        return "Icons.more_vert"

    def _extract_service_dependencies(self, window_model: dict) -> list:




        """Extract service dependencies from window model.

        Args:
            window_model: The window model dictionary

        Returns:
            List of service dependencies
        """
        services = []

        # Check for database operations in methods
        has_db_operations = False
        for method in window_model.get("methods", []):
            if method.get("body"):
                body_lower = str(method["body"]).lower()
                if any(db_op in body_lower for db_op in ["select", "insert", "update", "delete", "sqlca", "transaction"]):
                    has_db_operations = True
                    break

        # Add database service if needed
        if has_db_operations:
            services.append({
                "name": "databaseService", "type": "DatabaseService", "import": "../services/database_service.dart"
            })

        # Check for datawindow operations
        for control in window_model.get("controls", []):
            if control.get("type", "").lower() == "datawindow":
                services.append({
                    "name": "dataWindowService", "type": "DataWindowService", "import": "../services/datawindow_service.dart"
                })
                break

        # Check for file operations
        for method in window_model.get("methods", []):
            if method.get("body"):
                body_lower = str(method["body"]).lower()
                if any(file_op in body_lower for file_op in ["fileopen", "fileclose", "fileread", "filewrite"]):
                    services.append({
                        "name": "fileService", "type": "FileService", "import": "../services/file_service.dart"
                    })
                    break

        # Check for authentication needs (common patterns)
        if window_model.get("name", "").lower() in ["login", "w_login", "w_authentication"]:
            services.append({
                "name": "authService", "type": "AuthenticationService", "import": "../services/auth_service.dart"
            })

        return services

    def _convert_methods(self, methods: list) -> list:




        """Convert PowerBuilder methods to Dart methods."""
        dart_methods = []
        for method in methods:
            # Extract return type
            pb_return_type = method.get("return_type")
            if pb_return_type:
                return_type = self._convert_pb_type_to_dart(pb_return_type)
            else:
                return_type = "void"  # Default to void for methods without explicit return type

            # Extract parameters
            params = []
            for param in method.get("parameters", []):
                param_type = self._convert_pb_type_to_dart(param.get("type", "any"))
                param_name = param.get("name", "param")
                params.append(f"{param_type} {param_name}")
            param_str = ", ".join(params)

            # Check if method is async (has database or file operations)
            body = method.get("body", "")
            is_async = False
            if isinstance(body, str):
                body_lower = body.lower()
                is_async = any(async_op in body_lower for async_op in 
                             ["select", "insert", "update", "delete", "fileopen", "fileread", "http"])

            dart_methods.append({
                "name": method.get("name", "unknown"), "return_type": return_type, "params": param_str, "is_async": is_async, "body": self._convert_method_body(method)
            })
        return dart_methods

    def _convert_pb_type_to_dart(self, pb_type: str) -> str:




        """Convert PowerBuilder type to Dart type.

        Args:
            pb_type: PowerBuilder type string

        Returns:
            Dart type string
        """
        if not pb_type:
            return "dynamic"

        pb_type_lower = pb_type.lower()

        type_map = {
            "integer": "int", "long": "int", "decimal": "double", "real": "double", "double": "double", "string": "String", "char": "String", "boolean": "bool", "bool": "bool", "date": "DateTime", "datetime": "DateTime", "time": "DateTime", "blob": "Uint8List", "any": "dynamic"
        }

        return type_map.get(pb_type_lower, "dynamic")

    def _convert_method_body(self, method: dict) -> str:




        """Convert method body from PowerBuilder to Dart.

        Args:
            method: Method dictionary

        Returns:
            Dart method body
        """
        body = method.get("body", "")

        if not body:
            return f"// TODO: Implement {method.get('name', 'unknown')}"

        # If body is already a string of Dart code, return it
        if isinstance(body, str) and body.strip().startswith("//"):
            return body

        # Use the method body converter
        method_name = method.get("name", "unknown")
        parameters = method.get("parameters", [])
        return_type = method.get("return_type")

        # Build context with available controls and variables
        context = {
            "controls": self._current_window_controls if hasattr(self, "_current_window_controls") else {}, "variables": self._current_window_variables if hasattr(self, "_current_window_variables") else {}
        }

        # Convert the method body
        result = self.method_body_converter.convert_method_body(
            pb_code=body, method_name=method_name, parameters=parameters, return_type=return_type, context=context
        )

        # Return the Dart code
        return result.get("dart", f"// TODO: Implement {method_name}")

    def _extract_load_data_code(self, window_model: dict) -> str | None:




        """Extract data loading code from window open event.

        Args:
            window_model: Window model dictionary

        Returns:
            Dart code for loading data or None
        """
        # Look for window open event
        for event in window_model.get("events", []):
            if event.get("name", "").lower() in ["open", "window_open", "opened"]:
                # Check if event has database or datawindow operations
                event_body = event.get("body", "")
                if event_body:
                    # Simple patterns to detect data loading
                    if any(pattern in str(event_body).lower() for pattern in 
                          ["retrieve", "select", "datawindow", "settransobject"]):
                        # Return a basic data loading implementation
                        return """await Future.delayed(Duration(milliseconds: 100))
    try {
      // Load data from database
      await _loadData();
    } catch (e) {
      // Handle loading error
      _showError('Failed to load data: $e');
    }"""
        return None

    def _extract_init_code(self, window_model: dict) -> str | None:




        """Extract initialization code from constructor or create event.

        Args:
            window_model: Window model dictionary

        Returns:
            Dart initialization code or None
        """
        init_code_parts = []

        # Check for constructor or create event
        for event in window_model.get("events", []):
            if event.get("name", "").lower() in ["constructor", "create", "init"]:
                event_body = event.get("body", "")
                if event_body:
                    init_code_parts.append(f"// From {event['name']} event")
                    init_code_parts.append("// Original PowerBuilder code:")
                    init_code_parts.append(f"// {event_body}")

        # Check for initial values in instance variables
        for var in window_model.get("variables", []):
            if var.get("scope") == "instance" and var.get("initial_value"):
                var_name = var.get("name", "unknown")
                init_value = var.get("initial_value")
                dart_type = self._convert_pb_type_to_dart(var.get("type", "any"))

                # Generate initialization code
                if dart_type in ["String", "int", "double", "bool"]:
                    init_code_parts.append(f"{var_name} = {init_value};")
                else:
                    init_code_parts.append(f"// Initialize {var_name}")

        # Add controller initialization if needed
        for control in window_model.get("controls", []):
            if control.get("flutter_widget", {}).get("requires_controller"):
                control_name = control.get("name", "unknown")
                controller_type = control.get("flutter_widget", {}).get("controller_type", "TextEditingController")
                init_code_parts.append(f"{control_name}Controller = {controller_type}();")

        if init_code_parts:
            return "\n    ".join(init_code_parts)
        return None

    def generate_project_structure(self, app_info: dict) -> None:




        """Generate the complete Flutter project structure.

        Args:
            app_info: Application information including name, description, features
        """
        # Generate pubspec.yaml
        pubspec_context = {
            "app": {
                "name": app_info.get("name", "pb_app"),
                "description": app_info.get("description", "Flutter app converted from PowerBuilder"),
                "has_database": app_info.get("has_database", False),
                "has_charts": app_info.get("has_charts", False),
                "has_file_operations": app_info.get("has_file_operations", False),
                "has_printing": app_info.get("has_printing", False),
                "assets": app_info.get("assets", [])
            },
            "generate_tests": app_info.get("generate_tests", False)
        }
        content = self.render_template("pubspec.yaml.jinja2", pubspec_context)
        self.write_file("pubspec.yaml", content)

        # Generate design system
        design_context = {
            "app_name": app_info.get("name", "App")
        }
        content = self.render_template("design_system.dart.jinja2", design_context)
        self.write_file("lib/theme/design_system.dart", content)

        # Generate main.dart
        main_context = {
            "app": app_info
        }
        content = self.render_template("main.dart.jinja2", main_context)
        self.write_file("lib/main.dart", content)

        # Create directory structure
        directories = [
            "lib/screens",
            "lib/widgets", 
            "lib/models",
            "lib/services",
            "lib/theme",
            "lib/core",
            "assets/images",
            "assets/fonts"
        ]

        for directory in directories:
            dir_path = self.output_dir / directory
            dir_path.mkdir(parents=True, exist_ok=True)

        logger.info("Generated Flutter project structure")


def generate_models(parsed_dir: str = "data/output/current/parsed") -> None:








    """Generate all database models from parsed PowerBuilder files.

    Args:
        parsed_dir: Directory containing parsed AST files (default: output/parsed)
    """
    try:
        import json
        from pathlib import Path

        generator = ModelGenerator("templates", "output/backend")
        parsed_path = Path(parsed_dir)

        # Read parsed summary if available
        summary_file = parsed_path / "parsed_summary.json"
        if summary_file.exists():
            with open(summary_file) as f:
                summary = json.load(f)
                logger.info("Found parsed data from %s", summary['parsed_at'])

        # Find all parsed DataWindow files (.srd)
        datawindow_files = list(parsed_path.rglob("*.srd.ast.json"))
        logger.info("Found %s DataWindow files", len(datawindow_files))

        # Extract table information from DataWindows
        tables = {}
        for dw_file in datawindow_files:
            try:
                with open(dw_file) as f:
                    ast_data = json.load(f)

                # Extract table schema from AST
                table_name = dw_file.stem.replace(".srd.ast", "")
                if table_name not in tables:
                    # Extract DataWindow information
                    dw_data = extract_datawindow_from_ast(ast_data)
                    if dw_data:
                        tables[table_name] = {
                            "name": table_name,
                            "columns": dw_data.get("columns", []),
                            "relationships": dw_data.get("relationships", []),
                            "sql": dw_data.get("sql", {}),
                        }
            except Exception as e:
                logger.warning("Failed to process %s: %s", dw_file, e)

        # Generate models for each table
        for table in tables.values():
            generator.generate_model(
                table["name"],
                table["columns"],
                table.get("relationships"),
            )

        logger.info("Generated %s models", len(tables))

    except Exception as e:
        logger.exception("Failed to generate models: %s", e)
        raise


def generate_services(
    parsed_dir: str = "data/output/current/parsed", decompiled_dir: str = "data/output/current/decompiled"
) -> None:








    """Generate all services from parsed PowerBuilder files.

    Args:
        parsed_dir: Directory containing parsed AST files
        decompiled_dir: Directory containing decompiled functions
    """
    try:
        import json
        from pathlib import Path

        generator = ServiceGenerator("templates", "output/backend")
        parsed_path = Path(parsed_dir)
        decompiled_path = Path(decompiled_dir)

        # Find all parsed user object files (.sru) - these often contain business logic
        user_object_files = list(parsed_path.rglob("*.sru.ast.json"))
        logger.info("Found %s user object files", len(user_object_files))

        # Extract service information
        services = {}
        for uo_file in user_object_files:
            try:
                with open(uo_file) as f:
                    ast_data = json.load(f)

                # Extract service name from filename
                service_name = uo_file.stem.replace(".sru.ast", "")

                # Skip if it looks like a UI component
                if any(
                    prefix in service_name.lower() for prefix in ["w_", "dw_", "uo_"]
                ):
                    continue

                # Create service definition
                if service_name not in services:
                    # Extract methods from AST
                    methods = extract_methods_from_ast(ast_data)

                    services[service_name] = {
                        "name": service_name,
                        "methods": methods,
                    }

                    # Check for corresponding decompiled functions
                    fun_file = decompiled_path / f"{service_name}.fun"
                    if fun_file.exists():
                        logger.debug("Found decompiled functions for %s", service_name)
                        # Parse decompiled functions to get implementation details
                        decompiled_methods = parse_decompiled_functions(fun_file)
                        # Merge with AST methods
                        for method in services[service_name]["methods"]:
                            if method["name"] in decompiled_methods:
                                method["implementation"] = decompiled_methods[
                                    method["name"]
                                ]

            except Exception as e:
                logger.warning("Failed to process %s: %s", uo_file, e)

        # Generate services
        for service in services.values():
            generator.generate_service(
                service["name"],
                service["methods"],
            )

        logger.info("Generated %s services", len(services))

    except Exception as e:
        logger.exception("Failed to generate services: %s", e)
        raise


def generate_flutter(parsed_dir: str = "data/output/current/parsed") -> None:








    """Generate all Flutter widgets and screens from parsed PowerBuilder files.

    Args:
        parsed_dir: Directory containing parsed AST files
    """
    try:
        import json
        from pathlib import Path

        generator = FlutterGenerator("templates/flutter", "output/flutter")
        parsed_path = Path(parsed_dir)

        # Find all parsed window files (.srw)
        window_files = list(parsed_path.rglob("*.srw.ast.json"))
        logger.info("Found %s window files", len(window_files))

        # Generate screens from PowerBuilder windows
        for window_file in window_files:
            try:
                with open(window_file) as f:
                    ast_data = json.load(f)

                window_name = window_file.stem.replace(".srw.ast", "")

                # Extract window information from AST
                window_info = extract_window_from_ast(ast_data)

                # Create screen definition
                generator.generate_screen(
                    name=window_name,
                    route_name=f"/{window_name.lower()}",
                    params=window_info.get("params", {}),
                    controllers=window_info.get("controllers", []),
                    services=window_info.get("services", []),
                )

            except Exception as e:
                logger.warning("Failed to process window %s: %s", window_file, e)

        # Find all parsed user object files (.sru)
        user_object_files = list(parsed_path.rglob("*.sru.ast.json"))

        # Generate widgets from PowerBuilder user objects
        for uo_file in user_object_files:
            try:
                with open(uo_file) as f:
                    ast_data = json.load(f)

                widget_name = uo_file.stem.replace(".sru.ast", "")

                # Skip non-UI objects
                if not any(prefix in widget_name.lower() for prefix in ["uo_", "u_"]):
                    continue

                # Extract widget information from AST
                widget_info = extract_widget_from_ast(ast_data)

                generator.generate_widget(
                    name=widget_name,
                    props=widget_info.get("props", {}),
                    is_stateful=widget_info.get("is_stateful", True),
                    children=widget_info.get("children", []),
                )

            except Exception as e:
                logger.warning("Failed to process user object %s: %s", uo_file, e)

        # Find all parsed DataWindow files (.srd)
        datawindow_files = list(parsed_path.rglob("*.srd.ast.json"))
        logger.info("Found %s DataWindow files", len(datawindow_files))

        # Generate DataWindow widgets
        for dw_file in datawindow_files:
            try:
                with open(dw_file) as f:
                    ast_data = json.load(f)

                dw_name = dw_file.stem.replace(".srd.ast", "")

                # Extract DataWindow information (reuse existing function)
                dw_info = extract_datawindow_from_ast(ast_data)

                generator.generate_datawindow_widget(
                    name=dw_name,
                    columns=dw_info.get("columns", []) if dw_info else [],
                    data_source=f"api/{dw_name}",
                )

            except Exception as e:
                logger.warning("Failed to process DataWindow %s: %s", dw_file, e)

        logger.info(
            f"Generated Flutter code for {len(window_files)} screens and {len(datawindow_files)} DataWindows"
        )

    except Exception as e:
        logger.exception("Failed to generate Flutter code: %s", e)
        raise
