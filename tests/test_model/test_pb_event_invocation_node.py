"""Test cases for the PBEventInvocationNode class.

Ported from reference/moose-pb-parser/PowerBuilder-Parser-Tests/PWBASTVisitorTest.class.st
"""

from model.entities.pb_expression import PBEventInvocationNode


def test_event_invocation_node_creation():
    """Test creating an event invocation node."""
    identifier = "clicked"
    function_arguments = ["arg1", "arg2"]
    node = PBEventInvocationNode(
        identifier=identifier,
        function_arguments=function_arguments,
        start_position=10,
        stop_position=20,
    )
    assert node.identifier == identifier
    assert node.function_arguments == function_arguments
    assert node.start_position == 10
    assert node.stop_position == 20


def test_event_invocation_node_str():
    """Test string representation of event invocation node."""
    node = PBEventInvocationNode(
        identifier="clicked",
        function_arguments=["arg1", "arg2"],
    )
    assert str(node) == "clicked(arg1, arg2)"


def test_event_invocation_node_str_no_args():
    """Test string representation of event invocation node without arguments."""
    node = PBEventInvocationNode(
        identifier="clicked",
    )
    assert str(node) == "clicked()"


def test_event_invocation_node_equality():
    """Test event invocation node equality comparison."""
    identifier = "clicked"
    function_arguments1 = ["arg1", "arg2"]
    function_arguments2 = ["arg1", "arg2"]
    node1 = PBEventInvocationNode(
        identifier=identifier,
        function_arguments=function_arguments1,
        start_position=10,
        stop_position=20,
    )
    node2 = PBEventInvocationNode(
        identifier=identifier,
        function_arguments=function_arguments2,
        start_position=10,
        stop_position=20,
    )
    node3 = PBEventInvocationNode(
        identifier=identifier,
        function_arguments=function_arguments1,
        start_position=15,
        stop_position=25,
    )
    node4 = PBEventInvocationNode(
        identifier="doubleClicked",
        function_arguments=function_arguments1,
        start_position=10,
        stop_position=20,
    )

    assert node1 == node2  # Same values
    assert node1 != node3  # Different positions
    assert node1 != node4  # Different identifier
    assert node1 != "not a node"  # Different type


def test_event_invocation_node_hash():
    """Test event invocation node hashing."""
    identifier = "clicked"
    function_arguments = ["arg1", "arg2"]
    node1 = PBEventInvocationNode(
        identifier=identifier,
        function_arguments=function_arguments,
        start_position=10,
        stop_position=20,
    )
    node2 = PBEventInvocationNode(
        identifier=identifier,
        function_arguments=function_arguments.copy(),
        start_position=10,
        stop_position=20,
    )

    assert hash(node1) == hash(node2)


def test_event_invocation_node_visitor():
    """Test event invocation node visitor pattern."""

    class TestVisitor:
        def visit_event_invocation_node(self, node) -> str:
            return "visited"

    identifier = "clicked"
    function_arguments = ["arg1", "arg2"]
    node = PBEventInvocationNode(
        identifier=identifier,
        function_arguments=function_arguments,
        start_position=10,
        stop_position=20,
    )
    visitor = TestVisitor()

    assert node.accept_visitor(visitor) == "visited"
