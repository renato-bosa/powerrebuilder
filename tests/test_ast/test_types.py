"""Tests for PowerBuilder type nodes.

This module contains parametrized tests for all type-related AST nodes.
"""

import pytest

from src.model.ast import (
    CustomType,
    Type,
)

# Test data for different type cases
TYPE_CASES = [
    (
        Type,
        {
            "name": "integer",
            "is_array": False,
            "array_bounds": None,
        },
    ),
    (
        Type,
        {
            "name": "string",
            "is_array": True,
            "array_bounds": [10],
        },
    ),
    (
        CustomType,
        {
            "name": "MyType",
            "namespace": "app",
            "is_array": False,
            "array_bounds": None,
        },
    ),
]


@pytest.mark.parametrize(("cls", "attrs"), TYPE_CASES)
def test_type_creation(cls: type, attrs: dict) -> None:




    """Test type node creation and attributes."""
    type_node = cls(**attrs)
    assert isinstance(type_node, Type)
    for key, value in attrs.items():
        assert getattr(type_node, key) == value


def test_array_type_bounds() -> None:








    """Test array type bounds handling."""
    # Single dimension
    type1 = Type("integer", is_array=True, array_bounds=[10])
    assert type1.is_array
    assert type1.array_bounds == [10]

    # Multi-dimension
    type2 = Type("string", is_array=True, array_bounds=[5, 10])
    assert type2.is_array
    assert type2.array_bounds == [5, 10]

    # No bounds
    type3 = Type("integer", is_array=True)
    assert type3.is_array
    assert type3.array_bounds is None


def test_custom_type_namespace() -> None:








    """Test custom type namespace handling."""
    type1 = CustomType(name="MyType", namespace="app")
    assert type1.name == "MyType"
    assert type1.namespace == "app"

    type2 = CustomType(name="OtherType")
    assert type2.name == "OtherType"
    assert type2.namespace is None


def test_parametrized_type() -> None:








    """Test parameterized type functionality."""
    from src.model.ast.pb_types import PBBasicType, PBParametrizedType

    # Create type parameters
    string_type = PBBasicType(name="string")
    integer_type = PBBasicType(name="integer")

    # Create a parameterized list type
    list_of_string = PBParametrizedType(
        base_type="list",
        type_parameters=[string_type],
    )

    assert list_of_string.name == "list<string>"
    assert list_of_string.is_parameterized
    assert list_of_string.category == "parameterized"
    assert len(list_of_string.type_parameters) == 1
    assert list_of_string.type_parameters[0] == string_type

    # Create a map type with two parameters
    map_type = PBParametrizedType(
        base_type="map",
        type_parameters=[string_type, integer_type],
    )

    assert map_type.name == "map<string, integer>"
    assert len(map_type.type_parameters) == 2

    # Test type acceptance
    list_of_string2 = PBParametrizedType(
        base_type="list",
        type_parameters=[string_type],
    )
    list_of_int = PBParametrizedType(
        base_type="list", 
        type_parameters=[integer_type],
    )

    assert list_of_string.accepts(list_of_string2)
    assert not list_of_string.accepts(list_of_int)
    assert not list_of_string.accepts(map_type)

    # Test with custom name
    custom_param_type = PBParametrizedType(
        name="MyCollection",
        base_type="collection",
        type_parameters=[string_type],
    )
    assert custom_param_type.name == "MyCollection"


def test_format_type() -> None:








    """Test formatted type functionality."""
    from src.model.ast.pb_types import PBBasicType, PBFormatType

    # Create base types
    decimal_type = PBBasicType(name="decimal")
    date_type = PBBasicType(name="date")
    string_type = PBBasicType(name="string")

    # Create formatted decimal type
    currency_type = PBFormatType(
        base_type=decimal_type,
        format_string="$###,##0.00",
        edit_mask="###,##0.00",
        display_format="$###,##0.00",
    )

    assert currency_type.name == "decimal[$###,##0.00]"
    assert currency_type.is_formatted
    assert currency_type.category == "formatted"
    assert currency_type.get_effective_type() == decimal_type

    # Create formatted date type
    date_format = PBFormatType(
        base_type=date_type,
        format_string="mm/dd/yyyy",
        edit_mask="mm/dd/yyyy",
        display_format="MMM dd, yyyy",
    )

    assert date_format.name == "date[mm/dd/yyyy]"
    assert date_format.edit_mask == "mm/dd/yyyy"
    assert date_format.display_format == "MMM dd, yyyy"

    # Test type acceptance
    currency_type2 = PBFormatType(
        base_type=decimal_type,
        format_string="###,##0.00",
    )

    # Formatted types accept same base type
    assert currency_type.accepts(currency_type2)
    assert currency_type.accepts(decimal_type)
    assert not currency_type.accepts(date_format)
    assert not currency_type.accepts(string_type)

    # Test with custom name
    percent_type = PBFormatType(
        name="PercentageType",
        base_type=decimal_type,
        format_string="##0.00%",
    )
    assert percent_type.name == "PercentageType"


def test_type_equality() -> None:








    """Test type equality comparison."""
    type1 = Type("integer", is_array=True, array_bounds=[10])
    type2 = Type("integer", is_array=True, array_bounds=[10])
    type3 = Type("integer", is_array=True, array_bounds=[20])

    assert type1 == type2
    assert type1 != type3
    assert hash(type1) == hash(type2)
    assert hash(type1) != hash(type3)


def test_type_array_conversion() -> None:








    """Test type array conversion."""
    # Non-array to array
    type1 = Type("integer")
    type1.is_array = True
    type1.array_bounds = [10]

    assert type1.is_array
    assert type1.array_bounds == [10]

    # Array to non-array
    type2 = Type("string", is_array=True, array_bounds=[5])
    type2.is_array = False
    type2.array_bounds = None

    assert not type2.is_array
    assert type2.array_bounds is None
