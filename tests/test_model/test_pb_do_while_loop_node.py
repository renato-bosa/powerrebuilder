"""Test cases for the PBDoWhileLoopNode class.

Ported from reference/moose-pb-parser/PowerBuilder-Parser-Tests/PWBASTVisitorTest.class.st
"""

from model.entities.pb_expression import PBDoWhileLoopNode


def test_do_while_loop_node_creation():
    """Test creating a do-while loop node."""
    expression = "a < 10"
    statements = ["a = a + 1", "print(a)"]
    node = PBDoWhileLoopNode(
        expression=expression,
        statements=statements,
        start_position=10,
        stop_position=20,
    )
    assert node.expression == expression
    assert node.statements == statements
    assert node.start_position == 10
    assert node.stop_position == 20


def test_do_while_loop_node_str():
    """Test string representation of do-while loop node."""
    node = PBDoWhileLoopNode(
        expression="x < 10",
        statements=["stmt1", "stmt2"],
    )
    assert str(node) == "do while x < 10\nstmt1\nstmt2\nloop"


def test_do_while_loop_node_equality():
    """Test do-while loop node equality comparison."""
    expression = "a < 10"
    statements1 = ["a = a + 1", "print(a)"]
    statements2 = ["a = a + 1", "print(a)"]
    node1 = PBDoWhileLoopNode(
        expression=expression,
        statements=statements1,
        start_position=10,
        stop_position=20,
    )
    node2 = PBDoWhileLoopNode(
        expression=expression,
        statements=statements2,
        start_position=10,
        stop_position=20,
    )
    node3 = PBDoWhileLoopNode(
        expression=expression,
        statements=statements1,
        start_position=15,
        stop_position=25,
    )
    node4 = PBDoWhileLoopNode(
        expression="a < 20",
        statements=statements1,
        start_position=10,
        stop_position=20,
    )

    assert node1 == node2  # Same values
    assert node1 != node3  # Different positions
    assert node1 != node4  # Different expression
    assert node1 != "not a node"  # Different type


def test_do_while_loop_node_hash():
    """Test do-while loop node hashing."""
    expression = "a < 10"
    statements = ["a = a + 1", "print(a)"]
    node1 = PBDoWhileLoopNode(
        expression=expression,
        statements=statements,
        start_position=10,
        stop_position=20,
    )
    node2 = PBDoWhileLoopNode(
        expression=expression,
        statements=statements,
        start_position=10,
        stop_position=20,
    )

    assert hash(node1) == hash(node2)


def test_do_while_loop_node_visitor():
    """Test do-while loop node visitor pattern."""
    class TestVisitor:
        def visit_do_while_loop_node(self, node) -> str:
            return "visited"

    expression = "a < 10"
    statements = ["a = a + 1", "print(a)"]
    node = PBDoWhileLoopNode(
        expression=expression,
        statements=statements,
        start_position=10,
        stop_position=20,
    )
    visitor = TestVisitor()

    assert node.accept_visitor(visitor) == "visited"
