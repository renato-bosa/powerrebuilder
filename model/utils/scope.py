"""Scope management for AST nodes.

This module provides a Scope class for tracking variables, functions, and procedures
during AST validation.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from model.ast.functions import FunctionDefinition, ProcedureDefinition
    from model.ast.types import Type


class Scope:
    """Scope for variable and function lookup."""

    def __init__(self, parent: Scope | None = None) -> None:
        

        self.parent = parent
        self.variables: dict[str, Type] = {}
        self.functions: dict[str, FunctionDefinition] = {}
        self.procedures: dict[str, ProcedureDefinition] = {}

    def get_variable(self, name: str) -> Type | None:


        

        """Get variable type from this or parent scope."""
        if name in self.variables:
            return self.variables[name]
        if self.parent:
            return self.parent.get_variable(name)
        return None

    def get_function(self, name: str) -> FunctionDefinition | None:


        

        """Get function from this or parent scope."""
        if name in self.functions:
            return self.functions[name]
        if self.parent:
            return self.parent.get_function(name)
        return None

    def get_procedure(self, name: str) -> ProcedureDefinition | None:


        

        """Get procedure from this or parent scope."""
        if name in self.procedures:
            return self.procedures[name]
        if self.parent:
            return self.parent.get_procedure(name)
        return None

    def declare_variable(self, name: str, type_: Type) -> None:


        

        """Declare a variable in current scope."""
        self.variables[name] = type_

    def declare_function(self, func: FunctionDefinition) -> None:


        

        """Declare a function in current scope."""
        self.functions[func.signature.name] = func

    def declare_procedure(self, proc: ProcedureDefinition) -> None:


        

        """Declare a procedure in current scope."""
        self.procedures[proc.signature.name] = proc