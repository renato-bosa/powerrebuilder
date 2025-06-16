"""Tests for type inference system."""

import pytest

from model.utils.type_inference import (
    TypeInfo,
    TypeContext,
    TypeInferenceEngine,
    InferenceStrategy,
    infer_type,
)
from model.entities.expressions import (
    PBNumberLiteral,
    PBStringLiteral,
    PBBooleanLiteral,
    PBNullLiteral,
    PBVariable,
    PBBinaryOperator,
    PBUnaryOperator,
    PBFunctionCall,
    PBArrayAccess,
    PBFieldReference,
    PBCastExpression,
    PBTernaryExpression,
)


class TestTypeInfo:
    """Test TypeInfo class."""
    
    def test_type_string_representation(self):
        """Test string representation of types."""
        # Basic type
        type_info = TypeInfo("integer", is_nullable=False)
        assert str(type_info) == "integer"
        
        # Nullable type
        type_info = TypeInfo("string", is_nullable=True)
        assert str(type_info) == "string?"
        
        # Array type
        type_info = TypeInfo("integer", is_array=True, array_dimensions=1, element_type="integer")
        assert str(type_info) == "integer[]?"
        
        # Multi-dimensional array
        type_info = TypeInfo("double", is_array=True, array_dimensions=2, element_type="double")
        assert str(type_info) == "double[][]?"
    
    def test_type_compatibility(self):
        """Test type compatibility checking."""
        # Same types are compatible
        int_type = TypeInfo("integer", is_nullable=False)
        int_type2 = TypeInfo("integer", is_nullable=False)
        assert int_type.is_compatible_with(int_type2)
        
        # Null compatible with nullable
        null_type = TypeInfo("null")
        nullable_int = TypeInfo("integer", is_nullable=True)
        assert null_type.is_compatible_with(nullable_int)
        assert nullable_int.is_compatible_with(null_type)
        
        # Null not compatible with non-nullable
        non_nullable = TypeInfo("integer", is_nullable=False)
        assert not null_type.is_compatible_with(non_nullable)
        
        # Any is compatible with everything
        any_type = TypeInfo("any")
        assert any_type.is_compatible_with(int_type)
        assert int_type.is_compatible_with(any_type)
        
        # Numeric types are compatible
        byte_type = TypeInfo("byte")
        long_type = TypeInfo("long")
        assert byte_type.is_compatible_with(long_type)
        
        # String types are compatible
        char_type = TypeInfo("char")
        string_type = TypeInfo("string")
        assert char_type.is_compatible_with(string_type)
        
        # Array compatibility
        int_array = TypeInfo("integer", is_array=True, array_dimensions=1)
        int_array2 = TypeInfo("integer", is_array=True, array_dimensions=1)
        assert int_array.is_compatible_with(int_array2)
        
        # Different dimensions not compatible
        int_array_2d = TypeInfo("integer", is_array=True, array_dimensions=2)
        assert not int_array.is_compatible_with(int_array_2d)
    
    def test_type_merging(self):
        """Test merging type information."""
        # Merge with null returns other type
        int_type = TypeInfo("integer")
        null_type = TypeInfo("null")
        merged = int_type.merge_with(null_type)
        assert merged.type_name == "integer"
        
        # Merge compatible types returns more general
        int_type = TypeInfo("integer", confidence=0.8)
        long_type = TypeInfo("long", confidence=0.9)
        merged = int_type.merge_with(long_type)
        assert merged.type_name == "integer"  # Lower confidence wins
        
        # Merge incompatible types returns any
        int_type = TypeInfo("integer")
        string_type = TypeInfo("string")
        merged = int_type.merge_with(string_type)
        assert merged.type_name == "any"
        assert merged.confidence == 0.5


class TestTypeContext:
    """Test TypeContext class."""
    
    def test_variable_storage(self):
        """Test variable type storage."""
        context = TypeContext()
        int_type = TypeInfo("integer")
        context.set_variable_type("x", int_type)
        
        retrieved = context.get_variable_type("x")
        assert retrieved == int_type
        
        # Unknown variable
        assert context.get_variable_type("y") is None
    
    def test_parent_context_lookup(self):
        """Test parent context lookup."""
        parent = TypeContext()
        parent.set_variable_type("x", TypeInfo("integer"))
        
        child = TypeContext(parent=parent)
        assert child.get_variable_type("x").type_name == "integer"
        
        # Child can override
        child.set_variable_type("x", TypeInfo("string"))
        assert child.get_variable_type("x").type_name == "string"
        assert parent.get_variable_type("x").type_name == "integer"
    
    def test_function_types(self):
        """Test function return type storage."""
        context = TypeContext()
        context.functions["calculate"] = TypeInfo("double")
        
        assert context.get_function_return_type("calculate").type_name == "double"
        assert context.get_function_return_type("unknown") is None


