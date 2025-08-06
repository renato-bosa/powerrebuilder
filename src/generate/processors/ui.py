"""UI processing service for code generation."""

import logging
from typing import Any

from src.contracts.interfaces import IUIProcessor

logger = logging.getLogger(__name__)


class UIProcessor(IUIProcessor):
    """Processes UI elements for code generation."""

    def __init__(self) -> None:
        """Initialize the UI processor."""
        self._layout_strategies = {
            "absolute": self._generate_absolute_layout,
            "grid": self._generate_grid_layout,
            "flow": self._generate_flow_layout,
            "responsive": self._generate_responsive_layout,
        }

    def process_controls(self, controls: list[dict[str, Any]]) -> list[dict[str, Any]]:
        """Process UI controls.

        Args:
            controls: List of controls

        Returns:
            Processed controls with additional metadata
        """
        processed = []

        for control in controls:
            processed_control = control.copy()

            # Add control metadata
            control_type = control.get("type", "unknown").lower()
            processed_control["widget_type"] = self._map_control_to_widget(control_type)
            processed_control["requires_state"] = self._requires_state(control_type)

            # Process properties
            if "properties" in control:
                processed_control["properties"] = self._process_properties(
                    control["properties"], control_type
                )

            # Process events
            if "events" in control:
                processed_control["events"] = self._process_events(control["events"])

            # Add layout hints
            processed_control["layout_hints"] = self._get_layout_hints(control)

            processed.append(processed_control)

        return processed

    def generate_layout(self, controls: list[dict[str, Any]]) -> dict[str, Any]:
        """Generate layout from controls.

        Args:
            controls: List of controls

        Returns:
            Layout structure
        """
        if not controls:
            return {"type": "empty", "children": []}

        # Analyze control positions to determine layout type
        layout_type = self._determine_layout_type(controls)

        # Generate layout based on type
        layout_generator = self._layout_strategies.get(
            layout_type, self._generate_absolute_layout
        )

        layout = layout_generator(controls)

        # Add responsive breakpoints if needed
        if layout_type == "responsive":
            layout["breakpoints"] = self._calculate_breakpoints(controls)

        return layout

    def extract_menus(self, window: dict[str, Any]) -> list[dict[str, Any]]:
        """Extract menus from window.

        Args:
            window: Window structure

        Returns:
            List of menus
        """
        menus = []

        # Check for menu property
        if "menu" in window:
            menu_data = window["menu"]
            if isinstance(menu_data, dict):
                menus.append(self._process_menu(menu_data))
            elif isinstance(menu_data, list):
                for menu_item in menu_data:
                    if isinstance(menu_item, dict):
                        menus.append(self._process_menu(menu_item))

        # Check for menu items in controls
        if "controls" in window:
            for control in window["controls"]:
                if control.get("type", "").lower() in [
                    "menu",
                    "menubar",
                    "popupmenu",
                ]:
                    menus.append(self._process_menu(control))

        # Check for toolbar actions that should be menu items
        if "toolbar" in window:
            toolbar_menu = self._extract_toolbar_menu(window["toolbar"])
            if toolbar_menu:
                menus.append(toolbar_menu)

        return menus

    # Private helper methods

    def _map_control_to_widget(self, control_type: str) -> str:
        """Map PowerBuilder control type to widget type."""
        mapping = {
            "commandbutton": "button",
            "statictext": "label",
            "singlelineedit": "textfield",
            "multilineedit": "textarea",
            "checkbox": "checkbox",
            "radiobutton": "radio",
            "dropdownlistbox": "dropdown",
            "listbox": "listbox",
            "groupbox": "container",
            "picture": "image",
            "datawindow": "datagrid",
            "tab": "tabs",
            "treeview": "tree",
            "picturebutton": "imagebutton",
            "datepicker": "datepicker",
            "monthcalendar": "calendar",
            "progressbar": "progressbar",
            "hscrollbar": "slider_horizontal",
            "vscrollbar": "slider_vertical",
            "line": "divider",
            "rectangle": "box",
            "roundrectangle": "rounded_box",
            "oval": "circle",
            "userobject": "custom_widget",
        }

        return mapping.get(control_type, "container")

    def _requires_state(self, control_type: str) -> bool:
        """Check if control type requires state management."""
        stateful_controls = {
            "singlelineedit",
            "multilineedit",
            "checkbox",
            "radiobutton",
            "dropdownlistbox",
            "listbox",
            "datawindow",
            "tab",
            "treeview",
            "datepicker",
            "monthcalendar",
            "progressbar",
            "hscrollbar",
            "vscrollbar",
        }

        return control_type in stateful_controls

    def _process_properties(
        self, properties: dict[str, Any], control_type: str
    ) -> dict[str, Any]:
        """Process control properties."""
        processed = {}

        # Map common properties
        property_mapping = {
            "text": "label",
            "width": "width",
            "height": "height",
            "x": "x",
            "y": "y",
            "visible": "visible",
            "enabled": "enabled",
            "backcolor": "backgroundColor",
            "textcolor": "textColor",
            "font": "font",
            "fontsize": "fontSize",
            "bold": "fontWeight",
            "italic": "fontStyle",
            "underline": "textDecoration",
            "alignment": "textAlign",
            "borderstyle": "borderStyle",
            "taborder": "tabIndex",
            "tooltip": "tooltip",
        }

        for pb_prop, target_prop in property_mapping.items():
            if pb_prop in properties:
                processed[target_prop] = properties[pb_prop]

        # Process control-specific properties
        if control_type == "datawindow":
            processed["dataSource"] = properties.get("dataobject", "")
            processed["allowEdit"] = properties.get("editable", True)
        elif control_type == "dropdownlistbox":
            processed["items"] = properties.get("item", [])
            processed["allowEdit"] = properties.get("allowedit", False)
        elif control_type == "picture":
            processed["source"] = properties.get("picturename", "")
            processed["scaleMode"] = (
                "none" if properties.get("originalsize", False) else "fit"
            )

        return processed

    def _process_events(self, events: list[Any]) -> list[dict[str, str]]:
        """Process control events."""
        processed = []

        # Handle different event formats
        if isinstance(events, list):
            for event in events:
                if isinstance(event, dict):
                    processed.append(
                        {
                            "name": event.get("name", ""),
                            "handler": event.get("handler", ""),
                            "type": event.get("type", "user"),
                        }
                    )
                elif isinstance(event, str):
                    processed.append(
                        {"name": event, "handler": f"on_{event}", "type": "system"}
                    )

        return processed

    def _get_layout_hints(self, control: dict[str, Any]) -> dict[str, Any]:
        """Get layout hints for a control."""
        hints = {"stretch": False, "align": "left", "margin": 0, "padding": 0}

        # Check properties for layout hints
        props = control.get("properties", {})

        # Determine stretch behavior
        if props.get("width", 0) == "100%" or props.get("anchor", "") == "all":
            hints["stretch"] = True

        # Determine alignment
        alignment = props.get("alignment", "").lower()
        if "center" in alignment:
            hints["align"] = "center"
        elif "right" in alignment:
            hints["align"] = "right"

        # Extract margin/padding
        if "margin" in props:
            hints["margin"] = props["margin"]
        if "padding" in props:
            hints["padding"] = props["padding"]

        return hints

    def _determine_layout_type(self, controls: list[dict[str, Any]]) -> str:
        """Determine the best layout type for controls."""
        if not controls:
            return "flow"

        # Check if all controls have absolute positions
        all_absolute = all(
            "properties" in c and "x" in c["properties"] and "y" in c["properties"]
            for c in controls
        )

        if all_absolute:
            # Check if controls form a grid pattern
            if self._is_grid_layout(controls):
                return "grid"
            return "absolute"

        # Check for responsive indicators
        if any(
            c.get("properties", {}).get("responsive", False)
            or c.get("properties", {}).get("breakpoint", "")
            for c in controls
        ):
            return "responsive"

        return "flow"

    def _is_grid_layout(self, controls: list[dict[str, Any]]) -> bool:
        """Check if controls form a grid pattern."""
        if len(controls) < 4:
            return False

        # Extract positions
        positions = []
        for control in controls:
            props = control.get("properties", {})
            x = props.get("x", 0)
            y = props.get("y", 0)
            positions.append((x, y))

        # Check for regular spacing
        x_positions = sorted({x for x, y in positions})
        y_positions = sorted({y for x, y in positions})

        if len(x_positions) < 2 or len(y_positions) < 2:
            return False

        # Check for consistent spacing
        x_diffs = [
            x_positions[i + 1] - x_positions[i] for i in range(len(x_positions) - 1)
        ]
        y_diffs = [
            y_positions[i + 1] - y_positions[i] for i in range(len(y_positions) - 1)
        ]

        # Allow for small variations
        x_consistent = max(x_diffs) - min(x_diffs) < 10
        y_consistent = max(y_diffs) - min(y_diffs) < 10

        return x_consistent and y_consistent

    def _generate_absolute_layout(
        self, controls: list[dict[str, Any]]
    ) -> dict[str, Any]:
        """Generate absolute layout."""
        return {
            "type": "absolute",
            "children": [
                {
                    "control": control,
                    "position": {
                        "x": control.get("properties", {}).get("x", 0),
                        "y": control.get("properties", {}).get("y", 0),
                    },
                }
                for control in controls
            ],
        }

    def _generate_grid_layout(self, controls: list[dict[str, Any]]) -> dict[str, Any]:
        """Generate grid layout."""
        # Calculate grid dimensions
        positions = []
        for control in controls:
            props = control.get("properties", {})
            x = props.get("x", 0)
            y = props.get("y", 0)
            positions.append((x, y, control))

        # Sort by position
        positions.sort(key=lambda p: (p[1], p[0]))

        # Group into rows
        rows = []
        current_row = []
        current_y = None

        for x, y, control in positions:
            if current_y is None or abs(y - current_y) < 10:
                current_row.append(control)
                current_y = y
            else:
                rows.append(current_row)
                current_row = [control]
                current_y = y

        if current_row:
            rows.append(current_row)

        return {
            "type": "grid",
            "columns": max(len(row) for row in rows) if rows else 0,
            "rows": rows,
            "gap": 10,
        }

    def _generate_flow_layout(self, controls: list[dict[str, Any]]) -> dict[str, Any]:
        """Generate flow layout."""
        return {
            "type": "flow",
            "direction": "vertical",
            "children": controls,
            "spacing": 8,
            "wrap": True,
        }

    def _generate_responsive_layout(
        self, controls: list[dict[str, Any]]
    ) -> dict[str, Any]:
        """Generate responsive layout."""
        # Group controls by breakpoint
        breakpoint_groups = {}

        for control in controls:
            breakpoint = control.get("properties", {}).get("breakpoint", "default")
            if breakpoint not in breakpoint_groups:
                breakpoint_groups[breakpoint] = []
            breakpoint_groups[breakpoint].append(control)

        return {
            "type": "responsive",
            "breakpoints": list(breakpoint_groups.keys()),
            "layouts": {
                bp: self._generate_flow_layout(controls)
                for bp, controls in breakpoint_groups.items()
            },
        }

    def _calculate_breakpoints(self, _controls: list[dict[str, Any]]) -> dict[str, int]:
        """Calculate responsive breakpoints."""
        return {"mobile": 640, "tablet": 768, "desktop": 1024, "wide": 1280}

    def _process_menu(self, menu_data: dict[str, Any]) -> dict[str, Any]:
        """Process menu data."""
        processed = {
            "name": menu_data.get("name", "menu"),
            "type": menu_data.get("type", "menubar"),
            "items": [],
        }

        # Process menu items
        if "items" in menu_data:
            for item in menu_data["items"]:
                processed["items"].append(self._process_menu_item(item))
        elif "menuitems" in menu_data:
            for item in menu_data["menuitems"]:
                processed["items"].append(self._process_menu_item(item))

        return processed

    def _process_menu_item(self, item: dict[str, Any]) -> dict[str, Any]:
        """Process a single menu item."""
        processed = {
            "label": item.get("text", item.get("label", "")),
            "name": item.get("name", ""),
            "enabled": item.get("enabled", True),
            "visible": item.get("visible", True),
            "shortcut": item.get("shortcut", ""),
            "icon": item.get("icon", ""),
            "action": item.get("clicked", item.get("action", "")),
            "children": [],
        }

        # Process submenu items
        if "items" in item:
            for subitem in item["items"]:
                processed["children"].append(self._process_menu_item(subitem))

        return processed

    def _extract_toolbar_menu(self, toolbar: dict[str, Any]) -> dict[str, Any] | None:
        """Extract menu items from toolbar."""
        if not toolbar or "items" not in toolbar:
            return None

        menu = {"name": "toolbar_menu", "type": "toolbar", "items": []}

        for item in toolbar["items"]:
            if item.get("type") == "button":
                menu["items"].append(
                    {
                        "label": item.get("tooltip", item.get("name", "")),
                        "name": item.get("name", ""),
                        "icon": item.get("icon", ""),
                        "action": item.get("clicked", ""),
                        "enabled": item.get("enabled", True),
                    }
                )

        return menu if menu["items"] else None


