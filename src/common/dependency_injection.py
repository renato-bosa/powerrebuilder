"""
Dependency injection container for clean architecture.

This module provides a simple but powerful dependency injection container
that supports:
- Service registration and resolution
- Singleton and transient lifetimes
- Constructor injection
- Factory functions
- Service overrides for testing
"""

from typing import Any, Callable, Dict, Optional, Type, TypeVar, Union
from enum import Enum
import inspect
from functools import wraps
import threading


T = TypeVar('T')


class ServiceLifetime(Enum):
    """Service lifetime options."""
    SINGLETON = "singleton"
    TRANSIENT = "transient"


class ServiceDescriptor:
    """Describes a registered service."""

    def __init__(
        self,
        service_type: Type,
        implementation: Union[Type, Callable[..., Any]],
        lifetime: ServiceLifetime = ServiceLifetime.SINGLETON,
        factory: Optional[Callable[..., Any]] = None
    ):
        self.service_type = service_type
        self.implementation = implementation
        self.lifetime = lifetime
        self.factory = factory
        self.instance = None


class DIContainer:
    """Dependency injection container."""

    def __init__(self):
        self._services: Dict[Type, ServiceDescriptor] = {}
        self._lock = threading.Lock()

    def register(
        self,
        service_type: Type[T],
        implementation: Optional[Union[Type[T], Callable[..., T]]] = None,
        lifetime: ServiceLifetime = ServiceLifetime.SINGLETON,
        factory: Optional[Callable[..., T]] = None
    ) -> None:
        """
        Register a service in the container.

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
                factory=factory
            )

    def register_singleton(self, service_type: Type[T], implementation: Optional[Type[T]] = None) -> None:
        """Register a singleton service."""
        self.register(service_type, implementation, ServiceLifetime.SINGLETON)

    def register_transient(self, service_type: Type[T], implementation: Optional[Type[T]] = None) -> None:
        """Register a transient service."""
        self.register(service_type, implementation, ServiceLifetime.TRANSIENT)

    def register_factory(
        self,
        service_type: Type[T],
        factory: Callable[['DIContainer'], T],
        lifetime: ServiceLifetime = ServiceLifetime.SINGLETON
    ) -> None:
        """Register a service with a factory function."""
        self.register(service_type, None, lifetime, factory)

    def resolve(self, service_type: Type[T]) -> T:
        """
        Resolve a service from the container.

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
            if descriptor.lifetime == ServiceLifetime.SINGLETON and descriptor.instance is not None:
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
            if name == 'self':
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

    def has(self, service_type: Type) -> bool:
        """Check if a service is registered."""
        return service_type in self._services

    def clear(self) -> None:
        """Clear all registered services."""
        with self._lock:
            self._services.clear()

    def override(self, service_type: Type[T], implementation: Union[Type[T], T]) -> None:
        """
        Override a registered service (useful for testing).

        Args:
            service_type: The service to override
            implementation: The new implementation or instance
        """
        with self._lock:
            if inspect.isclass(implementation):
                self._services[service_type] = ServiceDescriptor(
                    service_type=service_type,
                    implementation=implementation,
                    lifetime=ServiceLifetime.SINGLETON
                )
            else:
                # It's an instance
                descriptor = ServiceDescriptor(
                    service_type=service_type,
                    implementation=type(implementation),
                    lifetime=ServiceLifetime.SINGLETON
                )
                descriptor.instance = implementation
                self._services[service_type] = descriptor

    def create_scope(self) -> 'DIContainer':
        """Create a scoped container (for request-scoped services)."""
        scoped = DIContainer()
        # Copy service descriptors but not instances
        with self._lock:
            for service_type, descriptor in self._services.items():
                scoped._services[service_type] = ServiceDescriptor(
                    service_type=descriptor.service_type,
                    implementation=descriptor.implementation,
                    lifetime=descriptor.lifetime,
                    factory=descriptor.factory
                )
        return scoped


# Global container instance
_container = DIContainer()


def get_container() -> DIContainer:
    """Get the global container instance."""
    return _container


def inject(func: Callable) -> Callable:
    """
    Decorator for automatic dependency injection.

    Usage:
        @inject
        def my_function(service: IMyService):
            service.do_something()
    """
    @wraps(func)
    def wrapper(*args, **kwargs):
        sig = inspect.signature(func)
        container = get_container()

        # Resolve dependencies
        for name, param in sig.parameters.items():
            if name not in kwargs and param.annotation != param.empty:
                try:
                    kwargs[name] = container.resolve(param.annotation)
                except ValueError:
                    # Skip if can't resolve
                    pass

        return func(*args, **kwargs)

    return wrapper


