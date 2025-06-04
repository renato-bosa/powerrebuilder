"""Test cases for the PBDynamicMethodInvocationNode class.

Ported from reference/moose-pb-parser/PowerBuilder-Parser-Tests/PWBASTVisitorTest.class.st
"""

from model.entities.pb_expression import PBDynamicMethodInvocationNode


def test_dynamic_method_invocation_node_creation():
    """Test creating a dynamic method invocation node."""
    unchecked_identifier = "obj.method"
    function_arguments = ["arg1", "arg2"]
    node = PBDynamicMethodInvocationNode(
        unchecked_identifier=unchecked_identifier,
        function_arguments=function_arguments,
        start_position=10,
        stop_position=20,
    )
    assert node.unchecked_identifier == unchecked_identifier
    assert node.function_arguments == function_arguments
    assert node.start_position == 10
    assert node.stop_position == 20


def test_dynamic_method_invocation_node_str():
    """Test string representation of dynamic method invocation node."""
    node = PBDynamicMethodInvocationNode(
        unchecked_identifier="obj.method",
        function_arguments=["arg1", "arg2"],
    )
    assert str(node) == "obj.method(arg1, arg2)"


def test_dynamic_method_invocation_node_equality():
    """Test dynamic method invocation node equality comparison."""
    unchecked_identifier = "obj.method"
    function_arguments1 = ["arg1", "arg2"]
    function_arguments2 = ["arg1", "arg2"]
    node1 = PBDynamicMethodInvocationNode(
        unchecked_identifier=unchecked_identifier,
        function_arguments=function_arguments1,
        start_position=10,
        stop_position=20,
    )
    node2 = PBDynamicMethodInvocationNode(
        unchecked_identifier=unchecked_identifier,
        function_arguments=function_arguments2,
        start_position=10,
        stop_position=20,
    )
    node3 = PBDynamicMethodInvocationNode(
        unchecked_identifier=unchecked_identifier,
        function_arguments=function_arguments1,
        start_position=15,
        stop_position=25,
    )
    node4 = PBDynamicMethodInvocationNode(
        unchecked_identifier="other.method",
        function_arguments=function_arguments1,
        start_position=10,
        stop_position=20,
    )

    assert node1 == node2  # Same values
    assert node1 != node3  # Different positions
    assert node1 != node4  # Different identifier
    assert node1 != "not a node"  # Different type


def test_dynamic_method_invocation_node_hash():
    """Test dynamic method invocation node hashing."""
    unchecked_identifier = "obj.method"
    function_arguments = ["arg1", "arg2"]
    node1 = PBDynamicMethodInvocationNode(
        unchecked_identifier=unchecked_identifier,
        function_arguments=function_arguments,
        start_position=10,
        stop_position=20,
    )
    node2 = PBDynamicMethodInvocationNode(
        unchecked_identifier=unchecked_identifier,
        function_arguments=function_arguments,
        start_position=10,
        stop_position=20,
    )

    assert hash(node1) == hash(node2)


def test_dynamic_method_invocation_node_visitor():
    """Test dynamic method invocation node visitor pattern."""
    class TestVisitor:
        def visit_dynamic_method_invocation_node(self, node) -> str:
            return "visited"

    unchecked_identifier = "obj.method"
    function_arguments = ["arg1", "arg2"]
    node = PBDynamicMethodInvocationNode(
        unchecked_identifier=unchecked_identifier,
        function_arguments=function_arguments,
        start_position=10,
        stop_position=20,
    )
    visitor = TestVisitor()

    assert node.accept_visitor(visitor) == "visited"
