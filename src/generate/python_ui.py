"""Python UI generator for creating Python GUI code from PowerBuilder UI definitions."""

import logging
from typing import Any

from .base import CodeGenerator

logger = logging.getLogger(__name__)


class PythonUIGenerator(CodeGenerator):
    """Generate Python UI code from PowerBuilder windows and controls."""

    def __init__(
        self, template_dir: str, output_dir: str, ui_framework: str = "tkinter"
    ) -> None:
        """Initialize the Python UI generator.

        Args:
            template_dir: Directory containing UI templates
            output_dir: Directory for generated UI code
            ui_framework: Target UI framework ('tkinter', 'pyqt5', 'kivy', 'wxpython')
        """
        super().__init__(template_dir, output_dir)
        self.ui_framework = ui_framework
        self.control_mapping = self._get_control_mapping()

    def _get_control_mapping(self) -> dict[str, str]:
        """Get PowerBuilder to Python UI control mappings."""
        if self.ui_framework == "tkinter":
            return {
                "window": "Toplevel",
                "commandbutton": "Button",
                "statictext": "Label",
                "singlelineedit": "Entry",
                "multilineedit": "Text",
                "checkbox": "Checkbutton",
                "radiobutton": "Radiobutton",
                "listbox": "Listbox",
                "dropdownlistbox": "Combobox",
                "picturebutton": "Button",
                "picturebox": "Label",
                "groupbox": "LabelFrame",
                "line": "Frame",
                "rectangle": "Frame",
                "datawindow": "Frame",  # Custom widget needed
                "treeview": "Treeview",
                "tab": "Notebook",
                "menu": "Menu",
            }
        if self.ui_framework == "pyqt5":
            return {
                "window": "QMainWindow",
                "commandbutton": "QPushButton",
                "statictext": "QLabel",
                "singlelineedit": "QLineEdit",
                "multilineedit": "QTextEdit",
                "checkbox": "QCheckBox",
                "radiobutton": "QRadioButton",
                "listbox": "QListWidget",
                "dropdownlistbox": "QComboBox",
                "picturebutton": "QPushButton",
                "picturebox": "QLabel",
                "groupbox": "QGroupBox",
                "line": "QFrame",
                "rectangle": "QFrame",
                "datawindow": "QTableWidget",
                "treeview": "QTreeWidget",
                "tab": "QTabWidget",
                "menu": "QMenuBar",
            }
        return {}

    def generate_window(self, window_model: dict[str, Any]) -> str:
        """Generate a Python window class.

        Args:
            window_model: Window model with properties, controls, and events

        Returns:
            Generated Python window code
        """
        # Prepare context for template
        context = {
            "class_name": self._to_class_name(window_model.get("name", "Window")),
            "window_title": window_model.get("title", "Window"),
            "width": window_model.get("width", 800),
            "height": window_model.get("height", 600),
            "controls": self._process_controls(window_model.get("controls", [])),
            "events": self._process_events(window_model.get("events", [])),
            "imports": self._get_required_imports(window_model),
            "ui_framework": self.ui_framework,
            "has_menu": any(
                c.get("type") == "menu" for c in window_model.get("controls", [])
            ),
            "has_datawindow": any(
                c.get("type") == "datawindow" for c in window_model.get("controls", [])
            ),
        }

        # Select template based on UI framework
        template_name = f"window_{self.ui_framework}.py.jinja2"

        try:
            return self.render_template(template_name, context)
        except Exception as e:
            logger.error(
                "Failed to generate window %s: %s", window_model.get("name"), e
            )
            # Fallback to simple window generation
            return self._generate_simple_window(context)

    def _process_controls(self, controls: list[dict[str, Any]]) -> list[dict[str, Any]]:
        """Process control definitions for template."""
        processed = []
        for ctrl in controls:
            control_type = ctrl.get("type", "").lower()
            processed_ctrl = {
                "name": ctrl.get("name", ""),
                "type": control_type,
                "widget_type": self.control_mapping.get(control_type, "Frame"),
                "text": ctrl.get("text", ""),
                "x": ctrl.get("x", 0),
                "y": ctrl.get("y", 0),
                "width": ctrl.get("width", 100),
                "height": ctrl.get("height", 30),
                "visible": ctrl.get("visible", True),
                "enabled": ctrl.get("enabled", True),
                "font": ctrl.get("font", {}),
                "properties": ctrl.get("properties", {}),
            }

            # Special handling for specific control types
            if control_type == "datawindow":
                processed_ctrl["dataobject"] = ctrl.get("dataobject", "")
                processed_ctrl["columns"] = ctrl.get("columns", [])
            elif control_type in ("dropdownlistbox", "listbox"):
                processed_ctrl["items"] = ctrl.get("items", [])
            elif control_type == "picturebutton":
                processed_ctrl["image"] = ctrl.get("picturename", "")

            processed.append(processed_ctrl)
        return processed

    def _process_events(self, events: list[dict[str, Any]]) -> list[dict[str, Any]]:
        """Process event definitions for template."""
        processed = []
        for event in events:
            processed_event = {
                "name": event.get("name", ""),
                "control": event.get("control", ""),
                "event_type": self._map_event_type(event.get("type", "")),
                "code": event.get("code", ""),
                "parameters": event.get("parameters", []),
            }
            processed.append(processed_event)
        return processed

    def _map_event_type(self, pb_event: str) -> str:
        """Map PowerBuilder event to Python UI framework event."""
        event_map = {
            "clicked": "command" if self.ui_framework == "tkinter" else "clicked",
            "modified": "changed",
            "getfocus": "focus_in",
            "losefocus": "focus_out",
            "constructor": "__init__",
            "destructor": "__del__",
            "open": "show",
            "close": "destroy",
        }
        return event_map.get(pb_event.lower(), pb_event.lower())

    def _get_required_imports(self, window_model: dict[str, Any]) -> list[str]:
        """Get required imports based on controls and framework."""
        imports = []

        if self.ui_framework == "tkinter":
            imports.append("import tkinter as tk")
            imports.append("from tkinter import ttk")

            # Check for specific widgets
            control_types = {
                c.get("type", "").lower() for c in window_model.get("controls", [])
            }
            if "dropdownlistbox" in control_types:
                imports.append("from tkinter.ttk import Combobox")
            if "treeview" in control_types:
                imports.append("from tkinter.ttk import Treeview")
            if "tab" in control_types:
                imports.append("from tkinter.ttk import Notebook")

        elif self.ui_framework == "pyqt5":
            imports.append("from PyQt5.QtWidgets import *")
            imports.append("from PyQt5.QtCore import *")
            imports.append("from PyQt5.QtGui import *")

        return imports

    def _to_class_name(self, name: str) -> str:
        """Convert PowerBuilder name to Python class name."""
        # Remove common prefixes
        name = name.lower()
        for prefix in ["w_", "win_", "window_"]:
            name = name.removeprefix(prefix)

        # Convert to PascalCase
        parts = name.replace("-", "_").split("_")
        return "".join(part.capitalize() for part in parts if part) + "Window"

    def _generate_simple_window(self, context: dict[str, Any]) -> str:
        """Generate a simple window class as fallback."""
        if self.ui_framework == "tkinter":
            lines = ["import tkinter as tk", ""]
            lines.append(f"class {context['class_name']}(tk.Tk):")
            lines.append('    """Generated window class."""')
            lines.append("    ")
            lines.append("    def __init__(self):")
            lines.append("        super().__init__()")
            lines.append(f"        self.title('{context['window_title']}')")
            lines.append(
                f"        self.geometry('{context['width']}x{context['height']}')"
            )
            lines.append("        self.create_widgets()")
            lines.append("    ")
            lines.append("    def create_widgets(self):")
            lines.append('        """Create and layout widgets."""')

            for ctrl in context["controls"]:
                widget_type = ctrl["widget_type"]
                name = ctrl["name"]
                if widget_type in {"Button", "Label"}:
                    lines.append(
                        f"        self.{name} = tk.{widget_type}(self, text='{ctrl['text']}')"
                    )
                elif widget_type == "Entry":
                    lines.append(f"        self.{name} = tk.{widget_type}(self)")
                else:
                    lines.append(f"        self.{name} = tk.{widget_type}(self)")
                lines.append(
                    f"        self.{name}.place(x={ctrl['x']}, y={ctrl['y']}, width={ctrl['width']}, height={ctrl['height']})"
                )

            return "\n".join(lines)

        return f"# UI generation not implemented for {self.ui_framework}"
