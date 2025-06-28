"""Test cases for PowerBuilder DataWindow component AST node.

Ported from reference/moose-pb-parser/PowerBuilder-Parser-Tests/PWBCommonParserTest.class.st
"""

from model.datawindow import PBDataComponentNode


def test_data_component_node_creation():






    """Test creating a data component node."""
    node = PBDataComponentNode(
        data_component="my_component", start_position=10, stop_position=20,
    )
    assert node.data_component == "my_component"
    assert node.start_position == 10
    assert node.stop_position == 20


def test_data_component_node_str():






    """Test string representation of data component node."""
    node = PBDataComponentNode(data_component="my_component")
    assert str(node) == "my_component"


def test_data_component_node_equality():






    """Test equality comparison of data component nodes."""
    node1 = PBDataComponentNode(
        data_component="comp1", start_position=1, stop_position=2,
    )
    node2 = PBDataComponentNode(
        data_component="comp1", start_position=1, stop_position=2,
    )
    node3 = PBDataComponentNode(
        data_component="comp2", start_position=1, stop_position=2,
    )

    assert node1 == node2
    assert node1 != node3
    assert node1 != "comp1"


def test_data_component_node_hash():






    """Test hashing of data component nodes."""
    node1 = PBDataComponentNode(
        data_component="comp1", start_position=1, stop_position=2,
    )
    node2 = PBDataComponentNode(
        data_component="comp1", start_position=1, stop_position=2,
    )

    # Same nodes should have same hash
    assert hash(node1) == hash(node2)

    # Can be used as dictionary keys
    d = {node1: "value"}
    assert d[node2] == "value"
