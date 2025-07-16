"""
Event bus implementation for decoupled communication.

This module provides an event-driven communication system that allows
different parts of the pipeline to communicate without direct dependencies.
"""

import logging
import threading
from collections import defaultdict
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Set
import weakref
from queue import Queue, Empty
import asyncio

from ..contracts.events import IEventBus, IEventHandler, Event, EventType

logger = logging.getLogger(__name__)


class EventHandler(IEventHandler):
    """Basic event handler implementation."""

    def __init__(self, handler_func: Callable[[Event], None], event_types: Optional[Set[EventType]] = None):
        """
        Initialize event handler.

        Args:
            handler_func: Function to handle events
            event_types: Set of event types this handler can handle
        """
        self.handler_func = handler_func
        self.event_types = event_types or set(EventType)

    def handle(self, event: Event) -> None:
        """Handle an event."""
        self.handler_func(event)

    def can_handle(self, event_type: EventType) -> bool:
        """Check if handler can handle event type."""
        return event_type in self.event_types


class AsyncEventHandler(IEventHandler):
    """Async event handler for non-blocking operations."""

    def __init__(self, handler_coro: Callable[[Event], Any], event_types: Optional[Set[EventType]] = None):
        """
        Initialize async event handler.

        Args:
            handler_coro: Async function to handle events
            event_types: Set of event types this handler can handle
        """
        self.handler_coro = handler_coro
        self.event_types = event_types or set(EventType)
        self._loop = None

    def handle(self, event: Event) -> None:
        """Handle an event asynchronously."""
        if self._loop is None:
            try:
                self._loop = asyncio.get_event_loop()
            except RuntimeError:
                self._loop = asyncio.new_event_loop()
                asyncio.set_event_loop(self._loop)

        # Schedule the coroutine
        asyncio.ensure_future(self.handler_coro(event), loop=self._loop)

    def can_handle(self, event_type: EventType) -> bool:
        """Check if handler can handle event type."""
        return event_type in self.event_types


class EventBus(IEventBus):
    """
    Event bus implementation with support for:
    - Synchronous and asynchronous handlers
    - Weak references to prevent memory leaks
    - Thread-safe operations
    - Event filtering and routing
    - Event history and replay
    """

    def __init__(self, history_size: int = 1000, enable_async: bool = True):
        """
        Initialize event bus.

        Args:
            history_size: Number of events to keep in history
            enable_async: Enable async event processing
        """
        self._handlers: Dict[EventType, List[weakref.ref]] = defaultdict(list)
        self._lock = threading.RLock()
        self._history: List[Event] = []
        self._history_size = history_size
        self._enable_async = enable_async

        # For async processing
        if enable_async:
            self._event_queue = Queue()
            self._processing_thread = threading.Thread(target=self._process_events, daemon=True)
            self._processing_thread.start()

        # Statistics
        self._stats = {
            'published': 0,
            'delivered': 0,
            'failed': 0
        }

    def publish(self, event: Event) -> None:
        """Publish an event to all subscribed handlers."""
        with self._lock:
            # Add to history
            self._history.append(event)
            if len(self._history) > self._history_size:
                self._history.pop(0)

            self._stats['published'] += 1

            # Get handlers for this event type
            handlers = self._get_active_handlers(event.type)

            logger.debug(f"Publishing event {event.type.value} to {len(handlers)} handlers")

            # Process event
            if self._enable_async:
                self._event_queue.put((event, handlers))
            else:
                self._deliver_event(event, handlers)

    def subscribe(self, event_type: EventType, handler: IEventHandler) -> None:
        """Subscribe to an event type."""
        with self._lock:
            # Create weak reference to handler
            handler_ref = weakref.ref(handler, self._create_cleanup_callback(event_type))

            # Add to handlers list
            if handler_ref not in self._handlers[event_type]:
                self._handlers[event_type].append(handler_ref)
                logger.debug(f"Subscribed handler to {event_type.value}")

    def unsubscribe(self, event_type: EventType, handler: IEventHandler) -> None:
        """Unsubscribe from an event type."""
        with self._lock:
            handlers = self._handlers[event_type]

            # Remove handler reference
            for i, handler_ref in enumerate(handlers):
                if handler_ref() is handler:
                    handlers.pop(i)
                    logger.debug(f"Unsubscribed handler from {event_type.value}")
                    break

    def get_handlers(self, event_type: EventType) -> List[IEventHandler]:
        """Get all handlers for an event type."""
        with self._lock:
            return self._get_active_handlers(event_type)

    def _get_active_handlers(self, event_type: EventType) -> List[IEventHandler]:
        """Get active (non-garbage collected) handlers."""
        active_handlers = []
        dead_refs = []

        for handler_ref in self._handlers[event_type]:
            handler = handler_ref()
            if handler is not None:
                active_handlers.append(handler)
            else:
                dead_refs.append(handler_ref)

        # Clean up dead references
        for dead_ref in dead_refs:
            self._handlers[event_type].remove(dead_ref)

        return active_handlers

    def _create_cleanup_callback(self, event_type: EventType) -> Callable:
        """Create cleanup callback for weak references."""
        def cleanup(ref):
            with self._lock:
                try:
                    self._handlers[event_type].remove(ref)
                    logger.debug(f"Cleaned up dead handler reference for {event_type.value}")
                except ValueError:
                    pass
        return cleanup

    def _deliver_event(self, event: Event, handlers: List[IEventHandler]) -> None:
        """Deliver event to handlers."""
        for handler in handlers:
            try:
                if handler.can_handle(event.type):
                    handler.handle(event)
                    self._stats['delivered'] += 1
            except Exception as e:
                self._stats['failed'] += 1
                logger.error(f"Handler failed to process event {event.type.value}: {e}")

    def _process_events(self) -> None:
        """Process events from queue (for async mode)."""
        while True:
            try:
                event, handlers = self._event_queue.get(timeout=1)
                self._deliver_event(event, handlers)
            except Empty:
                continue
            except Exception as e:
                logger.error(f"Error processing event: {e}")

    def get_history(self, event_type: Optional[EventType] = None, limit: Optional[int] = None) -> List[Event]:
        """Get event history."""
        with self._lock:
            history = self._history[:]

            # Filter by event type if specified
            if event_type:
                history = [e for e in history if e.type == event_type]

            # Limit results if specified
            if limit:
                history = history[-limit:]

            return history

    def replay_events(self, events: List[Event]) -> None:
        """Replay a list of events."""
        for event in events:
            self.publish(event)

    def get_statistics(self) -> Dict[str, int]:
        """Get event bus statistics."""
        with self._lock:
            return self._stats.copy()

    def clear_history(self) -> None:
        """Clear event history."""
        with self._lock:
            self._history.clear()

    def reset_statistics(self) -> None:
        """Reset statistics."""
        with self._lock:
            self._stats = {
                'published': 0,
                'delivered': 0,
                'failed': 0
            }


