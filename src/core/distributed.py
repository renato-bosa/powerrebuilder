"""Distributed processing infrastructure for pipeline stages.

This module provides:
- Job queue abstractions
- Worker pool management
- Task distribution and result aggregation
- Multiple backend support (multiprocessing, Celery, Ray)
- Fault tolerance and retry logic
"""

import asyncio
import logging
import multiprocessing as mp
import time
import uuid
from abc import ABC, abstractmethod
from collections.abc import Callable
from concurrent.futures import Future, ProcessPoolExecutor, ThreadPoolExecutor
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import TYPE_CHECKING, Any, Optional, Protocol, TypeVar

from src.core.exceptions import PipelineError

if TYPE_CHECKING:
    from celery import Celery

logger = logging.getLogger(__name__)

T = TypeVar("T")
R = TypeVar("R")


# =============================================================================
# Enums and Data Classes
# =============================================================================


class BackendType(Enum):
    """Available distributed processing backends."""

    MULTIPROCESSING = "multiprocessing"
    THREADING = "threading"
    CELERY = "celery"
    RAY = "ray"
    ASYNCIO = "asyncio"


class JobStatus(Enum):
    """Status of a distributed job."""

    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"
    RETRYING = "retrying"


@dataclass
class JobResult[R]:
    """Result of a distributed job execution."""

    job_id: str
    status: JobStatus
    result: R | None = None
    error: Exception | None = None
    start_time: datetime | None = None
    end_time: datetime | None = None
    retry_count: int = 0
    worker_id: str | None = None

    @property
    def duration(self) -> float | None:
        """Calculate job duration in seconds."""
        if self.start_time and self.end_time:
            return (self.end_time - self.start_time).total_seconds()
        return None

    @property
    def is_success(self) -> bool:
        """Check if job completed successfully."""
        return self.status == JobStatus.COMPLETED and self.error is None


@dataclass
class WorkerConfig:
    """Configuration for worker processes."""

    num_workers: int = mp.cpu_count()
    max_tasks_per_worker: int | None = None
    timeout: float | None = None
    retry_attempts: int = 3
    retry_delay: float = 1.0
    log_level: str = "INFO"
    resource_limits: dict[str, Any] = field(default_factory=dict)


@dataclass
class TaskMetrics:
    """Metrics for task execution."""

    tasks_submitted: int = 0
    tasks_completed: int = 0
    tasks_failed: int = 0
    tasks_retried: int = 0
    total_duration: float = 0.0
    avg_duration: float = 0.0
    min_duration: float | None = None
    max_duration: float | None = None


# =============================================================================
# Protocols and Base Classes
# =============================================================================


class IDistributedBackend(Protocol):
    """Protocol for distributed processing backends."""

    def submit(self, func: Callable[[T], R], *args: T, **kwargs: Any) -> Future[R]:
        """Submit a task for execution."""
        ...

    def map(self, func: Callable[[T], R], items: list[T]) -> list[Future[R]]:
        """Map function over items."""
        ...

    def shutdown(self, wait: bool = True) -> None:
        """Shutdown the backend."""
        ...

    def get_metrics(self) -> TaskMetrics:
        """Get execution metrics."""
        ...


class BaseDistributedBackend(ABC):
    """Base class for distributed processing backends."""

    def __init__(self, config: WorkerConfig) -> None:
        """Initialize backend with configuration."""
        self.config = config
        self.metrics = TaskMetrics()
        self._shutdown = False
        self._workers: dict[str, Any] = {}

    @abstractmethod
    def submit(self, func: Callable[[T], R], *args: T, **kwargs: Any) -> Future[R]:
        """Submit a task for execution."""

    @abstractmethod
    def map(self, func: Callable[[T], R], items: list[T]) -> list[Future[R]]:
        """Map function over items."""

    @abstractmethod
    def shutdown(self, wait: bool = True) -> None:
        """Shutdown the backend."""

    def get_metrics(self) -> TaskMetrics:
        """Get execution metrics."""
        if self.metrics.tasks_completed > 0:
            self.metrics.avg_duration = (
                self.metrics.total_duration / self.metrics.tasks_completed
            )
        return self.metrics

    def _update_metrics(self, result: JobResult) -> None:
        """Update metrics based on job result."""
        if result.is_success:
            self.metrics.tasks_completed += 1
            if result.duration:
                self.metrics.total_duration += result.duration
                if self.metrics.min_duration is None:
                    self.metrics.min_duration = result.duration
                else:
                    self.metrics.min_duration = min(
                        self.metrics.min_duration, result.duration
                    )
                if self.metrics.max_duration is None:
                    self.metrics.max_duration = result.duration
                else:
                    self.metrics.max_duration = max(
                        self.metrics.max_duration, result.duration
                    )
        else:
            self.metrics.tasks_failed += 1

        if result.retry_count > 0:
            self.metrics.tasks_retried += 1


