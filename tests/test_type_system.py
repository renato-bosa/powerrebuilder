"""Tests for the consolidated type system."""

import pytest

from model.ast.types import (
    ArrayType,
    TypeBounds,
    TypeCategory,
    TypeRegistry,
)
from model.utils.errors import TypeValidationError
from model.utils.type_system import (
    create_type_from_info,
    format_type_info,
    normalize_type_name,
    validate_simple_type,
    validate_type_compatibility,
    validate_value_type,
)


def test_normalize_type_name():
    """Test normalizing type names."""
    assert normalize_type_name('int') == 'integer'
    assert normalize_type_name('str') == 'string'
    assert normalize_type_name('bool') == 'boolean'
    assert normalize_type_name('MyType') == 'MyType'
    assert normalize_type_name('INTEGER') == 'INTEGER'  # Preserves case


def test_validate_simple_type():
    """Test simple type validation."""
    # Valid types
    assert validate_simple_type({'name': 'integer', 'is_array': False, 'array_bounds': None})
    assert validate_simple_type({'name': 'string', 'is_array': True, 'array_bounds': [10]})
    assert validate_simple_type({'name': 'MyType', 'is_array': False})

    # Invalid name
    with pytest.raises(TypeValidationError, match="Invalid type name"):
        validate_simple_type({'name': 123})

    # Invalid is_array
    with pytest.raises(TypeValidationError, match="Invalid is_array value"):
        validate_simple_type({'name': 'string', 'is_array': 'yes'})

    # Invalid array bounds
    with pytest.raises(TypeValidationError, match="Invalid array bounds"):
        validate_simple_type({'name': 'string', 'array_bounds': 'large'})

    # Invalid array bounds values
    with pytest.raises(TypeValidationError, match="Array bounds must be positive integers"):
        validate_simple_type({'name': 'string', 'array_bounds': [-1, 0]})


def test_format_type_info():
    """Test formatting type information."""
    assert format_type_info({'name': 'integer', 'is_array': False}) == 'integer'
    assert format_type_info({'name': 'string', 'is_array': True, 'array_bounds': [10]}) == 'string[10]'
    assert format_type_info({'name': 'MyType', 'is_array': True}) == 'MyType[]'
    assert format_type_info({'name': 'int', 'is_array': False}) == 'integer'  # Normalizes names


def test_validate_type_compatibility():
    """Test type compatibility validation."""
    registry = TypeRegistry()

    # Same types
    int_type = registry.get_type('INTEGER')
    assert validate_type_compatibility(int_type, int_type)

    # Numeric type conversions
    int_type = registry.get_type('INTEGER')
    real_type = registry.get_type('REAL')
    dec_type = registry.get_type('DECIMAL')
    assert validate_type_compatibility(int_type, real_type)
    assert validate_type_compatibility(real_type, int_type)
    assert validate_type_compatibility(int_type, dec_type)

    # ANY type accepts anything
    any_type = registry.get_type('ANY')
    assert validate_type_compatibility(int_type, any_type)
    assert validate_type_compatibility(real_type, any_type)

    # Different incompatible types
    string_type = registry.get_type('STRING')
    boolean_type = registry.get_type('BOOLEAN')
    assert not validate_type_compatibility(int_type, string_type)
    assert not validate_type_compatibility(string_type, boolean_type)


def test_validate_value_type():
    """Test value type validation."""
    registry = TypeRegistry()

    # Basic types
    int_type = registry.get_type('INTEGER')
    string_type = registry.get_type('STRING')
    boolean_type = registry.get_type('BOOLEAN')

    assert validate_value_type(42, int_type)
    assert validate_value_type(3.14, int_type)  # Floats compatible with integer
    assert not validate_value_type("42", int_type)

    assert validate_value_type("hello", string_type)
    assert not validate_value_type(42, string_type)

    assert validate_value_type(True, boolean_type)
    assert validate_value_type(False, boolean_type)
    assert not validate_value_type(1, boolean_type)

    # Array types
    bounds = [TypeBounds(1, 10)]
    int_array_type = ArrayType(
        name="ARRAY OF INTEGER",
        category=TypeCategory.COMPOSITE,
        bounds=bounds,
        element_type=int_type,
    )

    assert validate_value_type([1, 2, 3], int_array_type)
    assert not validate_value_type("not an array", int_array_type)
    assert not validate_value_type([1, "two", 3], int_array_type)


def test_create_type_from_info():
    """Test creating Type objects from type information."""
    registry = TypeRegistry()

    # Basic type
    int_type = create_type_from_info({'name': 'INTEGER'}, registry)
    assert int_type.name == 'INTEGER'
    assert int_type.category == TypeCategory.NUMERIC
    assert not int_type.is_array

    # Array type
    string_array_type = create_type_from_info(
        {'name': 'STRING', 'is_array': True, 'array_bounds': [20]},
        registry,
    )
    assert string_array_type.name == 'ARRAY OF STRING'
    assert string_array_type.category == TypeCategory.COMPOSITE
    assert string_array_type.is_array
    assert len(string_array_type.bounds) == 1
    assert string_array_type.bounds[0].upper == 20

    # Custom type
    custom_type = create_type_from_info({'name': 'MyCustomType'}, registry)
    assert custom_type.name == 'MyCustomType'
    assert custom_type.category == TypeCategory.CUSTOM
