"""Distributed processing infrastructure for pipeline stages.

This module provides:
- Job queue abstractions
- Worker pool management
- Task distribution and result aggregation
- Multiple backend support (multiprocessing, Celery, Ray)
- Fault tolerance and retry logic
"""

import asyncio
import json
import logging
import multiprocessing as mp
import pickle
import time
import uuid
from abc import ABC, abstractmethod
from concurrent.futures import ProcessPoolExecutor, ThreadPoolExecutor, Future
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Protocol, Tuple, Union

logger = logging.getLogger(__name__)


class JobStatus(Enum):
    """Job execution status."""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"
    RETRYING = "retrying"


@dataclass
class Job:
    """Represents a distributed job."""
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    task_name: str = ""
    args: Tuple[Any, ...] = ()
    kwargs: Dict[str, Any] = field(default_factory=dict)
    status: JobStatus = JobStatus.PENDING
    created_at: datetime = field(default_factory=datetime.utcnow)
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    result: Any = None
    error: Optional[str] = None
    retry_count: int = 0
    max_retries: int = 3
    priority: int = 0  # Higher = more important
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class WorkerInfo:
    """Information about a worker."""
    id: str
    hostname: str
    process_id: int
    status: str
    current_job: Optional[str] = None
    jobs_completed: int = 0
    jobs_failed: int = 0
    started_at: datetime = field(default_factory=datetime.utcnow)
    last_heartbeat: datetime = field(default_factory=datetime.utcnow)


class IJobQueue(Protocol):
    """Interface for job queue implementations."""
    
    def submit(self, job: Job) -> str:
        """Submit a job to the queue."""
        ...
    
    def get_job(self, timeout: Optional[float] = None) -> Optional[Job]:
        """Get next job from queue."""
        ...
    
    def complete_job(self, job_id: str, result: Any) -> None:
        """Mark job as completed with result."""
        ...
    
    def fail_job(self, job_id: str, error: str) -> None:
        """Mark job as failed with error."""
        ...
    
    def get_status(self, job_id: str) -> Optional[JobStatus]:
        """Get job status."""
        ...
    
    def cancel_job(self, job_id: str) -> bool:
        """Cancel a pending job."""
        ...


class IWorkerPool(Protocol):
    """Interface for worker pool implementations."""
    
    def start(self, num_workers: int) -> None:
        """Start worker pool."""
        ...
    
    def stop(self) -> None:
        """Stop worker pool."""
        ...
    
    def scale(self, num_workers: int) -> None:
        """Scale worker pool up or down."""
        ...
    
    def get_workers(self) -> List[WorkerInfo]:
        """Get information about workers."""
        ...


class ITaskRegistry(Protocol):
    """Interface for task registry."""
    
    def register(self, name: str, func: Callable) -> None:
        """Register a task function."""
        ...
    
    def get(self, name: str) -> Optional[Callable]:
        """Get a task function by name."""
        ...
    
    def list_tasks(self) -> List[str]:
        """List all registered tasks."""
        ...


