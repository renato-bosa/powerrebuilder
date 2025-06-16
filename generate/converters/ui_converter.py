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
            },
            
            # Advanced input controls
            "editmask": {
                "widget": "TextField",
                "container": False,
                "controller": "TextEditingController",
                "formatter": "TextInputFormatter",
                "properties": {
                    "text": "controller.text",
                    "mask": "_inputFormatters",
                    "enabled": "enabled",
                    "readonly": "readOnly",
                    "font": "style",
                    "textcolor": "style.color"
                }
            },
            
            # Tree and list controls
            "treeview": {
                "widget": "TreeView",
                "container": False,
                "custom": True,
                "properties": {
                    "items": "_treeData",
                    "haslines": "_showLines",
                    "hasbuttons": "_showExpandButtons",
                    "sorted": "_isSorted"
                }
            },
            "listview": {
                "widget": "ListView",
                "container": False,
                "builder": "ListView.builder",
                "properties": {
                    "columns": "_columnDefinitions",
                    "items": "_listViewItems",
                    "viewmode": "_viewMode",
                    "sorted": "_isSorted"
                }
            },
            
            # Chart/Graph control
            "graph": {
                "widget": "CustomChart",
                "container": False,
                "custom": True,
                "properties": {
                    "graphtype": "_chartType",
                    "title": "_chartTitle",
                    "series": "_dataSeries",
                    "category": "_categoryAxis",
                    "values": "_valueAxis"
                }
            },
            
            # OLE control
            "ole": {
                "widget": "Container",
                "container": True,
                "custom": True,
                "properties": {
                    "classname": "_oleClass",
                    "activation": "_activationType",
                    "displaytype": "_displayMode"
                },
                "config": {
                    "placeholder": "Text('OLE Control placeholder')"
                }
            },
            
            # Shape controls
            "roundrectangle": {
                "widget": "Container",
                "container": False,
                "properties": {
                    "x": "_left",
                    "y": "_top",
                    "width": "width",
                    "height": "height",
                    "cornerradius": "_borderRadius",
                    "fillcolor": "_fillColor",
                    "linecolor": "_borderColor",
                    "linethickness": "_borderWidth"
                }
            },
            "oval": {
                "widget": "Container",
                "container": False,
                "shape": "BoxShape.circle",
                "properties": {
                    "x": "_left",
                    "y": "_top",
                    "width": "width",
                    "height": "height",
                    "fillcolor": "_fillColor",
                    "linecolor": "_borderColor",
                    "linethickness": "_borderWidth"
                }
            },
            
            # Progress controls
            "progressbar": {
                "widget": "LinearProgressIndicator",
                "container": False,
                "properties": {
                    "position": "value",
                    "minposition": "_minValue",
                    "maxposition": "_maxValue",
                    "smooth": "_isIndeterminate",
                    "fillcolor": "valueColor",
                    "backcolor": "backgroundColor"
                }
            },
            "hprogressbar": {
                "widget": "LinearProgressIndicator",
                "container": False,
                "properties": {
                    "position": "value",
                    "minposition": "_minValue",
                    "maxposition": "_maxValue",
                    "smooth": "_isIndeterminate",
                    "fillcolor": "valueColor"
                }
            },
            "vprogressbar": {
                "widget": "RotatedBox",
                "container": True,
                "config": {
                    "quarterTurns": 3
                },
                "child_widget": "LinearProgressIndicator",
                "properties": {
                    "position": "value",
                    "minposition": "_minValue",
                    "maxposition": "_maxValue",
                    "smooth": "_isIndeterminate"
                }
            },
            
            # Slider/Trackbar controls
            "htrackbar": {
                "widget": "Slider",
                "container": False,
                "properties": {
                    "position": "value",
                    "minposition": "min",
                    "maxposition": "max",
                    "tickfrequency": "divisions",
                    "pagesize": "_stepSize",
                    "enabled": "_isEnabled"
                }
            },
            "vtrackbar": {
                "widget": "RotatedBox",
                "container": True,
                "config": {
                    "quarterTurns": 3
                },
                "child_widget": "Slider",
                "properties": {
                    "position": "value",
                    "minposition": "min",
                    "maxposition": "max",
                    "tickfrequency": "divisions"
                }
            },
            
            # Animation control
            "animation": {
                "widget": "AnimatedBuilder",
                "container": False,
                "custom": True,
                "controller": "AnimationController",
                "properties": {
                    "animationfile": "_animationAsset",
                    "autoplay": "_autoStart",
                    "transparent": "_isTransparent"
                }
            },
            
            # Date/Time controls
            "datepicker": {
                "widget": "DatePickerField",
                "container": False,
                "custom": True,
                "properties": {
                    "value": "_selectedDate",
                    "mindate": "_firstDate",
                    "maxdate": "_lastDate",
                    "format": "_dateFormat",
                    "enabled": "_isEnabled"
                }
            },
            "monthcalendar": {
                "widget": "TableCalendar",
                "container": False,
                "custom": True,
                "package": "table_calendar",
                "properties": {
                    "selecteddate": "_selectedDay",
                    "mindate": "_firstDay",
                    "maxdate": "_lastDay",
                    "showtoday": "_showToday",
                    "enabled": "_isEnabled"
                }
            },
            
            # Ink controls
            "inkpicture": {
                "widget": "CustomInkCanvas",
                "container": False,
                "custom": True,
                "properties": {
                    "picture": "_backgroundImage",
                    "inkcolor": "_strokeColor",
                    "inkwidth": "_strokeWidth",
                    "enabled": "_allowDrawing"
                }
            },
            "inkedit": {
                "widget": "CustomInkTextField",
                "container": False,
                "custom": True,
                "controller": "TextEditingController",
                "properties": {
                    "text": "controller.text",
                    "inkcolor": "_strokeColor",
                    "inkwidth": "_strokeWidth",
                    "recognitiontimeout": "_recognitionDelay",
                    "enabled": "_isEnabled"
                }
            },
            
            # Scrollbar controls
            "vscrollbar": {
                "widget": "Scrollbar",
                "container": False,
                "properties": {
                    "minposition": "_minValue",
                    "maxposition": "_maxValue",
                    "position": "_currentValue",
                    "linesize": "_stepSize",
                    "pagesize": "_pageSize",
                    "enabled": "_isEnabled"
                },
                "config": {
                    "axis": "Axis.vertical"
                }
            },
            "hscrollbar": {
                "widget": "Scrollbar",
                "container": False,
                "properties": {
                    "minposition": "_minValue",
                    "maxposition": "_maxValue",
                    "position": "_currentValue",
                    "linesize": "_stepSize",
                    "pagesize": "_pageSize",
                    "enabled": "_isEnabled"
                },
                "config": {
                    "axis": "Axis.horizontal"
                }
            },
            
            # ComboBox control (editable dropdown)
            "combobox": {
                "widget": "Autocomplete",
                "container": False,
                "properties": {
                    "text": "_selectedText",
                    "items": "_suggestions",
                    "allowedit": "_allowEdit",
                    "sorted": "_isSorted",
                    "enabled": "_isEnabled"
                }
            },
            
            # RichTextEdit control
            "richtextedit": {
                "widget": "QuillEditor",
                "container": False,
                "custom": True,
                "package": "flutter_quill",
                "properties": {
                    "text": "_document",
                    "readonly": "_readOnly",
                    "enabled": "_isEnabled",
                    "toolbar": "_showToolbar"
                }
            },
            
            # MDI Client control
            "mdiclient": {
                "widget": "Container",
                "container": True,
                "custom": True,
                "properties": {
                    "backcolor": "_backgroundColor"
                },
                "config": {
                    "placeholder": "Text('MDI Client Area')"
                }
            },
            
            # Hyperlink control
            "statichyperlink": {
                "widget": "InkWell",
                "container": True,
                "custom": True,
                "child_widget": "Text",
                "properties": {
                    "text": "_linkText",
                    "url": "_targetUrl",
                    "textcolor": "_linkColor",
                    "font": "_textStyle",
                    "enabled": "_isEnabled"
                },
                "config": {
                    "onTap": "_launchUrl",
                    "mouse_cursor": "SystemMouseCursors.click"
                }
            },
            
            # Spin control
            "spin": {
                "widget": "SpinBox",
                "container": False,
                "custom": True,
                "properties": {
                    "value": "_currentValue",
                    "minvalue": "_minValue",
                    "maxvalue": "_maxValue",
                    "increment": "_stepValue",
                    "acceleration": "_acceleration",
                    "enabled": "_isEnabled"
                },
                "config": {
                    "decoration": "InputDecoration"
                }
            },
            
            # Generic drawing control
            "drawobject": {
                "widget": "CustomPaint",
                "container": False,
                "custom": True,
                "painter": "CustomPainter",
                "properties": {
                    "drawtype": "_drawingType",
                    "fillcolor": "_fillColor",
                    "linecolor": "_strokeColor",
                    "linewidth": "_strokeWidth",
                    "fillpattern": "_fillPattern",
                    "points": "_drawingPoints"
                }
            },
            
            # Additional PowerBuilder controls
            "userobject": {
                "widget": "CustomUserObject",
                "container": True,
                "custom_widget": True,
                "properties": {
                    "classname": "_className",
                    "x": "_left",
                    "y": "_top",
                    "width": "width",
                    "height": "height",
                    "visible": "_isVisible",
                    "enabled": "_isEnabled"
                }
            },
            "menu": {
                "widget": "PopupMenuButton",
                "container": False,
                "properties": {
                    "text": "_tooltip",
                    "enabled": "enabled",
                    "visible": "_isVisible",
                    "menuitems": "_menuItems"
                }
            },
            "timer": {
                "widget": "Timer",
                "container": False,
                "non_visual": True,
                "properties": {
                    "interval": "_duration",
                    "enabled": "_isActive"
                }
            },
            "pipeline": {
                "widget": "DataPipeline",
                "container": False,
                "non_visual": True,
                "custom_widget": True,
                "properties": {
                    "source": "_sourceDataWindow",
                    "destination": "_destinationDataWindow",
                    "columns": "_columnMappings"
                }
            },
            "dropdownpicturelistbox": {
                "widget": "DropdownButton",
                "container": False,
                "properties": {
                    "items": "_items",
                    "pictures": "_pictures",
                    "value": "_selectedValue",
                    "enabled": "enabled",
                    "visible": "_isVisible",
                    "sorted": "_isSorted"
                },
                "custom_widget": True
            },
            "picturelistbox": {
                "widget": "ListView",
                "container": False,
                "properties": {
                    "items": "_items",
                    "pictures": "_pictures",
                    "multiselect": "_multiSelection",
                    "sorted": "_isSorted",
                    "enabled": "_isEnabled"
                },
                "config": {
                    "itemBuilder": "_buildPictureListItem"
                }
            },
            "tooltip": {
                "widget": "Tooltip",
                "container": False,
                "wrapper": True,
                "properties": {
                    "text": "message",
                    "delay": "_showDuration",
                    "enabled": "_isEnabled"
                }
            },
            "slider": {
                "widget": "Slider",
                "container": False,
                "properties": {
                    "minposition": "min",
                    "maxposition": "max",
                    "position": "value",
                    "frequency": "divisions",
                    "enabled": "_isEnabled",
                    "orientation": "_orientation"
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
        
        # Add package if present
        if "package" in mapping:
            flutter_info["package"] = mapping["package"]
        
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
                "decoration": "BoxDecoration(border: Border.all(color: Colors.grey), borderRadius: BorderRadius.circular(4))",
                "padding": "EdgeInsets.all(16)",
                "child": f"Column(mainAxisSize: MainAxisSize.min, children: [Icon(Icons.extension, size: 48, color: Colors.grey), SizedBox(height: 8), Text('{control_type}', style: TextStyle(color: Colors.grey))])"
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
        
        # Track which control types are used
        control_types = set()
        for control in controls:
            control_type = control.get("type", "").lower()
            control_types.add(control_type)
            
            widget = control.get("widget", "")
            
            # Add specific imports for certain widgets
            if "charts" in widget.lower() or control_type == "graph":
                imports.add("import 'package:charts_flutter/flutter.dart' as charts;")
            elif "image" in widget.lower() and control.get("properties", {}).get("picturename", "").startswith("http"):
                imports.add("import 'package:cached_network_image/cached_network_image.dart';")
            elif control.get("custom_widget") or control.get("custom"):
                imports.add(f"import '../widgets/{self._to_snake_case(widget)}.dart';")
        
        # Add imports for specific control types
        if "monthcalendar" in control_types:
            imports.add("import 'package:table_calendar/table_calendar.dart';")
        
        if "editmask" in control_types:
            imports.add("import 'package:flutter/services.dart';")  # For TextInputFormatter
        
        if "treeview" in control_types:
            imports.add("import '../widgets/tree_view.dart';")
        
        if "listview" in control_types:
            imports.add("import '../widgets/list_view_custom.dart';")
        
        if "graph" in control_types:
            imports.add("import '../widgets/custom_chart.dart';")
        
        if "datepicker" in control_types:
            imports.add("import '../widgets/date_picker_field.dart';")
        
        if "inkpicture" in control_types or "inkedit" in control_types:
            imports.add("import '../widgets/ink_controls.dart';")
        
        if "animation" in control_types:
            imports.add("import '../widgets/animation_widget.dart';")
        
        if "combobox" in control_types:
            imports.add("import 'package:flutter/material.dart';")  # Autocomplete is in material
        
        if "richtextedit" in control_types:
            imports.add("import 'package:flutter_quill/flutter_quill.dart';")
            imports.add("import '../widgets/rich_text_editor.dart';")
        
        if "mdiclient" in control_types:
            imports.add("import '../widgets/mdi_client.dart';")
        
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
        control_type = control.get("type", "").lower()
        
        # Generate based on widget type
        if widget == "Text":
            text = control.get("flutter_properties", {}).get("data", "''")
            return f"Text({text})"
        elif widget == "TextField":
            if control_type == "editmask":
                return f"TextField(controller: _{dart_name}Controller, inputFormatters: _{dart_name}Formatters)"
            else:
                return f"TextField(controller: _{dart_name}Controller)"
        elif widget == "ElevatedButton":
            text = control.get("flutter_properties", {}).get("_buttonText", "'Button'")
            return f"ElevatedButton(onPressed: _on{dart_name.capitalize()}Pressed, child: Text({text}))"
        elif widget == "LinearProgressIndicator":
            return f"LinearProgressIndicator(value: _{dart_name}Progress)"
        elif widget == "Slider":
            return f"Slider(value: _{dart_name}Value, onChanged: _on{dart_name.capitalize()}Changed, min: 0, max: 100)"
        elif widget == "TreeView":
            return f"TreeView(data: _{dart_name}TreeData)"
        elif widget == "ListView" and control_type == "listview":
            return f"ListViewCustom(columns: _{dart_name}Columns, items: _{dart_name}Items)"
        elif widget == "CustomChart":
            return f"CustomChart(type: ChartType.{control.get('properties', {}).get('graphtype', 'bar')}, data: _{dart_name}ChartData)"
        elif widget == "DatePickerField":
            return f"DatePickerField(selectedDate: _{dart_name}Date, onDateChanged: _on{dart_name.capitalize()}DateChanged)"
        elif widget == "TableCalendar":
            return f"TableCalendar(focusedDay: _{dart_name}FocusedDay, selectedDayPredicate: (day) => isSameDay(_{dart_name}SelectedDay, day))"
        elif widget == "Container" and control_type in ["roundrectangle", "oval"]:
            shape = "BoxShape.circle" if control_type == "oval" else "BoxShape.rectangle"
            radius = ", borderRadius: BorderRadius.circular(${control.get('properties', {}).get('cornerradius', '8')})" if control_type == "roundrectangle" else ""
            return f"Container(decoration: BoxDecoration(shape: {shape}{radius}))"
        elif widget == "RotatedBox":
            # For vertical progress bar or slider
            child_widget = control.get("child_widget", "Container")
            if child_widget == "LinearProgressIndicator":
                return f"RotatedBox(quarterTurns: 3, child: LinearProgressIndicator(value: _{dart_name}Progress))"
            elif child_widget == "Slider":
                return f"RotatedBox(quarterTurns: 3, child: Slider(value: _{dart_name}Value, onChanged: _on{dart_name.capitalize()}Changed))"
        elif widget == "Scrollbar":
            axis = control.get("config", {}).get("axis", "Axis.vertical")
            return f"Scrollbar(controller: _{dart_name}ScrollController, child: SingleChildScrollView(scrollDirection: {axis}, controller: _{dart_name}ScrollController, child: Container()))"
        elif widget == "Autocomplete":
            return f"Autocomplete<String>(optionsBuilder: (value) => _{dart_name}Options.where((s) => s.contains(value.text)), onSelected: _on{dart_name.capitalize()}Selected)"
        elif widget == "QuillEditor":
            return f"QuillEditor(controller: _{dart_name}QuillController, readOnly: false, scrollable: true, focusNode: _{dart_name}FocusNode, padding: EdgeInsets.all(16))"
        elif widget == "Container" and control_type == "mdiclient":
            return f"MdiClientArea(children: _{dart_name}Windows)"
        else:
            # Generate basic widget with common properties
            params = []
            
            # Add common properties if available
            if control.get('flutter_properties', {}).get('enabled') is not None:
                params.append(f"enabled: {control['flutter_properties']['enabled']}")
            
            if control.get('flutter_properties', {}).get('style') is not None:
                params.append(f"style: {control['flutter_properties']['style']}")
                
            if control.get('flutter_properties', {}).get('onPressed') is not None:
                params.append(f"onPressed: {control['flutter_properties']['onPressed']}")
            
            param_str = f"({', '.join(params)})" if params else "()"
            
            # Add descriptive comment for custom/unknown widgets
            comment = f" // {control_type}: {control['name']}" if control.get('unknown') or control.get('custom_widget') else ""
            
            return f"{widget}{param_str}{comment}"