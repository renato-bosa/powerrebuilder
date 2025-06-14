"""Tests for PowerBuilder expression nodes.

This module contains parametrized tests for all expression-related AST nodes.
"""

import pytest

from model.ast import (
    BinaryExpression,
    Expression,
    ExpressionAction,
    ExpressionList,
    ExpressionWithSign,
    IntervalExpression,
    Literal,
    NotExpression,
    ParenthesedExpression,
    UnaryExpression,
    Variable,
)

# Test data for different expression types
EXPRESSION_CASES = [
    (
        BinaryExpression,
        {
            "left": Literal("1", "number"),
            "operator": "+",
            "right": Literal("2", "number"),
        },
    ),
    (
        UnaryExpression,
        {
            "operator": "-",
            "operand": Literal("1", "number"),
        },
    ),
    (
        Literal,
        {
            "value": "42",
            "type": "number",
        },
    ),
    (
        Variable,
        {
            "name": "count",
            "type": None,
        },
    ),
    (
        ParenthesedExpression,
        {
            "expression": BinaryExpression(
                Literal("1", "number"),
                "+",
                Literal("2", "number"),
            ),
        },
    ),
    (
        NotExpression,
        {
            "expression": Variable("flag", None),
        },
    ),
    (
        IntervalExpression,
        {
            "start": Literal("1", "number"),
            "end": Literal("10", "number"),
        },
    ),
    (
        ExpressionWithSign,
        {
            "sign": "-",
            "expression": Literal("42", "number"),
        },
    ),
]

# Error cases
ERROR_CASES = [
    (
        BinaryExpression,
        {
            "left": None,  # Invalid: left operand cannot be None
            "operator": "+",
            "right": Literal("2", "number"),
        },
    ),
    (
        UnaryExpression,
        {
            "operator": None,  # Invalid: operator cannot be None
            "operand": Literal("1", "number"),
        },
    ),
]


@pytest.mark.ast
@pytest.mark.expressions
@pytest.mark.parametrize(("cls", "attrs"), EXPRESSION_CASES)
def test_expression_creation(cls: type, attrs: dict) -> None:
    """Test expression node creation and attributes."""
    expr = cls(**attrs)
    assert isinstance(expr, Expression)
    for key, value in attrs.items():
        assert getattr(expr, key) == value


@pytest.mark.ast
@pytest.mark.expressions
@pytest.mark.parametrize(("cls", "attrs"), ERROR_CASES)
def test_expression_creation_errors(cls: type, attrs: dict) -> None:
    """Test expression node creation with invalid attributes."""
    with pytest.raises(ValueError):
        cls(**attrs)


@pytest.mark.ast
@pytest.mark.expressions
def test_expression_equality(basic_expression: Expression) -> None:
    """Test expression node equality comparison."""
    expr1 = basic_expression
    expr2 = BinaryExpression(
        Literal("1", "number"),
        "+",
        Literal("2", "number"),
    )
    expr3 = BinaryExpression(
        Literal("2", "number"),
        "+",
        Literal("1", "number"),
    )

    assert expr1 == expr2
    assert expr1 != expr3
    assert hash(expr1) == hash(expr2)
    assert hash(expr1) != hash(expr3)


@pytest.mark.ast
@pytest.mark.expressions
def test_expression_source_tracking(basic_expression: Expression) -> None:
    """Test expression source position tracking."""
    expr = basic_expression
    expr.start_position = 10
    expr.stop_position = 15
    expr.source_file = "test.srw"

    assert expr.start_position == 10
    assert expr.stop_position == 15
    assert expr.source_file == "test.srw"


@pytest.mark.ast
@pytest.mark.expressions
def test_expression_operator_precedence(complex_expression: BinaryExpression) -> None:
    """Test expression operator precedence handling."""
    expr = complex_expression
    assert isinstance(expr.left, BinaryExpression)
    assert expr.operator == "+"
    assert expr.left.operator == "*"
    assert isinstance(expr.right, Literal)
    assert expr.right.value == "3"


@pytest.mark.ast
@pytest.mark.expressions
def test_expression_list() -> None:
    """Test expression list handling."""
    expr_list = ExpressionList(
        [
            Literal("1", "number"),
            Literal("2", "number"),
            Literal("3", "number"),
        ]
    )

    assert len(expr_list.expressions) == 3
    assert all(isinstance(e, Expression) for e in expr_list.expressions)


@pytest.mark.ast
@pytest.mark.expressions
def test_expression_action() -> None:
    """Test expression action handling."""
    action = ExpressionAction(
        Variable("button", None),
        "clicked",
    )

    assert action.target.name == "button"
    assert action.action == "clicked"


@pytest.mark.ast
@pytest.mark.expressions
def test_empty_expression_list() -> None:
    """Test empty expression list handling."""
    expr_list = ExpressionList([])
    assert len(expr_list.expressions) == 0


@pytest.mark.ast
@pytest.mark.expressions
def test_nested_expression_list() -> None:
    """Test nested expression list handling."""
    expr_list = ExpressionList(
        [
            ExpressionList(
                [
                    Literal("1", "number"),
                    Literal("2", "number"),
                ]
            ),
            ExpressionList(
                [
                    Literal("3", "number"),
                    Literal("4", "number"),
                ]
            ),
        ]
    )

    assert len(expr_list.expressions) == 2
    assert all(isinstance(e, ExpressionList) for e in expr_list.expressions)
    assert len(expr_list.expressions[0].expressions) == 2
    assert len(expr_list.expressions[1].expressions) == 2
