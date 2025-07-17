"""Flutter generator for creating Flutter/Dart UI from PowerBuilder definitions."""

import logging
from typing import Any, Dict, List, Optional
from pathlib import Path

from src.generate.base_generator import CodeGenerator

logger = logging.getLogger(__name__)


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
        self.generated_screens = []
        self.generated_widgets = []
        self.generated_models = []
        self.generated_services = []
        self.layout_converter = None
        self.event_converter = None
        self.menu_converter = None

    def generate_widget(
        self, widget_type: str, widget_name: str, properties: dict[str, Any]
    ) -> None:
        """Generate a Flutter widget.

        Args:
            widget_type: Type of widget to generate
            widget_name: Name for the widget class
            properties: Widget properties and configuration
        """
        context = {
            "widget_type": widget_type,
            "widget_name": widget_name,
            "properties": properties,
        }
        content = self.render_template(f"flutter/{widget_type}_widget.dart.jinja2", context)
        self.write_file(f"widgets/{widget_name.lower()}_widget.dart", content)
        self.generated_widgets.append(widget_name)

    def generate_screen_from_model(self, window_model: dict) -> dict:
        """Generate a Flutter screen from a window model."""
        screen_name = window_model.get("name", "UnknownScreen")
        
        # Enhanced data extraction from model
        extracted_data = self._extract_enhanced_screen_data(window_model)
        
        # Generate main screen file
        context = {
            **extracted_data,
            "screen_name": screen_name,
            "imports": self._generate_imports(extracted_data),
            "state_management": self._needs_state_management(extracted_data),
        }
        
        # Generate the main screen
        content = self.render_template("flutter/screen_enhanced.dart.jinja2", context)
        output_path = f"screens/{self._to_snake_case(screen_name)}_screen.dart"
        self.write_file(output_path, content)
        
        # Generate event handlers mixin if needed
        if extracted_data["event_handlers"]:
            self._generate_event_handlers_mixin(screen_name, extracted_data["event_handlers"])
        
        # Generate state provider if needed
        if self._needs_state_management(extracted_data):
            self._generate_state_provider(screen_name, window_model)
        
        self.generated_screens.append(screen_name)
        
        return {
            "screen": screen_name,
            "file": output_path,
            "has_state": self._needs_state_management(extracted_data),
            "dependencies": extracted_data.get("service_dependencies", [])
        }

    def _extract_enhanced_screen_data(self, window_model: dict) -> dict:
        """Extract and enhance screen data from window model."""
        # Process controls with enhanced converter
        controls = window_model.get("controls", [])
        processed_controls = self._process_controls_enhanced(controls)
        
        # Extract form fields
        form_fields = self._extract_form_fields(controls)
        
        # Process events with enhanced handler
        events = window_model.get("events", [])
        event_data = self._process_events_enhanced(events, controls)
        
        # Extract DataWindows
        datawindows = window_model.get("datawindows", [])
        processed_datawindows = self._process_datawindows(datawindows)
        
        # Extract instance variables
        instance_vars = window_model.get("instance_variables", [])
        
        # Extract service dependencies
        service_deps = self._extract_service_dependencies(window_model)
        
        # Extract menu if present
        menu_data = window_model.get("menu")
        menu_actions = self._extract_menu_actions(menu_data) if menu_data else []
        menu_callbacks = self._extract_menu_callbacks(menu_data) if menu_data else []
        
        # Extract toolbar actions
        toolbar_actions = self._extract_toolbar_actions(controls)
        
        # Extract initialization code
        init_code = self._extract_init_code(window_model)
        
        # Extract load data code
        load_data_code = self._extract_load_data_code(window_model)
        
        # Extract focus nodes
        focus_nodes = [f"{self._to_camel_case(f['name'])}Focus" 
                      for f in form_fields if f.get('type') in ['text', 'number', 'textarea']]
        
        # Extract dispose code
        dispose_code = self._extract_dispose_code(focus_nodes)
        
        return {
            "controls": processed_controls,
            "form_fields": form_fields,
            "event_handlers": event_data["handlers"],
            "event_listeners": event_data["listeners"],
            "datawindows": processed_datawindows,
            "instance_variables": instance_vars,
            "service_dependencies": service_deps,
            "menu_actions": menu_actions,
            "menu_callbacks": menu_callbacks,
            "toolbar_actions": toolbar_actions,
            "init_code": init_code,
            "load_data_code": load_data_code,
            "focus_nodes": focus_nodes,
            "dispose_code": dispose_code,
            "has_form": bool(form_fields),
            "has_datawindows": bool(datawindows),
            "has_menu": bool(menu_data),
            "has_toolbar": bool(toolbar_actions),
            "methods": self._convert_methods(window_model.get("methods", [])),
        }

    def _process_controls_enhanced(self, controls: list) -> list:
        """Process controls with enhanced layout and styling."""
        if not self.layout_converter:
            from src.generate.converters.flutter.ui.layout_converter import LayoutConverter
            self.layout_converter = LayoutConverter()
        
        processed = []
        for control in controls:
            # Basic control info
            ctrl_data = {
                "type": control.get("type", "unknown"),
                "name": control.get("name", ""),
                "properties": control.get("properties", {}),
                "position": control.get("position", {}),
                "size": control.get("size", {}),
                "visible": control.get("visible", True),
                "enabled": control.get("enabled", True),
            }
            
            # Add text styling
            if "text" in control:
                ctrl_data["text"] = control["text"]
                ctrl_data["text_style"] = self._get_text_style(control)
            
            # Add specific widget properties
            if control.get("type") == "commandbutton":
                ctrl_data["on_pressed"] = f"_on{control['name'].capitalize()}Click"
            elif control.get("type") == "singlelineedit":
                ctrl_data["controller"] = f"_{self._to_camel_case(control['name'])}Controller"
                ctrl_data["hint_text"] = control.get("properties", {}).get("hint", "")
            
            processed.append(ctrl_data)
        
        return self.layout_converter.convert_layout(processed)

    def _process_events_enhanced(self, events: list, controls: list) -> dict:
        """Process events into handlers and listeners."""
        if not self.event_converter:
            from src.generate.converters.flutter.state.event_converter import EventConverter
            self.event_converter = EventConverter()
        
        handlers = []
        listeners = []
        
        for event in events:
            event_data = {
                "name": event.get("name", ""),
                "control": event.get("control", ""),
                "type": event.get("type", ""),
                "params": self._format_event_params(event.get("parameters", [])),
                "body": self._convert_event_body(event),
                "async": event.get("async", False),
            }
            
            # Categorize as handler or listener
            if event.get("type") in ["clicked", "modified", "selectionchanged"]:
                handlers.append(event_data)
            else:
                listeners.append(event_data)
        
        return {
            "handlers": handlers,
            "listeners": listeners
        }

    def _convert_pb_type(self, pb_type: str) -> str:
        """Convert PowerBuilder type to Dart type."""
        type_map = {
            "string": "String",
            "long": "int",
            "integer": "int",
            "decimal": "double",
            "real": "double",
            "boolean": "bool",
            "date": "DateTime",
            "time": "TimeOfDay",
            "datetime": "DateTime",
            "any": "dynamic",
        }
        
        # Handle arrays
        if pb_type.endswith("[]"):
            base_type = pb_type[:-2]
            dart_type = type_map.get(base_type, base_type)
            return f"List<{dart_type}>"
        
        return type_map.get(pb_type.lower(), pb_type)

    def _get_initial_value(self, var: dict) -> str:
        """Get Dart initial value for a variable."""
        var_type = var.get("type", "any")
        initial = var.get("initial_value")
        
        if initial is not None:
            if var_type == "string":
                return f'"{initial}"'
            elif var_type in ["long", "integer", "decimal", "real"]:
                return str(initial)
            elif var_type == "boolean":
                return "true" if initial else "false"
            else:
                return str(initial)
        
        # Default values
        type_defaults = {
            "string": '""',
            "long": "0",
            "integer": "0",
            "decimal": "0.0",
            "real": "0.0",
            "boolean": "false",
            "date": "DateTime.now()",
            "time": "TimeOfDay.now()",
            "datetime": "DateTime.now()",
        }
        
        if var_type.endswith("[]"):
            return "[]"
        
        return type_defaults.get(var_type, "null")

    def _format_params(self, params: list) -> str:
        """Format method parameters for Dart."""
        if not params:
            return ""
        
        formatted = []
        for param in params:
            param_type = self._convert_pb_type(param.get("type", "any"))
            param_name = self._to_camel_case(param.get("name", ""))
            
            if param.get("optional", False):
                formatted.append(f"{param_type}? {param_name}")
            else:
                formatted.append(f"{param_type} {param_name}")
        
        return ", ".join(formatted)

    def _is_async_method(self, method: dict) -> bool:
        """Check if method should be async."""
        body = method.get("body", "")
        return any(keyword in body for keyword in ["await", "async", ".then(", "Future"])

    def _convert_method_body(self, method: dict) -> str:
        """Convert method body to Dart."""
        # This is a simplified conversion - in practice would need full AST translation
        body = method.get("body", "// TODO: Implement method")
        # Add basic conversions
        body = body.replace("this.", "")
        body = body.replace("NULL", "null")
        body = body.replace("TRUE", "true")
        body = body.replace("FALSE", "false")
        return body

    def _extract_form_fields(self, controls: list) -> list:
        """Extract form fields from controls."""
        form_fields = []
        
        for control in controls:
            if control.get("type") in ["singlelineedit", "multilineedit", "editmask"]:
                field = {
                    "name": self._to_camel_case(control.get("name", "")),
                    "type": "text",
                    "label": control.get("properties", {}).get("text", control.get("name", "")),
                    "required": control.get("properties", {}).get("required", False),
                    "validation": control.get("properties", {}).get("validation", None),
                }
                
                if control.get("type") == "multilineedit":
                    field["type"] = "textarea"
                elif control.get("properties", {}).get("password", False):
                    field["type"] = "password"
                
                form_fields.append(field)
        
        return form_fields

    def _extract_init_code(self, window_model: dict) -> str:
        """Extract initialization code from constructor/open event."""
        # Look for constructor or open event
        for event in window_model.get("events", []):
            if event.get("name") == "open" or event.get("name") == "constructor":
                return self._convert_event_body(event)
        
        return ""

    def _extract_dispose_code(self, focus_nodes: list) -> str:
        """Generate dispose code for resources."""
        if not focus_nodes:
            return ""
        
        dispose_parts = []
        for node in focus_nodes:
            dispose_parts.append(f"{node}.dispose();")
        
        return "\n    ".join(dispose_parts)

    def _process_datawindows(self, datawindows: list) -> list:
        """Process DataWindow definitions."""
        processed = []
        
        for dw in datawindows:
            processed.append({
                "name": dw.get("name", ""),
                "sql": dw.get("sql", ""),
                "columns": dw.get("columns", []),
                "update_properties": dw.get("update_properties", {}),
                "presentation": dw.get("presentation", {}),
            })
        
        return processed

    def _get_text_style(self, control: dict) -> str:
        """Get Flutter TextStyle from control properties."""
        # This would map PowerBuilder font properties to Flutter TextStyle
        return "Theme.of(context).textTheme.bodyMedium"

    def _format_event_params(self, params: list) -> str:
        """Format event parameters."""
        return self._format_params(params)

    def _convert_event_body(self, event: dict) -> str:
        """Convert event body to Dart."""
        return self._convert_method_body(event)

    def _generate_event_handlers_mixin(self, screen_name: str, handlers: list) -> None:
        """Generate mixin with event handlers."""
        context = {
            "screen_name": screen_name,
            "handlers": handlers,
        }
        
        content = self.render_template("flutter/event_handlers.dart.jinja2", context)
        self.write_file(f"mixins/{self._to_snake_case(screen_name)}_event_handlers.dart", content)

    def _needs_state_management(self, screen_data: dict) -> bool:
        """Check if screen needs state management."""
        return any([
            screen_data.get("has_form"),
            screen_data.get("has_datawindows"),
            len(screen_data.get("instance_variables", [])) > 0,
            len(screen_data.get("event_handlers", [])) > 0,
        ])

    def _generate_state_provider(self, screen_name: str, model: dict) -> None:
        """Generate state provider for screen."""
        context = {
            "screen_name": screen_name,
            "instance_variables": model.get("instance_variables", []),
            "methods": self._convert_methods(model.get("methods", [])),
            "datawindows": model.get("datawindows", []),
        }
        
        content = self.render_template("flutter/state_provider.dart.jinja2", context)
        self.write_file(f"providers/{self._to_snake_case(screen_name)}_provider.dart", content)

    def _generate_simple_layout(self, controls: list) -> str:
        """Generate simple layout code."""
        # This would use LayoutConverter to create proper Flutter layout
        return "Column(children: [])"

    def generate_screen(
        self, screen_name: str, controls: list[dict[str, Any]], events: list[dict[str, Any]] | None = None, ) -> None:
        """Generate a Flutter screen.

        Args:
            screen_name: Name of the screen
            controls: List of UI controls
            events: Optional list of event handlers
        """
        context = {
            "screen_name": screen_name,
            "controls": controls,
            "events": events or [],
        }
        content = self.render_template("flutter/screen.dart.jinja2", context)
        self.write_file(f"screens/{screen_name.lower()}_screen.dart", content)

    def generate_model(
        self, model_name: str, properties: dict[str, Any]
    ) -> None:
        """Generate a Dart model class.

        Args:
            model_name: Name of the model
            properties: Model properties and types
        """
        context = {"model_name": model_name, "properties": properties}
        content = self.render_template("flutter/model.dart.jinja2", context)
        self.write_file(f"models/{model_name.lower()}.dart", content)

    def generate_datawindow_widget(
        self, name: str, datawindow: dict[str, Any]
    ) -> None:
        """Generate a DataWindow widget.

        Args:
            name: Widget name
            datawindow: DataWindow definition
        """
        context = {"name": name, "datawindow": datawindow}
        content = self.render_template("flutter/datawindow_widget.dart.jinja2", context)
        self.write_file(f"widgets/{name.lower()}_datawindow.dart", content)

    def _generate_screen_from_model_old(self, window_model: dict) -> None:
        """Generate Flutter screen from window model (old method for compatibility)."""
        screen_name = window_model.get("name", "UnknownScreen")
        
        # Build screen context
        context = {
            "screen_name": screen_name,
            "title": window_model.get("title", screen_name),
            "controls": window_model.get("controls", []),
            "events": window_model.get("events", []),
            "instance_variables": window_model.get("instance_variables", []),
            "methods": window_model.get("methods", []),
            "imports": self._generate_imports(window_model),
        }
        
        # Process menu if present
        if window_model.get("menu"):
            context["has_menu"] = True
            context["menu_items"] = self._extract_menu_items(window_model["menu"])
        
        # Check if screen needs state management
        context["needs_state"] = (
            len(context["instance_variables"]) > 0
            or len(context["events"]) > 0
            or any(m.get("modifies_state") for m in context["methods"])
        )
        
        # Generate screen file
        content = self.render_template("flutter/screen.dart.jinja2", context)
        output_path = f"screens/{self._to_snake_case(screen_name)}_screen.dart"
        self.write_file(output_path, content)
        
        self.generated_screens.append(screen_name)

    def _build_screen_body(self, controls: list, wirings: list = None) -> str:
        """Build screen body with proper layout."""
        if not controls:
            return "Center(child: Text('No controls defined'))"
        
        # Group controls by container/position
        layout_tree = self._analyze_layout(controls)
        
        # Generate Flutter widget tree
        return self._generate_widget_tree(layout_tree, wirings)

    def _extract_menu_items(self, menu_data: dict) -> list:
        """Extract menu items from menu definition."""
        items = []
        
        def extract_item(item_data: dict, parent_path: str = "") -> None:
            item = {
                "text": item_data.get("text", ""),
                "name": item_data.get("name", ""),
                "enabled": item_data.get("enabled", True),
                "checked": item_data.get("checked", False),
                "action": f"_on{item_data.get('name', '').capitalize()}Click",
            }
            
            # Add keyboard shortcut if defined
            if item_data.get("shortcut"):
                item["shortcut"] = item_data["shortcut"]
            
            items.append(item)
            
            # Process sub-items
            for sub_item in item_data.get("items", []):
                extract_item(sub_item, f"{parent_path}/{item['name']}")
        
        # Process top-level menu items
        for menu_item in menu_data.get("items", []):
            extract_item(menu_item)
        
        return items

    def _extract_menu_actions(self, menu_data: dict | None) -> list:
        """Extract menu actions for app bar."""
        if not menu_data:
            return []
        
        actions = []
        
        # Process menu items to find top-level actions
        for item in menu_data.get("items", []):
            if item.get("visible", True) and not item.get("items"):
                # This is a top-level action item
                action = {
                    "icon": self._get_menu_icon(item),
                    "tooltip": item.get("tooltip", item.get("text", "")),
                    "on_pressed": f"_on{item.get('name', '').capitalize()}Click",
                }
                actions.append(action)
        
        return actions[:3]  # Limit to 3 actions in app bar

    def _extract_menu_callbacks(self, menu_data: dict | None) -> list:
        """Extract all menu callbacks that need to be implemented."""
        if not menu_data:
            return []
        
        callbacks = []
        
        def extract_callbacks(items: list) -> None:
            for item in items:
                if item.get("name"):
                    callback = {
                        "name": f"_on{item['name'].capitalize()}Click",
                        "async": False,  # Could be determined from event analysis
                        "body": f"// TODO: Implement {item.get('text', item['name'])} action",
                    }
                    callbacks.append(callback)
                
                # Recurse into sub-items
                if item.get("items"):
                    extract_callbacks(item["items"])
        
        extract_callbacks(menu_data.get("items", []))
        return callbacks

    def _get_menu_icon(self, menu_item: dict) -> str:
        """Get appropriate icon for menu item."""
        name = menu_item.get("name", "").lower()
        text = menu_item.get("text", "").lower()
        
        # Common menu item to icon mappings
        icon_map = {
            "save": "Icons.save",
            "open": "Icons.folder_open",
            "new": "Icons.add",
            "delete": "Icons.delete",
            "print": "Icons.print",
            "refresh": "Icons.refresh",
            "settings": "Icons.settings",
            "help": "Icons.help",
            "search": "Icons.search",
            "edit": "Icons.edit",
        }
        
        for key, icon in icon_map.items():
            if key in name or key in text:
                return icon
        
        return "Icons.more_vert"

    def _flatten_menu_items(self, items: list) -> list:
        """Flatten hierarchical menu structure."""
        flat_items = []
        
        def flatten(item: dict, level: int = 0) -> None:
            flat_item = {**item, "level": level}
            flat_items.append(flat_item)
            
            for sub_item in item.get("items", []):
                flatten(sub_item, level + 1)
        
        for item in items:
            flatten(item)
        
        return flat_items

    def _reconstruct_menu_items(self, items: list) -> list:
        """Reconstruct hierarchical menu from flat list."""
        if not self.menu_converter:
            from src.generate.converters.flutter.ui.menu_converter import MenuConverter
            self.menu_converter = MenuConverter()
        
        return self.menu_converter.convert_menu_items(items)

    def _extract_toolbar_actions(self, controls: list) -> list:
        """Extract toolbar actions from controls."""
        actions = []
        
        # Look for toolbar buttons
        for control in controls:
            if control.get("type") == "picturebutton" or (
                control.get("type") == "commandbutton" 
                and control.get("properties", {}).get("toolbar", False)
            ):
                action = {
                    "icon": self._determine_action_icon(control),
                    "tooltip": control.get("properties", {}).get("tooltip", control.get("text", "")),
                    "on_pressed": f"_on{control['name'].capitalize()}Click",
                }
                actions.append(action)
        
        return actions

    def _determine_action_icon(self, control: dict) -> str:
        """Determine icon for toolbar action."""
        # Check for explicit icon property
        if control.get("properties", {}).get("icon"):
            return f"Icons.{control['properties']['icon']}"
        
        # Infer from name or text
        name = control.get("name", "").lower()
        text = control.get("text", "").lower()
        
        icon_map = {
            "save": "Icons.save",
            "delete": "Icons.delete",
            "add": "Icons.add",
            "edit": "Icons.edit",
            "refresh": "Icons.refresh",
            "print": "Icons.print",
        }
        
        for key, icon in icon_map.items():
            if key in name or key in text:
                return icon
        
        return "Icons.circle"

    def _extract_service_dependencies(self, window_model: dict) -> list:
        """Extract service dependencies from window model."""
        dependencies = []
        
        # Check for database operations
        if any(dw.get("update_properties") for dw in window_model.get("datawindows", [])):
            dependencies.append("DatabaseService")
        
        # Check for specific service calls in methods/events
        for method in window_model.get("methods", []):
            body = method.get("body", "")
            if "http" in body.lower() or "api" in body.lower():
                dependencies.append("ApiService")
            if "auth" in body.lower() or "login" in body.lower():
                dependencies.append("AuthService")
        
        # Check instance variables for service references
        for var in window_model.get("instance_variables", []):
            if "service" in var.get("type", "").lower():
                dependencies.append(var["type"])
        
        return list(set(dependencies))  # Remove duplicates

    def _convert_methods(self, methods: list) -> list:
        """Convert PowerBuilder methods to Dart methods."""
        converted = []
        
        for method in methods:
            converted_method = {
                "name": self._to_camel_case(method.get("name", "")),
                "return_type": self._convert_pb_type_to_dart(method.get("return_type", "void")),
                "params": self._format_params(method.get("parameters", [])),
                "async": self._is_async_method(method),
                "body": self._convert_method_body(method),
                "visibility": method.get("access", "private"),
            }
            converted.append(converted_method)
        
        return converted

    def _convert_pb_type_to_dart(self, pb_type: str) -> str:
        """Convert PowerBuilder type to Dart type (alias for consistency)."""
        return self._convert_pb_type(pb_type)

    def _convert_method_body(self, method: dict) -> str:
        """Convert PowerBuilder method body to Dart."""
        body = method.get("body", "")
        
        if not body:
            return "// TODO: Implement method"
        
        # Basic conversions (this would be much more complex in reality)
        conversions = {
            "this.": "",
            "NULL": "null",
            "TRUE": "true",
            "FALSE": "false",
            "MessageBox": "showDialog",
            "Return": "return",
            "IF": "if",
            "THEN": "{",
            "END IF": "}",
            "ELSE": "} else {",
        }
        
        for old, new in conversions.items():
            body = body.replace(old, new)
        
        return body

    def _extract_load_data_code(self, window_model: dict) -> str | None:
        """Extract data loading code from window model."""
        # Look for retrieve operations in open event
        for event in window_model.get("events", []):
            if event.get("name") == "open":
                body = event.get("body", "")
                if "retrieve" in body.lower():
                    return self._convert_event_body(event)
        
        # Check for datawindow retrieve in methods
        for method in window_model.get("methods", []):
            if "retrieve" in method.get("name", "").lower():
                return f"await {self._to_camel_case(method['name'])}();"
        
        return None

    def _extract_init_code(self, window_model: dict) -> str | None:
        """Extract initialization code from constructor."""
        # Look for constructor or create event
        for event in window_model.get("events", []):
            if event.get("name") in ["constructor", "create"]:
                return self._convert_event_body(event)
        
        # Look for init method
        for method in window_model.get("methods", []):
            if method.get("name", "").lower() in ["init", "initialize"]:
                return f"{self._to_camel_case(method['name'])}();"
        
        # Generate default init code if we have form fields
        controls = window_model.get("controls", [])
        init_parts = []
        
        for control in controls:
            if control.get("type") == "singlelineedit":
                name = self._to_camel_case(control.get("name", ""))
                init_parts.append(f"_{name}Controller = TextEditingController();")
        
        return "\n    ".join(init_parts) if init_parts else None

    def generate_project_structure(self, app_info: dict) -> None:
        """Generate complete Flutter project structure."""
        # Create standard Flutter directories
        directories = [
            "lib/screens",
            "lib/widgets",
            "lib/models",
            "lib/services",
            "lib/providers",
            "lib/utils",
            "lib/constants",
        ]
        
        for directory in directories:
            Path(self.output_dir / directory).mkdir(parents=True, exist_ok=True)
        
        # Generate main.dart
        self._generate_main_dart(app_info)
        
        # Generate app.dart
        self._generate_app_dart(app_info)
        
        # Generate theme
        self._generate_theme(app_info)
        
        # Generate routes
        self._generate_routes()

    def _generate_main_dart(self, app_info: dict) -> None:
        """Generate main.dart file."""
        context = {
            "app_name": app_info.get("name", "PowerBuilderApp"),
            "uses_provider": any(s for s in self.generated_screens),
        }
        content = self.render_template("flutter/main.dart.jinja2", context)
        self.write_file("main.dart", content)

    def _generate_app_dart(self, app_info: dict) -> None:
        """Generate app.dart file."""
        context = {
            "app_name": app_info.get("name", "PowerBuilderApp"),
            "title": app_info.get("title", "PowerBuilder App"),
            "screens": self.generated_screens,
        }
        content = self.render_template("flutter/app.dart.jinja2", context)
        self.write_file("app.dart", content)

    def _generate_theme(self, app_info: dict) -> None:
        """Generate theme configuration."""
        context = {
            "primary_color": app_info.get("primary_color", "blue"),
            "accent_color": app_info.get("accent_color", "orange"),
        }
        content = self.render_template("flutter/theme.dart.jinja2", context)
        self.write_file("constants/theme.dart", content)

    def _generate_routes(self) -> None:
        """Generate routes configuration."""
        context = {"screens": self.generated_screens}
        content = self.render_template("flutter/routes.dart.jinja2", context)
        self.write_file("constants/routes.dart", content)

    def _to_camel_case(self, name: str) -> str:
        """Convert name to camelCase."""
        parts = name.split("_")
        if len(parts) == 1:
            return parts[0].lower()
        
        return parts[0].lower() + "".join(p.capitalize() for p in parts[1:])

    def _to_snake_case(self, name: str) -> str:
        """Convert name to snake_case."""
        import re
        name = re.sub(r"([A-Z]+)([A-Z][a-z])", r"\1_\2", name)
        name = re.sub(r"([a-z\d])([A-Z])", r"\1_\2", name)
        return name.lower()

    def _generate_imports(self, data: dict) -> list:
        """Generate import statements based on screen data."""
        imports = ["package:flutter/material.dart"]
        
        if data.get("has_form"):
            imports.append("package:flutter/services.dart")
        
        if data.get("has_datawindows"):
            imports.append("package:provider/provider.dart")
        
        if data.get("service_dependencies"):
            for service in data["service_dependencies"]:
                imports.append(f"../services/{self._to_snake_case(service)}.dart")
        
        return imports

    def _analyze_layout(self, controls: list) -> dict:
        """Analyze control positions to determine layout structure."""
        # This would use LayoutConverter to analyze control positions
        # and create a hierarchical layout structure
        return {"type": "column", "children": controls}

    def _generate_widget_tree(self, layout_tree: dict, wirings: list = None) -> str:
        """Generate Flutter widget tree from layout analysis."""
        # This would recursively build the widget tree
        # based on the layout structure
        return "Container()"

    def _extract_dispose_code(self, focus_nodes: list) -> str | None:
        """Generate dispose code for focus nodes.

        Args:
            focus_nodes: List of focus node names

        Returns:
            Dispose code or None
        """
        if not focus_nodes:
            return None

        dispose_parts = []
        for node in focus_nodes:
            dispose_parts.append(f"{node}.dispose();")

        return "\n    ".join(dispose_parts)