class LoggingEventHandler(EventHandler):
    """Event handler that logs events."""

    def __init__(self, log_level: int = logging.INFO):
        """Initialize logging handler."""
        super().__init__(self._log_event)
        self.log_level = log_level

    def _log_event(self, event: Event) -> None:
        """Log an event."""
        logger.log(
            self.log_level,
            f"Event: {event.type.value} from {event.source} - {event.data}"
        )


class FileEventHandler(EventHandler):
    """Event handler that writes events to a file."""

    def __init__(self, file_path: Path, event_types: Optional[Set[EventType]] = None):
        """Initialize file handler."""
        super().__init__(self._write_event, event_types)
        self.file_path = Path(file_path)
        self.file_path.parent.mkdir(parents=True, exist_ok=True)

    def _write_event(self, event: Event) -> None:
        """Write event to file."""
        import json

        event_data = {
            'type': event.type.value,
            'source': event.source,
            'timestamp': event.timestamp.isoformat(),
            'data': event.data
        }

        with open(self.file_path, 'a') as f:
            json.dump(event_data, f)
            f.write('\n')


class MetricsEventHandler(EventHandler):
    """Event handler that collects metrics."""

    def __init__(self):
        """Initialize metrics handler."""
        super().__init__(self._collect_metrics)
        self.metrics = defaultdict(lambda: {'count': 0, 'last_seen': None})

    def _collect_metrics(self, event: Event) -> None:
        """Collect metrics from event."""
        metric = self.metrics[event.type]
        metric['count'] += 1
        metric['last_seen'] = event.timestamp

        # Collect specific metrics based on event type
        if event.type == EventType.FILE_PROCESSED:
            self._update_file_metrics(event)
        elif event.type == EventType.PROGRESS_UPDATE:
            self._update_progress_metrics(event)

    def _update_file_metrics(self, event: Event) -> None:
        """Update file processing metrics."""
        if 'processing_times' not in self.metrics:
            self.metrics['processing_times'] = []

        if 'processing_time' in event.data:
            self.metrics['processing_times'].append(event.data['processing_time'])

    def _update_progress_metrics(self, event: Event) -> None:
        """Update progress metrics."""
        if 'current' in event.data and 'total' in event.data:
            self.metrics['progress'] = {
                'current': event.data['current'],
                'total': event.data['total'],
                'percentage': (event.data['current'] / event.data['total']) * 100
            }

    def get_metrics(self) -> Dict[str, Any]:
        """Get collected metrics."""
        return dict(self.metrics)


# Factory function for dependency injection
def create_event_bus() -> EventBus:
    """Factory function to create event bus."""
    return EventBus()


# Convenience decorator for event handlers
def event_handler(event_types: List[EventType]):
    """Decorator to create event handlers from functions."""
    def decorator(func):
        return EventHandler(func, set(event_types))
    return decorator


# Example usage:
@event_handler([EventType.FILE_PROCESSED, EventType.STAGE_COMPLETED])
def log_completion(event: Event):
    """Example event handler function."""
    logger.info(f"Completed: {event.data}")