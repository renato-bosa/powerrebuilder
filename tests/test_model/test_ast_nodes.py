"""Tests for AST node model classes.

Tests the AST node hierarchy and functionality in the model package.
"""

from dataclasses import fields, is_dataclass

import pytest

from model.ast import (
    BinaryExpression,
    Event,
    EventTrigger,
    Expression,
    Literal,
    NodeKind,
    PBNode,
    Statement,
    UnaryExpression,
)


class TestPBNode:
    """Test the base PBNode class."""

    def test_pbnode_is_dataclass(self):
        """Test that PBNode is a dataclass."""
        assert is_dataclass(PBNode)

    def test_pbnode_fields(self):
        """Test PBNode has expected fields."""
        field_names = {f.name for f in fields(PBNode)}
        # PBNode should have position tracking fields
        expected_fields = {"start_position", "stop_position", "source_file"}
        assert expected_fields.issubset(field_names)

    def test_pbnode_creation(self):
        """Test creating a PBNode instance."""
        node = PBNode()
        assert node.start_position is None
        assert node.stop_position is None
        assert node.source_file is None

    def test_pbnode_has_kind_property(self):
        """Test that PBNode has kind property."""
        node = PBNode()
        assert hasattr(node, "kind")
        assert node.kind == NodeKind.UNKNOWN


class TestExpression:
    """Test the Expression node class."""

    def test_expression_is_pbnode(self):
        """Test that Expression inherits from PBNode."""
        assert issubclass(Expression, PBNode)

    def test_expression_creation(self):
        """Test creating an Expression instance."""
        expr = Expression()
        assert isinstance(expr, Expression)
        assert isinstance(expr, PBNode)

    def test_expression_kind(self):
        """Test Expression node kind."""
        expr = Expression()
        assert expr.kind == NodeKind.EXPRESSION


class TestStatement:
    """Test the Statement node class."""

    def test_statement_is_pbnode(self):
        """Test that Statement inherits from PBNode."""
        assert issubclass(Statement, PBNode)

    def test_statement_creation(self):
        """Test creating a Statement instance."""
        stmt = Statement()
        assert isinstance(stmt, Statement)
        assert isinstance(stmt, PBNode)

    def test_statement_kind(self):
        """Test Statement node kind."""
        stmt = Statement()
        assert stmt.kind == NodeKind.STATEMENT


class TestLiteral:
    """Test the Literal node class."""

    def test_literal_is_expression(self):
        """Test that Literal inherits from Expression."""
        assert issubclass(Literal, Expression)

    def test_literal_fields(self):
        """Test Literal has expected fields."""
        field_names = {f.name for f in fields(Literal)}
        assert "value" in field_names
        assert "type" in field_names

    def test_literal_creation(self):
        """Test creating Literal instances."""
        # Integer literal
        int_lit = Literal(value=42, type="integer")
        assert int_lit.value == 42
        assert int_lit.type == "integer"

        # String literal
        str_lit = Literal(value="hello", type="string")
        assert str_lit.value == "hello"
        assert str_lit.type == "string"

        # Boolean literal
        bool_lit = Literal(value=True, type="boolean")
        assert bool_lit.value is True
        assert bool_lit.type == "boolean"

    def test_literal_kind(self):
        """Test Literal node kind."""
        # Test integer literal
        int_lit = Literal(value=42, type="integer")
        assert int_lit.kind == NodeKind.INTEGER_LITERAL

        # Test string literal
        str_lit = Literal(value="hello", type="string")
        assert str_lit.kind == NodeKind.STRING_LITERAL

        # Test boolean literal
        bool_lit = Literal(value=True, type="boolean")
        assert bool_lit.kind == NodeKind.BOOLEAN_LITERAL


class TestBinaryExpression:
    """Test the BinaryExpression node class."""

    def test_binary_expression_is_expression(self):
        """Test that BinaryExpression inherits from Expression."""
        assert issubclass(BinaryExpression, Expression)

    def test_binary_expression_fields(self):
        """Test BinaryExpression has expected fields."""
        field_names = {f.name for f in fields(BinaryExpression)}
        expected_fields = {"left", "operator", "right"}
        assert expected_fields.issubset(field_names)

    def test_binary_expression_creation(self):
        """Test creating BinaryExpression instances."""
        left = Literal(value=10, type="integer")
        right = Literal(value=20, type="integer")

        # Addition
        add_expr = BinaryExpression(left=left, operator="+", right=right)
        assert add_expr.left == left
        assert add_expr.operator == "+"
        assert add_expr.right == right

        # Comparison
        comp_expr = BinaryExpression(left=left, operator=">", right=right)
        assert comp_expr.operator == ">"

    def test_binary_expression_kind(self):
        """Test BinaryExpression node kind."""
        expr = BinaryExpression(
            left=Literal(value=1, type="integer"),
            operator="+",
            right=Literal(value=2, type="integer"),
        )
        assert expr.kind == NodeKind.BINARY_EXPRESSION


