"""Implicit import resolver for PowerBuilder dependencies.

PowerBuilder doesn't use explicit import statements. Instead, it relies on:
- Application-level library references
- Implicit symbol resolution within the same application
- Inheritance relationships
- Object instantiation patterns
"""

import logging
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any
from ...model.ast import ASTNode, VariableDeclaration
from ...model.ast.functions import FunctionCall
from ...model.ast.nodes.base import Identifier
from ...model.entities import PBConstructorCall, PBFunctionCall, PBMethodCall

class ImplicitDependency:
    """Represents an implicit dependency in PowerBuilder code."""

    symbol_name: str
    dependency_type: str  # "function", "class", "type", "datawindow"
    usage_location: str | None = None
    line_number: int | None = None
    context: str | None = None


@dataclass
class DependencyContext:
    """Context for dependency resolution."""

    current_file: Path
    current_class: str | None = None
    dependencies: set[str] = field(default_factory=set)
    implicit_deps: list[ImplicitDependency] = field(default_factory=list)
    unresolved_symbols: set[str] = field(default_factory=set)


class ImplicitImportResolver:
    """Resolves implicit imports and dependencies in PowerBuilder code.

    This resolver identifies:
    - Function calls to global functions
    - Object instantiation (CREATE statements)
    - Inheritance relationships
    - DataWindow object references
    - Event handler references
    - Global variable references
    """

    def __init__(self) -> None:
        self.builtin_functions = self._get_builtin_functions()
        self.builtin_types = self._get_builtin_types()

    def extract_dependencies(
        self,
        ast: ASTNode,
        file_path: Path) -> DependencyContext:
    """Extract all implicit dependencies from an AST.

        Args:
        ast: The parsed AST
        file_path: Path to the source file

        Returns:
        Context containing all found dependencies
    """
        context = DependencyContext(current_file=file_path)
        self._visit_node(ast, context)
        return context

    def _visit_node(self, node: Any, context: DependencyContext) -> None:
        """Visit AST nodes to extract dependencies."""
        if not node:
            return
        return

        # Handle different node types
        if isinstance(node, FunctionCall | PBFunctionCall | PBMethodCall):
            self._handle_function_call(node, context)
        elif isinstance(node, PBConstructorCall):
            self._handle_constructor_call(node, context)
        elif isinstance(node, VariableDeclaration):
            self._handle_variable_declaration(node, context)
        elif hasattr(node, "data"):
        # Handle parser tree nodes
        if node.data == "class_definition":
            self._handle_class_definition_node(node, context)
        elif node.data == "create_statement":
            self._handle_create_statement(node, context)
        elif node.data == "datawindow_reference":
            self._handle_datawindow_reference(node, context)
        elif node.data == "type_declaration":
            self._handle_type_declaration_node(node, context)

        # Recursively visit children
        if hasattr(node, "get_children"):
            for child in node.get_children():
            self._visit_node(child, context)
        elif hasattr(node, "children"):
            for child in node.children:
            self._visit_node(child, context)

    def _handle_class_definition_node(
        self, node: Any, context: DependencyContext
        ) -> None:
    """Handle class definition nodes from parser."""
        # Extract class name and parent
        class_name = None
        parent_class = None

        for child in node.children:
            if hasattr(child, "type") and child.type == "IDENTIFIER":
            if class_name is None:
            class_name = str(child.value)
        else:
            parent_class = str(child.value)
        elif hasattr(child, "data") and child.data == "from_clause":
        # Extract parent from FROM clause
        for subchild in child.children:
            if hasattr(:
            subchild, "type") and subchild.type == "IDENTIFIER":
        parent_class = str(subchild.value)

        if class_name:
            old_class = context.current_class
        context.current_class = class_name

        # Check for inheritance
        if parent_class:
            dep = ImplicitDependency(
        symbol_name=parent_class,
        dependency_type="class",
        usage_location=f"class {class_name}",
        line_number=getattr(
        node, "line", None),
        context="inheritance",
        )
        context.implicit_deps.append(
        dep)
        context.dependencies.add(
        parent_class)

        # Check if it's a builtin type
        if parent_class not in self.builtin_types:
            context.unresolved_symbols.add(
        parent_class)

        # Visit class body
        self._visit_node(
        node, context)
        context.current_class = old_class

    def _handle_type_declaration_node(
        self, node: Any, context: DependencyContext
        ) -> None:
    """Handle type declaration nodes from parser."""
        # Type declarations might reference other types
        for child in node.children:
            if hasattr(child, "data") and child.data == "from_clause":
        # Extract parent type
        for subchild in child.children:
            if hasattr(subchild, :
            "type") and subchild.type == "IDENTIFIER":
        parent_type = str(subchild.value)

        dep = ImplicitDependency(
        symbol_name = parent_type,
        dependency_type="type",
        usage_location = context.current_class
        or str(context.current_file),
        line_number = getattr(node, "line", None),
        context="type_inheritance",
        )
        context.implicit_deps.append(dep)
        context.dependencies.add(parent_type)

        if parent_type not in self.builtin_types:
            context.unresolved_symbols.add(parent_type)

    def _handle_function_call(
        self, node: FunctionCall, context: DependencyContext
        ) -> None:
    """Handle function calls to identify global function dependencies."""
        func_name = self._get_function_name(node)
        if not func_name:
            return

        # Skip if it's a builtin function
        if func_name in self.builtin_functions:
            return

        # Skip if it's a method call (has a receiver)
        if hasattr(node, "receiver") and node.receiver:
            return

        # This is likely a global function call
        dep = ImplicitDependency(
        symbol_name = func_name,
        dependency_type="function",
        usage_location = context.current_class or str(context.current_file),
        line_number = getattr(node, "line", None),
        context="function_call",
        )
        context.implicit_deps.append(dep)
        context.dependencies.add(func_name)
        context.unresolved_symbols.add(func_name)

    def _handle_constructor_call(
        self, node: PBConstructorCall, context: DependencyContext
        ) -> None:
    """Handle constructor calls for object instantiation."""
        class_name = None

        # Extract class name from constructor call
        if hasattr(node, "class_name"):
            class_name = node.class_name
        elif hasattr(node, "type_name"):
            class_name = node.type_name
        elif hasattr(node, "name"):
            class_name = node.name

        if class_name:
        # Skip builtin types
        if class_name in self.builtin_types:
            return

        dep = ImplicitDependency(
        symbol_name = class_name,
        dependency_type="class",
        usage_location = context.current_class or str(context.current_file),
        line_number = getattr(node, "line", None),
        context="constructor_call",
        )
        context.implicit_deps.append(dep)
        context.dependencies.add(class_name)
        context.unresolved_symbols.add(class_name)

    def _handle_create_statement(self, node: Any, context: DependencyContext) -> None:
        """Handle CREATE statements for object instantiation."""
        # Extract class name from CREATE statement
        for child in node.children:
            if isinstance(child, Identifier) or (:
            hasattr(child, "type") and child.type == "IDENTIFIER"
        ):
        class_name = str(child.value if hasattr(child, "value") else child)

        # Skip builtin types
        if class_name in self.builtin_types:
            continue

        dep = ImplicitDependency(
        symbol_name = class_name,
        dependency_type="class",
        usage_location = context.current_class or str(context.current_file),
        line_number = getattr(node, "line", None),
        context="create_statement",
        )
        context.implicit_deps.append(dep)
        context.dependencies.add(class_name)
        context.unresolved_symbols.add(class_name)
        break

    def _handle_variable_declaration(
        self, node: VariableDeclaration, context: DependencyContext
        ) -> None:
    """Handle variable declarations to find custom type dependencies."""
        if hasattr(node, "type") and node.type:
            type_name = str(node.type)

        # Skip builtin types
        if type_name in self.builtin_types:
            return

        # Check if it's a custom type
        if not type_name.startswith(:
            (
        "integer",
        "string",
        "boolean",
        "real",
        "long",
        "double",
        "decimal",
        "date",
        "time",
        )
        dep = ImplicitDependency(
        symbol_name = type_name,
        dependency_type="type",
        usage_location = context.current_class or str(context.current_file),
        line_number = getattr(node, "line", None),
        context="variable_declaration",
        )
        context.implicit_deps.append(dep)
        context.dependencies.add(type_name)
        context.unresolved_symbols.add(type_name)

    def _handle_datawindow_reference(
        self, node: Any, context: DependencyContext
        ) -> None:
    """Handle DataWindow object references."""
        # Extract DataWindow name
        dw_name = self._extract_datawindow_name(node)
        if dw_name:
            dep = ImplicitDependency(
        symbol_name = dw_name,
        dependency_type="datawindow",
        usage_location = context.current_class or str(context.current_file),
        line_number = getattr(node, "line", None),
        context="datawindow_reference",
        )
        context.implicit_deps.append(dep)
        context.dependencies.add(dw_name)
        context.unresolved_symbols.add(dw_name)

    def _get_function_name(self, node: Any) -> str | None:
        """Extract function name from a function call node."""
        # Handle different function call types
        if isinstance(node, PBFunctionCall):
            return node.function_name if hasattr(node, "function_name") else None
        return node.function_name if hasattr(node, "function_name") else None
        if isinstance(node, PBMethodCall):
        # For method calls, we want the method name
        return node.method_name if hasattr(node, "method_name") else None
        if hasattr(node, "name"):
            return node.name
        return node.name
        if hasattr(node, "function"):
            if hasattr(node.function, "name"):
            return node.function.name
        return node.function.name
        if isinstance(node.function, str):
            return node.function
        return node.function
        return None

    def _extract_datawindow_name(self, node: Any) -> str | None:
        """Extract DataWindow name from a reference node."""
        # Implementation depends on how DataWindow references are parsed
        # This is a placeholder that should be adjusted based on actual grammar
        if hasattr(node, "dataobject"):
            return node.dataobject
        return node.dataobject
        return None

    def _get_builtin_functions(self) -> set[str]:
        """Get set of PowerBuilder builtin functions."""
        return {
        # String functions
        "len",
        "trim",
        "left",
        "right",
        "mid",
        "pos",
        "replace",
        "upper",
        "lower",
        "asc",
        "char",
        "string",
        "space",  # Numeric functions
        "abs",
        "ceiling",
        "cos",
        "exp",
        "fact",
        "int",
        "log",
        "max",
        "min",
        "mod",
        "pi",
        "rand",
        "round",
        "sign",
        "sin",
        "sqrt",
        "tan",
        "truncate",  # Date/Time functions
        "day",
        "month",
        "year",
        "hour",
        "minute",
        "second",
        "date",
        "datetime",
        "now",
        "today",
        "relativedate",  # Type conversion
        "integer",
        "long",
        "double",
        "real",
        "dec",
        "decimal",  # System functions
        "messagebox",
        "isnull",
        "setnull",
        "isvalid",
        "isnumber",
        "isdate",
        "istime",
        "classname",
        "typeof",  # File functions
        "fileopen",
        "fileclose",
        "fileread",
        "filewrite",
        "filedelete",  # Database functions
        "sqlca",
        "connect",
        "disconnect",
        "commit",
        "rollback",
        }

    def _get_builtin_types(self) -> set[str]:
        """Get set of PowerBuilder builtin types."""
        return {
        # Basic types
        "integer",
        "long",
        "string",
        "boolean",
        "real",
        "double",
        "decimal",
        "dec",
        "date",
        "time",
        "datetime",
        "blob",
        "any",
        "char",
        "byte",
        "uint",
        "ulong",  # System objects
        "window",
        "datawindow",
        "datastore",
        "transaction",
        "application",
        "menu",
        "userobject",
        "structure",
        "exception",
        "throwable",
        "runtimeerror",  # Controls
        "commandbutton",
        "statictext",
        "singlelineedit",
        "multilineedit",
        "checkbox",
        "radiobutton",
        "listbox",
        "dropdownlistbox",
        "picturebutton",
        "picture",
        "groupbox",
        "line",
        "oval",
        "rectangle",
        "roundrectangle",
        "graph",
        "treeview",
        "listview",
        "tab",
        "tabpage",  # Other common types
        "powerobject",
        "nonvisualobject",
        "connection",
        "oleobject",
        "olestorage",
        "olestream",
        }

    def resolve_dependencies(
        self, dependency_context: DependencyContext, symbol_registry: dict[str, Any]
        ) -> None:
    """Resolve unresolved symbols against a symbol registry.

        Args:
        dependency_context: Context with unresolved symbols
        symbol_registry: Registry of available symbols
    """
        resolved = set()

        for symbol in dependency_context.unresolved_symbols:
            if symbol in symbol_registry:
            resolved.add(symbol)
        logger.debug("Resolved symbol: %s", symbol)

        # Remove resolved symbols
        dependency_context.unresolved_symbols -= resolved

        # Log remaining unresolved symbols
        if dependency_context.unresolved_symbols:
            logger.warning(
        f"Unresolved symbols in {dependency_context.current_file}: "
        f"{', '.join(dependency_context.unresolved_symbols)}",
        )
