"""Tests for expression evaluation system with proper construction."""

import pytest

from model.entities import (
    EvaluationContext,
    ExpressionEvaluator,
    PBArrayAccess,
    PBBinaryOperator,
    PBBooleanLiteral,
    PBCastExpression,
    PBConcatenationOperator,
    PBConstructorCall,
    PBDynamicSqlExpression,
    PBFieldReference,
    PBFunctionCall,
    PBMethodCall,
    PBNullLiteral,
    PBNumberLiteral,
    PBParentExpression,
    PBPowerOperator,
    PBSqlVariableExpression,
    PBStringLiteral,
    PBSuperExpression,
    PBTernaryExpression,
    PBThisExpression,
    PBUnaryOperator,
    PBVariable,
)
from model.utils.errors import ModelError


class TestExpressionEvaluatorFixed:
    """Test expression evaluator with proper object construction."""

    def test_literal_evaluation(self):




        """Test evaluating literals."""
        evaluator = ExpressionEvaluator()

        # Properly construct literals with keyword arguments
        assert evaluator.evaluate(PBNumberLiteral(value=42)) == 42
        assert evaluator.evaluate(PBStringLiteral(value="hello")) == "hello"
        assert evaluator.evaluate(PBBooleanLiteral(value=True)) is True
        assert evaluator.evaluate(PBNullLiteral()) is None

    def test_variable_evaluation(self):




        """Test variable evaluation."""
        context = EvaluationContext()
        context.set_variable("x", 100)
        evaluator = ExpressionEvaluator(context)

        var = PBVariable(name="x")
        assert evaluator.evaluate(var) == 100

    def test_binary_operations(self):




        """Test binary operations."""
        evaluator = ExpressionEvaluator()

        # Arithmetic
        add = PBBinaryOperator(
            left=PBNumberLiteral(value=10),
            operator="+",
            right=PBNumberLiteral(value=5),
        )
        assert evaluator.evaluate(add) == 15

        sub = PBBinaryOperator(
            left=PBNumberLiteral(value=10),
            operator="-",
            right=PBNumberLiteral(value=3),
        )
        assert evaluator.evaluate(sub) == 7

        mul = PBBinaryOperator(
            left=PBNumberLiteral(value=4),
            operator="*",
            right=PBNumberLiteral(value=5),
        )
        assert evaluator.evaluate(mul) == 20

        div = PBBinaryOperator(
            left=PBNumberLiteral(value=20),
            operator="/",
            right=PBNumberLiteral(value=4),
        )
        assert evaluator.evaluate(div) == 5.0

        # Comparison (PowerBuilder style)
        eq = PBBinaryOperator(
            left=PBNumberLiteral(value=5),
            operator="=",
            right=PBNumberLiteral(value=5),
        )
        assert evaluator.evaluate(eq) is True

        ne = PBBinaryOperator(
            left=PBNumberLiteral(value=5),
            operator="<>",
            right=PBNumberLiteral(value=3),
        )
        assert evaluator.evaluate(ne) is True

        # String concatenation
        concat = PBBinaryOperator(
            left=PBStringLiteral(value="Hello "),
            operator="+",
            right=PBStringLiteral(value="World"),
        )
        assert evaluator.evaluate(concat) == "Hello World"

    def test_unary_operations(self):




        """Test unary operations."""
        evaluator = ExpressionEvaluator()

        neg = PBUnaryOperator(
            operator="-",
            operand=PBNumberLiteral(value=42),
        )
        assert evaluator.evaluate(neg) == -42

        pos = PBUnaryOperator(
            operator="+",
            operand=PBNumberLiteral(value=42),
        )
        assert evaluator.evaluate(pos) == 42

        not_op = PBUnaryOperator(
            operator="not",
            operand=PBBooleanLiteral(value=True),
        )
        assert evaluator.evaluate(not_op) is False

    def test_array_access(self):




        """Test array access."""
        context = EvaluationContext()
        context.set_variable("arr", [10, 20, 30, 40])
        evaluator = ExpressionEvaluator(context)

        var = PBVariable(name="arr")

        # PowerBuilder arrays are 1-based
        access = PBArrayAccess(
            array=var,
            indices=[PBNumberLiteral(value=2)],
        )
        assert evaluator.evaluate(access) == 20

    def test_function_call(self):




        """Test function calls."""
        context = EvaluationContext()
        context.functions["add"] = lambda a, b: a + b
        evaluator = ExpressionEvaluator(context)

        call = PBFunctionCall(
            function_name="add",
            arguments=[PBNumberLiteral(value=10), PBNumberLiteral(value=5)],
        )
        assert evaluator.evaluate(call) == 15

    def test_field_reference(self):




        """Test field reference."""
        context = EvaluationContext()
        obj = {"name": "John", "age": 30}
        context.set_variable("person", obj)
        evaluator = ExpressionEvaluator(context)

        var = PBVariable(name="person")
        ref = PBFieldReference(object=var, field_name="name")
        assert evaluator.evaluate(ref) == "John"

    def test_cast_expression(self):




        """Test type casting."""
        evaluator = ExpressionEvaluator()

        # String to int
        cast_int = PBCastExpression(
            expression=PBStringLiteral(value="42"),
            target_type="integer",
        )
        assert evaluator.evaluate(cast_int) == 42

        # Int to string
        cast_str = PBCastExpression(
            expression=PBNumberLiteral(value=42),
            target_type="string",
        )
        assert evaluator.evaluate(cast_str) == "42"

        # To boolean
        cast_bool = PBCastExpression(
            expression=PBNumberLiteral(value=1),
            target_type="boolean",
        )
        assert evaluator.evaluate(cast_bool) is True

    def test_ternary_expression(self):




        """Test ternary conditional."""
        evaluator = ExpressionEvaluator()

        # True condition
        ternary1 = PBTernaryExpression(
            condition=PBBooleanLiteral(value=True),
            true_expr=PBStringLiteral(value="yes"),
            false_expr=PBStringLiteral(value="no"),
        )
        assert evaluator.evaluate(ternary1) == "yes"

        # False condition
        ternary2 = PBTernaryExpression(
            condition=PBBooleanLiteral(value=False),
            true_expr=PBStringLiteral(value="yes"),
            false_expr=PBStringLiteral(value="no"),
        )
        assert evaluator.evaluate(ternary2) == "no"

    def test_constructor_call(self):




        """Test constructor call."""
        context = EvaluationContext()

        # Register a constructor function
        class TestClass:
            def __init__(self, x, y):

                self.x = x
                self.y = y

        context.functions["TestClass"] = TestClass
        evaluator = ExpressionEvaluator(context)

        call = PBConstructorCall(
            class_name="TestClass",
            arguments=[PBNumberLiteral(value=10), PBNumberLiteral(value=20)],
        )
        obj = evaluator.evaluate(call)
        assert obj.x == 10
        assert obj.y == 20

    def test_special_references(self):




        """Test special references (this, parent, super)."""
        context = EvaluationContext()

        # Set up special references
        this_obj = {"name": "current"}
        parent_obj = {"name": "parent"}
        super_obj = {"name": "super"}

        context.set_variable("this", this_obj)
        context.set_variable("parent", parent_obj)
        context.set_variable("super", super_obj)

        evaluator = ExpressionEvaluator(context)

        assert evaluator.evaluate(PBThisExpression()) == this_obj
        assert evaluator.evaluate(PBParentExpression()) == parent_obj
        assert evaluator.evaluate(PBSuperExpression()) == super_obj

    def test_concatenation_operator(self):




        """Test string concatenation operator."""
        evaluator = ExpressionEvaluator()

        concat = PBConcatenationOperator(
            operands=[
                PBStringLiteral(value="Hello"),
                PBStringLiteral(value=" "),
                PBStringLiteral(value="World"),
                PBNumberLiteral(value=123),
            ],
        )
        assert evaluator.evaluate(concat) == "Hello World123"

    def test_power_operator(self):




        """Test power operator."""
        evaluator = ExpressionEvaluator()

        power = PBPowerOperator(
            base=PBNumberLiteral(value=2),
            exponent=PBNumberLiteral(value=3),
        )
        assert evaluator.evaluate(power) == 8

    def test_sql_variable_expression(self):




        """Test SQL variable expression."""
        context = EvaluationContext()
        context.set_variable("user_id", 123)
        evaluator = ExpressionEvaluator(context)

        # Variable in context
        sql_var = PBSqlVariableExpression(variable_name="user_id")
        assert evaluator.evaluate(sql_var) == 123

        # Variable not in context (returns placeholder)
        sql_var2 = PBSqlVariableExpression(variable_name="unknown")
        assert evaluator.evaluate(sql_var2) == ":unknown"

    def test_dynamic_sql_expression(self):




        """Test dynamic SQL expression."""
        context = EvaluationContext()
        context.set_variable("table_name", "users")
        context.set_variable("limit", 10)
        evaluator = ExpressionEvaluator(context)

        sql = PBDynamicSqlExpression(
            sql_parts=[
                "SELECT * FROM ",
                PBVariable(name="table_name"),
                " LIMIT ",
                PBVariable(name="limit"),
            ],
        )
        assert evaluator.evaluate(sql) == "SELECT * FROM users LIMIT 10"

    def test_method_call(self):




        """Test method call expression."""
        context = EvaluationContext()

        # Create object with method
        class TestObject:
            def greet(self, name):

                return f"Hello, {name}!"

        obj = TestObject()
        context.set_variable("obj", obj)
        evaluator = ExpressionEvaluator(context)

        method_call = PBMethodCall(
            object=PBVariable(name="obj"),
            function_name="greet",
            arguments=[PBStringLiteral(value="World")],
        )
        assert evaluator.evaluate(method_call) == "Hello, World!"

    def test_complex_expression(self):




        """Test complex nested expression."""
        context = EvaluationContext()
        context.set_variable("x", 10)
        context.set_variable("y", 5)
        evaluator = ExpressionEvaluator(context)

        # (x + y) * 2
        add = PBBinaryOperator(
            left=PBVariable(name="x"),
            operator="+",
            right=PBVariable(name="y"),
        )
        mul = PBBinaryOperator(
            left=add,
            operator="*",
            right=PBNumberLiteral(value=2),
        )

        assert evaluator.evaluate(mul) == 30

    def test_division_by_zero(self):




        """Test division by zero error."""
        evaluator = ExpressionEvaluator()

        div = PBBinaryOperator(
            left=PBNumberLiteral(value=10),
            operator="/",
            right=PBNumberLiteral(value=0),
        )

        with pytest.raises(ModelError, match="Division by zero"):
            evaluator.evaluate(div)

    def test_unknown_operator(self):




        """Test unknown operator error."""
        evaluator = ExpressionEvaluator()

        expr = PBBinaryOperator(
            left=PBNumberLiteral(value=10),
            operator="??",
            right=PBNumberLiteral(value=5),
        )

        with pytest.raises(ModelError, match="Unknown binary operator"):
            evaluator.evaluate(expr)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
