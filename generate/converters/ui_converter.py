"""PowerBuilder UI control to Flutter widget converter.

Converts PowerBuilder UI controls and their properties to Flutter widgets.
"""

import logging
from typing import Dict, Any, Optional, List

logger = logging.getLogger(__name__)


class UIConverter:
    """Converts PowerBuilder UI controls to Flutter widgets."""
    
    def __init__(self):
        """Initialize the UI converter with control mappings."""
        # PowerBuilder control to Flutter widget mappings
        self.control_map = {
            # Text controls
            "statictext": {
                "widget": "Text",
                "container": False,
                "properties": {
                    "text": "data",
                    "font": "style",
                    "alignment": "textAlign",
                    "textcolor": "style.color",
                    "backcolor": "_backgroundColor"
                }
            },
            "singlelineedit": {
                "widget": "TextField",
                "container": False,
                "controller": "TextEditingController",
                "properties": {
                    "text": "controller.text",
                    "maxlength": "maxLength",
                    "password": "obscureText",
                    "enabled": "enabled",
                    "readonly": "readOnly",
                    "font": "style",
                    "textcolor": "style.color"
                }
            },
            "multilineedit": {
                "widget": "TextField",
                "container": False,
                "controller": "TextEditingController",
                "properties": {
                    "text": "controller.text",
                    "maxlength": "maxLength",
                    "enabled": "enabled",
                    "readonly": "readOnly",
                    "vscrollbar": "_showScrollbar"
                },
                "config": {
                    "maxLines": None,
                    "minLines": 3
                }
            },
            
            # Button controls
            "commandbutton": {
                "widget": "ElevatedButton",
                "container": False,
                "properties": {
                    "text": "_buttonText",
                    "enabled": "_isEnabled",
                    "default": "autofocus",
                    "font": "style.textStyle"
                }
            },
            "picturebutton": {
                "widget": "IconButton",
                "container": False,
                "properties": {
                    "picturename": "_iconData",
                    "text": "tooltip",
                    "enabled": "_isEnabled"
                }
            },
            
            # Selection controls
            "checkbox": {
                "widget": "Checkbox",
                "container": "CheckboxListTile",
                "properties": {
                    "checked": "value",
                    "text": "title",
                    "enabled": "_isEnabled",
                    "threestate": "tristate"
                }
            },
            "radiobutton": {
                "widget": "Radio",
                "container": "RadioListTile",
                "properties": {
                    "checked": "_isSelected",
                    "text": "title",
                    "enabled": "_isEnabled"
                }
            },
            
            # List controls
            "dropdownlistbox": {
                "widget": "DropdownButton",
                "container": False,
                "properties": {
                    "items": "_dropdownItems",
                    "selected": "value",
                    "enabled": "_isEnabled",
                    "allowedit": "_isEditable"
                }
            },
            "listbox": {
                "widget": "ListView",
                "container": False,
                "builder": "ListView.builder",
                "properties": {
                    "items": "_listItems",
                    "multiselect": "_multiSelect",
                    "sorted": "_isSorted"
                }
            },
            
            # Container controls
            "groupbox": {
                "widget": "Container",
                "container": True,
                "child_layout": "Column",
                "properties": {
                    "text": "_groupTitle",
                    "border": "_boxDecoration"
                }
            },
            "tab": {
                "widget": "TabBar",
                "container": True,
                "view": "TabBarView",
                "controller": "TabController",
                "properties": {
                    "tabs": "_tabItems",
                    "selectedtab": "controller.index"
                }
            },
            
            # Data controls
            "datawindow": {
                "widget": "DataWindowWidget",
                "container": False,
                "custom": True,
                "properties": {
                    "dataobject": "_dataWindowName",
                    "enabled": "_isEnabled"
                }
            },
            
            # Other controls
            "picture": {
                "widget": "Image",
                "container": False,
                "properties": {
                    "picturename": "_imageSource",
                    "originalsize": "_fitMode",
                    "enabled": "_isVisible"
                }
            },
            "line": {
                "widget": "Divider",
                "container": False,
                "properties": {
                    "beginx": "_startX",
                    "beginy": "_startY",
                    "endx": "_endX",
                    "endy": "_endY",
                    "linecolor": "color",
                    "linethickness": "thickness"
                }
            },
            "rectangle": {
                "widget": "Container",
                "container": False,
                "properties": {
                    "x": "_left",
                    "y": "_top",
                    "width": "width",
                    "height": "height",
                    "fillcolor": "_fillColor",
                    "linecolor": "_borderColor"
                }
            }
        }
        
        # Property value converters
        self.property_converters = {
            "alignment": self._convert_alignment,
            "font": self._convert_font,
            "textcolor": self._convert_color,
            "backcolor": self._convert_color,
            "fillcolor": self._convert_color,
            "linecolor": self._convert_color,
            "enabled": self._convert_boolean,
            "visible": self._convert_boolean,
            "checked": self._convert_boolean,
            "border": self._convert_border
        }
    
    def convert_control(self, control_type: str, control_name: str, 
                       properties: Dict[str, Any]) -> Dict[str, Any]:
        """Convert a PowerBuilder control to Flutter widget info.
        
        Args:
            control_type: PowerBuilder control type
            control_name: Control instance name
            properties: Control properties
            
        Returns:
            Dictionary with Flutter widget information
        """
        # Get mapping for control type
        mapping = self.control_map.get(control_type.lower(), {})
        
        if not mapping:
            logger.warning(f"Unknown control type: {control_type}")
            return self._create_unknown_control(control_type, control_name, properties)
        
        # Create Flutter widget info
        flutter_info = {
            "type": control_type,
            "name": control_name,
            "widget": mapping["widget"],
            "dart_name": self._to_camel_case(control_name),
            "properties": {},
            "flutter_properties": {},
            "requires_controller": "controller" in mapping,
            "controller_type": mapping.get("controller"),
            "is_container": mapping.get("container", False),
            "child_layout": mapping.get("child_layout"),
            "builder_pattern": mapping.get("builder"),
            "custom_widget": mapping.get("custom", False)
        }
        
        # Convert properties
        for pb_prop, flutter_prop in mapping.get("properties", {}).items():
            if pb_prop in properties:
                value = properties[pb_prop]
                # Apply property converter if available
                if pb_prop in self.property_converters:
                    value = self.property_converters[pb_prop](value)
                flutter_info["flutter_properties"][flutter_prop] = value
        
        # Add config if present
        if "config" in mapping:
            flutter_info["config"] = mapping["config"]
        
        # Store original properties for reference
        flutter_info["properties"] = properties
        
        return flutter_info
    
    def _create_unknown_control(self, control_type: str, control_name: str,
                               properties: Dict[str, Any]) -> Dict[str, Any]:
        """Create placeholder for unknown control type."""
        return {
            "type": control_type,
            "name": control_name,
            "widget": "Container",  # Default to Container
            "dart_name": self._to_camel_case(control_name),
            "properties": properties,
            "flutter_properties": {
                "child": f"Text('TODO: Implement {control_type}')"
            },
            "unknown": True
        }
    
    def _convert_alignment(self, value: Any) -> str:
        """Convert PowerBuilder alignment to Flutter TextAlign."""
        alignment_map = {
            "0": "TextAlign.left",
            "1": "TextAlign.right", 
            "2": "TextAlign.center",
            "left": "TextAlign.left",
            "right": "TextAlign.right",
            "center": "TextAlign.center"
        }
        return alignment_map.get(str(value).lower(), "TextAlign.left")
    
    def _convert_font(self, value: Any) -> str:
        """Convert PowerBuilder font to Flutter TextStyle."""
        # This is simplified - full implementation would parse font string
        return "Theme.of(context).textTheme.bodyMedium"
    
    def _convert_color(self, value: Any) -> str:
        """Convert PowerBuilder color to Flutter Color."""
        if isinstance(value, int):
            # PowerBuilder color is often a Windows RGB value
            # Convert to Flutter Color
            r = value & 0xFF
            g = (value >> 8) & 0xFF
            b = (value >> 16) & 0xFF
            return f"Color.fromRGBO({r}, {g}, {b}, 1.0)"
        elif isinstance(value, str):
            # Try to parse named colors
            color_map = {
                "black": "Colors.black",
                "white": "Colors.white",
                "red": "Colors.red",
                "blue": "Colors.blue",
                "green": "Colors.green",
                "transparent": "Colors.transparent"
            }
            return color_map.get(value.lower(), "Colors.grey")
        else:
            return "Colors.grey"
    
    def _convert_boolean(self, value: Any) -> str:
        """Convert PowerBuilder boolean to Dart bool."""
        if isinstance(value, bool):
            return str(value).lower()
        elif isinstance(value, str):
            return "true" if value.lower() in ["true", "yes", "1"] else "false"
        elif isinstance(value, int):
            return "true" if value != 0 else "false"
        else:
            return "false"
    
    def _convert_border(self, value: Any) -> str:
        """Convert PowerBuilder border to Flutter BoxDecoration."""
        # Simplified - full implementation would handle border styles
        return "BoxDecoration(border: Border.all())"
    
    def _to_camel_case(self, name: str) -> str:
        """Convert name to camelCase."""
        # Remove common prefixes
        prefixes = ["cb_", "sle_", "st_", "dw_", "rb_", "ddlb_", "lb_", "pb_"]
        for prefix in prefixes:
            if name.lower().startswith(prefix):
                name = name[len(prefix):]
                break
        
        # Convert to camelCase
        parts = name.split("_")
        return parts[0].lower() + "".join(p.capitalize() for p in parts[1:])
    
    def get_widget_imports(self, controls: List[Dict[str, Any]]) -> List[str]:
        """Get required imports for Flutter widgets.
        
        Args:
            controls: List of control definitions
            
        Returns:
            List of import statements
        """
        imports = set()
        imports.add("import 'package:flutter/material.dart';")
        
        for control in controls:
            widget = control.get("widget", "")
            
            # Add specific imports for certain widgets
            if "charts" in widget.lower():
                imports.add("import 'package:charts_flutter/flutter.dart' as charts;")
            elif "image" in widget.lower() and control.get("properties", {}).get("picturename", "").startswith("http"):
                imports.add("import 'package:cached_network_image/cached_network_image.dart';")
            elif control.get("custom_widget"):
                imports.add(f"import '../widgets/{self._to_snake_case(widget)}.dart';")
        
        return sorted(list(imports))
    
    def _to_snake_case(self, name: str) -> str:
        """Convert name to snake_case."""
        # Convert from PascalCase to snake_case
        result = []
        for i, char in enumerate(name):
            if char.isupper() and i > 0:
                result.append("_")
            result.append(char.lower())
        return "".join(result)
    
    def generate_widget_tree(self, controls: List[Dict[str, Any]]) -> str:
        """Generate Flutter widget tree from controls.
        
        Args:
            controls: List of control definitions
            
        Returns:
            Dart code for widget tree
        """
        # This is a simplified implementation
        # A full implementation would handle layout and nesting
        
        if not controls:
            return "Container()"
        
        # Group controls by container
        containers = {}
        root_controls = []
        
        for control in controls:
            # Simplified - assume flat structure for now
            root_controls.append(control)
        
        # Generate Column with all controls
        widgets = []
        for control in root_controls:
            widget_code = self._generate_widget_code(control)
            widgets.append(widget_code)
        
        return f"""Column(
          children: [
            {',\n            '.join(widgets)}
          ],
        )"""
    
    def _generate_widget_code(self, control: Dict[str, Any]) -> str:
        """Generate Dart code for a single widget."""
        widget = control["widget"]
        dart_name = control["dart_name"]
        
        # Generate based on widget type
        if widget == "Text":
            text = control.get("flutter_properties", {}).get("data", "''")
            return f"Text({text})"
        elif widget == "TextField":
            return f"TextField(controller: _{dart_name}Controller)"
        elif widget == "ElevatedButton":
            text = control.get("flutter_properties", {}).get("_buttonText", "'Button'")
            return f"ElevatedButton(onPressed: _on{dart_name.capitalize()}Pressed, child: Text({text}))"
        else:
            return f"{widget}() // TODO: Configure {control['name']}"