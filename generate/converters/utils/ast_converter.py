"""PowerBuilder AST to intermediate representation converter.

This is the main converter that traverses PowerBuilder AST nodes and
converts them to an intermediate representation suitable for code generation.
"""

import logging
from dataclasses import dataclass, field
from typing import Any

from lark import Token, Tree

from ..logic.application_converter import ApplicationConverter, ApplicationDefinition
from ..ui.datawindow_converter import DataWindowConverter, DataWindowDefinition
from ..logic.event_converter import EventConverter
from .expression_converter import ExpressionConverter
from ..ui.menu_converter import MenuConverter, MenuDefinition
from .type_converter import TypeConverter
from ..ui.ui_converter import UIConverter

logger = logging.getLogger(__name__)


@dataclass
class Variable:
    """Represents a variable declaration."""
    name: str
    type: str
    dart_type: str
    initial_value: str | None = None
    is_array: bool = False
    is_constant: bool = False
    is_instance: bool = True
    access_modifier: str = "private"


@dataclass
class Method:
    """Represents a method/function."""
    name: str
    return_type: str
    dart_return_type: str
    parameters: list[Variable] = field(default_factory=list)
    body: list[str] = field(default_factory=list)
    is_event: bool = False
    is_async: bool = False
    access_modifier: str = "public"


@dataclass
class WindowDefinition:
    """Represents a window definition."""
    name: str
    title: str = ""
    variables: list[Variable] = field(default_factory=list)
    controls: list[dict[str, Any]] = field(default_factory=list)
    methods: list[Method] = field(default_factory=list)
    events: list[Method] = field(default_factory=list)
    datawindows: list[str] = field(default_factory=list)
    properties: dict[str, Any] = field(default_factory=dict)


@dataclass
class UserObjectDefinition:
    """Represents a user object definition."""
    name: str
    base_type: str = "userobject"
    variables: list[Variable] = field(default_factory=list)
    controls: list[dict[str, Any]] = field(default_factory=list)
    methods: list[Method] = field(default_factory=list)
    events: list[Method] = field(default_factory=list)
    properties: dict[str, Any] = field(default_factory=dict)


@dataclass
class StructureDefinition:
    """Represents a structure definition."""
    name: str
    fields: list[Variable] = field(default_factory=list)


