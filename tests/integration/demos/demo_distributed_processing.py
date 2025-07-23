#!/usr/bin/env python3
"""Demo of distributed processing for pipeline stages.

This demonstrates how pipeline stages can be distributed across
multiple workers for parallel processing.
"""

import logging
import multiprocessing as mp
import sys
import time
from pathlib import Path
from typing import Any

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from src.core.distributed import (
    DistributedPipeline,
    DistributedStageProcessor,
    Job,
    JobStatus,
    LocalJobQueue,
    LocalWorkerPool,
    get_task_registry,
    task,
)

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


def demo_basic_job_queue():
    """Demonstrate basic job queue functionality."""
    logger.info("=== Basic Job Queue Demo ===")

    # Create job queue
    job_queue = LocalJobQueue()

    # Submit some jobs
    job_ids = []
    for i in range(5):
        job = Job(
            task_name=f"task_{i}",
            args=(i,),
            kwargs={"value": i * 10},
            priority=i,  # Higher priority for later jobs
        )
        job_id = job_queue.submit(job)
        job_ids.append(job_id)
        logger.info("Submitted job %s", job_id)

    # Get and process jobs
    for _ in range(5):
        job = job_queue.get_job(timeout=1.0)
        if job:
            logger.info(
                "Got job %s: %s (priority=%d)", job.id, job.task_name, job.priority
            )

            # Simulate processing
            time.sleep(0.1)

            # Complete the job
            result = f"Result for {job.task_name}"
            job_queue.complete_job(job.id, result)

    # Check job statuses
    logger.info("\nJob statuses:")
    for job_id in job_ids:
        status = job_queue.get_status(job_id)
        logger.info("  %s: %s", job_id[:8], status.value)


def demo_distributed_tasks():
    """Demonstrate distributed task execution."""
    logger.info("\n=== Distributed Task Execution Demo ===")

    # Get task registry
    registry = get_task_registry()

    # Register some tasks
    @task("process_batch")
    def process_batch(items: list[int]) -> dict[str, Any]:
        """Process a batch of items."""
        process_id = mp.current_process().pid
        logger.info("[PID %d] Processing batch of %d items", process_id, len(items))

        # Simulate processing
        total = sum(items)
        time.sleep(0.5)

        return {
            "count": len(items),
            "sum": total,
            "average": total / len(items) if items else 0,
            "process_id": process_id,
        }

    @task("extract_features")
    def extract_features(data: dict[str, Any]) -> dict[str, Any]:
        """Extract features from data."""
        process_id = mp.current_process().pid
        logger.info("[PID %d] Extracting features", process_id)

        # Simulate feature extraction
        time.sleep(0.3)

        return {
            "features": ["feature1", "feature2", "feature3"],
            "process_id": process_id,
        }

    # Create job queue and worker pool
    job_queue = LocalJobQueue()
    worker_pool = LocalWorkerPool(job_queue, registry)

    # Start workers
    num_workers = 4
    worker_pool.start(num_workers)
    logger.info("Started %d workers", num_workers)

    try:
        # Submit batch processing jobs
        job_ids = []
        data = list(range(100))
        batch_size = 20

        for i in range(0, len(data), batch_size):
            batch = data[i : i + batch_size]
            job = Job(task_name="process_batch", args=(batch,))
            job_id = job_queue.submit(job)
            job_ids.append(job_id)

        logger.info("Submitted %d batch processing jobs", len(job_ids))

        # Wait for completion
        completed = 0
        while completed < len(job_ids):
            time.sleep(0.1)
            for job_id in job_ids:
                status = job_queue.get_status(job_id)
                if status == JobStatus.COMPLETED:
                    completed += 1
                    job_ids.remove(job_id)
                    logger.info("Job %s completed", job_id[:8])

        logger.info("All batch processing completed!")

        # Submit feature extraction jobs
        feature_jobs = []
        for i in range(10):
            job = Job(
                task_name="extract_features", args=({"id": i, "data": f"sample_{i}"},)
            )
            job_id = job_queue.submit(job)
            feature_jobs.append(job_id)

        logger.info("\nSubmitted %d feature extraction jobs", len(feature_jobs))

        # Wait for feature jobs
        time.sleep(2)

    finally:
        # Stop workers
        worker_pool.stop()
        logger.info("Stopped workers")


