"""Refactored Extract Coordinator using composition and dependency injection.

This coordinator uses proper dependency injection and delegates to focused components
for better maintainability and testability.
"""

import logging
from pathlib import Path
from typing import Any

from src.contracts.extractors import (
    IBinaryFileParser,
    IExtractionStatistics,
    IExtractionValidator,
    IProgressReporter,
    IRecoveryEngine,
    IResourceExtractor,
)
from src.core.coordination_base import EnhancedCoordinator
from src.extract.components.orchestrator import ExtractionOrchestrator

logger = logging.getLogger(__name__)


class ExtractCoordinator(EnhancedCoordinator):
    """Coordinator for PowerBuilder file extraction.

    This coordinator handles the extraction of resources from PBL/PBD files,
    delegating the actual work to specialized components.
    """

    def __init__(
        self,
        binary_parser: IBinaryFileParser | None = None,
        resource_extractor: IResourceExtractor | None = None,
        recovery_engine: IRecoveryEngine | None = None,
        validator: IExtractionValidator | None = None,
        statistics: IExtractionStatistics | None = None,
        progress_reporter: IProgressReporter | None = None,
        input_path: Path | str | None = None,
        output_dir: Path | str | None = None,
    ) -> None:
        """Initialize the extract coordinator.

        Args:
            binary_parser: Component for parsing binary files
            resource_extractor: Component for extracting resources
            recovery_engine: Component for recovery strategies
            validator: Component for validation
            statistics: Component for tracking statistics
            progress_reporter: Optional component for progress reporting
            input_path: Input PBL/PBD file path (for simple mode)
            output_dir: Output directory (for simple mode)
        """
        super().__init__()

        # Store paths for simple mode
        self.input_path = Path(input_path) if input_path else None
        self.output_dir = Path(output_dir) if output_dir else None

        # If no components provided, create default ones
        if not all(
            [binary_parser, resource_extractor, recovery_engine, validator, statistics]
        ):
            # Import defaults only when needed to avoid circular imports
            from src.extract.components.parser import BinaryFileParser
            from src.extract.components.recovery import RecoveryEngine
            from src.extract.components.resources import ResourceExtractor
            from src.extract.components.statistics import ExtractionStatistics
            from src.extract.components.validator import ExtractionValidator

            binary_parser = binary_parser or BinaryFileParser()
            resource_extractor = resource_extractor or ResourceExtractor()
            recovery_engine = recovery_engine or RecoveryEngine()
            validator = validator or ExtractionValidator()
            statistics = statistics or ExtractionStatistics()

        self.orchestrator = ExtractionOrchestrator(
            binary_parser=binary_parser,
            resource_extractor=resource_extractor,
            recovery_engine=recovery_engine,
            validator=validator,
            statistics=statistics,
            progress_reporter=progress_reporter,
        )

    async def run(self, **kwargs: Any) -> dict[str, Any]:
        """Run the extraction process.

        Args:
            **kwargs: Extraction parameters including:
                - input_path: Path to PBL/PBD file
                - output_dir: Directory for extracted files
                - enable_recovery: Whether to enable recovery mode

        Returns:
            Dictionary with extraction results
        """
        input_path = kwargs.get("input_path")
        output_dir = kwargs.get("output_dir")

        if not input_path or not output_dir:
            raise ValueError("input_path and output_dir are required")

        # Convert to Path objects
        input_path = Path(input_path)
        output_dir = Path(output_dir)

        # Ensure output directory exists
        output_dir.mkdir(parents=True, exist_ok=True)

        # Run extraction through orchestrator
        result = await self.orchestrator.orchestrate_extraction(
            library_path=input_path,
            output_dir=output_dir,
            enable_recovery=kwargs.get("enable_recovery", False),
        )

        # Update statistics
        self.update_stats(
            {
                "files_extracted": result.get("extracted_count", 0),
                "errors": result.get("error_count", 0),
            }
        )

        return result

    def extract(self, progress_callback=None) -> dict[str, Any]:
        """Synchronous extraction method for pipeline compatibility.

        Args:
            progress_callback: Optional callback for progress updates

        Returns:
            Dictionary with extraction results
        """
        import asyncio

        from src.common.pipeline.progress_adapter import PipelineProgressAdapter

        # Create progress adapter if callback provided
        if progress_callback:
            progress_adapter = PipelineProgressAdapter(progress_callback)
            # Replace the orchestrator's progress reporter
            self.orchestrator.progress_reporter = progress_adapter

        # Run async extraction
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            return loop.run_until_complete(
                self.run(
                    input_path=self.input_path,
                    output_dir=self.output_dir,
                    enable_recovery=True,
                )
            )
        finally:
            loop.close()
