"""Event bus interfaces for clean architecture."""

from abc import abstractmethod
from datetime import datetime
from enum import Enum
from typing import Any, Protocol


class EventType(Enum):
    """Event types."""

    STAGE_STARTED = "stage_started"
    STAGE_COMPLETED = "stage_completed"
    STAGE_FAILED = "stage_failed"
    FILE_PROCESSED = "file_processed"
    ERROR_OCCURRED = "error_occurred"
    WARNING_RAISED = "warning_raised"
    PROGRESS_UPDATE = "progress_update"


class Event:
    """Base event class."""

    type: EventType
    source: str
    timestamp: datetime
    data: dict[str, Any]


class IEventHandler(Protocol):
    """Interface for event handlers."""

    @abstractmethod
    def handle(self, event: Event) -> None:
        """Handle an event."""
        ...

    @abstractmethod
    def can_handle(self, event_type: EventType) -> bool:
        """Check if handler can handle event type."""
        ...


class IEventBus(Protocol):
    """Interface for event bus."""

    @abstractmethod
    def publish(self, event: Event) -> None:
        """Publish an event."""
        ...

    @abstractmethod
    def subscribe(self, event_type: EventType, handler: IEventHandler) -> None:
        """Subscribe to an event type."""
        ...

    @abstractmethod
    def unsubscribe(self, event_type: EventType, handler: IEventHandler) -> None:
        """Unsubscribe from an event type."""
        ...

    @abstractmethod
    def get_handlers(self, event_type: EventType) -> list[IEventHandler]:
        """Get all handlers for an event type."""
        ...
