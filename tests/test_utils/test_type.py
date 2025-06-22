"""Test PowerBuilder type system functionality."""

import pytest

from common.types import normalize_type_name as normalize_type
from common.types import validate_simple_type as validate_type
from model.ast import PBArrayDesignation, PBArrayType, PBBasicType


def test_array_expression() -> None:








    """Test array expression functionality.

    Ported from reference/moose-pb-parser/PowerBuilder-Parser-AST/PWBASTArray.class.st
    """
    # Create array type
    int_type = PBBasicType(name="integer")
    array_type = PBArrayType(
        name="int_array",
        element_type=int_type,
        dimensions=[3],
    )

    # Create array expression
    expr = array_type.create_array_expression([1, 2, 3])
    assert len(expr) == 3
    assert expr[0] == 1
    assert expr[1] == 2
    assert expr[2] == 3
    assert str(expr) == "{1, 2, 3}"

    # Test iteration
    values = list(expr)
    assert values == [1, 2, 3]

    # Test validation
    assert array_type.validate_expression(expr)

    # Test invalid length
    invalid_expr = array_type.create_array_expression([1, 2])
    assert not array_type.validate_expression(invalid_expr)

    # Test array type string representation
    assert str(array_type) == "integer[3]"

    # Test dynamic size array
    dynamic_array = PBArrayType(
        name="dynamic_array",
        element_type=int_type,
        dimensions=[None],
    )
    dynamic_expr = dynamic_array.create_array_expression([1, 2, 3, 4, 5])
    assert dynamic_array.validate_expression(dynamic_expr)
    assert str(dynamic_array) == "integer[]"


def test_array_designation() -> None:








    """Test array designation functionality.

    Ported from reference/moose-pb-parser/PowerBuilder-Parser-AST/PWBASTArrayDesignation.class.st
    """
    # Test basic designation
    desig = PBArrayDesignation(expressions=[1, 2])
    assert len(desig) == 2
    assert desig[0] == 1
    assert desig[1] == 2
    assert str(desig) == "[1, 2]"

    # Test iteration
    values = list(desig)
    assert values == [1, 2]

    # Test with expressions
    desig = PBArrayDesignation(expressions=["i+1", "j*2"])
    assert str(desig) == "[i+1, j*2]"

    # Test with array expression
    int_type = PBBasicType(name="integer")
    array_type = PBArrayType(
        name="int_array",
        element_type=int_type,
        dimensions=[3],
    )

    expr = array_type.create_array_expression(
        expressions=[1, 2, 3],
        designation=PBArrayDesignation(expressions=["i"]),
    )
    assert str(expr) == "{1, 2, 3}[i]"


def test_type_normalization() -> None:








    """Test type name normalization."""
    # Test basic types
    assert normalize_type("int") == "integer"
    assert normalize_type("str") == "string"
    assert normalize_type("bool") == "boolean"
    assert normalize_type("dec") == "decimal"
    assert normalize_type("real") == "real"
    assert normalize_type("char") == "character"
    assert normalize_type("blob") == "blob"
    assert normalize_type("any") == "any"

    # Test custom types
    assert normalize_type("MyType") == "MyType"
    assert normalize_type("w_customer") == "w_customer"

    # Test case insensitivity
    assert normalize_type("INT") == "integer"
    assert normalize_type("Str") == "string"


def test_type_validation() -> None:








    """Test type validation."""
    # Test valid types
    assert validate_type({"name": "integer", "is_array": False, "array_bounds": None})
    assert validate_type({"name": "string", "is_array": True, "array_bounds": [10]})
    assert validate_type({"name": "MyType", "is_array": False, "array_bounds": None})

    # Test invalid types
    with pytest.raises(ValueError, match="name"):  # More specific match
        validate_type({"name": 123})  # Invalid name type
    with pytest.raises(ValueError, match="is_array"):
        validate_type({"name": "integer", "is_array": "yes"})  # Invalid is_array type
    with pytest.raises(ValueError, match="array_bounds"):
        validate_type(
            {"name": "string", "array_bounds": "large"},
        )  # Invalid bounds type