class LocalJobQueue(IJobQueue):
    """Local in-memory job queue implementation."""
    
    def __init__(self, maxsize: int = 10000):
        """Initialize local job queue.
        
        Args:
            maxsize: Maximum queue size
        """
        self._queue = mp.Queue(maxsize=maxsize)
        self._jobs: Dict[str, Job] = {}
        self._lock = mp.Lock()
    
    def submit(self, job: Job) -> str:
        """Submit a job to the queue."""
        with self._lock:
            self._jobs[job.id] = job
            self._queue.put(job.id)
            logger.debug("Submitted job %s: %s", job.id, job.task_name)
        return job.id
    
    def get_job(self, timeout: Optional[float] = None) -> Optional[Job]:
        """Get next job from queue."""
        try:
            job_id = self._queue.get(timeout=timeout)
            with self._lock:
                job = self._jobs.get(job_id)
                if job and job.status == JobStatus.PENDING:
                    job.status = JobStatus.RUNNING
                    job.started_at = datetime.utcnow()
                    return job
        except:
            pass
        return None
    
    def complete_job(self, job_id: str, result: Any) -> None:
        """Mark job as completed with result."""
        with self._lock:
            if job_id in self._jobs:
                job = self._jobs[job_id]
                job.status = JobStatus.COMPLETED
                job.result = result
                job.completed_at = datetime.utcnow()
                logger.debug("Completed job %s", job_id)
    
    def fail_job(self, job_id: str, error: str) -> None:
        """Mark job as failed with error."""
        with self._lock:
            if job_id in self._jobs:
                job = self._jobs[job_id]
                job.error = error
                job.retry_count += 1
                
                if job.retry_count < job.max_retries:
                    job.status = JobStatus.RETRYING
                    self._queue.put(job_id)  # Requeue for retry
                    logger.warning("Retrying job %s (%d/%d)", 
                                 job_id, job.retry_count, job.max_retries)
                else:
                    job.status = JobStatus.FAILED
                    job.completed_at = datetime.utcnow()
                    logger.error("Failed job %s: %s", job_id, error)
    
    def get_status(self, job_id: str) -> Optional[JobStatus]:
        """Get job status."""
        with self._lock:
            job = self._jobs.get(job_id)
            return job.status if job else None
    
    def cancel_job(self, job_id: str) -> bool:
        """Cancel a pending job."""
        with self._lock:
            job = self._jobs.get(job_id)
            if job and job.status == JobStatus.PENDING:
                job.status = JobStatus.CANCELLED
                return True
        return False


class TaskRegistry:
    """Registry for task functions."""
    
    def __init__(self):
        """Initialize task registry."""
        self._tasks: Dict[str, Callable] = {}
        self._lock = mp.Lock()
    
    def register(self, name: str, func: Callable) -> None:
        """Register a task function."""
        with self._lock:
            self._tasks[name] = func
            logger.info("Registered task: %s", name)
    
    def get(self, name: str) -> Optional[Callable]:
        """Get a task function by name."""
        return self._tasks.get(name)
    
    def list_tasks(self) -> List[str]:
        """List all registered tasks."""
        return list(self._tasks.keys())
    
    def decorator(self, name: Optional[str] = None):
        """Decorator for registering tasks."""
        def wrapper(func):
            task_name = name or func.__name__
            self.register(task_name, func)
            return func
        return wrapper


class Worker:
    """Worker process that executes jobs."""
    
    def __init__(
        self,
        worker_id: str,
        job_queue: IJobQueue,
        task_registry: TaskRegistry,
        result_callback: Optional[Callable[[str, Any], None]] = None
    ):
        """Initialize worker.
        
        Args:
            worker_id: Unique worker identifier
            job_queue: Job queue to get jobs from
            task_registry: Registry of task functions
            result_callback: Callback for job results
        """
        self.worker_id = worker_id
        self.job_queue = job_queue
        self.task_registry = task_registry
        self.result_callback = result_callback
        self._running = False
        self._info = WorkerInfo(
            id=worker_id,
            hostname="localhost",
            process_id=mp.current_process().pid,
            status="idle"
        )
    
    def run(self) -> None:
        """Run worker loop."""
        self._running = True
        logger.info("Worker %s started", self.worker_id)
        
        while self._running:
            try:
                # Get next job
                job = self.job_queue.get_job(timeout=1.0)
                if not job:
                    continue
                
                self._info.current_job = job.id
                self._info.status = "busy"
                
                # Execute job
                self._execute_job(job)
                
                self._info.current_job = None
                self._info.status = "idle"
                
            except KeyboardInterrupt:
                break
            except Exception as e:
                logger.error("Worker %s error: %s", self.worker_id, e)
        
        logger.info("Worker %s stopped", self.worker_id)
    
    def stop(self) -> None:
        """Stop worker."""
        self._running = False
    
    def _execute_job(self, job: Job) -> None:
        """Execute a single job."""
        logger.debug("Worker %s executing job %s", self.worker_id, job.id)
        
        try:
            # Get task function
            task_func = self.task_registry.get(job.task_name)
            if not task_func:
                raise ValueError(f"Unknown task: {job.task_name}")
            
            # Execute task
            result = task_func(*job.args, **job.kwargs)
            
            # Mark job as completed
            self.job_queue.complete_job(job.id, result)
            self._info.jobs_completed += 1
            
            # Call result callback if provided
            if self.result_callback:
                self.result_callback(job.id, result)
            
        except Exception as e:
            # Mark job as failed
            error_msg = f"{type(e).__name__}: {str(e)}"
            self.job_queue.fail_job(job.id, error_msg)
            self._info.jobs_failed += 1
            logger.error("Job %s failed: %s", job.id, error_msg)


