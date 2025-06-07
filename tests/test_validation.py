"""Tests for validation utilities."""

import pytest

from common.exceptions import ValidationError
from model.utils.validation import (
    validate_access,
    validate_enum,
    validate_event,
    validate_name,
    validate_range,
    validate_required_fields,
    validate_unique,
)


def test_validate_access():
    """Test access modifier validation."""
    assert validate_access("public")
    assert validate_access("private")
    assert validate_access("protected")
    assert validate_access("global")
    assert validate_access("PUBLIC")  # Case insensitive
    assert not validate_access("invalid")
    assert not validate_access("")


def test_validate_event():
    """Test event type validation."""
    assert validate_event("clicked")
    assert validate_event("modified")
    assert validate_event("itemchanged")
    assert validate_event("getfocus")
    assert validate_event("losefocus")
    assert validate_event("constructor")
    assert validate_event("destructor")
    assert validate_event("open")
    assert validate_event("close")
    assert validate_event("CLICKED")  # Case insensitive
    assert not validate_event("invalid")
    assert not validate_event("")


def test_validate_name():
    """Test name validation according to conventions."""
    # Function names (camelCase)
    assert validate_name("calculateTotal", "function")
    assert validate_name("getValue", "function")
    assert not validate_name("CalculateTotal", "function")
    assert not validate_name("calculate-total", "function")
    assert not validate_name("_calculateTotal", "function")

    # Variable names (camelCase)
    assert validate_name("customerName", "variable")
    assert validate_name("totalAmount", "variable")
    assert not validate_name("CustomerName", "variable")
    assert not validate_name("customer-name", "variable")
    assert not validate_name("_customerName", "variable")

    # Constant names (UPPER_CASE)
    assert validate_name("MAX_VALUE", "constant")
    assert validate_name("DEFAULT_TIMEOUT", "constant")
    assert not validate_name("maxValue", "constant")
    assert not validate_name("Max_Value", "constant")
    assert not validate_name("MAX-VALUE", "constant")

    # Class names (PascalCase)
    assert validate_name("Customer", "class")
    assert validate_name("OrderItem", "class")
    assert validate_name("OrderItem123", "class")  # Numbers allowed
    assert not validate_name("customer", "class")
    assert not validate_name("order_item", "class")

    # Invalid convention
    with pytest.raises(ValidationError):
        validate_name("name", "invalid_convention")


def test_validate_required_fields():
    """Test required fields validation."""
    data = {
        "name": "John",
        "age": 30,
        "email": "john@example.com",
        "empty_string": "",
        "empty_list": [],
        "empty_dict": {},
        "zero": 0,
        "false": False,
    }

    # Single field
    assert validate_required_fields(data, ["name"])
    assert validate_required_fields(data, ["age"])
    assert not validate_required_fields(data, ["missing"])

    # Multiple fields
    assert validate_required_fields(data, ["name", "age", "email"])
    assert not validate_required_fields(data, ["name", "missing"])

    # Empty values
    assert not validate_required_fields(data, ["empty_string"])
    assert not validate_required_fields(data, ["empty_list"])
    assert not validate_required_fields(data, ["empty_dict"])

    # Zero and False are valid values
    assert validate_required_fields(data, ["zero"])
    assert validate_required_fields(data, ["false"])


def test_validate_range():
    """Test range validation."""
    # Both min and max
    assert validate_range(5, 0, 10)
    assert validate_range(0, 0, 10)  # Min boundary
    assert validate_range(10, 0, 10)  # Max boundary
    assert not validate_range(-1, 0, 10)  # Below min
    assert not validate_range(11, 0, 10)  # Above max

    # Only min
    assert validate_range(5, 0)
    assert validate_range(0, 0)  # Boundary
    assert not validate_range(-1, 0)  # Below min

    # Only max
    assert validate_range(5, None, 10)
    assert validate_range(10, None, 10)  # Boundary
    assert not validate_range(11, None, 10)  # Above max

    # No bounds
    assert validate_range(5)
    assert validate_range(-5)

    # Float values
    assert validate_range(5.5, 5.0, 10.0)
    assert not validate_range(4.9, 5.0, 10.0)


def test_validate_enum():
    """Test enum validation."""
    # List
    assert validate_enum("red", ["red", "green", "blue"])
    assert not validate_enum("yellow", ["red", "green", "blue"])

    # Set
    assert validate_enum("red", {"red", "green", "blue"})
    assert not validate_enum("yellow", {"red", "green", "blue"})

    # Dict (keys)
    assert validate_enum("red", {"red": 1, "green": 2, "blue": 3})
    assert not validate_enum("yellow", {"red": 1, "green": 2, "blue": 3})

    # Numbers
    assert validate_enum(1, [1, 2, 3])
    assert not validate_enum(4, [1, 2, 3])

    # Objects
    obj1 = object()
    obj2 = object()
    assert validate_enum(obj1, [obj1, obj2])
    assert not validate_enum(object(), [obj1, obj2])

    # Empty collections
    assert not validate_enum("anything", [])
    assert not validate_enum("anything", {})


def test_validate_unique():
    """Test uniqueness validation."""
    # Unique values
    assert validate_unique([1, 2, 3])
    assert validate_unique(["a", "b", "c"])
    assert validate_unique([])  # Empty list is valid

    # Duplicate values
    assert not validate_unique([1, 2, 1])
    assert not validate_unique(["a", "b", "a"])

    # Mixed types
    assert validate_unique([1, "a", True])
    assert not validate_unique([1, "a", 1])

    # Objects
    obj1 = object()
    obj2 = object()
    assert validate_unique([obj1, obj2])
    assert not validate_unique([obj1, obj2, obj1])
