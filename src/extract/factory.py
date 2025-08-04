"""Factory for creating ExtractCoordinator with all dependencies.

This factory handles the construction of the ExtractCoordinator and all its
dependencies, supporting both simple and advanced configurations.
"""

import logging
from pathlib import Path
from typing import Any

from src.contracts.interfaces import IProgressReporter
from src.extract.components.orchestrator import ExtractOrchestrator
from src.extract.components.parser import BinaryFileParser
from src.extract.components.recovery import RecoveryEngine
from src.extract.components.resources import ResourceExtractor
from src.extract.components.statistics import ExtractionStatistics
from src.extract.components.validator import ExtractionValidator
from src.extract.coordinator import ExtractCoordinator

logger = logging.getLogger(__name__)


class SimpleProgressReporter(IProgressReporter):
    """Simple progress reporter implementation."""

    def __init__(self, show_progress: bool = True) -> None:
        """Initialize the progress reporter.

        Args:
            show_progress: Whether to actually show progress
        """
        self.show_progress = show_progress
        self._current_file = None
        self._total_entries = 0
        self._current_entry = 0

    def start_file(self, file_path: Path, total_entries: int) -> None:
        """Start processing a new file."""
        self._current_file = file_path
        self._total_entries = total_entries
        self._current_entry = 0

        if self.show_progress:
            logger.info("Processing %s (%d entries)", file_path.name, total_entries)

    def update_progress(
        self, current_entry: int, entry_name: str, message: str | None = None
    ) -> None:
        """Update extraction progress."""
        self._current_entry = current_entry

        if self.show_progress:
            percentage = (
                (current_entry / self._total_entries * 100)
                if self._total_entries > 0
                else 0
            )
            logger.info(
                "  [%d/%d] %.1f%% - %s %s",
                current_entry,
                self._total_entries,
                percentage,
                entry_name,
                message or "",
            )

    def complete_file(self, success: bool, message: str | None = None) -> None:
        """Mark file processing as complete."""
        if self.show_progress:
            status = "successfully" if success else "with errors"
            logger.info(
                "Completed %s %s. %s",
                self._current_file.name if self._current_file else "file",
                status,
                message or "",
            )


class ExtractFactory:
    """Factory for creating ExtractCoordinator instances."""

    @staticmethod
    def create_simple(
        input_path: str | Path | None = None,
        output_path: str | Path | None = None,
        enable_byte_recovery: bool = False,
        show_progress: bool = True,
        **kwargs: Any,
    ) -> ExtractCoordinator:
        """Create a simple ExtractCoordinator with default components.

        Args:
            input_path: Path to input PBD/PBL file
            output_path: Path to output directory
            enable_byte_recovery: Whether to enable byte-level recovery
            show_progress: Whether to show extraction progress
            **kwargs: Additional options passed to ExtractCoordinator

        Returns:
            Configured ExtractCoordinator instance
        """
        # Create default components
        parser = BinaryFileParser()
        validator = ExtractionValidator()
        statistics = ExtractionStatistics()
        recovery_engine = RecoveryEngine() if enable_byte_recovery else None
        progress_reporter = SimpleProgressReporter(show_progress)
        resource_extractor = ResourceExtractor()
        orchestrator = ExtractOrchestrator(
            parser=parser,
            validator=validator,
            statistics=statistics,
            recovery_engine=recovery_engine,
            progress_reporter=progress_reporter,
            resource_extractor=resource_extractor,
        )

        # Create coordinator
        return ExtractCoordinator(
            orchestrator=orchestrator,
            input_path=input_path,
            output_path=output_path,
            **kwargs,
        )

    @staticmethod
    def create_advanced(
        parser: BinaryFileParser | None = None,
        validator: ExtractionValidator | None = None,
        statistics: ExtractionStatistics | None = None,
        recovery_engine: RecoveryEngine | None = None,
        progress_reporter: IProgressReporter | None = None,
        resource_extractor: ResourceExtractor | None = None,
        input_path: str | Path | None = None,
        output_path: str | Path | None = None,
        **kwargs: Any,
    ) -> ExtractCoordinator:
        """Create an ExtractCoordinator with custom components.

        Args:
            parser: Custom binary file parser
            validator: Custom extraction validator
            statistics: Custom statistics collector
            recovery_engine: Custom recovery engine
            progress_reporter: Custom progress reporter
            resource_extractor: Custom resource extractor
            input_path: Path to input PBD/PBL file
            output_path: Path to output directory
            **kwargs: Additional options passed to ExtractCoordinator

        Returns:
            Configured ExtractCoordinator instance
        """
        # Use provided components or create defaults
        parser = parser or BinaryFileParser()
        validator = validator or ExtractionValidator()
        statistics = statistics or ExtractionStatistics()
        progress_reporter = progress_reporter or SimpleProgressReporter()
        resource_extractor = resource_extractor or ResourceExtractor()

        orchestrator = ExtractOrchestrator(
            parser=parser,
            validator=validator,
            statistics=statistics,
            recovery_engine=recovery_engine,
            progress_reporter=progress_reporter,
            resource_extractor=resource_extractor,
        )

        return ExtractCoordinator(
            orchestrator=orchestrator,
            input_path=input_path,
            output_path=output_path,
            **kwargs,
        )
