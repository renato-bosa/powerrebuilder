"""Integration tests for type inference with expression evaluation."""

import pytest

from model.entities import (
    EvaluationContext,
    ExpressionEvaluator,
    PBVariable,
    PBBinaryOperator,
    PBNumberLiteral,
    PBStringLiteral,
    PBBooleanLiteral,
    PBFunctionCall,
    create_builtin_functions,
)
from model.utils.type_inference import (
    TypeInferenceEngine,
    TypeContext,
    TypeInfo,
)


class TestTypeInferenceIntegration:
    """Test integration between type inference and expression evaluation."""
    
    def test_type_aware_evaluation(self):
        """Test type-aware expression evaluation."""
        # Create shared context
        type_context = TypeContext()
        eval_context = EvaluationContext()
        
        # Initialize with builtin functions
        eval_context.functions.update(create_builtin_functions())
        
        # Create engines
        type_engine = TypeInferenceEngine(type_context)
        evaluator = ExpressionEvaluator(eval_context)
        
        # Simulate variable declaration: integer x = 42
        type_engine.infer_declaration_type("x", "integer")
        eval_context.set_variable("x", 42)
        
        # Create expression: x + 10
        expr = PBBinaryOperator(
            left=PBVariable(name="x"),
            operator="+",
            right=PBNumberLiteral(value=10)
        )
        
        # Infer type
        inferred_type = type_engine.infer_expression_type(expr)
        assert inferred_type.type_name in ["byte", "integer"]  # Could be either
        
        # Evaluate expression
        result = evaluator.evaluate(expr)
        assert result == 52
        
        # Verify type inference matches actual result
        result_type = type_engine.infer_literal_type(result)
        assert result_type.is_compatible_with(inferred_type)
    
    def test_function_return_type_inference(self):
        """Test inferring and validating function return types."""
        # Setup
        type_context = TypeContext()
        eval_context = EvaluationContext()
        eval_context.functions.update(create_builtin_functions())
        
        type_engine = TypeInferenceEngine(type_context)
        evaluator = ExpressionEvaluator(eval_context)
        
        # Set variable
        eval_context.set_variable("name", "john doe")
        type_engine.infer_declaration_type("name", "string")
        
        # Create function call: upper(name)
        upper_call = PBFunctionCall(
            function_name="upper",
            arguments=[PBVariable(name="name")]
        )
        
        # Infer return type
        inferred_type = type_engine.infer_expression_type(upper_call)
        assert inferred_type.type_name == "string"
        
        # Evaluate
        result = evaluator.evaluate(upper_call)
        assert result == "JOHN DOE"
        
        # Verify type correctness
        assert isinstance(result, str)
    
    def test_type_propagation_through_assignments(self):
        """Test type propagation through variable assignments."""
        # Setup
        type_context = TypeContext()
        eval_context = EvaluationContext()
        eval_context.functions.update(create_builtin_functions())
        
        type_engine = TypeInferenceEngine(type_context)
        evaluator = ExpressionEvaluator(eval_context)
        
        # First assignment: x = 42
        x_value = PBNumberLiteral(value=42)
        type_info = type_engine.infer_assignment_type("x", x_value)
        eval_context.set_variable("x", evaluator.evaluate(x_value))
        assert type_info.type_name == "byte"
        
        # Second assignment: y = x * 2
        y_expr = PBBinaryOperator(
            left=PBVariable(name="x"),
            operator="*",
            right=PBNumberLiteral(value=2)
        )
        type_info = type_engine.infer_assignment_type("y", y_expr)
        eval_context.set_variable("y", evaluator.evaluate(y_expr))
        assert type_info.type_name == "byte"
        assert eval_context.get_variable("y") == 84
        
        # Third assignment: z = string(y)
        z_expr = PBFunctionCall(
            function_name="string",
            arguments=[PBVariable(name="y")]
        )
        type_info = type_engine.infer_assignment_type("z", z_expr)
        eval_context.set_variable("z", evaluator.evaluate(z_expr))
        assert type_info.type_name == "string"
        assert eval_context.get_variable("z") == "84"
    
    def test_conditional_type_inference(self):
        """Test type inference in conditional expressions."""
        # Setup
        type_context = TypeContext()
        eval_context = EvaluationContext()
        
        type_engine = TypeInferenceEngine(type_context)
        evaluator = ExpressionEvaluator(eval_context)
        
        # Set variables
        eval_context.set_variable("age", 25)
        type_engine.infer_declaration_type("age", "integer")
        
        # Create condition: age >= 18
        condition = PBBinaryOperator(
            left=PBVariable(name="age"),
            operator=">=",
            right=PBNumberLiteral(value=18)
        )
        
        # Infer condition type
        cond_type = type_engine.infer_expression_type(condition)
        assert cond_type.type_name == "boolean"
        assert not cond_type.is_nullable
        
        # Evaluate condition
        result = evaluator.evaluate(condition)
        assert result is True
    
    def test_array_type_inference_and_evaluation(self):
        """Test array type inference with evaluation."""
        # Setup
        type_context = TypeContext()
        eval_context = EvaluationContext()
        eval_context.functions.update(create_builtin_functions())
        
        type_engine = TypeInferenceEngine(type_context)
        evaluator = ExpressionEvaluator(eval_context)
        
        # Declare array
        array_data = [10, 20, 30, 40]
        eval_context.set_variable("numbers", array_data)
        type_engine.infer_declaration_type("numbers", "integer", is_array=True, array_dims=1)
        
        # Get array type info
        array_type = type_engine.get_type_for_variable("numbers")
        assert array_type.is_array
        assert array_type.array_dimensions == 1
        assert array_type.element_type == "integer"
        
        # Call upperbound(numbers)
        upperbound_call = PBFunctionCall(
            function_name="upperbound",
            arguments=[PBVariable(name="numbers")]
        )
        
        # Infer return type
        bound_type = type_engine.infer_expression_type(upperbound_call)
        assert bound_type.type_name == "integer"
        assert not bound_type.is_nullable
        
        # Evaluate
        result = evaluator.evaluate(upperbound_call)
        assert result == 4
    
    def test_type_coercion_detection(self):
        """Test detecting type coercion in mixed operations."""
        # Setup
        type_context = TypeContext()
        eval_context = EvaluationContext()
        
        type_engine = TypeInferenceEngine(type_context)
        evaluator = ExpressionEvaluator(eval_context)
        
        # Integer + Double operation
        expr = PBBinaryOperator(
            left=PBNumberLiteral(value=10),  # integer
            operator="+",
            right=PBNumberLiteral(value=3.14)  # double
        )
        
        # Infer type - should be double due to coercion
        inferred_type = type_engine.infer_expression_type(expr)
        assert inferred_type.type_name == "double"
        
        # Evaluate
        result = evaluator.evaluate(expr)
        assert result == 13.14
        assert isinstance(result, float)
    
    def test_type_inference_with_nested_expressions(self):
        """Test type inference with complex nested expressions."""
        # Setup
        type_context = TypeContext()
        eval_context = EvaluationContext()
        eval_context.functions.update(create_builtin_functions())
        
        type_engine = TypeInferenceEngine(type_context)
        evaluator = ExpressionEvaluator(eval_context)
        
        # Set variables
        eval_context.set_variable("price", 19.99)
        eval_context.set_variable("quantity", 3)
        type_engine.infer_declaration_type("price", "double")
        type_engine.infer_declaration_type("quantity", "integer")
        
        # Create nested expression: round(price * quantity, 2)
        multiply = PBBinaryOperator(
            left=PBVariable(name="price"),
            operator="*",
            right=PBVariable(name="quantity")
        )
        
        round_call = PBFunctionCall(
            function_name="round",
            arguments=[multiply, PBNumberLiteral(value=2)]
        )
        
        # Infer type of nested expression
        # Multiply should be double (double * integer = double)
        multiply_type = type_engine.infer_expression_type(multiply)
        assert multiply_type.type_name == "double"
        
        # Round returns double
        round_type = type_engine.infer_expression_type(round_call)
        assert round_type.type_name == "double"
        
        # Evaluate
        result = evaluator.evaluate(round_call)
        assert result == 59.97
    
    def test_type_safety_validation(self):
        """Test using type inference to validate type safety."""
        type_engine = TypeInferenceEngine()
        
        # Declare variables with specific types
        type_engine.infer_declaration_type("count", "integer")
        type_engine.infer_declaration_type("name", "string")
        type_engine.infer_declaration_type("active", "boolean")
        
        # Valid operations
        # Integer arithmetic
        int_expr = PBBinaryOperator(
            left=PBVariable(name="count"),
            operator="+",
            right=PBNumberLiteral(value=1)
        )
        int_type = type_engine.infer_expression_type(int_expr)
        assert int_type.type_name in ["byte", "integer"]
        
        # String concatenation
        str_expr = PBBinaryOperator(
            left=PBVariable(name="name"),
            operator="+",
            right=PBStringLiteral(value=" Smith")
        )
        str_type = type_engine.infer_expression_type(str_expr)
        assert str_type.type_name == "string"
        
        # Boolean logic
        bool_expr = PBBinaryOperator(
            left=PBVariable(name="active"),
            operator="and",
            right=PBBooleanLiteral(value=True)
        )
        bool_type = type_engine.infer_expression_type(bool_expr)
        assert bool_type.type_name == "boolean"
        
        # Mixed types that would need runtime checking
        # String + Integer (PowerBuilder allows this with implicit conversion)
        mixed_expr = PBBinaryOperator(
            left=PBVariable(name="name"),
            operator="+",
            right=PBVariable(name="count")
        )
        mixed_type = type_engine.infer_expression_type(mixed_expr)
        # Should infer string since one operand is string
        assert mixed_type.type_name == "string"
    
    def test_get_all_variable_types(self):
        """Test getting all variable types in context."""
        type_engine = TypeInferenceEngine()
        
        # Declare several variables
        type_engine.infer_declaration_type("x", "integer")
        type_engine.infer_declaration_type("y", "double")
        type_engine.infer_declaration_type("name", "string")
        type_engine.infer_declaration_type("data", "blob")
        
        # Get all types
        all_types = type_engine.get_all_variable_types()
        
        assert len(all_types) == 4
        assert all_types["x"].type_name == "integer"
        assert all_types["y"].type_name == "double"
        assert all_types["name"].type_name == "string"
        assert all_types["data"].type_name == "blob"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])