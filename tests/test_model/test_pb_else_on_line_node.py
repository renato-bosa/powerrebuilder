"""Test cases for the PBElseOnLineNode class.

Ported from reference/moose-pb-parser/PowerBuilder-Parser-Tests/PWBASTVisitorTest.class.st
"""

from model.entities.pb_expression import PBElseOnLineNode


def test_else_on_line_node_creation():



    


    """Test creating an else-on-line node."""
    statement = "return 0"
    node = PBElseOnLineNode(
        statement=statement,
        start_position=10,
        stop_position=20,
    )
    assert node.statement == statement
    assert node.start_position == 10
    assert node.stop_position == 20


def test_else_on_line_node_str():



    


    """Test string representation of else-on-line node."""
    node = PBElseOnLineNode(
        statement="return 0",
    )
    assert str(node) == "else return 0"


def test_else_on_line_node_equality():



    


    """Test else-on-line node equality comparison."""
    statement1 = "return 0"
    statement2 = "return 0"
    statement3 = "return 1"
    node1 = PBElseOnLineNode(
        statement=statement1,
        start_position=10,
        stop_position=20,
    )
    node2 = PBElseOnLineNode(
        statement=statement2,
        start_position=10,
        stop_position=20,
    )
    node3 = PBElseOnLineNode(
        statement=statement1,
        start_position=15,
        stop_position=25,
    )
    node4 = PBElseOnLineNode(
        statement=statement3,
        start_position=10,
        stop_position=20,
    )

    assert node1 == node2  # Same values
    assert node1 != node3  # Different positions
    assert node1 != node4  # Different statement
    assert node1 != "not a node"  # Different type


def test_else_on_line_node_hash():



    


    """Test else-on-line node hashing."""
    statement = "return 0"
    node1 = PBElseOnLineNode(
        statement=statement,
        start_position=10,
        stop_position=20,
    )
    node2 = PBElseOnLineNode(
        statement=statement,
        start_position=10,
        stop_position=20,
    )

    assert hash(node1) == hash(node2)


def test_else_on_line_node_visitor():



    


    """Test else-on-line node visitor pattern."""

    class TestVisitor:
        def visit_else_on_line_node(self, node) -> str:
            
            return "visited"

    statement = "return 0"
    node = PBElseOnLineNode(
        statement=statement,
        start_position=10,
        stop_position=20,
    )
    visitor = TestVisitor()

    assert node.accept_visitor(visitor) == "visited"
