"""Type checking system for PowerBuilder AST validation.

This module provides type checking capabilities for PowerBuilder code,
validating type correctness, compatibility, and safety.
"""

from __future__ import annotations
import logging
from dataclasses import dataclass, field
from enum import Enum, auto
from typing import TYPE_CHECKING, Any, Optional

from src.model.ast.nodes.base import Statement, Expression
from src.model.ast.functions import Function, FunctionDefinition, Parameter
from src.model.symbols.scope import Scope
from src.model.ast.pb_types import (
    PBType, PBBasicType, PBCustomType, PBArrayType, PBTypeRegistry
)
from src.model.types.inference import TypeInferenceEngine, TypeInfo
from src.model.types.errors import ParseErrorRecord

if TYPE_CHECKING:
    pass

logger = logging.getLogger(__name__)


class CheckLevel(Enum):
    """Type checking strictness levels."""
    
    STRICT = auto()    # No implicit conversions allowed
    MODERATE = auto()  # Safe implicit conversions with warnings
    LENIENT = auto()   # Allow most conversions with warnings


@dataclass
class TypeCheckResult:
    """Result of type checking operation."""
    
    valid: bool
    errors: list[ParseErrorRecord] = field(default_factory=list)
    warnings: list[ParseErrorRecord] = field(default_factory=list)
    inferred_type: Optional[PBType] = None
    confidence: float = 1.0
    
    def add_error(self, message: str, **kwargs: Any) -> None:
        """Add an error to the result."""
        error = ParseErrorRecord(
            message=message,
            severity="error",
            **kwargs
        )
        self.errors.append(error)
        self.valid = False
    
    def add_warning(self, message: str, **kwargs: Any) -> None:
        """Add a warning to the result."""
        warning = ParseErrorRecord(
            message=message,
            severity="warning",
            **kwargs
        )
        self.warnings.append(warning)


