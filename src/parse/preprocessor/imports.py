"""Implicit import resolver for PowerBuilder dependencies.

- Application-level library references
- Implicit symbol resolution within the same application
- Inheritance relationships
- Object instantiation patterns
"""

import logging
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Union
from src.model.ast import ASTNode, VariableDeclaration
from src.model.ast.functions import FunctionCall
from src.model.ast.nodes.base import Identifier
from src.model.entities import PBConstructorCall, PBFunctionCall, PBMethodCall

logger = logging.getLogger(__name__)


@dataclass
class ImplicitDependency:
    """Represents an implicit dependency in PowerBuilder code."""

    name: str
    dependency_type: str
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

    def extract_dependencies(self, ast: ASTNode, file_path: Path) -> DependencyContext:
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

    def _visit_node(
        self, node: Union[ASTNode, Any], context: DependencyContext
    ) -> None:
        """Visit AST nodes to extract dependencies."""
        if not node:
            return
        if isinstance(node, FunctionCall | PBFunctionCall | PBMethodCall):
            self._handle_function_call(node, context)
        elif isinstance(node, PBConstructorCall):
            self._handle_constructor_call(node, context)
        elif isinstance(node, VariableDeclaration):
            self._handle_variable_declaration(node, context)
        elif hasattr(node, "data"):
            if node.data == "class_definition":
                self._handle_class_definition_node(node, context)
            elif node.data == "create_statement":
                self._handle_create_statement(node, context)
            elif node.data == "datawindow_reference":
                self._handle_datawindow_reference(node, context)
            elif node.data == "type_declaration":
                self._handle_type_declaration_node(node, context)
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
        class_name = None
        parent_class = None
        if hasattr(node, "children"):
            for child in node.children:
                if hasattr(child, "type") and child.type == "IDENTIFIER":
                    if class_name is None:
                        class_name = str(child.value)
                    else:
                        parent_class = str(child.value)
                if hasattr(child, "data") and child.data == "from_clause":
                    for subchild in child.children:
                        if hasattr(subchild, "type") and subchild.type == "IDENTIFIER":
                            parent_class = str(subchild.value)
        if class_name:
            old_class = context.current_class
            context.current_class = class_name
            if parent_class:
                dep = ImplicitDependency(
                    name=parent_class,
                    dependency_type="class",
                    usage_location=f"class {class_name}",
                    line_number=getattr(node, "line", None),
                    context="inheritance",
                )
                context.implicit_deps.append(dep)
                context.dependencies.add(parent_class)
                if parent_class not in self.builtin_types:
                    context.unresolved_symbols.add(parent_class)
            self._visit_node(node, context)
            context.current_class = old_class

    def _handle_type_declaration_node(
        self, node: Any, context: DependencyContext
    ) -> None:
        """Handle type declaration nodes from parser."""
        if hasattr(node, "children"):
            for child in node.children:
                if hasattr(child, "data") and child.data == "from_clause":
                    for subchild in child.children:
                        if hasattr(subchild, "type") and subchild.type == "IDENTIFIER":
                            parent_type = str(subchild.value)
                            dep = ImplicitDependency(
                                name=parent_type,
                                dependency_type="type",
                                usage_location=context.current_class
                                or str(context.current_file),
                                line_number=getattr(node, "line", None),
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
        if func_name in self.builtin_functions:
            return
        if hasattr(node, "receiver") and node.receiver:
            return
        dep = ImplicitDependency(
            name=func_name,
            dependency_type="function",
            usage_location=context.current_class or str(context.current_file),
            line_number=getattr(node, "line", None),
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
        if hasattr(node, "class_name"):
            class_name = node.class_name
        elif hasattr(node, "type_name"):
            class_name = node.type_name
        elif hasattr(node, "name"):
            class_name = node.name
        if class_name:
            if class_name in self.builtin_types:
                return
            dep = ImplicitDependency(
                name=class_name,
                dependency_type="class",
                usage_location=context.current_class or str(context.current_file),
                line_number=getattr(node, "line", None),
                context="constructor_call",
            )
            context.implicit_deps.append(dep)
            context.dependencies.add(class_name)
            context.unresolved_symbols.add(class_name)

    def _handle_create_statement(self, node: Any, context: DependencyContext) -> None:
        """Handle CREATE statements for object instantiation."""
        for child in node.children:
            if (
                isinstance(child, Identifier)
                or hasattr(child, "type")
                and child.type == "IDENTIFIER"
            ):
                class_name = str(child.value if hasattr(child, "value") else child)
                if class_name in self.builtin_types:
                    continue
                dep = ImplicitDependency(
                    name=class_name,
                    dependency_type="class",
                    usage_location=context.current_class or str(context.current_file),
                    line_number=getattr(node, "line", None),
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
            if type_name in self.builtin_types:
                return
            if not type_name.startswith(
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
            ):
                dep = ImplicitDependency(
                    name=type_name,
                    dependency_type="type",
                    usage_location=context.current_class or str(context.current_file),
                    line_number=getattr(node, "line", None),
                    context="variable_declaration",
                )
                context.implicit_deps.append(dep)
                context.dependencies.add(type_name)
                context.unresolved_symbols.add(type_name)

    def _handle_datawindow_reference(
        self, node: Any, context: DependencyContext
    ) -> None:
        """Handle DataWindow object references."""
        dw_name = self._extract_datawindow_name(node)
        if dw_name:
            dep = ImplicitDependency(
                name=dw_name,
                dependency_type="datawindow",
                usage_location=context.current_class or str(context.current_file),
                line_number=getattr(node, "line", None),
                context="datawindow_reference",
            )
            context.implicit_deps.append(dep)
            context.dependencies.add(dw_name)
            context.unresolved_symbols.add(dw_name)

    def _get_function_name(self, node: Any) -> str | None:
        """Extract function name from a function call node."""
        if isinstance(node, PBFunctionCall):
            return node.function_name if hasattr(node, "function_name") else None
        if isinstance(node, PBMethodCall):
            return node.method_name if hasattr(node, "method_name") else None
        if hasattr(node, "name"):
            return node.name
        if hasattr(node, "function"):
            if hasattr(node.function, "name"):
                return node.function.name
            if isinstance(node.function, str):
                return node.function
        return None

    def _extract_datawindow_name(self, node: Any) -> str | None:
        """Extract DataWindow name from a reference node."""
        if hasattr(node, "dataobject"):
            return node.dataobject
        return None

    def _get_builtin_functions(self) -> set[str]:
        """Get set of PowerBuilder builtin functions."""
        return {
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
            "space",
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
            "truncate",
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
            "relativedate",
            "integer",
            "long",
            "double",
            "real",
            "dec",
            "decimal",
            "messagebox",
            "isnull",
            "setnull",
            "isvalid",
            "isnumber",
            "isdate",
            "istime",
            "classname",
            "typeof",
            "fileopen",
            "fileclose",
            "fileread",
            "filewrite",
            "filedelete",
            "sqlca",
            "connect",
            "disconnect",
            "commit",
            "rollback",
        }

    def _get_builtin_types(self) -> set[str]:
        """Get set of PowerBuilder builtin types."""
        return {
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
            "ulong",
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
            "runtimeerror",
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
            "tabpage",
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

        dependency_context: Context with unresolved symbols
        symbol_registry: Registry of available symbols
        """
        resolved = set()
        for symbol in dependency_context.unresolved_symbols:
            if symbol in symbol_registry:
                resolved.add(symbol)
                logger.debug("Resolved symbol: %s", symbol)
        dependency_context.unresolved_symbols -= resolved
        if dependency_context.unresolved_symbols:
            logger.warning(
                "Unresolved symbols in %s: %s",
                dependency_context.current_file,
                ", ".join(dependency_context.unresolved_symbols),
            )
