"""Test cases for the PBElseNode class.

Ported from reference/moose-pb-parser/PowerBuilder-Parser-Tests/PWBASTVisitorTest.class.st
"""

from model.entities.pb_expression import PBElseNode


def test_else_node_creation():



    


    """Test creating an else node."""
    statements = ["a = a + 1", "print(a)"]
    node = PBElseNode(
        statements=statements,
        start_position=10,
        stop_position=20,
    )
    assert node.statements == statements
    assert node.start_position == 10
    assert node.stop_position == 20


def test_else_node_str():



    


    """Test string representation of else node."""
    node = PBElseNode(
        statements=["stmt1", "stmt2"],
    )
    assert str(node) == "else\nstmt1\nstmt2"


def test_else_node_equality():



    


    """Test else node equality comparison."""
    statements1 = ["a = a + 1", "print(a)"]
    statements2 = ["a = a + 1", "print(a)"]
    statements3 = ["b = b + 1", "print(b)"]
    node1 = PBElseNode(
        statements=statements1,
        start_position=10,
        stop_position=20,
    )
    node2 = PBElseNode(
        statements=statements2,
        start_position=10,
        stop_position=20,
    )
    node3 = PBElseNode(
        statements=statements1,
        start_position=15,
        stop_position=25,
    )
    node4 = PBElseNode(
        statements=statements3,
        start_position=10,
        stop_position=20,
    )

    assert node1 == node2  # Same values
    assert node1 != node3  # Different positions
    assert node1 != node4  # Different statements
    assert node1 != "not a node"  # Different type


def test_else_node_hash():



    


    """Test else node hashing."""
    statements = ["a = a + 1", "print(a)"]
    node1 = PBElseNode(
        statements=statements,
        start_position=10,
        stop_position=20,
    )
    node2 = PBElseNode(
        statements=statements,
        start_position=10,
        stop_position=20,
    )

    assert hash(node1) == hash(node2)


def test_else_node_visitor():



    


    """Test else node visitor pattern."""

    class TestVisitor:
        def visit_else_node(self, node) -> str:
            
            return "visited"

    statements = ["a = a + 1", "print(a)"]
    node = PBElseNode(
        statements=statements,
        start_position=10,
        stop_position=20,
    )
    visitor = TestVisitor()

    assert node.accept_visitor(visitor) == "visited"