class ASTConverter:
    """Main converter for PowerBuilder AST to intermediate representation."""

    def __init__(self) -> None:




        """Initialize the AST converter with sub-converters."""
        self.type_converter = TypeConverter()
        self.expression_converter = ExpressionConverter(self.type_converter)
        self.datawindow_converter = DataWindowConverter(
            self.type_converter, self.expression_converter,
        )
        self.event_converter = EventConverter(
            self.type_converter, self.expression_converter,
        )
        self.ui_converter = UIConverter()
        self.menu_converter = MenuConverter()
        self.application_converter = ApplicationConverter(self.type_converter)

        # Track current context
        self.current_object = None
        self.current_method = None
        self.imports = set()

    def convert_ast(self, ast: Tree, object_type: str) -> Any:




        """Convert a PowerBuilder AST to intermediate representation.

        Args:
            ast: Lark AST tree
            object_type: Type of PowerBuilder object (window, userobject, etc.)

        Returns:
            Appropriate definition object
        """
        logger.info("Converting AST for %s", object_type)

        if object_type == "window":
            return self.convert_window(ast)
        elif object_type == "userobject":
            return self.convert_user_object(ast)
        elif object_type == "datawindow":
            return self.convert_datawindow(ast)
        elif object_type == "structure":
            return self.convert_structure(ast)
        elif object_type == "function":
            return self.convert_function(ast)
        elif object_type == "menu":
            return self.convert_menu(ast)
        elif object_type == "application":
            return self.convert_application(ast)
        else:
            logger.warning("Unknown object type: %s", object_type)
            return None

    def convert_window(self, ast: Tree) -> WindowDefinition:




        """Convert window AST to WindowDefinition."""
        window = WindowDefinition(name="UnknownWindow")
        self.current_object = window

        # Extract window properties
        for node in ast.children:
            if isinstance(node, Tree):
                if node.data == "window_header":
                    self._process_window_header(node, window)
                elif node.data == "variable_declaration":
                    var = self._process_variable(node)
                    if var:
                        window.variables.append(var)
                elif node.data == "control_declaration":
                    control = self._process_control(node)
                    if control:
                        window.controls.append(control)
                elif node.data == "event_declaration":
                    event = self._process_event(node)
                    if event:
                        window.events.append(event)
                elif node.data == "function_declaration":
                    method = self._process_function(node)
                    if method:
                        window.methods.append(method)

        # Identify DataWindows from controls
        for control in window.controls:
            if control.get("type") == "datawindow":
                window.datawindows.append(control.get("name"))

        return window

    def _process_window_header(self, node: Tree, window: WindowDefinition) -> None:




        """Process window header information."""
        for child in node.children:
            if isinstance(child, Tree):
                if child.data == "window_name":
                    window.name = self._get_identifier(child)
                elif child.data == "window_properties":
                    self._process_properties(child, window.properties)

    def _process_properties(self, node: Tree, properties: dict[str, Any]) -> None:




        """Process property assignments."""
        for child in node.children:
            if isinstance(child, Tree) and child.data == "property_assignment":
                name = None
                value = None

                for prop_child in child.children:
                    if isinstance(prop_child, Tree):
                        if prop_child.data == "property_name":
                            name = self._get_identifier(prop_child)
                        elif prop_child.data == "property_value":
                            value = self._get_value(prop_child)

                if name and value is not None:
                    properties[name] = value

    def _process_variable(self, node: Tree) -> Variable | None:




        """Process variable declaration."""
        var_type = None
        var_name = None
        initial_value = None
        is_array = False
        is_constant = False
        access_modifier = "private"

        for child in node.children:
            if isinstance(child, Tree):
                if child.data == "type":
                    var_type = self._get_type(child)
                    is_array = "[]" in var_type
                elif child.data == "identifier":
                    var_name = child.children[0].value
                elif child.data == "initial_value":
                    initial_value = self._get_expression(child)
                elif child.data == "access_modifier":
                    access_modifier = child.children[0].value.lower()
            elif isinstance(child, Token):
                if child.type == "CONSTANT":
                    is_constant = True

        if var_type and var_name:
            dart_type = self.type_converter.convert_type(var_type)
            return Variable(
                name=var_name, type=var_type, dart_type=dart_type, initial_value=initial_value, is_array=is_array, is_constant=is_constant, access_modifier=access_modifier,
            )

        return None

    def _process_control(self, node: Tree) -> dict[str, Any | None]:




        """Process control declaration."""
        control_type = None
        control_name = None
        properties = {}

        for child in node.children:
            if isinstance(child, Tree):
                if child.data == "control_type":
                    control_type = child.children[0].value.lower()
                elif child.data == "control_name":
                    control_name = self._get_identifier(child)
                elif child.data == "control_properties":
                    self._process_properties(child, properties)

        if control_type and control_name:
            # Convert to Flutter widget info
            flutter_info = self.ui_converter.convert_control(
                control_type, control_name, properties,
            )
            return flutter_info

        return None

    def _process_event(self, node: Tree) -> Method | None:




        """Process event declaration."""
        event_name = None
        control_name = None
        parameters = []
        body = []

        for child in node.children:
            if isinstance(child, Tree):
                if child.data == "event_name":
                    full_event_name = self._get_identifier(child)
                    # Check if event name contains control name (e.g., "cb_ok::clicked")
                    if "::" in full_event_name:
                        parts = full_event_name.split("::")
                        control_name = parts[0]
                        event_name = parts[1]
                    else:
                        event_name = full_event_name
                elif child.data == "parameter_list":
                    parameters = self._process_parameters(child)
                elif child.data == "statement_list":
                    body = self._process_statements(child)

        if event_name:
            # Convert event to Flutter callback
            flutter_event = self.event_converter.convert_event(
                event_name, parameters, body, control_name,
            )
            return flutter_event

        return None

    def _process_function(self, node: Tree) -> Method | None:




        """Process function declaration."""
        func_name = None
        return_type = "void"
        parameters = []
        body = []
        access_modifier = "public"

        for child in node.children:
            if isinstance(child, Tree):
                if child.data == "function_name":
                    func_name = self._get_identifier(child)
                elif child.data == "return_type":
                    return_type = self._get_type(child)
                elif child.data == "parameter_list":
                    parameters = self._process_parameters(child)
                elif child.data == "statement_list":
                    body = self._process_statements(child)
                elif child.data == "access_modifier":
                    access_modifier = child.children[0].value.lower()

        if func_name:
            dart_return_type = self.type_converter.convert_type(return_type)

            # Check if function should be async
            is_async = self._should_be_async(body)

            return Method(
                name=func_name, return_type=return_type, dart_return_type=dart_return_type, parameters=parameters, body=body, is_async=is_async, access_modifier=access_modifier,
            )

        return None

    def _process_parameters(self, node: Tree) -> list[Variable]:




        """Process parameter list."""
        parameters = []

        for child in node.children:
            if isinstance(child, Tree) and child.data == "parameter":
                param = self._process_variable(child)
                if param:
                    parameters.append(param)

        return parameters

    def _process_statements(self, node: Tree) -> list[str]:




        """Process statement list and convert to Dart."""
        statements = []

        for child in node.children:
            if isinstance(child, Tree):
                stmt = self._convert_statement(child)
                if stmt:
                    statements.append(stmt)

        return statements

    def _convert_statement(self, node: Tree) -> str | None:




        """Convert a single statement to Dart."""
        if node.data == "assignment":
            return self._convert_assignment(node)
        elif node.data == "if_statement":
            return self._convert_if_statement(node)
        elif node.data == "for_statement":
            return self._convert_for_statement(node)
        elif node.data == "while_statement":
            return self._convert_while_statement(node)
        elif node.data == "function_call":
            return self._convert_function_call(node)
        elif node.data == "return_statement":
            return self._convert_return_statement(node)
        else:
            logger.debug("Unknown statement type: %s", node.data)
            return None

    def _convert_assignment(self, node: Tree) -> str:




        """Convert assignment statement."""
        target = None
        value = None

        for child in node.children:
            if isinstance(child, Tree):
                if child.data == "assignment_target":
                    target = self._get_identifier(child)
                elif child.data == "expression":
                    value = self._get_expression(child)

        if target and value:
            dart_value = self.expression_converter.convert_expression(value)
            return f"{target} = {dart_value}"

        return ""

    def _should_be_async(self, body: list[str]) -> bool:




        """Check if method should be async based on body content."""
        async_indicators = [
            "await", "Future", "Stream", 
            "database", "repository", "fetch", "load", "save",
        ]

        body_text = " ".join(body).lower()
        return any(indicator in body_text for indicator in async_indicators)

    # Helper methods
    def _get_identifier(self, node: Tree) -> str:


        """Extract identifier from node."""
        if isinstance(node, Token):
            return node.value
        elif isinstance(node, Tree):
            for child in node.children:
                if isinstance(child, Token):
                    return child.value
        return ""

    def _get_type(self, node: Tree) -> str:




        """Extract type from node."""
        if isinstance(node, Token):
            return node.value
        elif isinstance(node, Tree):
            type_parts = []
            for child in node.children:
                if isinstance(child, Token):
                    type_parts.append(child.value)
            return " ".join(type_parts)
        return "any"

    def _get_value(self, node: Any) -> Any:




        """Extract value from node."""
        if isinstance(node, Token):
            return node.value
        elif isinstance(node, Tree):
            if node.data == "string_literal":
                return node.children[0].value.strip('"\'')
            elif node.data == "number_literal":
                return float(node.children[0].value)
            elif node.data == "boolean_literal":
                return node.children[0].value.lower() == "true"
            else:
                return self._get_expression(node)
        return None

    def _get_expression(self, node: Tree) -> str:




        """Extract expression as string."""
        # This is simplified - a full implementation would build expression tree
        parts = []

        def collect_tokens(n) -> None:


            if isinstance(n, Token):
                parts.append(n.value)
            elif isinstance(n, Tree):
                for child in n.children:
                    collect_tokens(child)

        collect_tokens(node)
        return " ".join(parts)

    # Stub methods for other statement types
    def _convert_if_statement(self, node: Tree) -> str:


        """Convert IF statement."""
        # Implementation would parse condition and branches
        return "// IF statement conversion needed"

    def _convert_for_statement(self, node: Tree) -> str:




        """Convert FOR statement."""
        return "// FOR statement conversion needed"

    def _convert_while_statement(self, node: Tree) -> str:




        """Convert WHILE statement."""
        return "// WHILE statement conversion needed"

    def _convert_function_call(self, node: Tree) -> str:




        """Convert function call."""
        return "// Function call conversion needed"

    def _convert_return_statement(self, node: Tree) -> str:




        """Convert RETURN statement."""
        return "// RETURN statement conversion needed"

    # Other object type conversions
    def convert_user_object(self, ast: Tree) -> UserObjectDefinition:


        """Convert user object AST."""
        # Similar to window conversion
        return UserObjectDefinition(name="UnknownUserObject")

    def convert_datawindow(self, ast: Tree) -> DataWindowDefinition:




        """Convert DataWindow AST."""
        # Extract DataWindow syntax and use DataWindowConverter
        dw_syntax = self._extract_datawindow_syntax(ast)
        dw_name = self._extract_datawindow_name(ast)

        return self.datawindow_converter.convert_datawindow(dw_syntax, dw_name)

    def convert_structure(self, ast: Tree) -> StructureDefinition:




        """Convert structure AST."""
        structure = StructureDefinition(name="UnknownStructure")

        # Extract structure fields
        for node in ast.children:
            if isinstance(node, Tree):
                if node.data == "structure_name":
                    structure.name = self._get_identifier(node)
                elif node.data == "field_declaration":
                    field = self._process_variable(node)
                    if field:
                        structure.fields.append(field)

        return structure

    def convert_function(self, ast: Tree) -> Method:




        """Convert standalone function AST."""
        return self._process_function(ast) or Method(
            name="UnknownFunction",
            return_type="void",
            dart_return_type="void",
        )

    def _extract_datawindow_syntax(self, ast: Tree) -> str:




        """Extract DataWindow syntax from AST."""
        # This would extract the full DataWindow definition
        return ""

    def _extract_datawindow_name(self, ast: Tree) -> str:




        """Extract DataWindow name from AST."""
        # This would extract the DataWindow object name
        return "unknown_datawindow"

    def convert_menu(self, ast: Tree) -> MenuDefinition:




        """Convert menu AST to MenuDefinition."""
        # For AST conversion, we would parse the tree structure
        # For now, convert from raw syntax if available
        menu_name = self._extract_menu_name(ast)
        menu_syntax = self._extract_menu_syntax(ast)

        if menu_syntax:
            return self.menu_converter.convert_menu(menu_syntax, menu_name)

        # Otherwise, build from AST structure
        menu_def = MenuDefinition(name=menu_name)

        # Process menu items from AST
        for node in ast.children:
            if isinstance(node, Tree):
                if node.data == "menu_item":
                    # Process menu item
                    menu_item = self._convert_menu_item(node)
                    if menu_item:
                        menu_def.menu_bar.append(menu_item)

        return menu_def

    def convert_application(self, ast: Tree) -> ApplicationDefinition:




        """Convert application AST to ApplicationDefinition."""
        # For AST conversion, we would parse the tree structure
        # For now, convert from raw syntax if available
        app_name = self._extract_application_name(ast)
        app_syntax = self._extract_application_syntax(ast)

        if app_syntax:
            return self.application_converter.convert_application(app_syntax, app_name)

        # Otherwise, build from AST structure
        app_def = ApplicationDefinition(name=app_name)

        # Process application properties from AST
        for node in ast.children:
            if isinstance(node, Tree):
                if node.data == "application_properties":
                    # Process properties
                    self._extract_application_properties(node, app_def)
                elif node.data == "variable_declaration":
                    # Process global variables
                    app_var = self._convert_application_variable(node)
                    if app_var:
                        app_def.variables.append(app_var)
                elif node.data == "event_declaration":
                    # Process application events
                    app_event = self._convert_application_event(node)
                    if app_event:
                        app_def.events.append(app_event)

        return app_def

    def _extract_menu_name(self, ast: Tree) -> str:




        """Extract menu name from AST."""
        # Look for menu name in AST
        for node in ast.children:
            if isinstance(node, Tree) and node.data == "menu_name":
                return self._get_identifier(node)
        return "unknown_menu"

    def _extract_menu_syntax(self, ast: Tree) -> str:




        """Extract raw menu syntax from AST."""
        # This would extract the full menu definition if available
        return ""

    def _extract_application_name(self, ast: Tree) -> str:




        """Extract application name from AST."""
        # Look for application name in AST
        for node in ast.children:
            if isinstance(node, Tree) and node.data == "application_name":
                return self._get_identifier(node)
        return "unknown_application"

    def _extract_application_syntax(self, ast: Tree) -> str:




        """Extract raw application syntax from AST."""
        # This would extract the full application definition if available
        return ""

    def _convert_menu_item(self, node: Tree) -> "MenuItem | None":




        """Convert a menu_item AST node to MenuItem object."""
        from .menu_converter import MenuItem
        
        try:
            # Extract menu item properties
            name = "menu_item"
            text = "Menu Item"
            enabled = True
            visible = True
            shortcut = None
            on_click = None
            
            for child in node.children:
                if isinstance(child, Tree):
                    if child.data == "menu_item_name":
                        name = self._get_identifier(child)
                    elif child.data == "menu_item_text":
                        text = self._get_string_literal(child)
                    elif child.data == "menu_shortcut":
                        shortcut = self._get_string_literal(child)
                    elif child.data == "menu_action":
                        on_click = self._get_identifier(child)
                    elif child.data == "menu_property":
                        # Handle enabled/visible properties
                        prop_name = self._get_identifier(child)
                        if prop_name == "enabled":
                            enabled = self._get_boolean_value(child)
                        elif prop_name == "visible":
                            visible = self._get_boolean_value(child)
            
            return MenuItem(
                name=name,
                text=text,
                enabled=enabled,
                visible=visible,
                shortcut=shortcut,
                on_click=on_click
            )
        except Exception as e:
            logger.warning("Failed to convert menu item: %s", e)
            return None

    def _extract_application_properties(self, node: Tree, app_def: "ApplicationDefinition") -> None:




        """Extract application properties from AST node."""
        try:
            for child in node.children:
                if isinstance(child, Tree):
                    if child.data == "property_assignment":
                        prop_name, prop_value = self._extract_property_assignment(child)
                        self._apply_application_property(app_def, prop_name, prop_value)
        except Exception as e:
            logger.warning("Failed to extract application properties: %s", e)

    def _convert_application_variable(self, node: Tree) -> "ApplicationVariable | None":




        """Convert variable declaration AST node to ApplicationVariable."""
        from .application_converter import ApplicationVariable
        
        try:
            # Extract variable details
            var_name = "unknown_var"
            pb_type = "string"
            initial_value = None
            
            for child in node.children:
                if isinstance(child, Tree):
                    if child.data == "variable_name":
                        var_name = self._get_identifier(child)
                    elif child.data == "variable_type":
                        pb_type = self._get_identifier(child)
                    elif child.data == "initial_value":
                        initial_value = self._get_string_literal(child)
            
            # Convert types
            dart_type = self.type_converter.pb_to_dart_type(pb_type)
            python_type = self.type_converter.pb_to_python_type(pb_type)
            
            return ApplicationVariable(
                name=var_name,
                pb_type=pb_type,
                dart_type=dart_type,
                python_type=python_type,
                initial_value=initial_value,
                is_global=True
            )
        except Exception as e:
            logger.warning("Failed to convert application variable: %s", e)
            return None

    def _convert_application_event(self, node: Tree) -> "ApplicationEvent | None":




        """Convert event declaration AST node to ApplicationEvent."""
        from .application_converter import ApplicationEvent
        
        try:
            # Extract event details
            event_name = "unknown_event"
            parameters = []
            body = []
            
            for child in node.children:
                if isinstance(child, Tree):
                    if child.data == "event_name":
                        event_name = self._get_identifier(child)
                    elif child.data == "parameter_list":
                        parameters = self._extract_parameters(child)
                    elif child.data == "event_body":
                        body = self._extract_statements(child)
            
            return ApplicationEvent(
                name=event_name,
                parameters=parameters,
                body=body
            )
        except Exception as e:
            logger.warning("Failed to convert application event: %s", e)
            return None

    def _extract_property_assignment(self, node: Tree) -> tuple[str, Any]:




        """Extract property name and value from assignment node."""
        prop_name = "unknown"
        prop_value = None
        
        for child in node.children:
            if isinstance(child, Tree):
                if child.data == "property_name":
                    prop_name = self._get_identifier(child)
                elif child.data == "property_value":
                    prop_value = self._get_literal_value(child)
        
        return prop_name, prop_value

    def _apply_application_property(self, app_def: "ApplicationDefinition", prop_name: str, prop_value: Any) -> None:




        """Apply a property value to the application definition."""
        try:
            if prop_name == "appname":
                app_def.app_name = str(prop_value) if prop_value else ""
            elif prop_name == "displayname":
                app_def.display_name = str(prop_value) if prop_value else ""
            elif prop_name == "microhelp":
                app_def.micro_help = bool(prop_value)
            elif prop_name == "dynamicmicrohelp":
                app_def.dynamic_micro_help = bool(prop_value)
            elif prop_name == "toolbartext":
                app_def.toolbar_text = bool(prop_value)
            elif prop_name == "toolbartips":
                app_def.toolbar_tips = bool(prop_value)
            elif prop_name == "theme":
                app_def.theme = str(prop_value) if prop_value else "default"
            elif prop_name == "icon":
                app_def.icon = str(prop_value) if prop_value else None
            elif prop_name == "splashscreen":
                app_def.splash_screen = str(prop_value) if prop_value else None
            elif prop_name == "initialwindow":
                app_def.initial_window = str(prop_value) if prop_value else None
        except Exception as e:
            logger.debug("Failed to apply application property %s: %s", prop_name, e)

    def _extract_parameters(self, node: Tree) -> list[tuple[str, str]]:




        """Extract parameter list from AST node."""
        parameters = []
        try:
            for child in node.children:
                if isinstance(child, Tree) and child.data == "parameter":
                    param_name = "param"
                    param_type = "string"
                    
                    for param_child in child.children:
                        if isinstance(param_child, Tree):
                            if param_child.data == "parameter_name":
                                param_name = self._get_identifier(param_child)
                            elif param_child.data == "parameter_type":
                                param_type = self._get_identifier(param_child)
                    
                    parameters.append((param_name, param_type))
        except Exception as e:
            logger.debug("Failed to extract parameters: %s", e)
        
        return parameters

    def _extract_statements(self, node: Tree) -> list[str]:




        """Extract statement strings from AST node."""
        statements = []
        try:
            for child in node.children:
                if isinstance(child, Tree):
                    # Convert AST statement to string representation
                    stmt_str = self._ast_to_string(child)
                    if stmt_str:
                        statements.append(stmt_str)
                elif isinstance(child, Token):
                    statements.append(str(child.value))
        except Exception as e:
            logger.debug("Failed to extract statements: %s", e)
        
        return statements

    def _get_boolean_value(self, node: Tree) -> bool:




        """Extract boolean value from AST node."""
        try:
            for child in node.children:
                if isinstance(child, Token):
                    value = child.value.lower()
                    return value in ("true", "1", "yes", "on")
        except Exception:
            pass
        return True

    def _get_literal_value(self, node: Tree) -> Any:




        """Extract literal value from AST node."""
        try:
            for child in node.children:
                if isinstance(child, Token):
                    value = child.value
                    # Try to convert to appropriate type
                    if value.lower() in ("true", "false"):
                        return value.lower() == "true"
                    elif value.isdigit():
                        return int(value)
                    elif value.replace(".", "").isdigit():
                        return float(value)
                    else:
                        # Remove quotes if present
                        if value.startswith('"') and value.endswith('"'):
                            return value[1:-1]
                        return value
        except Exception:
            pass
        return None

    def _ast_to_string(self, node: Tree) -> str:




        """Convert AST node to string representation."""
        try:
            # Simple conversion - just join all tokens
            tokens = []
            for child in node.children:
                if isinstance(child, Token):
                    tokens.append(str(child.value))
                elif isinstance(child, Tree):
                    tokens.append(self._ast_to_string(child))
            return " ".join(tokens)
        except Exception:
            return ""
