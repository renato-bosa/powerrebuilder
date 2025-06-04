"""Test cases for the PBEventNameNode class.

Ported from reference/moose-pb-parser/PowerBuilder-Parser-Tests/PWBASTVisitorTest.class.st
"""
from model.entities.pb_expression import PBEventNameNode


def test_event_name_node_creation():
    """Test creating an event name node."""
    event_name = "clicked"
    node = PBEventNameNode(
        event_name=event_name,
        start_position=10,
        stop_position=20,
    )
    assert node.event_name == event_name
    assert node.start_position == 10
    assert node.stop_position == 20


def test_event_name_node_str():
    """Test string representation of event name node."""
    node = PBEventNameNode(
        event_name="clicked",
    )
    assert str(node) == "clicked"


def test_event_name_node_equality():
    """Test event name node equality comparison."""
    event_name1 = "clicked"
    event_name2 = "clicked"
    event_name3 = "doubleClicked"
    node1 = PBEventNameNode(
        event_name=event_name1,
        start_position=10,
        stop_position=20,
    )
    node2 = PBEventNameNode(
        event_name=event_name2,
        start_position=10,
        stop_position=20,
    )
    node3 = PBEventNameNode(
        event_name=event_name1,
        start_position=15,
        stop_position=25,
    )
    node4 = PBEventNameNode(
        event_name=event_name3,
        start_position=10,
        stop_position=20,
    )

    assert node1 == node2  # Same values
    assert node1 != node3  # Different positions
    assert node1 != node4  # Different event name
    assert node1 != "not a node"  # Different type


def test_event_name_node_hash():
    """Test event name node hashing."""
    event_name = "clicked"
    node1 = PBEventNameNode(
        event_name=event_name,
        start_position=10,
        stop_position=20,
    )
    node2 = PBEventNameNode(
        event_name=event_name,
        start_position=10,
        stop_position=20,
    )

    assert hash(node1) == hash(node2)


def test_event_name_node_visitor():
    """Test event name node visitor pattern."""
    class TestVisitor:
        def visit_event_name_node(self, node) -> str:
            return "visited"

    event_name = "clicked"
    node = PBEventNameNode(
        event_name=event_name,
        start_position=10,
        stop_position=20,
    )
    visitor = TestVisitor()

    assert node.accept_visitor(visitor) == "visited"
