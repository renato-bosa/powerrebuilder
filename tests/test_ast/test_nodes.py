"""Tests for PowerBuilder AST nodes.

This module contains parametrized tests for all AST node types.
"""

import pytest

from model.ast import (
    BinaryExpression,
    CustomType,
    Event,
    EventTrigger,
    Expression,
    IntegerLiteral,
    SQLCursor,
    SQLQuery,
    SQLTransaction,
    Statement,
    Type,
    TypeCategory,
    UnaryExpression,
    Variable,
    VariableDeclaration,
)
from model.utils.base import SourceAnchor

# Test data for different node types
EXPRESSION_CASES = [
    (IntegerLiteral, {"value": 42}),
    (
        BinaryExpression,
        {
            "left": IntegerLiteral(value=1),
            "operator": "+",
            "right": IntegerLiteral(value=2),
        },
    ),
    (UnaryExpression, {"operator": "-", "operand": IntegerLiteral(value=1)}),
]

STATEMENT_CASES = [
    (EventTrigger, {"object_name": "button1", "event_name": "clicked", "arguments": []}),
]

# Event is not a Statement, it's an ASTNode, so test it separately
EVENT_CASES = [
    (Event, {"name": "clicked", "parameters": [], "body": None}),
]

TYPE_CASES = [
    (Type, {"name": "integer", "category": TypeCategory.NUMERIC, "is_array": False}),
    (
        Type,
        {
            "name": "string",
            "category": TypeCategory.TEXT,
            "is_array": True,
            "array_bounds": [10],
        },
    ),
    (
        CustomType,
        {"name": "MyType", "category": TypeCategory.CUSTOM, "namespace": "app"},
    ),
]

VARIABLE_CASES = [
    (Variable, {"name": "count"}),
    (VariableDeclaration, {"name": "name", "type": Type("string", TypeCategory.TEXT)}),
]

SQL_CASES = [
    (SQLQuery, {"query": "SELECT * FROM users", "using_clause": None}),
    (SQLCursor, {"name": "cur", "query": "SELECT id FROM orders", "is_dynamic": False}),
    (SQLTransaction, {"action": "commit", "using_clause": None}),
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


@pytest.mark.parametrize(("cls", "attrs"), EVENT_CASES)
def test_event_nodes(cls: type, attrs: dict) -> None:

    
    
    """Test event node creation and attributes."""
    from model.ast import ASTNode
    node = cls(**attrs)
    assert isinstance(node, ASTNode)
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
    node = IntegerLiteral(value=42)
    # Note: source tracking is handled via source_anchor in the new AST
    # SourceAnchor uses line, column, offset, and file_path parameters
    node.source_anchor = SourceAnchor(line=5, column=10, offset=50, file_path="test.srw")

    assert node.source_anchor.line == 5
    assert node.source_anchor.column == 10
    assert node.source_anchor.offset == 50
    assert node.source_anchor.file_path == "test.srw"


# Test node equality and hashing
def test_node_equality() -> None:

    
    
    """Test node equality comparison."""
    node1 = IntegerLiteral(value=42)
    node2 = IntegerLiteral(value=42)
    node3 = IntegerLiteral(value=43)

    assert node1 == node2
    assert node1 != node3
    # Note: These nodes are not hashable since they're not frozen dataclasses
    # If we need hashable nodes, we should make the dataclasses frozen
