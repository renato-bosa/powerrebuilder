"""Base types to prevent circular dependencies.

These types can be imported by any module without creating cycles.
"""

from dataclasses import dataclass, field
from enum import Enum, auto
from typing import Any, Dict, List, Optional, Tuple, Union


@dataclass
class SourceAnchor:
    """Represents a position in source code."""
    line: int
    column: int
    offset: Optional[int] = None
    file_path: Optional[str] = None


@dataclass
class PBNode:
    """Base class for all PowerBuilder AST nodes."""
    
    # Source tracking fields with default values
    start_position: Optional[int] = field(default=None, init=False)
    stop_position: Optional[int] = field(default=None, init=False)
    source_file: Optional[str] = field(default=None, init=False)
    
    @property
    def kind(self) -> "NodeKind":
        """Get the node kind for this AST node.
        
        Subclasses should override this to return the appropriate NodeKind value.
        """
        return NodeKind.UNKNOWN
    
    def __eq__(self, other) -> bool:
        if not isinstance(other, self.__class__):
            return False
        return self.__dict__ == other.__dict__
    
    def __hash__(self):
        return hash(tuple(sorted(self.__dict__.items())))
    
    def validate(self, context: Optional[Dict[str, Any]] = None) -> bool:
        """Validate this node in the given context.
        
        Args:
            context: Dictionary containing validation context, such as type_registry, expected return type, parent scope, etc.
            
        Returns:
            bool: True if valid, False otherwise
        """
        # Base implementation always passes - subclasses should override
        return True


