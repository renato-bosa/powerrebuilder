"""Refactored Extract Coordinator using composition and dependency injection.

This coordinator uses proper dependency injection and delegates to focused components
for better maintainability and testability.
"""

import logging
from pathlib import Path
from typing import Callable

from src.contracts.types import ExtractionStatsDict

from src.contracts.interfaces import (
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
        super().__init__(
            input_path=input_path or Path.cwd(), output_path=output_dir or Path.cwd()
        )

        # Store paths for simple mode
        self.input_path = Path(input_path) if input_path else None
        self.output_dir = Path(output_dir) if output_dir else None

        # Import defaults only when needed to avoid circular imports
        from src.extract.components.parser import BinaryFileParser
        from src.extract.components.recovery import RecoveryEngine
        from src.extract.components.resources import ResourceExtractor
        from src.extract.components.statistics import ExtractionStatistics
        from src.extract.components.validator import ExtractionValidator

        # Ensure all components are available
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

    def process(self) -> ExtractionStatsDict:
        """Process input files and produce output.

        Returns:
            Dictionary with extraction results
        """
        if not self.input_path or not self.output_dir:
            raise ValueError("Input path and output directory must be set")

        # Use synchronous extraction for now
        from src.extract.extract import extract_pbl_file

        try:
            extract_pbl_file(str(self.input_path), str(self.output_dir))
            return {
                "status": "success",
                "input": str(self.input_path),
                "output": str(self.output_dir),
            }
        except Exception as e:
            logger.error("Extraction failed: %s", e)
            return {
                "status": "failed",
                "error": str(e),
                "input": str(self.input_path),
                "output": str(self.output_dir),
            }

    def validate_inputs(self) -> bool:
        """Validate input requirements for the stage.

        Returns:
            True if inputs are valid
        """
        if not self.input_path:
            logger.error("No input path specified")
            return False

        if not self.input_path.exists():
            logger.error("Input path does not exist: %s", self.input_path)
            return False

        if not self.output_dir:
            logger.error("No output directory specified")
            return False

        return True

    async def run(
        self, 
        progress_callback: Callable[[str, float], None] | None = None,
        **kwargs: str | Path | bool
    ) -> ExtractionStatsDict:
        """Run the extraction process.

        Args:
            progress_callback: Optional callback for progress updates
            **kwargs: Extraction parameters including:
                - input_path: Path to PBL/PBD file
                - output_dir: Directory for extracted files
                - enable_recovery: Whether to enable recovery mode

        Returns:
            Dictionary with extraction results
        """
        # Set progress callback if provided
        if progress_callback:
            self.set_progress_callback(progress_callback)
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
        return self.orchestrator.orchestrate_extraction(
            input_path=input_path,
            output_dir=output_dir,
        )

        # Statistics are already tracked in the orchestrator

    def extract(self, progress_callback=None) -> ExtractionStatsDict:
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
