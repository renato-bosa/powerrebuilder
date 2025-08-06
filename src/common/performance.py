"""Performance monitoring and optimization utilities."""

import logging
import time
from contextlib import contextmanager
from dataclasses import dataclass, field
from typing import Any

import psutil

logger = logging.getLogger(__name__)


@dataclass
class PerformanceMetrics:
    """Performance metrics for operations."""

    operation_name: str
    start_time: float
    end_time: float | None = None
    cpu_usage_start: float = 0.0
    cpu_usage_end: float = 0.0
    memory_usage_start: float = 0.0
    memory_usage_end: float = 0.0
    files_processed: int = 0
    bytes_processed: int = 0
    cache_hits: int = 0
    cache_misses: int = 0
    errors: list[str] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)

    @property
    def duration(self) -> float:
        """Get operation duration in seconds."""
        if self.end_time is None:
            return time.time() - self.start_time
        return self.end_time - self.start_time

    @property
    def throughput_files_per_sec(self) -> float:
        """Get files processed per second."""
        duration = self.duration
        return self.files_processed / duration if duration > 0 else 0.0

    @property
    def throughput_mb_per_sec(self) -> float:
        """Get MB processed per second."""
        duration = self.duration
        mb_processed = self.bytes_processed / (1024 * 1024)
        return mb_processed / duration if duration > 0 else 0.0

    @property
    def cache_hit_rate(self) -> float:
        """Get cache hit rate as percentage."""
        total = self.cache_hits + self.cache_misses
        return (self.cache_hits / total * 100) if total > 0 else 0.0

    def to_dict(self) -> dict[str, Any]:
        """Convert metrics to dictionary."""
        return {
            "operation_name": self.operation_name,
            "duration_seconds": self.duration,
            "cpu_usage_start": self.cpu_usage_start,
            "cpu_usage_end": self.cpu_usage_end,
            "memory_usage_start_mb": self.memory_usage_start,
            "memory_usage_end_mb": self.memory_usage_end,
            "files_processed": self.files_processed,
            "bytes_processed": self.bytes_processed,
            "throughput_files_per_sec": self.throughput_files_per_sec,
            "throughput_mb_per_sec": self.throughput_mb_per_sec,
            "cache_hits": self.cache_hits,
            "cache_misses": self.cache_misses,
            "cache_hit_rate": self.cache_hit_rate,
            "error_count": len(self.errors),
            "metadata": self.metadata,
        }


