"""Business logic mapper for PowerBuilder applications.

This module maps business logic functions to database operations and UI elements,
creating a comprehensive understanding of how data flows through the application.
"""

import logging
import re
from collections import defaultdict
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)


@dataclass
class DatabaseOperation:
    """Represents a database operation."""

    operation_type: str  # SELECT, INSERT, UPDATE, DELETE
    table_name: str
    columns: list[str] = field(default_factory=list)
    where_clause: str | None = None
    line_number: int | None = None


@dataclass
class BusinessFunction:
    """Represents a business logic function."""

    name: str
    object_name: str
    parameters: list[str] = field(default_factory=list)
    return_type: str | None = None
    accessed_tables: set[str] = field(default_factory=set)
    operations: list[DatabaseOperation] = field(default_factory=list)
    called_functions: set[str] = field(default_factory=set)
    ui_elements: set[str] = field(default_factory=set)
    description: str | None = None
    line_number: int | None = None

    def add_table_access(self, table: str, _operation: str) -> None:
        """Add a table access record."""
        self.accessed_tables.add(table)

    def add_ui_element(self, element: str) -> None:
        """Add a UI element that this function interacts with."""
        self.ui_elements.add(element)


@dataclass
class UIElement:
    """Represents a UI element (window, datawindow, control)."""

    name: str
    type: str  # Window, DataWindow, Button, etc.
    parent_object: str
    data_source: str | None = None  # For DataWindows
    accessed_tables: set[str] = field(default_factory=set)
    bound_columns: list[str] = field(default_factory=list)
    event_handlers: dict[str, str] = field(default_factory=dict)  # event -> function
    child_elements: list[str] = field(default_factory=list)

    def add_event_handler(self, event: str, function: str) -> None:
        """Add an event handler."""
        self.event_handlers[event] = function


@dataclass
class DataFlow:
    """Represents data flow between components."""

    source_component: str
    source_type: str  # Table, Function, UI
    target_component: str
    target_type: str  # Table, Function, UI
    data_elements: list[str] = field(default_factory=list)
    operation: str | None = None  # READ, WRITE, TRANSFORM
    description: str | None = None