# =============================================================================
# Multiprocessing Backend
# =============================================================================


class MultiprocessingBackend(BaseDistributedBackend):
    """Distributed backend using Python multiprocessing."""

    def __init__(self, config: WorkerConfig) -> None:
        """Initialize multiprocessing backend."""
        super().__init__(config)
        self._executor = ProcessPoolExecutor(
            max_workers=config.num_workers,
            mp_context=mp.get_context("spawn"),
        )
        self._futures: dict[str, Future] = {}
        logger.info(
            "Initialized multiprocessing backend with %d workers", config.num_workers
        )

    def submit(self, func: Callable[[T], R], *args: T, **kwargs: Any) -> Future[R]:
        """Submit a task for execution."""
        if self._shutdown:
            raise PipelineError("Backend is shutdown")

        job_id = str(uuid.uuid4())
        self.metrics.tasks_submitted += 1

        # Wrap function for error handling and retries
        wrapped_func = self._wrap_function(func, job_id)
        future = self._executor.submit(wrapped_func, *args, **kwargs)
        self._futures[job_id] = future

        return future

    def map(self, func: Callable[[T], R], items: list[T]) -> list[Future[R]]:
        """Map function over items."""
        return [self.submit(func, item) for item in items]

    def shutdown(self, wait: bool = True) -> None:
        """Shutdown the backend."""
        self._shutdown = True
        self._executor.shutdown(wait=wait)
        logger.info("Multiprocessing backend shutdown")

    def _wrap_function(
        self, func: Callable[[T], R], job_id: str
    ) -> Callable[[T], JobResult[R]]:
        """Wrap function with error handling and metrics."""

        def wrapper(*args: T, **kwargs: Any) -> R:
            result = JobResult[R](
                job_id=job_id,
                status=JobStatus.RUNNING,
                start_time=datetime.now(),
                worker_id=mp.current_process().name,
            )

            for attempt in range(self.config.retry_attempts):
                try:
                    # Execute function
                    output = func(*args, **kwargs)
                    result.result = output
                    result.status = JobStatus.COMPLETED
                    result.end_time = datetime.now()
                    return output

                except Exception as e:
                    result.error = e
                    result.retry_count = attempt + 1

                    if attempt < self.config.retry_attempts - 1:
                        result.status = JobStatus.RETRYING
                        time.sleep(self.config.retry_delay)
                    else:
                        result.status = JobStatus.FAILED
                        result.end_time = datetime.now()
                        raise

            return result.result  # type: ignore

        return wrapper


# =============================================================================
# Threading Backend
# =============================================================================


class ThreadingBackend(BaseDistributedBackend):
    """Distributed backend using Python threading."""

    def __init__(self, config: WorkerConfig) -> None:
        """Initialize threading backend."""
        super().__init__(config)
        self._executor = ThreadPoolExecutor(max_workers=config.num_workers)
        logger.info("Initialized threading backend with %d workers", config.num_workers)

    def submit(self, func: Callable[[T], R], *args: T, **kwargs: Any) -> Future[R]:
        """Submit a task for execution."""
        if self._shutdown:
            raise PipelineError("Backend is shutdown")

        self.metrics.tasks_submitted += 1
        return self._executor.submit(func, *args, **kwargs)

    def map(self, func: Callable[[T], R], items: list[T]) -> list[Future[R]]:
        """Map function over items."""
        return list(self._executor.map(func, items))

    def shutdown(self, wait: bool = True) -> None:
        """Shutdown the backend."""
        self._shutdown = True
        self._executor.shutdown(wait=wait)
        logger.info("Threading backend shutdown")


# =============================================================================
# Asyncio Backend
# =============================================================================


