"""Tests for the UI converter module."""

import pytest
from generate.converters.ui_converter import UIConverter


class TestUIConverter:
    """Test cases for PowerBuilder to Flutter UI conversion."""

    def setup_method(self):
        """Set up test instances."""
        self.converter = UIConverter()

    def test_basic_control_conversions(self):
        """Test basic PowerBuilder control to Flutter widget conversions."""
        # Text controls
        assert self.converter.convert_control_type("statictext") == "Text"
        assert self.converter.convert_control_type("singlelineedit") == "TextField"
        assert self.converter.convert_control_type("multilineedit") == "TextField"
        assert self.converter.convert_control_type("editmask") == "TextFormField"

        # Button controls
        assert self.converter.convert_control_type("commandbutton") == "ElevatedButton"
        assert self.converter.convert_control_type("picturebutton") == "IconButton"

        # Selection controls
        assert self.converter.convert_control_type("checkbox") == "Checkbox"
        assert self.converter.convert_control_type("radiobutton") == "Radio"
        assert self.converter.convert_control_type("dropdownlistbox") == "DropdownButton"
        assert self.converter.convert_control_type("listbox") == "ListView"

        # Container controls
        assert self.converter.convert_control_type("groupbox") == "Container"
        assert self.converter.convert_control_type("tab") == "TabBarView"
        assert self.converter.convert_control_type("userobject") == "Container"

        # Other controls
        assert self.converter.convert_control_type("picture") == "Image"
        assert self.converter.convert_control_type("picturelistbox") == "ListView"
        assert self.converter.convert_control_type("treeview") == "TreeView"
        assert self.converter.convert_control_type("listview") == "ListView"

    def test_datawindow_control_conversion(self):
        """Test DataWindow control conversion."""
        result = self.converter.convert_control_type("datawindow")
        assert result == "DataTable"

    def test_complex_control_conversions(self):
        """Test complex PowerBuilder control conversions."""
        # Graph control
        assert self.converter.convert_control_type("graph") == "Chart"
        
        # Rich text control
        assert self.converter.convert_control_type("richtextedit") == "RichText"
        
        # Progress bar
        assert self.converter.convert_control_type("hprogressbar") == "LinearProgressIndicator"
        assert self.converter.convert_control_type("vprogressbar") == "LinearProgressIndicator"
        
        # Scroll bars
        assert self.converter.convert_control_type("hscrollbar") == "Scrollbar"
        assert self.converter.convert_control_type("vscrollbar") == "Scrollbar"
        
        # Track bar
        assert self.converter.convert_control_type("htrackbar") == "Slider"
        assert self.converter.convert_control_type("vtrackbar") == "Slider"

    def test_menu_control_conversions(self):
        """Test menu-related control conversions."""
        assert self.converter.convert_control_type("menu") == "PopupMenuButton"
        assert self.converter.convert_control_type("menucascade") == "PopupMenuItem"
        assert self.converter.convert_control_type("menuitem") == "PopupMenuItem"

    def test_convert_properties(self):
        """Test property conversion from PowerBuilder to Flutter."""
        pb_props = {
            "text": '"Hello World"',
            "x": "100",
            "y": "200",
            "width": "300",
            "height": "50",
            "visible": "true",
            "enabled": "false",
            "backcolor": "255",
            "textcolor": "0",
            "font.face": '"Arial"',
            "font.height": "-10",
            "font.weight": "700"
        }
        
        flutter_props = self.converter.convert_properties("commandbutton", pb_props)
        
        assert "child" in flutter_props
        assert flutter_props["child"].startswith("Text('Hello World'")
        assert "onPressed" in flutter_props
        assert flutter_props["onPressed"] == "null"  # Disabled button

    def test_convert_position_properties(self):
        """Test position and size property conversion."""
        pb_props = {
            "x": "10",
            "y": "20",
            "width": "100",
            "height": "50"
        }
        
        position_props = self.converter.convert_position_properties(pb_props)
        
        assert position_props["left"] == 10.0
        assert position_props["top"] == 20.0
        assert position_props["width"] == 100.0
        assert position_props["height"] == 50.0

    def test_convert_color(self):
        """Test PowerBuilder color to Flutter color conversion."""
        # Basic colors
        assert self.converter.convert_color("0") == "Colors.black"
        assert self.converter.convert_color("16777215") == "Colors.white"
        assert self.converter.convert_color("255") == "Colors.red"
        assert self.converter.convert_color("65280") == "Colors.green"
        assert self.converter.convert_color("16711680") == "Colors.blue"
        
        # RGB color
        assert self.converter.convert_color("8421504").startswith("Color(0xFF")
        
        # System colors
        assert self.converter.convert_color("buttonface") == "Theme.of(context).colorScheme.surface"
        assert self.converter.convert_color("window") == "Theme.of(context).colorScheme.background"
        assert self.converter.convert_color("windowtext") == "Theme.of(context).colorScheme.onBackground"

    def test_convert_font_properties(self):
        """Test font property conversion."""
        pb_font = {
            "font.face": '"Arial"',
            "font.height": "-12",
            "font.weight": "700",
            "font.italic": "true"
        }
        
        flutter_font = self.converter.convert_font_properties(pb_font)
        
        assert flutter_font["fontFamily"] == "'Arial'"
        assert flutter_font["fontSize"] == 16.0  # Converted from points
        assert flutter_font["fontWeight"] == "FontWeight.bold"
        assert flutter_font["fontStyle"] == "FontStyle.italic"

    def test_convert_alignment(self):
        """Test alignment conversion."""
        assert self.converter.convert_alignment("left!") == "Alignment.centerLeft"
        assert self.converter.convert_alignment("center!") == "Alignment.center"
        assert self.converter.convert_alignment("right!") == "Alignment.centerRight"
        assert self.converter.convert_alignment("justify!") == "Alignment.center"

    def test_create_widget_tree(self):
        """Test creating a widget tree from control definitions."""
        controls = [
            {
                "type": "groupbox",
                "name": "gb_1",
                "properties": {
                    "text": '"Customer Info"',
                    "x": "10",
                    "y": "10",
                    "width": "400",
                    "height": "300"
                },
                "children": [
                    {
                        "type": "statictext",
                        "name": "st_1",
                        "properties": {
                            "text": '"Name:"',
                            "x": "20",
                            "y": "40",
                            "width": "100",
                            "height": "20"
                        }
                    },
                    {
                        "type": "singlelineedit",
                        "name": "sle_name",
                        "properties": {
                            "x": "130",
                            "y": "40",
                            "width": "200",
                            "height": "20"
                        }
                    }
                ]
            }
        ]
        
        widget_tree = self.converter.create_widget_tree(controls)
        
        assert len(widget_tree) == 1
        assert widget_tree[0]["type"] == "Container"
        assert len(widget_tree[0]["children"]) == 2
        assert widget_tree[0]["children"][0]["type"] == "Text"
        assert widget_tree[0]["children"][1]["type"] == "TextField"

    def test_convert_event_handler(self):
        """Test event handler conversion."""
        # Click event
        handler = self.converter.convert_event_handler("clicked", "commandbutton", "cb_ok_clicked()")
        assert handler == "onPressed"
        
        # Change event
        handler = self.converter.convert_event_handler("modified", "singlelineedit", "sle_name_modified()")
        assert handler == "onChanged"
        
        # Selection event
        handler = self.converter.convert_event_handler("selectionchanged", "listbox", "lb_items_selectionchanged()")
        assert handler == "onTap"

    def test_generate_widget_code(self):
        """Test widget code generation."""
        control = {
            "type": "commandbutton",
            "name": "cb_save",
            "properties": {
                "text": '"Save"',
                "x": "10",
                "y": "10",
                "width": "100",
                "height": "30",
                "enabled": "true"
            }
        }
        
        code = self.converter.generate_widget_code(control)
        
        assert "ElevatedButton(" in code
        assert "child: Text('Save')" in code
        assert "onPressed:" in code
        assert "Positioned(" in code  # Should be wrapped in Positioned

    def test_unknown_control_handling(self):
        """Test handling of unknown control types."""
        # Unknown control should return a Container with a comment
        result = self.converter.convert_control_type("unknowncontrol")
        assert result == "Container /* unknowncontrol */"

    def test_control_type_case_insensitivity(self):
        """Test that control type conversion is case-insensitive."""
        assert self.converter.convert_control_type("COMMANDBUTTON") == "ElevatedButton"
        assert self.converter.convert_control_type("CommandButton") == "ElevatedButton"
        assert self.converter.convert_control_type("StaticText") == "Text"

    def test_convert_border_style(self):
        """Test border style conversion."""
        assert self.converter.convert_border_style("StyleBox!") == "BoxDecoration(border: Border.all())"
        assert self.converter.convert_border_style("StyleLowered!") == "BoxDecoration(border: Border.all(color: Colors.grey))"
        assert self.converter.convert_border_style("StyleRaised!") == "BoxDecoration(border: Border.all(color: Colors.grey, width: 2))"
        assert self.converter.convert_border_style("StyleShadowBox!") == "BoxDecoration(boxShadow: [BoxShadow()])"

    def test_convert_edit_properties(self):
        """Test specific properties for edit controls."""
        pb_props = {
            "text": '"Default text"',
            "limit": "50",
            "password": "true",
            "displayonly": "false"
        }
        
        flutter_props = self.converter.convert_properties("singlelineedit", pb_props)
        
        assert "controller" in flutter_props
        assert "obscureText" in flutter_props
        assert flutter_props["obscureText"] == "true"
        assert "maxLength" in flutter_props
        assert flutter_props["maxLength"] == "50"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])