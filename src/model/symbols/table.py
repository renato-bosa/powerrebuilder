"""Enhanced symbol table management for PowerBuilder AST.

This module provides comprehensive symbol table functionality that integrates
with the type inference system and supports PowerBuilder-specific concepts.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from enum import Enum, auto
from typing import TYPE_CHECKING, Any, Dict, List, Optional, Set, Tuple

from src.model.types.inference import TypeContext, TypeInfo

if TYPE_CHECKING:
    pass

logger = logging.getLogger(__name__)


class SymbolKind(Enum):
    """Kind of symbol in the symbol table."""
    
    VARIABLE = auto()
    FUNCTION = auto()
    PROCEDURE = auto()
    TYPE = auto()
    CLASS = auto()
    STRUCTURE = auto()
    CONSTANT = auto()
    PROPERTY = auto()
    EVENT = auto()
    EXTERNAL_FUNCTION = auto()


class Visibility(Enum):
    """PowerBuilder visibility levels."""
    
    PUBLIC = "public"
    PRIVATE = "private"
    PROTECTED = "protected"
    GLOBAL = "global"
    LOCAL = "local"
    
    @classmethod
    def from_string(cls, value: str) -> "Visibility":
        """Create visibility from string."""
        value_lower = value.lower()
        for vis in cls:
            if vis.value == value_lower:
                return vis
        return cls.PUBLIC  # Default to public


@dataclass
class Symbol:
    """A symbol in the symbol table."""
    
    name: str
    kind: SymbolKind
    type_info: TypeInfo
    visibility: Visibility = Visibility.PUBLIC
    definition: Any = None  # The AST node or entity that defines this symbol
    scope_level: int = 0
    is_readonly: bool = False
    is_static: bool = False
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def __hash__(self) -> int:
        """Make Symbol hashable."""
        return hash((self.name, self.kind, self.scope_level))
    
    def __eq__(self, other: object) -> bool:
        """Compare symbols."""
        if not isinstance(other, Symbol):
            return False
        return (
            self.name == other.name and
            self.kind == other.kind and
            self.scope_level == other.scope_level
        )


@dataclass
class Scope:
    """A scope containing symbols."""
    
    name: str
    level: int
    parent: Optional["Scope"] = None
    symbols: Dict[str, Symbol] = field(default_factory=dict)
    children: List["Scope"] = field(default_factory=list)
    scope_type: str = "block"  # block, function, class, global
    owner: Any = None  # The AST node that owns this scope
    
    def add_symbol(self, symbol: Symbol) -> None:
        """Add a symbol to this scope."""
        if symbol.name in self.symbols:
            logger.warning(
                f"Symbol '{symbol.name}' already exists in scope '{self.name}'"
            )
        symbol.scope_level = self.level
        self.symbols[symbol.name] = symbol
    
    def lookup_local(self, name: str) -> Optional[Symbol]:
        """Look up a symbol in this scope only."""
        return self.symbols.get(name)
    
    def lookup(self, name: str) -> Optional[Symbol]:
        """Look up a symbol in this scope or parent scopes."""
        symbol = self.lookup_local(name)
        if symbol:
            return symbol
        if self.parent:
            return self.parent.lookup(name)
        return None


class SymbolTable:
    """Enhanced symbol table for PowerBuilder code."""
    
    def __init__(self, type_context: Optional[TypeContext] = None) -> None:
        """Initialize the symbol table.
        
        Args:
            type_context: Optional type context for type inference integration
        """
        self.type_context = type_context or TypeContext()
        self.global_scope = Scope("global", 0)
        self.current_scope = self.global_scope
        self.all_scopes: List[Scope] = [self.global_scope]
        self._scope_stack: List[Scope] = [self.global_scope]
        
        # Caches for performance
        self._symbol_cache: Dict[Tuple[str, int], Optional[Symbol]] = {}
        self._type_cache: Dict[str, TypeInfo] = {}
        
        # PowerBuilder-specific tracking
        self._instance_variables: Set[str] = set()
        self._shared_variables: Set[str] = set()
        self._global_variables: Set[str] = set()
        
        # Initialize built-in types
        self._initialize_builtin_types()
    
    def _initialize_builtin_types(self) -> None:
        """Initialize PowerBuilder built-in types."""
        builtin_types = [
            # Numeric types
            ("integer", "integer", False),
            ("long", "long", False),
            ("decimal", "decimal", False),
            ("real", "real", False),
            ("double", "double", False),
            ("byte", "byte", False),
            ("uint", "uint", False),
            ("ulong", "ulong", False),
            
            # String types
            ("string", "string", True),
            ("char", "char", False),
            
            # Boolean
            ("boolean", "boolean", False),
            
            # Date/Time types
            ("date", "date", True),
            ("time", "time", True),
            ("datetime", "datetime", True),
            
            # Binary
            ("blob", "blob", True),
            
            # Special types
            ("any", "any", True),
            ("powerobject", "powerobject", True),
        ]
        
        for type_name, base_type, is_nullable in builtin_types:
            type_info = TypeInfo(
                type_name=base_type,
                is_nullable=is_nullable,
                confidence=1.0
            )
            self._type_cache[type_name] = type_info
            
            symbol = Symbol(
                name=type_name,
                kind=SymbolKind.TYPE,
                type_info=type_info,
                visibility=Visibility.GLOBAL,
                is_readonly=True
            )
            self.global_scope.add_symbol(symbol)
    
    def enter_scope(self, name: str, scope_type: str = "block", 
                    owner: Any = None) -> Scope:
        """Enter a new scope.
        
        Args:
            name: Name of the scope
            scope_type: Type of scope (block, function, class, etc.)
            owner: The AST node that owns this scope
            
        Returns:
            The new scope
        """
        new_scope = Scope(
            name=name,
            level=self.current_scope.level + 1,
            parent=self.current_scope,
            scope_type=scope_type,
            owner=owner
        )
        
        self.current_scope.children.append(new_scope)
        self.current_scope = new_scope
        self._scope_stack.append(new_scope)
        self.all_scopes.append(new_scope)
        
        # Clear caches when scope changes
        self._symbol_cache.clear()
        
        logger.debug(f"Entered scope '{name}' at level {new_scope.level}")
        return new_scope
    
    def exit_scope(self) -> Optional[Scope]:
        """Exit the current scope.
        
        Returns:
            The scope that was exited, or None if at global scope
        """
        if len(self._scope_stack) <= 1:
            logger.warning("Cannot exit global scope")
            return None
        
        exited_scope = self._scope_stack.pop()
        self.current_scope = self._scope_stack[-1]
        
        # Clear caches when scope changes
        self._symbol_cache.clear()
        
        logger.debug(f"Exited scope '{exited_scope.name}'")
        return exited_scope
    
    def declare_variable(self, name: str, type_info: TypeInfo,
                        visibility: Visibility = Visibility.LOCAL,
                        is_readonly: bool = False,
                        is_static: bool = False,
                        definition: Any = None) -> Symbol:
        """Declare a variable in the current scope.
        
        Args:
            name: Variable name
            type_info: Type information
            visibility: Variable visibility
            is_readonly: Whether the variable is read-only
            is_static: Whether the variable is static
            definition: The AST node defining this variable
            
        Returns:
            The created symbol
        """
        symbol = Symbol(
            name=name,
            kind=SymbolKind.VARIABLE,
            type_info=type_info,
            visibility=visibility,
            is_readonly=is_readonly,
            is_static=is_static,
            definition=definition
        )
        
        self.current_scope.add_symbol(symbol)
        
        # Track special variable types
        if visibility == Visibility.GLOBAL:
            self._global_variables.add(name)
        elif is_static:
            self._shared_variables.add(name)
        elif self.current_scope.scope_type == "class":
            self._instance_variables.add(name)
        
        return symbol
    
    def declare_function(self, name: str, return_type: TypeInfo,
                        parameters: List[Tuple[str, TypeInfo]],
                        visibility: Visibility = Visibility.PUBLIC,
                        is_static: bool = False,
                        definition: Any = None) -> Symbol:
        """Declare a function in the current scope.
        
        Args:
            name: Function name
            return_type: Return type information
            parameters: List of (parameter_name, type_info) tuples
            visibility: Function visibility
            is_static: Whether the function is static
            definition: The AST node defining this function
            
        Returns:
            The created symbol
        """
        # Create a function type with parameter info
        func_type = TypeInfo(
            type_name="function",
            is_nullable=False,
            metadata={
                "return_type": return_type,
                "parameters": parameters
            }
        )
        
        symbol = Symbol(
            name=name,
            kind=SymbolKind.FUNCTION,
            type_info=func_type,
            visibility=visibility,
            is_static=is_static,
            definition=definition
        )
        
        self.current_scope.add_symbol(symbol)
        return symbol
    
    def declare_type(self, name: str, type_info: TypeInfo,
                    visibility: Visibility = Visibility.PUBLIC,
                    definition: Any = None) -> Symbol:
        """Declare a custom type.
        
        Args:
            name: Type name
            type_info: Type information
            visibility: Type visibility
            definition: The AST node defining this type
            
        Returns:
            The created symbol
        """
        symbol = Symbol(
            name=name,
            kind=SymbolKind.TYPE,
            type_info=type_info,
            visibility=visibility,
            is_readonly=True,
            definition=definition
        )
        
        self.current_scope.add_symbol(symbol)
        self._type_cache[name] = type_info
        return symbol
    
    def lookup(self, name: str, kind: Optional[SymbolKind] = None) -> Optional[Symbol]:
        """Look up a symbol by name.
        
        Args:
            name: Symbol name
            kind: Optional kind filter
            
        Returns:
            The symbol if found, None otherwise
        """
        # Check cache first
        cache_key = (name, self.current_scope.level)
        if cache_key in self._symbol_cache:
            symbol = self._symbol_cache[cache_key]
            if symbol and (kind is None or symbol.kind == kind):
                return symbol
        
        # Perform lookup
        symbol = self.current_scope.lookup(name)
        
        # Filter by kind if specified
        if symbol and kind and symbol.kind != kind:
            symbol = None
        
        # Cache result
        self._symbol_cache[cache_key] = symbol
        
        return symbol
    
    def lookup_type(self, type_name: str) -> Optional[TypeInfo]:
        """Look up type information by name.
        
        Args:
            type_name: Type name
            
        Returns:
            Type information if found
        """
        # Check type cache first
        if type_name in self._type_cache:
            return self._type_cache[type_name]
        
        # Look up type symbol
        symbol = self.lookup(type_name, SymbolKind.TYPE)
        if symbol:
            return symbol.type_info
        
        return None
    
    def get_visible_symbols(self, visibility_filter: Optional[Visibility] = None,
                           kind_filter: Optional[SymbolKind] = None) -> List[Symbol]:
        """Get all visible symbols from current scope.
        
        Args:
            visibility_filter: Optional visibility filter
            kind_filter: Optional kind filter
            
        Returns:
            List of visible symbols
        """
        visible = []
        scope = self.current_scope
        
        while scope:
            for symbol in scope.symbols.values():
                # Check visibility
                if visibility_filter and symbol.visibility != visibility_filter:
                    continue
                
                # Check kind
                if kind_filter and symbol.kind != kind_filter:
                    continue
                
                # Check PowerBuilder visibility rules
                if self._is_visible(symbol, scope):
                    visible.append(symbol)
            
            scope = scope.parent
        
        return visible
    
    def _is_visible(self, symbol: Symbol, from_scope: Scope) -> bool:
        """Check if a symbol is visible from a given scope.
        
        Implements PowerBuilder visibility rules:
        - PUBLIC: Visible everywhere
        - PRIVATE: Visible only in defining scope
        - PROTECTED: Visible in defining scope and derived classes
        - GLOBAL: Visible everywhere
        - LOCAL: Visible only in defining scope
        """
        if symbol.visibility in (Visibility.PUBLIC, Visibility.GLOBAL):
            return True
        
        if symbol.visibility in (Visibility.PRIVATE, Visibility.LOCAL):
            # Only visible in the exact scope where defined
            return symbol.scope_level == from_scope.level
        
        if symbol.visibility == Visibility.PROTECTED:
            # Check if we're in the same class or a derived class
            # This would require inheritance tracking
            # For now, treat as visible in same scope and children
            return symbol.scope_level <= from_scope.level
        
        return False
    
    def resolve_type(self, type_ref: Any) -> Optional[TypeInfo]:
        """Resolve a type reference to type information.
        
        Args:
            type_ref: Type reference (string, Type node, etc.)
            
        Returns:
            Resolved type information
        """
        if isinstance(type_ref, str):
            return self.lookup_type(type_ref)
        
        if hasattr(type_ref, "name"):
            return self.lookup_type(type_ref.name)
        
        return None
    
    def export(self) -> Dict[str, Any]:
        """Export the symbol table for serialization or debugging.
        
        Returns:
            Dictionary representation of the symbol table
        """
        def export_scope(scope: Scope) -> Dict[str, Any]:
            return {
                "name": scope.name,
                "level": scope.level,
                "type": scope.scope_type,
                "symbols": {
                    name: {
                        "kind": symbol.kind.name,
                        "type": str(symbol.type_info),
                        "visibility": symbol.visibility.value,
                        "readonly": symbol.is_readonly,
                        "static": symbol.is_static
                    }
                    for name, symbol in scope.symbols.items()
                },
                "children": [export_scope(child) for child in scope.children]
            }
        
        return {
            "global_scope": export_scope(self.global_scope),
            "instance_variables": list(self._instance_variables),
            "shared_variables": list(self._shared_variables),
            "global_variables": list(self._global_variables),
            "type_count": len(self._type_cache),
            "scope_count": len(self.all_scopes)
        }
    
    def clear(self) -> None:
        """Clear the symbol table."""
        self.global_scope = Scope("global", 0)
        self.current_scope = self.global_scope
        self.all_scopes = [self.global_scope]
        self._scope_stack = [self.global_scope]
        self._symbol_cache.clear()
        self._type_cache.clear()
        self._instance_variables.clear()
        self._shared_variables.clear()
        self._global_variables.clear()
        
        # Re-initialize built-in types
        self._initialize_builtin_types()
