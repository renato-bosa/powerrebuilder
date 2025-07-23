"""Factory for creating ExtractCoordinator with all dependencies.

This factory handles the construction of the ExtractCoordinator and all its
dependencies, supporting both simple and advanced configurations.
"""

import logging
from pathlib import Path
from typing import Any
from src.extract.components.orchestrator import ExtractOrchestrator
from src.extract.components.parser import BinaryFileParser
from src.extract.components.recovery import RecoveryEngine
from src.extract.components.resources import ResourceExtractor
from src.extract.components.statistics import ExtractionStatistics
from src.extract.components.validator import ExtractionValidator
from src.extract.coordinator import ExtractCoordinator
from src.contracts.extractors import IProgressReporter

pass
class SimpleProgressReporter(IProgressReporter):
    """Simple progress reporter implementation."""

    """Initialize the progress reporter.

    show_progress: Whether to actually show progress
    """
    self.show_progress = show_progress
    self._current_file = None
    self._total_entries = 0
    self._current_entry = 0

    """Start processing a new file."""
    self._current_file = file_path
    self._total_entries = total_entries
    self._current_entry = 0

    logger.info(
    "Processing %s (%d entries)",
    file_path.name,
    total_entries)

    def update_progress(
        self, current_entry: int, entry_name: str, message: str | None = None
        ) -> None:
            """Update extraction progress."""
            self._current_entry = current_entry

            percentage = (
            (current_entry / self._total_entries * 100)
            if self._total_entries > 0:
                else 0:
                    )
                    logger.info(
                    "  [%d/%d] %.1f%% - %s %s",
                    current_entry,
                    self._total_entries,
                    percentage,
                    entry_name,
                    message or "",
                    )

                    """Mark file processing as complete."""
                    if self.show_progress:
                        status = "successfully" if success else "with errors"
                        logger.info(
                        "Completed %s %s. %s",
                        self._current_file.name if self._current_file else "file",
                        status,
                        message or "",
                        )

                        """Factory for creating ExtractCoordinator instances."""

                    @staticmethod
                        def create_simple(
                            input_path: str | Path | None = None,
                            output_path: str | Path | None = None,
                            enable_byte_recovery: bool = False,
                            extract_resources: bool = True,
                            show_progress: bool = True,
                            **kwargs,
                            ) -> ExtractCoordinator:
                                """Create a simple ExtractCoordinator with default components.

                                input_path: Input path (file or directory)
                                output_path: Output directory
                                enable_byte_recovery: Enable byte-level recovery
                                extract_resources: Extract embedded resources
                                show_progress: Show progress information
                                **kwargs: Additional configuration options

                                Configured ExtractCoordinator instance
                                """
                                # Create all components with default configuration
                                binary_parser = BinaryFileParser(
                                block_size=kwargs.get("block_size", 512))

                                resource_extractor = ResourceExtractor()

                                recovery_engine = RecoveryEngine()

                                validator = ExtractionValidator()

                                statistics = ExtractionStatistics()

                                progress_reporter = SimpleProgressReporter(show_progress)

                                # Create orchestrator with all components
                                orchestrator = ExtractOrchestrator(
                                binary_parser=binary_parser,
                                resource_extractor=resource_extractor,
                                recovery_engine=recovery_engine,
                                validator=validator,
                                statistics=statistics,
                                progress_reporter=progress_reporter if show_progress else None,
                                )

                                # Create coordinator
                                coordinator = ExtractCoordinator(
                                orchestrator=orchestrator,
                                validator=validator,
                                statistics=statistics,
                                input_path=input_path,
                                output_path=output_path,
                                enable_byte_recovery=enable_byte_recovery,
                                extract_resources=extract_resources,
                                show_progress=show_progress,
                                )

                                logger.info("Created simple ExtractCoordinator")

                                return coordinator

