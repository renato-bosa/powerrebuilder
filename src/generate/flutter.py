"""Flutter generator for creating Flutter/Dart UI from PowerBuilder definitions."""

import logging
import re
from pathlib import Path
from typing import Any, cast

from .base import CodeGenerator

logger = logging.getLogger(__name__)


class FlutterGenerator(CodeGenerator):
    """Generate Flutter widgets and screens from PowerBuilder UI."""

    def __init__(
        self, template_dir: str, output_dir: str, validate_templates: bool = True
    ) -> None:
        """Initialize Flutter generator.

        Args:
            template_dir: Directory containing templates
            output_dir: Directory for generated code
            validate_templates: Whether to validate templates before rendering
        """
        super().__init__(template_dir, output_dir, validate_templates)
        self.generated_screens: Any = []
        self.generated_widgets: Any = []
        self.generated_models: Any = []
        self.generated_services: Any = []
        self.layout_converter: Any = None
        self.event_converter: Any = None
        self.menu_converter: Any = None

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
        content = self.render_template(
            f"flutter/{widget_type}_widget.dart.jinja2", context
        )
        self.write_file(f"widgets/{widget_name.lower()}_widget.dart", content)
        self.generated_widgets.append(widget_name)

    def generate_screen_from_model(self, window_model: dict[str, Any]) -> dict[str, Any]:
        """Generate a Flutter screen from a window model."""
        screen_name = window_model.get("name", "UnknownScreen")

        # Enhanced data extraction from model
        extracted_data = self._extract_enhanced_screen_data(window_model)

        # Generate lifecycle methods
        lifecycle_methods = self._generate_widget_lifecycle_methods(extracted_data)

        # Generate theme and styling
        theme_config = self._generate_theme_and_styling(extracted_data)

        # Determine if we need a separate state class
        needs_state_class = self._should_generate_state_class(extracted_data)

        # Generate main screen file
        context = {
            **extracted_data,
            "screen_name": screen_name,
            "imports": self._generate_imports(extracted_data),
            "state_management": self._needs_state_management(extracted_data),
            "needs_state_class": needs_state_class,
            "lifecycle_methods": lifecycle_methods,
            "theme_config": theme_config,
            "is_stateful": bool(lifecycle_methods)
            or self._needs_state_management(extracted_data),
        }

        # Select appropriate template based on complexity
        template_name = (
            "flutter/screen_enhanced.dart.jinja2"
            if needs_state_class
            else "flutter/screen.dart.jinja2"
        )

        # Generate the main screen
        content = self.render_template(template_name, context)
        output_path = f"screens/{self._to_snake_case(screen_name)}_screen.dart"
        self.write_file(output_path, content)

        # Generate event handlers mixin if needed
        if (
            extracted_data["event_handlers"]
            and len(extracted_data["event_handlers"]) > 3
        ):
            self._generate_event_handlers_mixin(
                screen_name, extracted_data["event_handlers"]
            )

        # Generate state provider if needed
        if needs_state_class or self._needs_state_management(extracted_data):
            self._generate_state_provider(screen_name, window_model)

        # Generate separate theme file if there are many custom styles
        if len(theme_config.get("custom_colors", {})) > 5:
            self._generate_screen_theme(screen_name, theme_config)

        self.generated_screens.append(screen_name)

        return {
            "screen": screen_name,
            "file": output_path,
            "has_state": self._needs_state_management(extracted_data),
            "has_state_class": needs_state_class,
            "dependencies": extracted_data.get("service_dependencies", []),
            "generated_files": self._get_generated_files_for_screen(
                screen_name, extracted_data
            ),
        }

    def _extract_enhanced_screen_data(self, window_model: dict[str, Any]) -> dict[str, Any]:
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
        focus_nodes = [
            f"{self._to_camel_case(f['name'])}Focus"
            for f in form_fields
            if f.get("type") in ["text", "number", "textarea"]
        ]

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

    def _process_controls_enhanced(self, controls: list[Any]) -> list[dict[str, Any]]:
        """Process controls with enhanced layout and styling."""
        if not self.layout_converter:
            from src.generate.converters.flutter.layouts import LayoutConverter

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
                ctrl_data["controller"] = (
                    f"_{self._to_camel_case(control['name'])}Controller"
                )
                ctrl_data["hint_text"] = control.get("properties", {}).get("hint", "")

            processed.append(ctrl_data)

        result = self.layout_converter.convert_layout(processed)
        return cast(list[dict[str, Any]], result)

    def _process_events_enhanced(self, events: list[Any], controls: list[Any]) -> dict[str, Any]:
        """Process events into handlers and listeners."""
        if not self.event_converter:
            from src.generate.converters.flutter.events import EventConverter

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

        return {"handlers": handlers, "listeners": listeners}

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

    def _get_initial_value(self, var: dict[str, Any]) -> str:
        """Get Dart initial value for a variable."""
        var_type = var.get("type", "any")
        initial = var.get("initial_value")

        if initial is not None:
            if var_type == "string":
                return f'"{initial}"'
            if var_type in ["long", "integer", "decimal", "real"]:
                return str(initial)
            if var_type == "boolean":
                return "true" if initial else "false"
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

    def _format_params(self, params: list[Any]) -> str:
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

    def _is_async_method(self, method: dict[str, Any]) -> bool:
        """Check if method should be async."""
        body = method.get("body", "")
        return any(
            keyword in body for keyword in ["await", "async", ".then(", "Future"]
        )

    def _convert_method_body(self, method: dict[str, Any]) -> str:
        """Convert method body to Dart."""
        # This is a simplified conversion - in practice would need full AST translation
        body = str(method.get("body", "// TODO: Implement method"))
        # Add basic conversions
        body = body.replace("this.", "")
        body = body.replace("NULL", "null")
        body = body.replace("TRUE", "true")
        return body.replace("FALSE", "false")

    def _extract_form_fields(self, controls: list[Any]) -> list[dict[str, Any]]:
        """Extract form fields from controls."""
        form_fields = []

        for control in controls:
            if control.get("type") in ["singlelineedit", "multilineedit", "editmask"]:
                field = {
                    "name": self._to_camel_case(control.get("name", "")),
                    "type": "text",
                    "label": control.get("properties", {}).get(
                        "text", control.get("name", "")
                    ),
                    "required": control.get("properties", {}).get("required", False),
                    "validation": control.get("properties", {}).get("validation", None),
                }

                if control.get("type") == "multilineedit":
                    field["type"] = "textarea"
                elif control.get("properties", {}).get("password", False):
                    field["type"] = "password"

                form_fields.append(field)

        return form_fields

    def _extract_init_code(self, window_model: dict[str, Any]) -> str:
        """Extract initialization code from constructor/open event."""
        # Look for constructor or open event
        for event in window_model.get("events", []):
            if event.get("name") == "open" or event.get("name") == "constructor":
                return self._convert_event_body(event)

        return ""

    def _extract_dispose_code(self, focus_nodes: list[Any]) -> str:
        """Generate dispose code for resources."""
        if not focus_nodes:
            return ""

        dispose_parts = []
        for node in focus_nodes:
            dispose_parts.append(f"{node}.dispose();")

        return "\n    ".join(dispose_parts)

    def _process_datawindows(self, datawindows: list[Any]) -> list[dict[str, Any]]:
        """Process DataWindow definitions."""
        processed = []

        for dw in datawindows:
            processed.append(
                {
                    "name": dw.get("name", ""),
                    "sql": dw.get("sql", ""),
                    "columns": dw.get("columns", []),
                    "update_properties": dw.get("update_properties", {}),
                    "presentation": dw.get("presentation", {}),
                }
            )

        return processed

    def _get_text_style(self, _control: Any) -> str:
        """Get Flutter TextStyle from control properties."""
        # This would map PowerBuilder font properties to Flutter TextStyle
        return "Theme.of(context).textTheme.bodyMedium"

    def _format_event_params(self, params: list[Any]) -> str:
        """Format event parameters."""
        return self._format_params(params)

    def _convert_event_body(self, event: dict[str, Any]) -> str:
        """Convert event body to Dart."""
        return self._convert_method_body(event)

    def _generate_event_handlers_mixin(
        self, screen_name: str, handlers: list[Any]
    ) -> None:
        """Generate mixin with event handlers."""
        context = {
            "screen_name": screen_name,
            "handlers": handlers,
        }

        content = self.render_template("flutter/event_handlers.dart.jinja2", context)
        self.write_file(
            f"mixins/{self._to_snake_case(screen_name)}_event_handlers.dart", content
        )

    def _needs_state_management(self, screen_data: dict[str, Any]) -> bool:
        """Check if screen needs state management."""
        return any(
            [
                screen_data.get("has_form"),
                screen_data.get("has_datawindows"),
                len(screen_data.get("instance_variables", [])) > 0,
                len(screen_data.get("event_handlers", [])) > 0,
            ]
        )

    def _generate_state_provider(self, screen_name: str, model: dict[str, Any]) -> None:
        """Generate state provider for screen."""
        context = {
            "screen_name": screen_name,
            "instance_variables": model.get("instance_variables", []),
            "methods": self._convert_methods(model.get("methods", [])),
            "datawindows": model.get("datawindows", []),
        }

        content = self.render_template("flutter/state_provider.dart.jinja2", context)
        self.write_file(
            f"providers/{self._to_snake_case(screen_name)}_provider.dart", content
        )

    def _generate_simple_layout(self, _controls: Any) -> str:
        """Generate simple layout code."""
        # This would use LayoutConverter to create proper Flutter layout
        return "Column(children: [])"

    def generate_screen(
        self,
        screen_name: str,
        controls: list[dict[str, Any]],
        events: list[dict[str, Any]] | None = None,
    ) -> None:
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

    def generate_model(self, model_name: str, properties: dict[str, Any]) -> None:
        """Generate a Dart model class.

        Args:
            model_name: Name of the model
            properties: Model properties and types
        """
        context = {"model_name": model_name, "properties": properties}
        content = self.render_template("flutter/model.dart.jinja2", context)
        self.write_file(f"models/{model_name.lower()}.dart", content)

    def generate_datawindow_widget(self, name: str, datawindow: dict[str, Any]) -> None:
        """Generate a DataWindow widget.

        Args:
            name: Widget name
            datawindow: DataWindow definition
        """
        context = {"name": name, "datawindow": datawindow}
        content = self.render_template("flutter/datawindow_widget.dart.jinja2", context)
        self.write_file(f"widgets/{name.lower()}_datawindow.dart", content)

    def _generate_screen_from_model_old(self, window_model: dict[str, Any]) -> None:
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

    def _build_screen_body(
        self, controls: list[Any], wirings: list[Any] | None = None
    ) -> str:
        """Build screen body with proper layout."""
        if not controls:
            return "Center(child: Text('No controls defined'))"

        # Group controls by container/position
        layout_tree = self._analyze_layout(controls)

        # Generate Flutter widget tree
        return self._generate_widget_tree(layout_tree, wirings)

    def _extract_menu_items(self, menu_data: dict[str, Any]) -> list[dict[str, Any]]:
        """Extract menu items from menu definition."""
        items = []

        def extract_item(item_data: dict[str, Any], parent_path: str = "") -> None:
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

    def _extract_menu_actions(self, menu_data: dict[str, Any] | None) -> list[dict[str, Any]]:
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

    def _extract_menu_callbacks(self, menu_data: dict[str, Any] | None) -> list[dict[str, Any]]:
        """Extract all menu callbacks that need to be implemented."""
        if not menu_data:
            return []

        callbacks = []

        def extract_callbacks(items: list[Any]) -> None:
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

    def _get_menu_icon(self, menu_item: dict[str, Any]) -> str:
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

    def _flatten_menu_items(self, items: list[Any]) -> list[dict[str, Any]]:
        """Flatten hierarchical menu structure."""
        flat_items = []

        def flatten(item: dict[str, Any], level: int = 0) -> None:
            flat_item = {**item, "level": level}
            flat_items.append(flat_item)

            for sub_item in item.get("items", []):
                flatten(sub_item, level + 1)

        for item in items:
            flatten(item)

        return flat_items

    def _reconstruct_menu_items(self, items: list[Any]) -> list[dict[str, Any]]:
        """Reconstruct hierarchical menu from flat list."""
        if not self.menu_converter:
            from src.generate.converters.flutter.menus import MenuConverter

            self.menu_converter = MenuConverter()

        result = self.menu_converter.convert_menu_items(items)
        return cast(list[dict[str, Any]], result)

    def _extract_toolbar_actions(self, controls: list[Any]) -> list[dict[str, Any]]:
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
                    "tooltip": control.get("properties", {}).get(
                        "tooltip", control.get("text", "")
                    ),
                    "on_pressed": f"_on{control['name'].capitalize()}Click",
                }
                actions.append(action)

        return actions

    def _determine_action_icon(self, control: dict[str, Any]) -> str:
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

    def _extract_service_dependencies(self, window_model: dict[str, Any]) -> list[str]:
        """Extract service dependencies from window model."""
        dependencies = []

        # Check for database operations
        if any(
            dw.get("update_properties") for dw in window_model.get("datawindows", [])
        ):
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

    def _convert_methods(self, methods: list[Any]) -> list[dict[str, Any]]:
        """Convert PowerBuilder methods to Dart methods."""
        converted = []

        for method in methods:
            converted_method = {
                "name": self._to_camel_case(method.get("name", "")),
                "return_type": self._convert_pb_type_to_dart(
                    method.get("return_type", "void")
                ),
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


    def _extract_load_data_code(self, window_model: dict[str, Any]) -> str | None:
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

    # Duplicate method removed - already defined above

    def generate_project_structure(self, app_info: dict[str, Any]) -> None:
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

    def _generate_main_dart(self, app_info: dict[str, Any]) -> None:
        """Generate main.dart file."""
        context = {
            "app_name": app_info.get("name", "PowerBuilderApp"),
            "uses_provider": any(s for s in self.generated_screens),
        }
        content = self.render_template("flutter/main.dart.jinja2", context)
        self.write_file("main.dart", content)

    def _generate_app_dart(self, app_info: dict[str, Any]) -> None:
        """Generate app.dart file."""
        context = {
            "app_name": app_info.get("name", "PowerBuilderApp"),
            "title": app_info.get("title", "PowerBuilder App"),
            "screens": self.generated_screens,
        }
        content = self.render_template("flutter/app.dart.jinja2", context)
        self.write_file("app.dart", content)

    def _generate_theme(self, app_info: dict[str, Any]) -> None:
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
        name = re.sub(r"([A-Z]+)([A-Z][a-z])", r"\1_\2", name)
        name = re.sub(r"([a-z\d])([A-Z])", r"\1_\2", name)
        return name.lower()

    def _generate_imports(self, data: dict[str, Any]) -> list[str]:
        """Generate import statements based on screen data."""
        imports = ["package:flutter/material.dart"]

        # Form handling imports
        if data.get("has_form"):
            imports.extend(
                [
                    "package:flutter/services.dart",
                    "package:flutter_form_builder/flutter_form_builder.dart",
                    "package:form_builder_validators/form_builder_validators.dart",
                ]
            )

        # State management imports
        if data.get("has_datawindows") or self._needs_state_management(data):
            imports.append("package:provider/provider.dart")

        # Async operations
        if data.get("event_handlers") or data.get("service_dependencies"):
            imports.append("dart:async")

        # HTTP/API imports
        if any("api" in dep.lower() for dep in data.get("service_dependencies", [])):
            imports.append("package:dio/dio.dart")

        # DataWindow specific imports
        if data.get("has_datawindows"):
            imports.extend(
                [
                    "../widgets/datawindow_widget.dart",
                    "../models/datawindow_model.dart",
                ]
            )

        # Menu imports
        if data.get("has_menu"):
            imports.append("../widgets/menu_drawer.dart")

        # Service dependencies
        if data.get("service_dependencies"):
            for service in data["service_dependencies"]:
                imports.append(f"../services/{self._to_snake_case(service)}.dart")

        # Model imports
        for control in data.get("controls", []):
            if control.get("type") == "datawindow" and control.get("model"):
                imports.append(
                    f"../models/{self._to_snake_case(control['model'])}.dart"
                )

        # Utility imports
        if data.get("form_fields"):
            imports.append("../utils/validators.dart")

        # Theme imports
        imports.append("../constants/theme.dart")

        # Remove duplicates while preserving order
        seen = set()
        unique_imports = []
        for imp in imports:
            if imp not in seen:
                seen.add(imp)
                unique_imports.append(imp)

        return unique_imports

    def _analyze_layout(self, controls: list[Any]) -> dict[str, Any]:
        """Analyze control positions to determine layout structure."""
        # This would use LayoutConverter to analyze control positions
        # and create a hierarchical layout structure
        return {"type": "column", "children": controls}

    def _generate_widget_tree(
        self, _layout_tree: dict[str, Any], _wirings: dict[str, Any] | None = None
    ) -> str:
        """Generate Flutter widget tree from layout analysis."""
        # This would recursively build the widget tree
        # based on the layout structure
        return "Container()"

    # Duplicate method removed - already defined above

    def _should_generate_state_class(self, screen_data: dict[str, Any]) -> bool:
        """Determine if a separate state class should be generated.

        Args:
            screen_data: Extracted screen data

        Returns:
            True if state class is needed
        """
        # Check for complex state requirements
        complex_state_indicators = [
            # Has multiple form fields that need validation
            len(screen_data.get("form_fields", [])) > 3,
            # Has datawindows that require data management
            len(screen_data.get("datawindows", [])) > 0,
            # Has async operations in event handlers
            any(
                handler.get("async", False)
                for handler in screen_data.get("event_handlers", [])
            ),
            # Has multiple instance variables to track
            len(screen_data.get("instance_variables", [])) > 5,
            # Has complex business logic methods
            any(
                len(method.get("body", "").split("\n")) > 10
                for method in screen_data.get("methods", [])
            ),
            # Has service dependencies that need lifecycle management
            len(screen_data.get("service_dependencies", [])) > 2,
            # Has timer or periodic updates
            any(
                "timer" in str(handler.get("body", "")).lower()
                or "periodic" in str(handler.get("body", "")).lower()
                for handler in screen_data.get("event_handlers", [])
            ),
            # Has data that needs to be shared between widgets
            any(
                var.get("scope") == "shared"
                for var in screen_data.get("instance_variables", [])
            ),
        ]

        # Generate state class if 2 or more indicators are true
        return sum(complex_state_indicators) >= 2

    def _generate_widget_lifecycle_methods(
        self, screen_data: dict[str, Any]
    ) -> dict[str, str]:
        """Generate widget lifecycle methods based on screen requirements.

        Args:
            screen_data: Extracted screen data

        Returns:
            Dictionary of lifecycle methods with their implementations
        """
        methods = {}

        # initState method
        init_parts = []

        # Initialize controllers
        for field in screen_data.get("form_fields", []):
            if field.get("type") in ["text", "number", "textarea"]:
                init_parts.append(
                    f"_{field['name']}Controller = TextEditingController();"
                )

        # Initialize focus nodes
        for node in screen_data.get("focus_nodes", []):
            init_parts.append(f"{node} = FocusNode();")

        # Call initialization code
        if screen_data.get("init_code"):
            init_parts.append("")
            init_parts.append("// Custom initialization")
            init_parts.append(screen_data["init_code"])

        # Load initial data
        if screen_data.get("load_data_code"):
            init_parts.append("")
            init_parts.append("// Load initial data")
            init_parts.append("WidgetsBinding.instance.addPostFrameCallback((_) {")
            init_parts.append(f"  {screen_data['load_data_code']}")
            init_parts.append("});")

        if init_parts:
            methods["initState"] = "\n    ".join(
                [
                    "@override",
                    "void initState() {",
                    "  super.initState();",
                    "  " + "\n    ".join(init_parts),
                    "}",
                ]
            )

        # dispose method
        dispose_parts = []

        # Dispose controllers
        for field in screen_data.get("form_fields", []):
            if field.get("type") in ["text", "number", "textarea"]:
                dispose_parts.append(f"_{field['name']}Controller.dispose();")

        # Dispose focus nodes
        if screen_data.get("dispose_code"):
            dispose_parts.append(screen_data["dispose_code"])

        # Cancel timers/subscriptions
        for var in screen_data.get("instance_variables", []):
            if var.get("type") in ["Timer", "StreamSubscription"]:
                dispose_parts.append(f"_{var['name']}?.cancel();")

        if dispose_parts:
            methods["dispose"] = "\n    ".join(
                [
                    "@override",
                    "void dispose() {",
                    "  " + "\n    ".join(dispose_parts),
                    "  super.dispose();",
                    "}",
                ]
            )

        # didChangeDependencies method (if using inherited widgets or providers)
        if screen_data.get("service_dependencies") or screen_data.get(
            "has_datawindows"
        ):
            dep_parts = []

            for service in screen_data.get("service_dependencies", []):
                dep_parts.append(
                    f"_{self._to_camel_case(service)} = "
                    f"Provider.of<{service}>(context, listen: false);"
                )

            if dep_parts:
                methods["didChangeDependencies"] = "\n    ".join(
                    [
                        "@override",
                        "void didChangeDependencies() {",
                        "  super.didChangeDependencies();",
                        "  " + "\n    ".join(dep_parts),
                        "}",
                    ]
                )

        return methods

    def _generate_theme_and_styling(
        self, screen_data: dict[str, Any]
    ) -> dict[str, Any]:
        """Generate theme and styling configuration for the screen.

        Args:
            screen_data: Extracted screen data

        Returns:
            Theme and styling configuration
        """
        theme_config: dict[str, Any] = {
            "uses_theme": True,
            "custom_colors": {},
            "text_styles": {},
            "decorations": {},
        }

        # Extract custom colors from controls
        for control in screen_data.get("controls", []):
            props = control.get("properties", {})

            # Background colors
            if props.get("background_color"):
                color_name = f"{control['name']}BackgroundColor"
                theme_config["custom_colors"][color_name] = self._convert_color(
                    props["background_color"]
                )

            # Text colors
            if props.get("text_color"):
                color_name = f"{control['name']}TextColor"
                theme_config["custom_colors"][color_name] = self._convert_color(
                    props["text_color"]
                )

        # Generate text styles for different control types
        text_style_types = {
            "title": "Theme.of(context).textTheme.headlineMedium",
            "subtitle": "Theme.of(context).textTheme.titleMedium",
            "body": "Theme.of(context).textTheme.bodyLarge",
            "caption": "Theme.of(context).textTheme.bodySmall",
            "button": "Theme.of(context).textTheme.labelLarge",
        }

        for control in screen_data.get("controls", []):
            if control.get("type") in ["statictext", "text"]:
                style_type = self._determine_text_style_type(control)
                theme_config["text_styles"][control["name"]] = text_style_types.get(
                    style_type, text_style_types["body"]
                )

        # Generate input decorations for form fields
        for field in screen_data.get("form_fields", []):
            theme_config["decorations"][field["name"]] = {
                "labelText": field.get("label", field["name"]),
                "hintText": field.get("hint", ""),
                "helperText": field.get("helper", ""),
                "prefixIcon": self._get_field_icon(field),
                "border": "OutlineInputBorder()",
                "filled": True,
                "fillColor": "Theme.of(context).inputDecorationTheme.fillColor",
            }

        return theme_config

    def _convert_color(self, pb_color: str | int) -> str:
        """Convert PowerBuilder color to Flutter color."""
        if isinstance(pb_color, int):
            # Convert RGB integer to Flutter Color
            r = (pb_color >> 16) & 0xFF
            g = (pb_color >> 8) & 0xFF
            b = pb_color & 0xFF
            return f"Color.fromRGBO({r}, {g}, {b}, 1.0)"

        # Handle named colors
        color_map = {
            "black": "Colors.black",
            "white": "Colors.white",
            "red": "Colors.red",
            "green": "Colors.green",
            "blue": "Colors.blue",
            "yellow": "Colors.yellow",
            "transparent": "Colors.transparent",
        }

        return color_map.get(pb_color.lower(), "Theme.of(context).colorScheme.surface")

    def _determine_text_style_type(self, control: dict[str, Any]) -> str:
        """Determine text style type based on control properties."""
        props = control.get("properties", {})

        # Check font size
        font_size = props.get("font_size", 12)
        if font_size >= 20:
            return "title"
        if font_size >= 16:
            return "subtitle"
        if font_size <= 10:
            return "caption"

        # Check font weight
        if props.get("font_weight") in ["bold", "700"]:
            return "subtitle"

        # Check control name patterns
        name_lower = control.get("name", "").lower()
        if any(pattern in name_lower for pattern in ["title", "header", "heading"]):
            return "title"
        if any(pattern in name_lower for pattern in ["subtitle", "subheading"]):
            return "subtitle"
        if any(pattern in name_lower for pattern in ["caption", "note", "hint"]):
            return "caption"

        return "body"

    def _get_field_icon(self, field: dict[str, Any]) -> str | None:
        """Get appropriate icon for a form field."""
        field_type = field.get("type", "")
        field_name = field.get("name", "").lower()

        # Type-based icons
        if field_type == "password":
            return "Icons.lock"
        if field_type == "email":
            return "Icons.email"
        if field_type == "phone":
            return "Icons.phone"
        if field_type == "date":
            return "Icons.calendar_today"
        if field_type == "time":
            return "Icons.access_time"

        # Name-based icons
        icon_map = {
            "user": "Icons.person",
            "name": "Icons.person",
            "email": "Icons.email",
            "password": "Icons.lock",
            "phone": "Icons.phone",
            "address": "Icons.location_on",
            "search": "Icons.search",
            "date": "Icons.calendar_today",
            "time": "Icons.access_time",
            "amount": "Icons.attach_money",
            "price": "Icons.attach_money",
            "quantity": "Icons.format_list_numbered",
        }

        for key, icon in icon_map.items():
            if key in field_name:
                return icon

        return None

    def _generate_screen_theme(
        self, screen_name: str, theme_config: dict[str, Any]
    ) -> None:
        """Generate a separate theme file for the screen."""
        context = {"screen_name": screen_name, **theme_config}

        content = self.render_template("flutter/screen_theme.dart.jinja2", context)
        self.write_file(
            f"themes/{self._to_snake_case(screen_name)}_theme.dart", content
        )

    def _get_generated_files_for_screen(
        self, screen_name: str, screen_data: dict[str, Any]
    ) -> list[str]:
        """Get list of all files generated for a screen."""
        files = [f"screens/{self._to_snake_case(screen_name)}_screen.dart"]

        # Check for additional generated files
        if screen_data.get("event_handlers") and len(screen_data["event_handlers"]) > 3:
            files.append(
                f"mixins/{self._to_snake_case(screen_name)}_event_handlers.dart"
            )

        if self._needs_state_management(
            screen_data
        ) or self._should_generate_state_class(screen_data):
            files.append(f"providers/{self._to_snake_case(screen_name)}_provider.dart")

        # Check for custom theme file
        theme_config = self._generate_theme_and_styling(screen_data)
        if len(theme_config.get("custom_colors", {})) > 5:
            files.append(f"themes/{self._to_snake_case(screen_name)}_theme.dart")

        # Check for generated widgets
        for control in screen_data.get("controls", []):
            if control.get("type") == "datawindow":
                files.append(
                    f"widgets/{self._to_snake_case(control['name'])}_datawindow.dart"
                )

        return files
