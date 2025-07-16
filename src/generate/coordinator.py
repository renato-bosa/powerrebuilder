"""Code generation module for converting PowerBuilder models to modern code.

This module forms the final stage in the PowerBuilder reverse engineering pipeline,
generating modern web application code from semantic models produced by the Model stage.

PIPELINE SEQUENCE:
1. Extract → .fun files
2. Decompile → .sru files  
3. Parse → AST JSON
4. Model → Semantic models
5. Generate → Modern code (THIS STAGE)

INPUTS:
- From Model stage: Semantic models containing typed representations of the application

OUTPUTS:
- Backend: Python/Litestar APIs, SQLModel models, Pydantic schemas
- Frontend: Flutter/Dart UI, screens, widgets, state management

Key components:
- CodeGenerator: Base class providing template rendering functionality
- ModelGenerator: Generates SQLModel models from database schema
- ServiceGenerator: Converts business logic into service layer classes
- FlutterGenerator: Transforms UI definitions into Flutter/Dart widgets

The code generation relies on Jinja2 templates to transform semantic models
into production-ready code for modern frameworks.

Each generator handles a specific aspect of the application and is orchestrated
through the main entry points: generate_models(), generate_services(), and generate_flutter().
"""

import logging
from pathlib import Path
from typing import Any


