"""Type-related AST nodes for PowerBuilder.

This module contains AST nodes for type declarations, type references,
and array operations.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum, auto
from typing import Any, Dict, List, Optional, Union

from model.utils.base import PBNode
from .ast_nodes import Expression, Statement


class TypeCategory(Enum):
    """Categories of types in PowerBuilder."""
    
    BASIC = auto()
    NUMERIC = auto()  # For numeric types (integer, long, decimal, etc.)
    TEXT = auto()     # For string/text types
    LOGICAL = auto()  # For boolean types
    ARRAY = auto()
    CUSTOM = auto()
    STRUCTURE = auto()
    ENUMERATION = auto()
    OBJECT = auto()
    WINDOW = auto()
    DATAWINDOW = auto()
    MENU = auto()


@dataclass
class Field(PBNode):
    """A field in a structure."""
    
    name: str
    field_type: Type
    initial_value: Optional[Any] = None
    is_nullable: bool = True
    
    def __str__(self) -> str:
        return f"{self.name}: {self.field_type}"


@dataclass
class Type(PBNode):
    """Base class for all types."""
    
    name: str
    category: TypeCategory = field(default=TypeCategory.BASIC)
    is_nullable: bool = field(default=True)
    is_array: bool = field(default=False)
    array_bounds: Optional[List[int]] = field(default=None)
    
    def __str__(self) -> str:
        return self.name
    
    def __hash__(self) -> int:
        """Custom hash that handles mutable fields."""
        # Convert array_bounds to tuple for hashing (or use 0 if None)
        bounds_tuple = tuple(self.array_bounds) if self.array_bounds else ()
        return hash((self.name, self.category, self.is_nullable, self.is_array, bounds_tuple))


@dataclass
class BasicType(Type):
    """Represents a basic/primitive type."""
    
    def __post_init__(self):
        # Set category to BASIC if not already set
        self.category = TypeCategory.BASIC


@dataclass
class TypeBounds:
    """Represents array bounds."""
    
    lower: Optional[int] = None
    upper: Optional[int] = None
    
    def __str__(self) -> str:
        if self.lower is None and self.upper is None:
            return "[]"
        elif self.lower is None:
            return f"[{self.upper}]"
        else:
            return f"[{self.lower}:{self.upper}]"


@dataclass
class ArrayType(Type):
    """Represents an array type."""
    
    element_type: Type = field(default=None)
    bounds: List[TypeBounds] = field(default_factory=list)
    
    def __post_init__(self):
        self.category = TypeCategory.ARRAY
        if self.element_type is None:
            raise ValueError("ArrayType requires element_type")
    
    def __str__(self) -> str:
        bounds_str = "".join(str(b) for b in self.bounds)
        return f"{self.element_type}{bounds_str}"


@dataclass
class CustomType(Type):
    """Represents a user-defined type."""
    
    parent_type: Optional[str] = None
    members: Dict[str, Type] = field(default_factory=dict)
    methods: List[str] = field(default_factory=list)
    is_global: bool = False
    namespace: Optional[str] = None
    
    def __post_init__(self):
        self.category = TypeCategory.CUSTOM
    
    def add_member(self, name: str, member_type: Type) -> None:
        """Add a member to this custom type."""
        self.members[name] = member_type
    
    def add_method(self, name: str) -> None:
        """Add a method to this custom type."""
        if name not in self.methods:
            self.methods.append(name)


@dataclass
class ArrayDeclaration(Statement):
    """Array declaration statement."""
    
    variable_name: str = ""
    array_type: Optional[ArrayType] = None
    initial_value: Optional[Expression] = None
    
    def __post_init__(self):
        if not self.variable_name:
            raise ValueError("ArrayDeclaration requires variable_name")
        if self.array_type is None:
            raise ValueError("ArrayDeclaration requires array_type")
    
    def accept(self, visitor):
        """Accept a visitor."""
        return visitor.visit_array_declaration(self)


@dataclass
class ArrayAccess(Expression):
    """Array access expression."""
    
    array: Optional[Expression] = None
    indices: List[Expression] = field(default_factory=list)
    
    def __post_init__(self):
        if self.array is None:
            raise ValueError("ArrayAccess requires array")
        if not self.indices:
            raise ValueError("ArrayAccess requires at least one index")
    
    def accept(self, visitor):
        """Accept a visitor."""
        return visitor.visit_array_access(self)


@dataclass
class ArrayAssignment(Statement):
    """Array element assignment."""
    
    array_access: Optional[ArrayAccess] = None
    value: Optional[Expression] = None
    
    def __post_init__(self):
        if self.array_access is None:
            raise ValueError("ArrayAssignment requires array_access")
        if self.value is None:
            raise ValueError("ArrayAssignment requires value")
    
    def accept(self, visitor):
        """Accept a visitor."""
        return visitor.visit_array_assignment(self)


@dataclass
class ArrayOperation(Expression):
    """Array operation (e.g., resize, copy)."""
    
    operation: str = ""  # e.g., "resize", "copy", "clear"
    array: Optional[Expression] = None
    arguments: List[Expression] = field(default_factory=list)
    
    def __post_init__(self):
        if not self.operation:
            raise ValueError("ArrayOperation requires operation")
        if self.array is None:
            raise ValueError("ArrayOperation requires array")
    
    def accept(self, visitor):
        """Accept a visitor."""
        return visitor.visit_array_operation(self)


@dataclass
class ArraySlice(Expression):
    """Array slice expression."""
    
    array: Optional[Expression] = None
    start: Optional[Expression] = None
    end: Optional[Expression] = None
    step: Optional[Expression] = None
    
    def __post_init__(self):
        if self.array is None:
            raise ValueError("ArraySlice requires array")
    
    def accept(self, visitor):
        """Accept a visitor."""
        return visitor.visit_array_slice(self)


@dataclass
class Structure(Type):
    """Represents a structure type."""
    
    fields: List[Field] = field(default_factory=list)
    is_global: bool = False
    
    def __post_init__(self):
        self.category = TypeCategory.STRUCTURE
    
    def add_field(self, field: Field) -> None:
        """Add a field to this structure."""
        self.fields.append(field)
    
    def get_field(self, name: str) -> Optional[Field]:
        """Get a field by name."""
        for f in self.fields:
            if f.name == name:
                return f
        return None


class TypeRegistry:
    """Registry for managing custom types."""
    
    def __init__(self):
        self._types: Dict[str, Type] = {}
        self._initialize_basic_types()
    
    def _initialize_basic_types(self):
        """Initialize registry with PowerBuilder basic types."""
        basic_types = [
            "integer", "long", "decimal", "real", "double",
            "string", "char", "boolean", "date", "time", 
            "datetime", "blob", "any"
        ]
        
        for type_name in basic_types:
            self.register_type(type_name, BasicType(name=type_name))
    
    def register_type(self, name: str, type_def: Type) -> None:
        """Register a type definition."""
        self._types[name.lower()] = type_def
    
    def get_type(self, name: str) -> Optional[Type]:
        """Get a type definition by name."""
        return self._types.get(name.lower())
    
    def is_registered(self, name: str) -> bool:
        """Check if a type is registered."""
        return name.lower() in self._types
    
    def all_types(self) -> Dict[str, Type]:
        """Get all registered types."""
        return self._types.copy()