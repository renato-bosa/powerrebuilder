"""Dependency injection container for clean architecture.

This module provides a simple but powerful dependency injection container
that supports:
- Service registration and resolution
- Singleton and transient lifetimes
- Constructor injection
- Property injection
- Factory functions
- Service overrides for testing
- Decorator support (@injectable, @singleton)
- Configuration injection
"""

import inspect
import logging
import threading
from collections.abc import Callable
from enum import Enum
from functools import wraps
from pathlib import Path
from typing import TYPE_CHECKING, Any, TypeVar

logger = logging.getLogger(__name__)

T = TypeVar("T")

if TYPE_CHECKING:
    from src.contracts.interfaces import (
        IASTExtractor,
        IASTProcessor,
        IBinaryExtractor,
        IEntityFactory,
        IEntityValidator,
        IEventProcessor,
        IGeneratorFactory,
        IModelExtractor,
        IModelPersistence,
        IPBDReader,
        IProjectScaffolder,
        IRecoveryEngine,
        IRelationshipManager,
        IResourceExtractor,
        IUIProcessor,
    )


class ServiceLifetime(Enum):
    """Service lifetime options."""

    SINGLETON = "singleton"
    TRANSIENT = "transient"


class ServiceDescriptor:
    """Describes a registered service."""

    def __init__(
        self,
        service_type: type,
        implementation: type | Callable[..., Any],
        lifetime: ServiceLifetime = ServiceLifetime.SINGLETON,
        factory: Callable[..., Any] | None = None,
    ) -> None:
        self.service_type = service_type
        self.implementation = implementation
        self.lifetime = lifetime
        self.factory = factory
        self.instance = None


class DIContainer:
    """Dependency injection container."""

    def __init__(self) -> None:
        self._services: dict[type, ServiceDescriptor] = {}
        self._lock = threading.Lock()

    def register(
        self,
        service_type: type[T],
        implementation: type[T] | Callable[..., T] | None = None,
        lifetime: ServiceLifetime = ServiceLifetime.SINGLETON,
        factory: Callable[..., T] | None = None,
    ) -> None:
        """Register a service in the container.

        Args:
            service_type: The interface or base type
            implementation: The concrete implementation (class or factory)
            lifetime: Service lifetime (singleton or transient)
            factory: Optional factory function
        """
        if implementation is None and factory is None:
            implementation = service_type

        with self._lock:
            self._services[service_type] = ServiceDescriptor(
                service_type=service_type,
                implementation=implementation or factory,
                lifetime=lifetime,
                factory=factory,
            )

    def register_singleton(
        self, service_type: type[T], implementation: type[T] | None = None
    ) -> None:
        """Register a singleton service."""
        self.register(service_type, implementation, ServiceLifetime.SINGLETON)

    def register_transient(
        self, service_type: type[T], implementation: type[T] | None = None
    ) -> None:
        """Register a transient service."""
        self.register(service_type, implementation, ServiceLifetime.TRANSIENT)

    def register_factory(
        self,
        service_type: type[T],
        factory: Callable[["DIContainer"], T],
        lifetime: ServiceLifetime = ServiceLifetime.SINGLETON,
    ) -> None:
        """Register a service with a factory function."""
        self.register(service_type, None, lifetime, factory)

    def resolve(self, service_type: type[T]) -> T:
        """Resolve a service from the container.

        Args:
            service_type: The type to resolve

        Returns:
            The resolved service instance

        Raises:
            ValueError: If service is not registered
        """
        with self._lock:
            if service_type not in self._services:
                raise ValueError(f"Service {service_type.__name__} is not registered")

            descriptor = self._services[service_type]

            # Return existing singleton instance if available
            if (
                descriptor.lifetime == ServiceLifetime.SINGLETON
                and descriptor.instance is not None
            ):
                return descriptor.instance

            # Create new instance
            instance = self._create_instance(descriptor)

            # Store singleton instance
            if descriptor.lifetime == ServiceLifetime.SINGLETON:
                descriptor.instance = instance

            return instance

    def _create_instance(self, descriptor: ServiceDescriptor) -> Any:
        """Create a service instance."""
        if descriptor.factory:
            # Use factory function
            return descriptor.factory(self)

        implementation = descriptor.implementation

        if not inspect.isclass(implementation):
            # It's already a callable/function
            return implementation(self)

        # Get constructor parameters
        sig = inspect.signature(implementation.__init__)
        params = {}

        for name, param in sig.parameters.items():
            if name == "self":
                continue

            # Try to resolve parameter type
            if param.annotation != param.empty:
                try:
                    params[name] = self.resolve(param.annotation)
                except ValueError:
                    # If can't resolve, skip (will use default if available)
                    if param.default == param.empty:
                        raise

        return implementation(**params)

    def has(self, service_type: type) -> bool:
        """Check if a service is registered."""
        return service_type in self._services

    def clear(self) -> None:
        """Clear all registered services."""
        with self._lock:
            self._services.clear()

    def override(self, service_type: type[T], implementation: type[T] | T) -> None:
        """Override a registered service (useful for testing).

        Args:
            service_type: The service to override
            implementation: The new implementation or instance
        """
        with self._lock:
            if inspect.isclass(implementation):
                self._services[service_type] = ServiceDescriptor(
                    service_type=service_type,
                    implementation=implementation,
                    lifetime=ServiceLifetime.SINGLETON,
                )
            else:
                # It's an instance
                descriptor = ServiceDescriptor(
                    service_type=service_type,
                    implementation=type(implementation),
                    lifetime=ServiceLifetime.SINGLETON,
                )
                descriptor.instance = implementation
                self._services[service_type] = descriptor

    def create_scope(self) -> "DIContainer":
        """Create a scoped container (for request-scoped services)."""
        scoped = DIContainer()
        # Copy service descriptors but not instances
        with self._lock:
            for service_type, descriptor in self._services.items():
                scoped._services[service_type] = ServiceDescriptor(
                    service_type=descriptor.service_type,
                    implementation=descriptor.implementation,
                    lifetime=descriptor.lifetime,
                    factory=descriptor.factory,
                )
        return scoped