def configure_services(container: Optional[DIContainer] = None) -> DIContainer:
    """
    Configure default services for the application.

    This is the main configuration point for the DI container.
    """
    if container is None:
        container = get_container()

    # Import here to avoid circular imports
    from ..extract.coordinator import ExtractCoordinator
    from ..parse.coordinator import ParseCoordinator
    from ..decompile.coordinator import DecompileCoordinator
    from ..model.coordinator import ModelCoordinator
    from ..generate.coordinator import GenerateCoordinator
    from ..common.pipeline.pipeline_coordinator import PipelineCoordinator
    
    # Import implementations
    from ..common.security import PathValidator
    from ..common.limits import ResourceMonitor
    from ..extract.pbd.io.progress import TqdmProgressTracker
    from ..decompile.pcode.decoder import PCodeDecoderV2
    from ..decompile.analysis.control_flow import ControlFlowAnalyzer
    from ..decompile.reconstruction.expression import ExpressionReconstructor
    from ..decompile.core.output_formatter import OutputFormatter
    from ..decompile.core.output_validator import OutputValidator
    from ..parse.grammar.loader import GrammarManager
    from ..parse.library import LibraryManager
    from ..parse.type_resolution import TypeResolver
    from ..parse.preprocessor.import_resolver import ImplicitImportResolver
    from ..parse.parser.powerbuilder import PowerBuilderParser
    from ..parse.transformer.ast_builder import PowerBuilderTransformer
    from ..generate.templates.engine import TemplateEngine
    from ..generate.converters.utils.type_converter import TypeConverter
    
    # Import interfaces
    from ..contracts.extractors import (
        IPathValidator, IResourceMonitor, IProgressTracker,
        IPBDReader, IRecoveryEngine, IBinaryExtractor, IResourceExtractor,
        IExtractorCoordinator
    )
    from ..contracts.decompilers import (
        IObjectTypeDetector, IPCodeDecoder, IControlFlowAnalyzer,
        IExpressionReconstructor, IOutputFormatter, IOutputValidator,
        IVersionDetector, IDecompilerCoordinator
    )
    from ..contracts.parsers import (
        IGrammarManager, ILibraryManager, ITypeResolver, IImportResolver,
        IParser, ITransformer, IPreprocessor, IParserCoordinator
    )
    from ..contracts.models import (
        IEntityFactory, IEntityValidator, IRelationshipManager,
        IASTProcessor, IModelExtractor, IModelPersistence, IModelCoordinator
    )
    from ..contracts.generators import (
        IASTExtractor, IGeneratorFactory, ITypeConverter, IUIProcessor,
        IEventProcessor, IProjectScaffolder, ITemplateEngine, IGeneratorCoordinator
    )
    
    # Register extraction services
    container.register_singleton(IPathValidator, PathValidator)
    container.register_singleton(IResourceMonitor, ResourceMonitor)
    container.register_transient(IProgressTracker, TqdmProgressTracker)
    
    # Register factories for readers and extractors
    container.register_factory(
        IPBDReader,
        lambda c: create_pbd_reader
    )
    container.register_factory(
        IRecoveryEngine,
        lambda c: create_recovery_engine
    )
    container.register_factory(
        IBinaryExtractor,
        lambda c: create_binary_extractor()
    )
    container.register_factory(
        IResourceExtractor,
        lambda c: create_resource_extractor()
    )
    
    # Register decompilation services
    container.register_singleton(IPCodeDecoder, PCodeDecoderV2)
    container.register_singleton(IControlFlowAnalyzer, ControlFlowAnalyzer)
    container.register_singleton(IExpressionReconstructor, ExpressionReconstructor)
    container.register_singleton(IOutputFormatter, OutputFormatter)
    container.register_singleton(IOutputValidator, OutputValidator)
    
    # Register parsing services
    container.register_singleton(IGrammarManager, GrammarManager)
    container.register_singleton(ILibraryManager, LibraryManager)
    container.register_singleton(ITypeResolver, TypeResolver)
    container.register_singleton(IImportResolver, ImplicitImportResolver)
    container.register_singleton(IParser, PowerBuilderParser)
    container.register_singleton(ITransformer, PowerBuilderTransformer)
    
    # Register model services (these will be extracted from ModelCoordinator)
    container.register_factory(
        IEntityFactory,
        lambda c: create_entity_factory()
    )
    container.register_factory(
        IEntityValidator,
        lambda c: create_entity_validator()
    )
    container.register_factory(
        IRelationshipManager,
        lambda c: create_relationship_manager()
    )
    container.register_factory(
        IASTProcessor,
        lambda c: create_ast_processor()
    )
    container.register_factory(
        IModelExtractor,
        lambda c: create_model_extractor()
    )
    container.register_factory(
        IModelPersistence,
        lambda c: create_model_persistence()
    )
    
    # Register generation services
    container.register_singleton(ITemplateEngine, TemplateEngine)
    container.register_singleton(ITypeConverter, TypeConverter)
    container.register_factory(
        IASTExtractor,
        lambda c: create_ast_extractor()
    )
    container.register_factory(
        IGeneratorFactory,
        lambda c: create_generator_factory()
    )
    container.register_factory(
        IUIProcessor,
        lambda c: create_ui_processor()
    )
    container.register_factory(
        IEventProcessor,
        lambda c: create_event_processor()
    )
    container.register_factory(
        IProjectScaffolder,
        lambda c: create_project_scaffolder()
    )
    
    # Register coordinators with injected dependencies
    container.register_factory(
        IExtractorCoordinator,
        lambda c: ExtractCoordinator(
            path_validator=c.resolve(IPathValidator),
            resource_monitor=c.resolve(IResourceMonitor),
            pbd_reader_factory=c.resolve(IPBDReader),
            progress_tracker_factory=lambda: c.resolve(IProgressTracker),
            recovery_engine_factory=c.resolve(IRecoveryEngine)
        )
    )
    
    container.register_singleton(IParserCoordinator, ParseCoordinator)
    container.register_singleton(IDecompilerCoordinator, DecompileCoordinator)
    
    # Register refactored ModelCoordinator with injected services
    container.register_factory(
        IModelCoordinator,
        lambda c: create_model_coordinator(c)
    )
    
    # Register refactored GenerateCoordinator with injected services
    container.register_factory(
        IGeneratorCoordinator,
        lambda c: create_generate_coordinator(c)
    )

    return container


