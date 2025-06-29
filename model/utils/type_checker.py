"""Type checking system for PowerBuilder AST validation.

This module provides type checking capabilities for PowerBuilder code,
validating type correctness, compatibility, and safety.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from enum import Enum, auto
from typing import TYPE_CHECKING, Any

from model.ast.pb_types import (
    PBArrayType, PBType, PBTypeRegistry, )
from model.utils.errors import ValidationError
from src.model.types.inference import TypeInfo, TypeInferenceEngine

if TYPE_CHECKING:
    from model.expressions import (BinaryExpression, Expression)
    from src.model.ast.nodes.base import (Assignment, FunctionCall, Statement)
    from model.ast.functions import Function, FunctionDefinition, Parameter
    from src.model.symbols.scope import Scope

logger = logging.getLogger(__name__)


class TypeCheckError(ValidationError):
    """Type checking error."""

    def __init__(self, message: str, node: Any = None, **kwargs) -> None:


        """Initialize type check error.

        Args:
            message: Error message
            node: AST node where error occurred
            **kwargs: Additional context
        """
        super().__init__(message, node=node, **kwargs)
        self.node = node


class TypeCheckWarning:
    """Type checking warning."""

    def __init__(self, message: str, node: Any = None) -> None:
        self.message = message
        self.node = node


class CheckLevel(Enum):
    """Type checking strictness levels."""

    STRICT = auto()      # All type errors are failures
    MODERATE = auto()    # Some implicit conversions allowed
    LENIENT = auto()     # Most conversions allowed, warnings only


@dataclass
class TypeCheckResult:
    """Result of type checking operation."""

    valid: bool
    errors: list[TypeCheckError] = field(default_factory=list)
    warnings: list[TypeCheckWarning] = field(default_factory=list)
    inferred_type: PBType | None = None

    def add_error(self, message: str, node: Any = None) -> None:


        """Add an error to the result."""
        self.valid = False
        self.errors.append(TypeCheckError(message, node=node))

    def add_warning(self, message: str, node: Any = None) -> None:


        """Add a warning to the result."""
        self.warnings.append(TypeCheckWarning(message, node))


class TypeChecker:
    """Type checker for PowerBuilder AST nodes."""

    def __init__(
        self, type_registry: PBTypeRegistry | None = None, type_inference: TypeInferenceEngine | None = None, check_level: CheckLevel = CheckLevel.MODERATE, ):


        """Initialize type checker.

        Args:
            type_registry: Registry of available types
            type_inference: Type inference engine
            check_level: Strictness level for type checking
        """
        self.registry = type_registry or PBTypeRegistry()
        self.inference = type_inference or TypeInferenceEngine()
        self.check_level = check_level
        self._current_scope: Scope | None = None
        self._current_function: Function | None = None

    def check_statement(
        self, statement: Statement, scope: Scope | None = None
    ) -> TypeCheckResult:




        """Type check a statement.

        Args:
            statement: Statement to check
            scope: Current scope

        Returns:
            Type check result
        """
        self._current_scope = scope
        result = TypeCheckResult(valid=True)

        # Dispatch based on statement type
        statement_type = type(statement).__name__
        method_name = f"_check_{statement_type.lower()}"
        method = getattr(self, method_name, self._check_generic_statement)

        try:
            method(statement, result)
        except Exception as e:
            result.add_error(f"Type check failed: {e}", statement)

        return result

    def check_expression(
        self, expression: Expression, expected_type: PBType | None = None
    ) -> TypeCheckResult:




        """Type check an expression.

        Args:
            expression: Expression to check
            expected_type: Expected type (if known)

        Returns:
            Type check result
        """
        result = TypeCheckResult(valid=True)

        # Get inferred type
        inferred = self.inference.infer_expression_type(expression)
        if inferred:
            pb_type = self._type_info_to_pb_type(inferred)
            result.inferred_type = pb_type

            # Check against expected type if provided
            if expected_type and pb_type and not expected_type.accepts(pb_type):
                if self._can_implicit_convert(pb_type, expected_type):
                    result.add_warning(
                        f"Implicit conversion from {pb_type.name} to {expected_type.name}", expression, )
                else:
                    result.add_error(
                        f"Type mismatch: expected {expected_type.name}, got {pb_type.name}", expression, )

        # Dispatch based on expression type
        expr_type = type(expression).__name__
        method_name = f"_check_{expr_type.lower()}"
        method = getattr(self, method_name, self._check_generic_expression)

        try:
            method(expression, result)
        except Exception as e:
            result.add_error(f"Expression type check failed: {e}", expression)

        return result

    def check_function_call(
        self, call: FunctionCall, function: FunctionDefinition
    ) -> TypeCheckResult:




        """Type check a function call.

        Args:
            call: Function call to check
            function: Function definition

        Returns:
            Type check result
        """
        result = TypeCheckResult(valid=True)

        # Get function signature
        if not hasattr(function, "signature") or not function.signature:
            result.add_error("Function has no signature", function)
            return result

        signature = function.signature

        # Check argument count
        if len(call.arguments) != len(signature.parameters):
            result.add_error(
                f"Argument count mismatch: expected {len(signature.parameters)}, "
                f"got {len(call.arguments)}", call, )
            return result

        # Check each argument
        for i, (arg, param) in enumerate(zip(call.arguments, signature.parameters)):
            param_type = self._get_parameter_type(param)
            if param_type:
                arg_result = self.check_expression(arg, param_type)
                if not arg_result.valid:
                    result.add_error(
                        f"Argument {i + 1} type error: {arg_result.errors[0].message}", arg, )
                result.warnings.extend(arg_result.warnings)

        # Set return type
        if hasattr(signature, "return_type") and signature.return_type:
            if hasattr(signature.return_type, "name"):
                # It's already a PBType
                result.inferred_type = signature.return_type
            else:
                # It's a string type name
                result.inferred_type = self._resolve_type(signature.return_type)

        return result

    def check_assignment(self, assignment: Assignment) -> TypeCheckResult:




        """Type check an assignment.

        Args:
            assignment: Assignment to check

        Returns:
            Type check result
        """
        result = TypeCheckResult(valid=True)

        # Get target type
        target_type = None
        if hasattr(assignment, "target"):
            target_info = self.inference.infer_type(assignment.target, self._current_scope)
            if target_info:
                target_type = self._type_info_to_pb_type(target_info)

        # Check value against target type
        if hasattr(assignment, "value") and target_type:
            value_result = self.check_expression(assignment.value, target_type)
            result.errors.extend(value_result.errors)
            result.warnings.extend(value_result.warnings)
            result.valid = value_result.valid

        return result

    def check_binary_operation(
        self, expr: BinaryExpression
    ) -> TypeCheckResult:




        """Type check a binary operation.

        Args:
            expr: Binary expression to check

        Returns:
            Type check result
        """
        result = TypeCheckResult(valid=True)

        # Check operands
        left_result = self.check_expression(expr.left)
        right_result = self.check_expression(expr.right)

        result.errors.extend(left_result.errors + right_result.errors)
        result.warnings.extend(left_result.warnings + right_result.warnings)

        if not (left_result.valid and right_result.valid):
            result.valid = False
            return result

        # Check operator compatibility
        if left_result.inferred_type and right_result.inferred_type:
            op_result = self._check_operator_compatibility(
                expr.operator, left_result.inferred_type, right_result.inferred_type, )

            if not op_result[0]:
                result.add_error(op_result[1], expr)
            else:
                result.inferred_type = op_result[2]

        return result

    def check_array_access(
        self, array_expr: Expression, indices: list[Expression]
    ) -> TypeCheckResult:




        """Type check array access.

        Args:
            array_expr: Array expression
            indices: Index expressions

        Returns:
            Type check result
        """
        result = TypeCheckResult(valid=True)

        # Check array expression
        array_result = self.check_expression(array_expr)
        if not array_result.valid:
            return array_result

        # Verify it's an array type
        if array_result.inferred_type and not isinstance(
            array_result.inferred_type, PBArrayType
        ):
            result.add_error(
                f"Cannot index non-array type {array_result.inferred_type.name}", array_expr, )
            return result

        # Check indices are numeric
        for i, index in enumerate(indices):
            index_result = self.check_expression(index)
            if index_result.inferred_type and not self._is_numeric_type(
                index_result.inferred_type
            ):
                result.add_error(
                    f"Array index {i + 1} must be numeric type", index
                )

        # Result type is element type
        if isinstance(array_result.inferred_type, PBArrayType):
            result.inferred_type = array_result.inferred_type.element_type

        return result

    # Helper methods

    def _check_generic_statement(
        self, statement: Statement, result: TypeCheckResult
    ) -> None:




        """Generic statement checking."""
        # Default: no specific checks
        pass

    def _check_generic_expression(
        self, expression: Expression, result: TypeCheckResult
    ) -> None:




        """Generic expression checking."""
        # Default: no specific checks
        pass

    def _check_binaryexpression(
        self, expression: BinaryExpression, result: TypeCheckResult
    ) -> None:




        """Check binary expression."""
        # Delegate to check_binary_operation
        op_result = self.check_binary_operation(expression)
        result.errors.extend(op_result.errors)
        result.warnings.extend(op_result.warnings)
        result.valid = op_result.valid
        if op_result.inferred_type:
            result.inferred_type = op_result.inferred_type

    def _type_info_to_pb_type(self, info: TypeInfo) -> PBType | None:




        """Convert TypeInfo to PBType."""
        if info.is_array:
            element_type = self.registry.get_type(info.element_type or info.type_name)
            if element_type:
                return PBArrayType(
                    element_type=element_type, dimensions=[0] * info.array_dimensions, )

        return self.registry.get_type(info.type_name)

    def _resolve_type(self, type_name: str) -> PBType | None:




        """Resolve a type name to a PBType."""
        return self.registry.get_type(type_name)

    def _get_parameter_type(self, param: Parameter) -> PBType | None:




        """Get the type of a parameter."""
        if hasattr(param, "type") and param.type:
            # If it's already a PBType, return it
            if hasattr(param.type, "name"):
                return param.type
            # If it's a string, resolve it
            if isinstance(param.type, str):
                return self._resolve_type(param.type)
        return None

    def _can_implicit_convert(
        self, from_type: PBType, to_type: PBType
    ) -> bool:




        """Check if implicit conversion is allowed."""
        if self.check_level == CheckLevel.STRICT:
            return False

        # Numeric promotions
        if self._is_numeric_type(from_type) and self._is_numeric_type(to_type):
            return self._is_safe_numeric_conversion(from_type, to_type)

        # String conversions
        if to_type.name == "string":
            return self.check_level == CheckLevel.LENIENT

        # Null to nullable
        if from_type.name == "null" and to_type.nullable:
            return True

        return False

    def _is_numeric_type(self, pb_type: PBType) -> bool:




        """Check if type is numeric."""
        numeric_types = {
            "byte", "integer", "long", "real", "double", "decimal", "uint", "ulong"
        }
        return pb_type.name in numeric_types

    def _is_safe_numeric_conversion(
        self, from_type: PBType, to_type: PBType
    ) -> bool:




        """Check if numeric conversion is safe (no data loss)."""
        # Define numeric type hierarchy
        type_order = {
            "byte": 0, "integer": 1, "uint": 1, "long": 2, "ulong": 2, "real": 3, "double": 4, "decimal": 4, }

        from_order = type_order.get(from_type.name, -1)
        to_order = type_order.get(to_type.name, -1)

        # Allow promotion to higher precision
        return from_order >= 0 and to_order >= from_order

    def _check_operator_compatibility(
        self, operator: str, left_type: PBType, right_type: PBType
    ) -> tuple[bool, str, PBType | None]:




        """Check if operator is compatible with operand types.

        Returns:
            Tuple of (is_valid, error_message, result_type)
        """
        # Arithmetic operators
        if operator in ["+", "-", "*", "/", "^", "mod"]:
            if self._is_numeric_type(left_type) and self._is_numeric_type(right_type):
                # Result is the wider type
                result_type = self._get_wider_numeric_type(left_type, right_type)
                return (True, "", result_type)
            elif operator == "+" and (
                left_type.name == "string" or right_type.name == "string"
            ):
                # String concatenation
                return (True, "", self.registry.get_type("string"))
            else:
                return (
                    False, f"Operator {operator} not supported for types "
                    f"{left_type.name} and {right_type.name}", None, )

        # Comparison operators
        elif operator in ["<", ">", "<=", ">=", "=", "<>"]:
            if self._are_comparable_types(left_type, right_type):
                return (True, "", self.registry.get_type("boolean"))
            else:
                return (
                    False, f"Cannot compare {left_type.name} with {right_type.name}", None, )

        # Logical operators
        elif operator in ["and", "or", "not"]:
            if left_type.name == "boolean" and right_type.name == "boolean":
                return (True, "", self.registry.get_type("boolean"))
            else:
                return (
                    False, f"Logical operator {operator} requires boolean operands", None, )

        else:
            return (False, f"Unknown operator {operator}", None)

    def _get_wider_numeric_type(
        self, type1: PBType, type2: PBType
    ) -> PBType:




        """Get the wider of two numeric types."""
        # Simplified logic - in practice would be more complex
        if type1.name == "double" or type2.name == "double":
            return self.registry.get_type("double")
        elif type1.name == "real" or type2.name == "real":
            return self.registry.get_type("real")
        elif type1.name == "long" or type2.name == "long":
            return self.registry.get_type("long")
        else:
            return self.registry.get_type("integer")

    def _are_comparable_types(self, type1: PBType, type2: PBType) -> bool:




        """Check if two types can be compared."""
        # Same type
        if type1.name == type2.name:
            return True

        # Numeric types
        if self._is_numeric_type(type1) and self._is_numeric_type(type2):
            return True

        # String types
        string_types = {"char", "string"}
        if type1.name in string_types and type2.name in string_types:
            return True

        # Date/time types
        datetime_types = {"date", "time", "datetime"}
        if type1.name in datetime_types and type2.name in datetime_types:
            return True

        # Null comparisons
        if type1.name == "null" or type2.name == "null":
            return True

        return False


__all__ = ["TypeChecker", "TypeCheckResult", "TypeCheckError", "CheckLevel"]