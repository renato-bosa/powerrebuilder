#!/usr/bin/env python3
"""Demonstration of PowerRebuilder infrastructure components.

This example shows how to use the dependency injection, event bus,
caching, and progress tracking infrastructure.
"""

import asyncio
import time

from src.common.pipeline.progress import PipelineProgress
from src.contracts.interfaces import Event, EventType
from src.core.events import EventHandler

# Initialize the application infrastructure
from src.core.startup import get_infrastructure_component, initialize_application


def demo_dependency_injection() -> None:
    """Demonstrate dependency injection usage."""
    # Get the DI container
    container = get_infrastructure_component("container")

    # Resolve a service
    from src.core.security import PathValidator

    path_validator = container.resolve(PathValidator)

    # Use the service
    path_validator.validate_output_path("/tmp/test")


def demo_event_bus() -> None:
    """Demonstrate event bus usage."""
    # Get the event bus
    event_bus = get_infrastructure_component("event_bus")

    # Create a custom event handler
    def handle_file_event(event: Event) -> None:
        pass

    # Create and subscribe the handler
    file_handler = EventHandler(
        handle_file_event, event_types={EventType.FILE_PROCESSED}
    )
    event_bus.subscribe(EventType.FILE_PROCESSED, file_handler)

    # Publish an event
    event = Event(
        type=EventType.FILE_PROCESSED,
        source="demo",
        data={"file": "test.pbl", "size": 1024},
    )
    event_bus.publish(event)

    # Get statistics
    event_bus.get_statistics()


async def demo_caching() -> None:
    """Demonstrate caching usage."""
    # Get caches
    ast_cache = get_infrastructure_component("ast_cache")
    file_cache = get_infrastructure_component("file_cache")

    # Use in-memory cache
    await ast_cache.put("test_key", {"ast": "test_data"})
    await ast_cache.get("test_key")

    # Use file cache for persistence
    await file_cache.put("persistent_key", {"data": "persistent_value"})
    await file_cache.get("persistent_key")

    # Show cache statistics
    ast_cache.stats()


def demo_progress_tracking() -> None:
    """Demonstrate progress tracking."""
    # Get progress tracker
    get_infrastructure_component(PipelineProgress)

    # Note: Full progress UI requires terminal context
    # Here we just demonstrate the API

    # Simple progress simulation
    for _i in range(5):
        time.sleep(0.2)


def main() -> None:
    """Run all demonstrations."""
    # Initialize the application
    startup = initialize_application(verbose=False)

    try:
        # Run demonstrations
        demo_dependency_injection()
        demo_event_bus()

        # Run async demonstrations
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            loop.run_until_complete(demo_caching())
        finally:
            loop.close()

        demo_progress_tracking()

    finally:
        # Cleanup
        startup.shutdown()


if __name__ == "__main__":
    main()
