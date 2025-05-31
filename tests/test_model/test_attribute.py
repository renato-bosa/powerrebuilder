"""Test PowerBuilder attribute model functionality."""

from model.pb_access import AccessType, PBAccess
from model.pb_attribute import PBAttribute, PBAttributeContainer
from model.pb_type import PBBasicType


def test_attribute_basic():
    """Test basic attribute functionality."""
    attr = PBAttribute(name="m_counter")
    assert attr.name == "m_counter"
    assert attr.pb_type is None
    assert attr.initial_value is None
    assert not attr.is_constant
    assert not attr.is_readonly
    assert attr.is_instance_variable


def test_attribute_type():
    """Test attribute type handling."""
    attr = PBAttribute(name="m_counter")
    int_type = PBBasicType(name="integer")

    # Set and get type
    attr.set_type(int_type)
    assert attr.get_type() == int_type
    assert attr.type_name == "integer"


def test_attribute_access():
    """Test attribute access tracking."""
    attr = PBAttribute(name="m_counter")

    # Add accesses
    read_access = PBAccess(
        name="read_access",
        variable_name="m_counter",
        access_type=AccessType.READ,
    )
    write_access = PBAccess(
        name="write_access",
        variable_name="m_counter",
        access_type=AccessType.WRITE,
    )

    attr.add_access(read_access)
    attr.add_access(write_access)

    # Test access retrieval
    assert len(attr.get_accesses()) == 2
    assert len(attr.get_read_accesses()) == 1
    assert len(attr.get_write_accesses()) == 1
    assert attr.get_read_accesses()[0] == read_access
    assert attr.get_write_accesses()[0] == write_access


def test_attribute_declaration():
    """Test attribute declaration generation."""
    # Basic attribute
    attr = PBAttribute(name="m_counter")
    attr.set_type(PBBasicType(name="integer"))
    assert attr.to_declaration() == "integer m_counter"

    # Constant attribute
    attr.is_constant = True
    assert attr.to_declaration() == "constant integer m_counter"

    # Readonly attribute
    attr.is_constant = False
    attr.is_readonly = True
    assert attr.to_declaration() == "readonly integer m_counter"

    # Attribute with initial value
    attr.is_readonly = False
    attr.initial_value = 0
    assert attr.to_declaration() == "integer m_counter = 0"

    # Attribute with all modifiers
    attr.is_constant = True
    attr.is_readonly = True
    assert attr.to_declaration() == "constant readonly integer m_counter = 0"


def test_attribute_container():
    """Test attribute container functionality."""
    container = PBAttributeContainer()

    # Create attributes
    attr1 = PBAttribute(
        name="m_counter",
        pb_type=PBBasicType(name="integer"),
        is_constant=True,
    )
    attr2 = PBAttribute(
        name="m_name",
        pb_type=PBBasicType(name="string"),
        is_readonly=True,
    )
    attr3 = PBAttribute(
        name="m_flag",
        pb_type=PBBasicType(name="boolean"),
    )

    # Add attributes
    container.add_attribute(attr1)
    container.add_attribute(attr2)
    container.add_attribute(attr3)

    # Test attribute retrieval
    assert container.get_attribute("m_counter") == attr1
    assert container.get_attribute("m_name") == attr2
    assert container.get_attribute("m_flag") == attr3
    assert container.get_attribute("nonexistent") is None

    # Test getting all attributes
    all_attrs = container.get_all_attributes()
    assert len(all_attrs) == 3
    assert attr1 in all_attrs
    assert attr2 in all_attrs
    assert attr3 in all_attrs

    # Test getting constant attributes
    const_attrs = container.get_constant_attributes()
    assert len(const_attrs) == 1
    assert const_attrs[0] == attr1

    # Test getting readonly attributes
    readonly_attrs = container.get_readonly_attributes()
    assert len(readonly_attrs) == 1
    assert readonly_attrs[0] == attr2

    # Test getting attributes by type
    integer_attrs = container.get_attributes_of_type("integer")
    assert len(integer_attrs) == 1
    assert integer_attrs[0] == attr1

    # Test removing attribute
    container.remove_attribute("m_counter")
    assert len(container.get_all_attributes()) == 2
    assert container.get_attribute("m_counter") is None


def test_attribute_reachable_entities() -> None:
    """Test attribute reachable entities."""
    class ReachableType(PBBasicType):
        def get_reachable_entities(self) -> set:
            return {self}

    # Type with reachable entities
    attr1 = PBAttribute(name="m_obj")
    reachable_type = ReachableType(name="custom_type")
    attr1.set_type(reachable_type)
    assert len(attr1.get_reachable_entities()) == 1
    assert reachable_type in attr1.get_reachable_entities()

    # Type without reachable entities
    attr2 = PBAttribute(name="m_counter")
    attr2.set_type(PBBasicType(name="integer"))
    assert len(attr2.get_reachable_entities()) == 0