class NodeKind(Enum):
    """Enumeration of all PowerBuilder AST node types."""

    # ─── Base Node Types ──────────────────────────────────────────────────────
    UNKNOWN = auto()
    ERROR = auto()

    # ─── Statement Types ──────────────────────────────────────────────────────
    STATEMENT = auto()
    ASSIGNMENT_STATEMENT = auto()
    EXPRESSION_STATEMENT = auto()
    RETURN_STATEMENT = auto()
    IF_STATEMENT = auto()
    ELSE_STATEMENT = auto()
    ELSEIF_STATEMENT = auto()
    FOR_LOOP = auto()
    WHILE_LOOP = auto()
    DO_WHILE_LOOP = auto()
    DO_UNTIL_LOOP = auto()
    REPEAT_UNTIL_LOOP = auto()
    CONTINUE_STATEMENT = auto()
    BREAK_STATEMENT = auto()
    EXIT_STATEMENT = auto()
    GOTO_STATEMENT = auto()
    CASE_STATEMENT = auto()
    CHOOSE_CASE_STATEMENT = auto()
    TRY_CATCH_STATEMENT = auto()
    THROW_STATEMENT = auto()

    # ─── Declaration Types ────────────────────────────────────────────────────
    VARIABLE_DECLARATION = auto()
    CONSTANT_DECLARATION = auto()
    FUNCTION_DECLARATION = auto()
    PROCEDURE_DECLARATION = auto()
    EVENT_DECLARATION = auto()
    TYPE_DECLARATION = auto()
    FORWARD_DECLARATION = auto()
    GLOBAL_DECLARATION = auto()
    SHARED_DECLARATION = auto()

    # ─── Expression Types ─────────────────────────────────────────────────────
    EXPRESSION = auto()
    BINARY_EXPRESSION = auto()
    UNARY_EXPRESSION = auto()
    TERNARY_EXPRESSION = auto()
    LITERAL_EXPRESSION = auto()
    IDENTIFIER_EXPRESSION = auto()
    MEMBER_ACCESS_EXPRESSION = auto()
    ARRAY_ACCESS_EXPRESSION = auto()
    FUNCTION_CALL_EXPRESSION = auto()
    METHOD_CALL_EXPRESSION = auto()
    CAST_EXPRESSION = auto()
    PARENTHESIZED_EXPRESSION = auto()

    # ─── Literal Types ────────────────────────────────────────────────────────
    INTEGER_LITERAL = auto()
    REAL_LITERAL = auto()
    STRING_LITERAL = auto()
    BOOLEAN_LITERAL = auto()
    NULL_LITERAL = auto()
    DATE_LITERAL = auto()
    TIME_LITERAL = auto()

    # ─── Type Types ───────────────────────────────────────────────────────────
    BASIC_TYPE = auto()
    ARRAY_TYPE = auto()
    CUSTOM_TYPE = auto()
    ENUMERATED_TYPE = auto()

    # ─── Object Types ─────────────────────────────────────────────────────────
    WINDOW = auto()
    USER_OBJECT = auto()
    MENU = auto()
    DATAWINDOW = auto()
    STRUCTURE = auto()

    # ─── Control Types ────────────────────────────────────────────────────────
    CONTROL = auto()
    BUTTON_CONTROL = auto()
    EDIT_CONTROL = auto()
    STATIC_TEXT_CONTROL = auto()
    CHECKBOX_CONTROL = auto()
    RADIOBUTTON_CONTROL = auto()
    LISTBOX_CONTROL = auto()
    DROPDOWNLIST_CONTROL = auto()
    COMBOBOX_CONTROL = auto()
    PICTURE_CONTROL = auto()
    GROUPBOX_CONTROL = auto()
    TREEVIEW_CONTROL = auto()
    LISTVIEW_CONTROL = auto()
    RICHTEXT_CONTROL = auto()
    DATAWINDOW_CONTROL = auto()
    TAB_CONTROL = auto()

    # ─── SQL Types ────────────────────────────────────────────────────────────
    SQL_STATEMENT = auto()
    SQL_SELECT = auto()
    SQL_INSERT = auto()
    SQL_UPDATE = auto()
    SQL_DELETE = auto()
    SQL_CURSOR = auto()
    SQL_PROCEDURE = auto()
    SQL_TRANSACTION = auto()
    SQL_QUERY = auto()
    SQL_COMMIT = auto()
    SQL_ROLLBACK = auto()
    SQL_PREPARE = auto()
    SQL_VARIABLE = auto()
    SQL_PARAMETER = auto()

    # ─── DataWindow Types ─────────────────────────────────────────────────────
    DW_COLUMN = auto()
    DW_COMPUTE = auto()
    DW_TABLE = auto()
    DW_GRAPH = auto()
    DW_CROSSTAB = auto()
    DW_NESTED = auto()

    # ─── Event Types ──────────────────────────────────────────────────────────
    EVENT = auto()
    EVENT_TRIGGER = auto()
    EVENT_POST = auto()
    SYSTEM_EVENT = auto()
    USER_EVENT = auto()

    # ─── Behavioral Types ─────────────────────────────────────────────────────
    BEHAVIORAL = auto()
    BEHAVIORAL_OPTION = auto()
    BEHAVIORAL_ALIAS = auto()
    BEHAVIORAL_LIBRARY = auto()

    # ─── Modifier Types ───────────────────────────────────────────────────────
    ACCESS_MODIFIER = auto()
    ARGUMENT_MODIFIER = auto()

    # ─── Other Types ──────────────────────────────────────────────────────────
    COMMENT = auto()
    ATTRIBUTE = auto()
    PARAMETER = auto()
    ARGUMENT = auto()
    IMPORT = auto()
    EXPORT = auto()
    LIBRARY = auto()
    
    # Backward compatibility aliases
    CLASS = CUSTOM_TYPE
    FUNCTION = FUNCTION_DECLARATION
    VARIABLE = VARIABLE_DECLARATION
    PROPERTY = auto()
    ASSIGNMENT = ASSIGNMENT_STATEMENT
    FOR_STATEMENT = FOR_LOOP
    WHILE_STATEMENT = WHILE_LOOP
    IDENTIFIER = IDENTIFIER_EXPRESSION
    LITERAL = LITERAL_EXPRESSION
    CALL_EXPRESSION = FUNCTION_CALL_EXPRESSION
    MEMBER_EXPRESSION = MEMBER_ACCESS_EXPRESSION
    PRIMITIVE_TYPE = BASIC_TYPE
    OBJECT_TYPE = CUSTOM_TYPE
    GENERIC_TYPE = auto()
    PROGRAM = auto()
    BLOCK = auto()

    def is_statement(self) -> bool:
        """Check if this node kind represents a statement."""
        return self.name.endswith("_STATEMENT") or self in {
            NodeKind.FOR_LOOP, NodeKind.WHILE_LOOP, NodeKind.DO_WHILE_LOOP, 
            NodeKind.DO_UNTIL_LOOP, NodeKind.REPEAT_UNTIL_LOOP, 
        }

    def is_expression(self) -> bool:
        """Check if this node kind represents an expression."""
        return self.name.endswith("_EXPRESSION") or self.name.endswith("_LITERAL")

    def is_declaration(self) -> bool:
        """Check if this node kind represents a declaration."""
        return self.name.endswith("_DECLARATION")

    def is_control(self) -> bool:
        """Check if this node kind represents a UI control."""
        return self.name.endswith("_CONTROL") or self == NodeKind.CONTROL

    def is_type(self) -> bool:
        """Check if this node kind represents a type."""
        return self.name.endswith("_TYPE") and self not in {
            NodeKind.SYSTEM_EVENT, NodeKind.USER_EVENT, 
        }

    def is_sql(self) -> bool:
        """Check if this node kind represents SQL-related node."""
        return self.name.startswith("SQL_")

    def is_datawindow(self) -> bool:
        """Check if this node kind represents DataWindow-related node."""
        return self.name.startswith("DW_") or self == NodeKind.DATAWINDOW