class AsyncioBackend(BaseDistributedBackend):
    """Distributed backend using Python asyncio."""

    def __init__(self, config: WorkerConfig) -> None:
        """Initialize asyncio backend."""
        super().__init__(config)
        self._loop = asyncio.new_event_loop()
        self._tasks: list[asyncio.Task] = []
        logger.info("Initialized asyncio backend")

    def submit(self, func: Callable[[T], R], *args: T, **kwargs: Any) -> Future[R]:
        """Submit a task for execution."""
        if self._shutdown:
            raise PipelineError("Backend is shutdown")

        self.metrics.tasks_submitted += 1

        # Convert to async if needed
        if asyncio.iscoroutinefunction(func):
            coro = func(*args, **kwargs)
        else:
            coro = self._loop.run_in_executor(None, func, *args, **kwargs)

        # Create future and task
        future = Future()
        task = self._loop.create_task(self._run_async(coro, future))
        self._tasks.append(task)

        return future

    def map(self, func: Callable[[T], R], items: list[T]) -> list[Future[R]]:
        """Map function over items."""
        return [self.submit(func, item) for item in items]

    def shutdown(self, wait: bool = True) -> None:
        """Shutdown the backend."""
        self._shutdown = True
        if wait and self._tasks:
            self._loop.run_until_complete(
                asyncio.gather(*self._tasks, return_exceptions=True)
            )
        self._loop.close()
        logger.info("Asyncio backend shutdown")

    async def _run_async(self, coro: Any, future: Future) -> None:
        """Run async coroutine and set future result."""
        try:
            result = await coro
            future.set_result(result)
        except Exception as e:
            future.set_exception(e)


# =============================================================================
# Celery Backend
# =============================================================================


class CeleryBackend(BaseDistributedBackend):
    """Distributed backend using Celery."""

    def __init__(self, config: WorkerConfig, app: Optional["Celery"] = None) -> None:
        """Initialize Celery backend."""
        super().__init__(config)
        try:
            from celery import Celery

            self.app = app or Celery("powerrebuilder")
            self._configure_celery()
            logger.info("Initialized Celery backend")
        except ImportError:
            raise PipelineError(
                "Celery is not installed. Install with: pip install celery"
            )

    def _configure_celery(self) -> None:
        """Configure Celery app."""
        self.app.conf.update(
            task_serializer="pickle",
            accept_content=["pickle"],
            result_serializer="pickle",
            timezone="UTC",
            enable_utc=True,
        )

    def submit(self, func: Callable[[T], R], *args: T, **kwargs: Any) -> Future[R]:
        """Submit a task for execution."""
        if self._shutdown:
            raise PipelineError("Backend is shutdown")

        self.metrics.tasks_submitted += 1

        # Create Celery task
        @self.app.task(bind=True, max_retries=self.config.retry_attempts)
        def celery_task(self, *task_args, **task_kwargs):
            try:
                return func(*task_args, **task_kwargs)
            except Exception as exc:
                raise self.retry(exc=exc, countdown=int(self.config.retry_delay))

        # Submit task
        result = celery_task.delay(*args, **kwargs)

        # Convert to Future
        future = Future()
        self._monitor_celery_result(result, future)
        return future

    def map(self, func: Callable[[T], R], items: list[T]) -> list[Future[R]]:
        """Map function over items."""
        return [self.submit(func, item) for item in items]

    def shutdown(self, wait: bool = True) -> None:
        """Shutdown the backend."""
        self._shutdown = True
        if wait:
            self.app.control.shutdown()
        logger.info("Celery backend shutdown")

    def _monitor_celery_result(self, celery_result: Any, future: Future) -> None:
        """Monitor Celery result and update Future."""
        import threading

        def monitor() -> None:
            try:
                result = celery_result.get(timeout=self.config.timeout)
                future.set_result(result)
            except Exception as e:
                future.set_exception(e)

        thread = threading.Thread(target=monitor)
        thread.start()


# =============================================================================
# Ray Backend
# =============================================================================


