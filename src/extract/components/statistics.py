"""Statistics tracking component for extraction operations.

This component tracks detailed metrics and statistics during the extraction process.
"""

import logging
import time
from collections import defaultdict
from datetime import datetime
from pathlib import Path
from typing import Any

from src.contracts.interfaces import IExtractionStatistics

logger = logging.getLogger(__name__)


class ExtractionStatistics(IExtractionStatistics):
    """Tracks extraction metrics and statistics.

    This component provides detailed tracking of extraction operations including
    timing, success rates, file types, and recovery attempts.
    """

    def __init__(self) -> None:
        """Initialize the statistics tracker."""
        self.reset_statistics()

    def reset_statistics(self) -> None:
        """Reset all statistics to initial state."""
        self._stats = {
            "files": {
                "total": 0,
                "successful": 0,
                "failed": 0,
                "in_progress": None,
            },
            "entries": {
                "total": 0,
                "successful": 0,
                "failed": 0,
            },
            "entry_types": defaultdict(
                lambda: {
                    "total": 0,
                    "successful": 0,
                    "failed": 0,
                }
            ),
            "sizes": {
                "total_bytes": 0,
                "extracted_bytes": 0,
                "largest_entry": 0,
                "largest_entry_name": "",
                "smallest_entry": 0,
                "smallest_entry_name": "",
            },
            "timing": {
                "start_time": None,
                "end_time": None,
                "total_duration": 0,
                "file_durations": {},
            },
            "errors": {
                "total": 0,
                "by_type": defaultdict(int),
                "entries": [],
            },
            "recovery": {
                "attempts": 0,
                "successful": 0,
                "total_recovered": 0,
                "by_strategy": defaultdict(
                    lambda: {
                        "attempts": 0,
                        "successful": 0,
                        "recovered": 0,
                    }
                ),
                "history": [],
            },
            "file_details": {},
        }

        self._current_file = None
        self._current_file_start = None
        self._overall_start = None

    def start_extraction(self, file_path: Path) -> None:
        """Start tracking extraction for a file.

        Args:
            file_path: File being extracted
        """
        self._current_file = str(file_path)
        self._current_file_start = time.time()

        # Initialize file statistics
        self._stats["files"]["total"] += 1  # type: ignore[operator]
        self._stats["files"]["in_progress"] = str(file_path)  # type: ignore[assignment]

        # Track file info
        file_info = {
            "path": str(file_path),
            "name": file_path.name,
            "size": file_path.stat().st_size if file_path.exists() else 0,
            "start_time": datetime.now().isoformat(),
            "entries": [],
            "duration": 0,
            "success": False,
        }

        self._stats["file_details"][str(file_path)] = file_info  # type: ignore[assignment]

        # Set overall start time if this is the first file
        if self._overall_start is None:
            self._overall_start = time.time()
            self._stats["timing"]["start_time"] = datetime.now().isoformat()  # type: ignore[assignment]

    def end_file_extraction(self, success: bool) -> None:
        """End tracking for current file extraction.

        Args:
            success: Whether extraction was successful
        """
        if not self._current_file:
            return

        # Update file statistics
        if success:
            self._stats["files"]["successful"] += 1  # type: ignore[operator]
        else:
            self._stats["files"]["failed"] += 1  # type: ignore[operator]

        # Calculate duration
        if self._current_file_start:
            duration = time.time() - self._current_file_start
            self._stats["timing"]["file_durations"][self._current_file] = duration  # type: ignore[assignment]

            if self._current_file in self._stats["file_details"]:
                self._stats["file_details"][self._current_file]["duration"] = duration  # type: ignore[assignment]
                self._stats["file_details"][self._current_file]["success"] = success  # type: ignore[assignment]
                self._stats["file_details"][self._current_file]["end_time"] = (  # type: ignore[assignment]
                    datetime.now().isoformat()
                )

        # Clear current file tracking
        self._stats["files"]["in_progress"] = None  # type: ignore[assignment]
        self._current_file = None
        self._current_file_start = None

    def start_file_extraction(self, file_path: Path) -> None:
        """Backward compatibility method for start_extraction.

        Args:
            file_path: File being extracted
        """
        self.start_extraction(file_path)

    def record_entry_extracted(
        self, entry_name: str, entry_type: str, size: int, success: bool
    ) -> None:
        """Record extraction of a single entry.

        Args:
            entry_name: Name of the entry
            entry_type: Type of the entry
            size: Size in bytes
            success: Whether extraction was successful
        """
        # Update entry counts
        self._stats["entries"]["total"] += 1  # type: ignore[operator]
        if success:
            self._stats["entries"]["successful"] += 1  # type: ignore[operator]
        else:
            self._stats["entries"]["failed"] += 1  # type: ignore[operator]

        # Track by type
        self._stats["entry_types"][entry_type]["total"] += 1  # type: ignore[operator]
        if success:
            self._stats["entry_types"][entry_type]["successful"] += 1  # type: ignore[operator]
        else:
            self._stats["entry_types"][entry_type]["failed"] += 1  # type: ignore[operator]

        # Update size statistics
        self._stats["sizes"]["total_bytes"] += size  # type: ignore[operator]
        if success:
            self._stats["sizes"]["extracted_bytes"] += size  # type: ignore[operator]

            # Track largest/smallest
            if size > self._stats["sizes"]["largest_entry"]:  # type: ignore[operator]
                self._stats["sizes"]["largest_entry"] = size  # type: ignore[assignment]
                self._stats["sizes"]["largest_entry_name"] = entry_name  # type: ignore[assignment]

            if (  # type: ignore[misc]
                self._stats["sizes"]["smallest_entry"] == 0  # type: ignore[assignment]
                or size < self._stats["sizes"]["smallest_entry"]
            ):
                self._stats["sizes"]["smallest_entry"] = size  # type: ignore[assignment]
                self._stats["sizes"]["smallest_entry_name"] = entry_name  # type: ignore[assignment]

        # Add to current file details
        if self._current_file and self._current_file in self._stats["file_details"]:
            entry_info = {
                "name": entry_name,
                "type": entry_type,
                "size": size,
                "success": success,
                "timestamp": datetime.now().isoformat(),
            }
            self._stats["file_details"][self._current_file]["entries"].append(  # type: ignore[arg-type]
                entry_info
            )

        # Track errors
        if not success:
            self._stats["errors"]["by_type"][entry_type] += 1  # type: ignore[operator]
            self._stats["errors"]["entries"].append(  # type: ignore[attr-defined]
                {
                    "file": self._current_file,
                    "entry": entry_name,
                    "type": entry_type,
                    "timestamp": datetime.now().isoformat(),
                }
            )

    def record_recovery_attempt(
        self, strategy: str, success: bool, recovered_count: int = 0
    ) -> None:
        """Record a recovery attempt.

        Args:
            strategy: Recovery strategy used
            success: Whether recovery was successful
            recovered_count: Number of entries recovered
        """
        # Update recovery statistics
        self._stats["recovery"]["attempts"] += 1  # type: ignore[operator]
        if success:
            self._stats["recovery"]["successful"] += 1  # type: ignore[operator]
            self._stats["recovery"]["total_recovered"] += recovered_count  # type: ignore[operator]

        # Track by strategy
        self._stats["recovery"]["by_strategy"][strategy]["attempts"] += 1  # type: ignore[operator]
        if success:
            self._stats["recovery"]["by_strategy"][strategy]["successful"] += 1  # type: ignore[operator]
            self._stats["recovery"]["by_strategy"][strategy]["recovered"] += (  # type: ignore[operator]
                recovered_count
            )

        # Record attempt details
        attempt_info = {
            "file": self._current_file,
            "strategy": strategy,
            "success": success,
            "recovered_count": recovered_count,
            "timestamp": datetime.now().isoformat(),
        }
        self._stats["recovery"]["history"].append(attempt_info)  # type: ignore[attr-defined]

    def record_error(self, error_type: str, error_msg: str) -> None:
        """Record an error during extraction.

        Args:
            error_type: Type/category of error
            error_msg: Error message
        """
        self._stats["errors"]["total"] += 1  # type: ignore[operator]
        self._stats["errors"]["by_type"][error_type] += 1  # type: ignore[operator]

        error_info = {
            "file": self._current_file,
            "type": error_type,
            "message": error_msg,
            "timestamp": datetime.now().isoformat(),
        }

        # Keep only last 100 errors to avoid memory issues
        if len(self._stats["errors"]["entries"]) >= 100:  # type: ignore[arg-type]
            self._stats["errors"]["entries"].pop(0)  # type: ignore[arg-type]

        self._stats["errors"]["entries"].append(error_info)  # type: ignore[attr-defined]

    def get_statistics(self) -> dict[str, Any]:
        """Get current statistics.

        Returns:
            Dictionary containing all statistics
        """
        # Update timing if still in progress
        if self._overall_start:
            self._stats["timing"]["total_duration"] = time.time() - self._overall_start  # type: ignore[assignment]

        # Calculate success rates
        stats_copy = self._stats.copy()

        # File success rate
        total_files = self._stats["files"]["total"]
        if total_files > 0:  # type: ignore[operator]
            stats_copy["files"]["success_rate"] = (  # type: ignore[arg-type]
                self._stats["files"]["successful"] / total_files * 100  # type: ignore[operator]
            )

        # Entry success rate
        total_entries = self._stats["entries"]["total"]
        if total_entries > 0:  # type: ignore[operator]
            stats_copy["entries"]["success_rate"] = (  # type: ignore[arg-type]
                self._stats["entries"]["successful"] / total_entries * 100  # type: ignore[operator]
            )

        # Recovery success rate
        recovery_attempts = self._stats["recovery"]["attempts"]
        if recovery_attempts > 0:  # type: ignore[operator]
            stats_copy["recovery"]["success_rate"] = (  # type: ignore[arg-type]
                self._stats["recovery"]["successful"] / recovery_attempts * 100  # type: ignore[operator]
            )

        return stats_copy

    def get_summary(self) -> str:
        """Get a human-readable summary of statistics.

        Returns:
            Formatted summary string
        """
        stats = self.get_statistics()

        summary_lines = [
            "Extraction Statistics Summary",
            "=" * 50,
            f"Files: {stats['files']['successful']}/{stats['files']['total']} successful "
            f"({stats['files'].get('success_rate', 0):.1f}%)",
            f"Entries: {stats['entries']['successful']}/{stats['entries']['total']} successful "
            f"({stats['entries'].get('success_rate', 0):.1f}%)",
            f"Total Size: {self._format_bytes(stats['sizes']['total_bytes'])}",
            f"Extracted: {self._format_bytes(stats['sizes']['extracted_bytes'])}",
        ]

        if stats["recovery"]["attempts"] > 0:
            summary_lines.append(
                f"Recovery: {stats['recovery']['successful']}/{stats['recovery']['attempts']} successful "
                f"({stats['recovery'].get('success_rate', 0):.1f}%), "
                f"{stats['recovery']['total_recovered']} entries recovered"
            )

        if stats["errors"]["total"] > 0:
            summary_lines.append(f"Errors: {stats['errors']['total']}")

        if stats["timing"]["total_duration"] > 0:
            summary_lines.append(
                f"Duration: {self._format_duration(stats['timing']['total_duration'])}"
            )

        return "\n".join(summary_lines)

    def _format_bytes(self, size_bytes: int) -> str:
        """Format bytes into human-readable string."""
        for unit in ["B", "KB", "MB", "GB"]:
            if size_bytes < 1024.0:
                return f"{size_bytes:.2f} {unit}"
            size_bytes /= 1024.0  # type: ignore[assignment]
        return f"{size_bytes:.2f} TB"

    def _format_duration(self, seconds: float) -> str:
        """Format duration into human-readable string."""
        if seconds < 60:
            return f"{seconds:.1f}s"
        if seconds < 3600:
            minutes = seconds / 60
            return f"{minutes:.1f}m"
        hours = seconds / 3600
        return f"{hours:.1f}h"
