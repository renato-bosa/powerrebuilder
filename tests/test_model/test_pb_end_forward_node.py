"""Test cases for the PBEndForwardNode class.

Ported from reference/moose-pb-parser/PowerBuilder-Parser-Tests/PWBASTVisitorTest.class.st
"""

from model.entities.pb_expression import PBEndForwardNode


def test_end_forward_node_creation():






    """Test creating an end forward node."""
    end_forward = "end forward"
    node = PBEndForwardNode(
        end_forward=end_forward,
        start_position=10,
        stop_position=20,
    )
    assert node.end_forward == end_forward
    assert node.start_position == 10
    assert node.stop_position == 20


def test_end_forward_node_str():






    """Test string representation of end forward node."""
    node = PBEndForwardNode(
        end_forward="end forward",
    )
    assert str(node) == "end forward"


def test_end_forward_node_equality():






    """Test end forward node equality comparison."""
    end_forward1 = "end forward"
    end_forward2 = "end forward"
    end_forward3 = "end forward;"  # Different token
    node1 = PBEndForwardNode(
        end_forward=end_forward1,
        start_position=10,
        stop_position=20,
    )
    node2 = PBEndForwardNode(
        end_forward=end_forward2,
        start_position=10,
        stop_position=20,
    )
    node3 = PBEndForwardNode(
        end_forward=end_forward1,
        start_position=15,
        stop_position=25,
    )
    node4 = PBEndForwardNode(
        end_forward=end_forward3,
        start_position=10,
        stop_position=20,
    )

    assert node1 == node2  # Same values
    assert node1 != node3  # Different positions
    assert node1 != node4  # Different token
    assert node1 != "not a node"  # Different type


def test_end_forward_node_hash():






    """Test end forward node hashing."""
    end_forward = "end forward"
    node1 = PBEndForwardNode(
        end_forward=end_forward,
        start_position=10,
        stop_position=20,
    )
    node2 = PBEndForwardNode(
        end_forward=end_forward,
        start_position=10,
        stop_position=20,
    )

    assert hash(node1) == hash(node2)


def test_end_forward_node_visitor():






    """Test end forward node visitor pattern."""

    class TestVisitor:
        def visit_end_forward_node(self, node) -> str:

            return "visited"

    end_forward = "end forward"
    node = PBEndForwardNode(
        end_forward=end_forward,
        start_position=10,
        stop_position=20,
    )
    visitor = TestVisitor()

    assert node.accept_visitor(visitor) == "visited"
