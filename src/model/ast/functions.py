"""Function and procedure AST nodes for PowerBuilder and Pseudocode.

This module contains AST nodes for representing functions and procedures in both PowerBuilder
and pseudocode, including parameter handling, type checking, and scope management.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import TYPE_CHECKING

from src.model.types.base import PBNode, NodeKind

from .nodes.base import Expression, Statement
from .nodes.declarations import Type

if TYPE_CHECKING:
    from .nodes.base import Statement


logger = logging.getLogger(__name__)


# ─── Block Definition ─────────────────────────────────────────────────────────

@dataclass
class Block(Statement):
    """Block of statements."""
    
    statements: list[Statement] = field(default_factory=list)
    
    @property
    def kind(self) -> NodeKind:
        """Return the node kind."""
        return NodeKind.BLOCK
    
    def add_statement(self, stmt: Statement) -> None:
        """Add a statement to the block."""
        self.statements.append(stmt)
    
    def accept(self, visitor):
        """Accept a visitor."""
        return visitor.visit_block(self)


# ─── Parameter Definition ─────────────────────────────────────────────────────

@dataclass
class Parameter(PBNode):
    """Function/procedure parameter definition."""
    
    name: str
    param_type: Type | str | None = None  # Type or type name
    default_value: Expression | None = None
    is_reference: bool = False  # Pass by reference
    is_readonly: bool = False   # Readonly reference
    is_optional: bool = False   # Optional parameter
    
    @property
    def kind(self) -> NodeKind:
        """Return the node kind."""
        return NodeKind.PARAMETER
    
    def __post_init__(self) -> None:
        """Validate parameter definition."""
        if not self.name:
            raise ValueError("Parameter requires name")
        
        # If parameter has default value, it's optional
        if self.default_value is not None:
            self.is_optional = True
        
        # Readonly only makes sense for reference parameters
        if self.is_readonly and not self.is_reference:
            logger.warning(
                f"Parameter '{self.name}' marked as readonly but not passed by reference"
            )
    
    def get_type_name(self) -> str:
        """Get the type name as a string."""
        if isinstance(self.param_type, str):
            return self.param_type
        elif isinstance(self.param_type, Type):
            return self.param_type.name
        return "any"
    
    def accept(self, visitor):
        """Accept a visitor."""
        return visitor.visit_parameter(self)


# ─── Function Declaration ─────────────────────────────────────────────────────

@dataclass
class FunctionDeclaration(Statement):
    """Function declaration (forward declaration or interface)."""
    
    name: str
    return_type: Type | str | None = None
    parameters: list[Parameter] = field(default_factory=list)
    visibility: str = "public"  # public, private, protected
    is_static: bool = False
    is_external: bool = False
    library_name: str | None = None  # For external functions
    alias: str | None = None  # External function alias
    
    @property
    def kind(self) -> NodeKind:
        """Return the node kind."""
        return NodeKind.FUNCTION_DECLARATION
    
    def __post_init__(self) -> None:
        """Validate function declaration."""
        if not self.name:
            raise ValueError("FunctionDeclaration requires name")
        
        # External functions must have library name
        if self.is_external and not self.library_name:
            raise ValueError(
                f"External function '{self.name}' requires library_name"
            )
    
    def get_return_type_name(self) -> str:
        """Get the return type name as a string."""
        if self.return_type is None:
            return "void"
        elif isinstance(self.return_type, str):
            return self.return_type
        elif isinstance(self.return_type, Type):
            return self.return_type.name
        return "any"
    
    def accept(self, visitor):
        """Accept a visitor."""
        return visitor.visit_function_declaration(self)


# ─── Signature (for compatibility) ────────────────────────────────────────────

@dataclass
class Signature(PBNode):
    """Function/procedure signature."""
    
    name: str
    return_type: Type | str | None = None
    parameters: list[Parameter] = field(default_factory=list)
    
    @property
    def kind(self) -> NodeKind:
        """Return the node kind."""
        return NodeKind.UNKNOWN
    
    def __post_init__(self) -> None:
        """Validate signature."""
        if not self.name:
            raise ValueError("Signature requires name")


# ─── Function Definition ──────────────────────────────────────────────────────

@dataclass
class FunctionDefinition(Statement):
    """Function definition with implementation."""
    
    # Support both interfaces for compatibility
    signature: Signature | None = None
    body: Block | None = None
    
    # Direct attributes (alternative interface)
    name: str | None = None
    return_type: Type | str | None = None
    parameters: list[Parameter] = field(default_factory=list)
    visibility: str = "public"
    is_static: bool = False
    is_override: bool = False
    is_virtual: bool = False
    is_abstract: bool = False
    throws: list[str] = field(default_factory=list)  # Exception types
    
    @property
    def kind(self) -> NodeKind:
        """Return the node kind."""
        return NodeKind.FUNCTION_DECLARATION
    
    def __post_init__(self) -> None:
        """Validate function definition and sync signature."""
        # If signature is provided, sync its values to direct attributes
        if self.signature:
            if not self.name:
                self.name = self.signature.name
            if not self.return_type:
                self.return_type = self.signature.return_type
            if not self.parameters:
                self.parameters = self.signature.parameters
        
        # If direct attributes provided but no signature, create signature
        elif self.name:
            self.signature = Signature(
                name=self.name,
                return_type=self.return_type,
                parameters=self.parameters
            )
        
        # Validate
        if not self.name and not (self.signature and self.signature.name):
            raise ValueError("FunctionDefinition requires name")
        
        # Abstract functions cannot have body
        if self.is_abstract and self.body is not None:
            raise ValueError(
                f"Abstract function '{self.name}' cannot have implementation"
            )
        
        # Non-abstract functions must have body
        if not self.is_abstract and self.body is None:
            logger.warning(
                f"Function '{self.name or (self.signature.name if self.signature else 'unknown')}' has no implementation body"
            )
    
    def get_return_type_name(self) -> str:
        """Get the return type name as a string."""
        return_type = self.return_type or (self.signature.return_type if self.signature else None)
        if return_type is None:
            return "void"
        elif isinstance(return_type, str):
            return return_type
        elif isinstance(return_type, Type):
            return return_type.name
        return "any"
    
    def get_signature(self) -> str:
        """Get function signature for display."""
        params = self.parameters or (self.signature.parameters if self.signature else [])
        param_str = ", ".join(
            f"{p.name}: {p.get_type_name()}" for p in params
        )
        return_type = self.get_return_type_name()
        name = self.name or (self.signature.name if self.signature else "unknown")
        return f"{name}({param_str}) -> {return_type}"
    
    def accept(self, visitor):
        """Accept a visitor."""
        return visitor.visit_function_definition(self)


# ─── Procedure Declaration ────────────────────────────────────────────────────

@dataclass  
class ProcedureDeclaration(Statement):
    """Procedure declaration (no return value)."""
    
    name: str
    parameters: list[Parameter] = field(default_factory=list)
    visibility: str = "public"
    is_static: bool = False
    is_external: bool = False
    library_name: str | None = None
    alias: str | None = None
    
    @property
    def kind(self) -> NodeKind:
        """Return the node kind."""
        return NodeKind.PROCEDURE_DECLARATION
    
    def __post_init__(self) -> None:
        """Validate procedure declaration."""
        if not self.name:
            raise ValueError("ProcedureDeclaration requires name")
        
        if self.is_external and not self.library_name:
            raise ValueError(
                f"External procedure '{self.name}' requires library_name"
            )
    
    def accept(self, visitor):
        """Accept a visitor."""
        return visitor.visit_procedure_declaration(self)


# ─── Procedure Definition ─────────────────────────────────────────────────────

@dataclass
class ProcedureDefinition(Statement):
    """Procedure definition with implementation."""
    
    name: str
    parameters: list[Parameter] = field(default_factory=list)
    body: Block | None = None
    visibility: str = "public"
    is_static: bool = False
    is_override: bool = False
    is_virtual: bool = False
    is_abstract: bool = False
    throws: list[str] = field(default_factory=list)
    
    @property
    def kind(self) -> NodeKind:
        """Return the node kind."""
        return NodeKind.PROCEDURE_DECLARATION
    
    def __post_init__(self) -> None:
        """Validate procedure definition."""
        if not self.name:
            raise ValueError("ProcedureDefinition requires name")
        
        if self.is_abstract and self.body is not None:
            raise ValueError(
                f"Abstract procedure '{self.name}' cannot have implementation"
            )
        
        if not self.is_abstract and self.body is None:
            logger.warning(
                f"Procedure '{self.name}' has no implementation body"
            )
    
    def get_signature(self) -> str:
        """Get procedure signature for display."""
        params = ", ".join(
            f"{p.name}: {p.get_type_name()}" for p in self.parameters
        )
        return f"{self.name}({params})"
    
    def accept(self, visitor):
        """Accept a visitor."""
        return visitor.visit_procedure_definition(self)


# ─── Function Call Expression ─────────────────────────────────────────────────

@dataclass
class FunctionCall(Expression):
    """Function call expression."""
    
    function_name: str
    arguments: list[Expression] = field(default_factory=list)
    object_expr: Expression | None = None  # For method calls
    
    @property
    def kind(self) -> NodeKind:
        """Return the node kind."""
        return NodeKind.FUNCTION_CALL_EXPRESSION
    
    def __post_init__(self) -> None:
        """Validate function call."""
        if not self.function_name:
            raise ValueError("FunctionCall requires function_name")
    
    def is_method_call(self) -> bool:
        """Check if this is a method call."""
        return self.object_expr is not None
    
    def accept(self, visitor):
        """Accept a visitor."""
        return visitor.visit_function_call(self)


# ─── Procedure Call Statement ─────────────────────────────────────────────────

@dataclass
class ProcedureCall(Statement):
    """Procedure call statement."""
    
    procedure_name: str
    arguments: list[Expression] = field(default_factory=list)
    object_expr: Expression | None = None  # For method calls
    
    @property
    def kind(self) -> NodeKind:
        """Return the node kind."""
        return NodeKind.STATEMENT
    
    def __post_init__(self) -> None:
        """Validate procedure call."""
        if not self.procedure_name:
            raise ValueError("ProcedureCall requires procedure_name")
    
    def is_method_call(self) -> bool:
        """Check if this is a method call."""
        return self.object_expr is not None
    
    def accept(self, visitor):
        """Accept a visitor."""
        return visitor.visit_procedure_call(self)


# ─── Return Statement ─────────────────────────────────────────────────────────

@dataclass
class ReturnStatement(Statement):
    """Return statement."""
    
    return_value: Expression | None = None
    
    @property
    def kind(self) -> NodeKind:
        """Return the node kind."""
        return NodeKind.RETURN_STATEMENT
    
    def accept(self, visitor):
        """Accept a visitor."""
        return visitor.visit_return_statement(self)


# ─── Event Definition ─────────────────────────────────────────────────────────

@dataclass
class Event(Statement):
    """Event definition for PowerBuilder objects."""
    
    name: str
    parameters: list[Parameter] = field(default_factory=list)
    body: Block | None = None
    return_type: Type | str | None = None  # Some events can return values
    visibility: str = "public"
    is_override: bool = False
    is_extended: bool = False  # Extended from parent
    
    @property
    def kind(self) -> NodeKind:
        """Return the node kind."""
        return NodeKind.EVENT_DECLARATION
    
    def __post_init__(self) -> None:
        """Validate event definition."""
        if not self.name:
            raise ValueError("Event requires name")
    
    def get_signature(self) -> str:
        """Get event signature for display."""
        params = ", ".join(
            f"{p.name}: {p.get_type_name()}" for p in self.parameters
        )
        return f"{self.name}({params})"
    
    def accept(self, visitor):
        """Accept a visitor."""
        return visitor.visit_event(self)


# ─── Event Trigger ────────────────────────────────────────────────────────────

@dataclass  
class EventTrigger(Statement):
    """Trigger an event on an object."""
    
    event_name: str
    object_expr: Expression | None = None  # Object to trigger event on
    arguments: list[Expression] = field(default_factory=list)
    is_post: bool = False  # POST vs immediate trigger
    
    @property
    def kind(self) -> NodeKind:
        """Return the node kind."""
        return NodeKind.EVENT_TRIGGER
    
    def __post_init__(self) -> None:
        """Validate event trigger."""
        if not self.event_name:
            raise ValueError("EventTrigger requires event_name")
    
    def accept(self, visitor):
        """Accept a visitor."""
        return visitor.visit_event_trigger(self)


# ─── Lambda/Anonymous Function ────────────────────────────────────────────────

@dataclass
class LambdaExpression(Expression):
    """Lambda/anonymous function expression."""
    
    parameters: list[Parameter] = field(default_factory=list)
    body: Expression | Block | None = None
    return_type: Type | str | None = None
    
    @property
    def kind(self) -> NodeKind:
        """Return the node kind."""
        return NodeKind.EXPRESSION
    
    def __post_init__(self) -> None:
        """Validate lambda expression."""
        if self.body is None:
            raise ValueError("LambdaExpression requires body")
    
    def accept(self, visitor):
        """Accept a visitor."""
        return visitor.visit_lambda_expression(self)


# ─── Function Signature (for type checking) ──────────────────────────────────

@dataclass
class FunctionSignature(PBNode):
    """Function signature for type checking and overload resolution."""
    
    name: str
    return_type: Type | str | None
    parameter_types: list[Type | str] = field(default_factory=list)
    parameter_names: list[str] = field(default_factory=list)
    is_variadic: bool = False  # Accepts variable number of arguments
    
    @property
    def kind(self) -> NodeKind:
        """Return the node kind."""
        return NodeKind.UNKNOWN
    
    def matches(self, other: FunctionSignature) -> bool:
        """Check if signatures match for overloading."""
        if self.name != other.name:
            return False
        
        # Check parameter count (considering variadic)
        if not self.is_variadic and not other.is_variadic:
            if len(self.parameter_types) != len(other.parameter_types):
                return False
        
        # Check parameter types
        min_params = min(len(self.parameter_types), len(other.parameter_types))
        for i in range(min_params):
            if not self._types_compatible(
                self.parameter_types[i], 
                other.parameter_types[i]
            ):
                return False
        
        return True
    
    def _types_compatible(self, t1: Type | str, t2: Type | str) -> bool:
        """Check if two types are compatible."""
        # Convert to strings for comparison
        type1_name = t1 if isinstance(t1, str) else t1.name
        type2_name = t2 if isinstance(t2, str) else t2.name
        
        # Exact match
        if type1_name.lower() == type2_name.lower():
            return True
        
        # Numeric compatibility
        numeric_types = {"integer", "long", "decimal", "double", "real"}
        if type1_name.lower() in numeric_types and type2_name.lower() in numeric_types:
            return True
        
        # Any type matches everything
        if type1_name.lower() == "any" or type2_name.lower() == "any":
            return True
        
        return False
    
    def is_compatible_with_call(self, arg_types: list[Type | str]) -> bool:
        """Check if a call with given argument types is compatible."""
        # Check minimum parameter count
        required_params = sum(
            1 for i, param_type in enumerate(self.parameter_types)
            if i >= len(self.parameter_names) or 
            not any(p.is_optional for p in self.parameter_types 
                   if hasattr(p, 'is_optional'))
        )
        
        if len(arg_types) < required_params:
            return False
        
        # Check if too many arguments (and not variadic)
        if not self.is_variadic and len(arg_types) > len(self.parameter_types):
            return False
        
        # Check type compatibility for provided arguments
        for i, arg_type in enumerate(arg_types):
            if i < len(self.parameter_types):
                if not self._types_compatible(arg_type, self.parameter_types[i]):
                    return False
        
        return True


# Method is an alias for FunctionDefinition (for compatibility)
Method = FunctionDefinition


# Export all function-related nodes
__all__ = [
    "Block",
    "Parameter", 
    "Signature",
    "FunctionDeclaration",
    "FunctionDefinition",
    "ProcedureDeclaration", 
    "ProcedureDefinition",
    "FunctionCall",
    "ProcedureCall",
    "ReturnStatement",
    "Event",
    "EventTrigger",
    "LambdaExpression",
    "FunctionSignature",
    "Method",  # Alias for FunctionDefinition
]
