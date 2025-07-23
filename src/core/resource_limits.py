"""Resource limits and monitoring for safe processing."""

import os
import threading
import time
from collections.abc import Callable
from dataclasses import dataclass
from functools import wraps

import psutil


class ResourceLimitError(Exception):
    """Raised when a resource limit is exceeded."""


@dataclass
class ResourceLimits:
    """Configuration for resource limits."""

    # File size limits
    max_file_size: int = 100 * 1024 * 1024  # 100 MB
    max_total_size: int = 1024 * 1024 * 1024  # 1 GB

    # Memory limits
    max_memory_percent: float = 80.0  # Max 80% of system memory
    max_memory_bytes: int | None = None  # Absolute memory limit

    # Time limits
    max_processing_time: float = 300.0  # 5 minutes per file
    max_total_time: float = 3600.0  # 1 hour total

    # File count limits
    max_file_count: int = 10000  # Maximum files to process
    max_depth: int = 20  # Maximum directory depth

    # Buffer limits
    max_buffer_size: int = 10 * 1024 * 1024  # 10 MB buffer

    def __post_init__(self):
        """Calculate absolute memory limit if not set."""
        if self.max_memory_bytes is None:
            total_memory = psutil.virtual_memory().total
            self.max_memory_bytes = int(total_memory * self.max_memory_percent / 100)


class ResourceMonitor:
    """Monitor resource usage and enforce limits."""

    def __init__(self, limits: ResourceLimits | None = None) -> None:
        """Initialize resource monitor with limits."""
        self.limits = limits or ResourceLimits()
        self.start_time = time.time()
        self.file_count = 0
        self.total_size = 0
        self.process = psutil.Process(os.getpid())
        self._stop_monitoring = threading.Event()
        self._monitor_thread = None

    def start_monitoring(self, callback: Callable[[str], None] | None = None) -> None:
        """Start background resource monitoring."""
        if self._monitor_thread is not None:
            return

        def monitor() -> None:
            while not self._stop_monitoring.is_set():
                try:
                    self.check_memory_usage()
                    self.check_time_limit()
                except ResourceLimitError as e:
                    if callback:
                        callback(str(e))
                    raise
                time.sleep(1)  # Check every second

        self._monitor_thread = threading.Thread(target=monitor, daemon=True)
        self._monitor_thread.start()

    def stop_monitoring(self) -> None:
        """Stop background resource monitoring."""
        if self._monitor_thread is not None:
            self._stop_monitoring.set()
            self._monitor_thread.join(timeout=5)
            self._monitor_thread = None
            self._stop_monitoring.clear()

    def check_file_size(self, size: int, filename: str = "") -> None:
        """Check if a file size is within limits."""
        if size > self.limits.max_file_size:
            raise ResourceLimitError(
                f"File {filename} size ({size:,} bytes) exceeds limit "
                f"({self.limits.max_file_size:,} bytes)"
            )

        if self.total_size + size > self.limits.max_total_size:
            raise ResourceLimitError(
                f"Total size would exceed limit ({self.limits.max_total_size:,} bytes)"
            )

    def check_memory_usage(self) -> None:
        """Check current memory usage against limits."""
        memory_info = self.process.memory_info()
        current_memory = memory_info.rss

        if current_memory > self.limits.max_memory_bytes:
            memory_percent = psutil.virtual_memory().percent
            raise ResourceLimitError(
                f"Memory usage ({current_memory:,} bytes, {memory_percent:.1f}%) "
                f"exceeds limit ({self.limits.max_memory_bytes:,} bytes)"
            )

    def check_time_limit(self) -> None:
        """Check if processing time has been exceeded."""
        elapsed = time.time() - self.start_time
        if elapsed > self.limits.max_total_time:
            raise ResourceLimitError(
                f"Total processing time ({elapsed:.1f}s) exceeds limit "
                f"({self.limits.max_total_time:.1f}s)"
            )

    def check_file_count(self) -> None:
        """Check if file count limit has been reached."""
        if self.file_count >= self.limits.max_file_count:
            raise ResourceLimitError(
                f"File count ({self.file_count}) exceeds limit "
                f"({self.limits.max_file_count})"
            )

    def check_depth(self, depth: int) -> None:
        """Check if directory depth limit has been exceeded."""
        if depth > self.limits.max_depth:
            raise ResourceLimitError(
                f"Directory depth ({depth}) exceeds limit ({self.limits.max_depth})"
            )

    def register_file(self, size: int) -> None:
        """Register a processed file."""
        self.file_count += 1
        self.total_size += size
        self.check_file_count()

    def get_stats(self) -> dict:
        """Get current resource usage statistics."""
        memory_info = self.process.memory_info()
        elapsed = time.time() - self.start_time

        return {
            "file_count": self.file_count,
            "total_size": self.total_size,
            "memory_usage": memory_info.rss,
            "memory_percent": psutil.virtual_memory().percent,
            "elapsed_time": elapsed,
            "cpu_percent": self.process.cpu_percent(),
        }


