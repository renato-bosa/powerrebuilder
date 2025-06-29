#!/usr/bin/env python3
"""Test event return type handling in EventConverter."""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

import pytest


class TestEventReturnTypes:
    """Test event return type handling functionality."""

    @pytest.fixture
    def event_converter(self):


        """Create EventConverter instance."""
        # Import here to avoid circular imports
        from src.generate.converters.flutter.state.event_converter import EventConverter
        from generate.converters.utils.expression_converter import ExpressionConverter
        from src.generate.converters.flutter.state.model_converter import TypeConverter

        type_converter = TypeConverter()
        expr_converter = ExpressionConverter(type_converter)
        return EventConverter(type_converter, expr_converter)

    def test_closequery_event_return_type(self, event_converter):




        """Test closequery event with bool return type."""
        # Test with return 0 (allow close)
        event = event_converter.convert_event(
            "closequery",
            [],
            ["IF not saved THEN", "  return 1", "END IF", "return 0"],
        )

        assert event.return_type == "Future<bool>"
        assert event.dart_return_type == "Future<bool>"
        assert event.is_async is True

        # Check body contains mapped return
        body_str = "\n".join(event.body)
        assert "return false;" in body_str  # return 1 maps to false
        assert "return true;" in body_str   # return 0 maps to true

    def test_itemerror_event_return_type(self, event_converter):




        """Test itemerror event with int return type."""
        event = event_converter.convert_event(
            "itemerror",
            [],
            ["MessageBox('Error', 'Invalid value')", "return 0"],
        )

        assert event.return_type == "int"
        assert event.dart_return_type == "int"

        # Check parameters
        assert len(event.parameters) == 4
        assert event.parameters[0].name == "rowIndex"
        assert event.parameters[1].name == "columnName"
        assert event.parameters[2].name == "value"
        assert event.parameters[3].name == "errorMessage"

        # Check body contains enum return
        body_str = "\n".join(event.body)
        assert "ValidationAction.reject.index" in body_str

    def test_key_event_return_type(self, event_converter):




        """Test key event with bool return type."""
        event = event_converter.convert_event(
            "key",
            [],
            ["IF key = KeyF1! THEN", "  ShowHelp()", "  return 1", "END IF"],
        )

        assert event.return_type == "bool"
        assert event.dart_return_type == "bool"

        # Check parameter
        assert len(event.parameters) == 1
        assert event.parameters[0].name == "event"
        assert event.parameters[0].dart_type == "KeyEvent"

        # Check body
        body_str = "\n".join(event.body)
        assert "return true;" in body_str  # return 1 maps to true

    def test_itemchanging_event_return_type(self, event_converter):




        """Test itemchanging event with bool return type."""
        event = event_converter.convert_event(
            "itemchanging",
            [],
            ["IF newvalue < 0 THEN", "  return 1", "END IF", "return 0"],
        )

        assert event.return_type == "bool"

        # Check parameters
        assert len(event.parameters) == 2
        assert event.parameters[0].name == "oldValue"
        assert event.parameters[1].name == "newValue"

        # Check body
        body_str = "\n".join(event.body)
        assert "return false;" in body_str  # return 1 maps to false
        assert "return true;" in body_str   # return 0 maps to true

    def test_updatestart_event_async_return(self, event_converter):




        """Test updatestart event with async bool return."""
        event = event_converter.convert_event(
            "updatestart",
            [],
            ["IF ValidateData() THEN", "  return 0", "ELSE", "  return 1", "END IF"],
        )

        assert event.return_type == "Future<bool>"
        assert event.is_async is True

        # Check body
        body_str = "\n".join(event.body)
        assert "return true;" in body_str   # return 0 maps to true
        assert "return false;" in body_str  # return 1 maps to false

    def test_event_without_return_type(self, event_converter):




        """Test event without specific return type."""
        event = event_converter.convert_event(
            "clicked",
            [],
            ["OpenWindow(w_details)"],
        )

        assert event.return_type == "void"
        assert event.dart_return_type == "void"

    def test_generic_event_inferred_return(self, event_converter):




        """Test generic event with inferred return type."""
        # Unknown event that returns bool
        event = event_converter.convert_event(
            "custom_validate",
            [],
            ["IF value > 100 THEN", "  return false", "END IF", "return true"],
        )

        # Should infer bool return type
        assert event.return_type == "bool"
        assert event.dart_return_type == "bool"

    def test_event_default_return_values(self, event_converter):




        """Test default return values for events."""
        # Event with return type but no explicit return
        event = event_converter.convert_event(
            "closequery",
            [],
            ["SaveData()"],
        )

        # Should have default return
        body_str = "\n".join(event.body)
        assert "return true; // Default: allow action" in body_str

    def test_rowfocuschanging_event(self, event_converter):




        """Test rowfocuschanging event with parameters and return."""
        event = event_converter.convert_event(
            "rowfocuschanging",
            [],
            ["IF newRow <= 0 THEN", "  return 1", "END IF"],
        )

        assert event.return_type == "bool"

        # Check parameters
        assert len(event.parameters) == 2
        assert event.parameters[0].name == "currentRow"
        assert event.parameters[0].dart_type == "int"
        assert event.parameters[1].name == "newRow"
        assert event.parameters[1].dart_type == "int"

    def test_event_registration_with_return_types(self, event_converter):




        """Test event registration code generation."""
        # Simple callback
        reg = event_converter.get_event_registration("clicked", "_clickedHandler")
        assert reg == "onPressed: _clickedHandler"

        # ValueChanged callback
        reg = event_converter.get_event_registration("modified", "_modifiedHandler")
        assert reg == "onChanged: (value) => _modifiedHandler(value)"

        # Complex callback with multiple params
        reg = event_converter.get_event_registration("itemerror", "_itemErrorHandler")
        assert reg == "onValidationError: (row, col, val, err) => _itemErrorHandler(row, col, val, err)"

        # Bool returning callbacks
        reg = event_converter.get_event_registration("itemchanging", "_itemChangingHandler")
        assert reg == "onChanging: (oldVal, newVal) => _itemChangingHandler(oldVal, newVal)"

    def test_get_event_enums(self, event_converter):




        """Test generation of event-related enums."""
        enums = event_converter.get_event_enums()

        assert len(enums) > 0

        # Check ValidationAction enum
        validation_enum = enums[0]
        assert "enum ValidationAction" in validation_enum
        assert "reject," in validation_enum
        assert "accept," in validation_enum
        assert "rejectAllowFocusChange," in validation_enum
        assert "rejectNoMessage," in validation_enum

    def test_extract_return_value(self, event_converter):




        """Test return value extraction."""
        # Test positive numbers
        assert event_converter._extract_return_value("return 0") == 0
        assert event_converter._extract_return_value("return 1") == 1
        assert event_converter._extract_return_value("return 42") == 42

        # Test negative numbers
        assert event_converter._extract_return_value("return -1") == -1

        # Test with whitespace
        assert event_converter._extract_return_value("  return   5  ") == 5

        # Test non-numeric returns
        assert event_converter._extract_return_value("return true") is None
        assert event_converter._extract_return_value("return somevar") is None

    def test_infer_return_type(self, event_converter):




        """Test return type inference."""
        # Infer int
        assert event_converter._infer_return_type(["return 0"]) == "int"
        assert event_converter._infer_return_type(["IF x THEN", "return -1"]) == "int"

        # Infer bool
        assert event_converter._infer_return_type(["return true"]) == "bool"
        assert event_converter._infer_return_type(["return FALSE"]) == "bool"

        # Infer String
        assert event_converter._infer_return_type(['return "hello"']) == "String"
        assert event_converter._infer_return_type(["return 'world'"]) == "String"

        # No return
        assert event_converter._infer_return_type(["x = 1", "y = 2"]) is None


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
