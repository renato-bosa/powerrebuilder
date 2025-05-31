"""Tests for PowerBuilder type nodes.

This module contains parametrized tests for all type-related AST nodes.
"""

import pytest

from model.ast.types import CustomType, FormatType, ParametrizedType, Type

# Test data for different type cases
TYPE_CASES = [
    (Type, {
        'name': 'integer',
        'is_array': False,
        'array_bounds': None,
    }),
    (Type, {
        'name': 'string',
        'is_array': True,
        'array_bounds': [10],
    }),
    (CustomType, {
        'name': 'MyType',
        'namespace': 'app',
        'is_array': False,
        'array_bounds': None,
    }),
    (ParametrizedType, {
        'base_type': Type('array'),
        'type_parameters': [Type('integer')],
        'is_array': False,
        'array_bounds': None,
    }),
    (FormatType, {
        'name': 'decimal',
        'format': '#,##0.00',
        'is_array': False,
        'array_bounds': None,
    }),
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
    type1 = Type('integer', is_array=True, array_bounds=[10])
    assert type1.is_array
    assert type1.array_bounds == [10]

    # Multi-dimension
    type2 = Type('string', is_array=True, array_bounds=[5, 10])
    assert type2.is_array
    assert type2.array_bounds == [5, 10]

    # No bounds
    type3 = Type('integer', is_array=True)
    assert type3.is_array
    assert type3.array_bounds is None


def test_custom_type_namespace() -> None:
    """Test custom type namespace handling."""
    type1 = CustomType('MyType', 'app')
    assert type1.name == 'MyType'
    assert type1.namespace == 'app'

    type2 = CustomType('OtherType')
    assert type2.name == 'OtherType'
    assert type2.namespace is None


def test_parametrized_type() -> None:
    """Test parametrized type handling."""
    base = Type('array')
    param = Type('integer')
    type_node = ParametrizedType(base, [param])

    assert type_node.base_type == base
    assert len(type_node.type_parameters) == 1
    assert type_node.type_parameters[0] == param


def test_format_type() -> None:
    """Test format type handling."""
    type_node = FormatType('decimal', '#,##0.00')
    assert type_node.name == 'decimal'
    assert type_node.format == '#,##0.00'


def test_type_equality() -> None:
    """Test type equality comparison."""
    type1 = Type('integer', is_array=True, array_bounds=[10])
    type2 = Type('integer', is_array=True, array_bounds=[10])
    type3 = Type('integer', is_array=True, array_bounds=[20])

    assert type1 == type2
    assert type1 != type3
    assert hash(type1) == hash(type2)
    assert hash(type1) != hash(type3)


def test_type_array_conversion() -> None:
    """Test type array conversion."""
    # Non-array to array
    type1 = Type('integer')
    type1.is_array = True
    type1.array_bounds = [10]

    assert type1.is_array
    assert type1.array_bounds == [10]

    # Array to non-array
    type2 = Type('string', is_array=True, array_bounds=[5])
    type2.is_array = False
    type2.array_bounds = None

    assert not type2.is_array
    assert type2.array_bounds is None