class BusinessLogicExtractor:
    """Extracts and maps business logic from PowerBuilder code."""

    # SQL operation patterns
    SQL_PATTERNS = {
        "SELECT": re.compile(
            r"SELECT\s+(.+?)\s+FROM\s+(\w+)", re.IGNORECASE | re.DOTALL
        ),
        "INSERT": re.compile(r"INSERT\s+INTO\s+(\w+)\s*\(([^)]+)\)", re.IGNORECASE),
        "UPDATE": re.compile(
            r"UPDATE\s+(\w+)\s+SET\s+(.+?)(?:\s+WHERE|$)", re.IGNORECASE | re.DOTALL
        ),
        "DELETE": re.compile(
            r"DELETE\s+FROM\s+(\w+)(?:\s+WHERE\s+(.+))?", re.IGNORECASE
        ),
    }

    # DataWindow operation patterns
    DW_PATTERNS = {
        "retrieve": re.compile(r"(\w+)\.Retrieve\s*\(", re.IGNORECASE),
        "update": re.compile(r"(\w+)\.Update\s*\(", re.IGNORECASE),
        "setitem": re.compile(
            r"(\w+)\.SetItem\s*\(\s*(\d+)\s*,\s*[\"'](\w+)[\"']", re.IGNORECASE
        ),
        "getitem": re.compile(
            r"(\w+)\.GetItem\s*\(\s*(\d+)\s*,\s*[\"'](\w+)[\"']", re.IGNORECASE
        ),
        "setsqlselect": re.compile(
            r"(\w+)\.SetSQLSelect\s*\([\"'](.+?)[\"']\)", re.IGNORECASE | re.DOTALL
        ),
    }

    # Function call patterns
    FUNCTION_PATTERNS = {
        "call": re.compile(r"(\w+)\s*\("),
        "dynamic_call": re.compile(r"DYNAMIC\s+(\w+)"),
        "trigger": re.compile(r"(\w+)\.TriggerEvent\s*\([\"'](\w+)[\"']"),
        "post": re.compile(r"(\w+)\.PostEvent\s*\([\"'](\w+)[\"']"),
    }

    def __init__(self) -> None:
        """Initialize the business logic extractor."""
        self.functions: dict[str, BusinessFunction] = {}
        self.ui_elements: dict[str, UIElement] = {}
        self.data_flows: list[DataFlow] = []
        self.table_dependencies: dict[str, set[str]] = defaultdict(set)

    def extract_from_object(
        self, object_name: str, content: str, object_type: str
    ) -> None:
        """Extract business logic from a PowerBuilder object.

        Args:
            object_name: Name of the object
            content: Object content
            object_type: Type of object (window, userobject, etc.)
        """
        lines = content.split("\n")

        if object_type in ["window", "userobject"]:
            self._extract_ui_logic(object_name, lines)
        elif object_type in ["function", "event"]:
            self._extract_function_logic(object_name, lines)
        else:
            # Try to extract any functions/events
            self._extract_mixed_logic(object_name, lines)

    def _extract_ui_logic(self, object_name: str, lines: list[str]) -> None:
        """Extract logic from UI objects (windows, user objects)."""
        current_control = None
        current_event = None

        for i, line in enumerate(lines):
            # Check for control definitions
            if "type " in line and " from " in line:
                parts = line.strip().split()
                if len(parts) >= 4:
                    control_type = parts[0]
                    control_name = parts[1]
                    ui_element = UIElement(
                        name=control_name,
                        type=control_type,
                        parent_object=object_name,
                    )
                    self.ui_elements[control_name] = ui_element
                    current_control = ui_element

            # Check for DataWindow assignments
            if current_control and "dataobject" in line.lower():
                match = re.search(r'dataobject\s*=\s*["\'](\w+)["\']', line)
                if match and current_control:
                    current_control.data_source = match.group(1)

            # Check for event handlers
            if line.strip().startswith("event "):
                event_match = re.match(r"event\s+(\w+)(?:\s|$)", line.strip())
                if event_match:
                    current_event = event_match.group(1)

            # Extract SQL and function calls within events
            if current_event:
                self._extract_sql_operations(
                    line, f"{object_name}.{current_event}", i + 1
                )
                self._extract_function_calls(
                    line, f"{object_name}.{current_event}", i + 1
                )

            # Check for end of event
            if line.strip() == "end event":
                current_event = None

    def _extract_function_logic(self, object_name: str, lines: list[str]) -> None:
        """Extract logic from function objects."""
        function_name = None
        function_obj = None

        for i, line in enumerate(lines):
            # Check for function definition
            if re.match(r"(function|subroutine|event)\s+\w+", line, re.IGNORECASE):
                match = re.match(
                    r"(function|subroutine|event)\s+(\w+)(?:\s+(\w+))?\s*\((.*?)\)",
                    line,
                    re.IGNORECASE,
                )
                if match:
                    func_type = match.group(1)
                    return_type = match.group(2) if match.group(3) else None
                    func_name = match.group(3) if match.group(3) else match.group(2)
                    params = match.group(4)

                    function_name = f"{object_name}.{func_name}"
                    function_obj = BusinessFunction(
                        name=func_name,
                        object_name=object_name,
                        return_type=return_type,
                        line_number=i + 1,
                    )

                    # Parse parameters
                    if params:
                        function_obj.parameters = [
                            p.strip() for p in params.split(",") if p.strip()
                        ]

                    self.functions[function_name] = function_obj

            # Extract operations within function
            if function_obj:
                self._extract_sql_operations(line, function_name, i + 1)
                self._extract_function_calls(line, function_name, i + 1)
                self._extract_dw_operations(line, function_name, i + 1)

            # Check for end of function
            if re.match(r"end\s+(function|subroutine|event)", line, re.IGNORECASE):
                function_name = None
                function_obj = None

    def _extract_mixed_logic(self, object_name: str, lines: list[str]) -> None:
        """Extract logic from mixed object types."""
        # Combine UI and function extraction logic
        self._extract_ui_logic(object_name, lines)
        self._extract_function_logic(object_name, lines)

    def _extract_sql_operations(
        self, line: str, context: str, line_number: int
    ) -> None:
        """Extract SQL operations from a line of code."""
        for op_type, pattern in self.SQL_PATTERNS.items():
            match = pattern.search(line)
            if match:
                if op_type == "SELECT":
                    columns_str = match.group(1)
                    table = match.group(2)
                    columns = [c.strip() for c in columns_str.split(",") if c.strip()]
                elif op_type in ["INSERT", "UPDATE"]:
                    table = match.group(1)
                    columns = []
                    if op_type == "INSERT" and match.group(2):
                        columns = [
                            c.strip() for c in match.group(2).split(",") if c.strip()
                        ]
                elif op_type == "DELETE":
                    table = match.group(1)
                    columns = []
                else:
                    continue

                operation = DatabaseOperation(
                    operation_type=op_type,
                    table_name=table,
                    columns=columns,
                    line_number=line_number,
                )

                # Add to current function if exists
                if context in self.functions:
                    self.functions[context].operations.append(operation)
                    self.functions[context].add_table_access(table, op_type)

                # Track table dependencies
                self.table_dependencies[table].add(context)

    def _extract_function_calls(
        self, line: str, context: str, line_number: int
    ) -> None:
        """Extract function calls from a line of code."""
        # Simple function calls
        matches = self.FUNCTION_PATTERNS["call"].findall(line)
        for func_name in matches:
            if func_name.lower() not in [
                "if",
                "then",
                "else",
                "end",
                "for",
                "while",
            ]:
                if context in self.functions:
                    self.functions[context].called_functions.add(func_name)

        # Dynamic calls
        dynamic_matches = self.FUNCTION_PATTERNS["dynamic_call"].findall(line)
        for func_name in dynamic_matches:
            if context in self.functions:
                self.functions[context].called_functions.add(f"DYNAMIC:{func_name}")

    def _extract_dw_operations(self, line: str, context: str, line_number: int) -> None:
        """Extract DataWindow operations from a line of code."""
        for op_name, pattern in self.DW_PATTERNS.items():
            match = pattern.search(line)
            if match:
                dw_name = match.group(1)

                # Add UI element reference
                if context in self.functions:
                    self.functions[context].add_ui_element(dw_name)

                # For SetSQLSelect, extract the SQL
                if op_name == "setsqlselect" and len(match.groups()) > 1:
                    sql = match.group(2)
                    self._extract_sql_operations(sql, context, line_number)

    def generate_business_logic_report(self) -> dict[str, Any]:
        """Generate a comprehensive business logic report.

        Returns:
            Dictionary containing business logic analysis
        """
        return {
            "functions": {
                name: {
                    "name": func.name,
                    "object": func.object_name,
                    "parameters": func.parameters,
                    "return_type": func.return_type,
                    "accessed_tables": list(func.accessed_tables),
                    "operations": [
                        {
                            "type": op.operation_type,
                            "table": op.table_name,
                            "columns": op.columns,
                            "line": op.line_number,
                        }
                        for op in func.operations
                    ],
                    "called_functions": list(func.called_functions),
                    "ui_elements": list(func.ui_elements),
                    "line_number": func.line_number,
                }
                for name, func in self.functions.items()
            },
            "ui_elements": {
                name: {
                    "name": elem.name,
                    "type": elem.type,
                    "parent": elem.parent_object,
                    "data_source": elem.data_source,
                    "accessed_tables": list(elem.accessed_tables),
                    "bound_columns": elem.bound_columns,
                    "event_handlers": elem.event_handlers,
                    "child_elements": elem.child_elements,
                }
                for name, elem in self.ui_elements.items()
            },
            "table_dependencies": {
                table: list(deps) for table, deps in self.table_dependencies.items()
            },
            "statistics": {
                "total_functions": len(self.functions),
                "total_ui_elements": len(self.ui_elements),
                "total_tables_accessed": len(self.table_dependencies),
                "total_data_flows": len(self.data_flows),
            },
        }

    def export_to_plantuml(self, output_file: Path) -> None:
        """Export business logic as PlantUML diagram.

        Args:
            output_file: Path to output .puml file
        """
        lines = ["@startuml Business Logic Flow", ""]

        # Define components
        lines.append("' Components")
        for table in self.table_dependencies:
            lines.append(f'database "{table}" as {table}')

        for func_name in self.functions:
            lines.append(f'component "{func_name}" as {func_name.replace(".", "_")}')

        for ui_name in self.ui_elements:
            lines.append(f'interface "{ui_name}" as {ui_name}')

        lines.append("")
        lines.append("' Relationships")

        # Function to table relationships
        for func_name, func in self.functions.items():
            safe_func_name = func_name.replace(".", "_")
            for table in func.accessed_tables:
                for op in func.operations:
                    if op.table_name == table:
                        if op.operation_type == "SELECT":
                            lines.append(f"{table} --> {safe_func_name} : READ")
                        elif op.operation_type in ["INSERT", "UPDATE", "DELETE"]:
                            lines.append(f"{safe_func_name} --> {table} : WRITE")

        # Function call relationships
        for func_name, func in self.functions.items():
            safe_func_name = func_name.replace(".", "_")
            for called in func.called_functions:
                safe_called = called.replace(".", "_")
                lines.append(f"{safe_func_name} --> {safe_called} : calls")

        lines.append("")
        lines.append("@enduml")

        output_file.write_text("\n".join(lines))
        logger.info("Exported business logic diagram to %s", output_file)
