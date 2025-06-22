"""Test cases for the PBDoUntilLoopNode class.

Ported from reference/moose-pb-parser/PowerBuilder-Parser-Tests/PWBASTVisitorTest.class.st
"""

from model.entities.pb_expression import PBDoUntilLoopNode


def test_do_until_loop_node_creation():



    


    """Test creating a do-until loop node."""
    expression = "a > 10"
    statements = ["a = a + 1", "print(a)"]
    node = PBDoUntilLoopNode(
        expression=expression,
        statements=statements,
        start_position=10,
        stop_position=20,
    )
    assert node.expression == expression
    assert node.statements == statements
    assert node.start_position == 10
    assert node.stop_position == 20


def test_do_until_loop_node_str():



    


    """Test string representation of do-until loop node."""
    node = PBDoUntilLoopNode(
        expression="x > 10",
        statements=["stmt1", "stmt2"],
    )
    assert str(node) == "do until x > 10\nstmt1\nstmt2\nloop"


def test_do_until_loop_node_equality():



    


    """Test do-until loop node equality comparison."""
    expression = "a > 10"
    statements1 = ["a = a + 1", "print(a)"]
    statements2 = ["a = a + 1", "print(a)"]
    node1 = PBDoUntilLoopNode(
        expression=expression,
        statements=statements1,
        start_position=10,
        stop_position=20,
    )
    node2 = PBDoUntilLoopNode(
        expression=expression,
        statements=statements2,
        start_position=10,
        stop_position=20,
    )
    node3 = PBDoUntilLoopNode(
        expression=expression,
        statements=statements1,
        start_position=15,
        stop_position=25,
    )
    node4 = PBDoUntilLoopNode(
        expression="a > 20",
        statements=statements1,
        start_position=10,
        stop_position=20,
    )

    assert node1 == node2  # Same values
    assert node1 != node3  # Different positions
    assert node1 != node4  # Different expression
    assert node1 != "not a node"  # Different type


def test_do_until_loop_node_hash():



    


    """Test do-until loop node hashing."""
    expression = "a > 10"
    statements = ["a = a + 1", "print(a)"]
    node1 = PBDoUntilLoopNode(
        expression=expression,
        statements=statements,
        start_position=10,
        stop_position=20,
    )
    node2 = PBDoUntilLoopNode(
        expression=expression,
        statements=statements,
        start_position=10,
        stop_position=20,
    )

    assert hash(node1) == hash(node2)


def test_do_until_loop_node_visitor():



    


    """Test do-until loop node visitor pattern."""

    class TestVisitor:
        def visit_do_until_loop_node(self, node) -> str:
            
            return "visited"

    expression = "a > 10"
    statements = ["a = a + 1", "print(a)"]
    node = PBDoUntilLoopNode(
        expression=expression,
        statements=statements,
        start_position=10,
        stop_position=20,
    )
    visitor = TestVisitor()

    assert node.accept_visitor(visitor) == "visited"
