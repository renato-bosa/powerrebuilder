"""Tests for expression evaluation system."""

import pytest

from model.entities import (
    EvaluationContext,
    ExpressionEvaluator,
    PBArrayAccess,
    PBBinaryOperator,
    PBBooleanLiteral,
    PBCastExpression,
    PBFieldReference,
    PBFunctionCall,
    PBNullLiteral,
    PBNumberLiteral,
    PBStringLiteral,
    PBTernaryExpression,
    PBUnaryOperator,
    PBVariable,
    evaluate_expression,
)
from model.utils.errors import ModelError


class TestEvaluationContext:
    """Test evaluation context."""

    def test_variable_storage(self):




        """Test variable storage and retrieval."""
        context = EvaluationContext()
        context.set_variable("x", 42)
        assert context.get_variable("x") == 42

    def test_undefined_variable(self):




        """Test accessing undefined variable."""
        context = EvaluationContext()
        with pytest.raises(ModelError, match="Undefined variable: y"):
            context.get_variable("y")

    def test_parent_context(self):




        """Test parent context lookup."""
        parent = EvaluationContext()
        parent.set_variable("x", 10)

        child = EvaluationContext(parent=parent)
        assert child.get_variable("x") == 10

        # Child can override parent
        child.set_variable("x", 20)
        assert child.get_variable("x") == 20
        assert parent.get_variable("x") == 10

    def test_function_storage(self):




        """Test function storage."""
        context = EvaluationContext()
        def func(x):

            return x * 2
        context.functions["double"] = func
        assert context.get_function("double")(5) == 10

class TestExpressionEvaluator:
    """Test expression evaluator."""

    def test_literal_evaluation(self):




        """Test evaluating literals."""
        evaluator = ExpressionEvaluator()

        assert evaluator.evaluate(PBNumberLiteral(42)) == 42
        assert evaluator.evaluate(PBStringLiteral("hello")) == "hello"
        assert evaluator.evaluate(PBBooleanLiteral(True)) is True
        assert evaluator.evaluate(PBNullLiteral()) is None

    def test_variable_evaluation(self):




        """Test variable evaluation."""
        context = EvaluationContext()
        context.set_variable("x", 100)
        evaluator = ExpressionEvaluator(context)

        var = PBVariable()
        var.name = "x"
        assert evaluator.evaluate(var) == 100

    def test_binary_operations(self):




        """Test binary operations."""
        evaluator = ExpressionEvaluator()

        # Arithmetic
        add = PBBinaryOperator(PBNumberLiteral(10), "+", PBNumberLiteral(5))
        assert evaluator.evaluate(add) == 15

        sub = PBBinaryOperator(PBNumberLiteral(10), "-", PBNumberLiteral(3))
        assert evaluator.evaluate(sub) == 7

        mul = PBBinaryOperator(PBNumberLiteral(4), "*", PBNumberLiteral(5))
        assert evaluator.evaluate(mul) == 20

        div = PBBinaryOperator(PBNumberLiteral(20), "/", PBNumberLiteral(4))
        assert evaluator.evaluate(div) == 5.0

        # Comparison
        eq = PBBinaryOperator(PBNumberLiteral(5), "=", PBNumberLiteral(5))
        assert evaluator.evaluate(eq) is True

        ne = PBBinaryOperator(PBNumberLiteral(5), "<>", PBNumberLiteral(3))
        assert evaluator.evaluate(ne) is True

        # String concatenation
        concat = PBBinaryOperator(PBStringLiteral("Hello "), "+", PBStringLiteral("World"))
        assert evaluator.evaluate(concat) == "Hello World"

    def test_unary_operations(self):




        """Test unary operations."""
        evaluator = ExpressionEvaluator()

        neg = PBUnaryOperator("-", PBNumberLiteral(42))
        assert evaluator.evaluate(neg) == -42

        pos = PBUnaryOperator("+", PBNumberLiteral(42))
        assert evaluator.evaluate(pos) == 42

        not_op = PBUnaryOperator("not", PBBooleanLiteral(True))
        assert evaluator.evaluate(not_op) is False

    def test_array_access(self):




        """Test array access."""
        context = EvaluationContext()
        context.set_variable("arr", [10, 20, 30, 40])
        evaluator = ExpressionEvaluator(context)

        var = PBVariable()
        var.name = "arr"

        # PowerBuilder arrays are 1-based
        access = PBArrayAccess()
        access.array = var
        access.indices = [PBNumberLiteral(2)]
        assert evaluator.evaluate(access) == 20

    def test_function_call(self):




        """Test function calls."""
        context = EvaluationContext()
        context.functions["add"] = lambda a, b: a + b
        evaluator = ExpressionEvaluator(context)

        call = PBFunctionCall("add", [PBNumberLiteral(10), PBNumberLiteral(5)])
        assert evaluator.evaluate(call) == 15

    def test_field_reference(self):




        """Test field reference."""
        context = EvaluationContext()
        obj = {"name": "John", "age": 30}
        context.set_variable("person", obj)
        evaluator = ExpressionEvaluator(context)

        var = PBVariable()
        var.name = "person"

        ref = PBFieldReference(var, "name")
        assert evaluator.evaluate(ref) == "John"

    def test_cast_expression(self):




        """Test type casting."""
        evaluator = ExpressionEvaluator()

        # String to int
        cast_int = PBCastExpression(PBStringLiteral("42"), "integer")
        assert evaluator.evaluate(cast_int) == 42

        # Int to string
        cast_str = PBCastExpression(PBNumberLiteral(42), "string")
        assert evaluator.evaluate(cast_str) == "42"

        # To boolean
        cast_bool = PBCastExpression(PBNumberLiteral(1), "boolean")
        assert evaluator.evaluate(cast_bool) is True

    def test_ternary_expression(self):




        """Test ternary conditional."""
        evaluator = ExpressionEvaluator()

        # True condition
        ternary1 = PBTernaryExpression(
            PBBooleanLiteral(True),
            PBStringLiteral("yes"),
            PBStringLiteral("no"),
        )
        assert evaluator.evaluate(ternary1) == "yes"

        # False condition
        ternary2 = PBTernaryExpression(
            PBBooleanLiteral(False),
            PBStringLiteral("yes"),
            PBStringLiteral("no"),
        )
        assert evaluator.evaluate(ternary2) == "no"

    def test_complex_expression(self):




        """Test complex nested expression."""
        context = EvaluationContext()
        context.set_variable("x", 10)
        context.set_variable("y", 5)
        evaluator = ExpressionEvaluator(context)

        # (x + y) * 2
        var_x = PBVariable()
        var_x.name = "x"
        var_y = PBVariable()
        var_y.name = "y"

        add = PBBinaryOperator(var_x, "+", var_y)
        mul = PBBinaryOperator(add, "*", PBNumberLiteral(2))

        assert evaluator.evaluate(mul) == 30

class TestEvaluateFunction:
    """Test the evaluate_expression convenience function."""

    def test_simple_evaluation(self):




        """Test simple expression evaluation."""
        result = evaluate_expression(
            PBNumberLiteral(42),
            variables={"x": 10},
        )
        assert result == 42

    def test_with_variables(self):




        """Test evaluation with variables."""
        var = PBVariable()
        var.name = "x"

        result = evaluate_expression(
            var,
            variables={"x": 100},
        )
        assert result == 100

    def test_with_functions(self):




        """Test evaluation with functions."""
        call = PBFunctionCall("square", [PBNumberLiteral(5)])

        result = evaluate_expression(
            call,
            functions={"square": lambda x: x * x},
        )
        assert result == 25
