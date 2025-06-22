"""Test cases for PowerBuilder descriptor AST node.

Ported from reference/moose-pb-parser/PowerBuilder-Parser-Tests/PWBCommonParserTest.class.st
"""

from model.entities.pb_expression import PBDescriptorNode


def test_descriptor_node_creation():



    


    """Test creating a descriptor node."""
    node = PBDescriptorNode(expression="my_expr", start_position=10, stop_position=20)
    assert node.expression == "my_expr"
    assert node.start_position == 10
    assert node.stop_position == 20


def test_descriptor_node_str():



    


    """Test string representation of descriptor node."""
    node = PBDescriptorNode(expression="my_expr")
    assert str(node) == "descriptor my_expr"


def test_descriptor_node_equality():



    


    """Test equality comparison of descriptor nodes."""
    node1 = PBDescriptorNode(expression="expr1", start_position=1, stop_position=2)
    node2 = PBDescriptorNode(expression="expr1", start_position=1, stop_position=2)
    node3 = PBDescriptorNode(expression="expr2", start_position=1, stop_position=2)

    assert node1 == node2
    assert node1 != node3
    assert node1 != "expr1"


def test_descriptor_node_hash():



    


    """Test hashing of descriptor nodes."""
    node1 = PBDescriptorNode(expression="expr1", start_position=1, stop_position=2)
    node2 = PBDescriptorNode(expression="expr1", start_position=1, stop_position=2)

    # Same nodes should have same hash
    assert hash(node1) == hash(node2)

    # Can be used as dictionary keys
    d = {node1: "value"}
    assert d[node2] == "value"