def demo_pipeline_stages():
    """Demonstrate distributed pipeline stages."""
    logger.info("\n=== Distributed Pipeline Stages Demo ===")

    # Create processor
    processor = DistributedStageProcessor(backend="local")

    # Register pipeline stage tasks
    @processor.task_registry.decorator("stage1_extract")
    def stage1_extract(file_paths: list[Path]) -> list[dict[str, Any]]:
        """Stage 1: Extract data from files."""
        process_id = mp.current_process().pid
        results = []

        for path in file_paths:
            logger.info("[PID %d] Extracting from %s", process_id, path.name)
            time.sleep(0.2)  # Simulate extraction

            results.append(
                {
                    "file": path.name,
                    "size": 1000,  # Mock size
                    "objects": [f"obj_{i}" for i in range(3)],
                }
            )

        return results

    @processor.task_registry.decorator("stage2_transform")
    def stage2_transform(extracted_items: list[dict]) -> list[dict[str, Any]]:
        """Stage 2: Transform extracted data."""
        process_id = mp.current_process().pid
        results = []

        for item in extracted_items:
            logger.info(
                "[PID %d] Transforming %s", process_id, item.get("file", "unknown")
            )
            time.sleep(0.3)  # Simulate transformation

            results.append(
                {
                    "source": item.get("file"),
                    "transformed": True,
                    "object_count": len(item.get("objects", [])),
                }
            )

        return results

    @processor.task_registry.decorator("stage3_generate")
    def stage3_generate(transformed_items: list[dict]) -> list[dict[str, Any]]:
        """Stage 3: Generate output from transformed data."""
        process_id = mp.current_process().pid
        results = []

        for item in transformed_items:
            logger.info(
                "[PID %d] Generating from %s", process_id, item.get("source", "unknown")
            )
            time.sleep(0.1)  # Simulate generation

            results.append(
                {
                    "source": item.get("source"),
                    "output": f"generated_{item.get('source', 'output')}.dart",
                    "lines": 100,  # Mock line count
                }
            )

        return results

    # Create test data
    test_files = [Path(f"test_file_{i}.pbl") for i in range(20)]

    # Create pipeline
    pipeline = DistributedPipeline(
        processor.job_queue, processor.worker_pool, processor.task_registry
    )

    # Start workers
    num_workers = 4
    processor.worker_pool.start(num_workers)

    try:
        # Stage 1: Extract
        logger.info("\n--- Stage 1: Extract ---")
        stage1_jobs = pipeline.submit_stage(
            stage_name="extract",
            items=test_files,
            task_name="stage1_extract",
            batch_size=5,
        )
        logger.info("Submitted %d jobs for extraction", len(stage1_jobs))

        # Wait for stage 1
        stage1_results = pipeline.wait_for_stage(stage1_jobs, timeout=30)
        logger.info("Stage 1 completed: %d jobs", len(stage1_results))

        # For demo, create mock results for next stage
        extracted_data = []
        for _i in range(4):  # 4 batches
            extracted_data.extend(
                [
                    {"file": f"file_{j}.pbl", "objects": ["obj1", "obj2"]}
                    for j in range(5)
                ]
            )

        # Stage 2: Transform
        logger.info("\n--- Stage 2: Transform ---")
        stage2_jobs = pipeline.submit_stage(
            stage_name="transform",
            items=extracted_data,
            task_name="stage2_transform",
            batch_size=8,
        )
        logger.info("Submitted %d jobs for transformation", len(stage2_jobs))

        # Wait for stage 2
        stage2_results = pipeline.wait_for_stage(stage2_jobs, timeout=30)
        logger.info("Stage 2 completed: %d jobs", len(stage2_results))

        # Mock transformed data
        transformed_data = [
            {"source": f"file_{i}.pbl", "transformed": True} for i in range(20)
        ]

        # Stage 3: Generate
        logger.info("\n--- Stage 3: Generate ---")
        stage3_jobs = pipeline.submit_stage(
            stage_name="generate",
            items=transformed_data,
            task_name="stage3_generate",
            batch_size=10,
        )
        logger.info("Submitted %d jobs for generation", len(stage3_jobs))

        # Wait for stage 3
        stage3_results = pipeline.wait_for_stage(stage3_jobs, timeout=30)
        logger.info("Stage 3 completed: %d jobs", len(stage3_results))

        logger.info("\nPipeline completed successfully!")

    finally:
        processor.worker_pool.stop()