@dataclass(frozen=True)
class Position:
    """Position in source code."""
    line: int
    column: int
    offset: Optional[int] = None
    
    def __str__(self) -> str:
        return f"{self.line}:{self.column}"


@dataclass(frozen=True)
class SourceLocation:
    """Source location with start and end positions."""
    start: Position
    end: Position
    filename: Optional[str] = None
    
    def __str__(self) -> str:
        if self.filename:
            return f"{self.filename}:{self.start}"
        return str(self.start)


@dataclass
class Identifier:
    """Identifier representation."""
    name: str
    location: Optional[SourceLocation] = None
    
    def __str__(self) -> str:
        return self.name


@dataclass
class QualifiedName:
    """Qualified name (e.g., namespace.class.member)."""
    parts: List[str]
    location: Optional[SourceLocation] = None
    
    def __str__(self) -> str:
        return ".".join(self.parts)
    
    @classmethod
    def from_string(cls, name: str, location: Optional[SourceLocation] = None) -> "QualifiedName":
        """Create from dotted string."""
        return cls(parts=name.split("."), location=location)


# Type aliases for common structures
TypeName = Union[str, QualifiedName]
Visibility = str  # "public", "private", "protected"
Modifiers = List[str]  # ["static", "readonly", etc.]


@dataclass
class TypeReference:
    """Reference to a type."""
    name: TypeName
    type_arguments: Optional[List["TypeReference"]] = None
    is_array: bool = False
    array_dimensions: Optional[List[Optional[int]]] = None
    location: Optional[SourceLocation] = None
    
    def __str__(self) -> str:
        base = str(self.name)
        if self.type_arguments:
            args = ", ".join(str(arg) for arg in self.type_arguments)
            base = f"{base}<{args}>"
        if self.is_array:
            dims = "[]" * (len(self.array_dimensions) if self.array_dimensions else 1)
            base = f"{base}{dims}"
        return base


@dataclass
class Parameter:
    """Function/method parameter."""
    name: str
    type: Optional[TypeReference] = None
    default_value: Any = None
    is_reference: bool = False
    is_readonly: bool = False
    is_optional: bool = False
    location: Optional[SourceLocation] = None


@dataclass
class Variable:
    """Variable declaration."""
    name: str
    type: Optional[TypeReference] = None
    initial_value: Any = None
    is_constant: bool = False
    visibility: Optional[Visibility] = None
    modifiers: Optional[Modifiers] = None
    location: Optional[SourceLocation] = None


# Metadata that can be attached to any node
Metadata = Dict[str, Any]


# Common attributes for nodes
@dataclass
class NodeAttributes:
    """Common attributes for AST nodes."""
    kind: NodeKind
    location: Optional[SourceLocation] = None
    metadata: Optional[Metadata] = None
    parent: Optional[Any] = None  # Avoid circular ref
    
    def add_metadata(self, key: str, value: Any) -> None:
        """Add metadata to node."""
        if self.metadata is None:
            self.metadata = {}
        self.metadata[key] = value
    
    def get_metadata(self, key: str, default: Any = None) -> Any:
        """Get metadata value."""
        if self.metadata is None:
            return default
        return self.metadata.get(key, default)