# Global container instance
_container = DIContainer()


def get_container() -> DIContainer:
    """Get the global container instance."""
    return _container


def inject(func: Callable[..., T]) -> Callable[..., T]:
    """Decorator for automatic dependency injection.

    Usage:
        @inject
        def my_function(service: IMyService):
            service.do_something()
    """

    @wraps(func)
    def wrapper(*args: Any, **kwargs: Any) -> Any:
        sig = inspect.signature(func)
        container = get_container()

        # Resolve dependencies
        for name, param in sig.parameters.items():
            if name not in kwargs and param.annotation != param.empty:
                try:
                    kwargs[name] = container.resolve(param.annotation)
                except ValueError as e:
                    # Skip if can't resolve, unless it's required
                    if param.default == param.empty:
                        logger.warning(
                            "Failed to inject required parameter %s: %s", name, e
                        )

        return func(*args, **kwargs)

    return wrapper


def injectable(
    lifetime: ServiceLifetime = ServiceLifetime.SINGLETON,
) -> Callable[[type[T]], type[T]]:
    """Class decorator to mark a class as injectable.

    Usage:
        @injectable()
        class MyService(IMyService):
            pass

        @injectable(ServiceLifetime.TRANSIENT)
        class MyTransientService:
            pass
    """

    def decorator(cls: type[T]) -> type[T]:
        # Store metadata on the class
        cls._injectable_lifetime = lifetime
        cls._injectable = True

        # Auto-register if container exists
        container = get_container()
        if container:
            # Try to find interface from base classes
            interfaces = [base for base in cls.__bases__ if base != object]
            if interfaces:
                container.register(interfaces[0], cls, lifetime)
            else:
                container.register(cls, cls, lifetime)

        return cls

    return decorator


def singleton(cls: type[T]) -> type[T]:
    """Class decorator to mark a class as a singleton service.

    Usage:
        @singleton
        class MyService(IMyService):
            pass
    """
    return injectable(ServiceLifetime.SINGLETON)(cls)


def transient(cls: type[T]) -> type[T]:
    """Class decorator to mark a class as a transient service.

    Usage:
        @transient
        class MyService(IMyService):
            pass
    """
    return injectable(ServiceLifetime.TRANSIENT)(cls)


class ConfigValue:
    """Represents a configuration value to be injected."""

    def __init__(self, key: str, default: Any = None) -> None:
        self.key = key
        self.default = default


