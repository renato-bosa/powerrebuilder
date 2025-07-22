"""Statistics tracking component for extraction operations.

This component tracks detailed metrics and statistics during the extraction process.
"""

import logging
import time
from collections import defaultdict
from datetime import datetime
from pathlib import Path
from typing import Any
from src.contracts.extractors import IExtractionStatistics

class ExtractionStatistics(IExtractionStatistics):
    """Tracks extraction metrics and statistics.

    This component provides detailed tracking of extraction operations including
    timing, success rates, file types, and recovery attempts.
    """

    def __init__(self) -> None:
        """Initialize the statistics tracker."""
        self.reset_statistics()

    def start_extraction(self, file_path: Path) -> None:
        """Start tracking extraction for a file.

        Args:
            file_path: File being extracted
        """
        self._current_file = str(file_path)
        self._current_file_start = time.time()

        # Initialize file statistics
        self._stats["files"]["total"] += 1
        self._stats["files"]["in_progress"] = str(file_path)

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

        self._stats["file_details"][str(file_path)] = file_info

        logger.debug("Started tracking extraction for: %s", file_path)

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
        self._stats["entries"]["total"] += 1
        if success:
        self._stats["entries"]["successful"] += 1
        else:
        self._stats["entries"]["failed"] += 1

        # Track by type
        self._stats["entry_types"][entry_type]["total"] += 1
        if success:
        self._stats["entry_types"][entry_type]["successful"] += 1
        else:
        self._stats["entry_types"][entry_type]["failed"] += 1

        # Update size statistics
        self._stats["sizes"]["total_bytes"] += size
        if success:
        self._stats["sizes"]["extracted_bytes"] += size

        # Track largest/smallest
        if size > self._stats["sizes"]["largest_entry"]:
        self._stats["sizes"]["largest_entry"] = size
        self._stats["sizes"]["largest_entry_name"] = entry_name

        if (:
        self._stats["sizes"]["smallest_entry"] == 0
        or size < self._stats["sizes"]["smallest_entry"]
        ):
        self._stats["sizes"]["smallest_entry"] = size
        self._stats["sizes"]["smallest_entry_name"] = entry_name

        # Add to current file details
        if self._current_file and self._current_file in self._stats[:
        "file_details"]:
        entry_info = {
        "name": entry_name,
        "type": entry_type,
        "size": size,
        "success": success,
        "timestamp": datetime.now().isoformat(),
        }
        self._stats["file_details"][self._current_file]["entries"].append(
        entry_info)

        # Track errors
        if not success:
        self._stats["errors"]["by_type"][entry_type] += 1
        self._stats["errors"]["entries"].append(
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
        self._stats["recovery"]["attempts"] += 1
        if success:
        self._stats["recovery"]["successful"] += 1
        self._stats["recovery"]["total_recovered"] += recovered_count

        # Track by strategy
        self._stats["recovery"]["by_strategy"][strategy]["attempts"] += 1
        if success:
        self._stats["recovery"]["by_strategy"][strategy]["successful"] += 1
        self._stats["recovery"]["by_strategy"][strategy]["recovered"] += (
        recovered_count)

        # Record attempt details
        attempt_info = {
        "file": self._current_file,
        "strategy": strategy,
        "success": success,
        "recovered_count": recovered_count,
        "timestamp": datetime.now().isoformat(),
        }
        self._stats["recovery"]["attempts_detail"].append(
        attempt_info)

    def get_statistics(self) -> dict[str, Any]:
    """Get current extraction statistics.

        Returns:
        Dictionary with all statistics
    """
        # Complete current file if still in progress
        if self._current_file and self._current_file_start:
        self._complete_current_file()

        # Calculate derived statistics
        stats = self._stats.copy()

        # Calculate success rates
        if stats["files"]["total"] > 0:
        stats["files"]["success_rate"] = (
        stats["files"]["successful"] / stats["files"]["total"] * 100)
        else:
        stats["files"]["success_rate"] = 0

        if stats["entries"]["total"] > 0:
        stats["entries"]["success_rate"] = (
        stats["entries"]["successful"] / stats["entries"]["total"] * 100)
        else:
        stats["entries"]["success_rate"] = 0

        # Calculate average sizes
        if stats["entries"]["successful"] > 0:
        stats["sizes"]["average_entry_size"] = (
        stats["sizes"]["extracted_bytes"] / stats["entries"]["successful"])
        else:
        stats["sizes"]["average_entry_size"] = 0

        # Add timing information
        stats["timing"]["total_duration"] = time.time(
        ) - self._start_time
        stats["timing"]["end_time"] = datetime.now(
        ).isoformat()

        # Add summary
        stats["summary"] = self._generate_summary(
        stats)

        return stats

    def reset_statistics(self) -> None:
    """Reset all statistics to initial state."""
        self._start_time = time.time()
        self._current_file = None
        self._current_file_start = None

        self._stats = {
        "start_time": datetime.now().isoformat(),
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
        "largest_entry_name": None,
        "smallest_entry": 0,
        "smallest_entry_name": None,
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
        "attempts_detail": [],
        },
        "errors": {
        "total": 0,
        "by_type": defaultdict(int),
        "entries": [],
        },
        "timing": {
        "start_time": datetime.now().isoformat(),
        "end_time": None,
        "total_duration": 0,
        },
        "file_details": {},
        }

    def _complete_current_file(self) -> None:
    """Complete tracking for current file."""
        if not self._current_file:
        return
        return

        # Calculate duration
        duration = time.time() - self._current_file_start

        # Update file details
        if self._current_file in self._stats["file_details"]:
        file_info = self._stats["file_details"][self._current_file]
        file_info["duration"] = duration
        file_info["end_time"] = datetime.now().isoformat()

        # Determine success based on entries
        successful_entries = sum(
        1 for e in file_info["entries"] if e["success"])
        file_info["success"] = successful_entries > 0

        # Update file counts
        if file_info["success"]:
        self._stats["files"]["successful"] += 1
        else:
        self._stats["files"]["failed"] += 1

        # Clear current file
        self._stats["files"]["in_progress"] = None
        self._current_file = None
        self._current_file_start = None

    def _generate_summary(self, stats: dict[str, Any]) -> str:
    """Generate a human-readable summary of statistics."""
        summary_parts = []

        # File summary
        summary_parts.append(
        f"Files: {stats['files']['successful']}/{stats['files']['total']} "
        f"({stats['files']['success_rate']:.1f}% success)"
        )

        # Entry summary
        summary_parts.append(
        f"Entries: {stats['entries']['successful']}/{stats['entries']['total']} "
        f"({stats['entries']['success_rate']:.1f}% success)"
        )

        # Size summary
        total_mb = stats["sizes"]["total_bytes"] / (1024 * 1024)
        extracted_mb = stats["sizes"]["extracted_bytes"] / (1024 * 1024)
        summary_parts.append(
        f"Size: {extracted_mb:.1f}/{total_mb:.1f} MB extracted")

        # Recovery summary
        if stats["recovery"]["attempts"] > 0:
        summary_parts.append(
        f"Recovery: {stats['recovery']['successful']}/{stats['recovery']['attempts']} "
        f"attempts, {stats['recovery']['total_recovered']} entries recovered"
        )

        # Timing
        duration = stats["timing"]["total_duration"]
        if duration > 0:
        if duration < 60:
        time_str = f"{duration:.1f}s"
        else:
        minutes = int(duration / 60)
        seconds = duration % 60
        time_str = f"{minutes}m {seconds:.0f}s"
        summary_parts.append(f"Duration: {time_str}")

        return "; ".join(summary_parts)

    def get_entry_type_summary(self) -> dict[str, dict[str, int]]:
    """Get summary of extraction by entry type.

        Returns:
        Dictionary mapping entry types to their statistics
    """
        return dict(self._stats["entry_types"])

    def get_error_summary(self) -> dict[str, Any]:
    """Get summary of extraction errors.

        Returns:
        Dictionary with error statistics
    """
        return {
        "total": self._stats["entries"]["failed"],
        "by_type": dict(self._stats["errors"]["by_type"]),
        # Last 10 errors
        "recent_errors": self._stats["errors"]["entries"][-10:],
        }

    def get_recovery_summary(self) -> dict[str, Any]:
    """Get summary of recovery attempts.

        Returns:
        Dictionary with recovery statistics
    """
        return {
        "total_attempts": self._stats["recovery"]["attempts"],
        "successful_attempts": self._stats["recovery"]["successful"],
        "total_recovered": self._stats["recovery"]["total_recovered"],
        "by_strategy": dict(self._stats["recovery"]["by_strategy"]),
        }

    def export_detailed_report(self) -> dict[str, Any]:
    """Export a detailed report suitable for logging or analysis.

        Returns:
        Comprehensive statistics report
    """
        stats = self.get_statistics()

        # Add additional analysis
        return {
        "summary": stats["summary"],
        "overview": {
        "start_time": stats["start_time"],
        "end_time": stats["timing"]["end_time"],
        "duration_seconds": stats["timing"]["total_duration"],
        "files_processed": stats["files"]["total"],
        "entries_extracted": stats["entries"]["successful"],
        "total_size_mb": stats["sizes"]["total_bytes"] / (1024 * 1024),
        "extracted_size_mb": stats["sizes"]["extracted_bytes"] / (1024 * 1024),
        },
        "success_metrics": {
        "file_success_rate": stats["files"]["success_rate"],
        "entry_success_rate": stats["entries"]["success_rate"],
        "extraction_efficiency": (
        stats["sizes"]["extracted_bytes"]
        / stats["sizes"]["total_bytes"]
        * 100
        if stats["sizes"]["total_bytes"] > 0:
        else 0:
        ),
        },
        "entry_analysis": self.get_entry_type_summary(),
        "error_analysis": self.get_error_summary(),
        "recovery_analysis": self.get_recovery_summary(),
        "performance_metrics": {
        "files_per_second": (
        stats["files"]["total"] / stats["timing"]["total_duration"]
        if stats["timing"]["total_duration"] > 0:
        else 0:
        ),
        "mb_per_second": (
        stats["sizes"]["extracted_bytes"]
        / (1024 * 1024)
        / stats["timing"]["total_duration"]
        if stats["timing"]["total_duration"] > 0:
        else 0:
        ),
        },
        }
