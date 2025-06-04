"""Test cases for PowerBuilder declare procedure AST node.

Ported from reference/moose-pb-parser/PowerBuilder-Parser-Tests/PWBCommonParserTest.class.st
"""

from model.entities.pb_expression import PBDeclareProcedureNode


def test_declare_procedure_node_creation():
    """Test creating a declare procedure node."""
    node = PBDeclareProcedureNode(procedure_name="my_proc", start_position=10, stop_position=20)
    assert node.procedure_name == "my_proc"
    assert node.start_position == 10
    assert node.stop_position == 20


def test_declare_procedure_node_str():
    """Test string representation of declare procedure node."""
    node = PBDeclareProcedureNode(procedure_name="my_proc")
    assert str(node) == "declare procedure my_proc"


def test_declare_procedure_node_equality():
    """Test equality comparison of declare procedure nodes."""
    node1 = PBDeclareProcedureNode(procedure_name="proc1", start_position=1, stop_position=2)
    node2 = PBDeclareProcedureNode(procedure_name="proc1", start_position=1, stop_position=2)
    node3 = PBDeclareProcedureNode(procedure_name="proc2", start_position=1, stop_position=2)

    assert node1 == node2
    assert node1 != node3
    assert node1 != "procedure"


def test_declare_procedure_node_hash():
    """Test hashing of declare procedure nodes."""
    node1 = PBDeclareProcedureNode(procedure_name="proc1", start_position=1, stop_position=2)
    node2 = PBDeclareProcedureNode(procedure_name="proc1", start_position=1, stop_position=2)

    # Same nodes should have same hash
    assert hash(node1) == hash(node2)

    # Can be used as dictionary keys
    d = {node1: "value"}
    assert d[node2] == "value"