class TypeChecker:
    """Type checker for PowerBuilder AST nodes."""
    
    def __init__(self,
                 type_registry: PBTypeRegistry,
                 type_inference: Optional[TypeInferenceEngine] = None,
                 check_level: CheckLevel = CheckLevel.MODERATE) -> None:
        """Initialize type checker.
        
        Args:
            type_registry: Registry of known types
            type_inference: Type inference engine
            check_level: Strictness level for type checking
        """
        self.registry = type_registry
        self.inference = type_inference or TypeInferenceEngine()
        self.check_level = check_level
        self._init_type_rules()
    
    def _init_type_rules(self) -> None:
        """Initialize type conversion and compatibility rules."""
        # Numeric type hierarchy (safe conversions)
        self.numeric_hierarchy = [
            "byte", "integer", "long", "decimal", "real", "double"
        ]
        
        # Type categories for comparison operations
        self.comparable_categories = {
            "numeric": {"byte", "integer", "long", "decimal", "real", "double"},
            "string": {"char", "string"},
            "datetime": {"date", "time", "datetime"},
            "boolean": {"boolean"}
        }
        
        # Allowed implicit conversions (lenient mode)
        self.implicit_conversions = {
            "integer": {"string", "double", "real", "long", "decimal"},
            "string": {"integer", "double", "boolean"},  # PowerBuilder allows this
            "boolean": {"integer", "string"},
            "char": {"string"},
            "byte": {"integer", "long", "double", "real", "decimal"},
            "long": {"double", "real", "decimal", "string"},
            "real": {"double", "string"},
            "double": {"string"},
            "decimal": {"double", "string"}
        }
    
    def check_expression(self,
                        expr: Expression,
                        expected_type: Optional[PBType] = None,
                        scope: Optional[Scope] = None) -> TypeCheckResult:
        """Check type of an expression.
        
        Args:
            expr: Expression to check
            expected_type: Expected type (if known)
            scope: Current scope for variable lookup
            
        Returns:
            TypeCheckResult with validation status
        """
        result = TypeCheckResult(valid=True)
        
        # Infer the expression type
        type_info = self.inference.infer_expression_type(expr)
        inferred_type = self._type_info_to_pb_type(type_info)
        result.inferred_type = inferred_type
        result.confidence = type_info.confidence
        
        # If no expected type, just return the inferred type
        if not expected_type:
            return result
        
        # Check type compatibility
        if self._is_compatible(inferred_type, expected_type):
            # Check if conversion is needed
            if inferred_type.name != expected_type.name:
                if self.check_level == CheckLevel.STRICT:
                    result.add_error(
                        f"Type mismatch: expected '{expected_type.name}', got '{inferred_type.name}'",
                        error_code="TYPE_001"
                    )
                else:
                    result.add_warning(
                        f"Implicit conversion from '{inferred_type.name}' to '{expected_type.name}'",
                        error_code="TYPE_002"
                    )
        else:
            result.add_error(
                f"Type mismatch: expected '{expected_type.name}', got '{inferred_type.name}'",
                error_code="TYPE_001"
            )
        
        return result
    
    def check_assignment(self,
                        assignment: Any,  # Changed to Any to work with simplified AST
                        scope: Optional[Scope] = None) -> TypeCheckResult:
        """Check type compatibility in assignment.
        
        Args:
            assignment: Assignment statement to check
            scope: Current scope
            
        Returns:
            TypeCheckResult
        """
        result = TypeCheckResult(valid=True)
        
        # Get target variable type
        target_type = None
        if scope and hasattr(assignment, 'variable'):
            target_type = scope.get_variable(assignment.variable)
        
        # Check the value expression
        value_result = self.check_expression(
            assignment.value,
            expected_type=target_type,
            scope=scope
        )
        
        result.errors.extend(value_result.errors)
        result.warnings.extend(value_result.warnings)
        result.valid = value_result.valid
        
        return result
    
    def check_function_call(self,
                           call: Any,  # Changed to Any to work with simplified AST
                           func_def: FunctionDefinition,
                           scope: Optional[Scope] = None) -> TypeCheckResult:
        """Check function call arguments against function signature.
        
        Args:
            call: Function call to check
            func_def: Function definition
            scope: Current scope
            
        Returns:
            TypeCheckResult
        """
        result = TypeCheckResult(valid=True)
        
        # Check argument count
        expected_count = len(func_def.signature.parameters)
        actual_count = len(call.arguments)
        
        if expected_count != actual_count:
            result.add_error(
                f"Argument count mismatch: expected {expected_count}, got {actual_count}",
                error_code="FUNC_001"
            )
            return result
        
        # Check each argument
        for i, (arg, param) in enumerate(zip(call.arguments, func_def.signature.parameters)):
            arg_result = self.check_expression(
                arg,
                expected_type=param.type,
                scope=scope
            )
            
            if not arg_result.valid:
                for error in arg_result.errors:
                    result.add_error(
                        f"Argument {i + 1} type error: {error.message}",
                        error_code="FUNC_002"
                    )
            
            result.warnings.extend(arg_result.warnings)
        
        # Set return type
        if func_def.signature.return_type:
            result.inferred_type = func_def.signature.return_type
        
        return result
    
    def check_binary_operation(self,
                              expr: Any,  # Changed to Any to work with simplified AST
                              scope: Optional[Scope] = None) -> TypeCheckResult:
        """Check type compatibility in binary operation.
        
        Args:
            expr: Binary expression to check
            scope: Current scope
            
        Returns:
            TypeCheckResult
        """
        result = TypeCheckResult(valid=True)
        
        # Check operands
        left_result = self.check_expression(expr.left, scope=scope)
        right_result = self.check_expression(expr.right, scope=scope)
        
        if not left_result.valid or not right_result.valid:
            result.valid = False
            result.errors.extend(left_result.errors)
            result.errors.extend(right_result.errors)
            return result
        
        left_type = left_result.inferred_type
        right_type = right_result.inferred_type
        operator = expr.operator
        
        # Comparison operators
        if operator in ["==", "!=", "<", ">", "<=", ">=", "=", "<>"]:
            if self._are_comparable_types(left_type, right_type):
                result.inferred_type = self.registry.get("boolean")
            else:
                result.add_error(
                    f"Cannot compare '{left_type.name}' with '{right_type.name}'",
                    error_code="OP_001"
                )
        
        # Logical operators
        elif operator in ["and", "or", "&&", "||"]:
            if left_type.name == "boolean" and right_type.name == "boolean":
                result.inferred_type = self.registry.get("boolean")
            else:
                result.add_error(
                    f"Logical operator '{operator}' requires boolean operands",
                    error_code="OP_002"
                )
        
        # Arithmetic operators
        elif operator in ["+", "-", "*", "/", "%", "^", "**"]:
            # String concatenation
            if operator == "+" and (left_type.name == "string" or right_type.name == "string"):
                result.inferred_type = self.registry.get("string")
            # Numeric operations
            elif self._is_numeric_type(left_type) and self._is_numeric_type(right_type):
                result.inferred_type = self._get_promoted_numeric_type(left_type, right_type)
            else:
                result.add_error(
                    f"Operator '{operator}' not supported between '{left_type.name}' and '{right_type.name}'",
                    error_code="OP_003"
                )
        
        return result
    
    def _type_info_to_pb_type(self, type_info: TypeInfo) -> PBType:
        """Convert TypeInfo to PBType.
        
        Args:
            type_info: Type information from inference
            
        Returns:
            Corresponding PBType
        """
        # Try to get from registry first
        pb_type = self.registry.get(type_info.type_name)
        if pb_type:
            return pb_type
        
        # Create new type if not in registry
        if type_info.is_array:
            element_type = self.registry.get(type_info.element_type or type_info.type_name)
            if element_type:
                return PBArrayType(
                    element_type=element_type,
                    dimensions=[type_info.array_dimensions]
                )
        
        # Default to basic type
        return PBBasicType(name=type_info.type_name)
    
    def _is_compatible(self, from_type: PBType, to_type: PBType) -> bool:
        """Check if from_type can be assigned to to_type.
        
        Args:
            from_type: Source type
            to_type: Target type
            
        Returns:
            True if compatible
        """
        # Same type is always compatible
        if from_type.name == to_type.name:
            return True
        
        # Check if target type accepts source type
        if to_type.accepts(from_type):
            return True
        
        # Check numeric conversions
        if self._is_numeric_type(from_type) and self._is_numeric_type(to_type):
            return self._is_safe_numeric_conversion(from_type, to_type)
        
        # Check implicit conversions based on mode
        if self.check_level != CheckLevel.STRICT:
            allowed = self.implicit_conversions.get(from_type.name, set())
            return to_type.name in allowed
        
        return False
    
    def _is_numeric_type(self, pb_type: PBType) -> bool:
        """Check if type is numeric.
        
        Args:
            pb_type: Type to check
            
        Returns:
            True if numeric
        """
        return pb_type.name in self.comparable_categories["numeric"]
    
    def _is_safe_numeric_conversion(self, from_type: PBType, to_type: PBType) -> bool:
        """Check if numeric conversion is safe (no data loss).
        
        Args:
            from_type: Source numeric type
            to_type: Target numeric type
            
        Returns:
            True if conversion is safe
        """
        try:
            from_idx = self.numeric_hierarchy.index(from_type.name)
            to_idx = self.numeric_hierarchy.index(to_type.name)
            # Safe if converting to larger type
            return from_idx <= to_idx
        except ValueError:
            return False
    
    def _get_promoted_numeric_type(self, type1: PBType, type2: PBType) -> PBType:
        """Get the promoted type for numeric operation.
        
        Args:
            type1: First numeric type
            type2: Second numeric type
            
        Returns:
            Promoted type
        """
        try:
            idx1 = self.numeric_hierarchy.index(type1.name)
            idx2 = self.numeric_hierarchy.index(type2.name)
            promoted_name = self.numeric_hierarchy[max(idx1, idx2)]
            return self.registry.get(promoted_name) or PBBasicType(name=promoted_name)
        except ValueError:
            # Default to double for unknown numeric types
            return self.registry.get("double") or PBBasicType(name="double")
    
    def _are_comparable_types(self, type1: PBType, type2: PBType) -> bool:
        """Check if two types can be compared.
        
        Args:
            type1: First type
            type2: Second type
            
        Returns:
            True if types can be compared
        """
        # Same type can always be compared
        if type1.name == type2.name:
            return True
        
        # Check if both types are in same category
        for category, types in self.comparable_categories.items():
            if type1.name in types and type2.name in types:
                return True
        
        # In lenient mode, allow more comparisons
        if self.check_level == CheckLevel.LENIENT:
            # Allow comparing any with anything
            if type1.name == "any" or type2.name == "any":
                return True
            # Allow string comparison with numbers
            if (type1.name == "string" and self._is_numeric_type(type2)) or \
               (type2.name == "string" and self._is_numeric_type(type1)):
                return True
        
        return False