def demo_fault_tolerance():
    """Demonstrate fault tolerance and retry logic."""
    logger.info("\n=== Fault Tolerance Demo ===")

    registry = get_task_registry()

    # Counter for simulating failures
    attempt_counter = {}

    @registry.decorator("flaky_task")
    def flaky_task(item_id: int) -> str:
        """Task that fails sometimes."""
        process_id = mp.current_process().pid

        # Track attempts
        if item_id not in attempt_counter:
            attempt_counter[item_id] = 0
        attempt_counter[item_id] += 1

        logger.info(
            "[PID %d] Processing item %d (attempt %d)",
            process_id,
            item_id,
            attempt_counter[item_id],
        )

        # Fail on first two attempts for even items
        if item_id % 2 == 0 and attempt_counter[item_id] < 3:
            raise Exception(f"Simulated failure for item {item_id}")

        return f"Success for item {item_id}"

    # Create job queue with retry support
    job_queue = LocalJobQueue()
    worker_pool = LocalWorkerPool(job_queue, registry)

    # Start workers
    worker_pool.start(2)

    try:
        # Submit jobs with retry enabled
        job_ids = []
        for i in range(10):
            job = Job(
                task_name="flaky_task",
                args=(i,),
                max_retries=3,  # Allow up to 3 retries
            )
            job_id = job_queue.submit(job)
            job_ids.append((job_id, i))

        logger.info("Submitted %d jobs with retry enabled", len(job_ids))

        # Monitor job completion
        time.sleep(5)  # Give time for retries

        # Check final statuses
        logger.info("\nFinal job statuses:")
        for job_id, item_id in job_ids:
            status = job_queue.get_status(job_id)
            logger.info("  Item %d: %s", item_id, status.value)

    finally:
        worker_pool.stop()


def demo_dynamic_scaling():
    """Demonstrate dynamic worker scaling."""
    logger.info("\n=== Dynamic Worker Scaling Demo ===")

    registry = get_task_registry()

    @registry.decorator("cpu_intensive")
    def cpu_intensive(n: int) -> int:
        """CPU intensive task."""
        # Simulate CPU work
        total = 0
        for i in range(n * 1000000):
            total += i
        return total

    job_queue = LocalJobQueue()
    worker_pool = LocalWorkerPool(job_queue, registry)

    # Start with few workers
    initial_workers = 2
    worker_pool.start(initial_workers)
    logger.info("Started with %d workers", initial_workers)

    try:
        # Submit initial batch
        for _i in range(10):
            job = Job(task_name="cpu_intensive", args=(10,))
            job_queue.submit(job)

        logger.info("Submitted 10 jobs")
        time.sleep(2)

        # Scale up workers
        new_workers = 6
        worker_pool.scale(new_workers)
        logger.info("\nScaled up to %d workers", new_workers)

        # Submit more jobs
        for _i in range(20):
            job = Job(task_name="cpu_intensive", args=(5,))
            job_queue.submit(job)

        logger.info("Submitted 20 more jobs")
        time.sleep(3)

        # Scale down workers
        final_workers = 3
        worker_pool.scale(final_workers)
        logger.info("\nScaled down to %d workers", final_workers)

        # Submit final batch
        for _i in range(5):
            job = Job(task_name="cpu_intensive", args=(2,))
            job_queue.submit(job)

        logger.info("Submitted 5 final jobs")
        time.sleep(2)

    finally:
        worker_pool.stop()


def main():
    """Run all distributed processing demos."""
    logger.info("PowerRebuilder Distributed Processing Demo")
    logger.info("=" * 50)

    # Set multiprocessing start method
    mp.set_start_method("spawn", force=True)

    # Demo 1: Basic job queue
    demo_basic_job_queue()

    # Demo 2: Distributed tasks
    demo_distributed_tasks()

    # Demo 3: Pipeline stages
    demo_pipeline_stages()

    # Demo 4: Fault tolerance
    demo_fault_tolerance()

    # Demo 5: Dynamic scaling
    demo_dynamic_scaling()

    logger.info("\n" + "=" * 50)
    logger.info("Demo completed!")
    logger.info("\nKey Benefits of Distributed Processing:")
    logger.info("✓ Parallel execution across multiple workers")
    logger.info("✓ Automatic load balancing")
    logger.info("✓ Fault tolerance with retry logic")
    logger.info("✓ Dynamic scaling based on workload")
    logger.info("✓ Support for multiple backends (local, Celery, Ray)")


if __name__ == "__main__":
    main()
