"""Python code generation for PowerBuilder and Pseudocode transpiler.

This module provides code generation features including:
- Clean Python output
- Source mapping
- Error location tracking
- Code optimization
"""

import ast
import logging
from dataclasses import dataclass, field
from enum import Enum
from textwrap import indent
from typing import Any

import black
import libcst as cst

from model.ast import (
    ArrayOperation,
    ArrayType,
    ControlFlow,
    FileOperation,
    FunctionDefinition,
    ProcedureDefinition,
    Type,
    TypeCategory,
)

logger = logging.getLogger(__name__)


class OptimizationLevel(Enum):
    """Code optimization levels."""

    NONE = 1  # No optimization
    BASIC = 2  # Dead code elimination
    AGGRESSIVE = 3  # Includes constant folding, loop optimization

    def __lt__(self, other) -> bool:




        """Less than comparison."""
        if self.__class__ is other.__class__:
            return self.value < other.value
        return NotImplemented

    def __le__(self, other) -> bool:




        """Less than or equal comparison."""
        if self.__class__ is other.__class__:
            return self.value <= other.value
        return NotImplemented

    def __gt__(self, other) -> bool:




        """Greater than comparison."""
        if self.__class__ is other.__class__:
            return self.value > other.value
        return NotImplemented

    def __ge__(self, other) -> bool:




        """Greater than or equal comparison."""
        if self.__class__ is other.__class__:
            return self.value >= other.value
        return NotImplemented


@dataclass
class SourceMapping:
    """Source code mapping information."""

    original_file: str
    original_line: int
    generated_file: str
    generated_line: int
    context: str = ""


@dataclass
class CodegenState:
    """Code generation state."""

    indent_level: int = 0
    current_function: str | None = None
    imports: set[str] = field(default_factory=set)
    source_maps: list[SourceMapping] = field(default_factory=list)
    variables: dict[str, Type] = field(default_factory=dict)
    optimization_level: OptimizationLevel = OptimizationLevel.BASIC

    def add_import(self, module: str) -> None:




        """Add import statement."""
        self.imports.add(module)

    def add_source_map(self, mapping: SourceMapping) -> None:




        """Add source mapping."""
        self.source_maps.append(mapping)

    def get_source_location(self, line: int) -> SourceMapping | None:




        """Get original source location for generated line."""
        for mapping in reversed(self.source_maps):
            if mapping.generated_line <= line:
                return mapping
        return None


