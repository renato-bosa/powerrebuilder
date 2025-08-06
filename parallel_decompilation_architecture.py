"""Parallel decompilation architecture for PowerRebuilder.

This module implements a high-performance parallel processing system that can
utilize multiple CPU cores and handle I/O-bound operations efficiently.
"""

import asyncio
import logging
import multiprocessing as mp
import time
from concurrent.futures import ProcessPoolExecutor, ThreadPoolExecutor, as_completed
from dataclasses import dataclass, field
from pathlib import Path
from queue import Queue
from threading import Lock, Thread
from typing import Any, Callable, Dict, List, Optional, Tuple

logger = logging.getLogger(__name__)


@dataclass
class ProcessingTask:
    """Represents a single file processing task."""
    file_path: Path
    output_dir: Path
    task_id: str
    priority: int = 1  # Higher = more priority
    estimated_size: int = 0
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass  
class ProcessingResult:
    """Result of processing a single task."""
    task_id: str
    file_path: Path
    success: bool
    processing_time: float
    output_files: List[Path] = field(default_factory=list)
    error_message: Optional[str] = None
    metrics: Dict[str, Any] = field(default_factory=dict)


class AdaptiveWorkerPool:
    """Adaptive worker pool that adjusts based on system load and task characteristics."""
    
    def __init__(self, 
                 min_workers: int = 2,
                 max_workers: Optional[int] = None,
                 cpu_threshold: float = 80.0,
                 memory_threshold: float = 85.0):
        """Initialize adaptive worker pool.
        
        Args:
            min_workers: Minimum number of workers to maintain
            max_workers: Maximum workers (defaults to CPU count)
            cpu_threshold: CPU usage % threshold for scaling decisions
            memory_threshold: Memory usage % threshold for scaling decisions
        """
        self.min_workers = min_workers
        self.max_workers = max_workers or mp.cpu_count()
        self.cpu_threshold = cpu_threshold
        self.memory_threshold = memory_threshold
        
        self.current_workers = min_workers
        self.task_queue: Queue[ProcessingTask] = Queue()
        self.result_queue: Queue[ProcessingResult] = Queue()
        
        # Worker pools for different task types
        self.cpu_pool: Optional[ProcessPoolExecutor] = None
        self.io_pool: Optional[ThreadPoolExecutor] = None
        
        # Performance tracking
        self.completed_tasks = 0
        self.total_processing_time = 0.0
        self.task_throughput_history: List[float] = []
        
        self._lock = Lock()
        self._shutdown = False
        
    def start(self):
        """Start the worker pool."""
        logger.info(f"Starting adaptive worker pool: {self.min_workers}-{self.max_workers} workers")
        
        # Create initial worker pools
        self.cpu_pool = ProcessPoolExecutor(max_workers=self.current_workers)
        self.io_pool = ThreadPoolExecutor(max_workers=self.current_workers * 2)  # More I/O threads
        
        # Start monitoring thread
        monitor_thread = Thread(target=self._monitor_performance, daemon=True)
        monitor_thread.start()
        
    def shutdown(self):
        """Shutdown the worker pool."""
        self._shutdown = True
        
        if self.cpu_pool:
            self.cpu_pool.shutdown(wait=True)
        if self.io_pool:
            self.io_pool.shutdown(wait=True)
            
        logger.info("Worker pool shut down")
        
    def submit_task(self, task: ProcessingTask) -> None:
        """Submit a task for processing."""
        self.task_queue.put(task)
        
    def process_batch(self, 
                     tasks: List[ProcessingTask],
                     processor_func: Callable[[ProcessingTask], ProcessingResult],
                     progress_callback: Optional[Callable] = None) -> List[ProcessingResult]:
        """Process a batch of tasks in parallel.
        
        Args:
            tasks: List of tasks to process
            processor_func: Function to process each task
            progress_callback: Optional progress callback
            
        Returns:
            List of processing results
        """
        logger.info(f"Processing batch of {len(tasks)} tasks")
        start_time = time.time()
        
        # Sort tasks by priority and estimated size (largest first for better load balancing)
        sorted_tasks = sorted(tasks, 
                            key=lambda t: (-t.priority, -t.estimated_size))
        
        results: List[ProcessingResult] = []
        completed = 0
        
        # Determine optimal batch size based on task characteristics
        batch_size = self._calculate_optimal_batch_size(tasks)
        
        # Process tasks in batches to avoid overwhelming the system
        for batch_start in range(0, len(sorted_tasks), batch_size):
            batch_end = min(batch_start + batch_size, len(sorted_tasks))
            batch_tasks = sorted_tasks[batch_start:batch_end]
            
            # Submit batch to appropriate executor
            futures = []
            for task in batch_tasks:
                if self._is_cpu_intensive_task(task):
                    future = self.cpu_pool.submit(processor_func, task)
                else:
                    future = self.io_pool.submit(processor_func, task)
                futures.append((future, task))
            
            # Collect results as they complete
            for future, task in as_completed([(f, t) for f, t in futures]):
                try:
                    result = future.result(timeout=300)  # 5 minute timeout per task
                    results.append(result)
                    completed += 1
                    
                    # Update metrics
                    with self._lock:
                        self.completed_tasks += 1
                        self.total_processing_time += result.processing_time
                    
                    # Progress callback
                    if progress_callback:
                        progress_callback(completed, len(tasks), task.file_path.name)
                        
                    logger.debug(f"Completed task {task.task_id} in {result.processing_time:.2f}s")
                    
                except Exception as e:
                    logger.error(f"Task {task.task_id} failed: {e}")
                    error_result = ProcessingResult(
                        task_id=task.task_id,
                        file_path=task.file_path,
                        success=False,
                        processing_time=0.0,
                        error_message=str(e)
                    )
                    results.append(error_result)
                    completed += 1
                    
                    if progress_callback:
                        progress_callback(completed, len(tasks), f"FAILED: {task.file_path.name}")
        
        total_time = time.time() - start_time
        throughput = len(tasks) / total_time if total_time > 0 else 0
        
        logger.info(f"Batch completed: {len(results)} tasks in {total_time:.2f}s "
                   f"({throughput:.2f} tasks/sec)")
        
        return results
        
    def _calculate_optimal_batch_size(self, tasks: List[ProcessingTask]) -> int:
        """Calculate optimal batch size based on task characteristics."""
        # Consider available memory and task sizes
        avg_task_size = sum(t.estimated_size for t in tasks) / len(tasks) if tasks else 0
        available_memory = self._get_available_memory_mb()
        
        # Estimate memory per task (rough heuristic)
        estimated_memory_per_task = max(avg_task_size / 1024 / 1024 * 2, 50)  # At least 50MB per task
        
        # Calculate how many tasks we can handle simultaneously
        max_concurrent_tasks = int(available_memory * 0.7 / estimated_memory_per_task)
        max_concurrent_tasks = max(2, min(max_concurrent_tasks, len(tasks)))
        
        # Don't exceed worker count
        return min(max_concurrent_tasks, self.current_workers * 2)
        
    def _is_cpu_intensive_task(self, task: ProcessingTask) -> bool:
        """Determine if task is CPU-intensive vs I/O-intensive."""
        # Heuristic: larger files are typically more CPU intensive to decompile
        # Small files are often I/O bound due to filesystem overhead
        return task.estimated_size > 100 * 1024  # Files > 100KB
        
    def _monitor_performance(self):
        """Monitor system performance and adjust worker count."""
        while not self._shutdown:
            try:
                cpu_percent = self._get_cpu_usage()
                memory_percent = self._get_memory_usage()
                
                # Calculate recent throughput
                with self._lock:
                    if self.completed_tasks > 0:
                        avg_throughput = self.completed_tasks / max(self.total_processing_time, 1)
                        self.task_throughput_history.append(avg_throughput)
                        
                        # Keep only recent history
                        if len(self.task_throughput_history) > 10:
                            self.task_throughput_history.pop(0)
                
                # Adaptive scaling decisions
                should_scale_up = (
                    cpu_percent < self.cpu_threshold and 
                    memory_percent < self.memory_threshold and
                    self.current_workers < self.max_workers and
                    self._is_throughput_increasing()
                )
                
                should_scale_down = (
                    (cpu_percent > self.cpu_threshold or memory_percent > self.memory_threshold) and
                    self.current_workers > self.min_workers
                )
                
                if should_scale_up:
                    self._scale_up()
                elif should_scale_down:
                    self._scale_down()
                    
                time.sleep(30)  # Check every 30 seconds
                
            except Exception as e:
                logger.warning(f"Performance monitoring error: {e}")
                time.sleep(60)  # Back off on errors
                
    def _scale_up(self):
        """Increase worker count."""
        new_worker_count = min(self.current_workers + 1, self.max_workers)
        if new_worker_count > self.current_workers:
            logger.info(f"Scaling up workers: {self.current_workers} -> {new_worker_count}")
            self.current_workers = new_worker_count
            
            # Recreate pools with new worker count
            self._recreate_pools()
            
    def _scale_down(self):
        """Decrease worker count."""
        new_worker_count = max(self.current_workers - 1, self.min_workers)
        if new_worker_count < self.current_workers:
            logger.info(f"Scaling down workers: {self.current_workers} -> {new_worker_count}")
            self.current_workers = new_worker_count
            
            # Recreate pools with new worker count
            self._recreate_pools()
            
    def _recreate_pools(self):
        """Recreate worker pools with new worker count."""
        # This is a simplified approach - in production, you'd want to gracefully
        # migrate existing tasks to avoid interruption
        old_cpu_pool = self.cpu_pool
        old_io_pool = self.io_pool
        
        self.cpu_pool = ProcessPoolExecutor(max_workers=self.current_workers)
        self.io_pool = ThreadPoolExecutor(max_workers=self.current_workers * 2)
        
        # Shutdown old pools in background
        if old_cpu_pool:
            Thread(target=old_cpu_pool.shutdown, kwargs={'wait': True}, daemon=True).start()
        if old_io_pool:
            Thread(target=old_io_pool.shutdown, kwargs={'wait': True}, daemon=True).start()
            
    def _is_throughput_increasing(self) -> bool:
        """Check if throughput is increasing (indicating we could handle more work)."""
        if len(self.task_throughput_history) < 3:
            return True  # Not enough data, assume we can scale
            
        recent_throughput = sum(self.task_throughput_history[-3:]) / 3
        older_throughput = sum(self.task_throughput_history[-6:-3]) / 3 if len(self.task_throughput_history) >= 6 else recent_throughput
        
        return recent_throughput > older_throughput * 1.1  # 10% improvement threshold
        
    def _get_cpu_usage(self) -> float:
        """Get current CPU usage percentage."""
        try:
            import psutil
            return psutil.cpu_percent(interval=1)
        except ImportError:
            return 50.0  # Conservative estimate if psutil not available
            
    def _get_memory_usage(self) -> float:
        """Get current memory usage percentage."""
        try:
            import psutil
            return psutil.virtual_memory().percent
        except ImportError:
            return 50.0  # Conservative estimate
            
    def _get_available_memory_mb(self) -> float:
        """Get available memory in MB."""
        try:
            import psutil
            return psutil.virtual_memory().available / 1024 / 1024
        except ImportError:
            return 4096.0  # Assume 4GB available
            
    def get_stats(self) -> Dict[str, Any]:
        """Get current pool statistics."""
        with self._lock:
            avg_processing_time = (
                self.total_processing_time / self.completed_tasks 
                if self.completed_tasks > 0 else 0
            )
            
            return {
                'current_workers': self.current_workers,
                'min_workers': self.min_workers,
                'max_workers': self.max_workers,
                'completed_tasks': self.completed_tasks,
                'avg_processing_time': avg_processing_time,
                'total_processing_time': self.total_processing_time,
                'cpu_usage': self._get_cpu_usage(),
                'memory_usage': self._get_memory_usage(),
            }


