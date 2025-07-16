"""PowerBuilder type system classes.

This module provides classes for representing the PowerBuilder type system,
including basic types, custom types, arrays, and type nodes.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from src.base import PBNode


@dataclass
class PBType:
    """Base class for PowerBuilder types."""

    name: str = ""
    category: str = "unknown"
    nullable: bool = False
    min_value: Any | None = None
    max_value: Any | None = None
    references: set[str] = field(default_factory=set)
    _owner: Any | None = field(default=None, init=False, repr=False)

    @property
    def is_basic(self) -> bool:


        """Check if this is a basic type."""
        return False

    @property
    def is_custom(self) -> bool:


        """Check if this is a custom type."""
        return False

    @property
    def is_array(self) -> bool:


        """Check if this is an array type."""
        return False

    @property
    def is_datawindow(self) -> bool:


        """Check if this is a datawindow type."""
        return False

    def accepts(self, other: PBType) -> bool:




        """Check if this type accepts another type."""
        return self == other

    def add_reference(self, ref: str) -> None:




        """Add a reference to this type."""
        self.references.add(ref)

    def remove_reference(self, ref: str) -> None:




        """Remove a reference from this type."""
        self.references.discard(ref)

    def get_reachable_entities(self) -> list[Any]:




        """Get all entities reachable from this type."""
        return []

    def set_owner(self, owner: Any) -> None:




        """Set the owner of this type."""
        self._owner = owner

    def get_owner(self) -> Any | None:




        """Get the owner of this type."""
        return self._owner


@dataclass
class PBBasicType(PBType):
    """PowerBuilder basic/primitive type."""

    size: int | None = None

    def __post_init__(self) -> None:




        """Initialize category."""
        self.category = "basic"

    @property
    def is_basic(self) -> bool:


        """Check if this is a basic type."""
        return True

    def accepts(self, other: PBType) -> bool:




        """Check if this type accepts another type."""
        return isinstance(other, PBBasicType) and self.name == other.name


@dataclass 
class PBCustomType(PBType):
    """PowerBuilder custom/user-defined type."""

    base_class: str | None = None
    super_type: PBCustomType | None = None
    namespace: str | None = None
    is_interface: bool = False
    attributes: dict[str, PBType] = field(default_factory=dict)

    def __post_init__(self) -> None:




        """Initialize category."""
        self.category = "custom"

    @property
    def is_custom(self) -> bool:


        """Check if this is a custom type."""
        return True

    def accepts(self, other: PBType) -> bool:




        """Check if this type accepts another type (supports inheritance)."""
        if not isinstance(other, PBCustomType):
            return False

        # Same type
        if self.name == other.name:
            return True

        # Check inheritance - accepts derived types
        current = other
        while current.super_type:
            if current.super_type.name == self.name:
                return True
            current = current.super_type

        return False

    def add_attribute(self, name: str, attr_type: PBType) -> None:




        """Add an attribute to this type."""
        self.attributes[name] = attr_type

    def get_attribute(self, name: str) -> PBType | None:




        """Get an attribute by name."""
        return self.attributes.get(name)

    def get_reachable_entities(self) -> list[PBCustomType]:




        """Get all entities reachable from this type."""
        entities = [self]
        if self.super_type:
            entities.extend(self.super_type.get_reachable_entities())
        return entities

    @property
    def qualified_name(self) -> str:


        """Get the fully qualified name including namespace."""
        if self.namespace:
            return f"{self.namespace}.{self.name}"
        return self.name


@dataclass
class PBArrayType(PBType):
    """PowerBuilder array type."""

    element_type: PBType = None  # Make it optional with a default
    dimensions: int | list[int] = field(default_factory=list)  # Can be int or list
    bounds: list[tuple[int, int | None]] = None

    def __post_init__(self) -> None:




        """Initialize category and name."""
        self.category = "array"

        # Determine number of dimensions
        if isinstance(self.dimensions, int):
            num_dims = self.dimensions
        else:
            num_dims = len(self.dimensions)

        # Auto-generate name if not provided
        if not self.name and self.element_type:
            brackets = "[]" * num_dims
            self.name = f"{self.element_type.name}{brackets}"

    @property
    def is_array(self) -> bool:


        """Check if this is an array type."""
        return True

    def accepts(self, other: PBType) -> bool:




        """Check if this type accepts another type."""
        if not isinstance(other, PBArrayType):
            return False

        # Check dimensions match
        if len(self.dimensions) != len(other.dimensions):
            return False

        # Check element type compatibility
        return self.element_type.accepts(other.element_type)


@dataclass
class PBDataWindowType(PBCustomType):
    """PowerBuilder DataWindow type."""

    def __post_init__(self) -> None:




        """Initialize as DataWindow type."""
        super().__post_init__()
        self.base_class = "datawindow"

    @property
    def is_datawindow(self) -> bool:


        """Check if this is a datawindow type."""
        return True


@dataclass
class PBParametrizedType(PBType):
    """PowerBuilder parameterized type (e.g., collections with type parameters)."""

    base_type: str = ""  # The base type name (e.g., "list", "collection")
    type_parameters: list[PBType] = field(default_factory=list)

    def __post_init__(self) -> None:




        """Initialize category and name."""
        self.category = "parameterized"

        # Auto-generate name if not provided
        if not self.name and self.base_type and self.type_parameters:
            param_names = ", ".join(p.name for p in self.type_parameters)
            self.name = f"{self.base_type}<{param_names}>"

    @property
    def is_parameterized(self) -> bool:


        """Check if this is a parameterized type."""
        return True

    def accepts(self, other: PBType) -> bool:




        """Check if this type accepts another type."""
        if not isinstance(other, PBParametrizedType):
            return False

        # Check base type matches
        if self.base_type != other.base_type:
            return False

        # Check same number of type parameters
        if len(self.type_parameters) != len(other.type_parameters):
            return False

        # Check each type parameter is compatible
        for self_param, other_param in zip(self.type_parameters, other.type_parameters):
            if not self_param.accepts(other_param):
                return False

        return True


@dataclass
class PBFormatType(PBType):
    """PowerBuilder type with format/display mask information."""

    base_type: PBType = None
    format_string: str = ""  # Format mask (e.g., "###, ##0.00", "mm/dd/yyyy")
    edit_mask: str | None = None  # Edit mask for data entry
    display_format: str | None = None  # Display format

    def __post_init__(self) -> None:




        """Initialize category and name."""
        self.category = "formatted"

        # Auto-generate name if not provided
        if not self.name and self.base_type:
            self.name = f"{self.base_type.name}[{self.format_string}]"

    @property
    def is_formatted(self) -> bool:


        """Check if this is a formatted type."""
        return True

    def accepts(self, other: PBType) -> bool:




        """Check if this type accepts another type."""
        # A formatted type accepts the same base type or another formatted type with same base
        if isinstance(other, PBFormatType):
            return self.base_type.accepts(other.base_type)
        else:
            return self.base_type.accepts(other)

    def get_effective_type(self) -> PBType:




        """Get the underlying type without formatting."""
        return self.base_type


# Type node classes for AST representation

@dataclass
class PBTypeNode(PBNode):
    """Base class for type nodes in the AST."""

    type_name: str = ""


@dataclass
class PBBasicTypeNode(PBTypeNode):
    """Basic type node in the AST."""

    is_array: bool = False


@dataclass
class PBCustomTypeNode(PBTypeNode):
    """Custom type node in the AST."""

    base_type: str | None = None


# Type registry for managing types

class PBTypeRegistry:
    """Registry for managing PowerBuilder types."""

    def __init__(self) -> None:




        """Initialize the type registry."""
        self._types: dict[str, PBType] = {}
        self._initialize_basic_types()

    def _initialize_basic_types(self) -> None:




        """Initialize standard PowerBuilder basic types."""
        basic_types = [
            "byte", "integer", "long", "decimal", "real", "double", "string", "char", "boolean", "date", "time", "datetime", "blob", "any", "uint", "ulong",
        ]

        for type_name in basic_types:
            self.register(PBBasicType(name=type_name))

    def register(self, pb_type: PBType) -> None:




        """Register a type."""
        # Always register by qualified name if it's a custom type with namespace
        if isinstance(pb_type, PBCustomType) and pb_type.namespace:
            self._types[pb_type.qualified_name] = pb_type
            # Only register by simple name if no conflict exists
            if pb_type.name not in self._types:
                self._types[pb_type.name] = pb_type
            else:
                # If there's a conflict, remove the simple name entry
                if pb_type.name in self._types:
                    del self._types[pb_type.name]
        else:
            # No namespace, register by simple name
            self._types[pb_type.name] = pb_type

    def register_type(self, pb_type: PBType) -> None:




        """Register a type (alias for register)."""
        self.register(pb_type)

    def get(self, name: str) -> PBType | None:




        """Get a type by name."""
        return self._types.get(name)

    def get_type(self, name: str) -> PBType | None:




        """Get a type by name (alias for get)."""
        return self.get(name)

    def exists(self, name: str) -> bool:




        """Check if a type exists."""
        return name in self._types

    def get_all(self) -> list[PBType]:




        """Get all registered types."""
        return list(self._types.values())

    def create_array_type(self, element_type: PBType, dimensions: list[int]) -> PBArrayType:




        """Create and register an array type."""
        array_type = PBArrayType(element_type=element_type, dimensions=dimensions)
        self.register(array_type)
        return array_type


# Aliases for backward compatibility
DataType = PBType  # DataType is an alias for PBType


# Entity classes that were in the tests
@dataclass
class PBSourcedEntity(PBNode):
    """Entity with source information."""

    name: str = ""
    source_file: str | None = None


__all__ = [
    "PBType", "PBBasicType", "PBCustomType", "PBArrayType", "PBDataWindowType", "PBParametrizedType", "PBFormatType", "PBTypeNode", "PBBasicTypeNode", "PBCustomTypeNode", "PBTypeRegistry", "DataType", "PBSourcedEntity", ]
