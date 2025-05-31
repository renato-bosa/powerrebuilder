"""Test cases for the PBFunctionArgumentNode class.

Ported from reference/moose-pb-parser/PowerBuilder-Parser-Tests/PWBASTVisitorTest.class.st
"""
from model.pb_function import PBFunctionArgumentNode


def test_function_argument_node_creation():
    """Test creating a function argument node."""
    node = PBFunctionArgumentNode(
        name="clicked",
        start_position=10,
        stop_position=20,
    )
    assert node.name == "clicked"
    assert node.start_position == 10
    assert node.stop_position == 20


def test_function_argument_node_equality():
    """Test function argument node equality comparison."""
    node1 = PBFunctionArgumentNode(
        name="clicked",
        start_position=10,
        stop_position=20,
    )
    node2 = PBFunctionArgumentNode(
        name="clicked",
        start_position=10,
        stop_position=20,
    )
    node3 = PBFunctionArgumentNode(
        name="clicked",
        start_position=15,
        stop_position=25,
    )
    node4 = PBFunctionArgumentNode(
        name="doubleClicked",
        start_position=10,
        stop_position=20,
    )

    assert node1 == node2  # Same values
    assert node1 != node3  # Different positions
    assert node1 != node4  # Different name
    assert node1 != "not a node"  # Different type


def test_function_argument_node_hash():
    """Test function argument node hashing."""
    node1 = PBFunctionArgumentNode(
        name="clicked",
        start_position=10,
        stop_position=20,
    )
    node2 = PBFunctionArgumentNode(
        name="clicked",
        start_position=10,
        stop_position=20,
    )

    assert hash(node1) == hash(node2)


def test_function_argument_node_visitor():
    """Test function argument node visitor pattern."""
    class TestVisitor:
        def visit_function_argument_node(self, node) -> str:
            return "visited"

    node = PBFunctionArgumentNode(
        name="clicked",
        start_position=10,
        stop_position=20,
    )
    visitor = TestVisitor()

    assert node.accept_visitor(visitor) == "visited"
