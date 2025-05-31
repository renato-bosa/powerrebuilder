"""Test cases for PowerBuilder destroy statement AST node.

Ported from reference/moose-pb-parser/PowerBuilder-Parser-Tests/PWBCommonParserTest.class.st
"""

from model.pb_expression import PBDestroyStatementNode


def test_destroy_statement_node_creation():
    """Test creating a destroy statement node."""
    node = PBDestroyStatementNode(expression="my_obj", start_position=10, stop_position=20)
    assert node.expression == "my_obj"
    assert node.start_position == 10
    assert node.stop_position == 20


def test_destroy_statement_node_str():
    """Test string representation of destroy statement node."""
    node = PBDestroyStatementNode(expression="my_obj")
    assert str(node) == "destroy my_obj"


def test_destroy_statement_node_equality():
    """Test equality comparison of destroy statement nodes."""
    node1 = PBDestroyStatementNode(expression="obj1", start_position=1, stop_position=2)
    node2 = PBDestroyStatementNode(expression="obj1", start_position=1, stop_position=2)
    node3 = PBDestroyStatementNode(expression="obj2", start_position=1, stop_position=2)

    assert node1 == node2
    assert node1 != node3
    assert node1 != "obj1"


def test_destroy_statement_node_hash():
    """Test hashing of destroy statement nodes."""
    node1 = PBDestroyStatementNode(expression="obj1", start_position=1, stop_position=2)
    node2 = PBDestroyStatementNode(expression="obj1", start_position=1, stop_position=2)

    # Same nodes should have same hash
    assert hash(node1) == hash(node2)

    # Can be used as dictionary keys
    d = {node1: "value"}
    assert d[node2] == "value"