class ValidationRule:
    """Represents a validation rule for UI components."""

    def __init__(self, rule_type: str, parameter: str = "", message: str = ""):
        """Initialize validation rule.

        Args:
            rule_type: Type of validation (required, length, pattern, etc.)
            parameter: Parameter for the rule (e.g., max length, regex pattern)
            message: Error message to display when validation fails
        """
        self.rule_type = rule_type
        self.parameter = parameter
        self.message = message
        self.priority = self._get_rule_priority(rule_type)

    def _get_rule_priority(self, rule_type: str) -> int:
        """Get priority for validation rule ordering."""
        priorities = {
            "required": 1,
            "type": 2,
            "length": 3,
            "range": 4,
            "pattern": 5,
            "custom": 6,
        }
        return priorities.get(rule_type, 10)

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary representation."""
        return {
            "type": self.rule_type,
            "parameter": self.parameter,
            "message": self.message,
            "priority": self.priority,
        }


class ValidationRuleProcessor:
    """Processes validation rules for UI components."""

    def __init__(self):
        """Initialize validation rule processor."""
        self.validation_rules: list[ValidationRule] = []

    def process_validation_rules(
        self, component: dict[str, Any]
    ) -> list[ValidationRule]:
        """Process validation rules from component definition.

        Args:
            component: Component definition with validation rules

        Returns:
            List of validation rules
        """
        rules = []

        # Extract validation from component properties
        if "validation" in component:
            validation_def = component["validation"]

            if isinstance(validation_def, dict):
                # Required field validation
                if validation_def.get("required", False):
                    message = validation_def.get(
                        "required_message", "This field is required"
                    )
                    rules.append(ValidationRule("required", "", message))

                # Length validation
                if "min_length" in validation_def or "max_length" in validation_def:
                    min_len = validation_def.get("min_length", 0)
                    max_len = validation_def.get("max_length", 0)
                    message = validation_def.get(
                        "length_message",
                        f"Length must be between {min_len} and {max_len}",
                    )
                    rules.append(
                        ValidationRule("length", f"{min_len},{max_len}", message)
                    )

                # Pattern validation
                if "pattern" in validation_def:
                    pattern = validation_def["pattern"]
                    message = validation_def.get("pattern_message", "Invalid format")
                    rules.append(ValidationRule("pattern", pattern, message))

                # Range validation
                if "min_value" in validation_def or "max_value" in validation_def:
                    min_val = validation_def.get("min_value", "")
                    max_val = validation_def.get("max_value", "")
                    message = validation_def.get(
                        "range_message",
                        f"Value must be between {min_val} and {max_val}",
                    )
                    rules.append(
                        ValidationRule("range", f"{min_val},{max_val}", message)
                    )

                # Custom validation
                if "custom" in validation_def:
                    custom_rule = validation_def["custom"]
                    message = validation_def.get("custom_message", "Validation failed")
                    rules.append(ValidationRule("custom", custom_rule, message))

        # Extract validation from component attributes
        self._extract_attribute_validation(component, rules)

        # Sort rules by priority
        rules.sort(key=lambda r: r.priority)

        return rules

    def _extract_attribute_validation(
        self, component: dict[str, Any], rules: list[ValidationRule]
    ) -> None:
        """Extract validation rules from component attributes."""
        # Check for required attribute
        if component.get("required", False):
            rules.append(ValidationRule("required", "", "This field is required"))

        # Check for data type
        data_type = component.get("data_type", "")
        if data_type in ["integer", "decimal", "date", "time"]:
            message = f"Please enter a valid {data_type}"
            rules.append(ValidationRule("type", data_type, message))

        # Check for display format constraints
        display_format = component.get("display_format", "")
        if display_format:
            # Convert PowerBuilder format to validation pattern
            pattern = self._convert_pb_format_to_pattern(display_format)
            if pattern:
                rules.append(ValidationRule("pattern", pattern, "Invalid format"))

    def _convert_pb_format_to_pattern(self, pb_format: str) -> str:
        """Convert PowerBuilder display format to regex pattern."""
        # Basic conversion - can be enhanced
        pattern_map = {
            "dd/mm/yyyy": r"\d{2}/\d{2}/\d{4}",
            "mm/dd/yyyy": r"\d{2}/\d{2}/\d{4}",
            "hh:mm:ss": r"\d{2}:\d{2}:\d{2}",
            "hh:mm": r"\d{2}:\d{2}",
            "#,##0": r"\d{1,3}(,\d{3})*",
            "#,##0.00": r"\d{1,3}(,\d{3})*\.\d{2}",
        }

        return pattern_map.get(pb_format, "")

    def generate_validation_code(
        self, rules: list[ValidationRule], target_language: str = "dart"
    ) -> str:
        """Generate validation code for the rules.

        Args:
            rules: List of validation rules
            target_language: Target language for generation

        Returns:
            Generated validation code
        """
        if target_language.lower() == "dart":
            return self._generate_dart_validation(rules)
        if target_language.lower() == "python":
            return self._generate_python_validation(rules)
        return "// Validation not implemented for " + target_language

    def _generate_dart_validation(self, rules: list[ValidationRule]) -> str:
        """Generate Dart validation code."""
        code_lines = []

        code_lines.append("String? validateValue(String? value) {")

        for rule in rules:
            if rule.rule_type == "required":
                code_lines.append("  if (value == null || value.isEmpty) {")
                code_lines.append(f"    return '{rule.message}';")
                code_lines.append("  }")

            elif rule.rule_type == "length":
                params = rule.parameter.split(",")
                if len(params) == 2:
                    min_len, max_len = params
                    if min_len != "0":
                        code_lines.append(f"  if (value.length < {min_len}) {{")
                        code_lines.append(f"    return '{rule.message}';")
                        code_lines.append("  }")
                    if max_len != "0":
                        code_lines.append(f"  if (value.length > {max_len}) {{")
                        code_lines.append(f"    return '{rule.message}';")
                        code_lines.append("  }")

            elif rule.rule_type == "pattern":
                code_lines.append(f"  final regex = RegExp(r'{rule.parameter}');")
                code_lines.append("  if (!regex.hasMatch(value)) {")
                code_lines.append(f"    return '{rule.message}';")
                code_lines.append("  }")

        code_lines.append("  return null;")
        code_lines.append("}")

        return "\n".join(code_lines)

    def _generate_python_validation(self, rules: list[ValidationRule]) -> str:
        """Generate Python validation code."""
        code_lines = []

        code_lines.append("def validate_value(value):")
        code_lines.append("    errors = []")

        for rule in rules:
            if rule.rule_type == "required":
                code_lines.append("    if not value:")
                code_lines.append(f"        errors.append('{rule.message}')")

            elif rule.rule_type == "length":
                params = rule.parameter.split(",")
                if len(params) == 2:
                    min_len, max_len = params
                    if min_len != "0":
                        code_lines.append(f"    if len(str(value)) < {min_len}:")
                        code_lines.append(f"        errors.append('{rule.message}')")
                    if max_len != "0":
                        code_lines.append(f"    if len(str(value)) > {max_len}:")
                        code_lines.append(f"        errors.append('{rule.message}')")

            elif rule.rule_type == "pattern":
                code_lines.append("    import re")
                code_lines.append(
                    f"    if not re.match(r'{rule.parameter}', str(value)):"
                )
                code_lines.append(f"        errors.append('{rule.message}')")

        code_lines.append("    return errors if errors else None")

        return "\n".join(code_lines)
