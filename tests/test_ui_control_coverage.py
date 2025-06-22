"""Test UI control type coverage."""

import json
from pathlib import Path

from generate.converters.ui_converter import UIConverter


def test_ui_control_coverage():






    """Test that all UI control types are properly covered."""

    converter = UIConverter()

    # List of all PowerBuilder control types that should be supported
    expected_controls = [
        # Basic controls
        "statictext",
        "singlelineedit", 
        "multilineedit",
        "commandbutton",
        "picturebutton",
        "checkbox",
        "radiobutton",
        "dropdownlistbox",
        "listbox",
        "combobox",
        "picture",
        "groupbox",
        "tab",

        # Advanced controls
        "datawindow",
        "treeview",
        "listview",
        "graph",
        "richtextedit",
        "editmask",

        # Shape controls
        "line",
        "rectangle",
        "roundrectangle",
        "oval",

        # Progress controls
        "progressbar",
        "hprogressbar",
        "vprogressbar",

        # Slider controls
        "htrackbar",
        "vtrackbar",

        # Scrollbar controls
        "hscrollbar",
        "vscrollbar",

        # Date/Time controls
        "datepicker",
        "monthcalendar",

        # Ink controls
        "inkpicture",
        "inkedit",

        # Animation control
        "animation",

        # OLE control
        "ole",

        # MDI control
        "mdiclient",

        # NEW controls added
        "statichyperlink",
        "spin",
        "drawobject",
    ]

    # Test that all controls are in the converter's control map
    missing_controls = []
    for control in expected_controls:
        if control not in converter.control_map:
            missing_controls.append(control)

    assert len(missing_controls) == 0, f"Missing controls: {missing_controls}"
    print(f"✓ All {len(expected_controls)} control types are mapped")

    # Test conversion of new controls
    # Test StaticHyperLink
    result = converter.convert_control("statichyperlink", "link1", {
        "text": "Visit our website",
        "url": "https://example.com",
        "enabled": True,
        "textcolor": "blue",
    })
    assert result["widget"] == "InkWell"
    assert result["is_container"] == True
    assert "_linkText" in result["flutter_properties"]
    print("✓ StaticHyperLink control converts correctly")

    # Test Spin control
    result = converter.convert_control("spin", "spin1", {
        "value": 5,
        "minvalue": 0,
        "maxvalue": 100,
        "increment": 1,
        "acceleration": 2,
    })
    assert result["widget"] == "SpinBox"
    assert result["custom_widget"] == True
    assert "_currentValue" in result["flutter_properties"]
    print("✓ Spin control converts correctly")

    # Test DrawObject control
    result = converter.convert_control("drawobject", "draw1", {
        "drawtype": "rectangle",
        "fillcolor": "red",
        "linecolor": "black",
        "linewidth": 2,
    })
    assert result["widget"] == "CustomPaint"
    assert result["custom_widget"] == True
    assert "_drawingType" in result["flutter_properties"]
    print("✓ DrawObject control converts correctly")

    # Check that templates exist for custom widgets
    template_dir = Path("generate/flutter/templates")
    custom_templates = [
        "spin_box_widget.dart.jinja2",
        "static_hyperlink_widget.dart.jinja2",
        "draw_object_widget.dart.jinja2",
    ]

    missing_templates = []
    for template in custom_templates:
        if not (template_dir / template).exists():
            missing_templates.append(template)

    assert len(missing_templates) == 0, f"Missing templates: {missing_templates}"
    print(f"✓ All custom widget templates exist")

    # Check PowerBuilder Flutter mapping JSON
    mapping_file = Path("generate/flutter/powerbuilder_flutter_mapping.json")
    with open(mapping_file) as f:
        mapping = json.load(f)

    # Check that new controls are in advanced_controls
    advanced = mapping["control_mappings"]["advanced_controls"]
    assert "statichyperlink" in advanced, "StaticHyperLink not in mapping"
    assert "spin" in advanced, "Spin not in mapping"
    assert "drawobject" in advanced, "DrawObject not in mapping"
    print("✓ New controls added to PowerBuilder Flutter mapping")

    print(f"\n✅ UI control type coverage is complete with {len(converter.control_map)} controls!")


if __name__ == "__main__":
    test_ui_control_coverage()
