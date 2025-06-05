"""Tests for PowerBuilder AST nodes.

This module contains parametrized tests for all AST node types.
"""

import pytest

from model.ast.nodes import (
    BinaryExpression,
    CustomType,
    Event,
    EventTrigger,
    Expression,
    Function,
    Literal,
    Statement,
    Type,
    UnaryExpression,
    Variable,
    VariableDeclaration,
)
from model.ast.sql import (
    SQLCursor,
    SQLQuery,
    SQLTransaction,
)

# Test data for different node types
EXPRESSION_CASES = [
    (Literal, {'value': '42', 'type': 'number'}),
    (BinaryExpression, {'left': Literal('1', 'number'), 'operator': '+', 'right': Literal('2', 'number')}),
    (UnaryExpression, {'operator': '-', 'operand': Literal('1', 'number')}),
]

STATEMENT_CASES = [
    (Event, {'name': 'clicked', 'parameters': [], 'body': []}),
    (EventTrigger, {'event': Event('clicked'), 'arguments': []}),
    (Function, {'name': 'calculate', 'return_type': Type('integer'), 'parameters': []}),
]

TYPE_CASES = [
    (Type, {'name': 'integer', 'is_array': False}),
    (Type, {'name': 'string', 'is_array': True, 'array_bounds': [10]}),
    (CustomType, {'name': 'MyType', 'namespace': 'app'}),
]

VARIABLE_CASES = [
    (Variable, {'name': 'count', 'type': Type('integer')}),
    (VariableDeclaration, {'name': 'name', 'type': Type('string')}),
]

SQL_CASES = [
    (SQLQuery, {'query': 'SELECT * FROM users', 'using_clause': None}),
    (SQLCursor, {'name': 'cur', 'query': 'SELECT id FROM orders', 'is_dynamic': False}),
    (SQLTransaction, {'action': 'commit', 'using_clause': None}),
]


@pytest.mark.parametrize(("cls", "attrs"), EXPRESSION_CASES)
def test_expression_nodes(cls: type, attrs: dict) -> None:
    """Test expression node creation and attributes."""
    node = cls(**attrs)
    assert isinstance(node, Expression)
    for key, value in attrs.items():
        assert getattr(node, key) == value


@pytest.mark.parametrize(("cls", "attrs"), STATEMENT_CASES)
def test_statement_nodes(cls: type, attrs: dict) -> None:
    """Test statement node creation and attributes."""
    node = cls(**attrs)
    assert isinstance(node, Statement)
    for key, value in attrs.items():
        assert getattr(node, key) == value


@pytest.mark.parametrize(("cls", "attrs"), TYPE_CASES)
def test_type_nodes(cls: type, attrs: dict) -> None:
    """Test type node creation and attributes."""
    node = cls(**attrs)
    assert isinstance(node, Type)
    for key, value in attrs.items():
        assert getattr(node, key) == value


@pytest.mark.parametrize(("cls", "attrs"), VARIABLE_CASES)
def test_variable_nodes(cls: type, attrs: dict) -> None:
    """Test variable node creation and attributes."""
    node = cls(**attrs)
    for key, value in attrs.items():
        assert getattr(node, key) == value


@pytest.mark.parametrize(("cls", "attrs"), SQL_CASES)
def test_sql_nodes(cls: type, attrs: dict) -> None:
    """Test SQL node creation and attributes."""
    node = cls(**attrs)
    assert isinstance(node, Statement)
    for key, value in attrs.items():
        assert getattr(node, key) == value


# Test node source tracking
def test_node_source_tracking() -> None:
    """Test source position tracking in nodes."""
    node = Literal('42', 'number')
    node.start_position = 10
    node.stop_position = 12
    node.source_file = 'test.srw'

    assert node.start_position == 10
    assert node.stop_position == 12
    assert node.source_file == 'test.srw'


# Test node equality and hashing
def test_node_equality() -> None:
    """Test node equality comparison."""
    node1 = Literal('42', 'number')
    node2 = Literal('42', 'number')
    node3 = Literal('43', 'number')

    assert node1 == node2
    assert node1 != node3
    # Note: These nodes are not hashable since they're not frozen dataclasses
    # If we need hashable nodes, we should make the dataclasses frozen