class TestTypeInferenceEngine:
    """Test type inference engine."""
    
    @pytest.fixture
    def engine(self):
        """Create inference engine."""
        return TypeInferenceEngine()
    
    def test_literal_type_inference(self, engine):
        """Test inferring types from literals."""
        # Null
        assert engine.infer_literal_type(None).type_name == "null"
        
        # Boolean
        assert engine.infer_literal_type(True).type_name == "boolean"
        assert not engine.infer_literal_type(True).is_nullable
        
        # Integer types
        assert engine.infer_literal_type(42).type_name == "byte"
        assert engine.infer_literal_type(1000).type_name == "integer"
        assert engine.infer_literal_type(100000).type_name == "long"
        
        # Float
        assert engine.infer_literal_type(3.14).type_name == "double"
        
        # String types
        assert engine.infer_literal_type("A").type_name == "char"
        assert engine.infer_literal_type("Hello").type_name == "string"
        
        # Array
        array_type = engine.infer_literal_type([1, 2, 3])
        assert array_type.is_array
        assert array_type.array_dimensions == 1
        assert array_type.element_type == "byte"
        
        # Blob
        assert engine.infer_literal_type(b"bytes").type_name == "blob"
    
    def test_expression_literal_inference(self, engine):
        """Test inferring types from literal expressions."""
        # Number literal
        num_expr = PBNumberLiteral(value=42)
        type_info = engine.infer_expression_type(num_expr)
        assert type_info.type_name == "byte"
        assert type_info.source == InferenceStrategy.LITERAL
        
        # String literal
        str_expr = PBStringLiteral(value="Hello")
        type_info = engine.infer_expression_type(str_expr)
        assert type_info.type_name == "string"
        
        # Boolean literal
        bool_expr = PBBooleanLiteral(value=True)
        type_info = engine.infer_expression_type(bool_expr)
        assert type_info.type_name == "boolean"
        
        # Null literal
        null_expr = PBNullLiteral()
        type_info = engine.infer_expression_type(null_expr)
        assert type_info.type_name == "null"
        assert type_info.is_nullable
    
    def test_variable_type_inference(self, engine):
        """Test inferring types from variables."""
        # Set variable type
        engine.context.set_variable_type("x", TypeInfo("integer"))
        
        # Infer from variable
        var_expr = PBVariable(name="x")
        type_info = engine.infer_expression_type(var_expr)
        assert type_info.type_name == "integer"
        
        # Unknown variable
        var_expr2 = PBVariable(name="unknown")
        type_info = engine.infer_expression_type(var_expr2)
        assert type_info.type_name == "any"
        assert type_info.confidence == 0.3
    
    def test_binary_operation_inference(self, engine):
        """Test inferring types from binary operations."""
        # Comparison returns boolean
        comp_expr = PBBinaryOperator(
            left=PBNumberLiteral(value=5),
            operator="<",
            right=PBNumberLiteral(value=10)
        )
        type_info = engine.infer_expression_type(comp_expr)
        assert type_info.type_name == "boolean"
        assert not type_info.is_nullable
        
        # Logical operation returns boolean
        logic_expr = PBBinaryOperator(
            left=PBBooleanLiteral(value=True),
            operator="and",
            right=PBBooleanLiteral(value=False)
        )
        type_info = engine.infer_expression_type(logic_expr)
        assert type_info.type_name == "boolean"
        
        # String concatenation
        concat_expr = PBBinaryOperator(
            left=PBStringLiteral(value="Hello"),
            operator="+",
            right=PBStringLiteral(value=" World")
        )
        type_info = engine.infer_expression_type(concat_expr)
        assert type_info.type_name == "string"
        
        # Numeric addition
        add_expr = PBBinaryOperator(
            left=PBNumberLiteral(value=5),
            operator="+",
            right=PBNumberLiteral(value=10)
        )
        type_info = engine.infer_expression_type(add_expr)
        assert type_info.type_name == "byte"
        
        # Division always returns double
        div_expr = PBBinaryOperator(
            left=PBNumberLiteral(value=10),
            operator="/",
            right=PBNumberLiteral(value=3)
        )
        type_info = engine.infer_expression_type(div_expr)
        assert type_info.type_name == "double"
        
        # Mixed numeric types
        mixed_expr = PBBinaryOperator(
            left=PBNumberLiteral(value=5),  # byte
            operator="*",
            right=PBNumberLiteral(value=3.14)  # double
        )
        type_info = engine.infer_expression_type(mixed_expr)
        assert type_info.type_name == "double"
    
    def test_unary_operation_inference(self, engine):
        """Test inferring types from unary operations."""
        # Logical not returns boolean
        not_expr = PBUnaryOperator(
            operator="not",
            operand=PBBooleanLiteral(value=True)
        )
        type_info = engine.infer_expression_type(not_expr)
        assert type_info.type_name == "boolean"
        
        # Numeric negation preserves type
        neg_expr = PBUnaryOperator(
            operator="-",
            operand=PBNumberLiteral(value=42)
        )
        type_info = engine.infer_expression_type(neg_expr)
        assert type_info.type_name == "byte"
    
    def test_function_call_inference(self, engine):
        """Test inferring types from function calls."""
        # Built-in function
        len_call = PBFunctionCall(
            function_name="len",
            arguments=[PBStringLiteral(value="Hello")]
        )
        type_info = engine.infer_expression_type(len_call)
        assert type_info.type_name == "integer"
        assert not type_info.is_nullable
        
        # String function
        upper_call = PBFunctionCall(
            function_name="upper",
            arguments=[PBStringLiteral(value="hello")]
        )
        type_info = engine.infer_expression_type(upper_call)
        assert type_info.type_name == "string"
        
        # Unknown function
        unknown_call = PBFunctionCall(
            function_name="custom_func",
            arguments=[]
        )
        type_info = engine.infer_expression_type(unknown_call)
        assert type_info.type_name == "any"
        assert type_info.confidence == 0.2
    
    def test_array_access_inference(self, engine):
        """Test inferring types from array access."""
        # Set up array variable
        array_type = TypeInfo("integer", is_array=True, array_dimensions=1, element_type="integer")
        engine.context.set_variable_type("arr", array_type)
        
        # Array access returns element type
        array_expr = PBArrayAccess(
            array=PBVariable(name="arr"),
            indices=[PBNumberLiteral(value=1)]
        )
        type_info = engine.infer_expression_type(array_expr)
        assert type_info.type_name == "integer"
        assert not type_info.is_array
    
    def test_cast_expression_inference(self, engine):
        """Test inferring types from cast expressions."""
        cast_expr = PBCastExpression(
            expression=PBStringLiteral(value="42"),
            target_type="integer"
        )
        type_info = engine.infer_expression_type(cast_expr)
        assert type_info.type_name == "integer"
    
    def test_ternary_expression_inference(self, engine):
        """Test inferring types from ternary expressions."""
        # Same types
        ternary1 = PBTernaryExpression(
            condition=PBBooleanLiteral(value=True),
            true_expr=PBNumberLiteral(value=5),
            false_expr=PBNumberLiteral(value=10)
        )
        type_info = engine.infer_expression_type(ternary1)
        assert type_info.type_name == "byte"
        
        # Different but compatible types
        ternary2 = PBTernaryExpression(
            condition=PBBooleanLiteral(value=True),
            true_expr=PBNumberLiteral(value=5),  # byte
            false_expr=PBNumberLiteral(value=1000)  # integer
        )
        type_info = engine.infer_expression_type(ternary2)
        assert type_info.type_name in ["byte", "integer"]  # One of them
        
        # Incompatible types
        ternary3 = PBTernaryExpression(
            condition=PBBooleanLiteral(value=True),
            true_expr=PBNumberLiteral(value=5),
            false_expr=PBStringLiteral(value="Hello")
        )
        type_info = engine.infer_expression_type(ternary3)
        assert type_info.type_name == "any"
    
    def test_assignment_inference(self, engine):
        """Test inferring types from assignments."""
        # New variable
        type_info = engine.infer_assignment_type("x", PBNumberLiteral(value=42))
        assert type_info.type_name == "byte"
        assert type_info.source == InferenceStrategy.ASSIGNMENT
        assert engine.context.get_variable_type("x").type_name == "byte"
        
        # Existing variable with same type
        type_info = engine.infer_assignment_type("x", PBNumberLiteral(value=100))
        assert type_info.type_name == "byte"
        
        # Existing variable with different type
        type_info = engine.infer_assignment_type("x", PBStringLiteral(value="Hello"))
        assert type_info.type_name == "any"  # Merged to any
        assert type_info.confidence < 1.0  # Reduced confidence
    
    def test_declaration_inference(self, engine):
        """Test inferring types from declarations."""
        # Simple type
        type_info = engine.infer_declaration_type("x", "integer")
        assert type_info.type_name == "integer"
        assert type_info.source == InferenceStrategy.DECLARATION
        assert type_info.confidence == 1.0
        
        # Array type
        type_info = engine.infer_declaration_type("arr", "double", is_array=True, array_dims=2)
        assert type_info.type_name == "double"
        assert type_info.is_array
        assert type_info.array_dimensions == 2
        assert type_info.element_type == "double"


class TestInferTypeFunction:
    """Test the convenience infer_type function."""
    
    def test_infer_raw_value(self):
        """Test inferring type from raw values."""
        assert infer_type(42).type_name == "byte"
        assert infer_type(3.14).type_name == "double"
        assert infer_type("Hello").type_name == "string"
        assert infer_type(True).type_name == "boolean"
        assert infer_type(None).type_name == "null"
        assert infer_type([1, 2, 3]).is_array
    
    def test_infer_expression(self):
        """Test inferring type from expressions."""
        expr = PBBinaryOperator(
            left=PBNumberLiteral(value=5),
            operator="+",
            right=PBNumberLiteral(value=10)
        )
        assert infer_type(expr).type_name == "byte"
    
    def test_infer_with_context(self):
        """Test inferring with context."""
        context = TypeContext()
        context.set_variable_type("x", TypeInfo("string"))
        
        var_expr = PBVariable(name="x")
        type_info = infer_type(var_expr, context)
        assert type_info.type_name == "string"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])