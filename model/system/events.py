"""PowerBuilder system event definitions.

This module contains definitions for PowerBuilder system events.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum, auto
from typing import Any

from model.utils.base import PBNode


class PBSystemEventType(Enum):
    """Types of system events in PowerBuilder."""
    
    # Window events
    ACTIVATE = auto()
    CLICKED = auto()
    CLOSE = auto()
    CLOSEQUERY = auto()
    DEACTIVATE = auto()
    DOUBLECLICKED = auto()
    DRAGDROP = auto()
    DRAGENTER = auto()
    DRAGLEAVE = auto()
    DRAGWITHIN = auto()
    GETFOCUS = auto()
    HIDE = auto()
    HOTLINKALARM = auto()
    IDLE = auto()
    KEY = auto()
    LOSEFOCUS = auto()
    MOUSEDOWN = auto()
    MOUSEMOVE = auto()
    MOUSEUP = auto()
    MOVED = auto()
    OPEN = auto()
    OTHER = auto()
    RBUTTONDOWN = auto()
    RESIZE = auto()
    SHOW = auto()
    SYSTEMERROR = auto()
    SYSTEMKEY = auto()
    TIMER = auto()
    TOOLBARMOVED = auto()
    
    # Control events
    CONSTRUCTOR = auto()
    DESTRUCTOR = auto()
    DRAGDROPOBJECT = auto()
    MODIFIED = auto()
    SELECTIONCHANGED = auto()
    SELECTIONCHANGING = auto()
    VALUECHANGED = auto()
    
    # DataWindow events
    CLICKED_DW = auto()
    DOUBLECLICKED_DW = auto()
    ERROR = auto()
    ITEMCHANGED = auto()
    ITEMERROR = auto()
    ITEMFOCUSCHANGED = auto()
    RBUTTONDOWN_DW = auto()
    RETRIEVEEND = auto()
    RETRIEVEROW = auto()
    RETRIEVESTART = auto()
    ROWFOCUSCHANGED = auto()
    ROWFOCUSCHANGING = auto()
    SQLPREVIEW = auto()
    UPDATEEND = auto()
    UPDATESTART = auto()


@dataclass
class PBSystemEventParameter(PBNode):
    """System event parameter."""
    
    name: str
    param_type: str
    is_reference: bool = False
    is_readonly: bool = False
    default_value: Any | None = None


@dataclass
class PBSystemEvent(PBNode):
    """Represents a PowerBuilder system event."""
    
    name: str
    event_type: PBSystemEventType
    object_type: str  # window, control, datawindow, etc.
    parameters: list[PBSystemEventParameter] = field(default_factory=list)
    return_type: str | None = None
    description: str | None = None
    properties: dict[str, Any] = field(default_factory=dict)
    
    def add_parameter(self, param: PBSystemEventParameter) -> None:

    
        
    
        """Add a parameter to this event."""
        self.parameters.append(param)
    
    def get_parameter(self, name: str) -> PBSystemEventParameter | None:

    
        
    
        """Get a parameter by name."""
        for param in self.parameters:
            if param.name == name:
                return param
        return None
    
    def __str__(self) -> str:
        
    
        params = ", ".join(p.name for p in self.parameters)
        return f"{self.name}({params})"


# Common system events
CLICKED_EVENT = PBSystemEvent(
    name="clicked", event_type=PBSystemEventType.CLICKED, object_type="control", description="Occurs when the user clicks the control"
)

CONSTRUCTOR_EVENT = PBSystemEvent(
    name="constructor", event_type=PBSystemEventType.CONSTRUCTOR, object_type="any", description="Occurs when an object is created"
)

DESTRUCTOR_EVENT = PBSystemEvent(
    name="destructor", event_type=PBSystemEventType.DESTRUCTOR, object_type="any", description="Occurs when an object is destroyed"
)


# Global registry of system events
_system_events: dict[str, PBSystemEvent] = {
    "clicked": CLICKED_EVENT, "constructor": CONSTRUCTOR_EVENT, "destructor": DESTRUCTOR_EVENT, }


def register_system_event(event: PBSystemEvent) -> None:



    
    


    """Register a system event.
    
    Args:
        event: The system event to register
    """
    _system_events[event.name.lower()] = event


def get_system_event(name: str) -> PBSystemEvent | None:



    
    


    """Get a system event by name.
    
    Args:
        name: The name of the system event
        
    Returns:
        The system event or None if not found
    """
    return _system_events.get(name.lower())