class LocalWorkerPool:
    """Local process-based worker pool."""
    
    def __init__(
        self,
        job_queue: IJobQueue,
        task_registry: TaskRegistry
    ):
        """Initialize worker pool.
        
        Args:
            job_queue: Job queue for workers
            task_registry: Task registry
        """
        self.job_queue = job_queue
        self.task_registry = task_registry
        self._workers: Dict[str, mp.Process] = {}
        self._worker_info: Dict[str, WorkerInfo] = {}
    
    def start(self, num_workers: int) -> None:
        """Start worker pool."""
        logger.info("Starting worker pool with %d workers", num_workers)
        
        for i in range(num_workers):
            worker_id = f"worker_{i}"
            worker = Worker(
                worker_id=worker_id,
                job_queue=self.job_queue,
                task_registry=self.task_registry
            )
            
            process = mp.Process(target=worker.run, name=worker_id)
            process.start()
            
            self._workers[worker_id] = process
            self._worker_info[worker_id] = worker._info
    
    def stop(self) -> None:
        """Stop worker pool."""
        logger.info("Stopping worker pool")
        
        for worker_id, process in self._workers.items():
            process.terminate()
            process.join(timeout=5)
            if process.is_alive():
                process.kill()
        
        self._workers.clear()
        self._worker_info.clear()
    
    def scale(self, num_workers: int) -> None:
        """Scale worker pool up or down."""
        current = len(self._workers)
        
        if num_workers > current:
            # Scale up
            for i in range(current, num_workers):
                worker_id = f"worker_{i}"
                worker = Worker(
                    worker_id=worker_id,
                    job_queue=self.job_queue,
                    task_registry=self.task_registry
                )
                
                process = mp.Process(target=worker.run, name=worker_id)
                process.start()
                
                self._workers[worker_id] = process
                self._worker_info[worker_id] = worker._info
        
        elif num_workers < current:
            # Scale down
            workers_to_remove = list(self._workers.keys())[num_workers:]
            for worker_id in workers_to_remove:
                process = self._workers[worker_id]
                process.terminate()
                process.join(timeout=5)
                del self._workers[worker_id]
                del self._worker_info[worker_id]
    
    def get_workers(self) -> List[WorkerInfo]:
        """Get information about workers."""
        return list(self._worker_info.values())


