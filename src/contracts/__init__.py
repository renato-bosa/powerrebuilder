"""Contracts and interfaces for PowerRebuilder components.

This module exports all interfaces and protocols from the consolidated
interfaces.py file that defines the contracts between different components
of the PowerRebuilder system.
"""

# Import all interfaces from the consolidated file
from .interfaces import (
    # Event interfaces
    Event,
    EventType,
    # Generator interfaces
    IASTExtractor,
    # Model interfaces
    IASTProcessor,
    # Extractor interfaces
    IBinaryExtractor,
    IBinaryFileParser,
    # Decompiler interfaces
    IControlFlowAnalyzer,
    IDecompiler,
    IDecompilerCoordinator,
    IEntityFactory,
    IEntityValidator,
    # Parser interfaces
    IEnumeratedType,
    IEventBus,
    IEventHandler,
    IEventProcessor,
    IExpressionEvaluator,
    IExpressionReconstructor,
    IExtractionStatistics,
    IExtractionValidator,
    IExtractor,
    IExtractOrchestrator,
    IExtractorCoordinator,
    IGenerator,
    IGeneratorCoordinator,
    IGeneratorFactory,
    IGrammarManager,
    IImportResolver,
    ILibraryManager,
    # Logger interfaces
    ILogger,
    IModelExtractor,
    IModelPersistence,
    IObjectTypeDetector,
    IOutputFormatter,
    IOutputValidator,
    IParser,
    IParserCoordinator,
    IPathValidator,
    IPBDReader,
    IPCodeDecoder,
    # Pipeline interfaces
    IPipelineCoordinator,
    IPipelineStage,
    IPipelineState,
    IPreprocessor,
    IProgressReporter,
    IProgressTracker,
    IProjectScaffolder,
    IRecoveryEngine,
    IResourceExtractor,
    IResourceMonitor,
    IStateManager,
    IStructureType,
    ITemplateEngine,
    ITransformer,
    ITypeConverter,
    ITypeParser,
    ITypeResolver,
    IUIProcessor,
    IVersionDetector,
    PipelineStage,
    ProgressCallback,
    StageStatus,
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
