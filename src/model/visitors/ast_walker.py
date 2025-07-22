"""AST walker utility for simple traversal operations.

This module provides utility functions for walking AST structures
and finding specific nodes without full visitor pattern overhead.
"""

from typing import Any, Dict, List, Optional, Callable, Union


class ASTWalker:
    """Utility class for walking AST structures."""
    
    @staticmethod
    def is_node(obj: Any) -> bool:
        """Check if an object is an AST node.
        
        Args:
            obj: Object to check
            
        Returns:
            True if the object is an AST node
        """
        return isinstance(obj, dict) and 'type' in obj
    
    @staticmethod
    def get_node_type(node: Dict[str, Any]) -> Optional[str]:
        """Get the type of an AST node.
        
        Args:
            node: AST node
            
        Returns:
            Node type or None
        """
        if not ASTWalker.is_node(node):
            return None
            
        # Handle different AST formats
        if node.get('type') == 'tree':
            return node.get('data')
        elif node.get('type') == 'token':
            return node.get('data')
        else:
            return node.get('type')
    
    @staticmethod
    def get_children(node: Dict[str, Any]) -> List[Any]:
        """Get the children of an AST node.
        
        Args:
            node: AST node
            
        Returns:
            List of child nodes
        """
        if not ASTWalker.is_node(node):
            return []
            
        # Handle different AST formats
        children = node.get('children', [])
        if not isinstance(children, list):
            return []
            
        return children
    
    @staticmethod
    def walk(node: Any, callback: Callable[[Dict[str, Any], int], None], depth: int = 0) -> None:
        """Walk an AST structure and call callback for each node.
        
        Args:
            node: Root node to walk
            callback: Function to call for each node (node, depth)
            depth: Current depth in the tree
        """
        if not ASTWalker.is_node(node):
            return
            
        # Call callback for current node
        callback(node, depth)
        
        # Recursively walk children
        for child in ASTWalker.get_children(node):
            if child is not None:
                ASTWalker.walk(child, callback, depth + 1)
    
    @staticmethod
    def find_by_type(root: Any, node_type: str) -> List[Dict[str, Any]]:
        """Find all nodes of a specific type.
        
        Args:
            root: Root node to search from
            node_type: Type of nodes to find
            
        Returns:
            List of matching nodes
        """
        results = []
        
        def collector(node: Dict[str, Any], depth: int) -> None:
            if ASTWalker.get_node_type(node) == node_type:                results.append(node)
        
        ASTWalker.walk(root, collector)
        return results
    
    @staticmethod
    def find_by_predicate(root: Any, predicate: Callable[[Dict[str, Any]], bool]) -> List[Dict[str, Any]]:
        """Find all nodes matching a predicate.
        
        Args:
            root: Root node to search from
            predicate: Function that returns True for matching nodes
            
        Returns:
            List of matching nodes
        """
        results = []
        
        def collector(node: Dict[str, Any], depth: int) -> None:
            if predicate(node):
                results.append(node)
        
        ASTWalker.walk(root, collector)
        return results
    
    @staticmethod
    def extract_identifiers(node: Dict[str, Any]) -> List[str]:
        """Extract all identifier tokens from a node and its children.
        
        Args:
            node: Node to extract from
            
        Returns:
            List of identifier values
        """
        identifiers = []
        
        def collector(n: Dict[str, Any], depth: int) -> None:
            if ASTWalker.get_node_type(n) == 'IDENTIFIER':
                value = n.get('value')
                if value:
                    identifiers.append(value)
        
        ASTWalker.walk(node, collector)
        return identifiers
    
    @staticmethod
    def extract_value(node: Dict[str, Any]) -> Optional[Union[str, int, float, bool]]:
        """Extract the value from a node.
        
        Args:
            node: Node to extract value from
            
        Returns:
            Extracted value or None
        """
        if not ASTWalker.is_node(node):
            return None
            
        # Direct value
        if 'value' in node:
            return node['value']
            
        # Check children for literal nodes
        children = ASTWalker.get_children(node)
        if len(children) == 1 and isinstance(children[0], (str, int, float, bool)):
            return children[0]
            
        return None
    
    @staticmethod
    def find_first_by_type(root: Any, node_type: str) -> Optional[Dict[str, Any]]:
        """Find the first node of a specific type.
        
        Args:
            root: Root node to search from
            node_type: Type of node to find
            
        Returns:
            First matching node or None
        """
        nodes = ASTWalker.find_by_type(root, node_type)
        return nodes[0] if nodes else None
    
    @staticmethod
    def get_path_to_node(root: Any, target: Dict[str, Any]) -> Optional[List[Dict[str, Any]]]:
        """Get the path from root to a target node.
        
        Args:
            root: Root node
            target: Target node to find path to
            
        Returns:
            List of nodes from root to target, or None if not found
        """
        path = []
        
        def search(node: Any) -> bool:
            if not ASTWalker.is_node(node):
                return False
                
            path.append(node)
            
            if node is target:
                return True
                
            for child in ASTWalker.get_children(node):
                if search(child):
                    return True
                    
            path.pop()
            return False
        
        if search(root):
            return path
        return None