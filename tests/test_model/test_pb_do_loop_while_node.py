"""Test cases for the PBDoLoopWhileNode class.

Ported from reference/moose-pb-parser/PowerBuilder-Parser-Tests/PWBASTVisitorTest.class.st
"""

from model.entities.pb_expression import PBDoLoopWhileNode


def test_do_loop_while_node_creation():



    


    """Test creating a do-loop-while node."""
    statements = ["a = a + 1", "print(a)"]
    expression = "a < 10"
    node = PBDoLoopWhileNode(
        statements=statements,
        expression=expression,
        start_position=10,
        stop_position=20,
    )
    assert node.statements == statements
    assert node.expression == expression
    assert node.start_position == 10
    assert node.stop_position == 20


def test_do_loop_while_node_str():



    


    """Test string representation of do-loop-while node."""
    node = PBDoLoopWhileNode(
        statements=["stmt1", "stmt2"],
        expression="x < 10",
    )
    assert str(node) == "do\nstmt1\nstmt2\nloop while x < 10"


def test_do_loop_while_node_equality():



    


    """Test do-loop-while node equality comparison."""
    statements1 = ["a = a + 1", "print(a)"]
    statements2 = ["a = a + 1", "print(a)"]
    expression = "a < 10"
    node1 = PBDoLoopWhileNode(
        statements=statements1,
        expression=expression,
        start_position=10,
        stop_position=20,
    )
    node2 = PBDoLoopWhileNode(
        statements=statements2,
        expression=expression,
        start_position=10,
        stop_position=20,
    )
    node3 = PBDoLoopWhileNode(
        statements=statements1,
        expression=expression,
        start_position=15,
        stop_position=25,
    )
    node4 = PBDoLoopWhileNode(
        statements=statements1,
        expression="a < 20",
        start_position=10,
        stop_position=20,
    )

    assert node1 == node2  # Same values
    assert node1 != node3  # Different positions
    assert node1 != node4  # Different expression
    assert node1 != "not a node"  # Different type


def test_do_loop_while_node_hash():



    


    """Test do-loop-while node hashing."""
    statements = ["a = a + 1", "print(a)"]
    expression = "a < 10"
    node1 = PBDoLoopWhileNode(
        statements=statements,
        expression=expression,
        start_position=10,
        stop_position=20,
    )
    node2 = PBDoLoopWhileNode(
        statements=statements,
        expression=expression,
        start_position=10,
        stop_position=20,
    )

    assert hash(node1) == hash(node2)


def test_do_loop_while_node_visitor():



    


    """Test do-loop-while node visitor pattern."""

    class TestVisitor:
        def visit_do_loop_while_node(self, node) -> str:
            
            return "visited"

    statements = ["a = a + 1", "print(a)"]
    expression = "a < 10"
    node = PBDoLoopWhileNode(
        statements=statements,
        expression=expression,
        start_position=10,
        stop_position=20,
    )
    visitor = TestVisitor()

    assert node.accept_visitor(visitor) == "visited"
