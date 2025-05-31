"""Test cases for PowerBuilder DataWindow file AST node.

Ported from reference/moose-pb-parser/PowerBuilder-Parser-Tests/PWBCommonParserTest.class.st
"""

from model.pb_datawindow import PBDataWindowFileNode


def test_data_window_file_node_creation():
    """Test creating a DataWindow file node."""
    node = PBDataWindowFileNode(file_statements=["stmt1", "stmt2"], start_position=10, stop_position=20)
    assert node.file_statements == ["stmt1", "stmt2"]
    assert node.start_position == 10
    assert node.stop_position == 20


def test_data_window_file_node_str():
    """Test string representation of DataWindow file node."""
    node = PBDataWindowFileNode(file_statements=["stmt1", "stmt2"])
    assert str(node) == "stmt1\nstmt2"


def test_data_window_file_node_equality():
    """Test equality comparison of DataWindow file nodes."""
    node1 = PBDataWindowFileNode(file_statements=["s1", "s2"], start_position=1, stop_position=2)
    node2 = PBDataWindowFileNode(file_statements=["s1", "s2"], start_position=1, stop_position=2)
    node3 = PBDataWindowFileNode(file_statements=["s3", "s4"], start_position=1, stop_position=2)

    assert node1 == node2
    assert node1 != node3
    assert node1 != "datawindow"


def test_data_window_file_node_hash():
    """Test hashing of DataWindow file nodes."""
    node1 = PBDataWindowFileNode(file_statements=["s1", "s2"], start_position=1, stop_position=2)
    node2 = PBDataWindowFileNode(file_statements=["s1", "s2"], start_position=1, stop_position=2)

    # Same nodes should have same hash
    assert hash(node1) == hash(node2)

    # Can be used as dictionary keys
    d = {node1: "value"}
    assert d[node2] == "value"
