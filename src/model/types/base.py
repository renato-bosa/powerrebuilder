"""Base types for the PowerRebuilder model module.

This module provides fundamental types used throughout the model stage,
including base node classes, enums, and type definitions.
"""

from dataclasses import dataclass, field
from enum import Enum, auto
from typing import Any, Dict, List, Optional, Union
from abc import ABC, abstractmethod


class NodeKind(Enum):
    """Enumeration of AST node types."""
    
    # Structural nodes
    FILE = auto()
    MODULE = auto()
    CLASS = auto()
    FUNCTION = auto()
    METHOD = auto()
    PROPERTY = auto()
    EVENT = auto()
    
    # Statement nodes
    STATEMENT = auto()
    EXPRESSION = auto()
    DECLARATION = auto()
    ASSIGNMENT = auto()
    IF_STATEMENT = auto()
    WHILE_LOOP = auto()
    FOR_LOOP = auto()
    CASE_STATEMENT = auto()
    TRY_CATCH = auto()
    RETURN_STATEMENT = auto()
    
    # Expression nodes
    BINARY_OP = auto()
    UNARY_OP = auto()
    CALL = auto()
    IDENTIFIER = auto()
    LITERAL = auto()
    ARRAY_ACCESS = auto()
    MEMBER_ACCESS = auto()
    
    # Type nodes
    TYPE = auto()
    BASIC_TYPE = auto()
    CUSTOM_TYPE = auto()
    ARRAY_TYPE = auto()
    
    # SQL nodes
    SQL_SELECT = auto()
    SQL_INSERT = auto()
    SQL_UPDATE = auto()
    SQL_DELETE = auto()
    
    # Special nodes
    UNKNOWN = auto()
    ERROR = auto()


@dataclass
class SourceAnchor:
    """Source location information for AST nodes."""
    
    file: Optional[str] = None
    line: Optional[int] = None
    column: Optional[int] = None
    start_pos: Optional[int] = None
    end_pos: Optional[int] = None
    
    def __str__(self) -> str:
        """String representation of source location."""
        if self.file and self.line:
            return f"{self.file}:{self.line}:{self.column or 0}"
        elif self.line:
            return f"line {self.line}:{self.column or 0}"
        else:
            return "unknown location"


