"""Dependency injection configuration for PowerRebuilder.

This module provides centralized configuration for all services and their
implementations, including:
- Service registration and lifetimes
- Factory configurations
- Environment-specific settings
- Service decorators
"""

import logging
import os
from collections.abc import Callable
from typing import Any

from src.core.dependency_injection import DIContainer, ServiceLifetime

logger = logging.getLogger(__name__)


class ServiceConfiguration:
    """Configuration for a single service registration."""

    def __init__(
        self,
        interface: type,
        implementation: type | None = None,
        factory: Callable | None = None,
        lifetime: ServiceLifetime = ServiceLifetime.TRANSIENT,
        config: dict[str, Any] | None = None,
    ) -> None:
        """Initialize service configuration."""
        self.interface = interface
        self.implementation = implementation
        self.factory = factory
        self.lifetime = lifetime
        self.config = config or {}


class DIConfiguration:
    """Main dependency injection configuration."""

    def __init__(self, environment: str = "production") -> None:
        """Initialize DI configuration.

        Args:
            environment: The environment name (production, development, testing)
        """
        self.environment = environment
        self._services: dict[type, ServiceConfiguration] = {}
        self._configured = False

    def configure(self, container: DIContainer) -> None:
        """Configure all services in the container.

        Args:
            container: The DI container to configure
        """
        if self._configured:
            logger.warning("Container already configured, skipping...")
            return

        # Configure based on environment
        if self.environment == "testing":
            self._configure_testing(container)
        elif self.environment == "development":
            self._configure_development(container)
        else:
            self._configure_production(container)

        self._configured = True
        logger.info("DI container configured for %s environment", self.environment)

    def _configure_production(self, container: DIContainer) -> None:
        """Configure services for production environment."""
        # Common services
        self._configure_common_services(container)

        # Extraction services
        self._configure_extraction_services(container)

        # Decompilation services
        self._configure_decompilation_services(container)

        # Parsing services
        self._configure_parsing_services(container)

        # Model services
        self._configure_model_services(container)

        # Generation services
        self._configure_generation_services(container)

        # Coordinator services
        self._configure_coordinators(container)

    def _configure_development(self, container: DIContainer) -> None:
        """Configure services for development environment."""
        # Start with production configuration
        self._configure_production(container)

        # Override with development-specific services
        from src.contracts.logger import DetailedLoggerAdapter
        from src.contracts.pipeline import ILogger
        from src.core.logging import get_logger

        # Use detailed logger for development
        container.override(
            ILogger,
            lambda: DetailedLoggerAdapter(get_logger(__name__)),
            ServiceLifetime.SINGLETON,
        )

    def _configure_testing(self, container: DIContainer) -> None:
        """Configure services for testing environment."""
        # Start with production configuration
        self._configure_production(container)

        # Override with test-specific services
        from src.contracts.logger import StandardLogger
        from src.contracts.pipeline import ILogger

        # Use simple logger for testing (no file output)
        container.override(
            ILogger, lambda: StandardLogger("test"), ServiceLifetime.SINGLETON
        )

    def _configure_common_services(self, container: DIContainer) -> None:
        """Configure common services used across the application."""
        from src.contracts.extractors import IPathValidator, IResourceMonitor
        from src.contracts.logger import StandardLogger
        from src.contracts.pipeline import ILogger
        from src.core.resource_limits import ResourceMonitor
        from src.core.security import PathValidator

        # Security and validation
        container.register_singleton(IPathValidator, PathValidator)

        # Resource monitoring
        container.register_singleton(IResourceMonitor, ResourceMonitor)

        # Logging
        container.register_factory(
            ILogger, lambda _: StandardLogger(__name__), ServiceLifetime.SINGLETON
        )

    def _configure_extraction_services(self, container: DIContainer) -> None:
        """Configure extraction-related services."""
        from src.contracts.extractors import (
            IPBDReader,
            IProgressTracker,
            IRecoveryEngine,
            IResourceExtractor,
        )
        from src.extract.pbd.checkpoint import EnhancedRecoveryEngine
        from src.extract.pbd.progress import TqdmProgressTracker
        from src.extract.pbd.reader import StreamingPBDReader
        from src.extract.pbd.resources import ResourceExtractor

        # Progress tracking
        container.register_transient(IProgressTracker, TqdmProgressTracker)

        # PBD reading with factory
        container.register_factory(
            IPBDReader,
            lambda _: lambda file_path: StreamingPBDReader(file_path),
            ServiceLifetime.TRANSIENT,
        )

        # Recovery engine with factory
        container.register_factory(
            IRecoveryEngine,
            lambda _: lambda data, file_path: EnhancedRecoveryEngine(data, file_path),
            ServiceLifetime.TRANSIENT,
        )

        # Extractors
        container.register_singleton(IResourceExtractor, ResourceExtractor)

    def _configure_decompilation_services(self, container: DIContainer) -> None:
        """Configure decompilation-related services."""
        from src.contracts.decompilers import (
            IControlFlowAnalyzer,
            IExpressionReconstructor,
            IObjectTypeDetector,
            IOutputFormatter,
            IOutputValidator,
            IPCodeDecoder,
            IVersionDetector,
        )
        from src.decompile.analysis.control import ControlFlowAnalyzer
        from src.decompile.core.output import OutputFormatter
        from src.decompile.core.validator import OutputValidator
        from src.decompile.pcode.decoder import PCodeDecoderV2
        from src.decompile.reconstruction.expression import ExpressionReconstructor
        from src.extract.pbd.type_detection import ObjectTypeDetector
        from src.extract.utils.version import PBVersionDetector as VersionDetector

        # Core decompilation services
        container.register_singleton(IPCodeDecoder, PCodeDecoderV2)
        container.register_singleton(IControlFlowAnalyzer, ControlFlowAnalyzer)
        container.register_singleton(IExpressionReconstructor, ExpressionReconstructor)
        container.register_singleton(IOutputFormatter, OutputFormatter)
        container.register_singleton(IOutputValidator, OutputValidator)
        container.register_singleton(IObjectTypeDetector, ObjectTypeDetector)
        container.register_singleton(IVersionDetector, VersionDetector)

    def _configure_parsing_services(self, container: DIContainer) -> None:
        """Configure parsing-related services."""
        from src.contracts.parsers import (
            IGrammarManager,
            IImportResolver,
            ILibraryManager,
            IParser,
            IPreprocessor,
            ITransformer,
            ITypeResolver,
        )
        from src.parse.grammar.loader import GrammarManager
        from src.parse.library import LibraryManager
        from src.parse.parser.powerbuilder import PowerBuilderParser
        from src.parse.preprocessor.imports import ImplicitImportResolver
        from src.parse.preprocessor.preprocessor import PowerBuilderPreprocessor
        from src.parse.transformer.ast_builder import PowerBuilderTransformer
        from src.parse.type_resolution import TypeResolver

        # Grammar and type management
        container.register_singleton(IGrammarManager, GrammarManager)
        container.register_singleton(ILibraryManager, LibraryManager)
        container.register_singleton(ITypeResolver, TypeResolver)

        # Import resolution
        container.register_singleton(IImportResolver, ImplicitImportResolver)

        # Parser and transformer
        container.register_singleton(IParser, PowerBuilderParser)
        container.register_singleton(ITransformer, PowerBuilderTransformer)
        container.register_singleton(IPreprocessor, PowerBuilderPreprocessor)

    def _configure_model_services(self, container: DIContainer) -> None:
        """Configure model-related services."""
        from src.contracts.models import (
            IASTProcessor,
            IEntityFactory,
            IEntityValidator,
            IModelExtractor,
            IModelPersistence,
            IRelationshipManager,
        )

        # Register factories for model services
        # These will be implemented when we extract services from
        # ModelCoordinator
        container.register_factory(
            IEntityFactory,
            lambda _: self._create_entity_factory(),
            ServiceLifetime.SINGLETON,
        )

        container.register_factory(
            IEntityValidator,
            lambda _: self._create_entity_validator(),
            ServiceLifetime.SINGLETON,
        )

        container.register_factory(
            IRelationshipManager,
            lambda _: self._create_relationship_manager(),
            ServiceLifetime.SINGLETON,
        )

        container.register_factory(
            IASTProcessor,
            lambda _: self._create_ast_processor(),
            ServiceLifetime.SINGLETON,
        )

        container.register_factory(
            IModelExtractor,
            lambda _: self._create_model_extractor(),
            ServiceLifetime.SINGLETON,
        )

        container.register_factory(
            IModelPersistence,
            lambda _: self._create_model_persistence(),
            ServiceLifetime.SINGLETON,
        )

    def _configure_generation_services(self, container: DIContainer) -> None:
        """Configure generation-related services."""
        from src.contracts.generators import (
            IASTExtractor,
            IEventProcessor,
            IGeneratorFactory,
            IProjectScaffolder,
            ITemplateEngine,
            ITypeConverter,
            IUIProcessor,
        )
        from src.generate.converters.utils.types import TypeConverter
        from src.generate.templates.engine import TemplateEngine

        # Template engine and utilities
        container.register_singleton(ITemplateEngine, TemplateEngine)
        container.register_singleton(ITypeConverter, TypeConverter)

        # Register factories for generation services
        container.register_factory(
            IASTExtractor,
            lambda _: self._create_ast_extractor(),
            ServiceLifetime.SINGLETON,
        )

        container.register_factory(
            IGeneratorFactory,
            lambda _: self._create_generator_factory(),
            ServiceLifetime.SINGLETON,
        )

        container.register_factory(
            IUIProcessor,
            lambda _: self._create_ui_processor(),
            ServiceLifetime.SINGLETON,
        )

        container.register_factory(
            IEventProcessor,
            lambda _: self._create_event_processor(),
            ServiceLifetime.SINGLETON,
        )

        container.register_factory(
            IProjectScaffolder,
            lambda _: self._create_project_scaffolder(),
            ServiceLifetime.SINGLETON,
        )

    def _configure_coordinators(self, container: DIContainer) -> None:
        """Configure coordinator services."""
        from src.contracts.decompilers import IDecompilerCoordinator
        from src.contracts.extractors import IExtractorCoordinator
        from src.contracts.generators import IGeneratorCoordinator
        from src.contracts.models import IModelCoordinator
        from src.contracts.parsers import IParserCoordinator

        # Extract coordinator with full DI
        container.register_factory(
            IExtractorCoordinator,
            lambda c: self._create_extract_coordinator(c),
            ServiceLifetime.TRANSIENT,
        )

        # Decompile coordinator
        container.register_factory(
            IDecompilerCoordinator,
            lambda c: self._create_decompile_coordinator(c),
            ServiceLifetime.TRANSIENT,
        )

        # Parse coordinator
        container.register_factory(
            IParserCoordinator,
            lambda c: self._create_parse_coordinator(c),
            ServiceLifetime.TRANSIENT,
        )

        # Model coordinator
        container.register_factory(
            IModelCoordinator,
            lambda c: self._create_model_coordinator(c),
            ServiceLifetime.TRANSIENT,
        )

        # Generate coordinator
        container.register_factory(
            IGeneratorCoordinator,
            lambda c: self._create_generate_coordinator(c),
            ServiceLifetime.TRANSIENT,
        )

    # Factory methods for complex services
    def _create_entity_factory(self) -> Any:
        """Create entity factory service."""
        # Placeholder - will be implemented when extracting from
        # ModelCoordinator
        from src.model.services.entity_factory import EntityFactory

        return EntityFactory()

    def _create_entity_validator(self) -> Any:
        """Create entity validator service."""
        from src.model.services.entity_validator import EntityValidator

        return EntityValidator()

    def _create_relationship_manager(self) -> Any:
        """Create relationship manager service."""
        from src.model.services.relationship_manager import RelationshipManager

        return RelationshipManager()

    def _create_ast_processor(self) -> Any:
        """Create AST processor service."""
        from src.model.services.ast_processor import ASTProcessor

        return ASTProcessor()

    def _create_model_extractor(self) -> Any:
        """Create model extractor service."""
        from src.model.services.model_extractor import ModelExtractor

        return ModelExtractor()

    def _create_model_persistence(self) -> Any:
        """Create model persistence service."""
        from src.model.services.model_persistence import ModelPersistence

        return ModelPersistence()

    def _create_ast_extractor(self) -> Any:
        """Create AST extractor service."""
        from src.generate.extractors.ast import ASTExtractor

        return ASTExtractor()

    def _create_generator_factory(self) -> Any:
        """Create generator factory service."""
        from src.generate.factories.factory import GeneratorFactory

        return GeneratorFactory()

    def _create_ui_processor(self) -> Any:
        """Create UI processor service."""
        from src.generate.processors.ui import UIProcessor

        return UIProcessor()

    def _create_event_processor(self) -> Any:
        """Create event processor service."""
        from src.generate.processors.events import EventProcessor

        return EventProcessor()

    def _create_project_scaffolder(self) -> Any:
        """Create project scaffolder service."""
        from src.generate.scaffolders.scaffolder import ProjectScaffolder

        return ProjectScaffolder()

    def _create_extract_coordinator(self, container: DIContainer) -> Any:
        """Create extract coordinator with dependencies."""
        from src.contracts.extractors import IProgressTracker
        from src.extract.components.orchestrator import ExtractOrchestrator
        from src.extract.components.parser import BinaryFileParser
        from src.extract.components.recovery import RecoveryEngine
        from src.extract.components.resources import ComponentResourceExtractor
        from src.extract.components.statistics import ExtractionStatistics
        from src.extract.components.validator import ExtractionValidator
        from src.extract.coordinator import ExtractCoordinator

        # Create components
        binary_parser = BinaryFileParser()
        resource_extractor = ComponentResourceExtractor()
        recovery_engine = RecoveryEngine()
        validator = ExtractionValidator()
        statistics = ExtractionStatistics()
        progress_reporter = container.resolve(IProgressTracker)

        # Create orchestrator
        orchestrator = ExtractOrchestrator(
            binary_parser=binary_parser,
            resource_extractor=resource_extractor,
            recovery_engine=recovery_engine,
            validator=validator,
            statistics=statistics,
            progress_reporter=progress_reporter,
        )

        # Create coordinator
        return ExtractCoordinator(
            orchestrator=orchestrator, validator=validator, statistics=statistics
        )

    def _create_decompile_coordinator(self, container: DIContainer) -> Any:
        """Create decompile coordinator with dependencies."""
        from src.contracts.decompilers import (
            IControlFlowAnalyzer,
            IExpressionReconstructor,
            IObjectTypeDetector,
            IOutputFormatter,
            IOutputValidator,
            IPCodeDecoder,
            IVersionDetector,
        )
        from src.decompile.coordinator import DecompileCoordinator

        return DecompileCoordinator(
            decoder=container.resolve(IPCodeDecoder),
            analyzer=container.resolve(IControlFlowAnalyzer),
            reconstructor=container.resolve(IExpressionReconstructor),
            formatter=container.resolve(IOutputFormatter),
            validator=container.resolve(IOutputValidator),
            type_detector=container.resolve(IObjectTypeDetector),
            version_detector=container.resolve(IVersionDetector),
        )

    def _create_parse_coordinator(self, container: DIContainer) -> Any:
        """Create parse coordinator with dependencies."""
        from src.contracts.parsers import (
            IGrammarManager,
            IImportResolver,
            ILibraryManager,
            IParser,
            IPreprocessor,
            ITransformer,
            ITypeResolver,
        )
        from src.parse.coordinator import ParseCoordinator

        return ParseCoordinator(
            grammar_manager=container.resolve(IGrammarManager),
            library_manager=container.resolve(ILibraryManager),
            type_resolver=container.resolve(ITypeResolver),
            import_resolver=container.resolve(IImportResolver),
            parser=container.resolve(IParser),
            transformer=container.resolve(ITransformer),
            preprocessor=container.resolve(IPreprocessor),
        )

    def _create_model_coordinator(self, container: DIContainer) -> Any:
        """Create model coordinator with dependencies."""
        from src.contracts.models import (
            IASTProcessor,
            IEntityFactory,
            IEntityValidator,
            IModelExtractor,
            IModelPersistence,
            IRelationshipManager,
        )
        from src.model.coordinator import ModelCoordinator

        # Create ModelCoordinator with all dependencies
        return ModelCoordinator(
            entity_factory=container.resolve(IEntityFactory),
            entity_validator=container.resolve(IEntityValidator),
            relationship_manager=container.resolve(IRelationshipManager),
            ast_processor=container.resolve(IASTProcessor),
            model_extractor=container.resolve(IModelExtractor),
            model_persistence=container.resolve(IModelPersistence),
            input_dir=None,  # Will be set by caller
            output_dir=None,  # Will be set by caller
        )

    def _create_generate_coordinator(self, _container: Any) -> Any:
        """Create generate coordinator with dependencies."""
        from src.generate.coordinator import GenerateCoordinator

        # Note: Current GenerateCoordinator doesn't support DI yet
        # Return a factory function that creates it with paths
        def factory(input_dir: str, output_dir: str, framework: str = "flutter"):
            return GenerateCoordinator(
                input_dir=input_dir, output_dir=output_dir, framework=framework
            )

        return factory


# Configuration presets
def create_production_config() -> DIConfiguration:
    """Create production configuration."""
    return DIConfiguration(environment="production")


def create_development_config() -> DIConfiguration:
    """Create development configuration."""
    return DIConfiguration(environment="development")


def create_testing_config() -> DIConfiguration:
    """Create testing configuration."""
    return DIConfiguration(environment="testing")


def create_config_from_env() -> DIConfiguration:
    """Create configuration based on environment variables."""
    env = os.getenv("POWERREBUILDER_ENV", "production").lower()

    if env == "testing":
        return create_testing_config()
    if env == "development":
        return create_development_config()
    return create_production_config()
