"""Test cases for PowerBuilder DataWindow AST node.

Ported from reference/moose-pb-parser/PowerBuilder-Parser-Tests/PWBCommonParserTest.class.st
"""

from model.pb_datawindow import PBDataWindowNode


def test_data_window_node_creation():



    


    """Test creating a DataWindow node."""
    node = PBDataWindowNode(
        parameters=["param1", "param2"], start_position=10, stop_position=20
    )
    assert node.parameters == ["param1", "param2"]
    assert node.start_position == 10
    assert node.stop_position == 20


def test_data_window_node_str():



    


    """Test string representation of DataWindow node."""
    node = PBDataWindowNode(parameters=["param1", "param2"])
    assert str(node) == "datawindow(param1, param2)"


def test_data_window_node_equality():



    


    """Test equality comparison of DataWindow nodes."""
    node1 = PBDataWindowNode(parameters=["p1", "p2"], start_position=1, stop_position=2)
    node2 = PBDataWindowNode(parameters=["p1", "p2"], start_position=1, stop_position=2)
    node3 = PBDataWindowNode(parameters=["p3", "p4"], start_position=1, stop_position=2)

    assert node1 == node2
    assert node1 != node3
    assert node1 != "datawindow"


def test_data_window_node_hash():



    


    """Test hashing of DataWindow nodes."""
    node1 = PBDataWindowNode(parameters=["p1", "p2"], start_position=1, stop_position=2)
    node2 = PBDataWindowNode(parameters=["p1", "p2"], start_position=1, stop_position=2)

    # Same nodes should have same hash
    assert hash(node1) == hash(node2)

    # Can be used as dictionary keys
    d = {node1: "value"}
    assert d[node2] == "value"