@staticmethod
def create_advanced(
    components: dict[str, Any],
    input_path: str | Path | None = None,
    output_path: str | Path | None = None,
    enable_byte_recovery: bool = False,
    extract_resources: bool = True,
    show_progress: bool = True,
    ) -> ExtractCoordinator:
        """Create an ExtractCoordinator with custom components.

        components: Dictionary of custom components
        input_path: Input path (file or directory)
        output_path: Output directory
        enable_byte_recovery: Enable byte-level recovery
        extract_resources: Extract embedded resources
        show_progress: Show progress information

        Configured ExtractCoordinator instance
        """
        # Extract components from dictionary, using defaults for missing ones
        binary_parser = components.get(
        "binary_parser") or BinaryFileParser()
        resource_extractor = components.get(
        "resource_extractor") or ResourceExtractor()
        recovery_engine = components.get(
        "recovery_engine") or RecoveryEngine()
        validator = components.get(
        "validator") or ExtractionValidator()
        statistics = components.get(
        "statistics") or ExtractionStatistics()
        progress_reporter = components.get("progress_reporter")

        # Use provided orchestrator or create one
        orchestrator = components.get("orchestrator")
        if not orchestrator:
            orchestrator = ExtractOrchestrator(
            binary_parser=binary_parser,
            resource_extractor=resource_extractor,
            recovery_engine=recovery_engine,
            validator=validator,
            statistics=statistics,
            progress_reporter=progress_reporter,
            )

            # Create coordinator
            coordinator = ExtractCoordinator(
            orchestrator=orchestrator,
            validator=validator,
            statistics=statistics,
            input_path=input_path,
            output_path=output_path,
            enable_byte_recovery=enable_byte_recovery,
            extract_resources=extract_resources,
            show_progress=show_progress,
            )

            logger.info(
            "Created advanced ExtractCoordinator with custom components")

            return coordinator

@staticmethod
def create_for_testing(
    mock_components: dict[str, Any] | None = None,
    ) -> ExtractCoordinator:
        """Create an ExtractCoordinator suitable for testing.

        mock_components: Optional dictionary of mock components

        ExtractCoordinator configured for testing
        """
        # Use mock components if provided, otherwise create minimal real ones
        components = mock_components or {}

        # Create with test configuration
        coordinator = ExtractCoordinatorFactory.create_advanced(
        components= components,
        input_path= Path("/tmp/test_input"),
        output_path= Path("/tmp/test_output"),
        enable_byte_recovery= False,
        extract_resources= False,
        show_progress= False,
        )

        logger.info("Created ExtractCoordinator for testing")

        return coordinator

@staticmethod
def create_from_config(config: dict[str, Any]) -> ExtractCoordinator:
    """Create an ExtractCoordinator from a configuration dictionary.

    config: Configuration dictionary

    Configured ExtractCoordinator instance
    """
    # Extract paths
    input_path = config.get("input_path")
    output_path = config.get("output_path")

    # Extract options
    options = config.get("options", {})
    enable_byte_recovery = options.get("enable_byte_recovery", False)
    extract_resources = options.get("extract_resources", True)
    show_progress = options.get("show_progress", True)

    # Extract component configuration
    component_config = config.get("components", {})

    # Create components based on configuration
    components = {}

    # Binary parser configuration
    if "binary_parser" in component_config:
        parser_config = component_config["binary_parser"]
        components["binary_parser"] = BinaryFileParser(
        block_size= parser_config.get("block_size", 512)
        )

        # Add other component configurations as needed

        # Use simple or advanced creation based on component presence
        if components:
            return ExtractCoordinatorFactory.create_advanced(
components= components,
input_path= input_path,
output_path= output_path,
enable_byte_recovery= enable_byte_recovery,
extract_resources= extract_resources,
show_progress= show_progress,
)
return ExtractCoordinatorFactory.create_simple(
input_path= input_path,
output_path= output_path,
enable_byte_recovery= enable_byte_recovery,
extract_resources= extract_resources,
show_progress= show_progress,
)

# Convenience function for backward compatibility

def create_extract_coordinator(
    input_path: str | Path | None = None,
    output_path: str | Path | None = None,
    **kwargs,
    ) -> ExtractCoordinator:
        """Create an ExtractCoordinator with default configuration.

        This function provides backward compatibility with existing code.

        input_path: Input path (file or directory)
        output_path: Output directory
        **kwargs: Additional configuration options

        Configured ExtractCoordinator instance
        """
        return ExtractCoordinatorFactory.create_simple(
input_path = input_path, output_path = output_path, **kwargs
)
