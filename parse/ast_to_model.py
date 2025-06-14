"""Convert AST nodes to model objects for the pipeline.

This module bridges the gap between the new AST nodes produced by the parser
and the existing model objects expected by the code generation pipeline.
"""

from typing import Any

from model.ast import (
    ASTAssignment,
    BinaryExpression,
    BooleanLiteral,
    CustomType,
    Event,
    ForLoop,
    FunctionDefinition,
    IfStatement,
    IntegerLiteral,
    ReturnStatement,
    StringLiteral,
    UnaryExpression,
    Variable,
    WhileLoop,
)
from model.entities.function_entities import PBFunction
from model.ui import Window


class ASTToModelConverter:
    """Convert AST nodes to model objects."""

    def __init__(self) -> None:
        self.source_registry = {}

    def convert_file(self, ast_dict: dict[str, Any]) -> list[Any]:
        """Convert a parsed file AST to model objects.

        Args:
            ast_dict: Dictionary with 'type': 'file' and 'elements' list

        Returns:
            List of model objects (Windows, Functions, etc.)
        """
        if not isinstance(ast_dict, dict) or ast_dict.get("type") != "file":
            return []

        model_objects = []

        for element in ast_dict.get("elements", []):
            model_obj = self.convert_element(element)
            if model_obj:
                model_objects.append(model_obj)

        return model_objects

    def convert_element(self, element: Any) -> Any | None:
        """Convert a single AST element to a model object.

        Args:
            element: AST node

        Returns:
            Model object or None
        """
        if isinstance(element, FunctionDefinition):
            return self.convert_function(element)
        if isinstance(element, CustomType):
            return self.convert_type(element)
        if isinstance(element, Event):
            # Events are typically part of a window/control,
            # but can also be standalone for now
            return element  # Return Event as-is for now
        # Unknown element type
        return None

    def convert_function(self, func_def: FunctionDefinition) -> PBFunction:
        """Convert FunctionDefinition AST to PBFunction model.

        Args:
            func_def: FunctionDefinition AST node

        Returns:
            PBFunction model object
        """
        # Create PBFunction
        pb_func = PBFunction(name=func_def.signature.name)

        # Set return type
        if func_def.signature.return_type:
            pb_func.return_type = func_def.signature.return_type.name

        # Convert parameters
        pb_func.parameters = []
        for param in func_def.signature.parameters:
            pb_param = {
                "name": param.name,
                "type": param.type.name if param.type else "any",
                "is_ref": param.is_ref,
                "is_readonly": param.is_readonly,
            }
            pb_func.parameters.append(pb_param)

        # Convert body statements to source
        source_lines = []
        for stmt in func_def.body.statements:
            source_lines.append(self.statement_to_source(stmt))

        # Store source as string (PBFunction expects string)
        pb_func.source = "\n".join(source_lines)

        # Set access modifier
        if hasattr(func_def.signature, "is_public"):
            pb_func.is_public = func_def.signature.is_public

        return pb_func

    def convert_type(self, custom_type: CustomType) -> Window | None:
        """Convert CustomType AST to Window or other type model.

        Args:
            custom_type: CustomType AST node

        Returns:
            Window or other model object
        """
        # Check parent type
        parent = None
        if hasattr(custom_type, "parent_type") and custom_type.parent_type:
            parent = str(custom_type.parent_type).lower()
        # Look for common patterns in the name
        elif "window" in custom_type.name.lower():
            parent = "window"

        if parent == "window":
            # Create Window model
            # Use the name as the title by default
            window = Window(name=custom_type.name, title=custom_type.name)

            # Set global flag
            if hasattr(custom_type, "is_global"):
                window.is_global = custom_type.is_global

            # Set parent type if available
            if hasattr(custom_type, "parent_type"):
                window.parent_type = custom_type.parent_type

            return window

        # For other types, return None for now
        return None

    def statement_to_source(self, stmt: Any) -> str:
        """Convert a statement to source code string.

        Args:
            stmt: Statement AST node

        Returns:
            Source code string
        """
        if isinstance(stmt, ReturnStatement):
            if stmt.value:
                return f"return {self.expression_to_source(stmt.value)}"
            return "return"

        if isinstance(stmt, ASTAssignment):
            target = self.expression_to_source(stmt.target)
            value = self.expression_to_source(stmt.value)
            return f"{target} = {value}"

        if isinstance(stmt, IfStatement):
            # Simple if statement conversion
            condition = self.expression_to_source(stmt.condition)
            result = f"if {condition} then\n"
            if hasattr(stmt, "then_branch") and stmt.then_branch:
                if hasattr(stmt.then_branch, "statements"):
                    for s in stmt.then_branch.statements:
                        result += f"    {self.statement_to_source(s)}\n"
                else:
                    result += f"    {self.statement_to_source(stmt.then_branch)}\n"
            if hasattr(stmt, "else_branch") and stmt.else_branch:
                result += "else\n"
                if hasattr(stmt.else_branch, "statements"):
                    for s in stmt.else_branch.statements:
                        result += f"    {self.statement_to_source(s)}\n"
                else:
                    result += f"    {self.statement_to_source(stmt.else_branch)}\n"
            result += "end if"
            return result

        if isinstance(stmt, ForLoop):
            result = f"for {stmt.variable} = {self.expression_to_source(stmt.start)} to {self.expression_to_source(stmt.end)}"
            if stmt.step:
                result += f" step {self.expression_to_source(stmt.step)}"
            result += "\n"
            if stmt.body:
                for s in stmt.body.statements:
                    result += f"    {self.statement_to_source(s)}\n"
            result += "next"
            return result

        if isinstance(stmt, WhileLoop):
            condition = self.expression_to_source(stmt.condition)
            result = f"do while {condition}\n"
            if stmt.body:
                for s in stmt.body.statements:
                    result += f"    {self.statement_to_source(s)}\n"
            result += "loop"
            return result

        # Default: try to convert to string
        return str(stmt)

    def expression_to_source(self, expr: Any) -> str:
        """Convert an expression to source code string.

        Args:
            expr: Expression AST node

        Returns:
            Source code string
        """
        if isinstance(expr, IntegerLiteral):
            return str(expr.value)
        if isinstance(expr, StringLiteral):
            return f'"{expr.value}"'
        if isinstance(expr, BooleanLiteral):
            return str(expr.value).lower()
        if isinstance(expr, Variable):
            return expr.name
        if isinstance(expr, BinaryExpression):
            left = self.expression_to_source(expr.left)
            right = self.expression_to_source(expr.right)
            return f"{left} {expr.operator} {right}"
        if isinstance(expr, UnaryExpression):
            operand = self.expression_to_source(expr.operand)
            return f"{expr.operator} {operand}"
        if hasattr(expr, "value"):
            # Token or simple value
            return str(expr.value)
        return str(expr)