class TestUnaryExpression:
    """Test the UnaryExpression node class."""

    def test_unary_expression_is_expression(self):
        """Test that UnaryExpression inherits from Expression."""
        assert issubclass(UnaryExpression, Expression)

    def test_unary_expression_fields(self):
        """Test UnaryExpression has expected fields."""
        field_names = {f.name for f in fields(UnaryExpression)}
        expected_fields = {"operator", "operand"}
        assert expected_fields.issubset(field_names)

    def test_unary_expression_creation(self):
        """Test creating UnaryExpression instances."""
        operand = Literal(value=42, type="integer")

        # Negation
        neg_expr = UnaryExpression(operator="-", operand=operand)
        assert neg_expr.operator == "-"
        assert neg_expr.operand == operand

        # Logical not
        not_expr = UnaryExpression(
            operator="not",
            operand=Literal(value=True, type="boolean"),
        )
        assert not_expr.operator == "not"

    def test_unary_expression_kind(self):
        """Test UnaryExpression node kind."""
        expr = UnaryExpression(
            operator="-",
            operand=Literal(value=42, type="integer"),
        )
        assert expr.kind == NodeKind.UNARY_EXPRESSION


class TestEvent:
    """Test the Event node class."""

    def test_event_is_statement(self):
        """Test that Event inherits from Statement."""
        assert issubclass(Event, Statement)

    def test_event_fields(self):
        """Test Event has expected fields."""
        field_names = {f.name for f in fields(Event)}
        expected_fields = {"name", "parameters", "body"}
        assert expected_fields.issubset(field_names)

    def test_event_creation(self):
        """Test creating Event instances."""
        event = Event(
            name="clicked",
            parameters=[],
            body=[],
        )
        assert event.name == "clicked"
        assert event.parameters == []
        assert event.body == []

    def test_event_kind(self):
        """Test Event node kind."""
        event = Event(name="test", parameters=[], body=[])
        assert event.kind == NodeKind.EVENT


class TestEventTrigger:
    """Test the EventTrigger node class."""

    def test_event_trigger_is_statement(self):
        """Test that EventTrigger inherits from Statement."""
        assert issubclass(EventTrigger, Statement)

    def test_event_trigger_fields(self):
        """Test EventTrigger has expected fields."""
        field_names = {f.name for f in fields(EventTrigger)}
        expected_fields = {"event", "arguments"}
        assert expected_fields.issubset(field_names)

    def test_event_trigger_creation(self):
        """Test creating EventTrigger instances."""
        event = Event(
            name="clicked",
            parameters=[],
            body=[],
        )
        trigger = EventTrigger(
            event=event,
            arguments=[],
        )
        assert trigger.event == event
        assert trigger.arguments == []

    def test_event_trigger_kind(self):
        """Test EventTrigger node kind."""
        event = Event(name="test", parameters=[], body=[])
        trigger = EventTrigger(
            event=event,
            arguments=[],
        )
        assert trigger.kind == NodeKind.EVENT_TRIGGER


class TestNodeKindEnum:
    """Test the NodeKind enumeration."""

    def test_node_kind_values(self):
        """Test that NodeKind has expected values."""
        expected_kinds = [
            "UNKNOWN",
            "EXPRESSION",
            "STATEMENT",
            "BINARY_EXPRESSION",
            "UNARY_EXPRESSION",
            "EVENT",
            "EVENT_TRIGGER",
            "INTEGER_LITERAL",
            "STRING_LITERAL",
            "BOOLEAN_LITERAL",
            "REAL_LITERAL",
            "DATE_LITERAL",
            "TIME_LITERAL",
            "NULL_LITERAL",
            "LITERAL_EXPRESSION",
        ]

        for kind_name in expected_kinds:
            assert hasattr(NodeKind, kind_name)

    def test_node_kind_categories(self):
        """Test NodeKind category methods."""
        # Test is_expression - names must end with _EXPRESSION or _LITERAL
        assert (
            not NodeKind.EXPRESSION.is_expression()
        )  # Just 'EXPRESSION' doesn't match
        assert NodeKind.LITERAL_EXPRESSION.is_expression()
        assert NodeKind.BINARY_EXPRESSION.is_expression()
        assert NodeKind.UNARY_EXPRESSION.is_expression()
        assert NodeKind.INTEGER_LITERAL.is_expression()
        assert NodeKind.STRING_LITERAL.is_expression()
        assert not NodeKind.STATEMENT.is_statement()  # Just 'STATEMENT' doesn't match

        # Test is_statement - names must end with _STATEMENT or be specific loop types
        assert NodeKind.ASSIGNMENT_STATEMENT.is_statement()
        assert NodeKind.IF_STATEMENT.is_statement()
        assert NodeKind.FOR_LOOP.is_statement()
        assert NodeKind.WHILE_LOOP.is_statement()
        assert not NodeKind.EXPRESSION.is_statement()

        # Test is_declaration - names must end with _DECLARATION
        assert NodeKind.EVENT_DECLARATION.is_declaration()
        assert NodeKind.VARIABLE_DECLARATION.is_declaration()
        assert not NodeKind.EXPRESSION.is_declaration()
        assert not NodeKind.EVENT.is_declaration()  # Just 'EVENT' doesn't match


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