class DistributedPipeline:
    """Distributed pipeline coordinator."""
    
    def __init__(
        self,
        job_queue: IJobQueue,
        worker_pool: IWorkerPool,
        task_registry: TaskRegistry
    ):
        """Initialize distributed pipeline.
        
        Args:
            job_queue: Job queue implementation
            worker_pool: Worker pool implementation
            task_registry: Task registry
        """
        self.job_queue = job_queue
        self.worker_pool = worker_pool
        self.task_registry = task_registry
        self._futures: Dict[str, Future] = {}
    
    def submit_stage(
        self,
        stage_name: str,
        items: List[Any],
        task_name: str,
        batch_size: int = 10
    ) -> List[str]:
        """Submit a pipeline stage for distributed processing.
        
        Args:
            stage_name: Name of the pipeline stage
            items: Items to process
            task_name: Registered task name
            batch_size: Items per job
            
        Returns:
            List of job IDs
        """
        job_ids = []
        
        # Create batches
        for i in range(0, len(items), batch_size):
            batch = items[i:i + batch_size]
            
            job = Job(
                task_name=task_name,
                args=(batch,),
                kwargs={"stage": stage_name},
                metadata={
                    "stage": stage_name,
                    "batch_index": i // batch_size,
                    "batch_size": len(batch)
                }
            )
            
            job_id = self.job_queue.submit(job)
            job_ids.append(job_id)
        
        logger.info("Submitted %d jobs for stage %s", len(job_ids), stage_name)
        return job_ids
    
    def wait_for_stage(
        self,
        job_ids: List[str],
        timeout: Optional[float] = None
    ) -> Dict[str, Any]:
        """Wait for stage completion and collect results.
        
        Args:
            job_ids: Job IDs to wait for
            timeout: Maximum wait time
            
        Returns:
            Dictionary of job results
        """
        start_time = time.time()
        results = {}
        
        while job_ids:
            if timeout and (time.time() - start_time) > timeout:
                raise TimeoutError("Stage timeout exceeded")
            
            completed = []
            for job_id in job_ids:
                status = self.job_queue.get_status(job_id)
                
                if status == JobStatus.COMPLETED:
                    # Get result (would need to be implemented)
                    results[job_id] = {"status": "completed"}
                    completed.append(job_id)
                
                elif status == JobStatus.FAILED:
                    results[job_id] = {"status": "failed"}
                    completed.append(job_id)
            
            # Remove completed jobs
            for job_id in completed:
                job_ids.remove(job_id)
            
            if job_ids:
                time.sleep(0.1)
        
        return results
    
    def run_distributed_pipeline(
        self,
        stages: List[Tuple[str, str, List[Any]]],
        num_workers: int = 4
    ) -> Dict[str, Any]:
        """Run a distributed pipeline.
        
        Args:
            stages: List of (stage_name, task_name, items) tuples
            num_workers: Number of workers to use
            
        Returns:
            Pipeline results
        """
        # Start workers
        self.worker_pool.start(num_workers)
        
        try:
            results = {}
            
            for stage_name, task_name, items in stages:
                logger.info("Running stage: %s", stage_name)
                
                # Submit stage
                job_ids = self.submit_stage(
                    stage_name=stage_name,
                    items=items,
                    task_name=task_name
                )
                
                # Wait for completion
                stage_results = self.wait_for_stage(job_ids)
                results[stage_name] = stage_results
                
                logger.info("Stage %s completed", stage_name)
            
            return results
        
        finally:
            # Stop workers
            self.worker_pool.stop()


# Celery backend support
class CeleryJobQueue(IJobQueue):
    """Celery-based job queue implementation."""
    
    def __init__(self, broker_url: str, backend_url: str):
        """Initialize Celery job queue.
        
        Args:
            broker_url: Celery broker URL (e.g., redis://localhost:6379)
            backend_url: Celery result backend URL
        """
        try:
            from celery import Celery
            self.app = Celery('powerrebuilder', broker=broker_url, backend=backend_url)
            self._jobs: Dict[str, Job] = {}
        except ImportError:
            raise ImportError("Celery not installed. Install with: pip install celery")
    
    def submit(self, job: Job) -> str:
        """Submit a job to Celery."""
        # Would implement Celery task submission
        raise NotImplementedError("Celery backend not fully implemented")


# Ray backend support
class RayJobQueue(IJobQueue):
    """Ray-based job queue implementation."""
    
    def __init__(self, address: Optional[str] = None):
        """Initialize Ray job queue.
        
        Args:
            address: Ray cluster address
        """
        try:
            import ray
            ray.init(address=address)
            self._jobs: Dict[str, Job] = {}
        except ImportError:
            raise ImportError("Ray not installed. Install with: pip install ray")
    
    def submit(self, job: Job) -> str:
        """Submit a job to Ray."""
        # Would implement Ray task submission
        raise NotImplementedError("Ray backend not fully implemented")


