#!/usr/bin/env python3
"""Demonstration of PowerRebuilder infrastructure components.

This example shows how to use the dependency injection, event bus,
caching, and progress tracking infrastructure.
"""

import asyncio
import time
from pathlib import Path

# Initialize the application infrastructure
from src.core.startup import initialize_application, get_infrastructure_component
from src.contracts.interfaces import Event, EventType
from src.common.pipeline.progress import PipelineProgress
from src.core.events import EventHandler


def demo_dependency_injection():
    """Demonstrate dependency injection usage."""
    print("\n=== Dependency Injection Demo ===")
    
    # Get the DI container
    container = get_infrastructure_component("container")
    
    # Resolve a service
    from src.core.security import PathValidator
    path_validator = container.resolve(PathValidator)
    
    # Use the service
    safe_path = path_validator.validate_output_path("/tmp/test")
    print(f"Validated path: {safe_path}")


def demo_event_bus():
    """Demonstrate event bus usage."""
    print("\n=== Event Bus Demo ===")
    
    # Get the event bus
    event_bus = get_infrastructure_component("event_bus")
    
    # Create a custom event handler
    def handle_file_event(event: Event):
        print(f"File processed: {event.data.get('file', 'unknown')}")
    
    # Create and subscribe the handler
    file_handler = EventHandler(
        handle_file_event, 
        event_types={EventType.FILE_PROCESSED}
    )
    event_bus.subscribe(EventType.FILE_PROCESSED, file_handler)
    
    # Publish an event
    event = Event(
        type=EventType.FILE_PROCESSED,
        source="demo",
        data={"file": "test.pbl", "size": 1024}
    )
    event_bus.publish(event)
    
    # Get statistics
    stats = event_bus.get_statistics()
    print(f"Event bus stats: {stats}")


async def demo_caching():
    """Demonstrate caching usage."""
    print("\n=== Caching Demo ===")
    
    # Get caches
    ast_cache = get_infrastructure_component("ast_cache")
    file_cache = get_infrastructure_component("file_cache")
    
    # Use in-memory cache
    await ast_cache.put("test_key", {"ast": "test_data"})
    cached_value = await ast_cache.get("test_key")
    print(f"Cached AST value: {cached_value}")
    
    # Use file cache for persistence
    await file_cache.put("persistent_key", {"data": "persistent_value"})
    persistent_value = await file_cache.get("persistent_key")
    print(f"Persistent cached value: {persistent_value}")
    
    # Show cache statistics
    stats = ast_cache.stats()
    print(f"AST cache stats: {stats}")


def demo_progress_tracking():
    """Demonstrate progress tracking."""
    print("\n=== Progress Tracking Demo ===")
    
    # Get progress tracker
    progress = get_infrastructure_component(PipelineProgress)
    
    # Note: Full progress UI requires terminal context
    # Here we just demonstrate the API
    print("Progress tracking API available:")
    print("- pipeline_context(): Full pipeline progress")
    print("- file_extraction_context(): File extraction progress")
    print("- operation_context(): Individual operation progress")
    
    # Simple progress simulation
    print("\nSimulating file extraction...")
    for i in range(5):
        print(f"  Processing file {i+1}/5")
        time.sleep(0.2)


def main():
    """Run all demonstrations."""
    print("PowerRebuilder Infrastructure Demonstration")
    print("=" * 50)
    
    # Initialize the application
    print("Initializing application infrastructure...")
    startup = initialize_application(verbose=False)
    print("✓ Infrastructure initialized")
    
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
        print("\nShutting down infrastructure...")
        startup.shutdown()
        print("✓ Infrastructure shutdown complete")


if __name__ == "__main__":
    main()