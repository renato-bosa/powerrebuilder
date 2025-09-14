#!/usr/bin/env python3
"""Demonstration of pipeline progress tracking.

This script shows how the PowerRebuilder pipeline tracks progress
through all stages of processing, providing real-time feedback to users.
"""

import logging
import sys
import time
from pathlib import Path

# Add the project root to the Python path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.common.pipeline.pipeline_coordinator import PipelineCoordinator
from src.common.pipeline.progress import PipelineProgress, track_progress
from src.parse.coordinator import ParseCoordinator


def demo_individual_stage_progress() -> None:
    """Demonstrate progress tracking for individual pipeline stages."""
    # Demo 1: Simple progress tracking
    with track_progress("Processing files", total=10) as progress:
        for i in range(10):
            time.sleep(0.2)
            progress.advance(1, description=f"Processing file_{i}.pbl")

    # Demo 2: File extraction with transfer speed
    progress = PipelineProgress()

    with progress.pipeline_context(total_steps=1) as pipeline:
        pipeline.start_step("Extracting PowerBuilder files", 1)

        with pipeline.file_extraction_context(total_files=5) as _:
            for i in range(5):
                # Simulate file extraction with varying speeds
                file_size = 1024 * 1024 * (i + 1)  # 1-5 MB
                start_time = time.time()
                time.sleep(0.5)  # Simulate extraction time
                speed = file_size / (time.time() - start_time)

                pipeline.update_file_progress(i + 1, f"file_{i}.pbl", speed)

        pipeline.complete_step(1)

    # Demo 3: Operation progress
    progress = PipelineProgress()

    with progress.pipeline_context(total_steps=1) as pipeline:
        pipeline.start_step("Processing operations", 1)

        # Decompiling functions
        with pipeline.operation_context("Decompiling functions", total=20):
            for i in range(20):
                pipeline.update_operation(i + 1, f"Function {i + 1}/20")
                time.sleep(0.05)

        # Parsing source files
        with pipeline.operation_context("Parsing source files", total=15):
            for i in range(15):
                pipeline.update_operation(i + 1, f"File {i + 1}/15")
                time.sleep(0.05)

        pipeline.complete_step(1)


def demo_full_pipeline_progress() -> None:
    """Demonstrate progress tracking through the complete pipeline."""
    progress = PipelineProgress()

    with progress.pipeline_context(total_steps=5) as pipeline:
        # Stage 1: Extract
        pipeline.start_step("Extracting PowerBuilder files", 1)
        with pipeline.file_extraction_context(total_files=10) as _:
            for i in range(10):
                pipeline.update_file_progress(i + 1, f"library_{i}.pbl", 2048000)
                time.sleep(0.1)
        pipeline.complete_step(1)

        # Stage 2: Decompile
        pipeline.start_step("Decompiling P-code", 2)
        with pipeline.operation_context("Decompiling functions", total=50):
            for i in range(50):
                pipeline.update_operation(i + 1, f"Function {i + 1}/50")
                time.sleep(0.02)
        pipeline.complete_step(2)

        # Stage 3: Parse
        pipeline.start_step("Parsing source code", 3)
        with pipeline.operation_context("Parsing files", total=30):
            for i in range(30):
                pipeline.update_operation(i + 1, f"Parsing file {i + 1}/30")
                time.sleep(0.03)
        pipeline.complete_step(3)

        # Stage 4: Model
        pipeline.start_step("Building models", 4)
        with pipeline.operation_context("Creating models", total=25):
            for i in range(25):
                pipeline.update_operation(i + 1, f"Model {i + 1}/25")
                time.sleep(0.03)
        pipeline.complete_step(4)

        # Stage 5: Generate
        pipeline.start_step("Generating output", 5)
        with pipeline.operation_context("Generating code", total=20):
            for i in range(20):
                pipeline.update_operation(i + 1, f"Generating {i + 1}/20")
                time.sleep(0.04)
        pipeline.complete_step(5)


def demo_pipeline_coordinator() -> None:
    """Demonstrate the actual pipeline coordinator with progress."""
    # Create test data structure
    test_dir = Path("examples/test_pipeline_data")
    test_dir.mkdir(exist_ok=True)

    # Create a mock PBL file
    mock_pbl = test_dir / "test.pbl"
    mock_pbl.write_bytes(b"MOCK PBL DATA")

    try:
        # Configure pipeline
        config = {
            "extract": {"preserve_structure": True},
            "decompile": {"output_format": "pb"},
            "parse": {"enable_recovery": True},
            "generate": {"target_framework": "flutter"},
        }

        # Create and run pipeline
        PipelineCoordinator(
            input_dir=test_dir, output_dir=test_dir / "output", config=config
        )

        # The coordinator would normally process files here
        # For demo purposes, we'll just show the structure

    finally:
        # Cleanup
        import shutil

        if test_dir.exists():
            shutil.rmtree(test_dir)


def demo_custom_progress_callbacks() -> None:
    """Demonstrate custom progress callbacks."""

    # Example 1: Simple callback
    def simple_callback(current: int, total: int, message: str) -> None:
        (current / total * 100) if total > 0 else 0

    # Create mock data
    test_dir = Path("examples/test_parse_data")
    test_dir.mkdir(exist_ok=True)

    # Create some mock source files
    for i in range(3):
        (test_dir / f"test_{i}.sru").write_text(f"// Mock source file {i}")

    try:
        # Create parser with custom callback
        ParseCoordinator(input_dir=test_dir, output_dir=test_dir / "parsed")

        # This would normally parse files, but we'll simulate
        simple_callback(0, 3, "Starting parsing")
        for i in range(3):
            simple_callback(i + 1, 3, f"Parsing test_{i}.sru")
            time.sleep(0.2)
        simple_callback(3, 3, "Parsing complete")

    finally:
        # Cleanup
        import shutil

        if test_dir.exists():
            shutil.rmtree(test_dir)

    # Example 2: Rich callback with more details
    class DetailedProgressTracker:
        def __init__(self) -> None:
            self.start_time = time.time()
            self.last_update = 0

        def __call__(self, current: int, total: int, message: str) -> None:
            elapsed = time.time() - self.start_time
            if total > 0 and current > 0:
                rate = current / elapsed
                (total - current) / rate if rate > 0 else 0
            else:
                pass

    tracker = DetailedProgressTracker()

    for i in range(5):
        tracker(i + 1, 5, f"Processing item {i + 1}")
        time.sleep(0.3)


def main() -> None:
    """Run all demonstrations."""
    # Configure logging to show only important messages
    logging.basicConfig(level=logging.WARNING)

    try:
        # Run demonstrations
        demo_individual_stage_progress()
        demo_full_pipeline_progress()
        demo_pipeline_coordinator()
        demo_custom_progress_callbacks()

    except KeyboardInterrupt:
        pass
    except Exception:
        import traceback

        traceback.print_exc()


if __name__ == "__main__":
    main()