class DistributedStageProcessor:
    """Processes pipeline stages in distributed manner."""
    
    def __init__(self, backend: str = "local", **kwargs):
        """Initialize distributed processor.
        
        Args:
            backend: Backend to use (local, celery, ray)
            **kwargs: Backend-specific arguments
        """
        self.backend = backend
        self.task_registry = TaskRegistry()
        
        # Create job queue based on backend
        if backend == "local":
            self.job_queue = LocalJobQueue()
            self.worker_pool = LocalWorkerPool(self.job_queue, self.task_registry)
        elif backend == "celery":
            self.job_queue = CeleryJobQueue(
                kwargs.get("broker_url", "redis://localhost:6379"),
                kwargs.get("backend_url", "redis://localhost:6379")
            )
            # Would need Celery worker pool
        elif backend == "ray":
            self.job_queue = RayJobQueue(kwargs.get("address"))
            # Would need Ray worker pool
        else:
            raise ValueError(f"Unknown backend: {backend}")
        
        # Register default tasks
        self._register_default_tasks()
    
    def _register_default_tasks(self):
        """Register default pipeline tasks."""
        
        @self.task_registry.decorator("extract_objects")
        def extract_objects(pbl_paths: List[Path]) -> List[Dict[str, Any]]:
            """Extract objects from PBL files."""
            results = []
            for pbl_path in pbl_paths:
                # Simplified extraction
                results.append({
                    "path": str(pbl_path),
                    "objects": ["obj1", "obj2"]  # Would do real extraction
                })
            return results
        
        @self.task_registry.decorator("decompile_pcode")
        def decompile_pcode(pcode_items: List[Dict]) -> List[Dict[str, Any]]:
            """Decompile P-code objects."""
            results = []
            for item in pcode_items:
                # Simplified decompilation
                results.append({
                    "name": item["name"],
                    "source": "decompiled source"
                })
            return results
        
        @self.task_registry.decorator("parse_source")
        def parse_source(source_items: List[Dict]) -> List[Dict[str, Any]]:
            """Parse source code."""
            results = []
            for item in source_items:
                # Simplified parsing
                results.append({
                    "name": item["name"],
                    "ast": {"type": "parsed"}
                })
            return results
    
    def process_directory_distributed(
        self,
        input_dir: Path,
        output_dir: Path,
        num_workers: int = 4,
        batch_size: int = 10
    ) -> Dict[str, Any]:
        """Process directory with distributed workers.
        
        Args:
            input_dir: Input directory
            output_dir: Output directory
            num_workers: Number of workers
            batch_size: Items per batch
            
        Returns:
            Processing results
        """
        # Find all PBL files
        pbl_files = list(input_dir.glob("*.pbl"))
        
        # Create distributed pipeline
        pipeline = DistributedPipeline(
            self.job_queue,
            self.worker_pool,
            self.task_registry
        )
        
        # Define stages
        stages = [
            ("extract", "extract_objects", pbl_files),
            # Results from previous stage would feed into next
            # ("decompile", "decompile_pcode", extracted_objects),
            # ("parse", "parse_source", decompiled_sources),
        ]
        
        # Run pipeline
        results = pipeline.run_distributed_pipeline(stages, num_workers)
        
        return results


# Singleton instances
_task_registry = TaskRegistry()
_job_queue: Optional[IJobQueue] = None
_worker_pool: Optional[IWorkerPool] = None


def get_task_registry() -> TaskRegistry:
    """Get global task registry."""
    return _task_registry


def get_distributed_processor(backend: str = "local", **kwargs) -> DistributedStageProcessor:
    """Get distributed processor instance."""
    return DistributedStageProcessor(backend, **kwargs)


def task(name: Optional[str] = None):
    """Decorator for registering distributed tasks."""
    return _task_registry.decorator(name)