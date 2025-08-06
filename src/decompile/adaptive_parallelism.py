"""Adaptive parallelism engine for PowerBuilder decompilation.

This module provides intelligent parallelism configuration based on:
- System resources (CPU, memory, disk I/O)
- File characteristics (size, type, complexity)
- Historical performance data
- Real-time system monitoring
"""

import logging
import os
import statistics
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import psutil

logger = logging.getLogger(__name__)


@dataclass
class SystemProfile:
    """System capability profile for parallelism optimization."""

    cpu_count: int
    cpu_freq_mhz: float
    memory_total_gb: float
    memory_available_gb: float
    disk_io_speed_mbps: float
    is_ssd: bool
    thermal_throttling: bool = False

    @classmethod
    def detect(cls) -> "SystemProfile":
        """Detect current system capabilities."""
        try:
            # CPU information
            cpu_count = os.cpu_count() or 4
            cpu_freq = psutil.cpu_freq()
            cpu_freq_mhz = cpu_freq.current if cpu_freq else 2000.0

            # Memory information
            memory = psutil.virtual_memory()
            memory_total_gb = memory.total / (1024**3)
            memory_available_gb = memory.available / (1024**3)

            # Disk information (simplified heuristic)
            disk_usage = psutil.disk_usage("/")
            disk_io = psutil.disk_io_counters()

            # Estimate disk speed (rough heuristic)
            if disk_io:
                # Use recent I/O activity as a proxy for speed
                disk_io_speed_mbps = min(
                    100.0, max(10.0, disk_io.read_bytes / 1024 / 1024)
                )
            else:
                disk_io_speed_mbps = 50.0  # Default assumption

            # SSD detection heuristic (not perfect but useful)
            is_ssd = disk_io_speed_mbps > 30.0 or "/dev/nvme" in str(disk_usage)

            return cls(
                cpu_count=cpu_count,
                cpu_freq_mhz=cpu_freq_mhz,
                memory_total_gb=memory_total_gb,
                memory_available_gb=memory_available_gb,
                disk_io_speed_mbps=disk_io_speed_mbps,
                is_ssd=is_ssd,
            )
        except Exception as e:
            logger.warning("Could not detect system profile: %s", e)
            return cls(
                cpu_count=4,
                cpu_freq_mhz=2000.0,
                memory_total_gb=8.0,
                memory_available_gb=4.0,
                disk_io_speed_mbps=50.0,
                is_ssd=False,
            )


@dataclass
class FileCharacteristics:
    """Characteristics of files to be processed."""

    file_count: int
    total_size_mb: float
    avg_file_size_mb: float
    max_file_size_mb: float
    size_distribution: list[float] = field(default_factory=list)
    file_types: dict[str, int] = field(default_factory=dict)

    @classmethod
    def analyze(cls, file_paths: list[Path]) -> "FileCharacteristics":
        """Analyze file characteristics for parallelism optimization."""
        if not file_paths:
            return cls(0, 0.0, 0.0, 0.0)

        # Calculate sizes
        file_sizes = []
        file_types = {}

        for file_path in file_paths:
            try:
                size = file_path.stat().st_size
                file_sizes.append(size)

                # Count file types
                ext = file_path.suffix.lower()
                file_types[ext] = file_types.get(ext, 0) + 1

            except Exception as e:
                logger.warning("Could not analyze file %s: %s", file_path, e)

        if not file_sizes:
            return cls(0, 0.0, 0.0, 0.0)

        # Convert to MB
        file_sizes_mb = [size / (1024 * 1024) for size in file_sizes]

        return cls(
            file_count=len(file_paths),
            total_size_mb=sum(file_sizes_mb),
            avg_file_size_mb=statistics.mean(file_sizes_mb),
            max_file_size_mb=max(file_sizes_mb),
            size_distribution=file_sizes_mb,
            file_types=file_types,
        )


@dataclass
class ParallelismConfig:
    """Configuration for parallel processing."""

    use_parallelism: bool
    use_processes: bool  # True for processes, False for threads
    max_workers: int
    chunk_size: int
    use_memory_mapping: bool
    section_parallelism: bool
    batch_size: int
    io_threads: int
    confidence: float = 0.0  # Confidence in this configuration (0-1)
    reasoning: list[str] = field(default_factory=list)

    def add_reason(self, reason: str) -> None:
        """Add reasoning for this configuration."""
        self.reasoning.append(reason)
        logger.debug("Parallelism reasoning: %s", reason)