class PerformanceMonitor:
    """Performance monitoring for pipeline operations."""

    def __init__(self):
        """Initialize performance monitor."""
        self.metrics: dict[str, PerformanceMetrics] = {}
        self.global_start_time = time.time()

    @contextmanager
    def monitor_operation(self, operation_name: str):
        """Context manager for monitoring an operation.

        Args:
            operation_name: Name of the operation being monitored

        Yields:
            PerformanceMetrics object for the operation
        """
        # Start monitoring
        start_time = time.time()
        cpu_start = psutil.cpu_percent(interval=0.1)
        memory_start = psutil.virtual_memory().used / (1024 * 1024)  # MB

        metrics = PerformanceMetrics(
            operation_name=operation_name,
            start_time=start_time,
            cpu_usage_start=cpu_start,
            memory_usage_start=memory_start,
        )

        self.metrics[operation_name] = metrics

        try:
            yield metrics
        except Exception as e:
            metrics.errors.append(str(e))
            raise
        finally:
            # Stop monitoring
            metrics.end_time = time.time()
            metrics.cpu_usage_end = psutil.cpu_percent(interval=0.1)
            metrics.memory_usage_end = psutil.virtual_memory().used / (1024 * 1024)

            logger.info(
                "Operation '%s' completed in %.2f seconds (%.1f files/s, %.1f MB/s)",
                operation_name,
                metrics.duration,
                metrics.throughput_files_per_sec,
                metrics.throughput_mb_per_sec,
            )

    def get_summary(self) -> dict[str, Any]:
        """Get summary of all monitored operations."""
        total_duration = time.time() - self.global_start_time
        total_files = sum(m.files_processed for m in self.metrics.values())
        total_bytes = sum(m.bytes_processed for m in self.metrics.values())
        total_errors = sum(len(m.errors) for m in self.metrics.values())
        total_cache_hits = sum(m.cache_hits for m in self.metrics.values())
        total_cache_misses = sum(m.cache_misses for m in self.metrics.values())

        return {
            "total_duration_seconds": total_duration,
            "total_files_processed": total_files,
            "total_bytes_processed": total_bytes,
            "overall_throughput_files_per_sec": total_files / total_duration
            if total_duration > 0
            else 0,
            "overall_throughput_mb_per_sec": (total_bytes / (1024 * 1024))
            / total_duration
            if total_duration > 0
            else 0,
            "total_errors": total_errors,
            "total_cache_hits": total_cache_hits,
            "total_cache_misses": total_cache_misses,
            "overall_cache_hit_rate": (
                total_cache_hits / (total_cache_hits + total_cache_misses) * 100
            )
            if (total_cache_hits + total_cache_misses) > 0
            else 0,
            "operations": {
                name: metrics.to_dict() for name, metrics in self.metrics.items()
            },
        }

    def log_summary(self):
        """Log performance summary."""
        summary = self.get_summary()

        logger.info("=== Performance Summary ===")
        logger.info("Total duration: %.2f seconds", summary["total_duration_seconds"])
        logger.info("Files processed: %d", summary["total_files_processed"])
        logger.info(
            "Bytes processed: %d (%.1f MB)",
            summary["total_bytes_processed"],
            summary["total_bytes_processed"] / (1024 * 1024),
        )
        logger.info(
            "Overall throughput: %.1f files/s, %.1f MB/s",
            summary["overall_throughput_files_per_sec"],
            summary["overall_throughput_mb_per_sec"],
        )
        logger.info(
            "Cache hit rate: %.1f%% (%d hits, %d misses)",
            summary["overall_cache_hit_rate"],
            summary["total_cache_hits"],
            summary["total_cache_misses"],
        )
        logger.info("Total errors: %d", summary["total_errors"])

        # Log individual operations
        for op_name, op_metrics in summary["operations"].items():
            logger.info(
                "  %s: %.2f seconds, %d files, %.1f%% cache hit rate",
                op_name,
                op_metrics["duration_seconds"],
                op_metrics["files_processed"],
                op_metrics["cache_hit_rate"],
            )


# Global performance monitor instance
_performance_monitor: PerformanceMonitor | None = None


def get_performance_monitor() -> PerformanceMonitor:
    """Get global performance monitor instance."""
    global _performance_monitor
    if _performance_monitor is None:
        _performance_monitor = PerformanceMonitor()
    return _performance_monitor


def reset_performance_monitor():
    """Reset global performance monitor."""
    global _performance_monitor
    _performance_monitor = PerformanceMonitor()


@contextmanager
def monitor_performance(operation_name: str):
    """Convenience function for monitoring performance.

    Args:
        operation_name: Name of the operation

    Yields:
        PerformanceMetrics object
    """
    monitor = get_performance_monitor()
    with monitor.monitor_operation(operation_name) as metrics:
        yield metrics


def log_system_info():
    """Log current system information."""
    try:
        cpu_count = psutil.cpu_count()
        cpu_freq = psutil.cpu_freq()
        memory = psutil.virtual_memory()
        disk = psutil.disk_usage("/")

        logger.info("=== System Information ===")
        logger.info(
            "CPU: %d cores @ %.1f MHz", cpu_count, cpu_freq.current if cpu_freq else 0
        )
        logger.info(
            "Memory: %.1f GB total, %.1f GB available (%.1f%% used)",
            memory.total / (1024**3),
            memory.available / (1024**3),
            memory.percent,
        )
        logger.info(
            "Disk: %.1f GB free / %.1f GB total (%.1f%% used)",
            disk.free / (1024**3),
            disk.total / (1024**3),
            (disk.used / disk.total) * 100,
        )

    except Exception as e:
        logger.warning("Could not get system information: %s", e)