class RayBackend(BaseDistributedBackend):
    """Distributed backend using Ray."""

    def __init__(self, config: WorkerConfig) -> None:
        """Initialize Ray backend."""
        super().__init__(config)
        try:
            import ray

            if not ray.is_initialized():
                ray.init(num_cpus=config.num_workers)
            self.ray = ray
            logger.info("Initialized Ray backend")
        except ImportError:
            raise PipelineError("Ray is not installed. Install with: pip install ray")

    def submit(self, func: Callable[[T], R], *args: T, **kwargs: Any) -> Future[R]:
        """Submit a task for execution."""
        if self._shutdown:
            raise PipelineError("Backend is shutdown")

        self.metrics.tasks_submitted += 1

        # Create Ray remote function
        remote_func = self.ray.remote(func)

        # Submit task
        object_ref = remote_func.remote(*args, **kwargs)

        # Convert to Future
        future = Future()
        self._monitor_ray_result(object_ref, future)
        return future

    def map(self, func: Callable[[T], R], items: list[T]) -> list[Future[R]]:
        """Map function over items."""
        remote_func = self.ray.remote(func)
        object_refs = [remote_func.remote(item) for item in items]

        futures = []
        for ref in object_refs:
            future = Future()
            self._monitor_ray_result(ref, future)
            futures.append(future)

        return futures

    def shutdown(self, wait: bool = True) -> None:
        """Shutdown the backend."""
        self._shutdown = True
        if self.ray.is_initialized():
            self.ray.shutdown()
        logger.info("Ray backend shutdown")

    def _monitor_ray_result(self, object_ref: Any, future: Future) -> None:
        """Monitor Ray result and update Future."""
        import threading

        def monitor() -> None:
            try:
                result = self.ray.get(object_ref, timeout=self.config.timeout)
                future.set_result(result)
            except Exception as e:
                future.set_exception(e)

        thread = threading.Thread(target=monitor)
        thread.start()


# =============================================================================
# Distributed Coordinator
# =============================================================================


class DistributedCoordinator:
    """Coordinator for distributed task execution."""

    def __init__(
        self,
        backend_type: BackendType = BackendType.MULTIPROCESSING,
        config: WorkerConfig | None = None,
    ) -> None:
        """Initialize distributed coordinator."""
        self.backend_type = backend_type
        self.config = config or WorkerConfig()
        self.backend = self._create_backend()
        self._job_registry: dict[str, JobResult] = {}

    def _create_backend(self) -> BaseDistributedBackend:
        """Create backend based on type."""
        if self.backend_type == BackendType.MULTIPROCESSING:
            return MultiprocessingBackend(self.config)
        if self.backend_type == BackendType.THREADING:
            return ThreadingBackend(self.config)
        if self.backend_type == BackendType.ASYNCIO:
            return AsyncioBackend(self.config)
        if self.backend_type == BackendType.CELERY:
            return CeleryBackend(self.config)
        if self.backend_type == BackendType.RAY:
            return RayBackend(self.config)
        raise ValueError(f"Unknown backend type: {self.backend_type}")

    def submit_task(
        self, func: Callable[[T], R], *args: T, **kwargs: Any
    ) -> tuple[str, Future[R]]:
        """Submit a task and return job ID and future."""
        job_id = str(uuid.uuid4())
        future = self.backend.submit(func, *args, **kwargs)

        # Track job
        self._job_registry[job_id] = JobResult(
            job_id=job_id,
            status=JobStatus.PENDING,
            start_time=datetime.now(),
        )

        # Monitor future
        self._monitor_future(job_id, future)

        return job_id, future

    def map_tasks(
        self, func: Callable[[T], R], items: list[T]
    ) -> list[tuple[str, Future[R]]]:
        """Map function over items and return job IDs and futures."""
        results = []
        for item in items:
            job_id, future = self.submit_task(func, item)
            results.append((job_id, future))
        return results

    def get_job_status(self, job_id: str) -> JobResult | None:
        """Get status of a job."""
        return self._job_registry.get(job_id)

    def wait_for_completion(
        self, futures: list[Future], timeout: float | None = None
    ) -> list[Any]:
        """Wait for futures to complete and return results."""
        from concurrent.futures import FIRST_COMPLETED, wait

        results = []
        remaining = set(futures)
        start_time = time.time()

        while remaining:
            if timeout and (time.time() - start_time) > timeout:
                raise TimeoutError("Timeout waiting for tasks to complete")

            done, remaining = wait(remaining, timeout=1.0, return_when=FIRST_COMPLETED)

            for future in done:
                try:
                    result = future.result()
                    results.append(result)
                except Exception as e:
                    logger.error("Task failed: %s", e)
                    results.append(None)

        return results

    def shutdown(self, wait: bool = True) -> None:
        """Shutdown the coordinator."""
        self.backend.shutdown(wait=wait)
        logger.info("Distributed coordinator shutdown")

    def get_metrics(self) -> TaskMetrics:
        """Get execution metrics."""
        return self.backend.get_metrics()

    def _monitor_future(self, job_id: str, future: Future) -> None:
        """Monitor future and update job status."""

        def update_status(fut: Future) -> None:
            job = self._job_registry.get(job_id)
            if not job:
                return

            try:
                result = fut.result()
                job.status = JobStatus.COMPLETED
                job.result = result
                job.end_time = datetime.now()
            except Exception as e:
                job.status = JobStatus.FAILED
                job.error = e
                job.end_time = datetime.now()

        future.add_done_callback(update_status)


