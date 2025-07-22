"""Symbol table management for PowerBuilder AST.

This module provides comprehensive symbol table functionality for managing
identifiers, types, functions, and other named entities in PowerBuilder code.
"""

from .table import (
    SymbolTable,
    SymbolKind,
    Visibility,
    Symbol,
    Scope,
)

__all__ = [
    "SymbolTable",
    "SymbolKind",
    "Visibility",
    "Symbol",
    "Scope",
]