def configure_services(container: DIContainer | None = None) -> DIContainer:
    """Configure default services for the application.

    This is the main configuration point for the DI container.
    """
    if container is None:
        container = get_container()

    # Import here to avoid circular imports
    from src.core.resource_limits import ResourceMonitor

    # Import implementations
    from src.core.security import PathValidator

    # Import interfaces
    from src.decompile.analysis.control import ControlFlowAnalyzer
    from src.decompile.coordinator import DecompileCoordinator
    from src.decompile.core.output import OutputFormatter
    from src.decompile.core.validator import OutputValidator
    from src.decompile.pcode.decoder import PCodeDecoderV2
    from src.decompile.reconstruction.expression import ExpressionReconstructor
    from src.extract.coordinator import ExtractCoordinator
    from src.extract.pbd.io_operations import TqdmProgressTracker
    from src.extract.utils.version import PBVersionDetector as VersionDetector
    from src.generate.converters.utils.types import TypeConverter
    from src.generate.templates.engine import TemplateEngine
    from src.parse.coordinator import ParseCoordinator
    from src.parse.grammar.loader import GrammarManager
    from src.parse.library import LibraryManager
    from src.parse.parser.powerbuilder import PowerBuilderParser
    from src.parse.preprocessor.imports import ImplicitImportResolver
    from src.parse.resolution import TypeResolver
    from src.parse.transformer.builder import PowerBuilderTransformer

    # NOTE: The interfaces below need to be defined
    # For now, we use the concrete classes directly

    # Register extraction services
    container.register_singleton(PathValidator, PathValidator)
    container.register_singleton(ResourceMonitor, ResourceMonitor)
    container.register_transient(TqdmProgressTracker, TqdmProgressTracker)

    # Register factories for readers and extractors
    container.register_factory("IPBDReader", lambda c: create_pbd_reader)
    container.register_factory("IRecoveryEngine", lambda c: create_recovery_engine)
    container.register_factory("IBinaryExtractor", lambda c: create_binary_extractor())
    container.register_factory(
        "IResourceExtractor", lambda c: create_resource_extractor()
    )

    # Register decompilation services
    container.register_singleton(PCodeDecoderV2, PCodeDecoderV2)
    container.register_singleton(ControlFlowAnalyzer, ControlFlowAnalyzer)
    container.register_singleton(ExpressionReconstructor, ExpressionReconstructor)
    container.register_singleton(OutputFormatter, OutputFormatter)
    container.register_singleton(OutputValidator, OutputValidator)
    container.register_singleton(VersionDetector, VersionDetector)

    # Register parsing services
    container.register_singleton(GrammarManager, GrammarManager)
    container.register_singleton(LibraryManager, LibraryManager)
    container.register_singleton(TypeResolver, TypeResolver)
    container.register_singleton(ImplicitImportResolver, ImplicitImportResolver)
    container.register_singleton(PowerBuilderParser, PowerBuilderParser)
    container.register_singleton(PowerBuilderTransformer, PowerBuilderTransformer)

    # Register model services (these will be extracted from ModelCoordinator)
    container.register_factory("IEntityFactory", lambda c: create_entity_factory())
    container.register_factory("IEntityValidator", lambda c: create_entity_validator())
    container.register_factory(
        "IRelationshipManager", lambda c: create_relationship_manager()
    )
    container.register_factory("IASTProcessor", lambda c: create_ast_processor())
    container.register_factory("IModelExtractor", lambda c: create_model_extractor())
    container.register_factory(
        "IModelPersistence", lambda c: create_model_persistence()
    )

    # Register generation services
    container.register_singleton(TemplateEngine, TemplateEngine)
    container.register_singleton(TypeConverter, TypeConverter)
    container.register_factory("IASTExtractor", lambda c: create_ast_extractor())
    container.register_factory(
        "IGeneratorFactory", lambda c: create_generator_factory()
    )
    container.register_factory("IUIProcessor", lambda c: create_ui_processor())
    container.register_factory("IEventProcessor", lambda c: create_event_processor())
    container.register_factory(
        "IProjectScaffolder", lambda c: create_project_scaffolder()
    )

    # Register coordinators with injected dependencies
    container.register_factory(
        ExtractCoordinator,
        lambda c: ExtractCoordinator(
            path_validator=c.resolve(PathValidator),
            resource_monitor=c.resolve(ResourceMonitor),
            pbd_reader_factory=c.resolve("IPBDReader"),
            progress_tracker_factory=lambda: c.resolve(TqdmProgressTracker),
            recovery_engine_factory=c.resolve("IRecoveryEngine"),
        ),
    )

    container.register_singleton(ParseCoordinator, ParseCoordinator)
    container.register_singleton(DecompileCoordinator, DecompileCoordinator)

    # Register refactored ModelCoordinator with injected services
    container.register_factory(
        "IModelCoordinator", lambda c: create_model_coordinator(c)
    )

    # Register refactored GenerateCoordinator with injected services
    container.register_factory(
        "IGeneratorCoordinator", lambda c: create_generate_coordinator(c)
    )

    return container