# Factory functions for services that need to be extracted from coordinators
def create_pbd_reader(file_path):
    """Factory for creating PBD reader."""
    from ..extract.pbd.reader import StreamingPBDReader
    return StreamingPBDReader(file_path)


def create_recovery_engine(data, file_path):
    """Factory for creating recovery engine."""
    from ..extract.pbd.recovery.corruption import EnhancedRecoveryEngine
    return EnhancedRecoveryEngine(data, file_path)


def create_binary_extractor():
    """Factory for creating binary extractor."""
    from ..extract.pbd.extractors.binary import BinaryExtractor
    return BinaryExtractor()


def create_resource_extractor():
    """Factory for creating resource extractor."""
    from ..extract.pbd.extractors.resource import ResourceExtractor
    return ResourceExtractor()


def create_entity_factory():
    """Factory for creating entity factory service."""
    # This will be extracted from ModelCoordinator
    from ..model.services.entity_factory import EntityFactory
    return EntityFactory()


def create_entity_validator():
    """Factory for creating entity validator service."""
    from ..model.services.entity_validator import EntityValidator
    return EntityValidator()


def create_relationship_manager():
    """Factory for creating relationship manager service."""
    from ..model.services.relationship_manager import RelationshipManager
    return RelationshipManager()


def create_ast_processor():
    """Factory for creating AST processor service."""
    from ..model.services.ast_processor import ASTProcessor
    return ASTProcessor()


def create_model_extractor():
    """Factory for creating model extractor service."""
    from ..model.services.model_extractor import ModelExtractor
    return ModelExtractor()


def create_model_persistence():
    """Factory for creating model persistence service."""
    from ..model.services.model_persistence import ModelPersistence
    return ModelPersistence()


def create_ast_extractor():
    """Factory for creating AST extractor service."""
    from ..generate.extractors.ast_extractor import ASTExtractor
    return ASTExtractor()


def create_generator_factory():
    """Factory for creating generator factory service."""
    from ..generate.factories.generator_factory import GeneratorFactory
    return GeneratorFactory()


def create_ui_processor():
    """Factory for creating UI processor service."""
    from ..generate.processors.ui_processor import UIProcessor
    return UIProcessor()


def create_event_processor():
    """Factory for creating event processor service."""
    from ..generate.processors.event_processor import EventProcessor
    return EventProcessor()


def create_project_scaffolder():
    """Factory for creating project scaffolder service."""
    from ..generate.scaffolders.project_scaffolder import ProjectScaffolder
    return ProjectScaffolder()


def create_model_coordinator(container: DIContainer):
    """Factory for creating refactored model coordinator with dependencies."""
    from ..model.coordinator_refactored import ModelCoordinator
    
    return ModelCoordinator(
        entity_factory=container.resolve(IEntityFactory),
        entity_validator=container.resolve(IEntityValidator),
        relationship_manager=container.resolve(IRelationshipManager),
        ast_processor=container.resolve(IASTProcessor),
        model_extractor=container.resolve(IModelExtractor),
        model_persistence=container.resolve(IModelPersistence)
    )


def create_generate_coordinator(container: DIContainer):
    """Factory for creating refactored generate coordinator with dependencies."""
    from ..generate.coordinator_refactored import GenerateCoordinator
    
    return GenerateCoordinator(
        ast_extractor=container.resolve(IASTExtractor),
        generator_factory=container.resolve(IGeneratorFactory),
        ui_processor=container.resolve(IUIProcessor),
        event_processor=container.resolve(IEventProcessor),
        project_scaffolder=container.resolve(IProjectScaffolder)
    )


# Convenience functions for testing
def reset_container():
    """Reset the global container (useful for testing)."""
    global _container
    _container = DIContainer()


def with_test_container(func: Callable) -> Callable:
    """Decorator to use a test container."""
    @wraps(func)
    def wrapper(*args, **kwargs):
        original = _container
        test_container = DIContainer()
        global _container
        _container = test_container
        try:
            return func(*args, **kwargs)
        finally:
            _container = original
    return wrapper