"""Test cases for the PBEventAttributeNode class.

Ported from reference/moose-pb-parser/PowerBuilder-Parser-Tests/PWBASTVisitorTest.class.st
"""

from model.entities.pb_expression import PBEventAttributeNode


def test_event_attribute_node_creation():



    


    """Test creating an event attribute node."""
    return_type = "integer"
    event_name = "clicked"
    attribute = "public"
    node = PBEventAttributeNode(
        return_type=return_type,
        event_name=event_name,
        attribute=attribute,
        start_position=10,
        stop_position=20,
    )
    assert node.return_type == return_type
    assert node.event_name == event_name
    assert node.attribute == attribute
    assert node.start_position == 10
    assert node.stop_position == 20


def test_event_attribute_node_str():



    


    """Test string representation of event attribute node."""
    node = PBEventAttributeNode(
        return_type="integer",
        event_name="clicked",
        attribute="public",
    )
    assert str(node) == "integer event clicked public"


def test_event_attribute_node_equality():



    


    """Test event attribute node equality comparison."""
    return_type = "integer"
    event_name = "clicked"
    attribute = "public"
    node1 = PBEventAttributeNode(
        return_type=return_type,
        event_name=event_name,
        attribute=attribute,
        start_position=10,
        stop_position=20,
    )
    node2 = PBEventAttributeNode(
        return_type=return_type,
        event_name=event_name,
        attribute=attribute,
        start_position=10,
        stop_position=20,
    )
    node3 = PBEventAttributeNode(
        return_type=return_type,
        event_name=event_name,
        attribute=attribute,
        start_position=15,
        stop_position=25,
    )
    node4 = PBEventAttributeNode(
        return_type="long",
        event_name=event_name,
        attribute=attribute,
        start_position=10,
        stop_position=20,
    )

    assert node1 == node2  # Same values
    assert node1 != node3  # Different positions
    assert node1 != node4  # Different return type
    assert node1 != "not a node"  # Different type


def test_event_attribute_node_hash():



    


    """Test event attribute node hashing."""
    return_type = "integer"
    event_name = "clicked"
    attribute = "public"
    node1 = PBEventAttributeNode(
        return_type=return_type,
        event_name=event_name,
        attribute=attribute,
        start_position=10,
        stop_position=20,
    )
    node2 = PBEventAttributeNode(
        return_type=return_type,
        event_name=event_name,
        attribute=attribute,
        start_position=10,
        stop_position=20,
    )

    assert hash(node1) == hash(node2)


def test_event_attribute_node_visitor():



    


    """Test event attribute node visitor pattern."""

    class TestVisitor:
        def visit_event_attribute_node(self, node) -> str:
            
            return "visited"

    return_type = "integer"
    event_name = "clicked"
    attribute = "public"
    node = PBEventAttributeNode(
        return_type=return_type,
        event_name=event_name,
        attribute=attribute,
        start_position=10,
        stop_position=20,
    )
    visitor = TestVisitor()

    assert node.accept_visitor(visitor) == "visited"
