"""Tests for PowerBuilder system events.

This module contains tests for system events, including registration and lookup.
"""

import pytest

from model.system.events import (
    PBSystemEvent,
    PBSystemEventType,
    get_all_system_events,
    get_system_event,
    get_system_events_by_type,
    register_system_event,
)


class TestSystemEvents:
    """Tests for PowerBuilder system events."""

    def test_event_registration(self):


        

        """Test event registration and retrieval."""
        # Create a test event
        test_event = PBSystemEvent(
            name="TestEvent",
            event_type=PBSystemEventType.CONTROL,
            description="Test event",
            object_types={"commandbutton"},
        )

        # Register the event
        registered = register_system_event(test_event)

        # Verify registration
        assert registered is test_event
        assert get_system_event("TestEvent") is test_event
        assert get_system_event("testevent") is test_event  # Case insensitive
        assert (
            get_system_event("TestEvent", PBSystemEventType.CONTROL) is test_event
        )  # With type

        # Trying to register again should raise an error
        with pytest.raises(ValueError):
            register_system_event(test_event)

        # Create a test event with the same name but different type
        test_event2 = PBSystemEvent(
            name="TestEvent",
            event_type=PBSystemEventType.WINDOW,
            description="Test window event",
            object_types={"window"},
        )

        # We can register it with a different type
        register_system_event(test_event2)

        # When we get by name only, we get the first one registered
        assert get_system_event("TestEvent") is test_event

        # But we can get by name and type
        assert get_system_event("TestEvent", PBSystemEventType.CONTROL) is test_event
        assert get_system_event("TestEvent", PBSystemEventType.WINDOW) is test_event2

    def test_get_nonexistent_event(self):


        

        """Test getting an event that doesn't exist."""
        assert get_system_event("NonExistentEvent") is None
        assert get_system_event("NonExistentEvent", PBSystemEventType.WINDOW) is None

    def test_predefined_events(self):


        

        """Test that predefined events are registered."""
        # Common events that should be registered
        common_events = ["open", "close", "clicked", "getfocus", "losefocus"]

        for event_name in common_events:
            assert get_system_event(event_name) is not None

    def test_get_events_by_type(self):


        

        """Test getting events by type."""
        # Get window events
        window_events = get_system_events_by_type(PBSystemEventType.WINDOW)
        assert len(window_events) > 0
        for event in window_events:
            assert event.event_type == PBSystemEventType.WINDOW

        # Common window events that should be included
        common_window_events = ["open", "close", "resize", "activate", "deactivate"]
        for event_name in common_window_events:
            event = get_system_event(event_name, PBSystemEventType.WINDOW)
            assert event in window_events

        # Get control events
        control_events = get_system_events_by_type(PBSystemEventType.CONTROL)
        assert len(control_events) > 0
        for event in control_events:
            assert event.event_type == PBSystemEventType.CONTROL

        # Common control events that should be included
        common_control_events = ["clicked", "doubleclicked", "getfocus", "losefocus"]
        for event_name in common_control_events:
            event = get_system_event(event_name, PBSystemEventType.CONTROL)
            if event:
                assert event in control_events

    def test_get_all_events(self):


        

        """Test getting all system events."""
        all_events = get_all_system_events()
        assert len(all_events) > 0

        # Should include events from various categories
        event_types = {event.event_type for event in all_events}
        assert PBSystemEventType.WINDOW in event_types
        assert PBSystemEventType.CONTROL in event_types
        assert PBSystemEventType.MENU in event_types

    def test_event_parameters(self):


        

        """Test event parameter properties."""
        # Test resize event which has parameters
        resize_event = get_system_event("resize", PBSystemEventType.WINDOW)
        assert resize_event is not None
        assert len(resize_event.parameters) > 0
        assert "sizetype" in resize_event.parameters[0]["name"]
        assert "newwidth" in resize_event.parameters[1]["name"]
        assert "newheight" in resize_event.parameters[2]["name"]

    def test_event_object_types(self):


        

        """Test event object type properties."""
        # Test clicked event which applies to multiple control types
        clicked_event = get_system_event("clicked", PBSystemEventType.CONTROL)
        assert clicked_event is not None
        assert len(clicked_event.object_types) > 0
        assert "commandbutton" in clicked_event.object_types
        assert "checkbox" in clicked_event.object_types

    def test_events_with_same_name(self):


        

        """Test events with the same name but different types."""
        # Get clicked events for different types
        control_clicked = get_system_event("clicked", PBSystemEventType.CONTROL)
        menu_clicked = get_system_event("clicked", PBSystemEventType.MENU)

        # Both should exist but be different events
        assert control_clicked is not None
        assert menu_clicked is not None
        assert control_clicked is not menu_clicked
        assert control_clicked.event_type == PBSystemEventType.CONTROL
        assert menu_clicked.event_type == PBSystemEventType.MENU

    def test_custom_event_registration(self):


        

        """Test registering custom events."""
        # Create and register a custom event
        custom_event = PBSystemEvent(
            name="CustomEvent",
            event_type=PBSystemEventType.USER_OBJECT,
            description="Custom user object event",
            parameters=[
                {"name": "data", "type": "string"},
                {"name": "id", "type": "integer"},
            ],
            return_type="boolean",
            object_types={"userobject"},
        )
        register_system_event(custom_event)

        # Get the event and check properties
        event = get_system_event("CustomEvent")
        assert event is not None
        assert event.event_type == PBSystemEventType.USER_OBJECT
        assert event.description == "Custom user object event"
        assert len(event.parameters) == 2
        assert event.parameters[0]["name"] == "data"
        assert event.parameters[1]["name"] == "id"
        assert event.return_type == "boolean"
        assert "userobject" in event.object_types

        # Event should be included in user object events
        user_object_events = get_system_events_by_type(PBSystemEventType.USER_OBJECT)
        assert event in user_object_events
