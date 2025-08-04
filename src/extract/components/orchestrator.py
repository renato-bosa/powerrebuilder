"""High-level extraction orchestration component.

This component coordinates the overall extraction process, delegating specific
tasks to other specialized components.
"""

import logging
from pathlib import Path
from typing import Any

from src.contracts.interfaces import (
    IBinaryFileParser,
    IExtractionStatistics,
    IExtractionValidator,
    IProgressReporter,
    IRecoveryEngine,
    IResourceExtractor,
)
from src.core.security import sanitize_filename

logger = logging.getLogger(__name__)


class ExtractionOrchestrator:
    """High-level extraction orchestration component.

    This component handles the overall extraction workflow, coordinating
    between various specialized components to extract PowerBuilder files.
    """

    def __init__(
        self,
        binary_parser: IBinaryFileParser,
        resource_extractor: IResourceExtractor,
        recovery_engine: IRecoveryEngine,
        validator: IExtractionValidator,
        statistics: IExtractionStatistics,
        progress_reporter: IProgressReporter | None = None,
    ) -> None:
        """Initialize the orchestrator with required components.

        Args:
            binary_parser: Component for parsing binary files
            resource_extractor: Component for extracting resources
            recovery_engine: Component for recovery strategies
            validator: Component for validation
            statistics: Component for tracking statistics
            progress_reporter: Optional component for progress reporting
        """
        self.binary_parser = binary_parser
        self.resource_extractor = resource_extractor
        self.recovery_engine = recovery_engine
        self.validator = validator
        self.statistics = statistics
        self.progress_reporter = progress_reporter

        self.enable_byte_recovery = False
        self.extract_resources = True
        self.show_progress = True

    def orchestrate_extraction(
        self,
        input_path: Path,
        output_dir: Path,
        pattern: str = "*.pbd",
    ) -> dict[str, Any]:
        """Orchestrate the extraction process.

        Args:
            input_path: Path to file or directory to extract
            output_dir: Directory to extract to
            pattern: File pattern for directory extraction

        Returns:
            Extraction results dictionary
        """
        # Ensure output directory exists
        output_dir.mkdir(parents=True, exist_ok=True)

        # Initialize statistics
        self.statistics.start_extraction()

        results = {
            "files": [],
            "errors": [],
            "statistics": {},
        }

        try:
            if input_path.is_file():
                # Single file extraction
                result = self._extract_single_file(input_path, output_dir)
                results["files"].append(result)
            else:
                # Directory extraction
                files = list(input_path.glob(pattern))
                for file_path in files:
                    if self.progress_reporter:
                        self.progress_reporter.report_file_start(str(file_path))

                    result = self._extract_single_file(file_path, output_dir)
                    results["files"].append(result)

                    if self.progress_reporter:
                        self.progress_reporter.report_file_complete(str(file_path))

        except Exception as e:
            logger.exception("Extraction failed: %s", e)
            results["errors"].append(str(e))

        # Finalize statistics
        self.statistics.finalize_extraction()
        results["statistics"] = self.statistics.get_summary()

        return results

    def _extract_single_file(self, file_path: Path, output_dir: Path) -> dict[str, Any]:
        """Extract a single file.

        Args:
            file_path: Path to file to extract
            output_dir: Directory to extract to

        Returns:
            Extraction result for the file
        """
        result = {
            "file": str(file_path),
            "status": "pending",
            "entries": [],
            "errors": [],
        }

        try:
            # Parse the binary file
            parsed_data = self.binary_parser.parse_file(file_path)

            # Create output directory for this file
            file_output_dir = output_dir / sanitize_filename(file_path.stem)
            file_output_dir.mkdir(exist_ok=True)

            # Extract entries
            for entry in parsed_data.get("entries", []):
                try:
                    # Validate entry
                    if self.validator.validate_entry(entry):
                        # Extract resources if enabled
                        if self.extract_resources:
                            extracted = self.resource_extractor.extract_resource(
                                entry, file_output_dir
                            )
                            result["entries"].append(extracted)
                            self.statistics.record_success(entry["type"])
                    # Try recovery if validation fails
                    elif self.enable_byte_recovery:
                        recovered = self.recovery_engine.attempt_recovery(
                            entry, file_output_dir
                        )
                        if recovered:
                            result["entries"].append(recovered)
                            self.statistics.record_recovery(entry["type"])
                        else:
                            result["errors"].append(
                                f"Failed to extract {entry.get('name', 'unknown')}"
                            )
                            self.statistics.record_failure(entry["type"])
                except Exception as e:
                    logger.error("Failed to extract entry: %s", e)
                    result["errors"].append(str(e))
                    self.statistics.record_failure(entry.get("type", "unknown"))

            result["status"] = "success" if not result["errors"] else "partial"

        except Exception as e:
            logger.exception("Failed to parse %s: %s", file_path, e)
            result["status"] = "failed"
            result["errors"].append(str(e))
            self.statistics.record_file_failure()

        return result

    def set_options(
        self,
        enable_byte_recovery: bool = False,
        extract_resources: bool = True,
        show_progress: bool = True,
    ) -> None:
        """Set extraction options.

        Args:
            enable_byte_recovery: Enable byte-level recovery
            extract_resources: Extract embedded resources
            show_progress: Show progress updates
        """
        self.enable_byte_recovery = enable_byte_recovery
        self.extract_resources = extract_resources
        self.show_progress = show_progress
