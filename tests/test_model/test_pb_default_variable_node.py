"""Test cases for PowerBuilder default variable AST node.

Ported from reference/moose-pb-parser/PowerBuilder-Parser-Tests/PWBCommonParserTest.class.st
"""

from model.entities.pb_variable import PBDefaultVariableNode


def test_default_variable_node_creation():
    """Test creating a default variable node."""
    node = PBDefaultVariableNode(
        default_variable="my_var", start_position=10, stop_position=20
    )
    assert node.default_variable == "my_var"
    assert node.start_position == 10
    assert node.stop_position == 20


def test_default_variable_node_str():
    """Test string representation of default variable node."""
    node = PBDefaultVariableNode(default_variable="my_var")
    assert str(node) == "default variable my_var"


def test_default_variable_node_equality():
    """Test equality comparison of default variable nodes."""
    node1 = PBDefaultVariableNode(
        default_variable="var1", start_position=1, stop_position=2
    )
    node2 = PBDefaultVariableNode(
        default_variable="var1", start_position=1, stop_position=2
    )
    node3 = PBDefaultVariableNode(
        default_variable="var2", start_position=1, stop_position=2
    )

    assert node1 == node2
    assert node1 != node3
    assert node1 != "var1"


def test_default_variable_node_hash():
    """Test hashing of default variable nodes."""
    node1 = PBDefaultVariableNode(
        default_variable="var1", start_position=1, stop_position=2
    )
    node2 = PBDefaultVariableNode(
        default_variable="var1", start_position=1, stop_position=2
    )

    # Same nodes should have same hash
    assert hash(node1) == hash(node2)

    # Can be used as dictionary keys
    d = {node1: "value"}
    assert d[node2] == "value"
