"""Enhanced symbol table management for PowerBuilder AST.

This module provides comprehensive symbol table functionality that integrates
with the type inference system and supports PowerBuilder-specific concepts.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from enum import Enum, auto
from typing import TYPE_CHECKING, Any

from src.model.types.inference import TypeContext, TypeInfo

if TYPE_CHECKING:
    pass

logger = logging.getLogger(__name__)


class SymbolKind(Enum):
    """Types of symbols in PowerBuilder."""

    VARIABLE = auto()
    CONSTANT = auto()
    FUNCTION = auto()
    PROCEDURE = auto()
    EVENT = auto()
    PROPERTY = auto()
    CLASS = auto()
    INTERFACE = auto()
    STRUCTURE = auto()
    ENUMERATION = auto()
    USER_OBJECT = auto()  # Windows, DataWindows, etc.
    PARAMETER = auto()
    LABEL = auto()


class SymbolVisibility(Enum):
    """Symbol visibility/access modifiers."""

    PUBLIC = auto()
    PRIVATE = auto()
    PROTECTED = auto()
    GLOBAL = auto()
    SHARED = auto()     # PowerBuilder shared variables
    INSTANCE = auto()   # Instance variables
    LOCAL = auto()      # Local to function/event


@dataclass
class SymbolLocation:
    """Location information for a symbol definition."""

    file_path: str | None = None
    object_name: str | None = None  # e.g., w_main, n_cst_service
    script_name: str | None = None  # e.g., clicked, constructor
    line: int = 0
    column: int = 0
    end_line: int = 0
    end_column: int = 0


@dataclass
class SymbolInfo:
    """Rich metadata for a symbol."""

    name: str
    kind: SymbolKind
    visibility: SymbolVisibility = SymbolVisibility.LOCAL
    type_info: TypeInfo | None = None
    location: SymbolLocation | None = None
    documentation: str | None = None
    is_forward_declaration: bool = False
    is_external: bool = False
    is_system: bool = False
    decorators: list[str] = field(default_factory=list)
    attributes: dict[str, Any] = field(default_factory=dict)

    # For functions/procedures/events
    parameters: list[SymbolInfo] = field(default_factory=list)
    return_type: TypeInfo | None = None

    # For classes/user objects
    ancestor: str | None = None
    implements: list[str] = field(default_factory=list)

    # For variables
    initial_value: Any | None = None
    is_readonly: bool = False
    is_static: bool = False

    def __str__(self) -> str:




        """String representation of symbol."""
        visibility = self.visibility.name.lower()
        kind = self.kind.name.lower()
        type_str = str(self.type_info) if self.type_info else "unknown"
        return f"{visibility} {kind} {self.name}: {type_str}"


class SymbolScope:
    """Enhanced scope with symbol management and PowerBuilder semantics."""

    def __init__(self, name: str, kind: str = "block", parent: "SymbolScope" | None = None) -> None:


        """Initialize a scope.

        Args:
            name: Scope name (e.g., "global", "w_main", "clicked")
            kind: Scope kind (e.g., "global", "class", "function", "block")
            parent: Parent scope for hierarchical lookup
        """
        self.name = name
        self.kind = kind
        self.parent = parent
        self.symbols: dict[str, SymbolInfo] = {}
        self.children: list[SymbolScope] = []
        self.type_context = TypeContext(parent=parent.type_context if parent else None)

        # Track imports and using statements
        self.imports: set[str] = set()
        self.using_namespaces: set[str] = set()

        if parent:
            parent.children.append(self)

    def add_symbol(self, symbol: SymbolInfo) -> None:




        """Add a symbol to this scope."""
        if symbol.name in self.symbols:
            # Check if it's a forward declaration being resolved
            existing = self.symbols[symbol.name]
            if existing.is_forward_declaration and not symbol.is_forward_declaration:
                # Replace forward declaration with actual definition
                self.symbols[symbol.name] = symbol
                logger.debug("Resolved forward declaration: %s", symbol.name)
            else:
                logger.warning("Symbol '%s' redefined in scope '%s'", symbol.name, self.name)

        self.symbols[symbol.name] = symbol

        # Update type context if applicable
        if symbol.type_info:
            if symbol.kind in [SymbolKind.VARIABLE, SymbolKind.PARAMETER, SymbolKind.CONSTANT]:
                self.type_context.set_variable_type(symbol.name, symbol.type_info)

        # For functions/procedures/events, register return type
        if symbol.kind in [SymbolKind.FUNCTION, SymbolKind.PROCEDURE, SymbolKind.EVENT]:
            if symbol.return_type:
                self.type_context.functions[symbol.name] = symbol.return_type

    def lookup_symbol(self, name: str, kind: SymbolKind | None = None) -> SymbolInfo | None:




        """Look up a symbol in this scope or parent scopes.

        Args:
            name: Symbol name to look up
            kind: Optional kind filter

        Returns:
            SymbolInfo if found, None otherwise
        """
        # Check current scope
        if name in self.symbols:
            symbol = self.symbols[name]
            if kind is None or symbol.kind == kind:
                return symbol

        # Check parent scope based on visibility rules
        if self.parent:
            parent_symbol = self.parent.lookup_symbol(name, kind)
            if parent_symbol and self._is_visible_from_parent(parent_symbol):
                return parent_symbol

        return None

    def _is_visible_from_parent(self, symbol: SymbolInfo) -> bool:




        """Check if a symbol from parent scope is visible in this scope."""
        # Within the same class/object, all members are visible
        if self._is_same_object_scope():
            return True

        # PowerBuilder visibility rules for cross-class access
        if symbol.visibility in [SymbolVisibility.PUBLIC, SymbolVisibility.GLOBAL]:
            return True
        if symbol.visibility == SymbolVisibility.PROTECTED and self.kind == "class":
            # Protected members visible in derived classes
            return True
        if symbol.visibility == SymbolVisibility.SHARED:
            # Shared variables visible within the same object
            return self._is_same_object_scope()
        return False

    def _is_same_object_scope(self) -> bool:




        """Check if this scope is within the same object as parent."""
        current = self
        while current and current.kind not in ["class", "global"]:
            current = current.parent

        parent_obj = self.parent
        while parent_obj and parent_obj.kind not in ["class", "global"]:
            parent_obj = parent_obj.parent

        return current and parent_obj and current.name == parent_obj.name

    def get_all_symbols(self, kind: SymbolKind | None = None) -> dict[str, SymbolInfo]:




        """Get all symbols visible in this scope.

        Args:
            kind: Optional filter by symbol kind

        Returns:
            Dictionary of visible symbols
        """
        result = {}

        # Add parent symbols first (so they can be overridden)
        if self.parent:
            parent_symbols = self.parent.get_all_symbols(kind)
            for name, symbol in parent_symbols.items():
                if self._is_visible_from_parent(symbol):
                    result[name] = symbol

        # Add local symbols (may override parent symbols)
        for name, symbol in self.symbols.items():
            if kind is None or symbol.kind == kind:
                result[name] = symbol

        return result

    def create_child_scope(self, name: str, kind: str = "block") -> "SymbolScope":




        """Create a child scope."""
        return SymbolScope(name, kind, parent=self)


class SymbolTable:
    """Main symbol table managing all scopes and symbols."""

    def __init__(self) -> None:




        """Initialize symbol table with global scope."""
        self.global_scope = SymbolScope("global", kind="global")
        self.current_scope = self.global_scope
        self.forward_declarations: list[SymbolInfo] = []
        self.unresolved_references: list[tuple[str, SymbolLocation]] = []

        # Cache for quick lookups
        self._symbol_cache: dict[str, SymbolInfo] = {}
        self._scope_stack: list[SymbolScope] = [self.global_scope]

        # Initialize built-in symbols
        self._init_builtin_symbols()

    def _init_builtin_symbols(self) -> None:




        """Initialize built-in PowerBuilder symbols."""
        # Built-in types
        builtin_types = [
            "integer", "long", "decimal", "real", "double", "boolean", "char", "string", "blob", "date", "time", "datetime", "any", "powerobject",
        ]

        for type_name in builtin_types:
            self.global_scope.add_symbol(SymbolInfo(
                name=type_name, kind=SymbolKind.CLASS, visibility=SymbolVisibility.GLOBAL, is_system=True, type_info=TypeInfo(type_name, is_nullable=False),
            ))

        # Built-in constants
        self.global_scope.add_symbol(SymbolInfo(
            name="NULL", kind=SymbolKind.CONSTANT, visibility=SymbolVisibility.GLOBAL, is_system=True, type_info=TypeInfo("null", is_nullable=True),
        ))

        self.global_scope.add_symbol(SymbolInfo(
            name="TRUE", kind=SymbolKind.CONSTANT, visibility=SymbolVisibility.GLOBAL, is_system=True, type_info=TypeInfo("boolean", is_nullable=False), initial_value=True,
        ))

        self.global_scope.add_symbol(SymbolInfo(
            name="FALSE", kind=SymbolKind.CONSTANT, visibility=SymbolVisibility.GLOBAL, is_system=True, type_info=TypeInfo("boolean", is_nullable=False), initial_value=False,
        ))

    def enter_scope(self, name: str, kind: str = "block") -> SymbolScope:




        """Enter a new scope."""
        new_scope = self.current_scope.create_child_scope(name, kind)
        self.current_scope = new_scope
        self._scope_stack.append(new_scope)
        self._symbol_cache.clear()  # Invalidate cache
        return new_scope

    def exit_scope(self) -> SymbolScope | None:




        """Exit current scope and return to parent."""
        if len(self._scope_stack) > 1:
            self._scope_stack.pop()
            old_scope = self.current_scope
            self.current_scope = self._scope_stack[-1]
            self._symbol_cache.clear()  # Invalidate cache
            return old_scope
        return None

    def add_symbol(self, symbol: SymbolInfo) -> None:




        """Add a symbol to the current scope."""
        self.current_scope.add_symbol(symbol)
        self._symbol_cache.clear()  # Invalidate cache

        if symbol.is_forward_declaration:
            self.forward_declarations.append(symbol)

    def lookup_symbol(self, name: str, kind: SymbolKind | None = None) -> SymbolInfo | None:




        """Look up a symbol starting from current scope.

        Args:
            name: Symbol name
            kind: Optional kind filter

        Returns:
            SymbolInfo if found, None otherwise
        """
        # Check cache first
        cache_key = f"{name}:{kind.name if kind else "any"}"
        if cache_key in self._symbol_cache:
            return self._symbol_cache[cache_key]

        # Look up in current scope
        symbol = self.current_scope.lookup_symbol(name, kind)
        if symbol:
            self._symbol_cache[cache_key] = symbol

        return symbol

    def declare_variable(self, name: str, type_name: str, visibility: SymbolVisibility = SymbolVisibility.LOCAL, location: SymbolLocation | None = None, **kwargs) -> SymbolInfo:




        """Declare a variable in current scope."""
        type_info = TypeInfo(
            type_name, is_array=kwargs.get("is_array", False), array_dimensions=kwargs.get("array_dimensions", 0),
        )

        symbol = SymbolInfo(
            name=name, kind=SymbolKind.VARIABLE, visibility=visibility, type_info=type_info, location=location, is_readonly=kwargs.get("is_readonly", False), is_static=kwargs.get("is_static", False), initial_value=kwargs.get("initial_value"),
        )

        self.add_symbol(symbol)
        return symbol

    def declare_function(self, name: str, return_type: str | None = None, parameters: list[tuple[str, str | None]] = None, visibility: SymbolVisibility = SymbolVisibility.PUBLIC, location: SymbolLocation | None = None, **kwargs) -> SymbolInfo:




        """Declare a function in current scope."""
        # Create parameter symbols
        param_symbols = []
        if parameters:
            for param_name, param_type in parameters:
                param_symbols.append(SymbolInfo(
                    name=param_name, kind=SymbolKind.PARAMETER, type_info=TypeInfo(param_type), visibility=SymbolVisibility.LOCAL,
                ))

        symbol = SymbolInfo(
            name=name, kind=SymbolKind.FUNCTION, visibility=visibility, return_type=TypeInfo(return_type) if return_type else None, parameters=param_symbols, location=location, is_forward_declaration=kwargs.get("is_forward", False), is_external=kwargs.get("is_external", False),
        )

        self.add_symbol(symbol)
        return symbol

    def declare_class(self, name: str, ancestor: str | None = None, visibility: SymbolVisibility = SymbolVisibility.PUBLIC, location: SymbolLocation | None = None, **kwargs) -> SymbolInfo:




        """Declare a class/user object in current scope."""
        symbol = SymbolInfo(
            name=name, kind=SymbolKind.CLASS if not kwargs.get("is_user_object") else SymbolKind.USER_OBJECT, visibility=visibility, type_info=TypeInfo(name, is_nullable=True), location=location, ancestor=ancestor, implements=kwargs.get("implements", []),
        )

        self.add_symbol(symbol)
        return symbol

    def resolve_forward_declarations(self) -> None:




        """Attempt to resolve forward declarations."""
        unresolved = []

        for forward_decl in self.forward_declarations:
            # Look for actual definition
            actual = self.lookup_symbol(forward_decl.name, forward_decl.kind)
            if actual and not actual.is_forward_declaration:
                logger.info("Resolved forward declaration: %s", forward_decl.name)
            else:
                unresolved.append(forward_decl)

        self.forward_declarations = unresolved

        if unresolved:
            logger.warning("%s forward declarations remain unresolved", len(unresolved))

    def get_all_symbols(self, kind: SymbolKind | None = None) -> dict[str, SymbolInfo]:




        """Get all symbols visible from current scope."""
        return self.current_scope.get_all_symbols(kind)

    def get_scope_path(self) -> list[str]:




        """Get the current scope path."""
        return [scope.name for scope in self._scope_stack]

    def find_symbols_by_type(self, type_name: str, kind_filter: SymbolKind | None = None) -> list[SymbolInfo]:




        """Find all symbols of a given type.

        Args:
            type_name: The type to search for
            kind_filter: Optional filter by symbol kind (e.g., only variables)

        Returns:
            List of symbols matching the type
        """
        result = []

        def search_scope(scope: SymbolScope) -> None:


            for symbol in scope.symbols.values():
                if symbol.type_info and symbol.type_info.type_name == type_name:
                    if kind_filter is None or symbol.kind == kind_filter:
                        result.append(symbol)
            for child in scope.children:
                search_scope(child)

        search_scope(self.global_scope)
        return result

    def get_undefined_references(self) -> list[tuple[str, SymbolLocation]]:




        """Get list of undefined symbol references."""
        return self.unresolved_references

    def clear(self) -> None:




        """Clear the symbol table."""
        self.global_scope = SymbolScope("global", kind="global")
        self.current_scope = self.global_scope
        self._scope_stack = [self.global_scope]
        self.forward_declarations.clear()
        self.unresolved_references.clear()
        self._symbol_cache.clear()
        self._init_builtin_symbols()
