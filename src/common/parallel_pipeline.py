"""Parallel pipeline infrastructure using asyncio."""

import asyncio
from dataclasses import dataclass, field
from typing import Any, AsyncIterator, Callable, Dict, List, Optional, Set, TypeVar, Union
import logging
from concurrent.futures import ProcessPoolExecutor, ThreadPoolExecutor
import multiprocessing as mp
import time

from .pipeline.progress import Progress
from src.common.exceptions import SimeFinchError as PipelineError

logger = logging.getLogger(__name__)

T = TypeVar('T')
R = TypeVar('R')


@dataclass
class PipelineMetrics:
    """Metrics for pipeline performance monitoring."""
    items_processed: int = 0
    items_failed: int = 0
    total_time: float = 0.0
    stage_times: Dict[str, float] = field(default_factory=dict)
    queue_sizes: Dict[str, int] = field(default_factory=dict)


class AsyncQueue:
    """Async queue with backpressure support."""

    def __init__(self, maxsize: int = 0, name: str = "queue"):
        self._queue = asyncio.Queue(maxsize=maxsize)
        self.name = name
        self._closed = False
        self._waiters: Set[asyncio.Task] = set()

    async def put(self, item: Any):
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

    def close(self):
        """Close queue for new items."""
        self._closed = True

    async def join(self):
        """Wait for all items to be processed."""
        await self._queue.join()

    def task_done(self):
        """Mark task as done."""
        self._queue.task_done()

    async def __aiter__(self):
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
    func: Callable
    parallelism: int = 1
    executor_type: str = "thread"  # "thread", "process", or "async"
    buffer_size: int = 100
    timeout: Optional[float] = None


class PipelineStage:
    """Single stage in the parallel pipeline."""

    def __init__(
        self,
        config: StageConfig,
        input_queue: Optional[AsyncQueue] = None,
        output_queue: Optional[AsyncQueue] = None
    ):
        self.config = config
        self.input_queue = input_queue
        self.output_queue = output_queue
        self.metrics = PipelineMetrics()
        self._tasks: List[asyncio.Task] = []
        self._executor = None
        self._running = False

    async def start(self):
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

        logger.info(f"Started {self.config.parallelism} workers for stage {self.config.name}")

    async def stop(self):
        """Stop the stage workers."""
        self._running = False

        # Wait for tasks to complete
        if self._tasks:
            await asyncio.gather(*self._tasks, return_exceptions=True)

        # Shutdown executor
        if self._executor:
            self._executor.shutdown(wait=True)

        logger.info(f"Stopped stage {self.config.name}")

    async def _worker(self, worker_id: int):
        """Worker coroutine."""
        logger.debug(f"Worker {worker_id} started for stage {self.config.name}")

        while self._running:
            try:
                # Get item from input queue
                if self.input_queue:
                    try:
                        item = await asyncio.wait_for(
                            self.input_queue.get(),
                            timeout=1.0
                        )
                    except asyncio.TimeoutError:
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

                except Exception as e:
                    logger.error(f"Error processing item in stage {self.config.name}: {e}")
                    self.metrics.items_failed += 1
                    # Optionally put error in output queue
                    if self.output_queue:
                        await self.output_queue.put(PipelineError(str(e), item))

                finally:
                    elapsed = time.time() - start_time
                    self.metrics.total_time += elapsed

                    if self.input_queue:
                        self.input_queue.task_done()

            except Exception as e:
                logger.error(f"Worker {worker_id} error in stage {self.config.name}: {e}")

        logger.debug(f"Worker {worker_id} stopped for stage {self.config.name}")

    async def _process_item(self, item: Any) -> Any:
        """Process a single item."""
        if self.config.executor_type == "async":
            # Direct async execution
            if asyncio.iscoroutinefunction(self.config.func):
                return await self.config.func(item)
            else:
                return self.config.func(item)
        else:
            # Execute in thread/process pool
            loop = asyncio.get_event_loop()
            future = loop.run_in_executor(self._executor, self.config.func, item)

            if self.config.timeout:
                return await asyncio.wait_for(future, timeout=self.config.timeout)
            else:
                return await future


class ParallelPipeline:
    """Parallel pipeline orchestrator."""

    def __init__(self, name: str = "pipeline"):
        self.name = name
        self.stages: List[PipelineStage] = []
        self.queues: List[AsyncQueue] = []
        self.metrics = PipelineMetrics()
        self._running = False

    def add_stage(self, config: StageConfig) -> 'ParallelPipeline':
        """Add a stage to the pipeline."""
        # Create input queue for stage (except first)
        input_queue = self.queues[-1] if self.queues else None

        # Create output queue for stage (except last)
        output_queue = AsyncQueue(
            maxsize=config.buffer_size,
            name=f"{config.name}_output"
        )
        self.queues.append(output_queue)

        # Create stage
        stage = PipelineStage(config, input_queue, output_queue)
        self.stages.append(stage)

        return self

    async def run(
        self,
        input_items: Optional[Union[List[Any], AsyncIterator[Any]]] = None,
        progress: Optional[Progress] = None
    ) -> List[Any]:
        """Run the pipeline."""
        self._running = True
        results = []

        try:
            # Start all stages
            await asyncio.gather(*[stage.start() for stage in self.stages])

            # Feed input items
            if input_items:
                if hasattr(input_items, '__aiter__'):
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
                result_task = asyncio.create_task(self._collect_results(last_queue, results))

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
            logger.error(f"Pipeline {self.name} failed: {e}")
            raise
        finally:
            self._running = False

    async def _collect_results(self, queue: AsyncQueue, results: List[Any]):
        """Collect results from output queue."""
        async for item in queue:
            if not isinstance(item, PipelineError):
                results.append(item)

    async def _monitor_progress(self, progress: Optional[Progress]):
        """Monitor pipeline progress."""
        while self._running:
            try:
                # Update queue sizes
                for i, queue in enumerate(self.queues):
                    self.metrics.queue_sizes[queue.name] = queue.qsize()

                # Update progress
                if progress:
                    total = sum(stage.metrics.items_processed for stage in self.stages)
                    progress.update(total)

                await asyncio.sleep(0.5)
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error monitoring progress: {e}")


# Convenience functions for common patterns

async def parallel_map(
    func: Callable[[T], R],
    items: List[T],
    parallelism: int = None,
    executor_type: str = "thread"
) -> List[R]:
    """Parallel map operation."""
    if parallelism is None:
        parallelism = mp.cpu_count()

    pipeline = ParallelPipeline("map")
    pipeline.add_stage(StageConfig(
        name="map",
        func=func,
        parallelism=parallelism,
        executor_type=executor_type
    ))

    return await pipeline.run(items)


async def parallel_filter(
    predicate: Callable[[T], bool],
    items: List[T],
    parallelism: int = None
) -> List[T]:
    """Parallel filter operation."""
    if parallelism is None:
        parallelism = mp.cpu_count()

    def filter_func(item):
        return item if predicate(item) else None

    pipeline = ParallelPipeline("filter")
    pipeline.add_stage(StageConfig(
        name="filter",
        func=filter_func,
        parallelism=parallelism,
        executor_type="thread"
    ))

    results = await pipeline.run(items)
    return [r for r in results if r is not None]


async def parallel_pipeline(*stages: StageConfig, input_items: List[Any]) -> List[Any]:
    """Create and run a parallel pipeline."""
    pipeline = ParallelPipeline()
    for stage in stages:
        pipeline.add_stage(stage)
    return await pipeline.run(input_items)