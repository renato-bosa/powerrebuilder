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
    "DetailedLoggerAdapter",
    # Events
    "Event",
    "EventType",
    # Generators
    "IASTExtractor",
    # Models
    "IASTProcessor",
    # Extractors
    "IBinaryExtractor",
    "IBinaryFileParser",
    # Decompilers
    "IControlFlowAnalyzer",
    "IDecompiler",
    "IDecompilerCoordinator",
    "IEntityFactory",
    "IEntityValidator",
    # Parsers
    "IEnumeratedType",
    "IEventBus",
    "IEventHandler",
    "IEventProcessor",
    "IExpressionEvaluator",
    "IExpressionReconstructor",
    "IExtractOrchestrator",
    "IExtractionStatistics",
    "IExtractionValidator",
    "IExtractor",
    "IExtractorCoordinator",
    "IGenerator",
    "IGeneratorCoordinator",
    "IGeneratorFactory",
    "IGrammarManager",
    "IImportResolver",
    "ILibraryManager",
    # Logger
    "ILogger",
    "IModelExtractor",
    "IModelPersistence",
    "IObjectTypeDetector",
    "IOutputFormatter",
    "IOutputValidator",
    "IPBDReader",
    "IPCodeDecoder",
    "IParser",
    "IParserCoordinator",
    "IPathValidator",
    # Pipeline
    "IPipelineCoordinator",
    "IPipelineStage",
    "IPipelineState",
    "IPreprocessor",
    "IProgressReporter",
    "IProgressTracker",
    "IProjectScaffolder",
    "IRecoveryEngine",
    "IResourceExtractor",
    "IResourceMonitor",
    "IStateManager",
    "IStructureType",
    "ITemplateEngine",
    "ITransformer",
    "ITypeConverter",
    "ITypeParser",
    "ITypeResolver",
    "IUIProcessor",
    "IVersionDetector",
    "PipelineStage",
    "ProgressCallback",
    "StageStatus",
    "StandardLogger",
]
