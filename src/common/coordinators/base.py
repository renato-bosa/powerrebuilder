"""Base coordinator class with common functionality for pipeline stages.

This module provides a consolidated BaseCoordinator class that contains all the
common functionality found across the various coordinator classes in the codebase.
This eliminates duplication and provides a consistent interface for all stages.
"""

import json
import logging
from abc import ABC, abstractmethod
from collections.abc import Callable
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Union


class BaseCoordinator(ABC):
    """Base coordinator with common functionality for all pipeline stages.
    
    This class provides shared functionality that was previously duplicated
    across multiple coordinator classes:
    - Common initialization (input_dir, output_dir)
    - Statistics tracking
    - Progress reporting
    - Error collection
    - Summary writing
    - File discovery methods
    """

    def __init__(
        self,
        input_dir: str | Path,
        output_dir: str | Path,
        stage_name: str | None = None,
    ) -> None:
        """Initialize the base coordinator.

        Args:
            input_dir: Directory containing input files
            output_dir: Directory to write output files
            stage_name: Name of the processing stage (defaults to class name)
        """
        self.input_dir = Path(input_dir)
        self.output_dir = Path(output_dir)
        self.stage_name = stage_name or self.__class__.__name__.replace("Coordinator", "").lower()
        
        # Ensure output directory exists
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        # Set up logging
        self.logger = logging.getLogger(self.__class__.__name__)
        
        # Initialize statistics tracking
        self._stats: dict[str, Any] = {
            "stage": self.stage_name,
            "total_files": 0,
            "successful": 0,
            "failed": 0,
            "skipped": 0,
            "errors": [],
            "warnings": [],
            "start_time": None,
            "end_time": None,
            "duration_seconds": 0.0,
        }

    @abstractmethod
    def process(self, progress_callback: Callable[[int, int, str], None] | None = None) -> dict[str, Any]:
        """Process input files and produce output.
        
        Args:
            progress_callback: Optional callback for progress updates (current, total, message)
        
        Returns:
            Dictionary containing processing statistics
        """

    @abstractmethod
    def validate_inputs(self) -> bool:
        """Validate input requirements for the stage.
        
        Returns:
            True if inputs are valid, False otherwise
        """

    def get_statistics(self) -> dict[str, Any]:
        """Get current processing statistics.
        
        Returns:
            Copy of current statistics
        """
        return self._stats.copy()

    def record_start(self) -> None:
        """Record processing start time."""
        self._stats["start_time"] = datetime.now().isoformat()

    def record_end(self) -> None:
        """Record processing end time and calculate duration."""
        end_time = datetime.now()
        self._stats["end_time"] = end_time.isoformat()
        
        if self._stats["start_time"]:
            start_time = datetime.fromisoformat(self._stats["start_time"])
            self._stats["duration_seconds"] = (end_time - start_time).total_seconds()

    def record_success(self) -> None:
        """Record a successful file processing."""
        self._stats["successful"] += 1

    def record_failure(self, error: str, context: str | None = None) -> None:
        """Record a failed file processing.
        
        Args:
            error: Error message
            context: Optional context (e.g., file path)
        """
        self._stats["failed"] += 1
        error_info = {"error": error}
        if context:
            error_info["context"] = context
        self._stats["errors"].append(error_info)

    def record_warning(self, warning: str, context: str | None = None) -> None:
        """Record a warning.
        
        Args:
            warning: Warning message  
            context: Optional context (e.g., file path)
        """
        warning_info = {"warning": warning}
        if context:
            warning_info["context"] = context
        self._stats["warnings"].append(warning_info)

    def record_skip(self) -> None:
        """Record a skipped file."""
        self._stats["skipped"] += 1

    def discover_files(self, patterns: list[str]) -> list[Path]:
        """Discover files matching the given patterns.
        
        Args:
            patterns: List of glob patterns (e.g., ["*.sru", "*.srw"])
        
        Returns:
            List of matching file paths
        """
        files = []
        for pattern in patterns:
            files.extend(self.input_dir.rglob(pattern))
        return sorted(files)

    def write_summary(self, filename: str = "summary.json") -> None:
        """Write processing summary to output directory.
        
        Args:
            filename: Name of summary file (default: "summary.json")
        """
        summary = {
            "stage": self.stage_name,
            "input_dir": str(self.input_dir),
            "output_dir": str(self.output_dir),
            "processed_at": datetime.now().isoformat(),
            "statistics": self._stats,
        }

        summary_path = self.output_dir / filename
        with summary_path.open("w", encoding="utf-8") as f:
            json.dump(summary, f, indent=2)

        self.logger.info("Wrote %s summary to %s", self.stage_name, summary_path)

    def log_summary(self) -> None:
        """Log processing summary."""
        total = self._stats["total_files"]
        successful = self._stats["successful"]
        failed = self._stats["failed"]
        skipped = self._stats["skipped"]
        duration = self._stats["duration_seconds"]

        self.logger.info(
            "%s complete: %d total, %d successful, %d failed, %d skipped (%.1fs)",
            self.stage_name.title(),
            total,
            successful,
            failed,
            skipped,
            duration,
        )

        if failed > 0:
            self.logger.warning("Encountered %d errors during %s", failed, self.stage_name)
            for error_info in self._stats["errors"][:5]:  # Show first 5 errors
                context = error_info.get("context", "")
                error = error_info.get("error", "Unknown error")
                self.logger.warning("  %s: %s", context, error)
            if len(self._stats["errors"]) > 5:
                self.logger.warning("  ... and %d more errors", len(self._stats["errors"]) - 5)

    def run_with_progress(
        self, 
        progress_callback: Callable[[int, int, str], None] | None = None
    ) -> dict[str, Any]:
        """Main entry point that handles timing and summary generation.
        
        Args:
            progress_callback: Optional callback for progress updates
            
        Returns:
            Processing statistics
        """
        self.logger.info("Starting %s processing", self.stage_name)
        self.logger.info("Input: %s", self.input_dir)
        self.logger.info("Output: %s", self.output_dir)

        # Validate inputs
        if not self.validate_inputs():
            error_msg = f"Input validation failed for {self.stage_name}"
            self.logger.error(error_msg)
            return {
                "stage": self.stage_name,
                "status": "failed",
                "error": error_msg,
                **self._stats,
            }

        try:
            # Record start time
            self.record_start()

            # Run processing
            result = self.process(progress_callback)

            # Record end time
            self.record_end()

            # Log summary
            self.log_summary()

            # Write summary to file
            self.write_summary()

            # Return result with updated statistics
            result.update(self._stats)
            result["status"] = "success" if self._stats["failed"] == 0 else "partial"
            
            return result

        except Exception as e:
            self.record_end()
            self.record_failure(str(e), "processing")
            self.logger.error("Processing failed: %s", e)
            
            # Still write summary on failure
            self.write_summary()
            
            return {
                "stage": self.stage_name,
                "status": "failed",
                "error": str(e),
                **self._stats,
            }

    def get_relative_output_path(self, input_file: Path, new_extension: str) -> Path:
        """Get output path for a file, preserving directory structure.
        
        Args:
            input_file: Input file path
            new_extension: New file extension (e.g., ".ast.json")
            
        Returns:
            Output file path with preserved directory structure
        """
        try:
            # Try to get relative path from input directory
            relative_path = input_file.relative_to(self.input_dir)
        except ValueError:
            # If file is not under input_dir, just use the filename
            relative_path = Path(input_file.name)

        # Change extension
        output_filename = relative_path.stem + new_extension
        output_path = self.output_dir / relative_path.parent / output_filename
        
        # Ensure parent directory exists
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        return output_path

    def validate_common_inputs(self) -> bool:
        """Validate common input requirements.
        
        Returns:
            True if basic inputs are valid
        """
        if not self.input_dir.exists():
            self.logger.error("Input directory does not exist: %s", self.input_dir)
            return False

        if not self.input_dir.is_dir():
            self.logger.error("Input path is not a directory: %s", self.input_dir)
            return False

        # Check if output directory can be created
        try:
            self.output_dir.mkdir(parents=True, exist_ok=True)
        except Exception as e:
            self.logger.error("Cannot create output directory %s: %s", self.output_dir, e)
            return False

        return True

    def process_files_with_callback(
        self,
        files: list[Path],
        processor: Callable[[Path], None],
        progress_callback: Callable[[int, int, str], None] | None = None,
        description: str = "Processing",
    ) -> None:
        """Process a list of files with progress reporting.
        
        Args:
            files: List of files to process
            processor: Function to process each file
            progress_callback: Optional progress callback
            description: Description for progress messages
        """
        self._stats["total_files"] = len(files)

        if progress_callback:
            progress_callback(0, len(files), f"Starting {description.lower()}")

        for idx, file_path in enumerate(files):
            if progress_callback:
                progress_callback(
                    idx + 1, 
                    len(files), 
                    f"{description} {file_path.name}"
                )

            try:
                processor(file_path)
                self.record_success()
                self.logger.debug("Successfully processed: %s", file_path)
            except Exception as e:
                self.record_failure(str(e), str(file_path))
                self.logger.error("Failed to process %s: %s", file_path, e)

        if progress_callback:
            progress_callback(len(files), len(files), f"{description} complete")