"""Test cases for the PBElseIfNode class.

Ported from reference/moose-pb-parser/PowerBuilder-Parser-Tests/PWBASTVisitorTest.class.st
"""

from model.entities.pb_expression import PBElseIfNode


def test_else_if_node_creation():
    """Test creating an elseif node."""
    expression = "a > 10"
    statements = ["a = a + 1", "print(a)"]
    node = PBElseIfNode(
        expression=expression,
        statements=statements,
        start_position=10,
        stop_position=20,
    )
    assert node.expression == expression
    assert node.statements == statements
    assert node.start_position == 10
    assert node.stop_position == 20


def test_else_if_node_str():
    """Test string representation of elseif node."""
    node = PBElseIfNode(
        expression="x > 10",
        statements=["stmt1", "stmt2"],
    )
    assert str(node) == "elseif x > 10 then\nstmt1\nstmt2"


def test_else_if_node_equality():
    """Test elseif node equality comparison."""
    expression = "a > 10"
    statements1 = ["a = a + 1", "print(a)"]
    statements2 = ["a = a + 1", "print(a)"]
    node1 = PBElseIfNode(
        expression=expression,
        statements=statements1,
        start_position=10,
        stop_position=20,
    )
    node2 = PBElseIfNode(
        expression=expression,
        statements=statements2,
        start_position=10,
        stop_position=20,
    )
    node3 = PBElseIfNode(
        expression=expression,
        statements=statements1,
        start_position=15,
        stop_position=25,
    )
    node4 = PBElseIfNode(
        expression="a > 20",
        statements=statements1,
        start_position=10,
        stop_position=20,
    )

    assert node1 == node2  # Same values
    assert node1 != node3  # Different positions
    assert node1 != node4  # Different expression
    assert node1 != "not a node"  # Different type


def test_else_if_node_hash():
    """Test elseif node hashing."""
    expression = "a > 10"
    statements = ["a = a + 1", "print(a)"]
    node1 = PBElseIfNode(
        expression=expression,
        statements=statements,
        start_position=10,
        stop_position=20,
    )
    node2 = PBElseIfNode(
        expression=expression,
        statements=statements,
        start_position=10,
        stop_position=20,
    )

    assert hash(node1) == hash(node2)


def test_else_if_node_visitor():
    """Test elseif node visitor pattern."""
    class TestVisitor:
        def visit_else_if_node(self, node) -> str:
            return "visited"

    expression = "a > 10"
    statements = ["a = a + 1", "print(a)"]
    node = PBElseIfNode(
        expression=expression,
        statements=statements,
        start_position=10,
        stop_position=20,
    )
    visitor = TestVisitor()

    assert node.accept_visitor(visitor) == "visited"
