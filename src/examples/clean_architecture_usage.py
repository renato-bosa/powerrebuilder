"""
Example demonstrating the clean architecture implementation.

This example shows how to use:
- Dependency injection
- Event bus
- State management
- Decoupled coordinators
"""

import logging
from pathlib import Path

from ..common.dependency_injection import configure_services, inject
from ..common.event_bus import EventBus, event_handler
from ..contracts import (
    IGeneratorCoordinator,
    IEventBus,
    IStateManager
)
from ..contracts.events import EventType, Event

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def setup_event_handlers(event_bus: IEventBus):
    """Set up event handlers for monitoring pipeline execution."""

    # Create a logging handler for all events
    @event_handler([
        EventType.STAGE_STARTED,
        EventType.STAGE_COMPLETED,
        EventType.STAGE_FAILED,
        EventType.FILE_PROCESSED,
        EventType.PROGRESS_UPDATE
    ])
    def log_events(event: Event):
        logger.info(f"[{event.type.value}] {event.source}: {event.data}")

    # Create a metrics handler
    from ..common.event_bus import MetricsEventHandler
    metrics_handler = MetricsEventHandler()

    # Subscribe handlers
    for event_type in EventType:
        event_bus.subscribe(event_type, log_events)
        event_bus.subscribe(event_type, metrics_handler)

    return metrics_handler


@inject
def run_generation_example(
    generator: IGeneratorCoordinator,
    event_bus: IEventBus,
    state_manager: IStateManager
):
    """
    Example of running generation with clean architecture.

    This function is automatically injected with dependencies.
    """
    logger.info("Starting generation example...")

    # Set up event handlers
    metrics_handler = setup_event_handlers(event_bus)

    # Create pipeline state
    state = state_manager.create_state()
    logger.info(f"Created pipeline state: {state.id}")

    # Run generation
    input_dir = Path("data/output/current/parsed")
    output_dir = Path("data/output/generated")

    try:
        # Create checkpoint before generation
        checkpoint_id = state_manager.create_checkpoint(state, "pre-generation")
        logger.info(f"Created checkpoint: {checkpoint_id}")

        # Run generation
        results = generator.generate(input_dir, output_dir, target="flutter")

        # Save state
        state_manager.save_state(state)

        # Get metrics
        metrics = metrics_handler.get_metrics()
        logger.info(f"Generation metrics: {metrics}")

        # Get event history
        history = event_bus.get_history(EventType.FILE_PROCESSED, limit=10)
        logger.info(f"Processed {len(history)} files recently")

        return results

    except Exception as e:
        logger.error(f"Generation failed: {e}")

        # Rollback on failure
        logger.info(f"Rolling back to checkpoint {checkpoint_id}")
        state_manager.rollback(state, checkpoint_id)

        raise


def demonstrate_modular_generation():
    """Demonstrate using individual coordinators."""
    from ..generate.coordinators import (
        ModelGenerationCoordinator,
        FlutterGenerationCoordinator,
        ServiceGenerationCoordinator
    )

    input_dir = Path("data/output/current/parsed")
    output_dir = Path("data/output/generated")

    # Create event bus for coordination
    event_bus = EventBus()
    setup_event_handlers(event_bus)

    # Create specialized coordinators
    model_coord = ModelGenerationCoordinator(
        input_dir,
        output_dir / "models",
        event_bus=event_bus
    )

    service_coord = ServiceGenerationCoordinator(
        input_dir,
        output_dir / "services",
        event_bus=event_bus
    )

    flutter_coord = FlutterGenerationCoordinator(
        input_dir,
        output_dir / "flutter",
        event_bus=event_bus,
        design_theme="liquid_glass"
    )

    # Generate each component separately
    logger.info("Generating models...")
    model_results = model_coord.generate({})

    logger.info("Generating services...")
    service_results = service_coord.generate({})

    logger.info("Generating Flutter UI...")
    flutter_results = flutter_coord.generate({
        'app_info': {
            'name': 'my_app',
            'display_name': 'My PowerBuilder App'
        }
    })

    return {
        'models': model_results,
        'services': service_results,
        'flutter': flutter_results
    }


def main():
    """Main entry point for the example."""
    # Configure dependency injection
    container = configure_services()
    logger.info("Configured dependency injection container")

    # Example 1: Using dependency injection
    logger.info("\n=== Example 1: Dependency Injection ===")
    results = run_generation_example()
    logger.info(f"Generation completed: {results}")

    # Example 2: Using modular coordinators
    logger.info("\n=== Example 2: Modular Generation ===")
    modular_results = demonstrate_modular_generation()
    logger.info(f"Modular generation completed: {modular_results}")

    # Example 3: Testing with override
    logger.info("\n=== Example 3: Testing with Mocks ===")

    # Create mock implementations
    class MockGenerator:
        def generate(self, input_dir, output_dir, target):
            return {'mocked': True, 'target': target}

        def register_generator(self, generator):
            pass

        def get_generators(self):
            return []

        def get_generator(self, target):
            return None

    # Override service
    container.override(IGeneratorCoordinator, MockGenerator())

    # Run with mock
    mock_generator = container.resolve(IGeneratorCoordinator)
    mock_result = mock_generator.generate(Path("."), Path("."), "test")
    logger.info(f"Mock result: {mock_result}")


if __name__ == "__main__":
    main()