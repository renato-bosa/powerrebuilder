"""PowerBuilder AST to intermediate representation converter.

This is the main converter that traverses PowerBuilder AST nodes and
converts them to an intermediate representation suitable for code generation.
"""

import logging
from typing import Dict, List, Any, Optional, Union
from dataclasses import dataclass, field
from lark import Tree, Token

from .type_converter import TypeConverter
from .expression_converter import ExpressionConverter
from .datawindow_converter import DataWindowConverter, DataWindowDefinition
from .event_converter import EventConverter
from .ui_converter import UIConverter

logger = logging.getLogger(__name__)


@dataclass
class Variable:
    """Represents a variable declaration."""
    name: str
    type: str
    dart_type: str
    initial_value: Optional[str] = None
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
    parameters: List[Variable] = field(default_factory=list)
    body: List[str] = field(default_factory=list)
    is_event: bool = False
    is_async: bool = False
    access_modifier: str = "public"


@dataclass
class WindowDefinition:
    """Represents a window definition."""
    name: str
    title: str = ""
    variables: List[Variable] = field(default_factory=list)
    controls: List[Dict[str, Any]] = field(default_factory=list)
    methods: List[Method] = field(default_factory=list)
    events: List[Method] = field(default_factory=list)
    datawindows: List[str] = field(default_factory=list)
    properties: Dict[str, Any] = field(default_factory=dict)


@dataclass
class UserObjectDefinition:
    """Represents a user object definition."""
    name: str
    base_type: str = "userobject"
    variables: List[Variable] = field(default_factory=list)
    controls: List[Dict[str, Any]] = field(default_factory=list)
    methods: List[Method] = field(default_factory=list)
    events: List[Method] = field(default_factory=list)
    properties: Dict[str, Any] = field(default_factory=dict)


@dataclass
class StructureDefinition:
    """Represents a structure definition."""
    name: str
    fields: List[Variable] = field(default_factory=list)


class ASTConverter:
    """Main converter for PowerBuilder AST to intermediate representation."""
    
    def __init__(self):
        """Initialize the AST converter with sub-converters."""
        self.type_converter = TypeConverter()
        self.expression_converter = ExpressionConverter(self.type_converter)
        self.datawindow_converter = DataWindowConverter(
            self.type_converter, 
            self.expression_converter
        )
        self.event_converter = EventConverter(
            self.type_converter,
            self.expression_converter
        )
        self.ui_converter = UIConverter()
        
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
        logger.info(f"Converting AST for {object_type}")
        
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
        else:
            logger.warning(f"Unknown object type: {object_type}")
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
    
    def _process_window_header(self, node: Tree, window: WindowDefinition):
        """Process window header information."""
        for child in node.children:
            if isinstance(child, Tree):
                if child.data == "window_name":
                    window.name = self._get_identifier(child)
                elif child.data == "window_properties":
                    self._process_properties(child, window.properties)
    
    def _process_properties(self, node: Tree, properties: Dict[str, Any]):
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
    
    def _process_variable(self, node: Tree) -> Optional[Variable]:
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
                name=var_name,
                type=var_type,
                dart_type=dart_type,
                initial_value=initial_value,
                is_array=is_array,
                is_constant=is_constant,
                access_modifier=access_modifier
            )
        
        return None
    
    def _process_control(self, node: Tree) -> Optional[Dict[str, Any]]:
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
                control_type, 
                control_name, 
                properties
            )
            return flutter_info
        
        return None
    
    def _process_event(self, node: Tree) -> Optional[Method]:
        """Process event declaration."""
        event_name = None
        parameters = []
        body = []
        
        for child in node.children:
            if isinstance(child, Tree):
                if child.data == "event_name":
                    event_name = self._get_identifier(child)
                elif child.data == "parameter_list":
                    parameters = self._process_parameters(child)
                elif child.data == "statement_list":
                    body = self._process_statements(child)
        
        if event_name:
            # Convert event to Flutter callback
            flutter_event = self.event_converter.convert_event(
                event_name,
                parameters,
                body
            )
            return flutter_event
        
        return None
    
    def _process_function(self, node: Tree) -> Optional[Method]:
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
                name=func_name,
                return_type=return_type,
                dart_return_type=dart_return_type,
                parameters=parameters,
                body=body,
                is_async=is_async,
                access_modifier=access_modifier
            )
        
        return None
    
    def _process_parameters(self, node: Tree) -> List[Variable]:
        """Process parameter list."""
        parameters = []
        
        for child in node.children:
            if isinstance(child, Tree) and child.data == "parameter":
                param = self._process_variable(child)
                if param:
                    parameters.append(param)
        
        return parameters
    
    def _process_statements(self, node: Tree) -> List[str]:
        """Process statement list and convert to Dart."""
        statements = []
        
        for child in node.children:
            if isinstance(child, Tree):
                stmt = self._convert_statement(child)
                if stmt:
                    statements.append(stmt)
        
        return statements
    
    def _convert_statement(self, node: Tree) -> Optional[str]:
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
            logger.debug(f"Unknown statement type: {node.data}")
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
            return f"{target} = {dart_value};"
        
        return ""
    
    def _should_be_async(self, body: List[str]) -> bool:
        """Check if method should be async based on body content."""
        async_indicators = [
            "await", "Future", "Stream", 
            "database", "repository", "fetch", "load", "save"
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
        
        def collect_tokens(n):
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
            dart_return_type="void"
        )
    
    def _extract_datawindow_syntax(self, ast: Tree) -> str:
        """Extract DataWindow syntax from AST."""
        # This would extract the full DataWindow definition
        return ""
    
    def _extract_datawindow_name(self, ast: Tree) -> str:
        """Extract DataWindow name from AST."""
        # This would extract the DataWindow object name
        return "unknown_datawindow"