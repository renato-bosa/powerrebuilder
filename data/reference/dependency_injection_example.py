"""Example demonstrating how to use the dependency injection container.

This example shows various ways to configure and use the DI container
in the PowerRebuilder project.
"""

import contextlib
import logging

from src.common.di_configuration import (
    create_development_config,
    create_production_config,
    create_testing_config,
)
from src.common.injection import get_container, inject, singleton, transient
from src.contracts.extractors import IExtractorCoordinator
from src.contracts.parsers import IParserCoordinator


# Example 1: Using decorators to mark services as injectable
@singleton
class MyCustomLogger:
    """Example singleton service."""

    def __init__(self) -> None:
        self.logger = logging.getLogger(__name__)
        self.logger.info("MyCustomLogger created (singleton)")

    def log(self, message: str) -> None:
        self.logger.info(f"Custom: {message}")


@transient
class RequestHandler:
    """Example transient service - new instance per resolution."""

    def __init__(self, logger: MyCustomLogger) -> None:
        self.logger = logger
        self.request_id = id(self)
        logger.log(f"RequestHandler {self.request_id} created")

    def handle(self, data: str) -> None:
        self.logger.log(f"Request {self.request_id}: {data}")


# Example 2: Using @inject decorator for function injection
@inject
def process_files(extractor: IExtractorCoordinator, parser: IParserCoordinator) -> None:
    """Function that gets dependencies injected automatically."""
    # The extractor and parser are automatically resolved from the container


# Example 3: Manual container usage
def example_manual_container() -> None:
    """Example of manually using the container."""
    # Get the container
    container = get_container()

    # Configure for production
    config = create_production_config()
    config.configure(container)

    # Resolve services manually
    container.resolve(IExtractorCoordinator)

    # Resolve multiple times - singleton returns same instance
    container.resolve(MyCustomLogger)
    container.resolve(MyCustomLogger)

    # Transient returns new instances
    container.resolve(RequestHandler)
    container.resolve(RequestHandler)


# Example 4: Environment-specific configuration
def example_environment_config() -> None:
    """Example of environment-specific configuration."""
    container = get_container()

    # Production configuration
    prod_config = create_production_config()
    prod_config.configure(container)

    # Development configuration (includes extra logging)
    dev_config = create_development_config()
    dev_config.configure(container)

    # Testing configuration (uses mocks)
    test_config = create_testing_config()
    test_config.configure(container)


# Example 5: Using factories from DI
def example_using_factories() -> None:
    """Example of using factory-created coordinators."""
    container = get_container()
    config = create_production_config()
    config.configure(container)

    # Use factories to create coordinators
    from src.decompile.factory import DecompileCoordinatorFactory
    from src.extract.extract_factory import ExtractCoordinatorFactory
    from src.parse.factory import ParseCoordinatorFactory

    # Create with simple configuration
    ExtractCoordinatorFactory.create_simple(
        input_path="input", output_path="output/extracted"
    )

    # Create with DI
    ParseCoordinatorFactory.create_with_di(container)

    # Create with custom components
    custom_components = {
        # Add custom component implementations
    }
    DecompileCoordinatorFactory.create_advanced(
        components=custom_components,
        input_dir="output/extracted",
        output_dir="output/decompiled",
    )



# Example 6: Scoped containers for request handling
def example_scoped_containers() -> None:
    """Example of using scoped containers."""
    # Get main container
    main_container = get_container()
    config = create_production_config()
    config.configure(main_container)

    # Create scoped container for a request
    request_scope = main_container.create_scope()

    # Services resolved in scope are independent
    main_container.resolve(RequestHandler)
    request_scope.resolve(RequestHandler)



# Example 7: Override services for testing
def example_override_for_testing() -> None:
    """Example of overriding services for testing."""
    container = get_container()
    config = create_production_config()
    config.configure(container)

    # Create a mock implementation
    class MockExtractor:
        def extract(self):
            return {"mocked": True}

    # Override the real service with mock
    container.override(IExtractorCoordinator, MockExtractor())

    # Now resolution returns the mock
    container.resolve(IExtractorCoordinator)


# Example 8: Complete pipeline with DI
def example_complete_pipeline() -> None:
    """Example of running complete pipeline with DI."""
    container = get_container()
    config = create_production_config()
    config.configure(container)

    # Resolve pipeline coordinator
    from src.pipeline_coordinator import PipelineCoordinator

    # Create pipeline with injected dependencies
    pipeline_config = {
        "extract": {"preserve_structure": True},
        "decompile": {"debug_mode": False},
        "parse": {"strict_mode": False},
        "model": {},
        "generate": {"target_framework": "flutter"},
    }

    PipelineCoordinator(
        input_dir="input", output_dir="output", config=pipeline_config
    )

    # The pipeline coordinator can now use DI to get its dependencies


def main() -> None:
    """Run all examples."""
    examples = [
        example_manual_container,
        example_environment_config,
        example_using_factories,
        example_scoped_containers,
        example_override_for_testing,
        example_complete_pipeline,
    ]

    for example in examples:
        with contextlib.suppress(Exception):
            example()

    # Also demonstrate the injected function
    try:
        # This will fail if container not configured
        container = get_container()
        if not container.has(IExtractorCoordinator):
            config = create_production_config()
            config.configure(container)

        # Now the function can be called without passing dependencies
        process_files()
    except Exception:
        pass


if __name__ == "__main__":
    # Configure logging
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    )

    main()
