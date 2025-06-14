"""Test PowerBuilder type system functionality."""

from model.ast import (
    PBArrayType,
    PBBasicType,
    PBCustomType,
    PBDataWindowType,
    PBSourcedEntity,
    PBTypeRegistry,
)


def test_basic_type():
    """Test basic type functionality."""
    int_type = PBBasicType(name="integer")
    str_type = PBBasicType(name="string")

    # Test type acceptance
    assert int_type.accepts(int_type)
    assert not int_type.accepts(str_type)

    # Test type properties
    assert int_type.is_basic
    assert not int_type.is_custom
    assert not int_type.is_array
    assert not int_type.is_datawindow

    # Test references
    int_type.add_reference("var1")
    int_type.add_reference("var2")
    assert "var1" in int_type.references
    assert "var2" in int_type.references

    int_type.remove_reference("var1")
    assert "var1" not in int_type.references
    assert "var2" in int_type.references

    # Test reachable entities
    assert len(int_type.get_reachable_entities()) == 0


def test_custom_type():
    """Test custom type functionality."""
    # Create base type
    shape = PBCustomType(name="shape")
    shape.add_attribute("x", PBBasicType(name="integer"))
    shape.add_attribute("y", PBBasicType(name="integer"))

    # Create derived type
    circle = PBCustomType(name="circle", super_type=shape)
    circle.add_attribute("radius", PBBasicType(name="integer"))

    # Test type acceptance
    assert shape.accepts(shape)
    assert shape.accepts(circle)
    assert circle.accepts(circle)
    assert not circle.accepts(shape)

    # Test type properties
    assert not shape.is_basic
    assert shape.is_custom
    assert not shape.is_array
    assert not shape.is_datawindow

    # Test attributes
    assert isinstance(shape.get_attribute("x"), PBBasicType)
    assert shape.get_attribute("x").name == "integer"
    assert circle.get_attribute("radius").name == "integer"
    assert circle.get_attribute("nonexistent") is None

    # Test reachable entities
    shape_entities = shape.get_reachable_entities()
    assert shape in shape_entities

    circle_entities = circle.get_reachable_entities()
    assert circle in circle_entities
    assert shape in circle_entities


def test_array_type():
    """Test array type functionality."""
    # Create array types
    int_type = PBBasicType(name="integer")
    int_array = PBArrayType(name="integer[]", element_type=int_type, dimensions=[10])
    int_matrix = PBArrayType(
        name="integer[][]", element_type=int_type, dimensions=[5, 5]
    )

    # Test dimensions
    assert len(int_array.dimensions) == 1
    assert len(int_matrix.dimensions) == 2

    # Test type properties
    assert not int_array.is_basic
    assert not int_array.is_custom
    assert int_array.is_array
    assert not int_array.is_datawindow

    # Test type acceptance
    assert int_array.accepts(int_array)
    assert not int_array.accepts(int_matrix)
    assert not int_array.accepts(int_type)

    # Test reachable entities
    array_entities = int_array.get_reachable_entities()
    assert len(array_entities) == 0  # Basic type has no reachable entities


def test_datawindow_type():
    """Test DataWindow type functionality."""
    # Create DataWindow type
    dw = PBDataWindowType(name="d_customer")
    dw.add_attribute("id", PBBasicType(name="integer"))
    dw.add_attribute("name", PBBasicType(name="string"))

    # Test type properties
    assert not dw.is_basic
    assert dw.is_custom
    assert not dw.is_array
    assert dw.is_datawindow

    # Test attributes
    assert isinstance(dw.get_attribute("id"), PBBasicType)
    assert dw.get_attribute("id").name == "integer"
    assert dw.get_attribute("name").name == "string"

    # Test reachable entities
    dw_entities = dw.get_reachable_entities()
    assert dw in dw_entities


def test_type_ownership():
    """Test type ownership functionality."""
    # Create types and owner
    int_type = PBBasicType(name="integer")
    owner = PBSourcedEntity(name="owner_entity")

    # Set and get owner
    int_type.set_owner(owner)
    assert int_type.get_owner() == owner
    assert int_type.get_owner().name == "owner_entity"


def test_type_registry():
    """Test type registry functionality."""
    registry = PBTypeRegistry()

    # Register basic types
    int_type = PBBasicType(name="integer")
    str_type = PBBasicType(name="string")
    registry.register_type(int_type)
    registry.register_type(str_type)

    # Test type lookup
    assert registry.get_type("integer") == int_type
    assert registry.get_type("string") == str_type
    assert registry.get_type("nonexistent") is None

    # Test array type creation
    int_array = registry.create_array_type(int_type, [10])
    assert registry.get_type("integer[]") == int_array
    assert int_array.element_type == int_type
    assert int_array.dimensions == [10]


def test_namespaced_types():
    """Test types with namespaces."""
    # Create types in different namespaces
    registry = PBTypeRegistry()

    window_type = PBCustomType(name="window", namespace="ui")
    dialog_type = PBCustomType(name="window", namespace="popup")

    registry.register_type(window_type)
    registry.register_type(dialog_type)

    # Test qualified names
    assert window_type.qualified_name == "ui.window"
    assert dialog_type.qualified_name == "popup.window"

    # Test type lookup
    assert registry.get_type("ui.window") == window_type
    assert registry.get_type("popup.window") == dialog_type
    assert registry.get_type("window") is None


def test_type_inheritance_chain():
    """Test type inheritance chain."""
    # Create inheritance chain
    entity = PBCustomType(name="entity")
    model = PBCustomType(name="model", super_type=entity)
    user = PBCustomType(name="user", super_type=model)
    admin = PBCustomType(name="admin", super_type=user)

    # Test type acceptance up the chain
    assert entity.accepts(admin)
    assert entity.accepts(user)
    assert entity.accepts(model)
    assert model.accepts(admin)
    assert model.accepts(user)
    assert user.accepts(admin)

    # Test type acceptance down the chain
    assert not admin.accepts(user)
    assert not admin.accepts(model)
    assert not admin.accepts(entity)
    assert not user.accepts(model)
    assert not user.accepts(entity)
    assert not model.accepts(entity)

    # Test reachable entities
    admin_entities = admin.get_reachable_entities()
    assert admin in admin_entities
    assert user in admin_entities
    assert model in admin_entities
    assert entity in admin_entities