@dataclass
class CodeGenerator:
    """Python code generator."""

    state: CodegenState = field(default_factory=CodegenState)

    def generate_module(self, statements: list[Any]) -> str:




        """Generate complete Python module."""
        self._add_standard_imports()

        parts = []

        # Add imports
        if self.state.imports:
            parts.append(self._generate_imports())
            parts.append("")  # Empty line after imports

        # Add statements
        for stmt in statements:
            parts.append(self.generate_statement(stmt))

        code = "\n".join(parts)

        # Apply optimizations
        if self.state.optimization_level != OptimizationLevel.NONE:
            code = self._optimize_code(code)

        # Format with black
        try:
            code = black.format_str(code, mode=black.FileMode())
        except Exception as e:
            logger.exception("Failed to format code with black: %s", str(e))
            # Return unformatted code

        return code

    def generate_statement(self, stmt: Any) -> str:




        """Generate Python code for a statement."""
        if isinstance(stmt, ControlFlow):
            return self._generate_control_flow(stmt)
        if isinstance(stmt, FunctionDefinition):
            return self._generate_function(stmt)
        if isinstance(stmt, ProcedureDefinition):
            return self._generate_procedure(stmt)
        if isinstance(stmt, ArrayOperation):
            return self._generate_array_operation(stmt)
        if isinstance(stmt, FileOperation):
            return self._generate_file_operation(stmt)
        return self._generate_expression(stmt)

    def _add_standard_imports(self) -> None:




        """Add standard library imports."""
        self.state.add_import("typing import List, Any")
        self.state.add_import("dataclasses import dataclass")
        self.state.add_import("datetime import datetime")

    def _generate_imports(self) -> str:




        """Generate import statements."""
        return "\n".join(f"from {imp}" for imp in sorted(self.state.imports))

    def _generate_control_flow(self, stmt: ControlFlow) -> str:




        """Generate control flow statement."""
        if stmt.type == "if":
            return self._generate_if(stmt)
        if stmt.type == "while":
            return self._generate_while(stmt)
        if stmt.type == "for":
            return self._generate_for(stmt)
        if stmt.type == "try":
            return self._generate_try(stmt)
        msg = f"Unknown control flow type: {stmt.type}"
        raise ValueError(msg)

    def _generate_function(self, func: FunctionDefinition) -> str:




        """Generate function definition."""
        self.state.current_function = func.name

        # Generate signature
        params = []
        for param in func.parameters:
            annotation = self._type_to_python(param.type)
            default = f" = {param.default}" if param.default else ""
            params.append(f"{param.name}: {annotation}{default}")

        return_type = self._type_to_python(func.return_type)
        signature = f"def {func.name}({", ".join(params)}) -> {return_type}:"

        # Generate body
        body = []
        if func.docstring:
            body.append(f'    """{func.docstring}"""')

        for stmt in func.body:
            body.append(indent(self.generate_statement(stmt), "    "))

        self.state.current_function = None
        return "\n".join([signature, *body])

    def _generate_procedure(self, proc: ProcedureDefinition) -> str:




        """Generate procedure definition."""
        self.state.current_function = proc.name

        # Generate signature
        params = []
        for param in proc.parameters:
            annotation = self._type_to_python(param.type)
            params.append(f"{param.name}: {annotation}")

        signature = f"def {proc.name}({", ".join(params)}) -> None:"

        # Generate body
        body = []
        if proc.docstring:
            body.append(f'    """{proc.docstring}"""')

        for stmt in proc.body:
            body.append(indent(self.generate_statement(stmt), "    "))

        self.state.current_function = None
        return "\n".join([signature, *body])

    def _generate_array_operation(self, op: ArrayOperation) -> str:




        """Generate array operation."""
        # Get the array name (assuming it's an Identifier)
        array_name = op.array.name if hasattr(op.array, 'name') else str(op.array)
        
        if op.operation == "LENGTH":
            return f"len({array_name})"
        if op.operation == "COPY":
            return f"{array_name}.copy()"
        if op.operation == "CONCAT":
            # Get the argument (assuming it's an Identifier)
            arg = op.arguments[0].name if hasattr(op.arguments[0], 'name') else str(op.arguments[0])
            return f"{array_name} + {arg}"
        if op.operation == "RESIZE":
            # Get the dimensions from arguments
            dims = ", ".join(str(arg.value if hasattr(arg, 'value') else arg) for arg in op.arguments)
            return f"{array_name}.resize([{dims}])"
        msg = f"Unknown array operation: {op.operation}"
        raise ValueError(msg)

    def _generate_file_operation(self, op: FileOperation) -> str:




        """Generate file operation."""
        if op.type == "OPEN":
            return f'open("{op.file_path}", "{op.mode.value}")'
        if op.type == "CLOSE":
            return f"{op.file_path}.close()"
        if op.type == "READ":
            if op.max_bytes:
                return f"{op.file_path}.read({op.max_bytes})"
            return f"{op.file_path}.read()"
        if op.type == "WRITE":
            return f'{op.file_path}.write("{op.content}")'
        msg = f"Unknown file operation: {op.type}"
        raise ValueError(msg)

    def _generate_expression(self, expr: Any) -> str:




        """Generate Python expression."""
        if isinstance(expr, ast.AST):
            return self._ast_to_source_with_libcst(expr)
        return str(expr)

    def _ast_to_source_with_libcst(self, node: ast.AST) -> str:




        """Convert a Python ast.AST node to source code.

        Attempts to use built-in ast.unparse (Python 3.9+) with a fallback for older Python versions.
        Then tries to format the code with LibCST if available.

        Args:
            node: The AST node to convert to source

        Returns:
            str: Formatted source code
        """
        # First, convert AST to source code
        try:
            # Try using ast.unparse (Python 3.9+)
            code = ast.unparse(node)
        except AttributeError:
            # For Python <3.9, use a simple fallback
            if isinstance(node, ast.Module):
                code = "\n".join(self.generate_statement(stmt) for stmt in node.body)
            else:
                # This is a very simplified fallback
                code = str(node)

        # Then attempt to format with LibCST if available
        try:
            # If LibCST is available, use it for formatting
            module = cst.parse_module(code)
            formatted = module.code
            return formatted.strip()
        except Exception as e:
            logger.exception("Failed to format code with LibCST: %s", str(e))
            # Fallback: return the code as-is
            return code.strip()

    def _type_to_python(self, type_: Type) -> str:




        """Convert type to Python type annotation."""
        if isinstance(type_, ArrayType):
            elem_type = self._type_to_python(type_.element_type)
            return f"list[{elem_type}]"

        if type_.category == TypeCategory.NUMERIC:
            if type_.name == "INTEGER":
                return "int"
            if type_.name == "REAL":
                return "float"
            if type_.name == "DECIMAL":
                self.state.add_import("decimal import Decimal")
                return "Decimal"
        elif type_.category == TypeCategory.TEXT:
            return "str"
        elif type_.category == TypeCategory.LOGICAL:
            return "bool"
        elif type_.category == TypeCategory.BASIC:
            if type_.name == "DATE":
                self.state.add_import("datetime import date")
                return "date"
            if type_.name == "TIME":
                self.state.add_import("datetime import time")
                return "time"

        return "Any"

    def _optimize_code(self, code: str) -> str:




        """Apply code optimizations."""
        tree = ast.parse(code)

        if self.state.optimization_level >= OptimizationLevel.BASIC:
            tree = self._eliminate_dead_code(tree)

        if self.state.optimization_level >= OptimizationLevel.AGGRESSIVE:
            tree = self._fold_constants(tree)
            tree = self._optimize_loops(tree)

        return self._ast_to_source_with_libcst(tree)

    def _eliminate_dead_code(self, tree: ast.AST) -> ast.AST:




        """Eliminate dead code."""

        class DeadCodeEliminator(ast.NodeTransformer):
            def visit_If(self, node) -> None:

                # Remove if statements with constant False condition
                if isinstance(node.test, ast.Constant) and not node.test.value:
                    return node.orelse if node.orelse else None
                # Remove empty else blocks
                if not node.orelse:
                    return node
                return self.generic_visit(node)

            def visit_While(self, node) -> None:


                # Remove while loops with constant False condition
                if isinstance(node.test, ast.Constant) and not node.test.value:
                    return None
                return self.generic_visit(node)

        return DeadCodeEliminator().visit(tree)

    def _fold_constants(self, tree: ast.AST) -> ast.AST:




        """Fold constant expressions."""

        class ConstantFolder(ast.NodeTransformer):
            def visit_BinOp(self, node) -> None:

                node = self.generic_visit(node)
                if isinstance(node.left, ast.Constant) and isinstance(
                    node.right, ast.Constant, ):
                    try:
                        if isinstance(node.op, ast.Add):
                            return ast.Constant(node.left.value + node.right.value)
                        if isinstance(node.op, ast.Sub):
                            return ast.Constant(node.left.value - node.right.value)
                        if isinstance(node.op, ast.Mult):
                            return ast.Constant(node.left.value * node.right.value)
                        if isinstance(node.op, ast.Div):
                            return ast.Constant(node.left.value / node.right.value)
                    except Exception as e:
                        logger.debug("Failed to fold constant expression: %s", str(e))
                return node

        return ConstantFolder().visit(tree)

    def _optimize_loops(self, tree: ast.AST) -> ast.AST:




        """Optimize loops."""

        class LoopOptimizer(ast.NodeTransformer):
            def visit_For(self, node) -> None:

                node = self.generic_visit(node)
                # Convert range(len(x)) to enumerate(x)
                if (
                    isinstance(node.iter, ast.Call)
                    and isinstance(node.iter.func, ast.Name)
                    and node.iter.func.id == "range"
                    and len(node.iter.args) == 1
                    and isinstance(node.iter.args[0], ast.Call)
                    and isinstance(node.iter.args[0].func, ast.Name)
                    and node.iter.args[0].func.id == "len"
                ):
                    return ast.For(
                        target=ast.Tuple(
                            [node.target, ast.Name(id="_")], ctx=ast.Store(), ), iter=ast.Call(
                            func=ast.Name(id="enumerate", ctx=ast.Load()), args=[node.iter.args[0].args[0]], keywords=[], ), body=node.body, orelse=node.orelse, )
                return node

        return LoopOptimizer().visit(tree)