class AdaptiveParallelismEngine:
    """Engine for determining optimal parallel processing configuration."""

    def __init__(self):
        """Initialize the adaptive parallelism engine."""
        self.system_profile = SystemProfile.detect()
        self.performance_history: list[dict[str, Any]] = []

        logger.info("Adaptive parallelism engine initialized")
        logger.info(
            "System profile: CPUs=%d, Memory=%.1fGB, SSD=%s",
            self.system_profile.cpu_count,
            self.system_profile.memory_total_gb,
            self.system_profile.is_ssd,
        )

    def optimize_configuration(
        self,
        file_paths: list[Path],
        target_memory_usage_percent: float = 70.0,
        prefer_throughput: bool = True,
    ) -> ParallelismConfig:
        """Optimize parallelism configuration for given files.

        Args:
            file_paths: List of files to be processed
            target_memory_usage_percent: Target memory usage percentage
            prefer_throughput: Whether to prefer throughput over latency

        Returns:
            Optimized parallelism configuration
        """
        logger.info("Optimizing parallelism for %d files", len(file_paths))

        # Analyze file characteristics
        file_chars = FileCharacteristics.analyze(file_paths)

        # Start with base configuration
        config = ParallelismConfig(
            use_parallelism=False,
            use_processes=True,
            max_workers=1,
            chunk_size=1,
            use_memory_mapping=False,
            section_parallelism=False,
            batch_size=1,
            io_threads=1,
        )

        # Determine if parallelism is beneficial
        if self._should_use_parallelism(file_chars):
            config.use_parallelism = True
            config.add_reason("Parallelism beneficial for file characteristics")

            # Determine process vs thread parallelism
            config.use_processes = self._should_use_processes(file_chars)
            if config.use_processes:
                config.add_reason("Process parallelism chosen for CPU-bound tasks")
            else:
                config.add_reason("Thread parallelism chosen for I/O-bound tasks")

            # Calculate optimal worker count
            config.max_workers = self._calculate_optimal_workers(
                file_chars, config.use_processes
            )
            config.add_reason(f"Optimal worker count: {config.max_workers}")

            # Configure memory mapping
            config.use_memory_mapping = self._should_use_memory_mapping(file_chars)
            if config.use_memory_mapping:
                config.add_reason("Memory mapping enabled for large files")

            # Configure section parallelism
            config.section_parallelism = self._should_use_section_parallelism(
                file_chars
            )
            if config.section_parallelism:
                config.add_reason("Section-level parallelism enabled")

            # Calculate chunk size and batch size
            config.chunk_size = self._calculate_chunk_size(
                file_chars, config.max_workers
            )
            config.batch_size = self._calculate_batch_size(
                file_chars, config.max_workers
            )

            # Configure I/O threads
            config.io_threads = self._calculate_io_threads(file_chars)

        else:
            config.add_reason("Sequential processing preferred for small workload")

        # Calculate confidence
        config.confidence = self._calculate_confidence(file_chars, config)

        logger.info(
            "Parallelism configuration: workers=%d, processes=%s, confidence=%.2f",
            config.max_workers,
            config.use_processes,
            config.confidence,
        )

        return config

    def _should_use_parallelism(self, file_chars: FileCharacteristics) -> bool:
        """Determine if parallelism would be beneficial."""
        # Use parallelism if we have multiple files or large files
        if file_chars.file_count >= 4:
            return True

        if file_chars.total_size_mb > 10.0:  # 10MB total
            return True

        if file_chars.max_file_size_mb > 5.0:  # 5MB individual file
            return True

        return False

    def _should_use_processes(self, file_chars: FileCharacteristics) -> bool:
        """Determine if process-based parallelism is better than threads."""
        # Use processes for CPU-intensive tasks
        if file_chars.avg_file_size_mb > 1.0:
            return True

        # Use threads for I/O-bound tasks with many small files
        if file_chars.file_count > 20 and file_chars.avg_file_size_mb < 0.5:
            return False

        # Default to processes for better isolation
        return True

    def _calculate_optimal_workers(
        self, file_chars: FileCharacteristics, use_processes: bool
    ) -> int:
        """Calculate optimal number of workers."""
        cpu_count = self.system_profile.cpu_count
        memory_gb = self.system_profile.memory_available_gb

        if use_processes:
            # Process-based: limited by CPU count and memory
            max_by_cpu = cpu_count
            max_by_memory = max(1, int(memory_gb / 0.5))  # Assume 500MB per process
            workers = min(max_by_cpu, max_by_memory)
        else:
            # Thread-based: can use more workers for I/O
            workers = min(cpu_count * 2, 16)  # Up to 2x CPU count, max 16

        # Adjust based on file count
        workers = min(workers, file_chars.file_count)

        # Adjust based on file sizes
        if file_chars.avg_file_size_mb > 5.0:
            # Large files - fewer workers to avoid memory pressure
            workers = min(workers, max(2, cpu_count // 2))

        return max(1, workers)

    def _should_use_memory_mapping(self, file_chars: FileCharacteristics) -> bool:
        """Determine if memory mapping should be used."""
        # Use memory mapping for large files on systems with sufficient memory
        if (
            file_chars.max_file_size_mb > 2.0
            and self.system_profile.memory_available_gb > 2.0
        ):
            return True

        # Use memory mapping if total workload is large
        if (
            file_chars.total_size_mb > 20.0
            and self.system_profile.memory_available_gb > 4.0
        ):
            return True

        return False

    def _should_use_section_parallelism(self, file_chars: FileCharacteristics) -> bool:
        """Determine if section-level parallelism should be used."""
        # Use section parallelism for large individual files
        if file_chars.max_file_size_mb > 1.0:
            return True

        # Use section parallelism if we have multiple CPU cores available
        if self.system_profile.cpu_count >= 4 and file_chars.avg_file_size_mb > 0.5:
            return True

        return False

    def _calculate_chunk_size(
        self, file_chars: FileCharacteristics, max_workers: int
    ) -> int:
        """Calculate optimal chunk size for processing."""
        # Base chunk size on file count and worker count
        if file_chars.file_count < max_workers * 2:
            return 1  # Process files individually

        # For many files, use larger chunks to reduce overhead
        chunk_size = max(1, file_chars.file_count // (max_workers * 3))
        return min(chunk_size, 10)  # Cap at 10 files per chunk

    def _calculate_batch_size(
        self, file_chars: FileCharacteristics, max_workers: int
    ) -> int:
        """Calculate optimal batch size for processing."""
        # Batch size for grouping operations
        if file_chars.file_count < 10:
            return file_chars.file_count

        return max(5, file_chars.file_count // max_workers)

    def _calculate_io_threads(self, file_chars: FileCharacteristics) -> int:
        """Calculate optimal number of I/O threads."""
        # More I/O threads for many small files
        if file_chars.file_count > 50 and file_chars.avg_file_size_mb < 0.1:
            return min(8, self.system_profile.cpu_count)

        # Fewer I/O threads for large files
        if file_chars.avg_file_size_mb > 5.0:
            return 2

        return min(4, max(2, self.system_profile.cpu_count // 2))

    def _calculate_confidence(
        self, file_chars: FileCharacteristics, config: ParallelismConfig
    ) -> float:
        """Calculate confidence in the configuration."""
        confidence = 0.5  # Base confidence

        # Increase confidence based on clear indicators
        if file_chars.file_count > 10:
            confidence += 0.2

        if file_chars.total_size_mb > 50:
            confidence += 0.2

        if self.system_profile.cpu_count >= 4:
            confidence += 0.1

        # Decrease confidence for edge cases
        if file_chars.file_count == 1:
            confidence -= 0.2

        if self.system_profile.memory_available_gb < 2.0:
            confidence -= 0.1

        return max(0.0, min(1.0, confidence))

    def record_performance(
        self, config: ParallelismConfig, results: dict[str, Any]
    ) -> None:
        """Record performance results for learning."""
        performance_record = {
            "config": {
                "use_processes": config.use_processes,
                "max_workers": config.max_workers,
                "chunk_size": config.chunk_size,
                "use_memory_mapping": config.use_memory_mapping,
            },
            "results": results,
            "timestamp": psutil.boot_time(),  # Simple timestamp
        }

        self.performance_history.append(performance_record)

        # Keep only recent history
        if len(self.performance_history) > 100:
            self.performance_history = self.performance_history[-50:]

        logger.debug(
            "Recorded performance data: %d records in history",
            len(self.performance_history),
        )

    def get_recommended_config_summary(self, config: ParallelismConfig) -> str:
        """Get a human-readable summary of the recommended configuration."""
        summary_parts = []

        if config.use_parallelism:
            parallelism_type = "processes" if config.use_processes else "threads"
            summary_parts.append(
                f"Parallel processing with {config.max_workers} {parallelism_type}"
            )

            if config.use_memory_mapping:
                summary_parts.append("memory mapping enabled")

            if config.section_parallelism:
                summary_parts.append("section-level parallelism")

            summary_parts.append(f"confidence: {config.confidence:.0%}")
        else:
            summary_parts.append("Sequential processing recommended")

        return "; ".join(summary_parts)


# Global instance for convenience
_adaptive_engine: AdaptiveParallelismEngine | None = None


def get_adaptive_engine() -> AdaptiveParallelismEngine:
    """Get the global adaptive parallelism engine instance."""
    global _adaptive_engine
    if _adaptive_engine is None:
        _adaptive_engine = AdaptiveParallelismEngine()
    return _adaptive_engine


def optimize_for_files(
    file_paths: list[Path],
    prefer_throughput: bool = True,
) -> ParallelismConfig:
    """Convenience function to optimize configuration for files."""
    engine = get_adaptive_engine()
    return engine.optimize_configuration(
        file_paths, prefer_throughput=prefer_throughput
    )
