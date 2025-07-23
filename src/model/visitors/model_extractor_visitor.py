"""Model extractor visitor for converting AST to model data.

This module provides specialized visitors for extracting model information
from PowerBuilder AST structures without using regex.
"""

from typing import Any, Dict, List
import logging

from .ast_tree_visitor import ASTTreeVisitor
from .ast_walker import ASTWalker

logger = logging.getLogger(__name__)


class ModelExtractorVisitor(ASTTreeVisitor[Dict[str, Any]]):
    """Main visitor for extracting model data from AST."""
    
    def __init__(self) -> None:
        """Initialize the model extractor."""
        super().__init__()
        self.current_model: Dict[str, Any] = {}
    
    def extract_model(self, ast: Dict[str, Any], object_type: str, object_name: str) -> Dict[str, Any]:
        """Extract model data from AST based on object type.
        
        Args:
            ast: AST dictionary
            object_type: Type of PowerBuilder object
            object_name: Name of the object
            
        Returns:
            Extracted model data
        """
        # Initialize model
        self.current_model = {
        'type': object_type,
            'name': object_name,
            'events': [],
            'methods': [],
            'variables': [],
            'properties': {}
        }
        
        # Visit the AST
        self.visit(ast)
        
        # Return the extracted model
        return self.current_model
    
    # Specific visitor methods for different node types
    
    def visit_type_declaration(self, node: Dict[str, Any]) -> None:
        """Visit a type declaration node."""
        # Extract type information
        identifiers = ASTWalker.extract_identifiers(node)
        if identifiers:
            self.current_model['name'] = identifiers[0]
            if len(identifiers) > 1:
                self.current_model['parent_type'] = identifiers[1]
        
        # Continue visiting children
        self.generic_visit(node)
    
    def visit_global_type(self, node: Dict[str, Any]) -> None:
        """Visit a global type declaration node."""
        # Same as type_declaration
        self.visit_type_declaration(node)
    
    def visit_event_handler(self, node: Dict[str, Any]) -> None:
        """Visit an event handler node."""
        event_data = {
        'type': 'event',
            'name': '',
            'parameters': [],
            'return_type': 'any'
        }
        
        # Extract event name
        identifier_node = self.find_child_by_type(node, 'IDENTIFIER')
        if identifier_node:
            event_data['name'] = self.get_node_value(identifier_node)
        
        # Extract parameters
        params_node = self.find_child_by_type(node, 'parameter_list')
        if params_node:
            event_data['parameters'] = self._extract_parameters(params_node)
        
        # Extract return type if present
        return_node = self.find_child_by_type(node, 'return_type')
        if return_node:
            event_data['return_type'] = self._extract_type(return_node)
        
        # Add to model
        if event_data['name']:
            self.current_model['events'].append(event_data)
        
        # Visit body
        self.generic_visit(node)
    
    def visit_function_decl(self, node: Dict[str, Any]) -> None:
        """Visit a function declaration node."""
        method_data = {
        'type': 'function',
            'name': '',
            'return_type': 'void',
            'parameters': [],
            'visibility': 'public'
        }
        
        # Extract visibility
        visibility_node = self.find_child_by_type(node, 'visibility_modifier')
        if visibility_node:
            method_data['visibility'] = self.get_node_value(visibility_node)
        
        # Extract return type and name
        children = node.get('children', [])
        for i, child in enumerate(children):
            if isinstance(child, dict):
                child_type = self._get_node_type(child)
                if child_type == 'TYPE_NAME':
                    method_data['return_type'] = self.get_node_value(child)
                elif child_type == 'IDENTIFIER' and not method_data['name']:
                    method_data['name'] = self.get_node_value(child)
        
        # Extract parameters
        params_node = self.find_child_by_type(node, 'parameter_list')
        if params_node:
            method_data['parameters'] = self._extract_parameters(params_node)
        
        # Add to model
        if method_data['name']:
            self.current_model['methods'].append(method_data)
        
        # Visit body
        self.generic_visit(node)
    
    def visit_on_block(self, node: Dict[str, Any]) -> None:
        """Visit an on block (create/destroy handlers)."""
        # Extract the event type
        children = node.get('children', [])
        for child in children:
            if isinstance(child, dict):
                value = self.get_node_value(child)
                if value in ['CREATE', 'DESTROY']:
                    event_data = {
                    'name': value.lower(),
                        'type': 'system_event'
                    }
                    self.current_model['events'].append(event_data)
                    break
        
        # Visit body
        self.generic_visit(node)
    
    def visit_variable_decl(self, node: Dict[str, Any]) -> None:
        """Visit a variable declaration node."""
        var_data = {
        'name': '',
            'type': '',
            'visibility': 'private',
            'initial_value': None
        }
        
        # Extract visibility
        visibility_node = self.find_child_by_type(node, 'visibility_modifier')
        if visibility_node:
            var_data['visibility'] = self.get_node_value(visibility_node)
        
        # Extract type and name
        type_node = self.find_child_by_type(node, 'TYPE_NAME')
        if type_node:
            var_data['type'] = self.get_node_value(type_node)
        
        identifier_node = self.find_child_by_type(node, 'IDENTIFIER')
        if identifier_node:
            var_data['name'] = self.get_node_value(identifier_node)
        
        # Extract initial value
        assign_node = self.find_child_by_type(node, 'assignment')
        if assign_node:
            var_data['initial_value'] = self._extract_expression(assign_node)
        
        # Add to model
        if var_data['name'] and var_data['type']:
            self.current_model['variables'].append(var_data)
        
        # Continue visiting
        self.generic_visit(node)
    
    def visit_control_decl(self, node: Dict[str, Any]) -> None:
        """Visit a control declaration node."""
        control_data = {
        'name': '',
            'type': '',
            'properties': {}
        }
        
        # Extract control type and name
        children = node.get('children', [])
        for child in children:
            if isinstance(child, dict):
                child_type = self._get_node_type(child)
                if child_type == 'TYPE_NAME':
                    control_data['type'] = self.get_node_value(child)
                elif child_type == 'IDENTIFIER' and not control_data['name']:
                    control_data['name'] = self.get_node_value(child)
        
        # Extract properties
        within_node = self.find_child_by_type(node, 'within_clause')
        if within_node:
            control_data['properties'] = self._extract_properties(within_node)
        
        # Add to controls list
        if control_data['name']:
            if 'controls' not in self.current_model:
                self.current_model['controls'] = []
            self.current_model['controls'].append(control_data)
        
        # Continue visiting
        self.generic_visit(node)
    
    def visit_structure_decl(self, node: Dict[str, Any]) -> None:
        """Visit a structure declaration node."""
        struct_data = {
        'name': '',
            'fields': []
        }
        
        # Extract structure name
        identifier_node = self.find_child_by_type(node, 'IDENTIFIER')
        if identifier_node:
            struct_data['name'] = self.get_node_value(identifier_node)
        
        # Extract fields
        fields_node = self.find_child_by_type(node, 'structure_body')
        if fields_node:
            field_nodes = self.get_children_by_type(fields_node, 'field_decl')
            for field in field_nodes:
                field_data = {
                'name': '',
                    'type': ''
                }
                
                type_node = self.find_child_by_type(field, 'TYPE_NAME')
                if type_node:
                    field_data['type'] = self.get_node_value(type_node)
                
                id_node = self.find_child_by_type(field, 'IDENTIFIER')
                if id_node:
                    field_data['name'] = self.get_node_value(id_node)
                
                if field_data['name'] and field_data['type']:
                    struct_data['fields'].append(field_data)
        
        # Add to structures list
        if struct_data['name']:
            if 'structures' not in self.current_model:
                self.current_model['structures'] = []
            self.current_model['structures'].append(struct_data)
        
        # Continue visiting
        self.generic_visit(node)
    
    def visit_menu_item(self, node: Dict[str, Any]) -> None:
        """Visit a menu item node."""
        item_data = {
        'name': '',
            'text': '',
            'type': 'menu_item',
            'children': []
        }
        
        # Extract menu item details
        identifier_node = self.find_child_by_type(node, 'IDENTIFIER')
        if identifier_node:
            item_data['name'] = self.get_node_value(identifier_node)
        
        # Extract text property
        text_node = self.find_child_by_type(node, 'text_property')
        if text_node:
            item_data['text'] = self._extract_expression(text_node)
        
        # Add to menu items
        if item_data['name']:
            if 'menu_items' not in self.current_model:
                self.current_model['menu_items'] = []
            self.current_model['menu_items'].append(item_data)
        
        # Continue visiting for nested items
        self.generic_visit(node)
    
    def visit_datawindow_syntax(self, node: Dict[str, Any]) -> None:
        """Visit a datawindow syntax node."""
        # Extract DataWindow properties
        syntax_data = {
        'release': '',
            'dataobject': '',
            'table': '',
            'columns': []
        }
        
        # Parse DataWindow syntax (simplified)
        children = node.get('children', [])
        for child in children:
            if isinstance(child, dict):
                child_type = self._get_node_type(child)
                if child_type == 'release':
                    syntax_data['release'] = self.get_node_value(child)
                elif child_type == 'dataobject':
                    syntax_data['dataobject'] = self.get_node_value(child)
                elif child_type == 'table':
                    syntax_data['table'] = self._extract_table_info(child)
                elif child_type == 'column':
                    syntax_data['columns'].append(self._extract_column_info(child))
        
        # Update model with DataWindow info
        self.current_model.update(syntax_data)
        
        # Continue visiting
        self.generic_visit(node)
    
    # Helper methods
    
    def _extract_parameters(self, params_node: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Extract parameters from a parameter list node."""
        parameters = []
        
        # Find all parameter nodes
        param_nodes = self.get_children_by_type(params_node, 'parameter')
        
        for param in param_nodes:
            param_data = {
            'name': '',
                'type': '',
                'pass_by': 'value'
            }
            
            # Extract pass by reference/value
            ref_node = self.find_child_by_type(param, 'REF')
            if ref_node:
                param_data['pass_by'] = 'reference'
            
            # Extract type and name
            type_node = self.find_child_by_type(param, 'TYPE_NAME')
            if type_node:
                param_data['type'] = self.get_node_value(type_node)
            
            identifier_node = self.find_child_by_type(param, 'IDENTIFIER')
            if identifier_node:
                param_data['name'] = self.get_node_value(identifier_node)
            
            if param_data['name'] and param_data['type']:
                parameters.append(param_data)
        
        return parameters
    
    def _extract_type(self, type_node: Dict[str, Any]) -> str:
        """Extract type information from a type node."""
        # Direct type name
        type_name = self.get_node_value(type_node)
        if type_name:
            return type_name
        
        # Look for TYPE_NAME child
        type_name_node = self.find_child_by_type(type_node, 'TYPE_NAME')
        if type_name_node:
            return self.get_node_value(type_name_node)
        
        # Look for any identifier
        identifiers = ASTWalker.extract_identifiers(type_node)
        if identifiers:
            return identifiers[0]
        
        return 'any'
    
    def _extract_expression(self, expr_node: Dict[str, Any]) -> Any:
        """Extract expression value from an expression node."""
        # Simple literal
        value = self.get_node_value(expr_node)
        if value is not None:
            return value
        
        # Look for literal nodes
        literal_types = ['STRING', 'NUMBER', 'BOOLEAN', 'NULL']
        for lit_type in literal_types:
            lit_node = self.find_child_by_type(expr_node, lit_type)
            if lit_node:
                return self.get_node_value(lit_node)
        
        # Complex expression - return string representation
        return self._node_to_string(expr_node)
    
    def _extract_properties(self, within_node: Dict[str, Any]) -> Dict[str, Any]:
        """Extract properties from a within clause."""
        properties = {}
        
        # Find all property assignments
        assign_nodes = ASTWalker.find_by_type(within_node, 'assignment')
        
        for assign in assign_nodes:
            # Get property name
            prop_name = ''
            value = None
            
            children = assign.get('children', [])
            if len(children) >= 2:
                # First child is property name
                if isinstance(children[0], dict):
                    prop_name = self.get_node_value(children[0])
                
                # Second child is value
                if isinstance(children[1], dict):
                    value = self._extract_expression(children[1])
            
            if prop_name:
                properties[prop_name] = value
        
        return properties
    
    def _node_to_string(self, node: Dict[str, Any]) -> str:
        """Convert a node to string representation."""
        if not isinstance(node, dict):
            return str(node)
        
        # Get node value
        value = self.get_node_value(node)
        if value is not None:
            return str(value)
        
        # For complex nodes, return type
        node_type = self._get_node_type(node)
        return f"<{node_type}>"
    
    def _extract_table_info(self, table_node: Dict[str, Any]) -> str:
        """Extract table information from a table node."""
        # Look for table name
        table_name = self.get_node_value(table_node)
        if table_name:
            return table_name
        
        # Look for identifier child
        id_node = self.find_child_by_type(table_node, 'IDENTIFIER')
        if id_node:
            return self.get_node_value(id_node)
        
        return ''
    
    def _extract_column_info(self, column_node: Dict[str, Any]) -> Dict[str, Any]:
        """Extract column information from a column node."""
        column_data = {
        'name': '',
            'type': '',
            'dbname': ''
        }
        
        # Extract column properties
        children = column_node.get('children', [])
        for child in children:
            if isinstance(child, dict):
                child_type = self._get_node_type(child)
                value = self.get_node_value(child)
                
                if child_type == 'name' and value:
                    column_data['name'] = value
                elif child_type == 'type' and value:
                    column_data['type'] = value
                elif child_type == 'dbname' and value:
                    column_data['dbname'] = value
        
        return column_data


class WindowModelExtractor(ModelExtractorVisitor):
    """Specialized extractor for window models."""
    
    def extract_model(self, ast: Dict[str, Any], object_type: str, object_name: str) -> Dict[str, Any]:
        """Extract window-specific model data."""
        # Initialize window model
        self.current_model = {
        'title': '',
            'controls': [],
            'events': [],
            'methods': [],
            'variables': [],
            'properties': {}
        }
        
        # Visit AST
        self.visit(ast)
        
        return self.current_model


class UserObjectModelExtractor(ModelExtractorVisitor):
    """Specialized extractor for user object models."""
    
    def extract_model(self, ast: Dict[str, Any], object_type: str, object_name: str) -> Dict[str, Any]:
        """Extract user object-specific model data."""
        # Initialize user object model
        self.current_model = {
        'visual': False,
            'controls': [],
            'methods': [],
            'events': [],
            'variables': [],
            'properties': {}
        }
        
        # Check if it's a visual user object
        type_decl = ASTWalker.find_first_by_type(ast, 'type_declaration')
        if type_decl:
            identifiers = ASTWalker.extract_identifiers(type_decl)
            if len(identifiers) > 1:
                parent_type = identifiers[1].lower()
                if 'visual' in parent_type or 'custom' in parent_type:
                    self.current_model['visual'] = True
        
        # Visit AST
        self.visit(ast)
        
        return self.current_model