def with_timeout(timeout: float):
    """Decorator to add timeout to a function."""

    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            result = [None]
            exception = [None]

            def target() -> None:
                try:
                    result[0] = func(*args, **kwargs)
                except Exception as e:
                    exception[0] = e

            thread = threading.Thread(target=target)
            thread.daemon = True
            thread.start()
            thread.join(timeout)

            if thread.is_alive():
                raise ResourceLimitError(
                    f"Function {func.__name__} timed out after {timeout}s"
                )

            if exception[0]:
                raise exception[0]

            return result[0]

        return wrapper

    return decorator


def with_memory_limit(max_memory: int):
    """Decorator to enforce memory limit on a function."""

    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            process = psutil.Process(os.getpid())
            start_memory = process.memory_info().rss

            def check_memory() -> None:
                current_memory = process.memory_info().rss
                if current_memory - start_memory > max_memory:
                    raise ResourceLimitError(
                        f"Function {func.__name__} exceeded memory limit "
                        f"({max_memory:,} bytes)"
                    )

            # Set up periodic memory checking
            stop_event = threading.Event()

            def monitor() -> None:
                while not stop_event.is_set():
                    check_memory()
                    time.sleep(0.1)

            monitor_thread = threading.Thread(target=monitor, daemon=True)
            monitor_thread.start()

            try:
                return func(*args, **kwargs)
            finally:
                stop_event.set()
                monitor_thread.join(timeout=1)

        return wrapper

    return decorator


class RateLimiter:
    """Simple rate limiter for operations."""

    def __init__(self, max_calls: int, period: float) -> None:
        """Initialize rate limiter.

        Args:
            max_calls: Maximum number of calls allowed
            period: Time period in seconds
        """
        self.max_calls = max_calls
        self.period = period
        self.calls = []
        self.lock = threading.Lock()

    def __call__(self, func):
        """Decorator to rate limit a function."""

        @wraps(func)
        def wrapper(*args, **kwargs):
            with self.lock:
                now = time.time()
                # Remove old calls
                self.calls = [t for t in self.calls if now - t < self.period]

                if len(self.calls) >= self.max_calls:
                    sleep_time = self.period - (now - self.calls[0])
                    if sleep_time > 0:
                        time.sleep(sleep_time)
                        # Retry after sleeping
                        now = time.time()
                        self.calls = [t for t in self.calls if now - t < self.period]

                self.calls.append(now)

            return func(*args, **kwargs)

        return wrapper


def safe_read_file(path: str, max_size: int | None = None) -> bytes:
    """Safely read a file with size limits.

    Args:
        path: Path to the file
        max_size: Maximum file size to read

    Returns:
        File contents

    Raises:
        ResourceLimitError: If file is too large
    """
    if max_size is None:
        max_size = ResourceLimits().max_file_size

    # Check file size before reading
    file_size = os.path.getsize(path)
    if file_size > max_size:
        raise ResourceLimitError(
            f"File {path} size ({file_size:,} bytes) exceeds limit ({max_size:,} bytes)"
        )

    with open(path, "rb") as f:
        return f.read()


def chunked_read(path: str, chunk_size: int = 8192, max_size: int | None = None):
    """Read a file in chunks with size limits.

    Args:
        path: Path to the file
        chunk_size: Size of each chunk
        max_size: Maximum total size to read

    Yields:
        File chunks

    Raises:
        ResourceLimitError: If file is too large
    """
    if max_size is None:
        max_size = ResourceLimits().max_file_size

    total_read = 0
    with open(path, "rb") as f:
        while True:
            if total_read >= max_size:
                raise ResourceLimitError(
                    f"File {path} exceeds size limit ({max_size:,} bytes)"
                )

            chunk = f.read(min(chunk_size, max_size - total_read))
            if not chunk:
                break

            total_read += len(chunk)
            yield chunk