# =============================================================================
# Pipeline Integration
# =============================================================================


class DistributedPipelineStage:
    """Distributed execution wrapper for pipeline stages."""

    def __init__(
        self,
        stage_func: Callable,
        backend_type: BackendType = BackendType.MULTIPROCESSING,
        config: WorkerConfig | None = None,
    ) -> None:
        """Initialize distributed pipeline stage."""
        self.stage_func = stage_func
        self.coordinator = DistributedCoordinator(backend_type, config)

    def execute_parallel(
        self, items: list[Any], batch_size: int | None = None
    ) -> list[Any]:
        """Execute stage function on items in parallel."""
        if batch_size:
            # Process in batches
            results = []
            for i in range(0, len(items), batch_size):
                batch = items[i : i + batch_size]
                futures = [
                    self.coordinator.submit_task(self.stage_func, item)[1]
                    for item in batch
                ]
                batch_results = self.coordinator.wait_for_completion(futures)
                results.extend(batch_results)
            return results
        # Process all at once
        futures = [
            self.coordinator.submit_task(self.stage_func, item)[1] for item in items
        ]
        return self.coordinator.wait_for_completion(futures)

    def execute_distributed(
        self, input_dir: Path, output_dir: Path, file_pattern: str = "*.pbl"
    ) -> dict[str, Any]:
        """Execute stage on files in a directory."""
        files = list(input_dir.glob(file_pattern))
        logger.info("Processing %d files with distributed execution", len(files))

        # Process files in parallel
        def process_file(file_path: Path) -> tuple[str, Any]:
            try:
                result = self.stage_func(file_path, output_dir)
                return str(file_path), result
            except Exception as e:
                logger.error("Failed to process %s: %s", file_path, e)
                return str(file_path), {"error": str(e)}

        job_futures = self.coordinator.map_tasks(process_file, files)
        results = self.coordinator.wait_for_completion(
            [future for _, future in job_futures]
        )

        # Aggregate results
        processed_files = {}
        for file_path, result in results:
            if result:
                processed_files[file_path] = result

        metrics = self.coordinator.get_metrics()
        return {
            "processed_files": processed_files,
            "metrics": {
                "total_files": len(files),
                "successful": metrics.tasks_completed,
                "failed": metrics.tasks_failed,
                "avg_duration": metrics.avg_duration,
            },
        }

    def shutdown(self) -> None:
        """Shutdown the distributed stage."""
        self.coordinator.shutdown()


# =============================================================================
# Convenience Functions
# =============================================================================


def create_distributed_backend(
    backend_type: BackendType = BackendType.MULTIPROCESSING,
    num_workers: int | None = None,
) -> BaseDistributedBackend:
    """Create a distributed backend with default configuration."""
    config = WorkerConfig(num_workers=num_workers or mp.cpu_count())

    if backend_type == BackendType.MULTIPROCESSING:
        return MultiprocessingBackend(config)
    if backend_type == BackendType.THREADING:
        return ThreadingBackend(config)
    if backend_type == BackendType.ASYNCIO:
        return AsyncioBackend(config)
    if backend_type == BackendType.CELERY:
        return CeleryBackend(config)
    if backend_type == BackendType.RAY:
        return RayBackend(config)
    raise ValueError(f"Unknown backend type: {backend_type}")


def distribute_work(
    func: Callable[[T], R],
    items: list[T],
    backend_type: BackendType = BackendType.MULTIPROCESSING,
    num_workers: int | None = None,
) -> list[R]:
    """Distribute work across multiple workers."""
    coordinator = DistributedCoordinator(
        backend_type, WorkerConfig(num_workers=num_workers or mp.cpu_count())
    )

    try:
        futures = [coordinator.submit_task(func, item)[1] for item in items]
        return coordinator.wait_for_completion(futures)
    finally:
        coordinator.shutdown()


async def distribute_async(
    func: Callable[[T], R], items: list[T], max_concurrent: int = 10
) -> list[R]:
    """Distribute work using asyncio with concurrency limit."""
    semaphore = asyncio.Semaphore(max_concurrent)

    async def process_item(item: T) -> R:
        async with semaphore:
            if asyncio.iscoroutinefunction(func):
                return await func(item)
            loop = asyncio.get_event_loop()
            return await loop.run_in_executor(None, func, item)

    tasks = [process_item(item) for item in items]
    return await asyncio.gather(*tasks)
