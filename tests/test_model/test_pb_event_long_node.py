"""Test cases for the PBEventLongNode class.

Ported from reference/moose-pb-parser/PowerBuilder-Parser-Tests/PWBASTVisitorTest.class.st
"""

from model.entities.pb_event import PBEventLongNode
from model.entities.pb_function import PBFunctionArgumentNode


def test_event_long_node_creation():
    """Test creating an event long node."""
    function_arg = PBFunctionArgumentNode(name="clicked")
    node = PBEventLongNode(
        function_argument=function_arg,
        start_position=10,
        stop_position=20,
    )
    assert node.function_argument == function_arg
    assert node.start_position == 10
    assert node.stop_position == 20


def test_event_long_node_equality():
    """Test event long node equality comparison."""
    function_arg1 = PBFunctionArgumentNode(name="clicked")
    function_arg2 = PBFunctionArgumentNode(name="clicked")
    node1 = PBEventLongNode(
        function_argument=function_arg1,
        start_position=10,
        stop_position=20,
    )
    node2 = PBEventLongNode(
        function_argument=function_arg2,
        start_position=10,
        stop_position=20,
    )
    node3 = PBEventLongNode(
        function_argument=function_arg1,
        start_position=15,
        stop_position=25,
    )

    assert node1 == node2  # Same values
    assert node1 != node3  # Different positions
    assert node1 != "not a node"  # Different type


def test_event_long_node_hash():
    """Test event long node hashing."""
    function_arg = PBFunctionArgumentNode(name="clicked")
    node1 = PBEventLongNode(
        function_argument=function_arg,
        start_position=10,
        stop_position=20,
    )
    node2 = PBEventLongNode(
        function_argument=function_arg,
        start_position=10,
        stop_position=20,
    )

    assert hash(node1) == hash(node2)


def test_event_long_node_visitor():
    """Test event long node visitor pattern."""

    class TestVisitor:
        def visit_event_long_node(self, node) -> str:
            return "visited"

    function_arg = PBFunctionArgumentNode(name="clicked")
    node = PBEventLongNode(
        function_argument=function_arg,
        start_position=10,
        stop_position=20,
    )
    visitor = TestVisitor()

    assert node.accept_visitor(visitor) == "visited"
