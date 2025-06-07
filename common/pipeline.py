"""Common pipeline utilities and base classes.

This module provides base classes and utilities for pipeline stages
to reduce code duplication across coordinators.
"""

import json
import logging
from abc import ABC, abstractmethod
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


class PipelineStage(ABC):
    """Base class for all pipeline stages (coordinators).
    
    Provides common functionality for:
    - Directory handling
    - Progress tracking
    - Error handling
    - Summary generation
    """
    
    def __init__(self, stage_name: str):
        """Initialize pipeline stage.
        
        Args:
            stage_name: Name of this pipeline stage (e.g., 'extract', 'parse')
        """
        self.stage_name = stage_name
        self.logger = logging.getLogger(f"{__name__}.{stage_name}")
        
    def ensure_directory(self, path: Path) -> Path:
        """Ensure directory exists, creating if necessary.
        
        Args:
            path: Directory path
            
        Returns:
            The path object for chaining
        """
        path.mkdir(parents=True, exist_ok=True)
        return path
    
    @abstractmethod
    def process_file(self, input_file: Path, output_dir: Path) -> Dict[str, Any]:
        """Process a single file.
        
        Args:
            input_file: Input file path
            output_dir: Output directory path
            
        Returns:
            Dictionary with processing results
            
        Raises:
            Exception: If processing fails
        """
        pass
    
    def process_directory(
        self,
        input_dir: Path,
        output_dir: Path,
        pattern: str = "*",
        recursive: bool = True,
        progress: bool = True
    ) -> Dict[str, Any]:
        """Process all matching files in a directory.
        
        Args:
            input_dir: Input directory path
            output_dir: Output directory path
            pattern: File pattern to match (e.g., "*.pbd")
            recursive: Whether to search recursively
            progress: Whether to show progress
            
        Returns:
            Summary dictionary with processing results
        """
        # Ensure paths are Path objects
        input_dir = Path(input_dir)
        output_dir = Path(output_dir)
        
        # Ensure output directory exists
        self.ensure_directory(output_dir)
        
        # Find files
        if recursive:
            files = list(input_dir.rglob(pattern))
        else:
            files = list(input_dir.glob(pattern))
            
        # Initialize summary
        summary = PipelineSummary(self.stage_name, input_dir, output_dir)
        
        # Get progress tracker
        tracker = self._get_progress_tracker(len(files), progress)
        
        # Process files
        with tracker:
            for file_path in files:
                try:
                    # Process file
                    result = self.process_file(file_path, output_dir)
                    summary.add_success(file_path, result)
                    
                except Exception as e:
                    self.logger.error(f"Failed to process {file_path}: {e}")
                    summary.add_failure(file_path, str(e))
                    
                finally:
                    tracker.update()
        
        return summary.generate()
    
    def _get_progress_tracker(self, total: int, enabled: bool = True):
        """Get appropriate progress tracker.
        
        Args:
            total: Total number of items
            enabled: Whether progress tracking is enabled
            
        Returns:
            Progress tracker instance
        """
        try:
            from extract.pbd_io.progress import (
                SilentProgressTracker,
                TqdmProgressTracker,
            )
            
            if enabled and total > 0:
                return TqdmProgressTracker(
                    total=total,
                    description=f"{self.stage_name.capitalize()} progress"
                )
            else:
                return SilentProgressTracker(
                    total=total,
                    description=f"{self.stage_name.capitalize()} progress"
                )
        except ImportError:
            # Fallback to no-op progress tracker
            return NoOpProgressTracker()
    
    def save_summary(self, summary: Dict[str, Any], output_dir: Path) -> Path:
        """Save processing summary to JSON file.
        
        Args:
            summary: Summary dictionary
            output_dir: Output directory
            
        Returns:
            Path to saved summary file
        """
        summary_file = output_dir / f"{self.stage_name}_summary.json"
        
        with open(summary_file, "w", encoding="utf-8") as f:
            json.dump(summary, f, indent=2, default=str)
            
        self.logger.info(f"Saved {self.stage_name} summary to {summary_file}")
        return summary_file


class PipelineSummary:
    """Standardized summary generation for pipeline stages."""
    
    def __init__(self, stage_name: str, input_dir: Path, output_dir: Path):
        """Initialize summary.
        
        Args:
            stage_name: Name of pipeline stage
            input_dir: Input directory
            output_dir: Output directory
        """
        self.stage_name = stage_name
        self.input_dir = input_dir
        self.output_dir = output_dir
        self.start_time = datetime.now()
        self.success_count = 0
        self.failure_count = 0
        self.results: List[Dict[str, Any]] = []
        self.errors: List[Dict[str, str]] = []
        
    def add_success(self, file_path: Path, result: Optional[Dict[str, Any]] = None):
        """Record successful processing.
        
        Args:
            file_path: File that was processed
            result: Optional result data
        """
        self.success_count += 1
        
        if result:
            self.results.append({
                "file": str(file_path),
                "status": "success",
                **result
            })
            
    def add_failure(self, file_path: Path, error: str):
        """Record processing failure.
        
        Args:
            file_path: File that failed
            error: Error message
        """
        self.failure_count += 1
        self.errors.append({
            "file": str(file_path),
            "error": error
        })
        
    def generate(self) -> Dict[str, Any]:
        """Generate final summary.
        
        Returns:
            Summary dictionary
        """
        duration = (datetime.now() - self.start_time).total_seconds()
        
        return {
            "stage": self.stage_name,
            "processed_at": self.start_time.isoformat(),
            "duration_seconds": duration,
            "input_directory": str(self.input_dir),
            "output_directory": str(self.output_dir),
            "statistics": {
                "total_files": self.success_count + self.failure_count,
                "successful": self.success_count,
                "failed": self.failure_count,
                "success_rate": (
                    self.success_count / (self.success_count + self.failure_count)
                    if (self.success_count + self.failure_count) > 0
                    else 0.0
                )
            },
            "results": self.results if self.results else None,
            "errors": self.errors if self.errors else None
        }


class NoOpProgressTracker:
    """No-operation progress tracker for when tqdm is not available."""
    
    def __enter__(self):
        return self
        
    def __exit__(self, exc_type, exc_val, exc_tb):
        pass
        
    def update(self, n=1):
        pass
        
    def finish(self):
        pass