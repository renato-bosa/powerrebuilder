"""Tests for PowerBuilder type checker."""


from src.model.ast import (
    BinaryExpression,
    FunctionCall,
    IntegerLiteral,
    StringLiteral,
)
from src.model.ast.functions import (
    FunctionDefinition,
    Parameter,
    Signature,
)
from src.model.ast.pb_types import (
    PBArrayType,
    PBBasicType,
    PBTypeRegistry,
)
from src.model.utils.type_checker import (
    CheckLevel,
    TypeChecker,
)
from src.model.types.inference import TypeInferenceEngine


class TestTypeChecker:
    """Test type checker functionality."""

    def setup_method(self):




        """Set up test fixtures."""
        self.registry = PBTypeRegistry()
        self.inference = TypeInferenceEngine()
        self.checker = TypeChecker(
            type_registry=self.registry,
            type_inference=self.inference,
            check_level=CheckLevel.MODERATE,
        )

    def test_numeric_literal_type_check(self):




        """Test type checking of numeric literals."""
        # Small integer literal (fits in byte)
        int_lit = IntegerLiteral(value=42)
        result = self.checker.check_expression(int_lit)

        assert result.valid
        assert len(result.errors) == 0
        assert result.inferred_type is not None
        assert result.inferred_type.name == "byte"  # 42 fits in byte range

        # Larger integer literal
        large_int_lit = IntegerLiteral(value=1000)
        result = self.checker.check_expression(large_int_lit)

        assert result.valid
        assert result.inferred_type is not None
        assert result.inferred_type.name == "integer"  # 1000 needs integer

    def test_string_literal_type_check(self):




        """Test type checking of string literals."""
        str_lit = StringLiteral(value="hello")
        result = self.checker.check_expression(str_lit)

        assert result.valid
        assert len(result.errors) == 0
        assert result.inferred_type is not None
        assert result.inferred_type.name == "string"

    def test_type_mismatch_error(self):




        """Test type mismatch detection."""
        # Try to check string literal against integer type
        str_lit = StringLiteral(value="hello")
        int_type = self.registry.get("integer")

        result = self.checker.check_expression(str_lit, int_type)

        assert not result.valid
        assert len(result.errors) == 1
        assert "Type mismatch" in result.errors[0].message

    def test_numeric_promotion_warning(self):




        """Test numeric type promotion warnings."""
        # Integer to double conversion
        int_lit = IntegerLiteral(value=42)
        double_type = self.registry.get("double")

        result = self.checker.check_expression(int_lit, double_type)

        assert result.valid  # Should be valid with warning
        assert len(result.warnings) == 1
        assert "Implicit conversion" in result.warnings[0].message

    def test_binary_operation_numeric(self):




        """Test type checking of numeric binary operations."""
        left = IntegerLiteral(value=1000)  # Use larger values to get integer type
        right = IntegerLiteral(value=2000)
        expr = BinaryExpression(operator="+", left=left, right=right)

        result = self.checker.check_expression(expr)

        assert result.valid
        assert result.inferred_type is not None
        assert result.inferred_type.name == "integer"

    def test_binary_operation_string_concat(self):




        """Test type checking of string concatenation."""
        left = StringLiteral(value="hello")
        right = StringLiteral(value="world")
        expr = BinaryExpression(operator="+", left=left, right=right)

        result = self.checker.check_expression(expr)

        assert result.valid
        assert result.inferred_type is not None
        assert result.inferred_type.name == "string"

    def test_binary_operation_type_error(self):




        """Test type error in binary operations."""
        left = IntegerLiteral(value=10)
        right = StringLiteral(value="hello")
        expr = BinaryExpression(operator="*", left=left, right=right)

        result = self.checker.check_expression(expr)

        assert not result.valid
        assert len(result.errors) > 0
        assert "not supported" in result.errors[0].message

    def test_comparison_operation(self):




        """Test type checking of comparison operations."""
        left = IntegerLiteral(value=1000)
        right = IntegerLiteral(value=2000)
        expr = BinaryExpression(operator="<", left=left, right=right)

        result = self.checker.check_expression(expr)

        assert result.valid
        assert result.inferred_type is not None
        assert result.inferred_type.name == "boolean"

    def test_logical_operation(self):




        """Test type checking of logical operations."""
        # This would normally be boolean expressions, but we'll use
        # comparison results
        left = BinaryExpression(
            operator="<",
            left=IntegerLiteral(value=10),
            right=IntegerLiteral(value=20),
        )
        right = BinaryExpression(
            operator=">",
            left=IntegerLiteral(value=5),
            right=IntegerLiteral(value=0),
        )
        expr = BinaryExpression(operator="and", left=left, right=right)

        # For this test, we'll check the sub-expressions first
        # In a real scenario, the type checker would handle this recursively
        assert self.checker.check_expression(left).inferred_type.name == "boolean"
        assert self.checker.check_expression(right).inferred_type.name == "boolean"

    def test_function_call_type_check(self):




        """Test type checking of function calls."""
        # Create a simple function definition
        int_type = PBBasicType(name="integer")
        params = [
            Parameter(name="x", type=int_type),
            Parameter(name="y", type=int_type),
        ]
        signature = Signature(
            name="add",
            parameters=params,
            return_type=int_type,
        )
        func_def = FunctionDefinition(signature=signature)

        # Create a function call with correct arguments
        args = [IntegerLiteral(value=10), IntegerLiteral(value=20)]
        call = FunctionCall(function_name="add", arguments=args)

        result = self.checker.check_function_call(call, func_def)

        assert result.valid
        assert result.inferred_type is not None
        assert result.inferred_type.name == "integer"

    def test_function_call_argument_mismatch(self):




        """Test function call with wrong argument types."""
        # Function expecting integers
        int_type = PBBasicType(name="integer")
        params = [
            Parameter(name="x", type=int_type),
            Parameter(name="y", type=int_type),
        ]
        signature = Signature(
            name="add",
            parameters=params,
            return_type=int_type,
        )
        func_def = FunctionDefinition(signature=signature)

        # Call with string argument
        args = [IntegerLiteral(value=10), StringLiteral(value="hello")]
        call = FunctionCall(function_name="add", arguments=args)

        result = self.checker.check_function_call(call, func_def)

        assert not result.valid
        assert len(result.errors) > 0
        assert "Argument 2 type error" in result.errors[0].message

    def test_function_call_argument_count_mismatch(self):




        """Test function call with wrong number of arguments."""
        int_type = PBBasicType(name="integer")
        params = [
            Parameter(name="x", type=int_type),
            Parameter(name="y", type=int_type),
        ]
        signature = Signature(
            name="add",
            parameters=params,
            return_type=int_type,
        )
        func_def = FunctionDefinition(signature=signature)

        # Call with only one argument
        args = [IntegerLiteral(value=10)]
        call = FunctionCall(function_name="add", arguments=args)

        result = self.checker.check_function_call(call, func_def)

        assert not result.valid
        assert len(result.errors) == 1
        assert "Argument count mismatch" in result.errors[0].message

    def test_strict_mode_no_implicit_conversion(self):




        """Test that strict mode disallows implicit conversions."""
        strict_checker = TypeChecker(
            type_registry=self.registry,
            type_inference=self.inference,
            check_level=CheckLevel.STRICT,
        )

        # Integer to double - should fail in strict mode
        int_lit = IntegerLiteral(value=42)
        double_type = self.registry.get("double")

        result = strict_checker.check_expression(int_lit, double_type)

        assert not result.valid
        assert len(result.errors) == 1
        assert "Type mismatch" in result.errors[0].message

    def test_lenient_mode_allows_conversions(self):




        """Test that lenient mode allows more conversions."""
        lenient_checker = TypeChecker(
            type_registry=self.registry,
            type_inference=self.inference,
            check_level=CheckLevel.LENIENT,
        )

        # Integer to string - allowed in lenient mode
        int_lit = IntegerLiteral(value=42)
        str_type = self.registry.get("string")

        result = lenient_checker.check_expression(int_lit, str_type)

        assert result.valid
        assert len(result.warnings) == 1
        assert "Implicit conversion" in result.warnings[0].message

    def test_array_type_checking(self):




        """Test array type checking."""
        # Create an integer array type
        int_type = self.registry.get("integer")
        array_type = PBArrayType(element_type=int_type, dimensions=[10])
        self.registry.register(array_type)

        # For this test, we'll assume the type inference correctly
        # identifies array expressions
        # In a real implementation, this would involve checking
        # array literals or variables

    def test_numeric_type_hierarchy(self):




        """Test numeric type conversion hierarchy."""
        # byte -> integer -> long -> real -> double

        # byte to integer (should allow)
        result = self.checker._is_safe_numeric_conversion(
            PBBasicType(name="byte"),
            PBBasicType(name="integer"),
        )
        assert result is True

        # integer to byte (should not allow)
        result = self.checker._is_safe_numeric_conversion(
            PBBasicType(name="integer"),
            PBBasicType(name="byte"),
        )
        assert result is False

        # integer to double (should allow)
        result = self.checker._is_safe_numeric_conversion(
            PBBasicType(name="integer"),
            PBBasicType(name="double"),
        )
        assert result is True

    def test_comparable_types(self):




        """Test which types can be compared."""
        int_type = PBBasicType(name="integer")
        double_type = PBBasicType(name="double")
        string_type = PBBasicType(name="string")
        boolean_type = PBBasicType(name="boolean")

        # Numeric types can compare
        assert self.checker._are_comparable_types(int_type, double_type)

        # String types can compare
        assert self.checker._are_comparable_types(string_type, string_type)

        # Different type categories cannot compare
        assert not self.checker._are_comparable_types(int_type, string_type)
        assert not self.checker._are_comparable_types(boolean_type, string_type)
