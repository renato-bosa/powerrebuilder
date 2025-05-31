"""PowerBuilder system events.

This module defines classes and functions for PowerBuilder system events.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum, auto

from ..utils.base import PBNode


class PBSystemEventType(Enum):
    """Types of PowerBuilder system events."""

    WINDOW = auto()  # Window events
    CONTROL = auto()  # Control events
    MENU = auto()  # Menu events
    APPLICATION = auto()  # Application events
    USER_OBJECT = auto()  # User object events
    TRANSACTION = auto()  # Transaction events
    ERROR = auto()  # Error events
    DATAWINDOW = auto()  # DataWindow events
    PIPELINE = auto()  # Pipeline events
    SYSTEM = auto()  # System events
    OTHER = auto()  # Other events


@dataclass
class PBSystemEvent(PBNode):
    """PowerBuilder system event.

    Attributes:
        name: Event name
        event_type: Type of event
        ancestor_events: Events that this event can trigger
        description: Description of the event
        parameters: Parameters passed to the event handler
        return_type: Return type of the event handler
        is_deprecated: Whether the event is deprecated
        object_types: Object types that can handle this event
    """

    name: str
    event_type: PBSystemEventType
    ancestor_events: list[str] = field(default_factory=list)
    description: str | None = None
    parameters: list[dict[str, str]] = field(default_factory=list)
    return_type: str | None = None
    is_deprecated: bool = False
    object_types: set[str] = field(default_factory=set)


# Registry for system events
# Key is a tuple of (event_name_lower, event_type)
_SYSTEM_EVENTS: dict[tuple[str, PBSystemEventType], PBSystemEvent] = {}


def register_system_event(
    event: PBSystemEvent,
    target_classes=None,
    is_abstract: bool = False,
) -> None:
    """Register system-defined PowerBuilder events.

    Args:
        event: PBSystemEvent object containing event name and type
        target_classes: List of class types that can receive this event (not used currently)
        is_abstract: Whether this is an abstract event (implementation-dependent) (not used currently)
    """
    event_name_lower = event.name.lower()
    event_key = (event_name_lower, event.event_type)

    # Skip if already registered
    if event_key in _SYSTEM_EVENTS:
        return

    # Register the event
    _SYSTEM_EVENTS[event_key] = event


def get_system_event(
    name: str, event_type: PBSystemEventType | None = None,
) -> PBSystemEvent | None:
    """Get a system event by name and optionally by type.

    Args:
        name: The name of the event (case-insensitive)
        event_type: The type of the event (optional)

    Returns:
        The event, or None if not found
    """
    name_lower = name.lower()

    # If event_type is provided, look for that specific event
    if event_type is not None:
        return _SYSTEM_EVENTS.get((name_lower, event_type))

    # Otherwise, find all events with the given name and return the first one
    for (n, _), event in _SYSTEM_EVENTS.items():
        if n == name_lower:
            return event

    return None


def get_system_events_by_type(event_type: PBSystemEventType) -> list[PBSystemEvent]:
    """Get all system events of a specific type.

    Args:
        event_type: The event type to filter by

    Returns:
        List of events of the specified type
    """
    return [event for (_, t), event in _SYSTEM_EVENTS.items() if t == event_type]


def get_all_system_events() -> list[PBSystemEvent]:
    """Get all registered system events.

    Returns:
        List of all system events
    """
    return list(_SYSTEM_EVENTS.values())


# Register common PowerBuilder system events

# Window events
register_system_event(
    PBSystemEvent(
        name="open",
        event_type=PBSystemEventType.WINDOW,
        description="Occurs when a window is opened",
        parameters=[],
        return_type=None,
        object_types={"window"},
    ),
)

register_system_event(
    PBSystemEvent(
        name="close",
        event_type=PBSystemEventType.WINDOW,
        description="Occurs when a window is closed",
        parameters=[],
        return_type=None,
        object_types={"window"},
    ),
)

register_system_event(
    PBSystemEvent(
        name="resize",
        event_type=PBSystemEventType.WINDOW,
        description="Occurs when a window is resized",
        parameters=[
            {"name": "sizetype", "type": "unsignedlong"},
            {"name": "newwidth", "type": "integer"},
            {"name": "newheight", "type": "integer"},
        ],
        return_type=None,
        object_types={"window"},
    ),
)

register_system_event(
    PBSystemEvent(
        name="activate",
        event_type=PBSystemEventType.WINDOW,
        description="Occurs when a window is activated",
        parameters=[],
        return_type=None,
        object_types={"window"},
    ),
)

register_system_event(
    PBSystemEvent(
        name="deactivate",
        event_type=PBSystemEventType.WINDOW,
        description="Occurs when a window is deactivated",
        parameters=[],
        return_type=None,
        object_types={"window"},
    ),
)

# Control events
register_system_event(
    PBSystemEvent(
        name="clicked",
        event_type=PBSystemEventType.CONTROL,
        description="Occurs when a control is clicked",
        parameters=[],
        return_type=None,
        object_types={
            "commandbutton",
            "picturebutton",
            "checkbox",
            "radiobutton",
            "picturecontrol",
        },
    ),
)

register_system_event(
    PBSystemEvent(
        name="doubleclicked",
        event_type=PBSystemEventType.CONTROL,
        description="Occurs when a control is double-clicked",
        parameters=[],
        return_type=None,
        object_types={"listbox", "picturecontrol", "listview", "treeview"},
    ),
)

register_system_event(
    PBSystemEvent(
        name="getfocus",
        event_type=PBSystemEventType.CONTROL,
        description="Occurs when a control receives focus",
        parameters=[],
        return_type=None,
        object_types={
            "commandbutton",
            "picturebutton",
            "checkbox",
            "radiobutton",
            "editmask",
            "edit",
            "multilineedit",
            "singlelineedit",
        },
    ),
)

register_system_event(
    PBSystemEvent(
        name="losefocus",
        event_type=PBSystemEventType.CONTROL,
        description="Occurs when a control loses focus",
        parameters=[],
        return_type=None,
        object_types={
            "commandbutton",
            "picturebutton",
            "checkbox",
            "radiobutton",
            "editmask",
            "edit",
            "multilineedit",
            "singlelineedit",
        },
    ),
)

register_system_event(
    PBSystemEvent(
        name="modified",
        event_type=PBSystemEventType.CONTROL,
        description="Occurs when the contents of a control are modified",
        parameters=[],
        return_type=None,
        object_types={"editmask", "edit", "multilineedit", "singlelineedit"},
    ),
)

# Menu events
register_system_event(
    PBSystemEvent(
        name="clicked",
        event_type=PBSystemEventType.MENU,
        description="Occurs when a menu item is clicked",
        parameters=[],
        return_type=None,
        object_types={"menu"},
    ),
)

# Application events
register_system_event(
    PBSystemEvent(
        name="idle",
        event_type=PBSystemEventType.APPLICATION,
        description="Occurs when the application is idle",
        parameters=[],
        return_type=None,
        object_types={"application"},
    ),
)

register_system_event(
    PBSystemEvent(
        name="close",
        event_type=PBSystemEventType.APPLICATION,
        description="Occurs when the application is closing",
        parameters=[],
        return_type=None,
        object_types={"application"},
    ),
)

register_system_event(
    PBSystemEvent(
        name="error",
        event_type=PBSystemEventType.APPLICATION,
        description="Occurs when an application error occurs",
        parameters=[
            {"name": "error_number", "type": "integer"},
            {"name": "error_text", "type": "string"},
            {"name": "error_object", "type": "string"},
            {"name": "error_script", "type": "string"},
        ],
        return_type="integer",
        object_types={"application"},
    ),
)

# DataWindow events
register_system_event(
    PBSystemEvent(
        name="clicked",
        event_type=PBSystemEventType.DATAWINDOW,
        description="Occurs when a datawindow is clicked",
        parameters=[
            {"name": "row", "type": "integer"},
            {"name": "column", "type": "integer"},
        ],
        return_type=None,
        object_types={"datawindow"},
    ),
)

register_system_event(
    PBSystemEvent(
        name="itemchanged",
        event_type=PBSystemEventType.DATAWINDOW,
        description="Occurs when a datawindow item is changed",
        parameters=[
            {"name": "row", "type": "long"},
            {"name": "column", "type": "string"},
            {"name": "data", "type": "string"},
        ],
        return_type="integer",
        object_types={"datawindow"},
    ),
)

register_system_event(
    PBSystemEvent(
        name="rowfocuschanged",
        event_type=PBSystemEventType.DATAWINDOW,
        description="Occurs when the current row in a datawindow changes",
        parameters=[
            {"name": "currentrow", "type": "long"},
        ],
        return_type=None,
        object_types={"datawindow"},
    ),
)

register_system_event(
    PBSystemEvent(
        name="buttonclicked",
        event_type=PBSystemEventType.DATAWINDOW,
        description="Occurs when a button in a datawindow is clicked",
        parameters=[
            {"name": "row", "type": "long"},
            {"name": "object", "type": "string"},
        ],
        return_type=None,
        object_types={"datawindow"},
    ),
)

register_system_event(
    PBSystemEvent(
        name="retrievestart",
        event_type=PBSystemEventType.DATAWINDOW,
        description="Occurs when a retrieve operation is started",
        parameters=[],
        return_type="integer",
        object_types={"datawindow"},
    ),
)

register_system_event(
    PBSystemEvent(
        name="retrieveend",
        event_type=PBSystemEventType.DATAWINDOW,
        description="Occurs when a retrieve operation is completed",
        parameters=[
            {"name": "rowcount", "type": "long"},
        ],
        return_type=None,
        object_types={"datawindow"},
    ),
)

# Transaction events
register_system_event(
    PBSystemEvent(
        name="sqlpreview",
        event_type=PBSystemEventType.TRANSACTION,
        description="Occurs before a SQL statement is executed",
        parameters=[
            {"name": "sqlsyntax", "type": "string"},
            {"name": "error", "type": "long"},
        ],
        return_type="string",
        object_types={"transaction"},
    ),
)

register_system_event(
    PBSystemEvent(
        name="dberror",
        event_type=PBSystemEventType.TRANSACTION,
        description="Occurs when a database error occurs",
        parameters=[
            {"name": "sqldbcode", "type": "long"},
            {"name": "sqlerrtext", "type": "string"},
        ],
        return_type="integer",
        object_types={"transaction"},
    ),
)

# TreeView events
register_system_event(
    PBSystemEvent(
        name="selectionchanged",
        event_type=PBSystemEventType.CONTROL,
        description="Occurs when the selection in a treeview changes",
        parameters=[
            {"name": "oldhandle", "type": "long"},
            {"name": "newhandle", "type": "long"},
        ],
        return_type=None,
        object_types={"treeview"},
    ),
)

register_system_event(
    PBSystemEvent(
        name="itemexpanding",
        event_type=PBSystemEventType.CONTROL,
        description="Occurs when a treeview item is being expanded",
        parameters=[
            {"name": "handle", "type": "long"},
        ],
        return_type="long",
        object_types={"treeview"},
    ),
)

register_system_event(
    PBSystemEvent(
        name="itemcollapsing",
        event_type=PBSystemEventType.CONTROL,
        description="Occurs when a treeview item is being collapsed",
        parameters=[
            {"name": "handle", "type": "long"},
        ],
        return_type="long",
        object_types={"treeview"},
    ),
)

# ListView events
register_system_event(
    PBSystemEvent(
        name="selectionchanged",
        event_type=PBSystemEventType.CONTROL,
        description="Occurs when the selection in a listview changes",
        parameters=[],
        return_type=None,
        object_types={"listview"},
    ),
)

register_system_event(
    PBSystemEvent(
        name="columnclick",
        event_type=PBSystemEventType.CONTROL,
        description="Occurs when a column header in a listview is clicked",
        parameters=[
            {"name": "column", "type": "integer"},
        ],
        return_type=None,
        object_types={"listview"},
    ),
)

# RichText events
register_system_event(
    PBSystemEvent(
        name="textchanged",
        event_type=PBSystemEventType.CONTROL,
        description="Occurs when the text in a richtext control changes",
        parameters=[],
        return_type=None,
        object_types={"richtextedit"},
    ),
)

register_system_event(
    PBSystemEvent(
        name="selectionchanged",
        event_type=PBSystemEventType.CONTROL,
        description="Occurs when the selection in a richtext control changes",
        parameters=[],
        return_type=None,
        object_types={"richtextedit"},
    ),
)
