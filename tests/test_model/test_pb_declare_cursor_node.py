"""Test cases for PowerBuilder declare cursor AST node.

Ported from reference/moose-pb-parser/PowerBuilder-Parser-Tests/PWBCommonParserTest.class.st
"""

from model.entities.pb_expression import PBDeclareCursorNode


def test_declare_cursor_node_creation():



    


    """Test creating a declare cursor node."""
    node = PBDeclareCursorNode(
        identifier="my_cursor",
        target="SELECT * FROM table",
        start_position=10,
        stop_position=20,
    )
    assert node.identifier == "my_cursor"
    assert node.target == "SELECT * FROM table"
    assert node.start_position == 10
    assert node.stop_position == 20


def test_declare_cursor_node_str():



    


    """Test string representation of declare cursor node."""
    node = PBDeclareCursorNode(identifier="my_cursor", target="SELECT * FROM table")
    assert str(node) == "declare my_cursor cursor for SELECT * FROM table"


def test_declare_cursor_node_equality():



    


    """Test equality comparison of declare cursor nodes."""
    node1 = PBDeclareCursorNode(
        identifier="c1", target="SELECT 1", start_position=1, stop_position=2
    )
    node2 = PBDeclareCursorNode(
        identifier="c1", target="SELECT 1", start_position=1, stop_position=2
    )
    node3 = PBDeclareCursorNode(
        identifier="c2", target="SELECT 2", start_position=1, stop_position=2
    )

    assert node1 == node2
    assert node1 != node3
    assert node1 != "cursor"


def test_declare_cursor_node_hash():



    


    """Test hashing of declare cursor nodes."""
    node1 = PBDeclareCursorNode(
        identifier="c1", target="SELECT 1", start_position=1, stop_position=2
    )
    node2 = PBDeclareCursorNode(
        identifier="c1", target="SELECT 1", start_position=1, stop_position=2
    )

    # Same nodes should have same hash
    assert hash(node1) == hash(node2)

    # Can be used as dictionary keys
    d = {node1: "value"}
    assert d[node2] == "value"
