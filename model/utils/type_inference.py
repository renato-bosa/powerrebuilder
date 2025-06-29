"""Type inference system for PowerBuilder expressions and variables.

This module provides type inference capabilities for PowerBuilder code,
allowing automatic type detection from context and usage patterns.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from enum import Enum, auto
from typing import TYPE_CHECKING, Any

from common.constants import BUFFER_SIZE, HEADER_SIZE, STRING_TABLE_OFFSET

if TYPE_CHECKING:
    from model.expressions import (Expression)
    from model.expressions import (PBExpression)

logger = logging.getLogger(__name__)


class InferenceStrategy(Enum):
    """Type inference strategies."""

    LITERAL = auto()        # Infer from literal values
    ASSIGNMENT = auto()     # Infer from assignments
    FUNCTION_RETURN = auto() # Infer from function returns
    OPERATION = auto()      # Infer from operations
    CONTEXT = auto()        # Infer from context/usage
    DECLARATION = auto()    # Explicit declaration


@dataclass
class TypeInfo:
    """Type information for a variable or expression."""

    type_name: str
    is_nullable: bool = True
    is_array: bool = False
    array_dimensions: int = 0
    element_type: str | None = None
    confidence: float = 1.0  # 0.0 to 1.0
    source: InferenceStrategy = InferenceStrategy.CONTEXT
    constraints: dict[str, Any] = field(default_factory=dict)

    def __str__(self) -> str:




        """String representation of type."""
        base = self.type_name
        if self.is_array:
            base = self.element_type or base
            base += "[]" * self.array_dimensions
        if self.is_nullable:
            base += "?"
        return base

    def is_compatible_with(self, other: "TypeInfo") -> bool:




        """Check if this type is compatible with another."""
        # Null is compatible with any nullable type
        if self.type_name == "null":
            return other.is_nullable
        if other.type_name == "null":
            return self.is_nullable

        # Any type is compatible with anything
        if self.type_name == "any" or other.type_name == "any":
            return True

        # Array compatibility
        if self.is_array != other.is_array:
            return False
        if self.is_array and self.array_dimensions != other.array_dimensions:
            return False

        # Check base type compatibility
        return self._is_base_type_compatible(other)

    def _is_base_type_compatible(self, other: "TypeInfo") -> bool:




        """Check base type compatibility."""
        # Exact match
        if self.type_name == other.type_name:
            return True

        # Numeric type promotion
        numeric_types = ["byte", "integer", "long", "real", "double", "decimal"]
        if self.type_name in numeric_types and other.type_name in numeric_types:
            return True

        # String compatibility
        string_types = ["char", "string"]
        if self.type_name in string_types and other.type_name in string_types:
            return True

        # Date/time compatibility
        datetime_types = ["date", "time", "datetime"]
        if self.type_name in datetime_types and other.type_name in datetime_types:
            return True

        return False

    def merge_with(self, other: "TypeInfo") -> "TypeInfo":




        """Merge this type info with another, creating a unified type."""
        # If one is null, return the other
        if self.type_name == "null":
            return other
        if other.type_name == "null":
            return self

        # If either is any, return any
        if self.type_name == "any" or other.type_name == "any":
            return TypeInfo("any", is_nullable=True)

        # If compatible, return the more general type
        if self.is_compatible_with(other):
            # Choose the type with lower confidence
            if self.confidence <= other.confidence:
                return self
            else:
                return other

        # If not compatible, return any
        return TypeInfo("any", is_nullable=True, confidence=0.5)


@dataclass
class TypeContext:
    """Context for type inference within a scope."""

    variables: dict[str, TypeInfo] = field(default_factory=dict)
    functions: dict[str, TypeInfo] = field(default_factory=dict)
    parent: "TypeContext" | None = None

    def get_variable_type(self, name: str) -> TypeInfo | None:




        """Get type of a variable, checking parent contexts."""
        if name in self.variables:
            return self.variables[name]
        if self.parent:
            return self.parent.get_variable_type(name)
        return None

    def set_variable_type(self, name: str, type_info: TypeInfo) -> None:




        """Set variable type in current context."""
        self.variables[name] = type_info

    def get_function_return_type(self, name: str) -> TypeInfo | None:




        """Get return type of a function."""
        if name in self.functions:
            return self.functions[name]
        if self.parent:
            return self.parent.get_function_return_type(name)
        return None

    def create_child_context(self) -> "TypeContext":




        """Create a child context for nested scope."""
        return TypeContext(parent=self)


class TypeInferenceEngine:
    """Engine for inferring types in PowerBuilder code."""

    def __init__(self, context: TypeContext | None = None) -> None:


        """Initialize type inference engine."""
        self.context = context or TypeContext()
        self._init_builtin_types()

    def _init_builtin_types(self) -> None:




        """Initialize built-in function return types."""
        # String functions
        self.context.functions.update({
            "len": TypeInfo("integer", is_nullable=False), "lenw": TypeInfo("integer", is_nullable=False), "trim": TypeInfo("string"), "upper": TypeInfo("string"), "lower": TypeInfo("string"), "mid": TypeInfo("string"), "left": TypeInfo("string"), "right": TypeInfo("string"), "pos": TypeInfo("integer", is_nullable=False), "replace": TypeInfo("string"), # Numeric functions
            "abs": TypeInfo("double", is_nullable=False), "ceiling": TypeInfo("integer", is_nullable=False), "floor": TypeInfo("integer", is_nullable=False), "round": TypeInfo("double", is_nullable=False), "sqrt": TypeInfo("double", is_nullable=False), "sin": TypeInfo("double", is_nullable=False), "cos": TypeInfo("double", is_nullable=False), # Type conversion
            "int": TypeInfo("integer", is_nullable=False), "integer": TypeInfo("integer", is_nullable=False), "long": TypeInfo("long", is_nullable=False), "real": TypeInfo("real", is_nullable=False), "double": TypeInfo("double", is_nullable=False), "string": TypeInfo("string"), "boolean": TypeInfo("boolean", is_nullable=False), # Type checking
            "isnull": TypeInfo("boolean", is_nullable=False), "isvalid": TypeInfo("boolean", is_nullable=False), "isnumber": TypeInfo("boolean", is_nullable=False), "isdate": TypeInfo("boolean", is_nullable=False), # Date/time
            "today": TypeInfo("date", is_nullable=False), "now": TypeInfo("datetime", is_nullable=False), "year": TypeInfo("integer", is_nullable=False), "month": TypeInfo("integer", is_nullable=False), "day": TypeInfo("integer", is_nullable=False), # Array
            "upperbound": TypeInfo("integer", is_nullable=False), "lowerbound": TypeInfo("integer", is_nullable=False), })

    def infer_literal_type(self, value: Any) -> TypeInfo:




        """Infer type from a literal value."""
        if value is None:
            return TypeInfo("null", is_nullable=True, source=InferenceStrategy.LITERAL)

        if isinstance(value, bool):
            return TypeInfo("boolean", is_nullable=False, source=InferenceStrategy.LITERAL)

        if isinstance(value, int):
            # Check range for different integer types
            if -128 <= value <= 127:
                return TypeInfo("byte", is_nullable=False, source=InferenceStrategy.LITERAL)
            elif -32768 <= value <= 32767:
                return TypeInfo("integer", is_nullable=False, source=InferenceStrategy.LITERAL)
            else:
                return TypeInfo("long", is_nullable=False, source=InferenceStrategy.LITERAL)

        if isinstance(value, float):
            return TypeInfo("double", is_nullable=False, source=InferenceStrategy.LITERAL)

        if isinstance(value, str):
            if len(value) == 1:
                return TypeInfo("char", is_nullable=False, source=InferenceStrategy.LITERAL)
            else:
                return TypeInfo("string", is_nullable=False, source=InferenceStrategy.LITERAL)

        if isinstance(value, list):
            # Infer array type from elements
            if not value:
                return TypeInfo("any", is_array=True, array_dimensions=1, source=InferenceStrategy.LITERAL)

            # Check first element for type
            element_type = self.infer_literal_type(value[0])
            return TypeInfo(
                element_type.type_name, is_array=True, array_dimensions=1, element_type=element_type.type_name, is_nullable=False, source=InferenceStrategy.LITERAL,
            )

        if isinstance(value, bytes):
            return TypeInfo("blob", is_nullable=False, source=InferenceStrategy.LITERAL)

        # Default to any
        return TypeInfo("any", source=InferenceStrategy.LITERAL, confidence=0.5)

    def infer_expression_type(self, expr: Expression | PBExpression) -> TypeInfo:




        """Infer type from an expression."""
        # Get expression class name
        expr_type = expr.__class__.__name__

        # Handle literals
        if "Literal" in expr_type:
            if hasattr(expr, "value"):
                return self.infer_literal_type(expr.value)
            elif "Null" in expr_type:
                return TypeInfo("null", is_nullable=True, source=InferenceStrategy.LITERAL)

        # Handle variables
        if "Variable" in expr_type and hasattr(expr, "name"):
            var_type = self.context.get_variable_type(expr.name)
            if var_type:
                return var_type
            # Unknown variable
            return TypeInfo("any", confidence=0.3, source=InferenceStrategy.CONTEXT)

        # Handle binary operations
        if "Binary" in expr_type and hasattr(expr, "operator"):
            return self._infer_binary_operation_type(expr)

        # Handle unary operations
        if "Unary" in expr_type and hasattr(expr, "operator"):
            return self._infer_unary_operation_type(expr)

        # Handle function calls
        if "FunctionCall" in expr_type or "MethodCall" in expr_type:
            return self._infer_function_call_type(expr)

        # Handle array access
        if "ArrayAccess" in expr_type:
            return self._infer_array_access_type(expr)

        # Handle field reference
        if "FieldReference" in expr_type:
            return self._infer_field_reference_type(expr)

        # Handle cast expression
        if "Cast" in expr_type and hasattr(expr, "target_type"):
            return TypeInfo(expr.target_type.lower(), source=InferenceStrategy.OPERATION)

        # Handle ternary/conditional
        if "Ternary" in expr_type or "Conditional" in expr_type:
            return self._infer_ternary_type(expr)

        # Default to any
        return TypeInfo("any", confidence=0.2, source=InferenceStrategy.CONTEXT)

    def _infer_binary_operation_type(self, expr) -> TypeInfo:




        """Infer type from binary operation."""
        operator = expr.operator

        # Comparison operators always return boolean
        if operator in ["==", "!=", "<", ">", "<=", ">=", "=", "<>"]:
            return TypeInfo("boolean", is_nullable=False, source=InferenceStrategy.OPERATION)

        # Logical operators return boolean
        if operator in ["and", "or", "&&", "||"]:
            return TypeInfo("boolean", is_nullable=False, source=InferenceStrategy.OPERATION)

        # String concatenation
        if operator == "+":
            # Check if either operand is string
            left_type = self.infer_expression_type(expr.left)
            right_type = self.infer_expression_type(expr.right)

            if left_type.type_name == "string" or right_type.type_name == "string":
                return TypeInfo("string", source=InferenceStrategy.OPERATION)

        # Numeric operations
        if operator in ["+", "-", "*", "/", "%", "^", "**"]:
            left_type = self.infer_expression_type(expr.left)
            right_type = self.infer_expression_type(expr.right)

            # If either is double/real, result is double
            if left_type.type_name in ["double", "real"] or right_type.type_name in ["double", "real"]:
                return TypeInfo("double", is_nullable=False, source=InferenceStrategy.OPERATION)

            # Division always returns double
            if operator == "/":
                return TypeInfo("double", is_nullable=False, source=InferenceStrategy.OPERATION)

            # Otherwise, use the larger numeric type
            numeric_hierarchy = ["byte", "integer", "long", "decimal", "double"]
            left_rank = numeric_hierarchy.index(left_type.type_name) if left_type.type_name in numeric_hierarchy else -1
            right_rank = numeric_hierarchy.index(right_type.type_name) if right_type.type_name in numeric_hierarchy else -1

            if left_rank >= 0 and right_rank >= 0:
                result_type = numeric_hierarchy[max(left_rank, right_rank)]
                return TypeInfo(result_type, is_nullable=False, source=InferenceStrategy.OPERATION)

        # Default to any
        return TypeInfo("any", confidence=0.5, source=InferenceStrategy.OPERATION)

    def _infer_unary_operation_type(self, expr) -> TypeInfo:




        """Infer type from unary operation."""
        operator = expr.operator

        # Logical not returns boolean
        if operator in ["not", "!"]:
            return TypeInfo("boolean", is_nullable=False, source=InferenceStrategy.OPERATION)

        # Numeric operators preserve type
        if operator in ["-", "+", "~"]:
            operand_type = self.infer_expression_type(expr.operand)
            return operand_type

        return TypeInfo("any", confidence=0.5, source=InferenceStrategy.OPERATION)

    def _infer_function_call_type(self, expr) -> TypeInfo:




        """Infer type from function call."""
        # Get function name
        func_name = getattr(expr, "function_name", None) or getattr(expr, "name", None)
        if not func_name:
            return TypeInfo("any", confidence=0.3, source=InferenceStrategy.FUNCTION_RETURN)

        # Check known function return types
        return_type = self.context.get_function_return_type(func_name.lower())
        if return_type:
            return return_type

        # Handle method calls
        if hasattr(expr, "object") and expr.object:
            # For now, return any for method calls
            return TypeInfo("any", confidence=0.4, source=InferenceStrategy.FUNCTION_RETURN)

        return TypeInfo("any", confidence=0.2, source=InferenceStrategy.FUNCTION_RETURN)

    def _infer_array_access_type(self, expr) -> TypeInfo:




        """Infer type from array access."""
        if hasattr(expr, "array"):
            array_type = self.infer_expression_type(expr.array)
            if array_type.is_array:
                # Return element type
                return TypeInfo(
                    array_type.element_type or array_type.type_name, is_nullable=array_type.is_nullable, source=InferenceStrategy.OPERATION,
                )

        return TypeInfo("any", confidence=0.4, source=InferenceStrategy.OPERATION)

    def _infer_field_reference_type(self, expr) -> TypeInfo:




        """Infer type from field reference."""
        # For now, we don't have object type information
        # In a full implementation, we would look up the object type
        # and find the field type
        return TypeInfo("any", confidence=0.3, source=InferenceStrategy.CONTEXT)

    def _infer_ternary_type(self, expr) -> TypeInfo:




        """Infer type from ternary/conditional expression."""
        # Get types of both branches
        true_expr = getattr(expr, "true_expr", None) or getattr(expr, "then_expr", None)
        false_expr = getattr(expr, "false_expr", None) or getattr(expr, "else_expr", None)

        if true_expr and false_expr:
            true_type = self.infer_expression_type(true_expr)
            false_type = self.infer_expression_type(false_expr)

            # Merge the types
            return true_type.merge_with(false_type)

        return TypeInfo("any", confidence=0.3, source=InferenceStrategy.OPERATION)

    def infer_assignment_type(self, target: str, value_expr: Expression) -> TypeInfo:




        """Infer type from assignment and update context."""
        # Infer type from the value
        value_type = self.infer_expression_type(value_expr)

        # Check if variable already has a type
        existing_type = self.context.get_variable_type(target)

        if existing_type:
            # Merge with existing type
            merged_type = existing_type.merge_with(value_type)
            # Reduce confidence if types don't match exactly
            if existing_type.type_name != value_type.type_name:
                merged_type.confidence *= 0.8
            self.context.set_variable_type(target, merged_type)
            return merged_type
        else:
            # New variable
            value_type.source = InferenceStrategy.ASSIGNMENT
            self.context.set_variable_type(target, value_type)
            return value_type

    def infer_declaration_type(self, var_name: str, type_name: str, is_array: bool = False, array_dims: int = 0) -> TypeInfo:




        """Infer type from explicit declaration."""
        type_info = TypeInfo(
            type_name.lower(), is_array=is_array, array_dimensions=array_dims, element_type=type_name.lower() if is_array else None, source=InferenceStrategy.DECLARATION, confidence=1.0,
        )

        self.context.set_variable_type(var_name, type_info)
        return type_info

    def get_type_for_variable(self, var_name: str) -> TypeInfo | None:




        """Get inferred type for a variable."""
        return self.context.get_variable_type(var_name)

    def get_all_variable_types(self) -> dict[str, TypeInfo]:




        """Get all variable types in current context."""
        return dict(self.context.variables)


def infer_type(expr: Expression | PBExpression | Any, context: TypeContext | None = None) -> TypeInfo:








    """Convenience function to infer type of an expression.

    Args:
        expr: Expression or value to infer type from
        context: Optional type context

    Returns:
        TypeInfo object
    """
    engine = TypeInferenceEngine(context)

    # If it's a raw value, infer literal type
    if not hasattr(expr, "__class__") or not hasattr(expr, "__dict__"):
        return engine.infer_literal_type(expr)

    return engine.infer_expression_type(expr)
