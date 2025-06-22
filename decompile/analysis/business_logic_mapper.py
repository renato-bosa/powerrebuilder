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

from .database_schema_extractor import DatabaseOperation, DatabaseSchemaExtractor

logger = logging.getLogger(__name__)


@dataclass
class BusinessFunction:
    """Represents a business logic function."""
    name: str
    object_name: str
    object_type: str  # Window, UserObject, Function, etc.
    parameters: list[str] = field(default_factory=list)
    return_type: str | None = None
    accessed_tables: set[str] = field(default_factory=set)
    operations: list[DatabaseOperation] = field(default_factory=list)
    called_functions: set[str] = field(default_factory=set)
    ui_elements: set[str] = field(default_factory=set)
    description: str | None = None
    line_number: int | None = None

    def add_table_access(self, table: str, operation: str) -> None:




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
    target_type: str
    operation: str  # READ, WRITE, DISPLAY, etc.
    data_items: list[str] = field(default_factory=list)  # columns/variables


class BusinessLogicMapper:
    """Maps business logic to database operations and UI elements."""

    def __init__(self, schema_extractor: DatabaseSchemaExtractor | None = None) -> None:


        """Initialize the mapper.

        Args:
            schema_extractor: Optional pre-configured schema extractor
        """
        self.schema_extractor = schema_extractor or DatabaseSchemaExtractor()
        self.business_functions: dict[str, BusinessFunction] = {}
        self.ui_elements: dict[str, UIElement] = {}
        self.data_flows: list[DataFlow] = []
        self.function_hierarchy: dict[str, set[str]] = defaultdict(set)  # caller -> callees

    def map_project(self, project_path: Path) -> dict[str, Any]:




        """Map business logic for an entire project.

        Args:
            project_path: Path to the PowerBuilder project

        Returns:
            Dictionary containing comprehensive mapping information
        """
        logger.info(f"Mapping business logic for project: {project_path}")

        # First extract database schema
        schema_info = self.schema_extractor.extract_schema_from_project(project_path)

        # Find all relevant files
        pb_files = []
        for pattern in ["*.srw", "*.sru", "*.srf", "*.fun", "*.srd", "*.dwo"]:
            pb_files.extend(project_path.rglob(pattern))

        # Process each file
        for file_path in pb_files:
            try:
                self._process_file_for_logic(file_path)
            except Exception as e:
                logger.error(f"Error processing file {file_path}: {e}")

        # Analyze data flows
        self._analyze_data_flows()

        # Build comprehensive result
        return self._build_mapping_result(schema_info)

    def _process_file_for_logic(self, file_path: Path) -> None:




        """Process a file to extract business logic mappings."""
        logger.debug(f"Processing file for logic: {file_path}")

        try:
            with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
                content = f.read()
        except Exception as e:
            logger.error(f"Error reading file {file_path}: {e}")
            return

        object_name = file_path.stem
        object_type = self._determine_object_type(file_path.suffix)

        # Extract functions/events
        self._extract_functions(content, object_name, object_type)

        # Extract UI elements
        if object_type in ["Window", "UserObject", "DataWindow"]:
            self._extract_ui_elements(content, object_name, object_type)

        # Map function calls
        self._extract_function_calls(content, object_name)

    def _determine_object_type(self, suffix: str) -> str:




        """Determine object type from file suffix."""
        type_map = {
            ".srw": "Window", ".sru": "UserObject", ".srf": "Function", ".fun": "Function", ".srd": "DataWindow", ".dwo": "DataWindow", ".srm": "Menu", }
        return type_map.get(suffix.lower(), "Unknown")

    def _extract_functions(self, content: str, object_name: str, object_type: str) -> None:




        """Extract function and event definitions."""
        # Pattern for functions
        function_pattern = r"(?:public|protected|private)?\s*(?:function|subroutine)\s+(\w+)\s+(\w+)\s*\(([^)]*)\)"

        # Pattern for events
        event_pattern = r"event\s+(\w+)(?:\s+(\w+))?\s*(?:\(([^)]*)\))?"

        lines = content.split("\n")

        # Extract functions
        for i, line in enumerate(lines):
            match = re.search(function_pattern, line, re.IGNORECASE)
            if match:
                return_type = match.group(1)
                func_name = match.group(2)
                params_str = match.group(3)

                func_key = f"{object_name}.{func_name}"

                func = BusinessFunction(
                    name=func_name, object_name=object_name, object_type=object_type, return_type=return_type if return_type != "subroutine" else None, parameters=self._parse_parameters(params_str), line_number=i + 1,
                )

                # Analyze function body
                func_body = self._extract_function_body(lines, i)
                self._analyze_function_body(func, func_body, object_name)

                self.business_functions[func_key] = func

        # Extract events
        for i, line in enumerate(lines):
            match = re.search(event_pattern, line, re.IGNORECASE)
            if match:
                event_name = match.group(1)
                params_str = match.group(3) if match.group(3) else ""

                func_key = f"{object_name}.{event_name}"

                func = BusinessFunction(
                    name=event_name, object_name=object_name, object_type=object_type, parameters=self._parse_parameters(params_str), line_number=i + 1, description=f"Event handler for {event_name}",
                )

                # Analyze event body
                event_body = self._extract_function_body(lines, i)
                self._analyze_function_body(func, event_body, object_name)

                self.business_functions[func_key] = func

    def _parse_parameters(self, params_str: str) -> list[str]:




        """Parse function parameters."""
        if not params_str or params_str.strip() == "":
            return []

        params = []
        for param in params_str.split(", "):
            param = param.strip()
            if param:
                # Extract parameter name (simplified)
                parts = param.split()
                if len(parts) >= 2:
                    params.append(parts[-1])

        return params

    def _extract_function_body(self, lines: list[str], start_line: int) -> str:




        """Extract function body starting from a line."""
        body_lines = []
        indent_level = 0
        in_function = False

        for i in range(start_line, len(lines)):
            line = lines[i]

            if not in_function and ("function" in line.lower() or "event" in line.lower()):
                in_function = True
                continue

            if in_function:
                if "end function" in line.lower() or "end event" in line.lower():
                    if indent_level == 0:
                        break
                    indent_level -= 1
                elif "function" in line.lower() or "event" in line.lower():
                    indent_level += 1

                body_lines.append(line)

        return "\n".join(body_lines)

    def _analyze_function_body(self, func: BusinessFunction, body: str, object_name: str) -> None:




        """Analyze function body for database operations and UI interactions."""
        # Look for SQL operations
        sql_keywords = ["SELECT", "INSERT", "UPDATE", "DELETE", "FETCH", "OPEN", "CLOSE"]

        for keyword in sql_keywords:
            if keyword in body.upper():
                # Extract the SQL statement
                pattern = rf"{keyword}\s+.*?(?:|\n)"
                matches = re.finditer(pattern, body, re.IGNORECASE | re.DOTALL)

                for match in matches:
                    sql_text = match.group(0)
                    # Use schema extractor to get table info
                    tables = self._extract_tables_from_sql(sql_text)
                    for table in tables:
                        func.add_table_access(table, keyword)

        # Look for DataWindow operations
        dw_operations = [
            r"(\w+)\.Retrieve\s*\(",
            r"(\w+)\.Update\s*\(",
            r"(\w+)\.InsertRow\s*\(",
            r"(\w+)\.DeleteRow\s*\(",
            r"(\w+)\.SetItem\s*\(",
            r"(\w+)\.GetItem\w*\s*\(",
        ]

        for pattern in dw_operations:
            matches = re.finditer(pattern, body, re.IGNORECASE)
            for match in matches:
                dw_name = match.group(1)
                func.add_ui_element(dw_name)

        # Look for window/control operations
        ui_operations = [
            r"(\w+)\.Text\s*=",
            r"(\w+)\.Enabled\s*=",
            r"(\w+)\.Visible\s*=",
            r"Open\s*\(\s*(\w+)",
            r"Close\s*\(\s*(\w+)",
        ]

        for pattern in ui_operations:
            matches = re.finditer(pattern, body, re.IGNORECASE)
            for match in matches:
                ui_element = match.group(1)
                func.add_ui_element(ui_element)

        # Look for function calls
        call_pattern = r"(?:this|parent|super)?\.?(\w+)\s*\("
        matches = re.finditer(call_pattern, body)

        for match in matches:
            called_func = match.group(1)
            # Skip common PowerBuilder functions
            if called_func.lower() not in ["if", "then", "else", "for", "while", "return", "string", "integer"]:
                func.called_functions.add(called_func)
                self.function_hierarchy[func.name].add(called_func)

    def _extract_tables_from_sql(self, sql_text: str) -> list[str]:




        """Extract table names from SQL text."""
        tables = []

        # Simple regex extraction
        from_pattern = r"FROM\s+(\w+)"
        matches = re.finditer(from_pattern, sql_text, re.IGNORECASE)
        for match in matches:
            tables.append(match.group(1))

        # Also check for INTO (for INSERT)
        into_pattern = r"INTO\s+(\w+)"
        matches = re.finditer(into_pattern, sql_text, re.IGNORECASE)
        for match in matches:
            tables.append(match.group(1))

        # UPDATE table
        update_pattern = r"UPDATE\s+(\w+)"
        matches = re.finditer(update_pattern, sql_text, re.IGNORECASE)
        for match in matches:
            tables.append(match.group(1))

        return list(set(tables))

    def _extract_ui_elements(self, content: str, object_name: str, object_type: str) -> None:




        """Extract UI element definitions."""
        if object_type == "Window":
            self._extract_window_controls(content, object_name)
        elif object_type == "DataWindow":
            self._extract_datawindow_info(content, object_name)

    def _extract_window_controls(self, content: str, window_name: str) -> None:




        """Extract controls from a window definition."""
        # Pattern for control definitions
        control_patterns = [
            r"type\s+(\w+)\s+from\s+(\w+)\s+within\s+(\w+)",
            r"create\s+(\w+)",
        ]

        for pattern in control_patterns:
            matches = re.finditer(pattern, content, re.IGNORECASE)

            for match in matches:
                control_name = match.group(1)

                if len(match.groups()) >= 2:
                    control_type = match.group(2)
                else:
                    # Determine type from context
                    control_type = self._determine_control_type(content, control_name)

                ui_key = f"{window_name}.{control_name}"

                ui_element = UIElement(
                    name=control_name,
                    type=control_type,
                    parent_object=window_name,
                )

                # Extract DataWindow-specific info
                if control_type.lower() in ["datawindow", "dw"]:
                    self._extract_datawindow_control_info(content, control_name, ui_element)

                self.ui_elements[ui_key] = ui_element

        # Extract events for controls
        event_pattern = r"event\s+(\w+)::(\w+)\s*\("
        matches = re.finditer(event_pattern, content, re.IGNORECASE)

        for match in matches:
            control_name = match.group(1)
            event_name = match.group(2)

            ui_key = f"{window_name}.{control_name}"
            if ui_key in self.ui_elements:
                self.ui_elements[ui_key].add_event_handler(event_name, f"{window_name}.{control_name}_{event_name}")

    def _determine_control_type(self, content: str, control_name: str) -> str:




        """Determine control type from context."""
        # Look for property assignments that indicate type
        type_indicators = {
            "dataobject": "DataWindow",
            "text": "StaticText",
            "clicked": "CommandButton",
            "itemchanged": "DataWindow",
            "getfocus": "SingleLineEdit",
        }

        for indicator, control_type in type_indicators.items():
            pattern = rf"{control_name}\.{indicator}"
            if re.search(pattern, content, re.IGNORECASE):
                return control_type

        return "Control"  # Generic

    def _extract_datawindow_control_info(self, content: str, control_name: str, ui_element: UIElement) -> None:




        """Extract DataWindow control specific information."""
        # Look for dataobject assignment
        dataobject_pattern = rf'{control_name}\.dataobject\s*=\s*["\'](\w+)["\']'
        match = re.search(dataobject_pattern, content, re.IGNORECASE)

        if match:
            ui_element.data_source = match.group(1)

        # Look for retrieve operations
        retrieve_pattern = rf"{control_name}\.retrieve\s*\("
        if re.search(retrieve_pattern, content, re.IGNORECASE):
            # This DataWindow retrieves data
            # Try to get tables from the associated dataobject
            if ui_element.data_source:
                # Get tables from schema extractor if available
                for table_name, table_info in self.schema_extractor.tables.items():
                    if ui_element.data_source in table_info.used_in_objects:
                        ui_element.accessed_tables.add(table_name)

    def _extract_datawindow_info(self, content: str, dw_name: str) -> None:




        """Extract DataWindow object information."""
        ui_element = UIElement(
            name=dw_name,
            type="DataWindow",
            parent_object=dw_name,
        )

        # Extract SQL/data source
        sql_pattern = r'retrieve\s*=\s*"([^"]+)"'
        match = re.search(sql_pattern, content, re.IGNORECASE | re.DOTALL)

        if match:
            sql_text = match.group(1)
            tables = self._extract_tables_from_sql(sql_text)
            for table in tables:
                ui_element.accessed_tables.add(table)

        # Extract columns
        column_pattern = r"column\s*=\s*\(.*?name\s*=\s*(\w+)\.(\w+)"
        matches = re.finditer(column_pattern, content, re.IGNORECASE | re.DOTALL)

        for match in matches:
            table_name = match.group(1)
            column_name = match.group(2)
            ui_element.accessed_tables.add(table_name)
            ui_element.bound_columns.append(f"{table_name}.{column_name}")

        self.ui_elements[dw_name] = ui_element

    def _extract_function_calls(self, content: str, object_name: str) -> None:




        """Extract function call relationships."""
        # Pattern for function calls
        call_patterns = [
            r"(?:this|parent|super)?\.?(\w+)\s*\(",
            r"(\w+)::(\w+)\s*\(",  # object::function
        ]

        for pattern in call_patterns:
            matches = re.finditer(pattern, content)

            for match in matches:
                if len(match.groups()) == 2:
                    # object::function format
                    called_object = match.group(1)
                    called_function = match.group(2)
                    self.function_hierarchy[object_name].add(f"{called_object}.{called_function}")
                else:
                    # Simple function call
                    called_function = match.group(1)
                    # Skip common PB functions
                    if called_function.lower() not in ["if", "then", "else", "for", "while", "return", "string", "integer", "long", "open", "close"]:
                        self.function_hierarchy[object_name].add(called_function)

    def _analyze_data_flows(self) -> None:




        """Analyze data flows between components."""
        # Create flows from business functions to tables
        for func_key, func in self.business_functions.items():
            for table in func.accessed_tables:
                for op in func.operations:
                    if table in op.tables:
                        flow = DataFlow(
                            source_component=func_key,
                            source_type="Function",
                            target_component=table,
                            target_type="Table",
                            operation=op.operation_type,
                            data_items=op.columns,
                        )
                        self.data_flows.append(flow)

        # Create flows from UI elements to tables
        for ui_key, ui_element in self.ui_elements.items():
            for table in ui_element.accessed_tables:
                flow = DataFlow(
                    source_component=table,
                    source_type="Table",
                    target_component=ui_key,
                    target_type="UI",
                    operation="DISPLAY",
                    data_items=ui_element.bound_columns,
                )
                self.data_flows.append(flow)

        # Create flows between functions
        for caller, callees in self.function_hierarchy.items():
            for callee in callees:
                flow = DataFlow(
                    source_component=caller,
                    source_type="Function",
                    target_component=callee,
                    target_type="Function",
                    operation="CALL",
                    data_items=[],
                )
                self.data_flows.append(flow)

    def _build_mapping_result(self, schema_info: dict[str, Any]) -> dict[str, Any]:




        """Build the comprehensive mapping result."""
        return {
            "database_schema": schema_info,
            "business_functions": {
                key: {
                    "name": func.name,
                    "object": func.object_name,
                    "type": func.object_type,
                    "parameters": func.parameters,
                    "return_type": func.return_type,
                    "accessed_tables": sorted(list(func.accessed_tables)),
                    "operations": [
                        {
                            "type": op.operation_type,
                            "tables": op.tables,
                            "columns": op.columns,
                        }
                        for op in func.operations
                    ],
                    "called_functions": sorted(list(func.called_functions)),
                    "ui_elements": sorted(list(func.ui_elements)),
                    "description": func.description,
                    "line_number": func.line_number,
                }
                for key, func in self.business_functions.items()
            },
            "ui_elements": {
                key: {
                    "name": ui.name,
                    "type": ui.type,
                    "parent": ui.parent_object,
                    "data_source": ui.data_source,
                    "accessed_tables": sorted(list(ui.accessed_tables)),
                    "bound_columns": ui.bound_columns,
                    "event_handlers": ui.event_handlers,
                    "child_elements": ui.child_elements,
                }
                for key, ui in self.ui_elements.items()
            },
            "data_flows": [
                {
                    "source": flow.source_component,
                    "source_type": flow.source_type,
                    "target": flow.target_component,
                    "target_type": flow.target_type,
                    "operation": flow.operation,
                    "data_items": flow.data_items,
                }
                for flow in self.data_flows
            ],
            "function_hierarchy": {
                caller: sorted(list(callees))
                for caller, callees in self.function_hierarchy.items()
            },
            "statistics": {
                "total_functions": len(self.business_functions),
                "total_ui_elements": len(self.ui_elements),
                "total_data_flows": len(self.data_flows),
                "functions_by_type": self._count_functions_by_type(),
                "ui_elements_by_type": self._count_ui_elements_by_type(),
            },
        }

    def _count_functions_by_type(self) -> dict[str, int]:




        """Count functions by object type."""
        counts = defaultdict(int)
        for func in self.business_functions.values():
            counts[func.object_type] += 1
        return dict(counts)

    def _count_ui_elements_by_type(self) -> dict[str, int]:




        """Count UI elements by type."""
        counts = defaultdict(int)
        for ui in self.ui_elements.values():
            counts[ui.type] += 1
        return dict(counts)
