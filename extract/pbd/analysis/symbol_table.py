"""Defines structures for managing symbols, scopes, and a symbol table
for PowerBuilder object analysis.
"""

from dataclasses import dataclass, field
from enum import Enum, auto
from typing import Optional


class SymbolType(Enum):
    VARIABLE = auto()
    FUNCTION = auto()
    EVENT = auto()
    USER_OBJECT = auto()  # NVOs, Windows, Menus, DataWindows etc.
    # Add more types as needed: Constant, Parameter, Label, etc.


class SymbolScope(Enum):
    GLOBAL = auto()
    SHARED = auto()  # Shared variables within an object
    INSTANCE = auto()  # Instance variables of an object
    LOCAL = auto()  # Local to a script (function/event)
    # We might need more granular scopes, e.g., for object types themselves


@dataclass
class DefinitionLocation:
    """Where a symbol is defined."""

    file_path: str | None = None  # PBD/PBL file name
    object_name: str | None = None  # e.g., w_main, n_cst_filesrv
    script_name: str | None = None  # e.g., of_process, cb_clicked_event
    line_number: int | None = None
    # Add other relevant info like column, offset, etc.


@dataclass
class Symbol:
    """Represents a single symbol in the codebase."""

    name: str
    symbol_type: SymbolType
    scope: SymbolScope
    data_type: str | None = None  # e.g., "integer", "string", "n_cst_myobject"
    definition_location: DefinitionLocation | None = None
    # For USER_OBJECT type symbols:
    ancestor: str | None = None  # e.g., "n_base_service", "window"
    # For FUNCTION/EVENT type symbols:
    parameters: list["Symbol"] = field(default_factory=list)  # Name, type of params
    return_type: str | None = None
    # For forward references:
    is_forward_reference: bool = False
    # Other attributes like access modifiers (public, private, protected) can be added


@dataclass
class ScopeNode:
    """Represents a node in the scope tree. Can hold symbols and child scopes."""

    name: str  # e.g., "global", "w_main", "w_main.cb_1.clicked"
    scope_type: SymbolScope
    parent_scope: Optional["ScopeNode"] = None
    symbols: dict[str, Symbol] = field(default_factory=dict)
    child_scopes: dict[str, "ScopeNode"] = field(default_factory=dict)

    def add_symbol(self, symbol: Symbol) -> None:
        if symbol.name in self.symbols:
            # Handle redefinition or shadowing - for now, simple overwrite with warning
            # In a real system, this would depend on language rules
            # logger.warning("Symbol '%s' redefined in scope '%s'.", symbol.name, self.name)
            pass  # Placeholder for logging/warning
        self.symbols[symbol.name] = symbol

    def lookup_symbol(self, name: str, recursive: bool = True) -> Symbol | None:
        symbol = self.symbols.get(name)
        if symbol:
            return symbol
        if recursive and self.parent_scope:
            return self.parent_scope.lookup_symbol(name, recursive=True)
        return None

    def get_or_create_child_scope(
        self, name: str, scope_type: SymbolScope
    ) -> "ScopeNode":
        if name not in self.child_scopes:
            self.child_scopes[name] = ScopeNode(
                name=name, scope_type=scope_type, parent_scope=self
            )
        return self.child_scopes[name]


class SymbolTable:
    """Manages all scopes and symbols for a project or library."""

    def __init__(self) -> None:
        self.global_scope = ScopeNode(name="global", scope_type=SymbolScope.GLOBAL)
        self.forward_references: list[
            Symbol
        ] = []  # For symbols that need later resolution

    def add_symbol(self, symbol: Symbol, scope_path: list[str] | None = None) -> None:
        """Adds a symbol to the specified scope.
        scope_path is a list of names from global down, e.g. ["w_main", "cb_1", "clicked"].
        """
        current_scope_node = self.global_scope
        if scope_path:
            # This is a simplified way to specify scope for now.
            # We'd need to map PBD object structure to scope types correctly.
            # For example, an object's instance vars are in a scope named after the object.
            # A script's local vars are in a scope named after the script, child of the object scope.
            # This needs more thought on how scope_path translates to ScopeNode types.
            temp_scope = current_scope_node
            for part_idx, path_part in enumerate(scope_path):
                # Crude type assignment, needs refinement
                stype = SymbolScope.INSTANCE if part_idx == 0 else SymbolScope.LOCAL
                temp_scope = temp_scope.get_or_create_child_scope(path_part, stype)
            current_scope_node = temp_scope

        current_scope_node.add_symbol(symbol)
        if symbol.is_forward_reference:
            self.forward_references.append(symbol)

    def lookup_symbol(
        self, name: str, current_scope_path: list[str] | None = None
    ) -> Symbol | None:
        """Looks up a symbol, starting from the current scope and going up to global."""
        current_scope_node = self.global_scope
        if current_scope_path:
            # Traverse to the current scope node
            temp_scope = current_scope_node
            found = True
            for path_part in current_scope_path:
                if path_part in temp_scope.child_scopes:
                    temp_scope = temp_scope.child_scopes[path_part]
                else:
                    found = False  # Path doesn't exist
                    break
            if found:
                current_scope_node = temp_scope
            # If path not fully found, lookup will start from deepest valid part or global

        return current_scope_node.lookup_symbol(name, recursive=True)

    def resolve_forward_references(self) -> None:
        """Placeholder for logic to try and resolve forward references.
        
        This would iterate self.forward_references and try to find their actual definitions
        and update them (e.g., fill in data_type, ancestor for USER_OBJECTs).
        """
        # TODO: Implement forward reference resolution
        # logger.info("Attempting to resolve %s forward references.", len(self.forward_references))


# Example usage (conceptual):
# table = SymbolTable()
# w_main_loc = DefinitionLocation(object_name="w_main", line_number=1)
# w_main_symbol = Symbol(name="w_main", symbol_type=SymbolType.USER_OBJECT,
#                        data_type="window", scope=SymbolScope.GLOBAL,
#                        definition_location=w_main_loc, ancestor="window")
# table.add_symbol(w_main_symbol) # Added to global scope

# inst_var_loc = DefinitionLocation(object_name="w_main", script_name="Instance Variables", line_number=5)
# my_var = Symbol(name="ii_counter", symbol_type=SymbolType.VARIABLE, data_type="integer",
#                 scope=SymbolScope.INSTANCE, definition_location=inst_var_loc)
# table.add_symbol(my_var, scope_path=["w_main"]) # Instance var in w_main

# cb_clicked_loc = DefinitionLocation(object_name="w_main", script_name="cb_1::clicked", line_number=10)
# local_var = Symbol(name="li_temp", symbol_type=SymbolType.VARIABLE, data_type="integer",
#                    scope=SymbolScope.LOCAL, definition_location=cb_clicked_loc)
# table.add_symbol(local_var, scope_path=["w_main", "cb_1::clicked"]) # Local var

# found_local = table.lookup_symbol("li_temp", current_scope_path=["w_main", "cb_1::clicked"])
# found_instance = table.lookup_symbol("ii_counter", current_scope_path=["w_main", "cb_1::clicked"])
# found_global_obj = table.lookup_symbol("w_main", current_scope_path=["w_main", "cb_1::clicked"])
