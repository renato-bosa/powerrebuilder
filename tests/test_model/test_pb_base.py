"""Test cases for the base PBNode class."""

import pytest

from model.base.pb_behavioral import PBNode


def test_pb_node_creation():



    


    """Test creating a base node."""
    node = PBNode(start_position=10, stop_position=20)
    assert node.start_position == 10
    assert node.stop_position == 20


def test_pb_node_default_values():



    


    """Test default values for base node."""
    node = PBNode()
    assert node.start_position is None
    assert node.stop_position is None


def test_pb_node_equality():



    


    """Test base node equality comparison."""
    node1 = PBNode(start_position=10, stop_position=20)
    node2 = PBNode(start_position=10, stop_position=20)
    node3 = PBNode(start_position=15, stop_position=25)

    assert node1 == node2  # Same values
    assert node1 != node3  # Different positions


def test_pb_node_visitor_not_implemented():



    


    """Test that accept_visitor raises NotImplementedError."""
    node = PBNode()
    with pytest.raises(NotImplementedError):
        node.accept_visitor(None)
