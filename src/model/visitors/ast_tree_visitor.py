"""Base AST tree visitor for traversing PowerBuilder AST structures.

This module provides the base visitor pattern implementation for
traversing AST trees represented as dictionaries.
"""

from typing import Any, Dict, List, Optional, TypeVar, Generic
import logging

logger = logging.getLogger(__name__)

T = TypeVar('T')


class ASTTreeVisitor(Generic[T]):
    """Base visitor class for traversing AST tree structures.
    
    This class provides the visitor pattern for AST nodes represented
    as dictionaries with 'type', 'data', and 'children' fields.
    """
    
    def __init__(self) -> None:
        """Initialize the visitor."""
        self.context_stack: List[Dict[str, Any]] = []
        self.errors: List[str] = []
    
    def visit(self, node: Any) -> Optional[T]:
        """Visit a node and dispatch to appropriate handler.
        
        Args:
            node: AST node to visit
            
        Returns:
            Result of visiting the node
        """
        if node is None:
            return None
            
        # Handle different node types
        if isinstance(node, dict):
            return self._visit_dict_node(node)
        elif isinstance(node, list):
            return self._visit_list(node)
        else:
            # Leaf value (string, number, etc.)
            return self._visit_leaf(node)
    
    def _visit_dict_node(self, node: Dict[str, Any]) -> Optional[T]:
        """Visit a dictionary node.
        
        Args:
            node: Dictionary node
            
        Returns:
            Result of visiting the node
        """
        # Push context
        self.context_stack.append(node)
        
        try:
            # Determine node type
            node_type = self._get_node_type(node)
            
            # Dispatch to specific visitor method
            method_name = f'visit_{node_type}'
            method = getattr(self, method_name, None)
            
            if method:
                result = method(node)
            else:
                # Default handling
                result = self.generic_visit(node)
                
            return result
            
        finally:
            # Pop context
            self.context_stack.pop()
    
    def _visit_list(self, nodes: List[Any]) -> List[Optional[T]]:
        """Visit a list of nodes.
        
        Args:
            nodes: List of nodes
            
        Returns:
            List of results
        """
        return [self.visit(node) for node in nodes]
    
    def _visit_leaf(self, value: Any) -> Any:
        """Visit a leaf value.
        
        Args:
            value: Leaf value
            
        Returns:
            The value itself
        """
        return value
    
    def _get_node_type(self, node: Dict[str, Any]) -> str:
        """Get the type of a node.
        
        Args:
            node: AST node
            
        Returns:
            Node type string
        """
        # Handle different AST formats
        if 'type' in node:
            if node['type'] == 'tree':
                # Lark tree node
                return node.get('data', 'unknown')
            elif node['type'] == 'token':
                # Lark token node
                return node.get('data', 'unknown')
            else:
                # Direct type field
                return node['type']
        
        # Fallback
        return 'unknown'
    
    def generic_visit(self, node: Dict[str, Any]) -> Optional[T]:
        """Default visitor for nodes without specific handlers.
        
        Args:
            node: AST node
            
        Returns:
            Default result (visits children)
        """
        # Visit children if present
        children = node.get('children', [])
        if children:
            return self._visit_list(children)
        return None
    
    def get_current_context(self) -> Optional[Dict[str, Any]]:
        """Get the current context node.
        
        Returns:
            Current context node or None
        """
        return self.context_stack[-1] if self.context_stack else None
    
    def get_parent_context(self, levels: int = 1) -> Optional[Dict[str, Any]]:
        """Get a parent context node.
        
        Args:
            levels: Number of levels up to go
            
        Returns:
            Parent context node or None
        """
        if len(self.context_stack) > levels:
            return self.context_stack[-(levels + 1)]
        return None
    
    def add_error(self, message: str) -> None:
        """Add an error message.
        
        Args:
            message: Error message
        """
        context = self.get_current_context()
        if context:
            location = context.get('meta', {})
            line = location.get('line', '?')
            column = location.get('column', '?')
            self.errors.append(f"Line {line}:{column} - {message}")
        else:
            self.errors.append(message)
    
    def get_node_value(self, node: Dict[str, Any]) -> Optional[Any]:
        """Extract the value from a node.
        
        Args:
            node: AST node
            
        Returns:
            Node value or None
        """
        # Direct value
        if 'value' in node:
            return node['value']
            
        # Single child that's a value
        children = node.get('children', [])
        if len(children) == 1 and not isinstance(children[0], dict):
            return children[0]
            
        return None
    
    def get_child_by_index(self, node: Dict[str, Any], index: int) -> Optional[Any]:
        """Get a child node by index.
        
        Args:
            node: Parent node
            index: Child index
            
        Returns:
            Child node or None
        """
        children = node.get('children', [])
        if 0 <= index < len(children):
            return children[index]
        return None
    
    def get_children_by_type(self, node: Dict[str, Any], child_type: str) -> List[Dict[str, Any]]:
        """Get all children of a specific type.
        
        Args:
            node: Parent node
            child_type: Type of children to find
            
        Returns:
            List of matching children
        """
        children = node.get('children', [])
        results = []
        
        for child in children:
            if isinstance(child, dict) and self._get_node_type(child) == child_type:
                results.append(child)
                
        return results
    
    def find_child_by_type(self, node: Dict[str, Any], child_type: str) -> Optional[Dict[str, Any]]:
        """Find the first child of a specific type.
        
        Args:
            node: Parent node
            child_type: Type of child to find
            
        Returns:
            First matching child or None
        """
        children = self.get_children_by_type(node, child_type)
        return children[0] if children else None