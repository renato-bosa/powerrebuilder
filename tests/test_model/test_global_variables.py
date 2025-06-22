"""Tests for PowerBuilder global variables.

This module contains tests for global variables, including registration and lookup.
"""

import pytest

from model.system.globals import (
    PBGlobalScope,
    PBGlobalVariable,
    get_all_global_variables,
    get_global_variable,
    get_global_variables_by_scope,
    register_global_variable,
)


class TestGlobalVariables:
    """Tests for PowerBuilder global variables."""

    def test_variable_registration(self):


        

        """Test variable registration and retrieval."""
        # Create a test variable
        test_var = PBGlobalVariable(
            name="TestVar",
            type_name="string",
            scope=PBGlobalScope.GLOBAL,
            description="Test variable",
            used_by={"application"},
        )

        # Register the variable
        registered = register_global_variable(test_var)

        # Verify registration
        assert registered is test_var
        assert get_global_variable("TestVar") is test_var
        assert get_global_variable("testvar") is test_var  # Case insensitive

        # Trying to register again should raise an error
        with pytest.raises(ValueError):
            register_global_variable(test_var)

    def test_get_nonexistent_variable(self):


        

        """Test getting a variable that doesn't exist."""
        assert get_global_variable("NonExistentVariable") is None

    def test_predefined_variables(self):


        

        """Test that predefined variables are registered."""
        # Common variables that should be registered
        common_vars = ["SQLCA", "Error", "True", "False", "Null", "TAB", "NEWLINE"]

        for var_name in common_vars:
            assert get_global_variable(var_name) is not None

    def test_get_variables_by_scope(self):


        

        """Test getting variables by scope."""
        # Get global scope variables
        global_vars = get_global_variables_by_scope(PBGlobalScope.GLOBAL)
        assert len(global_vars) > 0
        for var in global_vars:
            assert var.scope == PBGlobalScope.GLOBAL

        # Common global variables that should be included
        common_global_vars = ["SQLCA", "Message", "Error", "True", "False"]
        for var_name in common_global_vars:
            var = get_global_variable(var_name)
            assert var in global_vars

    def test_get_all_variables(self):


        

        """Test getting all global variables."""
        all_vars = get_all_global_variables()
        assert len(all_vars) > 0

        # Should include variables from various scopes
        var_scopes = {var.scope for var in all_vars}
        assert PBGlobalScope.GLOBAL in var_scopes

    def test_variable_properties(self):


        

        """Test variable properties."""
        # Test readonly variable
        true_var = get_global_variable("True")
        assert true_var is not None
        assert true_var.is_readonly is True
        assert true_var.default_value is True

        # Test variable with used_by property
        sqlca_var = get_global_variable("SQLCA")
        assert sqlca_var is not None
        assert len(sqlca_var.used_by) > 0
        assert "application" in sqlca_var.used_by
        assert "datawindow" in sqlca_var.used_by

    def test_button_constants(self):


        

        """Test button constant variables."""
        # Test button constants
        ok_var = get_global_variable("OK!")
        assert ok_var is not None
        assert ok_var.type_name == "integer"
        assert ok_var.default_value == 1

        cancel_var = get_global_variable("CANCEL!")
        assert cancel_var is not None
        assert cancel_var.type_name == "integer"
        assert cancel_var.default_value == 2

        yes_var = get_global_variable("YES!")
        assert yes_var is not None
        assert yes_var.type_name == "integer"
        assert yes_var.default_value == 1

        no_var = get_global_variable("NO!")
        assert no_var is not None
        assert no_var.type_name == "integer"
        assert no_var.default_value == 2

    def test_icon_constants(self):


        

        """Test icon constant variables."""
        # Test icon constants
        exclamation_var = get_global_variable("EXCLAMATION!")
        assert exclamation_var is not None
        assert exclamation_var.type_name == "integer"
        assert exclamation_var.default_value == 1

        information_var = get_global_variable("INFORMATION!")
        assert information_var is not None
        assert information_var.type_name == "integer"
        assert information_var.default_value == 2

        question_var = get_global_variable("QUESTION!")
        assert question_var is not None
        assert question_var.type_name == "integer"
        assert question_var.default_value == 3

        stopsign_var = get_global_variable("STOPSIGN!")
        assert stopsign_var is not None
        assert stopsign_var.type_name == "integer"
        assert stopsign_var.default_value == 4

    def test_custom_variable_registration(self):


        

        """Test registering custom variables."""
        # Create and register a custom variable
        custom_var = PBGlobalVariable(
            name="CustomSetting",
            type_name="string",
            scope=PBGlobalScope.SHARED,
            default_value="default",
            description="Custom application setting",
            is_readonly=False,
            used_by={"application", "window"},
        )
        register_global_variable(custom_var)

        # Get the variable and check properties
        var = get_global_variable("CustomSetting")
        assert var is not None
        assert var.type_name == "string"
        assert var.scope == PBGlobalScope.SHARED
        assert var.default_value == "default"
        assert var.description == "Custom application setting"
        assert var.is_readonly is False
        assert "application" in var.used_by
        assert "window" in var.used_by

        # Variable should be included in shared variables
        shared_vars = get_global_variables_by_scope(PBGlobalScope.SHARED)
        assert var in shared_vars
