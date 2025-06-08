"""Tests for PowerBuilder type nodes.

This module contains parametrized tests for all type-related AST nodes.
"""

import pytest
from model.ast import (
    CustomType,
    Type,
)

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

# TODO: Add tests for ParametrizedType when implemented
# TODO: Add tests for FormatType when implemented

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
