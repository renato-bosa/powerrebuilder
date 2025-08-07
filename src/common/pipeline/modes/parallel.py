"""Parallel pipeline infrastructure using asyncio."""

import asyncio
import logging
import multiprocessing as mp
import time
from collections.abc import AsyncIterator, Callable
from concurrent.futures import ProcessPoolExecutor, ThreadPoolExecutor
from dataclasses import dataclass, field
from typing import Any, TypeVar

from src.common.pipeline.progress import PipelineProgress
from src.core.exceptions import PipelineError

logger = logging.getLogger(__name__)

T = TypeVar("T")
R = TypeVar("R")


@dataclass
class PipelineMetrics:
    """Metrics for pipeline performance monitoring."""

    items_processed: int = 0
    items_failed: int = 0
    total_time: float = 0.0
    stage_times: dict[str, float] = field(default_factory=dict)
    queue_sizes: dict[str, int] = field(default_factory=dict)


class AsyncQueue:
    """Async queue with backpressure support."""

    def __init__(self, maxsize: int = 0, name: str = "queue") -> None:
        self._queue: asyncio.Queue[Any] = asyncio.Queue(maxsize=maxsize)
        self.name = name
        self._closed = False
        self._waiters: set[asyncio.Task[Any]] = set()

    async def put(self, item: Any) -> None:
        """Put item in queue."""
        if self._closed:
            raise RuntimeError(f"Queue {self.name} is closed")
        await self._queue.put(item)

    async def get(self) -> Any:
        """Get item from queue."""
        if self._closed and self._queue.empty():
            raise StopAsyncIteration
        return await self._queue.get()

    def qsize(self) -> int:
        """Get queue size."""
        return self._queue.qsize()

    def close(self) -> None:
        """Close queue for new items."""
        self._closed = True

    async def join(self) -> None:
        """Wait for all items to be processed."""
        await self._queue.join()

    def task_done(self) -> None:
        """Mark task as done."""
        self._queue.task_done()

    async def __aiter__(self) -> AsyncIterator[Any]:
        """Iterate over queue items."""
        while True:
            try:
                item = await self.get()
                yield item
                self.task_done()
            except StopAsyncIteration:
                break


@dataclass
class StageConfig:
    """Configuration for a pipeline stage."""

    name: str
    func: Callable[..., Any]
    parallelism: int = 1
    executor_type: str = "thread"  # "thread", "process", or "async"
    buffer_size: int = 100
    timeout: float | None = None


class PipelineStage:
    """Single stage in the parallel pipeline."""

    def __init__(
        self,
        config: StageConfig,
        input_queue: AsyncQueue | None = None,
        output_queue: AsyncQueue | None = None,
    ) -> None:
        self.config = config
        self.input_queue = input_queue
        self.output_queue = output_queue
        self.metrics = PipelineMetrics()
        self._tasks: list[asyncio.Task[Any]] = []
        self._executor: ThreadPoolExecutor | ProcessPoolExecutor | None = None
        self._running = False

    async def start(self) -> None:
        """Start the stage workers."""
        self._running = True

        # Create executor if needed
        if self.config.executor_type == "thread":
            self._executor = ThreadPoolExecutor(max_workers=self.config.parallelism)
        elif self.config.executor_type == "process":
            self._executor = ProcessPoolExecutor(max_workers=self.config.parallelism)

        # Start worker tasks
        for i in range(self.config.parallelism):
            task = asyncio.create_task(self._worker(i))
            self._tasks.append(task)

        logger.info(
            "Started %s workers for stage %s", self.config.parallelism, self.config.name
        )

    async def stop(self) -> None:
        """Stop the stage workers."""
        self._running = False

        # Wait for tasks to complete
        if self._tasks:
            await asyncio.gather(*self._tasks, return_exceptions=True)

        # Shutdown executor
        if self._executor:
            self._executor.shutdown(wait=True)

        logger.info("Stopped stage %s", self.config.name)

    async def _worker(self, worker_id: int) -> None:
        """Worker coroutine."""
        logger.debug("Worker %s started for stage %s", worker_id, self.config.name)

        while self._running:
            try:
                # Get item from input queue
                if self.input_queue:
                    try:
                        item = await asyncio.wait_for(
                            self.input_queue.get(), timeout=1.0
                        )
                    except TimeoutError:
                        continue
                    except StopAsyncIteration:
                        break
                else:
                    # No input queue, single execution
                    item = None
                    self._running = False

                # Process item
                start_time = time.time()
                try:
                    result = await self._process_item(item)

                    # Put result in output queue
                    if self.output_queue and result is not None:
                        await self.output_queue.put(result)

                    self.metrics.items_processed += 1

                # Pipeline processing: can fail for many reasons (I/O, parsing, validation, etc.)
                except Exception as e:
                    logger.error(
                        "Error processing item in stage %s: %s", self.config.name, e
                    )
                    self.metrics.items_failed += 1
                    # Optionally put error in output queue
                    if self.output_queue:
                        await self.output_queue.put(PipelineError(str(e), item))

                finally:
                    elapsed = time.time() - start_time
                    self.metrics.total_time += elapsed

                    if self.input_queue:
                        self.input_queue.task_done()

            # Worker thread: catch all exceptions to prevent thread death
            except Exception as e:
                logger.error(
                    "Worker %s error in stage %s: %s", worker_id, self.config.name, e
                )

        logger.debug("Worker %s stopped for stage %s", worker_id, self.config.name)

    async def _process_item(self, item: Any) -> Any:
        """Process a single item."""
        if self.config.executor_type == "async":
            # Direct async execution
            if asyncio.iscoroutinefunction(self.config.func):
                return await self.config.func(item)
            return self.config.func(item)
        # Execute in thread/process pool
        loop = asyncio.get_event_loop()
        future = loop.run_in_executor(self._executor, self.config.func, item)

        if self.config.timeout:
            return await asyncio.wait_for(future, timeout=self.config.timeout)
        return await future