# Factory functions for services that need to be extracted from coordinators
def create_pbd_reader(file_path: Path) -> "IPBDReader":
    """Factory for creating PBD reader."""
    from src.extract.pbd.reader import StreamingPBDReader

    return StreamingPBDReader(file_path)


def create_recovery_engine(data: bytes, file_path: Path) -> "IRecoveryEngine":
    """Factory for creating recovery engine."""
    from src.extract.pbd.recovery import EnhancedRecoveryEngine

    return EnhancedRecoveryEngine(data, file_path)


def create_binary_extractor() -> "IBinaryExtractor":
    """Factory for creating binary extractor."""
    from src.extract.pbd.extraction import StringResourceExtractor

    return StringResourceExtractor()


def create_resource_extractor() -> "IResourceExtractor":
    """Factory for creating resource extractor."""
    from src.extract.pbd.extraction import UnifiedResourceExtractor

    return UnifiedResourceExtractor()


def create_entity_factory() -> "IEntityFactory":
    """Factory for creating entity factory service."""
    # This will be extracted from ModelCoordinator
    from src.model.services.entity_factory import EntityFactory

    return EntityFactory()


def create_entity_validator() -> "IEntityValidator":
    """Factory for creating entity validator service."""
    from src.model.services.entity_validator import EntityValidator

    return EntityValidator()


def create_relationship_manager() -> "IRelationshipManager":
    """Factory for creating relationship manager service."""
    from src.model.services.relationship_manager import RelationshipManager

    return RelationshipManager()


def create_ast_processor() -> "IASTProcessor":
    """Factory for creating AST processor service."""
    from src.model.services.ast_processor import ASTProcessor

    return ASTProcessor()


def create_model_extractor() -> "IModelExtractor":
    """Factory for creating model extractor service."""
    from src.model.services.model_extractor import ModelExtractor

    return ModelExtractor()


def create_model_persistence() -> "IModelPersistence":
    """Factory for creating model persistence service."""
    from src.model.services.model_persistence import ModelPersistence

    return ModelPersistence()


def create_ast_extractor() -> "IASTExtractor":
    """Factory for creating AST extractor service."""
    from src.generate.extractors.ast import ASTExtractor

    return ASTExtractor()


def create_generator_factory() -> "IGeneratorFactory":
    """Factory for creating generator factory service."""
    from src.generate.factories.factory import GeneratorFactory

    return GeneratorFactory()


def create_ui_processor() -> "IUIProcessor":
    """Factory for creating UI processor service."""
    from src.generate.processors.ui import UIProcessor

    return UIProcessor()


def create_event_processor() -> "IEventProcessor":
    """Factory for creating event processor service."""
    from src.generate.processors.events import EventProcessor

    return EventProcessor()


def create_project_scaffolder() -> "IProjectScaffolder":
    """Factory for creating project scaffolder service."""
    from src.generate.scaffolders.scaffolder import ProjectScaffolder

    return ProjectScaffolder()


def create_model_coordinator(container: DIContainer) -> Any:
    """Factory for creating model coordinator with dependencies."""
    from src.model.coordinator import ModelCoordinator

    return ModelCoordinator(
        input_dir=container.resolve("IEntityFactory"),
        output_dir=container.resolve("IEntityValidator"),
        relationship_manager=container.resolve("IRelationshipManager"),
        ast_processor=container.resolve("IASTProcessor"),
        model_extractor=container.resolve("IModelExtractor"),
        model_persistence=container.resolve("IModelPersistence"),
    )


def create_generate_coordinator(_container: DIContainer) -> Any:
    """Factory for creating generate coordinator.

    Note: The current GenerateCoordinator doesn't use dependency injection,
    so we create it with default parameters. The refactored architecture
    with services is available in src/generate/coordinators/ for future migration.
    """
    from src.generate.coordinator import GenerateCoordinator

    # Return a factory function that creates the coordinator with provided paths
    def factory(input_dir: str, output_dir: str, framework: str = "flutter") -> Any:
        return GenerateCoordinator(
            input_dir=input_dir, output_dir=output_dir, framework=framework
        )

    return factory


# Convenience functions for testing
def reset_container() -> None:
    """Reset the global container (useful for testing)."""
    global _container
    _container = DIContainer()


def with_test_container(func: Callable[..., T]) -> Callable[..., T]:
    """Decorator to use a test container."""

    @wraps(func)
    def wrapper(*args: Any, **kwargs: Any) -> Any:
        global _container
        original = _container
        test_container = DIContainer()
        _container = test_container
        try:
            return func(*args, **kwargs)
        finally:
            _container = original

    return wrapper