from src.parse.parser.sql import SQLParser
from src.generate.converters.data.relationship_extractor import RelationshipExtractor
from src.generate.converters.utils.ast_converter import ASTConverter
from src.generate.converters.flutter.ui.widget_converter import UIConverter
from src.generate.converters.flutter.state.model_converter import TypeConverter
from src.generate.converters.flutter.business.logic_converter import MethodBodyConverter
from src.generate.converters.logic.event_wiring import EventWiringSystem
from src.generate.converters.flutter.ui.layout_converter import LayoutConverter, LayoutStrategy
from src.generate.converters.flutter.ui.menu_converter import MenuConverter
from src.generate.base_generator import CodeGenerator
from src.generate.python_ui_generator import PythonUIGenerator
from src.generate.model_generator import ModelGenerator
from src.generate.service_generator import ServiceGenerator
from src.generate.flutter_generator import FlutterGenerator

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
            str(Path(__file__).parent / "templates"), str(self.output_dir / "backend"), validate_templates=False
        )
        self.service_generator = ServiceGenerator(
            str(Path(__file__).parent / "templates"), str(self.output_dir / "backend"), validate_templates=False
        )
        self.flutter_generator = FlutterGenerator(
            str(Path(__file__).parent / "templates" / "flutter"), str(self.output_dir / "flutter"), validate_templates=False
        )

        # Pass the layout converter to the Flutter generator
        self.flutter_generator.layout_converter = None  # Will set after initialization

        # Initialize Python UI generator
        self.python_ui_generator = PythonUIGenerator(
            str(Path(__file__).parent / "templates" / "python"), str(self.output_dir / "python")
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

    def generate_from_model(self, model_file: str) -> dict:
        """Generate code from a model file.

        Args:
            model_file: Path to model JSON file

        Returns:
            Dictionary with generation results
        """
        try:
            import json

            # Load model data
            model_path = Path(model_file)
            if not model_path.exists():
                # Try relative to input dir
                model_path = self.input_dir / model_file

            if not model_path.exists():
                logger.error(f"Model file not found: {model_file}")
                return {'success': False, 'error': 'Model file not found'}

            with open(model_path) as f:
                model_data = json.load(f)

            generated_files = []

            # Extract original AST file reference if available
            ast_file = model_data.get('ast_file', model_data.get('file'))

            # Process each model object in the file
            models = model_data.get('models', [])
            if not models:
                logger.warning(f"No models found in {model_file}")
                return {'success': False, 'error': 'No models in file'}

            for model in models:
                model_type = model.get('type', 'Unknown')
                model_name = model.get('name', 'unnamed')
                model_instance = model.get('data', {})

                # Skip error models
                if model_instance == 'error' or (isinstance(model_instance, dict) and model_instance.get('type') == 'tree' and model_instance.get('data') == 'error'):
                    logger.warning(f"Skipping error model in {model_file}")
                    continue

                # Generate code based on model type
                if model_type in ['window', 'PBWindow', 'Window']:
                    # Use model_name with fallback to properties
                    name = model_name or model_instance.get('name', 'unnamed_window')
                    # Ensure model_instance has required properties
                    if not model_instance.get('name'):
                        model_instance['name'] = name
                    result = self.flutter_generator.generate_screen_from_model(model_instance)
                    generated_files.append(f"flutter/screens/{name}_screen.dart")

                elif model_type in ['datawindow', 'PBDataWindow', 'DataWindow']:
                    name = model_name or model_instance.get('name', 'unnamed_datawindow')
                    columns = model_instance.get('columns', [])
                    result = self.model_generator.generate_model(name, columns, [])
                    generated_files.append(f"backend/models/{name}.py")

                elif model_type in ['userobject', 'PBUserObject', 'UserObject']:
                    name = model_name or model_instance.get('name', 'unnamed_userobject')
                    if model_instance.get('visual', False):
                        # Generate Flutter widget
                        result = self.flutter_generator.generate_widget(
                            name=name,
                            properties=model_instance.get('properties', {}),
                            methods=model_instance.get('methods', [])
                        )
                        generated_files.append(f"flutter/widgets/{name}_widget.dart")
                    else:
                        # Generate service
                        methods = model_instance.get('methods', [])
                        self.service_generator.generate_service(name, methods)
                        generated_files.append(f"backend/services/{name}_service.py")

                elif model_type in ['function', 'PBFunction', 'Function']:
                    name = model_name or model_instance.get('name', 'unnamed_function')
                    # Generate service method
                    self.service_generator.generate_service(name, [model_instance])
                    generated_files.append(f"backend/services/{name}_service.py")

                elif model_type == 'application':
                    name = model_name or 'app'
                    # Generate application structure
                    app_info = {
                        'name': name,
                        'display_name': model_instance.get('title', name),
                        'description': f'PowerBuilder {name} application',
                        'has_database': True,  # Assume most PB apps use database
                        'initial_window': model_instance.get('open_window', ''),
                        'variables': model_instance.get('variables', []),
                        'events': model_instance.get('events', [])
                    }
                    self.flutter_generator.generate_project_structure(app_info)
                    generated_files.append(f"flutter/pubspec.yaml")
                    generated_files.append(f"flutter/lib/main.dart")

                elif model_type == 'menu':
                    name = model_name or 'menu'
                    # Generate menu widget
                    if self.framework == 'flutter':
                        # Convert menu definition to Flutter
                        menu_syntax = model_instance.get('syntax', '')
                        menu_def = self.flutter_generator.menu_converter.convert_menu(menu_syntax, name)
                        
                        # Generate Flutter menu code
                        flutter_menu = self.flutter_generator.menu_converter.generate_flutter_menu(menu_def)
                        
                        # Write menu widget file
                        context = {
                            "menu": menu_def.to_dict(),
                            "flutter_code": flutter_menu
                        }
                        content = self.flutter_generator.render_template("menu_widget.dart.jinja2", context)
                        self.flutter_generator.write_file(f"widgets/{name.lower()}_menu.dart", content)
                        generated_files.append(f"flutter/widgets/{name.lower()}_menu.dart")
                    else:
                        logger.info(f"Menu generation not yet implemented for framework: {self.framework}")

                elif model_type == 'structure':
                    name = model_name or 'struct'
                    # Generate data model from structure
                    fields = model_instance.get('fields', [])
                    columns = []
                    for field in fields:
                        columns.append({
                            'name': field.get('name', ''),
                            'type': field.get('type', 'string'),
                            'nullable': field.get('nullable', True)
                        })
                    if columns:
                        result = self.model_generator.generate_model(name, columns, [])
                        generated_files.append(f"backend/models/{name}.py")

                elif model_type == 'unknown':
                    # Check if we can infer type from name
                    if model_name:
                        inferred_type = self._infer_type_from_name(model_name)
                        if inferred_type != 'unknown':
                            # Retry with inferred type
                            model['type'] = inferred_type
                            continue
                    logger.warning(f"Unknown model type for {model_name}")

                else:
                    logger.warning(f"Unsupported model type: {model_type}")

            return {
                'success': True,
                'files': generated_files,
                'model_file': str(model_file)
            }

        except Exception as e:
            logger.error(f"Failed to generate code from model {model_file}: {e}")
            return {
                'success': False,
                'error': str(e),
                'model_file': str(model_file)
            }

    def process_directory(self) -> dict:
        """Process all model files in the input directory.

        Returns:
            Dictionary with processing results
        """
        if not self.input_dir or not self.input_dir.exists():
            logger.error("Input directory does not exist: %s", self.input_dir)
            return {'success': False, 'error': 'Input directory not found', 'files_generated': 0}

        # Find all model.json files
        model_files = list(self.input_dir.rglob("*.model.json"))
        logger.info("Found %d model files to process", len(model_files))

        total_generated = 0
        failed_files = []

        for model_file in model_files:
            try:
                result = self.generate_from_model(str(model_file))
                if result.get('success'):
                    total_generated += len(result.get('files', []))
                else:
                    failed_files.append(str(model_file))
            except Exception as e:
                logger.error("Failed to process model file %s: %s", model_file, e)
                failed_files.append(str(model_file))

        return {
            'success': True,
            'total_models': len(model_files),
            'files_generated': total_generated,
            'failed_files': failed_files
        }

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
                    logger.info(f"Extracted {len(methods)} methods from {object_name} for service generation")
                    if methods:
                        for method in methods:
                            logger.debug(f"  - Method: {method.get('name', 'unnamed')} -> {method.get('return_type', 'void')}")
                    self.service_generator.generate_service(
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
            'name': object_name, 'title': ast_data.get('title', object_name), 'controls': [], 'events': [], 'variables': [], 'methods': [], 'menu': None
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

        # Extract menu if present
        if 'menu' in ast_data and ast_data['menu']:
            menu_data = ast_data['menu']
            if isinstance(menu_data, dict):
                menu_name = menu_data.get('name', 'window_menu')
                menu_syntax = menu_data.get('syntax', '')
                # Convert menu using menu converter
                try:
                    menu_def = self.flutter_generator.menu_converter.convert_menu(menu_syntax, menu_name)
                    window_model['menu'] = menu_def.to_dict()
                    logger.debug(f"Extracted menu {menu_name} for window {object_name}")
                except Exception as e:
                    logger.warning(f"Failed to convert menu for window {object_name}: {e}")

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

    def _infer_type_from_name(self, name: str) -> str:
        """Infer object type from name patterns.

        Args:
            name: Object name

        Returns:
            Inferred type or 'unknown'
        """
        name_lower = name.lower()

        if name_lower.startswith('w_'):
            return 'window'
        elif name_lower.startswith('d_') or name_lower.startswith('dw_'):
            return 'datawindow'
        elif name_lower.startswith('n_') or name_lower.startswith('nv_'):
            return 'userobject'  # Non-visual
        elif name_lower.startswith('u_') or name_lower.startswith('uo_'):
            return 'userobject'  # Visual
        elif name_lower.startswith('f_'):
            return 'function'
        elif name_lower.startswith('m_'):
            return 'menu'
        elif name_lower.startswith('s_'):
            return 'structure'
        elif '_app' in name_lower:
            return 'application'
        else:
            return 'unknown'


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
        List of method dictionaries with required fields:
        - name: Method name
        - return_type: Return type (defaults to 'void')
        - parameters: List of parameter dicts
        - body: Method implementation (optional)
        - visibility: public/private (defaults to 'public')
    """
    methods = []

    if not isinstance(ast_data, dict):
        logger.debug("extract_methods_from_ast: ast_data is not a dict, returning empty list")
        return methods

    # Look for function/event nodes
    node_type = ast_data.get("node_type") or ast_data.get("type")
    
    # Also check for methods within functions/events lists
    if 'functions' in ast_data:
        for func in ast_data['functions']:
            if isinstance(func, dict):
                sub_methods = extract_methods_from_ast(func)
                methods.extend(sub_methods)
    
    if 'events' in ast_data:
        for event in ast_data['events']:
            if isinstance(event, dict):
                sub_methods = extract_methods_from_ast(event)
                methods.extend(sub_methods)
    
    if node_type in ["Function", "Event", "Method", "function", "event", "method", "PBFunction", "PBEvent"]:
        method_name = ast_data.get("name", "unnamed_method")
        logger.debug(f"Found method node: {method_name} (type: {node_type})")
        
        method_info = {
            "name": method_name, 
            "return_type": ast_data.get("return_type", "void"), 
            "visibility": ast_data.get("visibility", "public"), 
            "parameters": [],
            "body": ast_data.get("body", []),  # Include body for implementation
        }

        # Extract parameters
        if "arguments" in ast_data:
            args = ast_data["arguments"]
            if isinstance(args, dict) and "arguments" in args:
                args = args["arguments"]

            for arg in args if isinstance(args, list) else []:
                param = {
                    "name": arg.get("name", ""), "type": arg.get("type", "any"), "is_reference": arg.get("is_reference", False), "is_readonly": arg.get("is_readonly", False), "default_value": arg.get("default_value"), }
                method_info["parameters"].append(param)

        # Also check for parameters in different formats
        if "parameters" in ast_data:
            params = ast_data["parameters"]
            if isinstance(params, list):
                method_info["parameters"] = []
                for param in params:
                    if isinstance(param, dict):
                        method_info["parameters"].append({
                            "name": param.get("name", ""),
                            "type": param.get("type", "any"),
                            "is_reference": param.get("is_reference", False),
                            "is_readonly": param.get("is_readonly", False),
                            "default_value": param.get("default_value"),
                        })
        
        # Validate method info
        if method_info["name"] and method_info["name"] != "unnamed_method":
            methods.append(method_info)
            logger.debug(f"Added method: {method_info['name']} with {len(method_info['parameters'])} parameters")
        else:
            logger.warning(f"Skipping method with invalid name: {method_info.get('name')}")

    # Recursively search for method nodes, but skip already processed keys
    skip_keys = {'functions', 'events', 'body', 'statements'}  # Avoid infinite recursion
    for key, value in ast_data.items():
        if key in skip_keys:
            continue
        if isinstance(value, dict):
            sub_methods = extract_methods_from_ast(value)
            if sub_methods:
                logger.debug(f"Found {len(sub_methods)} methods in {key}")
                methods.extend(sub_methods)
        elif isinstance(value, list) and key not in ['parameters', 'arguments']:
            for i, item in enumerate(value):
                if isinstance(item, dict):
                    sub_methods = extract_methods_from_ast(item)
                    if sub_methods:
                        logger.debug(f"Found {len(sub_methods)} methods in {key}[{i}]")
                        methods.extend(sub_methods)

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


def generate_models(parsed_dir: str = "data/output/current/parsed") -> None:

    """Generate all database models from parsed PowerBuilder files.

    Args:
        parsed_dir: Directory containing parsed AST files (default: output/parsed)
    """
    try:
        import json
        from pathlib import Path

        generator = ModelGenerator(str(Path(__file__).parent / "templates"), "output/backend", validate_templates=False)
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

        generator = ServiceGenerator(str(Path(__file__).parent / "templates"), "output/backend", validate_templates=False)
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
                    logger.info(f"Extracted {len(methods)} methods from {service_name} AST")
                    if methods:
                        for method in methods:
                            logger.debug(f"  - Method: {method.get('name', 'unnamed')} -> {method.get('return_type', 'void')}")

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
        logger.info(f"Generating {len(services)} services")
        for service in services.values():
            logger.info(f"Generating service {service['name']} with {len(service['methods'])} methods")
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

        generator = FlutterGenerator(
            str(Path(__file__).parent / "templates" / "flutter"), 
            "data/output/current/flutter"
        )
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