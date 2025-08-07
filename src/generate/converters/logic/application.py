"""PowerBuilder application object to Flutter/Python converter.

Converts PowerBuilder application objects to Flutter main app configuration
or Python application entry points.
"""

import logging
import re
from dataclasses import dataclass, field
from typing import Any

logger = logging.getLogger(__name__)


@dataclass
class ApplicationVariable:
    """Represents an application-level variable."""

    name: str
    pb_type: str
    dart_type: str
    python_type: str
    initial_value: str | None = None
    is_global: bool = True

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for template rendering."""
        return {
            "name": self.name,
            "pb_type": self.pb_type,
            "dart_type": self.dart_type,
            "python_type": self.python_type,
            "initial_value": self.initial_value,
            "is_global": self.is_global,
        }


@dataclass
class ApplicationEvent:
    """Represents an application event."""

    name: str
    parameters: list[tuple[str, str]] = field(default_factory=list)
    body: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for template rendering."""
        return {
            "name": self.name,
            "parameters": self.parameters,
            "body": self.body,
            "has_parameters": len(self.parameters) > 0,
        }


@dataclass
class DatabaseConfig:
    """Database configuration settings."""

    dbms: str | None = None
    database: str | None = None
    userid: str | None = None
    db_pass: str | None = None
    log_id: str | None = None
    log_pass: str | None = None
    server_name: str | None = None
    db_parm: str | None = None

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for template rendering."""
        return {
            "dbms": self.dbms,
            "database": self.database,
            "userid": self.userid,
            "db_pass": self.db_pass,
            "log_id": self.log_id,
            "log_pass": self.log_pass,
            "server_name": self.server_name,
            "db_parm": self.db_parm,
            "has_database": self.dbms is not None,
        }


@dataclass
class ApplicationDefinition:
    """Represents a PowerBuilder application object."""

    name: str
    app_name: str = ""
    display_name: str = ""
    micro_help: bool = True
    dynamic_micro_help: bool = True
    toolbar_text: bool = True
    toolbar_tips: bool = True

    # Application properties
    variables: list[ApplicationVariable] = field(default_factory=list)
    events: list[ApplicationEvent] = field(default_factory=list)

    # Application settings
    theme: str = "default"
    icon: str | None = None
    splash_screen: str | None = None

    # Database settings
    database_config: DatabaseConfig | None = None
    has_database: bool = False

    # Initial window
    initial_window: str | None = None

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for template rendering."""
        return {
            "name": self.name,
            "app_name": self.app_name or self.name,
            "display_name": self.display_name or self.app_name or self.name,
            "micro_help": self.micro_help,
            "dynamic_micro_help": self.dynamic_micro_help,
            "toolbar_text": self.toolbar_text,
            "toolbar_tips": self.toolbar_tips,
            "variables": [var.to_dict() for var in self.variables],
            "events": [event.to_dict() for event in self.events],
            "has_variables": len(self.variables) > 0,
            "has_events": len(self.events) > 0,
            "theme": self.theme,
            "icon": self.icon,
            "splash_screen": self.splash_screen,
            "has_database": self.database_config is not None
            and self.database_config.dbms is not None,
            "database_config": self.database_config.to_dict()
            if self.database_config
            else None,
            "initial_window": self.initial_window,
        }


