"""Test cases for PowerBuilder custom type AST node.

Ported from reference/moose-pb-parser/PowerBuilder-Parser-Tests/PWBCommonParserTest.class.st
"""

from model.ast.types import PBCustomTypeNode


def test_custom_type_node_creation():
    """Test creating a custom type node."""
    node = PBCustomTypeNode(identifier="my_type", start_position=10, stop_position=20)
    assert node.identifier == "my_type"
    assert node.start_position == 10
    assert node.stop_position == 20


def test_custom_type_node_str():
    """Test string representation of custom type node."""
    node = PBCustomTypeNode(identifier="my_type")
    assert str(node) == "my_type"


def test_custom_type_node_equality():
    """Test equality comparison of custom type nodes."""
    node1 = PBCustomTypeNode(identifier="type1", start_position=1, stop_position=2)
    node2 = PBCustomTypeNode(identifier="type1", start_position=1, stop_position=2)
    node3 = PBCustomTypeNode(identifier="type2", start_position=1, stop_position=2)

    assert node1 == node2
    assert node1 != node3
    assert node1 != "type1"


def test_custom_type_node_hash():
    """Test hashing of custom type nodes."""
    node1 = PBCustomTypeNode(identifier="type1", start_position=1, stop_position=2)
    node2 = PBCustomTypeNode(identifier="type1", start_position=1, stop_position=2)

    # Same nodes should have same hash
    assert hash(node1) == hash(node2)

    # Can be used as dictionary keys
    d = {node1: "value"}
    assert d[node2] == "value"
