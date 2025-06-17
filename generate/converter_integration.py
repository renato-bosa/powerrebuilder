"""Integration module for PowerBuilder to Flutter/Dart converters.

This module connects the AST converters with the code generators,
providing the bridge between parsed PowerBuilder code and generated output.
"""

import logging
from pathlib import Path
from typing import Dict, Any, List, Optional
from lark import Tree

from .converters import (
    ASTConverter,
    TypeConverter,
    ExpressionConverter,
    DataWindowConverter,
    EventConverter,
    UIConverter
)
from .generate_coordinator import FlutterGenerator, ModelGenerator

logger = logging.getLogger(__name__)


class ConversionPipeline:
    """Orchestrates the conversion from PowerBuilder AST to generated code."""
    
    def __init__(self, output_dir: Path, template_dir: Optional[Path] = None):
        """Initialize the conversion pipeline.
        
        Args:
            output_dir: Directory for generated code
            template_dir: Directory containing templates
        """
        self.output_dir = Path(output_dir)
        self.template_dir = template_dir or Path(__file__).parent / "flutter" / "templates"
        
        # Initialize converters
        self.ast_converter = ASTConverter()
        
        # Initialize generators
        self.flutter_generator = FlutterGenerator(
            str(self.template_dir),
            str(self.output_dir)
        )
        self.model_generator = ModelGenerator(
            str(self.template_dir.parent / "backend" / "templates"),
            str(self.output_dir / "models")
        )
    
    def convert_window(self, ast: Tree, window_name: str) -> None:
        """Convert a PowerBuilder window to Flutter screen.
        
        Args:
            ast: Parsed AST of the window
            window_name: Name of the window
        """
        logger.info("Converting window: %s", window_name)
        
        # Convert AST to intermediate representation
        window_def = self.ast_converter.convert_window(ast)
        
        # Generate Flutter screen
        self._generate_flutter_screen(window_def)
        
        # Generate associated widgets
        for control in window_def.controls:
            if control.get("custom_widget"):
                self._generate_custom_widget(control)
        
        # Generate DataWindow widgets
        for dw_name in window_def.datawindows:
            self._generate_datawindow_widget(dw_name, window_def)
    
    def convert_datawindow(self, dw_syntax: str, dw_name: str) -> None:
        """Convert a PowerBuilder DataWindow to Flutter widget.
        
        Args:
            dw_syntax: DataWindow syntax
            dw_name: Name of the DataWindow
        """
        logger.info("Converting DataWindow: %s", dw_name)
        
        # Convert DataWindow definition
        dw_def = self.ast_converter.datawindow_converter.convert_datawindow(
            dw_syntax, 
            dw_name
        )
        
        # Generate Flutter DataWindow widget
        self.flutter_generator.generate_datawindow_widget(
            name=dw_def.name,
            columns=[col.to_dict() for col in dw_def.columns],
            data_source=dw_def.sql or "",
            presentation_style=dw_def.presentation_style,
            row_type=dw_def.row_type
        )
        
        # Generate model if needed
        if dw_def.row_type != "Map<String, dynamic>":
            self._generate_datawindow_model(dw_def)
    
    def convert_user_object(self, ast: Tree, object_name: str) -> None:
        """Convert a PowerBuilder user object to Flutter widget.
        
        Args:
            ast: Parsed AST of the user object
            object_name: Name of the user object
        """
        logger.info("Converting user object: %s", object_name)
        
        # Convert AST to intermediate representation
        uo_def = self.ast_converter.convert_user_object(ast)
        
        # Determine if stateful
        is_stateful = len(uo_def.variables) > 0 or len(uo_def.events) > 0
        
        # Generate Flutter widget
        self._generate_flutter_widget(uo_def, is_stateful)
    
    def convert_structure(self, ast: Tree, structure_name: str) -> None:
        """Convert a PowerBuilder structure to Dart model.
        
        Args:
            ast: Parsed AST of the structure
            structure_name: Name of the structure
        """
        logger.info("Converting structure: %s", structure_name)
        
        # Convert AST to intermediate representation
        struct_def = self.ast_converter.convert_structure(ast)
        
        # Generate Dart model
        fields = []
        for field in struct_def.fields:
            fields.append({
                "name": field.name,
                "type": field.dart_type,
                "nullable": field.dart_type.endswith("?"),
                "required": not field.dart_type.endswith("?"),
                "default": field.initial_value
            })
        
        self.flutter_generator.generate_model(
            name=struct_def.name,
            fields=fields
        )
    
    def _generate_flutter_screen(self, window_def) -> None:
        """Generate Flutter screen from window definition."""
        # Extract parameters (instance variables)
        params = []
        for var in window_def.variables:
            if var.access_modifier == "public":
                params.append({
                    "name": var.name,
                    "type": var.dart_type,
                    "required": not var.dart_type.endswith("?")
                })
        
        # Extract controllers
        controllers = []
        for control in window_def.controls:
            if control.get("requires_controller"):
                controllers.append({
                    "name": f"_{control['dart_name']}Controller",
                    "type": control["controller_type"],
                    "widget_name": control["dart_name"]
                })
        
        # Extract services (from method calls)
        services = self._extract_services(window_def.methods)
        
        # Generate screen with full context
        context = {
            "screen": {
                "name": window_def.name,
                "title": window_def.properties.get("title", window_def.name),
                "route_name": f"/{self._to_snake_case(window_def.name)}"
            },
            "parameters": params,
            "controllers": controllers,
            "services": services,
            "state_variables": [v for v in window_def.variables if v.is_instance],
            "methods": self._convert_methods(window_def.methods),
            "events": self._convert_events(window_def.events),
            "build_method": self._generate_build_method(window_def)
        }
        
        # Use the screen template directly with full context
        content = self.flutter_generator.render_template("screen.dart.jinja2", context)
        output_file = f"screens/{self._to_snake_case(window_def.name)}_screen.dart"
        self.flutter_generator.write_file(output_file, content)
    
    def _generate_flutter_widget(self, uo_def, is_stateful: bool) -> None:
        """Generate Flutter widget from user object definition."""
        # Convert properties to widget props
        props = []
        for var in uo_def.variables:
            if var.access_modifier == "public":
                props.append({
                    "name": var.name,
                    "type": var.dart_type,
                    "required": not var.dart_type.endswith("?"),
                    "default": var.initial_value
                })
        
        # Generate widget tree
        widget_tree = self.ast_converter.ui_converter.generate_widget_tree(
            uo_def.controls
        )
        
        # Generate widget with full context
        context = {
            "widget": {
                "name": uo_def.name,
                "is_stateful": is_stateful
            },
            "properties": props,
            "state_variables": [v for v in uo_def.variables if v.is_instance],
            "methods": self._convert_methods(uo_def.methods),
            "events": self._convert_events(uo_def.events),
            "build_content": widget_tree,
            "imports": self._get_widget_imports(uo_def)
        }
        
        content = self.flutter_generator.render_template("widget.dart.jinja2", context)
        output_file = f"widgets/{self._to_snake_case(uo_def.name)}_widget.dart"
        self.flutter_generator.write_file(output_file, content)
    
    def _generate_custom_widget(self, control: Dict[str, Any]) -> None:
        """Generate a custom widget for a control.
        
        Args:
            control: Control definition with type and properties
        """
        control_type = control.get("type", "").lower()
        widget_name = control.get("widget", "")
        dart_name = control.get("dart_name", control.get("name", ""))
        
        logger.info("Generating custom widget for %s: %s", control_type, widget_name)
        
        # Determine which custom widget to generate
        if control_type == "datawindow":
            self._generate_datawindow_custom_widget(control)
        elif control_type == "treeview":
            self._generate_tree_view_widget(control)
        elif control_type == "graph":
            self._generate_chart_widget(control)
        elif control_type == "datepicker":
            self._generate_date_picker_widget(control)
        elif control_type == "monthcalendar":
            self._generate_calendar_widget(control)
        elif control_type in ["inkpicture", "inkedit"]:
            self._generate_ink_widget(control)
        elif control_type == "animation":
            self._generate_animation_widget(control)
        elif control_type == "ole":
            self._generate_ole_placeholder_widget(control)
        else:
            logger.warning("Unknown custom widget type: %s", control_type)
    
    def _generate_datawindow_custom_widget(self, control: Dict[str, Any]) -> None:
        """Generate DataWindow custom widget."""
        dw_object = control.get("properties", {}).get("dataobject", "")
        context = {
            "widget": {
                "name": f"{self._to_pascal_case(control['dart_name'])}DataWindow",
                "is_stateful": True
            },
            "datawindow_name": dw_object,
            "dart_name": control['dart_name'],
            "properties": control.get("properties", {}),
            "imports": [
                "import 'package:flutter/material.dart';",
                "import '../models/datawindow_model.dart';",
                "import '../services/datawindow_service.dart';"
            ]
        }
        
        content = self.flutter_generator.render_template("datawindow_widget.dart.jinja2", context)
        output_file = f"widgets/{self._to_snake_case(context['widget']['name'])}.dart"
        self.flutter_generator.write_file(output_file, content)
    
    def _generate_tree_view_widget(self, control: Dict[str, Any]) -> None:
        """Generate TreeView custom widget."""
        context = {
            "widget": {
                "name": f"{self._to_pascal_case(control['dart_name'])}TreeView",
                "is_stateful": True
            },
            "dart_name": control['dart_name'],
            "properties": control.get("flutter_properties", {}),
            "show_lines": control.get("properties", {}).get("haslines", True),
            "show_expand_buttons": control.get("properties", {}).get("hasbuttons", True),
            "is_sorted": control.get("properties", {}).get("sorted", False),
            "imports": [
                "import 'package:flutter/material.dart';",
                "import 'package:flutter_fancy_tree_view/flutter_fancy_tree_view.dart';"
            ]
        }
        
        content = self.flutter_generator.render_template("tree_view_widget.dart.jinja2", context)
        output_file = f"widgets/{self._to_snake_case(context['widget']['name'])}.dart"
        self.flutter_generator.write_file(output_file, content)
    
    def _generate_chart_widget(self, control: Dict[str, Any]) -> None:
        """Generate Chart/Graph custom widget."""
        graph_type = control.get("properties", {}).get("graphtype", "bar")
        context = {
            "widget": {
                "name": f"{self._to_pascal_case(control['dart_name'])}Chart",
                "is_stateful": True
            },
            "dart_name": control['dart_name'],
            "chart_type": graph_type,
            "properties": control.get("flutter_properties", {}),
            "imports": [
                "import 'package:flutter/material.dart';",
                "import 'package:fl_chart/fl_chart.dart';"
            ]
        }
        
        content = self.flutter_generator.render_template("chart_widget.dart.jinja2", context)
        output_file = f"widgets/{self._to_snake_case(context['widget']['name'])}.dart"
        self.flutter_generator.write_file(output_file, content)
    
    def _generate_date_picker_widget(self, control: Dict[str, Any]) -> None:
        """Generate DatePicker custom widget."""
        context = {
            "widget": {
                "name": f"{self._to_pascal_case(control['dart_name'])}DatePicker",
                "is_stateful": False
            },
            "dart_name": control['dart_name'],
            "properties": control.get("flutter_properties", {}),
            "date_format": control.get("properties", {}).get("format", "yyyy-MM-dd"),
            "imports": [
                "import 'package:flutter/material.dart';",
                "import 'package:intl/intl.dart';"
            ]
        }
        
        content = self.flutter_generator.render_template("date_picker_widget.dart.jinja2", context)
        output_file = f"widgets/{self._to_snake_case(context['widget']['name'])}.dart"
        self.flutter_generator.write_file(output_file, content)
    
    def _generate_calendar_widget(self, control: Dict[str, Any]) -> None:
        """Generate Calendar custom widget."""
        context = {
            "widget": {
                "name": f"{self._to_pascal_case(control['dart_name'])}Calendar",
                "is_stateful": True
            },
            "dart_name": control['dart_name'],
            "properties": control.get("flutter_properties", {}),
            "show_today": control.get("properties", {}).get("showtoday", True),
            "imports": [
                "import 'package:flutter/material.dart';",
                "import 'package:table_calendar/table_calendar.dart';"
            ]
        }
        
        content = self.flutter_generator.render_template("calendar_widget.dart.jinja2", context)
        output_file = f"widgets/{self._to_snake_case(context['widget']['name'])}.dart"
        self.flutter_generator.write_file(output_file, content)
    
    def _generate_ink_widget(self, control: Dict[str, Any]) -> None:
        """Generate Ink (drawing) custom widget."""
        is_text_field = control.get("type", "").lower() == "inkedit"
        context = {
            "widget": {
                "name": f"{self._to_pascal_case(control['dart_name'])}Ink{'Edit' if is_text_field else 'Canvas'}",
                "is_stateful": True
            },
            "dart_name": control['dart_name'],
            "is_text_field": is_text_field,
            "properties": control.get("flutter_properties", {}),
            "stroke_color": control.get("properties", {}).get("inkcolor", "Colors.black"),
            "stroke_width": control.get("properties", {}).get("inkwidth", 2.0),
            "imports": [
                "import 'package:flutter/material.dart';",
                "import 'package:perfect_freehand/perfect_freehand.dart';"
            ]
        }
        
        content = self.flutter_generator.render_template("ink_widget.dart.jinja2", context)
        output_file = f"widgets/{self._to_snake_case(context['widget']['name'])}.dart"
        self.flutter_generator.write_file(output_file, content)
    
    def _generate_animation_widget(self, control: Dict[str, Any]) -> None:
        """Generate Animation custom widget."""
        context = {
            "widget": {
                "name": f"{self._to_pascal_case(control['dart_name'])}Animation",
                "is_stateful": True
            },
            "dart_name": control['dart_name'],
            "properties": control.get("flutter_properties", {}),
            "animation_file": control.get("properties", {}).get("animationfile", ""),
            "auto_play": control.get("properties", {}).get("autoplay", True),
            "is_transparent": control.get("properties", {}).get("transparent", False),
            "imports": [
                "import 'package:flutter/material.dart';",
                "import 'package:lottie/lottie.dart';"
            ]
        }
        
        content = self.flutter_generator.render_template("animation_widget.dart.jinja2", context)
        output_file = f"widgets/{self._to_snake_case(context['widget']['name'])}.dart"
        self.flutter_generator.write_file(output_file, content)
    
    def _generate_ole_placeholder_widget(self, control: Dict[str, Any]) -> None:
        """Generate OLE placeholder widget."""
        context = {
            "widget": {
                "name": f"{self._to_pascal_case(control['dart_name'])}OleContainer",
                "is_stateful": False
            },
            "dart_name": control['dart_name'],
            "ole_class": control.get("properties", {}).get("classname", "Unknown"),
            "activation_type": control.get("properties", {}).get("activation", "manual"),
            "display_mode": control.get("properties", {}).get("displaytype", "content"),
            "imports": [
                "import 'package:flutter/material.dart';"
            ]
        }
        
        content = self.flutter_generator.render_template("ole_placeholder_widget.dart.jinja2", context)
        output_file = f"widgets/{self._to_snake_case(context['widget']['name'])}.dart"
        self.flutter_generator.write_file(output_file, content)
    
    def _generate_datawindow_widget(self, dw_name: str, window_def) -> None:
        """Generate DataWindow widget referenced in window."""
        # Find DataWindow control properties
        for control in window_def.controls:
            if control.get("name") == dw_name and control.get("type") == "datawindow":
                # Get DataWindow object name
                dw_object = control.get("properties", {}).get("dataobject", "")
                if dw_object:
                    # This would load and convert the DataWindow definition
                    logger.info("Would generate DataWindow widget for: %s", dw_object)
    
    def _generate_datawindow_model(self, dw_def) -> None:
        """Generate model class for DataWindow row type."""
        fields = []
        imports = []
        has_blob = False
        
        for col in dw_def.columns:
            field_name = self._to_camel_case(col.name.split(".")[-1])
            field_type = col.data_type
            
            # Handle blob fields specially
            if col.blob_metadata:
                has_blob = True
                # Use appropriate type based on blob usage
                usage = col.blob_metadata.get("usage", "data")
                if usage == "image":
                    # For images, store as Uint8List but provide helper methods
                    field_type = "Uint8List"
                else:
                    field_type = "Uint8List"
                
                # Add blob-specific JSON conversion
                from_json = f"json['{col.name}'] != null ? base64Decode(json['{col.name}']) : null"
                to_json = f"'{col.name}': {field_name} != null ? base64Encode({field_name}!) : null"
            else:
                from_json = f"json['{col.name}']"
                to_json = f"'{col.name}': {field_name}"
            
            fields.append({
                "name": field_name,
                "type": field_type,
                "nullable": True,  # DataWindow columns are typically nullable
                "from_json": from_json,
                "to_json": to_json,
                "is_blob": col.blob_metadata is not None,
                "blob_metadata": col.blob_metadata
            })
        
        # Add blob imports if needed
        if has_blob:
            imports.extend([
                "import 'dart:typed_data';",
                "import 'dart:convert';"
            ])
        
        # Generate blob handling code
        blob_handling = dw_def.generate_blob_handling_code(self.ast_converter.datawindow_converter.blob_converter)
        
        # Generate blob display widgets
        for widget in blob_handling.get("display_widgets", []):
            widget_file = f"widgets/{self._to_snake_case(widget['name'])}.dart"
            self.flutter_generator.write_file(widget_file, widget['code'])
        
        context = {
            "model": {
                "name": dw_def.row_type,
                "fields": fields,
                "has_custom_methods": has_blob,
                "imports": imports,
                "blob_repository_methods": blob_handling.get("repository_methods", "")
            }
        }
        
        content = self.flutter_generator.render_template("model.dart.jinja2", context)
        output_file = f"models/{self._to_snake_case(dw_def.row_type)}.dart"
        self.flutter_generator.write_file(output_file, content)
    
    def _convert_methods(self, methods: List) -> List[Dict[str, Any]]:
        """Convert method definitions for template."""
        converted = []
        for method in methods:
            converted.append({
                "name": method.name,
                "return_type": method.dart_return_type,
                "parameters": [
                    {"name": p.name, "type": p.dart_type} 
                    for p in method.parameters
                ],
                "is_async": method.is_async,
                "is_private": method.access_modifier == "private",
                "body": method.body
            })
        return converted
    
    def _convert_events(self, events: List) -> List[Dict[str, Any]]:
        """Convert event handlers for template."""
        converted = []
        for event in events:
            converted.append({
                "name": event.name,
                "handler_name": f"_{self._to_camel_case(event.name)}Handler",
                "parameters": [
                    {"name": p.name, "type": p.dart_type}
                    for p in event.parameters
                ],
                "is_async": event.is_async,
                "body": event.body,
                "widget_wrapper": self.ast_converter.event_converter.get_event_widget_wrapper(event.name)
            })
        return converted
    
    def _generate_build_method(self, window_def) -> str:
        """Generate the build method content for a screen."""
        # Generate widget tree from controls
        return self.ast_converter.ui_converter.generate_widget_tree(
            window_def.controls
        )
    
    def _extract_services(self, methods: List) -> List[str]:
        """Extract service dependencies from method calls."""
        services = set()
        
        # Look for repository/service patterns in method bodies
        for method in methods:
            for statement in method.body:
                if "repository" in statement.lower():
                    services.add("repository")
                elif "service" in statement.lower():
                    services.add("service")
        
        return list(services)
    
    def _get_widget_imports(self, definition) -> List[str]:
        """Get required imports for a widget/screen."""
        imports = set()
        imports.add("import 'package:flutter/material.dart';")
        
        # Add imports based on controls
        widget_imports = self.ast_converter.ui_converter.get_widget_imports(
            definition.controls
        )
        imports.update(widget_imports)
        
        # Add imports based on types
        for var in definition.variables:
            type_imports = self.ast_converter.type_converter.get_imports_for_type(
                var.type
            )
            imports.update(type_imports)
        
        return sorted(list(imports))
    
    def _to_snake_case(self, name: str) -> str:
        """Convert name to snake_case."""
        # Remove prefixes
        if name.startswith("w_"):
            name = name[2:]
        
        # Convert from PascalCase/camelCase to snake_case
        result = []
        for i, char in enumerate(name):
            if char.isupper() and i > 0 and name[i-1].islower():
                result.append("_")
            result.append(char.lower())
        return "".join(result)
    
    def _to_camel_case(self, name: str) -> str:
        """Convert name to camelCase."""
        parts = name.split("_")
        return parts[0].lower() + "".join(p.capitalize() for p in parts[1:])
    
    def _to_pascal_case(self, name: str) -> str:
        """Convert name to PascalCase preserving existing capitalization."""
        if not name:
            return ""
        # If already in camelCase or PascalCase, just ensure first letter is capital
        if "_" not in name:
            return name[0].upper() + name[1:]
        # If snake_case, convert to PascalCase
        parts = name.split("_")
        return "".join(p.capitalize() for p in parts)


def integrate_converters(ast: Tree, object_type: str, object_name: str,
                        output_dir: Path, template_dir: Optional[Path] = None) -> None:
    """Main entry point for converter integration.
    
    Args:
        ast: Parsed PowerBuilder AST
        object_type: Type of PowerBuilder object
        object_name: Name of the object
        output_dir: Output directory for generated code
        template_dir: Optional template directory
    """
    pipeline = ConversionPipeline(output_dir, template_dir)
    
    if object_type == "window":
        pipeline.convert_window(ast, object_name)
    elif object_type == "userobject":
        pipeline.convert_user_object(ast, object_name)
    elif object_type == "structure":
        pipeline.convert_structure(ast, object_name)
    elif object_type == "datawindow":
        # For DataWindow, we need the syntax not AST
        # This would be called differently
        logger.warning("DataWindow conversion requires syntax, not AST")
    else:
        logger.warning("Unsupported object type for conversion: %s", object_type)