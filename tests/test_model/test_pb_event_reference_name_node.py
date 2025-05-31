"""Test cases for the PBEventReferenceNameNode class.

Ported from reference/moose-pb-parser/PowerBuilder-Parser-Tests/PWBASTVisitorTest.class.st
"""
from model.pb_expression import PBEventReferenceNameNode


def test_event_reference_name_node_creation():
    """Test creating an event reference name node."""
    object_class = "Button"
    event_name = "clicked"
    arguments = ["arg1", "arg2"]
    node = PBEventReferenceNameNode(
        object_class=object_class,
        event_name=event_name,
        arguments=arguments,
        start_position=10,
        stop_position=20,
    )
    assert node.object_class == object_class
    assert node.event_name == event_name
    assert node.arguments == arguments
    assert node.start_position == 10
    assert node.stop_position == 20


def test_event_reference_name_node_str():
    """Test string representation of event reference name node."""
    node = PBEventReferenceNameNode(
        object_class="Button",
        event_name="clicked",
        arguments=["arg1", "arg2"],
    )
    assert str(node) == "Button::clicked(arg1, arg2)"


def test_event_reference_name_node_str_no_args():
    """Test string representation of event reference name node without arguments."""
    node = PBEventReferenceNameNode(
        object_class="Button",
        event_name="clicked",
    )
    assert str(node) == "Button::clicked()"


def test_event_reference_name_node_equality():
    """Test event reference name node equality comparison."""
    object_class = "Button"
    event_name = "clicked"
    arguments1 = ["arg1", "arg2"]
    arguments2 = ["arg1", "arg2"]
    node1 = PBEventReferenceNameNode(
        object_class=object_class,
        event_name=event_name,
        arguments=arguments1,
        start_position=10,
        stop_position=20,
    )
    node2 = PBEventReferenceNameNode(
        object_class=object_class,
        event_name=event_name,
        arguments=arguments2,
        start_position=10,
        stop_position=20,
    )
    node3 = PBEventReferenceNameNode(
        object_class=object_class,
        event_name=event_name,
        arguments=arguments1,
        start_position=15,
        stop_position=25,
    )
    node4 = PBEventReferenceNameNode(
        object_class="CheckBox",
        event_name=event_name,
        arguments=arguments1,
        start_position=10,
        stop_position=20,
    )

    assert node1 == node2  # Same values
    assert node1 != node3  # Different positions
    assert node1 != node4  # Different object class
    assert node1 != "not a node"  # Different type


def test_event_reference_name_node_hash():
    """Test event reference name node hashing."""
    object_class = "Button"
    event_name = "clicked"
    arguments = ["arg1", "arg2"]
    node1 = PBEventReferenceNameNode(
        object_class=object_class,
        event_name=event_name,
        arguments=arguments,
        start_position=10,
        stop_position=20,
    )
    node2 = PBEventReferenceNameNode(
        object_class=object_class,
        event_name=event_name,
        arguments=arguments.copy(),
        start_position=10,
        stop_position=20,
    )

    assert hash(node1) == hash(node2)


def test_event_reference_name_node_visitor():
    """Test event reference name node visitor pattern."""
    class TestVisitor:
        def visit_event_reference_name_node(self, node) -> str:
            return "visited"

    object_class = "Button"
    event_name = "clicked"
    arguments = ["arg1", "arg2"]
    node = PBEventReferenceNameNode(
        object_class=object_class,
        event_name=event_name,
        arguments=arguments,
        start_position=10,
        stop_position=20,
    )
    visitor = TestVisitor()

    assert node.accept_visitor(visitor) == "visited"
