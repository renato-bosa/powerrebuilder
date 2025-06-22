"""Tests for PowerBuilder UI components.

This module contains parametrized tests for all UI component types.
"""

import pytest

from model.ui.ui_elements import (
    Control,
    Menu,
    UserObject,
    Window,
)

# Test data for different UI components
WINDOW_CASES = [
    (Window, {"name": "w_main", "title": "Main Window"}),
    (Window, {"name": "w_dialog", "title": "Dialog", "type": "response"}),
]

CONTROL_CASES = [
    (Control, {"name": "cb_ok", "text": "OK", "type": "commandbutton"}),
    (Control, {"name": "st_label", "text": "Label", "type": "statictext"}),
]

MENU_CASES = [
    (Menu, {"name": "m_file", "text": "File"}),
    (Menu, {"name": "m_edit", "text": "Edit"}),
]

USER_OBJECT_CASES = [
    (UserObject, {"name": "u_grid", "type": "grid"}),
    (UserObject, {"name": "u_tree", "type": "treeview"}),
]


@pytest.mark.parametrize(("cls", "attrs"), WINDOW_CASES)
def test_window_components(cls: type, attrs: dict[str, object]) -> None:

    
    
    """Test window component creation and attributes."""
    window = cls(**attrs)
    for key, value in attrs.items():
        assert getattr(window, key) == value


@pytest.mark.parametrize(("cls", "attrs"), CONTROL_CASES)
def test_control_components(cls: type, attrs: dict[str, object]) -> None:

    
    
    """Test control component creation and attributes."""
    control = cls(**attrs)
    for key, value in attrs.items():
        assert getattr(control, key) == value


@pytest.mark.parametrize(("cls", "attrs"), MENU_CASES)
def test_menu_components(cls: type, attrs: dict[str, object]) -> None:

    
    
    """Test menu component creation and attributes."""
    menu = cls(**attrs)
    for key, value in attrs.items():
        assert getattr(menu, key) == value


@pytest.mark.parametrize(("cls", "attrs"), USER_OBJECT_CASES)
def test_user_object_components(cls: type, attrs: dict[str, object]) -> None:

    
    
    """Test user object creation and attributes."""
    obj = cls(**attrs)
    for key, value in attrs.items():
        assert getattr(obj, key) == value


# Test UI element properties
def test_ui_element_properties() -> None:

    
    
    """Test UI element property handling."""
    control = Control(
        "cb_ok",
        "button",
        (10, 10),
        (80, 25),
        properties={"text": "OK", "enabled": "true"},
    )
    assert control.properties["text"] == "OK"
    assert control.properties["enabled"] == "true"


# Test control positioning
def test_control_positioning() -> None:

    
    
    """Test control position and size handling."""
    control = Control("st_label", "statictext", (10, 20), (100, 30))
    assert control.position == (10, 20)
    assert control.size == (100, 30)
