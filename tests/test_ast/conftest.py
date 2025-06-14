"""Test fixtures for PowerBuilder AST tests."""

import pytest

from model.ast import (
    BinaryExpression,
    Event,
    Literal,
    SQLQuery,
    Type,
    TypeCategory,
)

collect_ignore = [
    "test_events.py",
    "test_expressions.py",
    "test_sql.py",
    "test_statements.py",
    "test_types.py",
]


@pytest.fixture
def basic_expression():
    """Basic binary expression: 1 + 2."""
    return BinaryExpression(
        Literal("1", "number"),
        "+",
        Literal("2", "number"),
    )


@pytest.fixture
def complex_expression():
    """Complex expression: (1 * 2) + 3."""
    return BinaryExpression(
        BinaryExpression(
            Literal("1", "number"),
            "*",
            Literal("2", "number"),
        ),
        "+",
        Literal("3", "number"),
    )


@pytest.fixture
def basic_event():
    """Basic event: clicked()."""
    return Event("clicked", [], [])


@pytest.fixture
def parameterized_event():
    """Event with parameters: itemchanged(row: integer, col: integer)."""
    return Event(
        "itemchanged",
        [
            {"name": "row", "type": Type("integer", TypeCategory.NUMERIC)},
            {"name": "col", "type": Type("integer", TypeCategory.NUMERIC)},
        ],
        [],
    )


@pytest.fixture
def basic_sql():
    """Basic SQL query: SELECT * FROM users."""
    return SQLQuery("SELECT * FROM users", None)


@pytest.fixture
def parameterized_sql():
    """SQL query with parameters: SELECT * FROM users WHERE id = ?."""
    return SQLQuery("SELECT * FROM users WHERE id = ?", "SQLCA")