@dataclass
class PBNode(ABC):
    """Base class for all PowerBuilder AST nodes.
    
    This is the fundamental building block of the AST representation.
    All AST nodes inherit from this class.
    """
    
    name: Optional[str] = None
    kind: NodeKind = NodeKind.UNKNOWN
    source_anchor: Optional[SourceAnchor] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    children: List["PBNode"] = field(default_factory=list)
    parent: Optional["PBNode"] = None
    
    def __post_init__(self):
        """Initialize parent references for children."""
        for child in self.children:
            if isinstance(child, PBNode):
                child.parent = self
    
    @abstractmethod
    def accept(self, visitor: "Visitor") -> Any:
        """Accept a visitor for the visitor pattern.
        
        Args:
            visitor: The visitor to accept
            
        Returns:
            Result from the visitor's visit method
        """
        pass
    
    def add_child(self, child: "PBNode") -> None:
        """Add a child node.
        
        Args:
            child: The child node to add
        """
        if child and isinstance(child, PBNode):
            child.parent = self
            self.children.append(child)
    
    def remove_child(self, child: "PBNode") -> bool:
        """Remove a child node.
        
        Args:
            child: The child node to remove
            
        Returns:
            True if the child was removed, False otherwise
        """
        try:
            self.children.remove(child)
            child.parent = None
            return True
        except ValueError:
            return False
    
    def find_children(self, kind: NodeKind) -> List["PBNode"]:
        """Find all children of a specific kind.
        
        Args:
            kind: The node kind to search for
            
        Returns:
            List of matching child nodes
        """
        return [child for child in self.children if child.kind == kind]
    
    def find_ancestor(self, kind: NodeKind) -> Optional["PBNode"]:
        """Find the first ancestor of a specific kind.
        
        Args:
            kind: The node kind to search for
            
        Returns:
            The first matching ancestor or None
        """
        current = self.parent
        while current:
            if current.kind == kind:
                return current
            current = current.parent
        return None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert the node to a dictionary representation.
        
        Returns:
            Dictionary representation of the node
        """
        result = {
            "kind": self.kind.name,
            "name": self.name,
        }
        
        if self.source_anchor:
            result["source"] = {
                "file": self.source_anchor.file,
                "line": self.source_anchor.line,
                "column": self.source_anchor.column,
            }
        
        if self.metadata:
            result["metadata"] = self.metadata
        
        if self.children:
            result["children"] = [child.to_dict() for child in self.children]
        
        return result


class Visitor(ABC):
    """Abstract base class for AST visitors."""
    
    @abstractmethod
    def visit(self, node: PBNode) -> Any:
        """Visit a node.
        
        Args:
            node: The node to visit
            
        Returns:
            Result of the visit
        """
        pass


@dataclass
class Type(PBNode):
    """Base class for type nodes."""
    
    type_name: str = ""
    is_array: bool = False
    is_nullable: bool = True
    
    def __post_init__(self):
        super().__post_init__()
        self.kind = NodeKind.TYPE
    
    def accept(self, visitor: Visitor) -> Any:
        return visitor.visit(self)


@dataclass
class BasicType(Type):
    """Represents a basic/primitive type."""
    
    def __post_init__(self):
        super().__post_init__()
        self.kind = NodeKind.BASIC_TYPE


@dataclass
class CustomType(Type):
    """Represents a custom/user-defined type."""
    
    base_type: Optional[str] = None
    
    def __post_init__(self):
        super().__post_init__()
        self.kind = NodeKind.CUSTOM_TYPE


@dataclass
class ArrayType(Type):
    """Represents an array type."""
    
    element_type: Optional[Type] = None
    dimensions: List[Optional[int]] = field(default_factory=list)
    
    def __post_init__(self):
        super().__post_init__()
        self.kind = NodeKind.ARRAY_TYPE
        self.is_array = True


# Type aliases for convenience
NodeDict = Dict[str, Any]
NodeList = List[PBNode]
NodeOrDict = Union[PBNode, NodeDict]


# Common type constants
STRING_TYPE = BasicType(type_name="string")
INTEGER_TYPE = BasicType(type_name="integer")
LONG_TYPE = BasicType(type_name="long")
DECIMAL_TYPE = BasicType(type_name="decimal")
BOOLEAN_TYPE = BasicType(type_name="boolean")
DATE_TYPE = BasicType(type_name="date")
TIME_TYPE = BasicType(type_name="time")
DATETIME_TYPE = BasicType(type_name="datetime")
ANY_TYPE = BasicType(type_name="any")
VOID_TYPE = BasicType(type_name="void")


def create_node_from_dict(data: Dict[str, Any]) -> PBNode:
    """Create a PBNode from a dictionary representation.
    
    Args:
        data: Dictionary containing node data
        
    Returns:
        PBNode instance
    """
    # This is a simplified factory - extend as needed
    kind_str = data.get("kind", "UNKNOWN")
    kind = NodeKind[kind_str] if kind_str in NodeKind.__members__ else NodeKind.UNKNOWN
    
    # Create source anchor if present
    source_anchor = None
    if "source" in data:
        source_data = data["source"]
        source_anchor = SourceAnchor(
            file=source_data.get("file"),
            line=source_data.get("line"),
            column=source_data.get("column"),
            start_pos=source_data.get("start_pos"),
            end_pos=source_data.get("end_pos")
        )
    
    # Create appropriate node type based on kind
    if kind in [NodeKind.BASIC_TYPE, NodeKind.CUSTOM_TYPE, NodeKind.ARRAY_TYPE]:
        if kind == NodeKind.BASIC_TYPE:
            node = BasicType(type_name=data.get("type_name", ""))
        elif kind == NodeKind.CUSTOM_TYPE:
            node = CustomType(
                type_name=data.get("type_name", ""),
                base_type=data.get("base_type")
            )
        else:  # ARRAY_TYPE
            node = ArrayType(
                type_name=data.get("type_name", ""),
                dimensions=data.get("dimensions", [])
            )
    else:
        # Generic node for now - extend with specific node types as needed
        class GenericNode(PBNode):
            def accept(self, visitor: Visitor) -> Any:
                return visitor.visit(self)
        
        node = GenericNode(
            name=data.get("name"),
            kind=kind,
            source_anchor=source_anchor,
            metadata=data.get("metadata", {})
        )
    
    # Recursively create children
    if "children" in data:
        for child_data in data["children"]:
            if isinstance(child_data, dict):
                child = create_node_from_dict(child_data)
                node.add_child(child)
    
    return node