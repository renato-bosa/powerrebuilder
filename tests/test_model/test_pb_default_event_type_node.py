"""Test cases for PowerBuilder default event type AST node.

Ported from reference/moose-pb-parser/PowerBuilder-Parser-Tests/PWBCommonParserTest.class.st
"""

from model.entities.pb_event import PBDefaultEventTypeNode


def test_default_event_type_node_creation():
    """Test creating a default event type node."""
    node = PBDefaultEventTypeNode(default_event_type="clicked", start_position=10, stop_position=20)
    assert node.default_event_type == "clicked"
    assert node.start_position == 10
    assert node.stop_position == 20


def test_default_event_type_node_str():
    """Test string representation of default event type node."""
    node = PBDefaultEventTypeNode(default_event_type="clicked")
    assert str(node) == "default event type clicked"


def test_default_event_type_node_equality():
    """Test equality comparison of default event type nodes."""
    node1 = PBDefaultEventTypeNode(default_event_type="clicked", start_position=1, stop_position=2)
    node2 = PBDefaultEventTypeNode(default_event_type="clicked", start_position=1, stop_position=2)
    node3 = PBDefaultEventTypeNode(default_event_type="changed", start_position=1, stop_position=2)

    assert node1 == node2
    assert node1 != node3
    assert node1 != "clicked"


def test_default_event_type_node_hash():
    """Test hashing of default event type nodes."""
    node1 = PBDefaultEventTypeNode(default_event_type="clicked", start_position=1, stop_position=2)
    node2 = PBDefaultEventTypeNode(default_event_type="clicked", start_position=1, stop_position=2)

    # Same nodes should have same hash
    assert hash(node1) == hash(node2)

    # Can be used as dictionary keys
    d = {node1: "value"}
    assert d[node2] == "value"
