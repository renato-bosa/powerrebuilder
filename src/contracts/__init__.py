"""Contracts and interfaces for PowerRebuilder components.

This module exports all interfaces and protocols from the consolidated
interfaces.py file that defines the contracts between different components
of the PowerRebuilder system.
"""

# Import all interfaces from the consolidated file
from .interfaces import (
    # Logger interfaces
    ILogger,
    # Event interfaces
    Event,
    EventType,
    IEventBus,
    IEventHandler,
    # Pipeline interfaces
    IPipelineCoordinator,
    IPipelineStage,
    IPipelineState,
    IStateManager,
    PipelineStage,
    ProgressCallback,
    StageStatus,
    # Decompiler interfaces
    IControlFlowAnalyzer,
    IDecompiler,
    IDecompilerCoordinator,
    IExpressionReconstructor,
    IObjectTypeDetector,
    IOutputFormatter,
    IOutputValidator,
    IPCodeDecoder,
    IVersionDetector,
    # Extractor interfaces
    IBinaryExtractor,
    IBinaryFileParser,
    IExtractionStatistics,
    IExtractionValidator,
    IExtractor,
    IExtractorCoordinator,
    IExtractOrchestrator,
    IPathValidator,
    IPBDReader,
    IProgressReporter,
    IProgressTracker,
    IRecoveryEngine,
    IResourceExtractor,
    IResourceMonitor,
    # Generator interfaces
    IASTExtractor,
    IEventProcessor,
    IGenerator,
    IGeneratorCoordinator,
    IGeneratorFactory,
    IProjectScaffolder,
    ITemplateEngine,
    ITypeConverter,
    IUIProcessor,
    # Parser interfaces
    IEnumeratedType,
    IGrammarManager,
    IImportResolver,
    ILibraryManager,
    IParser,
    IParserCoordinator,
    IPreprocessor,
    IStructureType,
    ITransformer,
    ITypeParser,
    ITypeResolver,
    # Model interfaces
    IASTProcessor,
    IEntityFactory,
    IEntityValidator,
    IExpressionEvaluator,
    IModelExtractor,
    IModelPersistence,
)

# Keep imports from logger.py for backward compatibility
from .logger import DetailedLoggerAdapter, StandardLogger

__all__ = [
    # Logger
    "ILogger",
    "StandardLogger",
    "DetailedLoggerAdapter",
    # Events
    "Event",
    "EventType",
    "IEventBus",
    "IEventHandler",
    # Pipeline
    "IPipelineCoordinator",
    "IPipelineStage",
    "IPipelineState",
    "IStateManager",
    "PipelineStage",
    "ProgressCallback",
    "StageStatus",
    # Decompilers
    "IControlFlowAnalyzer",
    "IDecompiler",
    "IDecompilerCoordinator",
    "IExpressionReconstructor",
    "IObjectTypeDetector",
    "IOutputFormatter",
    "IOutputValidator",
    "IPCodeDecoder",
    "IVersionDetector",
    # Extractors
    "IBinaryExtractor",
    "IBinaryFileParser",
    "IExtractionStatistics",
    "IExtractionValidator",
    "IExtractor",
    "IExtractorCoordinator",
    "IExtractOrchestrator",
    "IPathValidator",
    "IPBDReader",
    "IProgressReporter",
    "IProgressTracker",
    "IRecoveryEngine",
    "IResourceExtractor",
    "IResourceMonitor",
    # Generators
    "IASTExtractor",
    "IEventProcessor",
    "IGenerator",
    "IGeneratorCoordinator",
    "IGeneratorFactory",
    "IProjectScaffolder",
    "ITemplateEngine",
    "ITypeConverter",
    "IUIProcessor",
    # Parsers
    "IEnumeratedType",
    "IGrammarManager",
    "IImportResolver",
    "ILibraryManager",
    "IParser",
    "IParserCoordinator",
    "IPreprocessor",
    "IStructureType",
    "ITransformer",
    "ITypeParser",
    "ITypeResolver",
    # Models
    "IASTProcessor",
    "IEntityFactory",
    "IEntityValidator",
    "IExpressionEvaluator",
    "IModelExtractor",
    "IModelPersistence",
]