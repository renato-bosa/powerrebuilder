"""Tests for PowerBuilder system functions.

This module contains tests for system functions, including registration and lookup.
"""

import pytest

from model.system.functions import (
    PBFunctionCategory,
    PBParameter,
    PBSystemFunction,
    get_all_system_functions,
    get_system_function,
    get_system_functions_by_category,
    register_system_function,
)


class TestSystemFunctions:
    """Tests for PowerBuilder system functions."""

    def test_function_registration(self):
        """Test function registration and retrieval."""
        # Create a test function
        test_function = PBSystemFunction(
            name="TestFunc",
            category=PBFunctionCategory.STRING,
            return_type="string",
            parameters=[
                PBParameter(name="input", type_name="string"),
            ],
            description="Test function",
        )

        # Register the function
        registered = register_system_function(test_function)

        # Verify registration
        assert registered is test_function
        assert get_system_function("TestFunc") is test_function
        assert get_system_function("testfunc") is test_function  # Case insensitive

        # Trying to register again should raise an error
        with pytest.raises(ValueError):
            register_system_function(test_function)

    def test_get_nonexistent_function(self):
        """Test getting a function that doesn't exist."""
        assert get_system_function("NonExistentFunction") is None

    def test_predefined_functions(self):
        """Test that predefined functions are registered."""
        # Common functions that should be registered
        common_functions = ["Len", "Left", "Right", "Mid", "Abs", "Today", "MessageBox"]

        for func_name in common_functions:
            assert get_system_function(func_name) is not None

    def test_get_functions_by_category(self):
        """Test getting functions by category."""
        # Get string functions
        string_funcs = get_system_functions_by_category(PBFunctionCategory.STRING)
        assert len(string_funcs) > 0
        for func in string_funcs:
            assert func.category == PBFunctionCategory.STRING

        # Common string functions that should be included
        common_string_funcs = ["Len", "Left", "Right", "Mid", "Trim", "Upper", "Lower"]
        for func_name in common_string_funcs:
            func = get_system_function(func_name)
            assert func in string_funcs

        # Get math functions
        math_funcs = get_system_functions_by_category(PBFunctionCategory.MATH)
        assert len(math_funcs) > 0
        for func in math_funcs:
            assert func.category == PBFunctionCategory.MATH

        # Common math functions that should be included
        common_math_funcs = ["Abs", "Ceiling", "Floor", "Round", "Sqrt"]
        for func_name in common_math_funcs:
            func = get_system_function(func_name)
            assert func in math_funcs

    def test_get_all_functions(self):
        """Test getting all system functions."""
        all_funcs = get_all_system_functions()
        assert len(all_funcs) > 0

        # Should include functions from various categories
        categories = {func.category for func in all_funcs}
        assert PBFunctionCategory.STRING in categories
        assert PBFunctionCategory.MATH in categories
        assert PBFunctionCategory.DATE in categories

    def test_parameter_properties(self):
        """Test function parameter properties."""
        # Test Mid function which has an optional parameter
        mid_func = get_system_function("Mid")
        assert mid_func is not None
        assert len(mid_func.parameters) == 3
        assert mid_func.parameters[0].name == "string"
        assert mid_func.parameters[0].type_name == "string"
        assert not mid_func.parameters[0].is_optional

        assert mid_func.parameters[2].name == "length"
        assert mid_func.parameters[2].type_name == "integer"
        assert mid_func.parameters[2].is_optional

        # Test FileRead function which has a reference parameter
        fileread_func = get_system_function("FileRead")
        assert fileread_func is not None
        assert len(fileread_func.parameters) == 2
        assert fileread_func.parameters[1].name == "buffer"
        assert fileread_func.parameters[1].is_reference

    def test_function_examples(self):
        """Test function examples."""
        # Test examples for common functions
        len_func = get_system_function("Len")
        assert len_func is not None
        assert len(len_func.examples) > 0
        assert "len('Hello World')" in len_func.examples[0]

        abs_func = get_system_function("Abs")
        assert abs_func is not None
        assert len(abs_func.examples) > 0
        assert "Abs(-5.7)" in abs_func.examples[0]

    def test_deprecated_functions(self):
        """Test deprecated function properties."""
        # Register a deprecated function for testing
        deprecated_func = PBSystemFunction(
            name="OldFunc",
            category=PBFunctionCategory.STRING,
            return_type="string",
            parameters=[
                PBParameter(name="input", type_name="string"),
            ],
            description="Old deprecated function",
            is_deprecated=True,
            alternative="NewFunc",
            version_introduced="5.0",
            version_deprecated="8.0",
        )
        register_system_function(deprecated_func)

        # Get the function and check properties
        func = get_system_function("OldFunc")
        assert func is not None
        assert func.is_deprecated
        assert func.alternative == "NewFunc"
        assert func.version_introduced == "5.0"
        assert func.version_deprecated == "8.0"

    def test_function_categories(self):
        """Test all function categories have at least one function."""
        for category in PBFunctionCategory:
            funcs = get_system_functions_by_category(category)
            assert len(funcs) > 0, (
                f"No functions registered for category {category.name}"
            )

    def test_custom_function_registration(self):
        """Test registering custom functions."""
        # Create and register a custom function
        custom_func = PBSystemFunction(
            name="CustomCalculation",
            category=PBFunctionCategory.MATH,
            return_type="double",
            parameters=[
                PBParameter(name="value1", type_name="double"),
                PBParameter(name="value2", type_name="double"),
                PBParameter(name="operation", type_name="string"),
            ],
            description="Performs a custom calculation based on the operation",
            examples=["CustomCalculation(10.5, 5.2, 'multiply') // Returns 54.6"],
        )
        register_system_function(custom_func)

        # Get the function and check properties
        func = get_system_function("CustomCalculation")
        assert func is not None
        assert func.category == PBFunctionCategory.MATH
        assert func.return_type == "double"
        assert len(func.parameters) == 3

        # Function should be included in math functions
        math_funcs = get_system_functions_by_category(PBFunctionCategory.MATH)
        assert func in math_funcs