class ParallelPipeline:
    """Parallel pipeline orchestrator."""

    def __init__(self, name: str = "pipeline") -> None:
        self.name = name
        self.stages: list[PipelineStage] = []
        self.queues: list[AsyncQueue] = []
        self.metrics = PipelineMetrics()
        self._running = False

    def add_stage(self, config: StageConfig) -> "ParallelPipeline":
        """Add a stage to the pipeline."""
        # Create input queue for stage (except first)
        input_queue = self.queues[-1] if self.queues else None

        # Create output queue for stage (except last)
        output_queue = AsyncQueue(
            maxsize=config.buffer_size, name=f"{config.name}_output"
        )
        self.queues.append(output_queue)

        # Create stage
        stage = PipelineStage(config, input_queue, output_queue)
        self.stages.append(stage)

        return self

    async def run(
        self,
        input_items: list[Any] | AsyncIterator[Any] | None = None,
        progress: PipelineProgress | None = None,
    ) -> list[Any]:
        """Run the pipeline."""
        self._running = True
        results: list[Any] = []

        try:
            # Start all stages
            await asyncio.gather(*[stage.start() for stage in self.stages])

            # Feed input items
            if input_items:
                if hasattr(input_items, "__aiter__"):
                    # Async iterator
                    async for item in input_items:
                        await self.queues[0].put(item)
                else:
                    # List
                    for item in input_items:
                        await self.queues[0].put(item)

            # Close input queue
            if self.queues:
                self.queues[0].close()

            # Monitor progress
            monitor_task = asyncio.create_task(self._monitor_progress(progress))

            # Collect results from last queue
            last_queue = self.queues[-1] if self.queues else None
            if last_queue:
                result_task = asyncio.create_task(
                    self._collect_results(last_queue, results)
                )

                # Wait for all stages to complete
                for i, stage in enumerate(self.stages):
                    if stage.input_queue:
                        await stage.input_queue.join()
                    # Close output queue for next stage
                    if i < len(self.stages) - 1 and stage.output_queue:
                        stage.output_queue.close()

                # Close last queue
                last_queue.close()

                # Wait for results
                await result_task

            # Stop monitoring
            monitor_task.cancel()

            # Stop all stages
            await asyncio.gather(*[stage.stop() for stage in self.stages])

            # Aggregate metrics
            for stage in self.stages:
                self.metrics.items_processed += stage.metrics.items_processed
                self.metrics.items_failed += stage.metrics.items_failed
                self.metrics.stage_times[stage.config.name] = stage.metrics.total_time

            return results

        except Exception as e:
            logger.error("Pipeline %s failed: %s", self.name, e)
            raise
        finally:
            self._running = False

    async def _collect_results(self, queue: AsyncQueue, results: list[Any]) -> None:
        """Collect results from output queue."""
        async for item in queue:
            if not isinstance(item, PipelineError):
                results.append(item)

    async def _monitor_progress(self, progress: PipelineProgress | None) -> None:
        """Monitor pipeline progress."""
        while self._running:
            try:
                # Update queue sizes
                for _i, queue in enumerate(self.queues):
                    self.metrics.queue_sizes[queue.name] = queue.qsize()

                # Update progress
                if progress:
                    total = sum(stage.metrics.items_processed for stage in self.stages)
                    progress.update(total)

                await asyncio.sleep(0.5)
            except asyncio.CancelledError:
                break
            # Progress monitoring: catch all exceptions to keep monitoring alive
            except Exception as e:
                logger.error("Error monitoring progress: %s", e)


# Convenience functions for common patterns


async def parallel_map(
    func: Callable[[T], R],
    items: list[T],
    parallelism: int | None = None,
    executor_type: str = "thread",
) -> list[R]:
    """Parallel map operation."""
    if parallelism is None:
        parallelism = mp.cpu_count()

    pipeline = ParallelPipeline("map")
    pipeline.add_stage(
        StageConfig(
            name="map", func=func, parallelism=parallelism, executor_type=executor_type
        )
    )

    return await pipeline.run(items)


async def parallel_filter(
    predicate: Callable[[T], bool], items: list[T], parallelism: int | None = None
) -> list[T]:
    """Parallel filter operation."""
    if parallelism is None:
        parallelism = mp.cpu_count()

    def filter_func(item: T) -> T | None:
        return item if predicate(item) else None

    pipeline = ParallelPipeline("filter")
    pipeline.add_stage(
        StageConfig(
            name="filter",
            func=filter_func,
            parallelism=parallelism,
            executor_type="thread",
        )
    )

    results = await pipeline.run(items)
    return [r for r in results if r is not None]


async def parallel_pipeline(*stages: StageConfig, input_items: list[Any]) -> list[Any]:
    """Create and run a parallel pipeline."""
    pipeline = ParallelPipeline()
    for stage in stages:
        pipeline.add_stage(stage)
    return await pipeline.run(input_items)