class ApplicationConverter:
    """Converts PowerBuilder application objects to Flutter/Python apps."""

    def __init__(self, type_converter=None) -> None:
        """Initialize the application converter.

        Args:
            type_converter: Type converter for variable types
        """
        self.type_converter = type_converter
        if not self.type_converter:
            from .types import TypeConverter

            self.type_converter = TypeConverter()

    def convert_application(
        self, app_syntax: str, app_name: str
    ) -> ApplicationDefinition:
        """Convert PowerBuilder application syntax to ApplicationDefinition.

        Args:
            app_syntax: PowerBuilder application syntax/source
            app_name: Name of the application

        Returns:
            ApplicationDefinition object
        """
        definition = ApplicationDefinition(name=self._to_pascal_case(app_name))

        # Extract basic properties
        self._extract_properties(app_syntax, definition)

        # Extract variables
        definition.variables = self._extract_variables(app_syntax)

        # Extract events
        definition.events = self._extract_events(app_syntax)

        # Extract database configuration
        self._extract_database_config(app_syntax, definition)

        # Extract initial window
        definition.initial_window = self._extract_initial_window(app_syntax)

        return definition

    def _extract_properties(
        self, syntax: str, definition: ApplicationDefinition
    ) -> None:
        """Extract application properties."""
        # App name
        app_name_match = re.search(r'appname\s*=\s*"([^"]*)"', syntax, re.IGNORECASE)
        if app_name_match:
            definition.app_name = app_name_match.group(1)

        # Display name
        display_match = re.search(r'displayname\s*=\s*"([^"]*)"', syntax, re.IGNORECASE)
        if display_match:
            definition.display_name = display_match.group(1)

        # Micro help settings
        micro_help_match = re.search(
            r"microhelp\s*=\s*(true|false)", syntax, re.IGNORECASE
        )
        if micro_help_match:
            definition.micro_help = micro_help_match.group(1).lower() == "true"

        dynamic_help_match = re.search(
            r"dynamicmicrohelp\s*=\s*(true|false)", syntax, re.IGNORECASE
        )
        if dynamic_help_match:
            definition.dynamic_micro_help = (
                dynamic_help_match.group(1).lower() == "true"
            )

        # Toolbar settings
        toolbar_text_match = re.search(
            r"toolbartext\s*=\s*(true|false)", syntax, re.IGNORECASE
        )
        if toolbar_text_match:
            definition.toolbar_text = toolbar_text_match.group(1).lower() == "true"

        toolbar_tips_match = re.search(
            r"toolbartips\s*=\s*(true|false)", syntax, re.IGNORECASE
        )
        if toolbar_tips_match:
            definition.toolbar_tips = toolbar_tips_match.group(1).lower() == "true"

        # Icon
        icon_match = re.search(r'icon\s*=\s*"([^"]*)"', syntax, re.IGNORECASE)
        if icon_match:
            definition.icon = icon_match.group(1)

    def _extract_variables(self, syntax: str) -> list[ApplicationVariable]:
        """Extract application variables."""
        variables = []

        # Global variables pattern
        global_pattern = r"global\s+(\w+)\s+(\w+)(?:\s*=\s*([^\n]+))?"
        global_matches = re.findall(global_pattern, syntax, re.IGNORECASE)

        for pb_type, var_name, initial_value in global_matches:
            dart_type = self.type_converter.convert_type(pb_type)
            python_type = self._convert_to_python_type(pb_type)

            var = ApplicationVariable(
                name=var_name,
                pb_type=pb_type,
                dart_type=dart_type,
                python_type=python_type,
                initial_value=initial_value.strip() if initial_value else None,
                is_global=True,
            )
            variables.append(var)

        # Instance variables pattern
        instance_pattern = (
            r"(?:public|private|protected)?\s*(\w+)\s+(\w+)(?:\s*=\s*([^;\n]+))?"
        )
        instance_matches = re.findall(instance_pattern, syntax, re.IGNORECASE)

        for pb_type, var_name, initial_value in instance_matches:
            # Skip if already added as global
            if any(v.name == var_name for v in variables):
                continue

            # Skip common keywords
            if pb_type.lower() in [
                "global",
                "type",
                "from",
                "end",
                "on",
                "event",
            ]:
                continue

            dart_type = self.type_converter.convert_type(pb_type)
            python_type = self._convert_to_python_type(pb_type)

            var = ApplicationVariable(
                name=var_name,
                pb_type=pb_type,
                dart_type=dart_type,
                python_type=python_type,
                initial_value=initial_value.strip() if initial_value else None,
                is_global=False,
            )
            variables.append(var)

        return variables

    def _extract_events(self, syntax: str) -> list[ApplicationEvent]:
        """Extract application events."""
        events = []

        # Common application events
        event_names = [
            "open",
            "close",
            "idle",
            "systemerror",
            "connectionbegin",
            "connectionend",
        ]

        for event_name in event_names:
            # Look for event implementation
            event_pattern = rf"event\s+{event_name}\s*\(([^)]*)\).*?end\s+event"
            event_match = re.search(event_pattern, syntax, re.IGNORECASE | re.DOTALL)

            if event_match:
                event = ApplicationEvent(name=event_name)

                # Extract parameters
                params_str = event_match.group(1).strip()
                if params_str:
                    param_parts = params_str.split(",")
                    for param in param_parts:
                        param = param.strip()
                        if " " in param:
                            param_type, param_name = param.rsplit(" ", 1)
                            event.parameters.append(
                                (param_type.strip(), param_name.strip())
                            )

                # Extract body (simplified - just capture main logic indicators)
                body_text = event_match.group(0)

                # Look for key operations
                if "open(" in body_text.lower():
                    event.body.append("// Open initial window")
                if "connect" in body_text.lower():
                    event.body.append("// Connect to database")
                if "sqlca" in body_text.lower():
                    event.body.append("// Initialize SQLCA")
                if "transaction" in body_text.lower():
                    event.body.append("// Setup transaction")

                events.append(event)

        return events

    def _extract_database_config(
        self, syntax: str, definition: ApplicationDefinition
    ) -> None:
        """Extract database configuration."""
        # Create database config if needed
        config = DatabaseConfig()

        # SQLCA properties
        sqlca_pattern = r'sqlca\.(\w+)\s*=\s*"([^"]*)"'
        sqlca_matches = re.findall(sqlca_pattern, syntax, re.IGNORECASE)

        for prop, value in sqlca_matches:
            prop_lower = prop.lower()
            if prop_lower == "dbms":
                config.dbms = value
            elif prop_lower == "database":
                config.database = value
            elif prop_lower == "userid":
                config.userid = value
            elif prop_lower == "dbpass":
                config.db_pass = value
            elif prop_lower == "logid":
                config.log_id = value
            elif prop_lower == "logpass":
                config.log_pass = value
            elif prop_lower == "servername":
                config.server_name = value
            elif prop_lower == "dbparm":
                config.db_parm = value

        # Only set if we found database config
        if config.dbms:
            definition.database_config = config

    def _extract_initial_window(self, syntax: str) -> str | None:
        """Extract the initial window to open."""
        # Look in open event
        open_pattern = r"event\s+open.*?open\s*\(\s*(\w+)\s*\)"
        open_match = re.search(open_pattern, syntax, re.IGNORECASE | re.DOTALL)

        if open_match:
            return open_match.group(1)

        # Alternative pattern
        window_pattern = r"open\s*\(\s*(\w+)\s*\)"
        window_match = re.search(window_pattern, syntax, re.IGNORECASE)

        if window_match:
            return window_match.group(1)

        return None

    def _convert_to_python_type(self, pb_type: str) -> str:
        """Convert PowerBuilder type to Python type."""
        type_map = {
            "integer": "int",
            "long": "int",
            "decimal": "float",
            "real": "float",
            "double": "float",
            "boolean": "bool",
            "string": "str",
            "char": "str",
            "date": "datetime.date",
            "time": "datetime.time",
            "datetime": "datetime.datetime",
            "blob": "bytes",
        }

        pb_type_lower = pb_type.lower()
        return type_map.get(pb_type_lower, "Any")

    def _to_pascal_case(self, name: str) -> str:
        """Convert name to PascalCase."""
        # Remove common prefixes
        name = name.removeprefix("n_")

        # Convert to PascalCase
        parts = name.split("_")
        return "".join(p.capitalize() for p in parts)

    def generate_flutter_main(
        self, app_def: ApplicationDefinition
    ) -> dict[str, list[str]]:
        """Generate Flutter main.dart file content.

        Returns:
            Dictionary with different sections of main.dart
        """
        code: dict[str, list[str]] = {
            "imports": [],
            "globals": [],
            "main_function": [],
            "app_class": [],
            "app_state": [],
        }

        # Imports
        code["imports"] = [
            "import 'package:flutter/material.dart';",
            "import 'package:flutter/services.dart';",
            "import 'core/app_design_system.dart';",
            "import 'core/database_helper.dart';",
            "import 'core/global_state.dart';",
        ]

        if app_def.initial_window:
            window_name = self._to_pascal_case(app_def.initial_window)
            code["imports"].append(
                f"import 'windows/{self._to_snake_case(window_name)}.dart';"
            )

        # Global variables
        if app_def.variables:
            code["globals"].append("// Global variables")
            for var in app_def.variables:
                if var.is_global:
                    init_val = var.initial_value or self._get_default_value(
                        var.dart_type
                    )
                    code["globals"].append(
                        f"late {var.dart_type} {var.name} = {init_val};"
                    )

        # Main function
        code["main_function"] = [
            "void main() async {",
            "  WidgetsFlutterBinding.ensureInitialized();",
            "",
        ]

        if app_def.has_database:
            code["main_function"].extend(
                [
                    "  // Initialize database",
                    "  await DatabaseHelper.instance.initDatabase();",
                    "",
                ]
            )

        # Handle open event
        open_event = next((e for e in app_def.events if e.name == "open"), None)
        if open_event:
            code["main_function"].extend(
                [
                    "  // Application open event",
                    "  await _applicationOpen();",
                    "",
                ]
            )

        code["main_function"].extend(
            [
                f"  runApp({app_def.name}App());",
                "}",
            ]
        )

        # App class
        code["app_class"] = self._generate_flutter_app_class(app_def)

        # App state (for stateful initial window)
        if app_def.initial_window:
            code["app_state"] = self._generate_flutter_app_state(app_def)

        # Event implementations
        if app_def.events:
            code["app_class"].extend(self._generate_flutter_events(app_def))

        return code

    def _generate_flutter_app_class(self, app_def: ApplicationDefinition) -> list[str]:
        """Generate Flutter app class."""
        lines = []

        lines.append(f"class {app_def.name}App extends StatelessWidget {{")
        lines.append("  @override")
        lines.append("  Widget build(BuildContext context) {")
        lines.append("    return MaterialApp(")
        lines.append(f'      title: "{app_def.display_name}",')
        lines.append("      theme: AppDesignSystem.lightTheme,")
        lines.append("      darkTheme: AppDesignSystem.darkTheme,")
        lines.append("      themeMode: ThemeMode.system,")

        if app_def.initial_window:
            window_name = self._to_pascal_case(app_def.initial_window)
            lines.append(f"      home: {window_name}(),")
        else:
            lines.append("      home: Scaffold(")
            lines.append(
                '        appBar: AppBar(title: Text("' + app_def.display_name + '")),'
            )
            lines.append(
                '        body: Center(child: Text("No initial window specified")),'
            )
            lines.append("      ),")

        lines.append("      debugShowCheckedModeBanner: false,")
        lines.append("    );")
        lines.append("  }")
        lines.append("}")

        return lines

    def _generate_flutter_app_state(self, app_def: ApplicationDefinition) -> list[str]:
        """Generate Flutter app state class if needed."""
        lines: list[str] = []

        if not app_def.variables or all(v.is_global for v in app_def.variables):
            return lines

        lines.append(f"class {app_def.name}State extends ChangeNotifier {{")
        lines.append("  // Application instance variables")

        for var in app_def.variables:
            if not var.is_global:
                init_val = var.initial_value or self._get_default_value(var.dart_type)
                lines.append(f"  {var.dart_type} _{var.name} = {init_val};")

        lines.append("")

        # Getters and setters
        for var in app_def.variables:
            if not var.is_global:
                lines.append(f"  {var.dart_type} get {var.name} => _{var.name};")
                lines.append(f"  set {var.name}({var.dart_type} value) {{")
                lines.append(f"    _{var.name} = value;")
                lines.append("    notifyListeners();")
                lines.append("  }")
                lines.append("")

        lines.append("}")

        return lines

    def _generate_flutter_events(self, app_def: ApplicationDefinition) -> list[str]:
        """Generate Flutter event implementations."""
        lines = []

        for event in app_def.events:
            lines.append("")
            if event.name == "open":
                lines.append("Future<void> _applicationOpen() async {")
            else:
                params = ", ".join(
                    f"{self.type_converter.convert_type(t)} {n}"
                    for t, n in event.parameters
                )
                lines.append(f"void _application{event.name.capitalize()}({params}) {{")

            for body_line in event.body:
                lines.append(f"  {body_line}")

            lines.append("  // TODO: Implement application " + event.name + " event")
            lines.append("}")

        return lines

    def generate_python_main(
        self, app_def: ApplicationDefinition
    ) -> dict[str, list[str]]:
        """Generate Python application entry point.

        Returns:
            Dictionary with different sections of the main file
        """
        code: dict[str, list[str]] = {
            "imports": [],
            "globals": [],
            "app_class": [],
            "main_block": [],
        }

        # Imports
        code["imports"] = [
            "#!/usr/bin/env python3",
            '"""'
            + app_def.display_name
            + ' - Generated from PowerBuilder Application"""',
            "",
            "import sys",
            "import tkinter as tk",
            "from tkinter import ttk, messagebox",
            "import logging",
            "from typing import Optional",
        ]

        if app_def.has_database:
            code["imports"].extend(
                [
                    "from sqlalchemy import create_engine",
                    "from sqlalchemy.orm import sessionmaker",
                    "from .models import Base",
                ]
            )

        if app_def.initial_window:
            window_name = self._to_pascal_case(app_def.initial_window)
            code["imports"].append(
                f"from .windows.{self._to_snake_case(window_name)} import {window_name}"
            )

        # Global variables
        if app_def.variables:
            code["globals"].append("")
            code["globals"].append("# Global variables")
            for var in app_def.variables:
                if var.is_global:
                    init_val = var.initial_value or self._get_python_default_value(
                        var.python_type
                    )
                    code["globals"].append(
                        f"{var.name}: {var.python_type} = {init_val}"
                    )

        # App class
        code["app_class"] = self._generate_python_app_class(app_def)

        # Main block
        code["main_block"] = [
            "",
            'if __name__ == "__main__":',
            "    # Configure logging",
            '    logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")',
            "    ",
            "    # Create and run application",
            f"    app = {app_def.name}Application()",
            "    app.run()",
        ]

        return code

    def _generate_python_app_class(self, app_def: ApplicationDefinition) -> list[str]:
        """Generate Python application class."""
        lines = []

        lines.append(f"class {app_def.name}Application:")
        lines.append('    """Main application class."""')
        lines.append("    ")
        lines.append("    def __init__(self):")
        lines.append('        """Initialize the application."""')
        lines.append("        self.root = None")
        lines.append("        self.main_window = None")

        if app_def.has_database:
            lines.append("        self.engine = None")
            lines.append("        self.session_factory = None")

        # Instance variables
        for var in app_def.variables:
            if not var.is_global:
                init_val = var.initial_value or self._get_python_default_value(
                    var.python_type
                )
                lines.append(f"        self.{var.name}: {var.python_type} = {init_val}")

        lines.append("    ")
        lines.append("    def run(self):")
        lines.append('        """Run the application."""')

        # Handle open event
        open_event = next((e for e in app_def.events if e.name == "open"), None)
        if open_event or app_def.has_database:
            lines.append("        # Initialize application")
            lines.append("        self._application_open()")
            lines.append("        ")

        lines.append("        # Create main window")
        lines.append("        self.root = tk.Tk()")
        lines.append(f'        self.root.title("{app_def.display_name}")')
        lines.append(
            '        self.root.protocol("WM_DELETE_WINDOW", self._application_close)'
        )
        lines.append("        ")

        if app_def.initial_window:
            window_name = self._to_pascal_case(app_def.initial_window)
            lines.append("        # Open initial window")
            lines.append(f"        self.main_window = {window_name}()")
            lines.append("        self.main_window.mainloop()")
        else:
            lines.append("        # No initial window specified")
            lines.append(
                '        label = ttk.Label(self.root, text="No initial window specified")'
            )
            lines.append("        label.pack(padx=20, pady=20)")
            lines.append("        self.root.mainloop()")

        # Event methods
        if app_def.events:
            lines.extend(self._generate_python_events(app_def))
        else:
            # Add default event handlers
            lines.append("    ")
            lines.append("    def _application_open(self):")
            lines.append('        """Handle application open event."""')

            if app_def.has_database:
                lines.append("        # Initialize database")
                lines.append("        self._init_database()")
            else:
                lines.append("        pass")

            lines.append("    ")
            lines.append("    def _application_close(self):")
            lines.append('        """Handle application close event."""')
            lines.append("        if self.root:")
            lines.append("            self.root.destroy()")

        # Database initialization
        if app_def.has_database:
            lines.extend(self._generate_python_database_init(app_def))

        return lines

    def _generate_python_events(self, app_def: ApplicationDefinition) -> list[str]:
        """Generate Python event method implementations."""
        lines = []

        for event in app_def.events:
            lines.append("    ")
            params = ["self"] + [
                f"{n}: {self._convert_to_python_type(t)}" for t, n in event.parameters
            ]
            lines.append(f"    def _application_{event.name}({', '.join(params)}):")
            lines.append(f'        """Handle application {event.name} event."""')

            if event.body:
                for body_line in event.body:
                    lines.append(f"        {body_line}")

            lines.append(f"        # TODO: Implement application {event.name} event")

            if event.name == "close":
                lines.append("        if self.root:")
                lines.append("            self.root.destroy()")

        return lines

    def _generate_python_database_init(
        self, app_def: ApplicationDefinition
    ) -> list[str]:
        """Generate Python database initialization code."""
        lines: list[str] = []

        if not app_def.database_config:
            return lines

        lines.append("    ")
        lines.append("    def _init_database(self):")
        lines.append('        """Initialize database connection."""')
        lines.append("        try:")

        # Build connection string based on DBMS
        if app_def.database_config.dbms:
            dbms_lower = app_def.database_config.dbms.lower()

            if "sqlite" in dbms_lower:
                db_path = app_def.database_config.database or "app.db"
                lines.append(
                    f'            self.engine = create_engine("sqlite:///{db_path}")'
                )
            elif "postgresql" in dbms_lower or "postgres" in dbms_lower:
                lines.append("            connection_string = (")
                lines.append(
                    f'                "postgresql://{app_def.database_config.userid or "user"}:"'
                )
                lines.append(
                    f'                "{app_def.database_config.db_pass or "password"}@"'
                )
                lines.append(
                    f'                "{app_def.database_config.server_name or "localhost"}/"'
                )
                lines.append(
                    f'                "{app_def.database_config.database or "database"}"'
                )
                lines.append("            )")
                lines.append(
                    "            self.engine = create_engine(connection_string)"
                )
            elif "mysql" in dbms_lower:
                lines.append("            connection_string = (")
                lines.append(
                    f'                "mysql+pymysql://{app_def.database_config.userid or "user"}:"'
                )
                lines.append(
                    f'                "{app_def.database_config.db_pass or "password"}@"'
                )
                lines.append(
                    f'                "{app_def.database_config.server_name or "localhost"}/"'
                )
                lines.append(
                    f'                "{app_def.database_config.database or "database"}"'
                )
                lines.append("            )")
                lines.append(
                    "            self.engine = create_engine(connection_string)"
                )
            else:
                lines.append(
                    f"            # TODO: Configure {app_def.database_config.dbms} connection"
                )
                lines.append("            self.engine = None")
        else:
            lines.append("            # TODO: Configure database connection")
            lines.append("            self.engine = None")

        lines.append("            ")
        lines.append("            if self.engine:")
        lines.append("                # Create tables if needed")
        lines.append("                Base.metadata.create_all(self.engine)")
        lines.append("                ")
        lines.append("                # Create session factory")
        lines.append(
            "                self.session_factory = sessionmaker(bind=self.engine)"
        )
        lines.append("                ")
        lines.append(
            '                logging.info("Database initialized successfully")'
        )
        lines.append("        except Exception as e:")
        lines.append(
            '            logging.error("Failed to initialize database: %s", e)'
        )
        lines.append(
            '            messagebox.showerror("Database Error", f"Failed to connect to database: {e}")'
        )

        return lines

    def _get_default_value(self, dart_type: str) -> str:
        """Get default value for Dart type."""
        defaults = {
            "int": "0",
            "double": "0.0",
            "String": '""',
            "bool": "false",
            "DateTime": "DateTime.now()",
            "List": "[]",
            "Map": "{}",
        }

        # Handle generic types
        if dart_type.startswith("List<"):
            return "[]"
        if dart_type.startswith("Map<"):
            return "{}"

        return defaults.get(dart_type, "null")

    def _get_python_default_value(self, python_type: str) -> str:
        """Get default value for Python type."""
        defaults = {
            "int": "0",
            "float": "0.0",
            "str": '""',
            "bool": "False",
            "datetime.date": "datetime.date.today()",
            "datetime.time": "datetime.time()",
            "datetime.datetime": "datetime.datetime.now()",
            "list": "[]",
            "dict": "{}",
            "bytes": 'b""',
        }

        return defaults.get(python_type, "None")

    def _to_snake_case(self, name: str) -> str:
        """Convert name to snake_case."""
        s1 = re.sub("(.)([A-Z][a-z]+)", r"\1_\2", name)
        return re.sub("([a-z0-9])([A-Z])", r"\1_\2", s1).lower()