class ParallelDecompileCoordinator:
    """High-level coordinator for parallel decompilation."""
    
    def __init__(self, 
                 input_dir: Path,
                 output_dir: Path,
                 max_workers: Optional[int] = None,
                 use_adaptive_parallelism: bool = True):
        """Initialize parallel coordinator.
        
        Args:
            input_dir: Directory containing P-code files to decompile
            output_dir: Directory to write decompiled output
            max_workers: Maximum worker processes (None = auto-detect)
            use_adaptive_parallelism: Whether to use adaptive worker scaling
        """
        self.input_dir = Path(input_dir)
        self.output_dir = Path(output_dir)
        
        # Create worker pool
        if use_adaptive_parallelism:
            self.worker_pool = AdaptiveWorkerPool(
                min_workers=2,
                max_workers=max_workers or mp.cpu_count()
            )
        else:
            # Simple fixed-size pool fallback
            self.worker_pool = None
            self.max_workers = max_workers or mp.cpu_count()
            
        self.stats = {
            'files_processed': 0,
            'files_failed': 0,
            'total_time': 0.0,
            'average_time_per_file': 0.0,
        }
        
    def decompile(self,
                 input_dir: Optional[Path] = None,
                 output_dir: Optional[Path] = None,
                 progress_callback: Optional[Callable] = None) -> Dict[str, Any]:
        """Execute parallel decompilation.
        
        Args:
            input_dir: Override input directory
            output_dir: Override output directory  
            progress_callback: Progress callback function
            
        Returns:
            Decompilation results and statistics
        """
        in_dir = Path(input_dir) if input_dir else self.input_dir
        out_dir = Path(output_dir) if output_dir else self.output_dir
        
        logger.info(f"Starting parallel decompilation: {in_dir} -> {out_dir}")
        start_time = time.time()
        
        # Ensure output directory exists
        out_dir.mkdir(parents=True, exist_ok=True)
        
        # Start worker pool
        if self.worker_pool:
            self.worker_pool.start()
        
        try:
            # Discover and prepare tasks
            tasks = self._discover_tasks(in_dir, out_dir)
            logger.info(f"Found {len(tasks)} files to decompile")
            
            if not tasks:
                return {'status': 'completed', 'message': 'No files to process'}
            
            # Process tasks in parallel
            if self.worker_pool:
                results = self.worker_pool.process_batch(
                    tasks, 
                    self._decompile_single_file,
                    progress_callback
                )
            else:
                # Fallback to simple multiprocessing
                results = self._process_with_simple_multiprocessing(tasks, progress_callback)
            
            # Analyze results
            successful = sum(1 for r in results if r.success)
            failed = len(results) - successful
            total_time = time.time() - start_time
            
            self.stats.update({
                'files_processed': successful,
                'files_failed': failed,
                'total_time': total_time,
                'average_time_per_file': total_time / len(results) if results else 0,
            })
            
            logger.info(f"Parallel decompilation completed: {successful} success, "
                       f"{failed} failed in {total_time:.2f}s")
            
            return {
                'status': 'completed',
                'successful': successful,
                'failed': failed,
                'total_time': total_time,
                'throughput': len(results) / total_time if total_time > 0 else 0,
                'results': results,
                'worker_stats': self.worker_pool.get_stats() if self.worker_pool else {},
            }
            
        finally:
            if self.worker_pool:
                self.worker_pool.shutdown()
                
    def _discover_tasks(self, input_dir: Path, output_dir: Path) -> List[ProcessingTask]:
        """Discover P-code files and create processing tasks."""
        tasks = []
        pcode_extensions = ['.fun', '.men', '.udo', '.win']
        
        for ext in pcode_extensions:
            for pcode_file in input_dir.rglob(f"*{ext}"):
                try:
                    file_size = pcode_file.stat().st_size
                    
                    # Calculate priority based on file size (smaller files first for quick wins)
                    priority = max(1, int(100000 / max(file_size, 1000)))
                    
                    task = ProcessingTask(
                        file_path=pcode_file,
                        output_dir=output_dir,
                        task_id=f"{pcode_file.stem}_{pcode_file.suffix}",
                        priority=priority,
                        estimated_size=file_size,
                        metadata={'extension': ext}
                    )
                    tasks.append(task)
                    
                except OSError as e:
                    logger.warning(f"Could not stat file {pcode_file}: {e}")
                    
        return tasks
        
    def _decompile_single_file(self, task: ProcessingTask) -> ProcessingResult:
        """Decompile a single file (this runs in worker process)."""
        start_time = time.time()
        
        try:
            # Import here to avoid pickling issues with multiprocessing
            from src.decompile.coordinator import ExtractedFileDecompiler
            
            # Create decompiler instance
            decompiler = ExtractedFileDecompiler(
                output_dir=task.output_dir,
                enable_filtering=True,
                output_format="pb"
            )
            
            # Perform decompilation
            success = decompiler.decompile_extracted_file(task.file_path)
            
            processing_time = time.time() - start_time
            
            # Determine output files (simplified for this example)
            output_files = []
            if success:
                # Look for created output files
                stem = task.file_path.stem
                for ext in ['.sru', '.srw', '.srm']:
                    output_file = task.output_dir / f"{stem}{ext}"
                    if output_file.exists():
                        output_files.append(output_file)
            
            return ProcessingResult(
                task_id=task.task_id,
                file_path=task.file_path,
                success=success,
                processing_time=processing_time,
                output_files=output_files,
                metrics={
                    'input_size': task.estimated_size,
                    'output_count': len(output_files)
                }
            )
            
        except Exception as e:
            processing_time = time.time() - start_time
            logger.error(f"Error decompiling {task.file_path}: {e}")
            
            return ProcessingResult(
                task_id=task.task_id,
                file_path=task.file_path,
                success=False,
                processing_time=processing_time,
                error_message=str(e)
            )
            
    def _process_with_simple_multiprocessing(self, 
                                           tasks: List[ProcessingTask],
                                           progress_callback: Optional[Callable] = None) -> List[ProcessingResult]:
        """Fallback processing using simple ProcessPoolExecutor."""
        logger.info(f"Using simple multiprocessing with {self.max_workers} workers")
        
        results = []
        completed = 0
        
        with ProcessPoolExecutor(max_workers=self.max_workers) as executor:
            # Submit all tasks
            futures = {executor.submit(self._decompile_single_file, task): task 
                      for task in tasks}
            
            # Collect results as they complete
            for future in as_completed(futures):
                task = futures[future]
                try:
                    result = future.result(timeout=300)  # 5 minute timeout
                    results.append(result)
                    completed += 1
                    
                    if progress_callback:
                        progress_callback(completed, len(tasks), task.file_path.name)
                        
                except Exception as e:
                    logger.error(f"Task failed: {e}")
                    error_result = ProcessingResult(
                        task_id=task.task_id,
                        file_path=task.file_path,
                        success=False,
                        processing_time=0.0,
                        error_message=str(e)
                    )
                    results.append(error_result)
                    completed += 1
                    
        return results


# Performance demonstration
def demo_parallel_performance():
    """Demonstrate parallel vs sequential performance."""
    print("Parallel Decompilation Performance Demo")
    print("=" * 50)
    
    # This would be used with actual P-code files
    # For demo purposes, we'll show the expected improvements
    
    test_scenarios = [
        (10, "10 small files (~50KB each)"),
        (100, "100 medium files (~500KB each)"), 
        (50, "50 large files (~5MB each)"),
    ]
    
    for file_count, description in test_scenarios:
        print(f"\nScenario: {description}")
        
        # Estimated sequential time (based on current performance)
        avg_time_per_file = 0.5  # seconds
        sequential_time = file_count * avg_time_per_file
        
        # Estimated parallel time with 8 cores
        worker_count = 8
        parallel_time = sequential_time / min(worker_count, file_count) * 1.2  # 20% overhead
        
        speedup = sequential_time / parallel_time
        
        print(f"  Sequential: {sequential_time:.1f}s")
        print(f"  Parallel:   {parallel_time:.1f}s") 
        print(f"  Speedup:    {speedup:.1f}x")
        
    print(f"\nExpected overall improvement: 3-7x faster depending on file count and sizes")


if __name__ == "__main__":
    demo_parallel_performance()