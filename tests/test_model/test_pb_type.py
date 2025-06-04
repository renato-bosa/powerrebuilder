"""Tests for PowerBuilder type model."""

import pytest

from model.base.pb_type import (
    PBArrayType,
    PBBasicType,
    PBBasicTypeNode,
    PBCustomType,
    PBCustomTypeNode,
    PBType,
    PBTypeNode,
)


class TestPBTypeNode:
    """Test PBTypeNode base class."""

    def test_type_node_creation(self):
        """Test creating a type node."""
        node = PBTypeNode(type_name="integer")
        assert node.type_name == "integer"


class TestPBBasicTypeNode:
    """Test PBBasicTypeNode class."""

    def test_basic_type_node_creation(self):
        """Test creating a basic type node."""
        node = PBBasicTypeNode(type_name="string", is_array=False)
        assert node.type_name == "string"
        assert node.is_array is False

    def test_basic_type_node_array(self):
        """Test creating an array basic type node."""
        node = PBBasicTypeNode(type_name="integer", is_array=True)
        assert node.type_name == "integer"
        assert node.is_array is True


class TestPBCustomTypeNode:
    """Test PBCustomTypeNode class."""

    def test_custom_type_node_creation(self):
        """Test creating a custom type node."""
        node = PBCustomTypeNode(
            type_name="n_customer",
            base_type="nonvisualobject",
        )
        assert node.type_name == "n_customer"
        assert node.base_type == "nonvisualobject"


class TestPBBasicType:
    """Test PBBasicType class."""

    @pytest.mark.parametrize("type_name", [
        "integer", "long", "decimal", "real", "double",
        "string", "char", "boolean", "date", "time",
        "datetime", "blob",
    ])
    def test_basic_types(self, type_name):
        """Test creating various basic types."""
        basic_type = PBBasicType(name=type_name)
        assert basic_type.name == type_name

    def test_basic_type_with_size(self):
        """Test basic type with size constraint."""
        string_type = PBBasicType(name="string", size=100)
        assert string_type.name == "string"
        assert string_type.size == 100

    def test_basic_type_nullable(self):
        """Test nullable basic type."""
        nullable_int = PBBasicType(name="integer", nullable=True)
        assert nullable_int.name == "integer"
        assert nullable_int.nullable is True


class TestPBArrayType:
    """Test PBArrayType class."""

    def test_array_type_creation(self):
        """Test creating an array type."""
        element_type = PBBasicType(name="integer")
        array_type = PBArrayType(
            element_type=element_type,
            dimensions=1,
        )
        assert array_type.element_type.name == "integer"
        assert array_type.dimensions == 1

    def test_multi_dimensional_array(self):
        """Test creating a multi-dimensional array type."""
        element_type = PBBasicType(name="string")
        array_type = PBArrayType(
            element_type=element_type,
            dimensions=2,
            bounds=[(1, 10), (1, 5)],
        )
        assert array_type.dimensions == 2
        assert len(array_type.bounds) == 2
        assert array_type.bounds[0] == (1, 10)
        assert array_type.bounds[1] == (1, 5)

    def test_array_with_custom_type(self):
        """Test array of custom type."""
        custom_type = PBCustomType(name="n_customer")
        array_type = PBArrayType(
            element_type=custom_type,
            dimensions=1,
        )
        assert array_type.element_type.name == "n_customer"


class TestPBCustomType:
    """Test PBCustomType class."""

    def test_custom_type_creation(self):
        """Test creating a custom type."""
        custom_type = PBCustomType(
            name="n_customer",
            base_class="nonvisualobject",
        )
        assert custom_type.name == "n_customer"
        assert custom_type.base_class == "nonvisualobject"

    def test_custom_type_with_namespace(self):
        """Test custom type with namespace."""
        custom_type = PBCustomType(
            name="customer",
            namespace="myapp.entities",
            base_class="structure",
        )
        assert custom_type.name == "customer"
        assert custom_type.namespace == "myapp.entities"

    def test_custom_type_interface(self):
        """Test custom type as interface."""
        interface_type = PBCustomType(
            name="i_validator",
            is_interface=True,
        )
        assert interface_type.name == "i_validator"
        assert interface_type.is_interface is True


class TestPBType:
    """Test PBType base class."""

    def test_type_creation(self):
        """Test creating a type."""
        pb_type = PBType(name="mytype", category="basic")
        assert pb_type.name == "mytype"
        assert pb_type.category == "basic"

    def test_type_with_constraints(self):
        """Test type with constraints."""
        pb_type = PBType(
            name="bounded_int",
            category="basic",
            min_value=0,
            max_value=100,
        )
        assert pb_type.name == "bounded_int"
        assert pb_type.min_value == 0
        assert pb_type.max_value == 100
