"""Tests for PowerBuilder event nodes.

This module contains parametrized tests for all event-related AST nodes.
"""

import pytest

from model.ast import (
    Event,
    EventReference,
    EventTrigger,
    EventType,
    EventWord,
    PostEvent,
    TriggerEvent,
    Type,
)

# Test data for different event types
EVENT_CASES = [
    (
        Event,
        {
            "name": "clicked",
            "parameters": [],
            "body": [],
        },
    ),
    (
        Event,
        {
            "name": "itemchanged",
            "parameters": [
                {"name": "row", "type": Type("integer")},
                {"name": "col", "type": Type("integer")},
            ],
            "body": [],
        },
    ),
]

EVENT_TRIGGER_CASES = [
    (
        EventTrigger,
        {
            "event": Event("clicked"),
            "arguments": [],
        },
    ),
    (
        EventTrigger,
        {
            "event": Event("itemchanged"),
            "arguments": [1, 2],
        },
    ),
]

EVENT_TYPE_CASES = [
    (EventType, {"name": "clicked"}),
    (EventType, {"name": "getfocus"}),
    (EventType, {"name": "losefocus"}),
    (EventType, {"name": "modified"}),
]


@pytest.mark.parametrize(("cls", "attrs"), EVENT_CASES)
def test_event_creation(cls: type, attrs: dict) -> None:
    """Test event node creation and attributes."""
    event = cls(**attrs)
    assert isinstance(event, Event)
    for key, value in attrs.items():
        assert getattr(event, key) == value


@pytest.mark.parametrize(("cls", "attrs"), EVENT_TRIGGER_CASES)
def test_event_trigger_creation(cls: type, attrs: dict) -> None:
    """Test event trigger node creation and attributes."""
    trigger = cls(**attrs)
    assert isinstance(trigger, EventTrigger)
    for key, value in attrs.items():
        assert getattr(trigger, key) == value


@pytest.mark.parametrize(("cls", "attrs"), EVENT_TYPE_CASES)
def test_event_type_creation(cls: type, attrs: dict) -> None:
    """Test event type node creation and attributes."""
    event_type = cls(**attrs)
    assert isinstance(event_type, EventType)
    for key, value in attrs.items():
        assert getattr(event_type, key) == value


def test_event_reference() -> None:
    """Test event reference handling."""
    ref = EventReference("clicked", "button1")
    assert ref.event_name == "clicked"
    assert ref.control_name == "button1"


def test_event_word() -> None:
    """Test event word handling."""
    word = EventWord("clicked")
    assert word.value == "clicked"


def test_post_event() -> None:
    """Test post event handling."""
    event = PostEvent(
        "clicked",
        "button1",
        arguments=[1, 2],
    )
    assert event.event_name == "clicked"
    assert event.control_name == "button1"
    assert event.arguments == [1, 2]


def test_trigger_event() -> None:
    """Test trigger event handling."""
    event = TriggerEvent(
        "itemchanged",
        "dw_1",
        arguments=[1, 2],
    )
    assert event.event_name == "itemchanged"
    assert event.control_name == "dw_1"
    assert event.arguments == [1, 2]


def test_event_parameters() -> None:
    """Test event parameter handling."""
    event = Event(
        "itemchanged",
        parameters=[
            {"name": "row", "type": Type("integer")},
            {"name": "col", "type": Type("integer")},
        ],
        body=[],
    )
    assert len(event.parameters) == 2
    assert event.parameters[0]["name"] == "row"
    assert event.parameters[1]["name"] == "col"


def test_event_body() -> None:
    """Test event body handling."""
    event = Event(
        "clicked",
        parameters=[],
        body=[
            PostEvent("refresh", "dw_1"),
            TriggerEvent("itemchanged", "dw_2", [1, 2]),
        ],
    )
    assert len(event.body) == 2
    assert isinstance(event.body[0], PostEvent)
    assert isinstance(event.body[1], TriggerEvent)


def test_event_trigger_chaining() -> None:
    """Test event trigger chaining."""
    # Create a chain of events
    event1 = Event("clicked")
    event2 = Event("itemchanged")

    EventTrigger(event1)
    trigger2 = EventTrigger(event2, [1, 2])

    # Add triggers to event body
    event1.body = [trigger2]

    assert len(event1.body) == 1
    assert isinstance(event1.body[0], EventTrigger)
    assert event1.body[0].event == event2
