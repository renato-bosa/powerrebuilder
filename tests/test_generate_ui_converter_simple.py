"""Simple tests for the UI converter module."""

import pytest

from generate.converters.ui_converter import UIConverter


class TestUIConverter:
    """Test cases for PowerBuilder to Flutter UI conversion."""

    def setup_method(self):




        """Set up test instances."""
        self.converter = UIConverter()

    def test_control_mapping_exists(self):




        """Test that control mappings are loaded."""
        assert hasattr(self.converter, "control_map")
        assert len(self.converter.control_map) > 0

        # Check some basic controls exist
        assert "statictext" in self.converter.control_map
        assert "commandbutton" in self.converter.control_map
        assert "singlelineedit" in self.converter.control_map
        assert "datawindow" in self.converter.control_map

    def test_basic_control_conversion(self):




        """Test basic control conversion."""
        # Test a simple static text control
        control = self.converter.convert_control(
            control_type="statictext",
            control_name="st_label",
            properties={
                "text": '"Hello World"',
                "x": "10",
                "y": "20",
                "width": "100",
                "height": "20",
            },
        )

        assert control is not None
        assert control["widget"] == "Text"
        assert control["dart_name"] == "label"  # camelCase conversion with prefix removed

    def test_button_control_conversion(self):




        """Test button control conversion."""
        control = self.converter.convert_control(
            control_type="commandbutton",
            control_name="cb_save",
            properties={
                "text": '"Save"',
                "enabled": "true",
                "x": "10",
                "y": "10",
                "width": "80",
                "height": "25",
            },
        )

        assert control is not None
        assert control["widget"] == "ElevatedButton"
        assert control["dart_name"] == "save"  # prefix removed

    def test_textfield_control_conversion(self):




        """Test text field control conversion."""
        control = self.converter.convert_control(
            control_type="singlelineedit",
            control_name="sle_name",
            properties={
                "text": '"Default"',
                "maxlength": "50",
                "enabled": "true",
            },
        )

        assert control is not None
        assert control["widget"] == "TextField"
        assert control["dart_name"] == "name"  # prefix removed
        assert control.get("requires_controller") is True
        assert control.get("controller_type") == "TextEditingController"

    def test_unknown_control_handling(self):




        """Test handling of unknown control types."""
        control = self.converter.convert_control(
            control_type="unknowncontrol",
            control_name="uc_test",
            properties={},
        )

        assert control is not None
        assert control["widget"] == "Container"
        assert control["type"] == "unknowncontrol"

    def test_camel_case_conversion(self):




        """Test snake_case to camelCase conversion."""
        # Note: _to_camel_case removes common prefixes
        assert self.converter._to_camel_case("cb_save_button") == "saveButton"
        assert self.converter._to_camel_case("st_label") == "label"
        assert self.converter._to_camel_case("dw_1") == "1"
        assert self.converter._to_camel_case("sle_customer_name") == "customerName"
        # Without prefix
        assert self.converter._to_camel_case("save_button") == "saveButton"

    def test_get_widget_imports(self):




        """Test widget import generation."""
        controls = [
            {"widget": "Text", "name": "label"},
            {"widget": "TextField", "name": "input"},
            {"widget": "ElevatedButton", "name": "button"},
            {"widget": "DataTable", "name": "table"},
        ]

        imports = self.converter.get_widget_imports(controls)

        assert "import 'package:flutter/material.dart';" in imports
        # DataTable might require additional imports
        assert len(imports) >= 1

    def test_color_conversion(self):




        """Test PowerBuilder color to Flutter color conversion."""
        # Integer colors are converted to RGB
        assert self.converter._convert_color(0) == "Color.fromRGBO(0, 0, 0, 1.0)"
        assert self.converter._convert_color(255) == "Color.fromRGBO(255, 0, 0, 1.0)"

        # String named colors
        assert self.converter._convert_color("black") == "Colors.black"
        assert self.converter._convert_color("white") == "Colors.white"
        assert self.converter._convert_color("red") == "Colors.red"

    def test_boolean_conversion(self):




        """Test boolean value conversion."""
        assert self.converter._convert_boolean("true") == "true"
        assert self.converter._convert_boolean("false") == "false"
        assert self.converter._convert_boolean("1") == "true"
        assert self.converter._convert_boolean("0") == "false"
        assert self.converter._convert_boolean("yes") == "true"
        assert self.converter._convert_boolean("no") == "false"

    def test_alignment_conversion(self):




        """Test alignment conversion."""
        assert self.converter._convert_alignment("left") == "TextAlign.left"
        assert self.converter._convert_alignment("center") == "TextAlign.center"
        assert self.converter._convert_alignment("right") == "TextAlign.right"
        assert self.converter._convert_alignment("0") == "TextAlign.left"
        assert self.converter._convert_alignment("1") == "TextAlign.right"
        assert self.converter._convert_alignment("2") == "TextAlign.center"
        # Unknown defaults to left
        assert self.converter._convert_alignment("unknown") == "TextAlign.left"

    def test_datawindow_control(self):




        """Test DataWindow control conversion."""
        control = self.converter.convert_control(
            control_type="datawindow",
            control_name="dw_list",
            properties={
                "dataobject": '"d_customer_list"',
                "x": "10",
                "y": "50",
                "width": "600",
                "height": "400",
            },
        )

        assert control is not None
        assert control["widget"] == "DataWindowWidget"
        assert control["dart_name"] == "list"  # prefix removed
        assert control.get("custom_widget") is True


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
