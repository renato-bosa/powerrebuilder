"""Tests for PowerBuilder built-in functions."""

import datetime
import pytest

from model.entities import (
    EvaluationContext,
    ExpressionEvaluator,
    PBFunctionCall,
    PBNumberLiteral,
    PBStringLiteral,
    PBVariable,
    evaluate_expression,
)
from model.entities.pb_builtin_functions import create_builtin_functions


class TestPBBuiltinFunctions:
    """Test PowerBuilder built-in functions."""

    @pytest.fixture
    def context_with_builtins(self):
        """Create evaluation context with built-in functions."""
        context = EvaluationContext()
        context.functions.update(create_builtin_functions())
        return context

    def test_string_functions(self, context_with_builtins):
        """Test string manipulation functions."""
        evaluator = ExpressionEvaluator(context_with_builtins)
        
        # len/lenw
        assert evaluator.evaluate(PBFunctionCall(
            function_name="len",
            arguments=[PBStringLiteral(value="Hello")]
        )) == 5
        
        # trim functions
        assert evaluator.evaluate(PBFunctionCall(
            function_name="trim",
            arguments=[PBStringLiteral(value="  Hello  ")]
        )) == "Hello"
        
        assert evaluator.evaluate(PBFunctionCall(
            function_name="ltrim",
            arguments=[PBStringLiteral(value="  Hello")]
        )) == "Hello"
        
        assert evaluator.evaluate(PBFunctionCall(
            function_name="rtrim",
            arguments=[PBStringLiteral(value="Hello  ")]
        )) == "Hello"
        
        # case functions
        assert evaluator.evaluate(PBFunctionCall(
            function_name="upper",
            arguments=[PBStringLiteral(value="hello")]
        )) == "HELLO"
        
        assert evaluator.evaluate(PBFunctionCall(
            function_name="lower",
            arguments=[PBStringLiteral(value="HELLO")]
        )) == "hello"
        
        # mid function (PowerBuilder 1-based)
        assert evaluator.evaluate(PBFunctionCall(
            function_name="mid",
            arguments=[
                PBStringLiteral(value="Hello World"),
                PBNumberLiteral(value=7),
                PBNumberLiteral(value=5)
            ]
        )) == "World"
        
        # pos function (returns 1-based position)
        assert evaluator.evaluate(PBFunctionCall(
            function_name="pos",
            arguments=[
                PBStringLiteral(value="Hello World"),
                PBStringLiteral(value="World")
            ]
        )) == 7
        
        # replace function
        assert evaluator.evaluate(PBFunctionCall(
            function_name="replace",
            arguments=[
                PBStringLiteral(value="Hello World"),
                PBStringLiteral(value="World"),
                PBStringLiteral(value="PowerBuilder")
            ]
        )) == "Hello PowerBuilder"
        
        # left/right functions
        assert evaluator.evaluate(PBFunctionCall(
            function_name="left",
            arguments=[PBStringLiteral(value="Hello"), PBNumberLiteral(value=3)]
        )) == "Hel"
        
        assert evaluator.evaluate(PBFunctionCall(
            function_name="right",
            arguments=[PBStringLiteral(value="Hello"), PBNumberLiteral(value=3)]
        )) == "llo"

    def test_numeric_functions(self, context_with_builtins):
        """Test numeric functions."""
        evaluator = ExpressionEvaluator(context_with_builtins)
        
        # abs
        assert evaluator.evaluate(PBFunctionCall(
            function_name="abs",
            arguments=[PBNumberLiteral(value=-42)]
        )) == 42
        
        # ceiling/floor
        assert evaluator.evaluate(PBFunctionCall(
            function_name="ceiling",
            arguments=[PBNumberLiteral(value=3.14)]
        )) == 4
        
        assert evaluator.evaluate(PBFunctionCall(
            function_name="floor",
            arguments=[PBNumberLiteral(value=3.14)]
        )) == 3
        
        # round
        assert evaluator.evaluate(PBFunctionCall(
            function_name="round",
            arguments=[PBNumberLiteral(value=3.14159), PBNumberLiteral(value=2)]
        )) == 3.14
        
        # truncate
        assert evaluator.evaluate(PBFunctionCall(
            function_name="truncate",
            arguments=[PBNumberLiteral(value=3.14159), PBNumberLiteral(value=2)]
        )) == 3.14
        
        # mod
        assert evaluator.evaluate(PBFunctionCall(
            function_name="mod",
            arguments=[PBNumberLiteral(value=10), PBNumberLiteral(value=3)]
        )) == 1
        
        # sign
        assert evaluator.evaluate(PBFunctionCall(
            function_name="sign",
            arguments=[PBNumberLiteral(value=-5)]
        )) == -1
        
        assert evaluator.evaluate(PBFunctionCall(
            function_name="sign",
            arguments=[PBNumberLiteral(value=0)]
        )) == 0
        
        assert evaluator.evaluate(PBFunctionCall(
            function_name="sign",
            arguments=[PBNumberLiteral(value=5)]
        )) == 1

    def test_type_conversion_functions(self, context_with_builtins):
        """Test type conversion functions."""
        evaluator = ExpressionEvaluator(context_with_builtins)
        
        # int/integer
        assert evaluator.evaluate(PBFunctionCall(
            function_name="int",
            arguments=[PBStringLiteral(value="42")]
        )) == 42
        
        assert evaluator.evaluate(PBFunctionCall(
            function_name="int",
            arguments=[PBNumberLiteral(value=3.14)]
        )) == 3
        
        # real/double
        assert evaluator.evaluate(PBFunctionCall(
            function_name="real",
            arguments=[PBStringLiteral(value="3.14")]
        )) == 3.14
        
        # string
        assert evaluator.evaluate(PBFunctionCall(
            function_name="string",
            arguments=[PBNumberLiteral(value=42)]
        )) == "42"
        
        # boolean
        assert evaluator.evaluate(PBFunctionCall(
            function_name="boolean",
            arguments=[PBStringLiteral(value="true")]
        )) is True
        
        assert evaluator.evaluate(PBFunctionCall(
            function_name="boolean",
            arguments=[PBNumberLiteral(value=1)]
        )) is True
        
        assert evaluator.evaluate(PBFunctionCall(
            function_name="boolean",
            arguments=[PBNumberLiteral(value=0)]
        )) is False

    def test_type_checking_functions(self, context_with_builtins):
        """Test type checking functions."""
        evaluator = ExpressionEvaluator(context_with_builtins)
        context_with_builtins.set_variable("null_var", None)
        context_with_builtins.set_variable("valid_var", "Hello")
        
        # isnull
        assert evaluator.evaluate(PBFunctionCall(
            function_name="isnull",
            arguments=[PBVariable(name="null_var")]
        )) is True
        
        assert evaluator.evaluate(PBFunctionCall(
            function_name="isnull",
            arguments=[PBVariable(name="valid_var")]
        )) is False
        
        # isvalid
        assert evaluator.evaluate(PBFunctionCall(
            function_name="isvalid",
            arguments=[PBVariable(name="valid_var")]
        )) is True
        
        assert evaluator.evaluate(PBFunctionCall(
            function_name="isvalid",
            arguments=[PBVariable(name="null_var")]
        )) is False
        
        # isnumber
        assert evaluator.evaluate(PBFunctionCall(
            function_name="isnumber",
            arguments=[PBStringLiteral(value="3.14")]
        )) is True
        
        assert evaluator.evaluate(PBFunctionCall(
            function_name="isnumber",
            arguments=[PBStringLiteral(value="abc")]
        )) is False
        
        # isdate
        assert evaluator.evaluate(PBFunctionCall(
            function_name="isdate",
            arguments=[PBStringLiteral(value="2023-12-25")]
        )) is True
        
        assert evaluator.evaluate(PBFunctionCall(
            function_name="isdate",
            arguments=[PBStringLiteral(value="not a date")]
        )) is False

    def test_array_functions(self, context_with_builtins):
        """Test array functions."""
        evaluator = ExpressionEvaluator(context_with_builtins)
        context_with_builtins.set_variable("arr", [10, 20, 30, 40])
        context_with_builtins.set_variable("empty_arr", [])
        
        # upperbound (size)
        assert evaluator.evaluate(PBFunctionCall(
            function_name="upperbound",
            arguments=[PBVariable(name="arr")]
        )) == 4
        
        assert evaluator.evaluate(PBFunctionCall(
            function_name="upperbound",
            arguments=[PBVariable(name="empty_arr")]
        )) == 0
        
        # lowerbound (always 1 for non-empty arrays)
        assert evaluator.evaluate(PBFunctionCall(
            function_name="lowerbound",
            arguments=[PBVariable(name="arr")]
        )) == 1
        
        assert evaluator.evaluate(PBFunctionCall(
            function_name="lowerbound",
            arguments=[PBVariable(name="empty_arr")]
        )) == 0

    def test_control_flow_functions(self, context_with_builtins):
        """Test control flow functions."""
        evaluator = ExpressionEvaluator(context_with_builtins)
        
        # if function
        assert evaluator.evaluate(PBFunctionCall(
            function_name="if",
            arguments=[
                PBNumberLiteral(value=1),  # True
                PBStringLiteral(value="yes"),
                PBStringLiteral(value="no")
            ]
        )) == "yes"
        
        assert evaluator.evaluate(PBFunctionCall(
            function_name="if",
            arguments=[
                PBNumberLiteral(value=0),  # False
                PBStringLiteral(value="yes"),
                PBStringLiteral(value="no")
            ]
        )) == "no"
        
        # choose function (1-based index)
        assert evaluator.evaluate(PBFunctionCall(
            function_name="choose",
            arguments=[
                PBNumberLiteral(value=2),
                PBStringLiteral(value="first"),
                PBStringLiteral(value="second"),
                PBStringLiteral(value="third")
            ]
        )) == "second"
        
        # case function
        assert evaluator.evaluate(PBFunctionCall(
            function_name="case",
            arguments=[
                PBNumberLiteral(value=2),
                PBNumberLiteral(value=1), PBStringLiteral(value="one"),
                PBNumberLiteral(value=2), PBStringLiteral(value="two"),
                PBNumberLiteral(value=3), PBStringLiteral(value="three")
            ]
        )) == "two"

    def test_date_functions(self, context_with_builtins):
        """Test date/time functions."""
        evaluator = ExpressionEvaluator(context_with_builtins)
        
        # Create test date
        test_date = datetime.date(2023, 12, 25)
        context_with_builtins.set_variable("test_date", test_date)
        
        # year/month/day
        assert evaluator.evaluate(PBFunctionCall(
            function_name="year",
            arguments=[PBVariable(name="test_date")]
        )) == 2023
        
        assert evaluator.evaluate(PBFunctionCall(
            function_name="month",
            arguments=[PBVariable(name="test_date")]
        )) == 12
        
        assert evaluator.evaluate(PBFunctionCall(
            function_name="day",
            arguments=[PBVariable(name="test_date")]
        )) == 25
        
        # dayname
        assert evaluator.evaluate(PBFunctionCall(
            function_name="dayname",
            arguments=[PBVariable(name="test_date")]
        )) == "Monday"
        
        # daynumber (1=Sunday, 2=Monday, ...)
        assert evaluator.evaluate(PBFunctionCall(
            function_name="daynumber",
            arguments=[PBVariable(name="test_date")]
        )) == 2  # Monday
        
        # daysafter
        date1 = datetime.date(2023, 12, 20)
        date2 = datetime.date(2023, 12, 25)
        context_with_builtins.set_variable("date1", date1)
        context_with_builtins.set_variable("date2", date2)
        
        assert evaluator.evaluate(PBFunctionCall(
            function_name="daysafter",
            arguments=[PBVariable(name="date1"), PBVariable(name="date2")]
        )) == 5
        
        # relativedate
        result = evaluator.evaluate(PBFunctionCall(
            function_name="relativedate",
            arguments=[PBVariable(name="test_date"), PBNumberLiteral(value=5)]
        ))
        assert result == datetime.date(2023, 12, 30)

    def test_expression_with_builtins(self, context_with_builtins):
        """Test complex expressions using built-in functions."""
        from model.entities import PBBinaryOperator
        
        evaluator = ExpressionEvaluator(context_with_builtins)
        context_with_builtins.set_variable("name", "john doe")
        
        # upper(name) + " - " + string(len(name))
        upper_call = PBFunctionCall(
            function_name="upper",
            arguments=[PBVariable(name="name")]
        )
        
        len_call = PBFunctionCall(
            function_name="len",
            arguments=[PBVariable(name="name")]
        )
        
        string_call = PBFunctionCall(
            function_name="string",
            arguments=[len_call]
        )
        
        # Build expression: upper(name) + " - " + string(len(name))
        part1 = PBBinaryOperator(
            left=upper_call,
            operator="+",
            right=PBStringLiteral(value=" - ")
        )
        
        full_expr = PBBinaryOperator(
            left=part1,
            operator="+",
            right=string_call
        )
        
        assert evaluator.evaluate(full_expr) == "JOHN DOE - 8"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])