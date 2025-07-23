#!/usr/bin/env python3
"""Demo of streaming pipeline with in-memory communication.

This demonstrates how the pipeline stages can communicate through
memory streams instead of file I/O, resulting in:
- Faster processing
- Lower memory usage
- Better resource utilization
"""

import logging
import sys
import time
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

import contextlib

from src.common.injection import configure_services
from src.common.pipeline.modes.streaming import StreamingPipelineCoordinator

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


def demo_memory_streaming():
    """Demonstrate in-memory streaming between stages."""
    from src.common.pipeline.streaming import StreamManager

    logger.info("=== Memory Streaming Demo ===")

    # Create stream manager
    manager = StreamManager()

    # Create a stream
    stream = manager.create_stream(
        "demo_stream",
        source_stage="producer",
        target_stage="consumer",
        data_type="demo_data",
        maxsize=10,
    )

    # Producer thread
    def producer() -> None:
        logger.info("Producer: Starting")
        for i in range(20):
            try:
                data = {"id": i, "value": f"item_{i}"}
                stream.write(data)
                logger.info("Producer: Wrote item %d", i)
                time.sleep(0.1)
            except Exception as e:
                logger.warning("Producer: Backpressure - %s", e)
                time.sleep(0.5)
                # Retry
                stream.write(data)
        stream.close()
        logger.info("Producer: Finished")

    # Consumer thread
    def consumer() -> None:
        logger.info("Consumer: Starting")
        count = 0
        while not stream.is_closed or stream._queue.size > 0:
            try:
                item = stream.read()
                if item:
                    logger.info("Consumer: Read %s", item)
                    count += 1
                    time.sleep(0.2)  # Simulate processing
            except Exception:
                time.sleep(0.1)
        logger.info("Consumer: Finished. Processed %d items", count)

    # Run producer and consumer concurrently
    import threading

    producer_thread = threading.Thread(target=producer)
    consumer_thread = threading.Thread(target=consumer)

    producer_thread.start()
    consumer_thread.start()

    producer_thread.join()
    consumer_thread.join()

    # Show statistics
    stats = manager.get_stats()
    logger.info("Stream statistics: %s", stats)

    manager.close_all()


def compare_pipeline_modes():
    """Compare file-based vs streaming pipeline performance."""
    logger.info("\n=== Pipeline Mode Comparison ===")

    # Configure services
    container = configure_services()

    # Get coordinators
    extract_coord = container.resolve("IExtractorCoordinator")
    decompile_coord = container.resolve("IDecompilerCoordinator")
    parse_coord = container.resolve("IParserCoordinator")
    model_coord = container.resolve("IModelCoordinator")
    generate_coord = container.resolve("IGeneratorCoordinator")

    # Create streaming pipeline
    pipeline = StreamingPipelineCoordinator(
        extract_coordinator=extract_coord,
        decompile_coordinator=decompile_coord,
        parse_coordinator=parse_coord,
        model_coordinator=model_coord,
        generate_coordinator=generate_coord,
    )

    # Test data
    test_input = Path("test_data/sample.pbl")
    output_dir = Path("output")

    if not test_input.exists():
        logger.warning("Test file %s not found. Creating mock data...", test_input)
        test_input = create_mock_test_data()

    # Run file-based pipeline
    logger.info("\n--- File-based Pipeline ---")
    start_time = time.time()

    file_result = pipeline.run_pipeline(
        test_input, output_dir / "file_based", target="flutter", use_streaming=False
    )

    file_time = time.time() - start_time
    logger.info("File-based pipeline completed in %.2f seconds", file_time)
    logger.info("Results: %s", file_result)

    # Run streaming pipeline
    logger.info("\n--- Streaming Pipeline ---")
    start_time = time.time()

    stream_result = pipeline.run_pipeline(
        test_input, output_dir / "streaming", target="flutter", use_streaming=True
    )

    stream_time = time.time() - start_time
    logger.info("Streaming pipeline completed in %.2f seconds", stream_time)
    logger.info("Results: %s", stream_result)

    # Compare results
    logger.info("\n--- Comparison ---")
    logger.info(
        "Time saved: %.2f seconds (%.1f%% faster)",
        file_time - stream_time,
        ((file_time - stream_time) / file_time) * 100,
    )
    logger.info("Memory saved: %.2f MB", stream_result.get("memory_saved_mb", 0))

    # Show stream statistics
    if "stream_stats" in stream_result:
        logger.info("\nStream Statistics:")
        for stream_id, stats in stream_result["stream_stats"].items():
            logger.info(
                "  %s: %d items, %.2f MB",
                stream_id,
                stats["items"],
                stats["bytes"] / (1024 * 1024),
            )


def create_mock_test_data() -> Path:
    """Create mock test data for demo."""
    test_dir = Path("test_data")
    test_dir.mkdir(exist_ok=True)

    # Create mock P-code files
    for i in range(5):
        pcode_file = test_dir / f"test_object_{i}.fun"
        with open(pcode_file, "wb") as f:
            # Write mock P-code data
            f.write(b"PBFUN\x00\x00\x00")
            f.write(f"test_object_{i}".encode())
            f.write(b"\x00" * 100)  # Mock bytecode

        logger.info("Created mock file: %s", pcode_file)

    return test_dir


def demonstrate_backpressure():
    """Demonstrate backpressure handling in streams."""
    logger.info("\n=== Backpressure Handling Demo ===")

    from src.common.pipeline.streaming import MemoryStream

    # Create small stream to trigger backpressure
    stream = MemoryStream(
        source_stage="fast_producer",
        target_stage="slow_consumer",
        data_type="test",
        maxsize=5,  # Small queue
    )

    backpressure_events = []

    # Fast producer
    def fast_producer() -> None:
        for i in range(50):
            try:
                stream.write({"id": i})
                logger.info("Produced: %d", i)
                time.sleep(0.01)  # Very fast
            except Exception as e:
                backpressure_events.append(i)
                logger.warning("Backpressure at item %d: %s", i, e)
                time.sleep(0.5)  # Back off
                # Retry
                with contextlib.suppress(Exception):
                    stream.write({"id": i})
        stream.close()

    # Slow consumer
    def slow_consumer() -> None:
        count = 0
        while not stream.is_closed or stream._queue.size > 0:
            try:
                item = stream.read()
                if item:
                    logger.info("Consumed: %s", item)
                    count += 1
                    time.sleep(0.1)  # Slow processing
            except:
                time.sleep(0.05)
        logger.info("Consumed %d items", count)

    # Run test
    import threading

    prod = threading.Thread(target=fast_producer)
    cons = threading.Thread(target=slow_consumer)

    prod.start()
    cons.start()

    prod.join()
    cons.join()

    logger.info("\nBackpressure events: %d times", len(backpressure_events))
    logger.info("Queue prevented memory overflow by applying backpressure")
    logger.info("Stream metadata: %s", stream.metadata.__dict__)


async def demo_async_streaming():
    """Demonstrate async streaming capabilities."""
    logger.info("\n=== Async Streaming Demo ===")

    import asyncio

    from src.common.pipeline.streaming import AsyncMemoryStream

    # Create async stream
    stream = AsyncMemoryStream(
        source_stage="async_producer",
        target_stage="async_consumer",
        data_type="async_data",
        maxsize=10,
    )

    # Async producer
    async def async_producer() -> None:
        for i in range(10):
            await stream.write({"id": i, "data": f"async_item_{i}"})
            logger.info("Async produced: %d", i)
            await asyncio.sleep(0.1)
        await stream.close()

    # Async consumer
    async def async_consumer() -> None:
        count = 0
        async for item in stream:
            logger.info("Async consumed: %s", item)
            count += 1
            await asyncio.sleep(0.05)
        logger.info("Async consumer processed %d items", count)

    # Run concurrently
    await asyncio.gather(async_producer(), async_consumer())


def main():
    """Run all demos."""
    logger.info("PowerRebuilder Streaming Pipeline Demo")
    logger.info("=" * 50)

    # Demo 1: Basic memory streaming
    demo_memory_streaming()

    # Demo 2: Compare pipeline modes
    # compare_pipeline_modes()  # Commented as it needs real coordinators

    # Demo 3: Backpressure handling
    demonstrate_backpressure()

    # Demo 4: Async streaming
    import asyncio

    asyncio.run(demo_async_streaming())

    logger.info("\n" + "=" * 50)
    logger.info("Demo completed!")
    logger.info("\nKey Benefits of Streaming Pipeline:")
    logger.info("✓ No intermediate files between stages")
    logger.info("✓ Lower memory usage with bounded queues")
    logger.info("✓ Automatic backpressure handling")
    logger.info("✓ Concurrent stage execution")
    logger.info("✓ Better resource utilization")


if __name__ == "__main__":
    main()
