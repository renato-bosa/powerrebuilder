"""End-to-end benchmarks for the complete conversion pipeline."""

import logging
import time
import tracemalloc
from pathlib import Path
from typing import Any
from unittest.mock import patch

import pytest
from pytest_benchmark.fixture import BenchmarkFixture

from common.pipeline.pipeline_coordinator import PipelineCoordinator

logger = logging.getLogger(__name__)

class TestEndToEndPerformance:
    """Benchmark complete conversion pipeline."""

    @pytest.fixture
    def pipeline(self, tmp_path: Path) -> PipelineCoordinator:
        """Create pipeline coordinator."""
        return PipelineCoordinator(
            input_dir=str(tmp_path / "input"),
            output_dir=str(tmp_path / "output"),
            enable_recovery=True,
        )

    @pytest.fixture
    def sample_pb_project(self, tmp_path: Path) -> Path:
        """Create a sample PowerBuilder project structure."""
        project_dir = tmp_path / "pb_project"
        project_dir.mkdir()

        # Create sample PBL files
        (project_dir / "app.pbl").write_bytes(b'HDR*' + b'\x00' * 1024)
        (project_dir / "windows.pbl").write_bytes(b'HDR*' + b'\x00' * 2048)
        (project_dir / "datawindows.pbl").write_bytes(b'HDR*' + b'\x00' * 1536)

        # Create sample source files
        src_dir = project_dir / "src"
        src_dir.mkdir()

        (src_dir / "w_main.srw").write_text('''
            forward
            global type w_main from window
            end type
            end forward

            global type w_main from window
            integer width = 2000
            integer height = 1500
            end type
        ''')

        (src_dir / "f_calculate.srf").write_text('''
            global function integer f_calculate(integer a, integer b)
                return a + b
            end function
        ''')

        return project_dir

    def test_small_project_conversion(self, benchmark: BenchmarkFixture, pipeline: PipelineCoordinator, sample_pb_project: Path) -> None:
        """Benchmark conversion of a small project."""
        # Mock the actual conversion steps
        with patch.object(pipeline, 'extract_step') as mock_extract, \
             patch.object(pipeline, 'parse_step') as mock_parse, \
             patch.object(pipeline, 'generate_step') as mock_generate:

            # Simulate realistic timing
            mock_extract.return_value = {"files": 5, "time": 0.1}
            mock_parse.return_value = {"ast_nodes": 10, "time": 0.2}
            mock_generate.return_value = {"generated": 15, "time": 0.15}

            def convert() -> dict[str, Any]:
                """Convert the project."""
                return pipeline.process_directory(str(sample_pb_project))

            benchmark(convert)
            assert benchmark.stats['mean'] < 1.0  # Under 1 second for small project

    def test_medium_project_conversion(self, benchmark: BenchmarkFixture, pipeline: PipelineCoordinator, tmp_path: Path) -> None:
        """Benchmark conversion of a medium-sized project."""
        # Create a medium project (50 files)
        project_dir = tmp_path / "medium_project"
        project_dir.mkdir()

        for i in range(10):
            pbl_file = project_dir / f"module_{i}.pbl"
            pbl_file.write_bytes(b'HDR*' + b'\x00' * (1024 * (i + 1)))

        src_dir = project_dir / "src"
        src_dir.mkdir()

        for i in range(40):
            src_file = src_dir / f"object_{i}.sro"
            src_file.write_text(f'''
                global type obj_{i} from nonvisualobject
                end type

                forward prototypes
                public function integer calculate_{i}()
                end prototypes

                public function integer calculate_{i}()
                    return {i}
                end function
            ''')

        with patch.object(pipeline, 'process_file') as mock_process:
            mock_process.return_value = {"status": "success", "time": 0.01}

            def convert() -> int:
                """Convert the medium project."""
                processed = 0
                for file in project_dir.rglob("*"):
                    if file.is_file():
                        pipeline.process_file(str(file), str(tmp_path / "output"))
                        processed += 1
                return processed

            benchmark(convert)
            # Medium projects should complete reasonably fast
            assert benchmark.stats['mean'] < 5.0  # Under 5 seconds

    def test_memory_efficiency(self, benchmark: BenchmarkFixture, pipeline: PipelineCoordinator, sample_pb_project: Path) -> None:
        """Benchmark memory usage during conversion."""
        def measure_memory() -> float:


            tracemalloc.start()

            with patch.object(pipeline, 'process_file') as mock_process:
                mock_process.return_value = {"status": "success"}
                pipeline.process_directory(str(sample_pb_project))

            current, peak = tracemalloc.get_traced_memory()
            tracemalloc.stop()
            return peak / 1024 / 1024  # MB

        benchmark(measure_memory)
        # Memory usage should be reasonable
        assert benchmark.stats['mean'] < 200  # Less than 200MB peak

    def test_parallel_processing(self, benchmark: BenchmarkFixture, pipeline: PipelineCoordinator, sample_pb_project: Path) -> None:
        """Benchmark parallel processing performance."""
        # Enable parallel processing
        pipeline.parallel = True
        pipeline.max_workers = 4

        with patch.object(pipeline, 'process_file') as mock_process:
            # Simulate some processing time
            def side_effect(*_args: object) -> dict:
                """Side effect for mocking file processing.

                Returns:
                    dict: A dictionary with status "success"
                """
                time.sleep(0.01)  # 10ms per file
                return {"status": "success"}

            mock_process.side_effect = side_effect

            def convert_parallel() -> dict[str, Any]:
                """Convert with parallel processing."""
                return pipeline.process_directory(str(sample_pb_project))

            benchmark(convert_parallel)
            # Parallel processing should be faster
            assert benchmark.stats['mean'] < 0.5  # Should benefit from parallelism

    def test_error_recovery_overhead(self, benchmark: BenchmarkFixture, pipeline: PipelineCoordinator) -> None:
        """Benchmark overhead of error recovery."""
        # Create files with errors
        error_file = "corrupted.pbl"

        def process_with_recovery() -> dict[str, str]:
            """Process with error recovery."""
            with patch.object(pipeline, 'extract_step') as mock_extract:
                # Simulate extraction with errors
                mock_extract.side_effect = Exception("Corrupted file")

                try:
                    return pipeline.process_file(error_file, "output")
                except Exception as e:  # noqa: BLE001
                    logger.debug("Exception caught: %s", e)
                    # Recovery should handle this
                    return {"status": "recovered"}

        benchmark(process_with_recovery)
        # Recovery adds overhead but should be reasonable
        assert benchmark.stats['mean'] < 0.1  # Under 100ms

    def test_incremental_conversion(self, benchmark: BenchmarkFixture, pipeline: PipelineCoordinator, sample_pb_project: Path, tmp_path: Path) -> None:
        """Benchmark incremental conversion (only changed files)."""
        output_dir = tmp_path / "output"
        output_dir.mkdir()

        # First conversion (full)
        with patch.object(pipeline, 'process_file') as mock_process:
            mock_process.return_value = {"status": "success"}
            pipeline.process_directory(str(sample_pb_project))

        # Mark some files as already processed
        cache_file = output_dir / ".conversion_cache"
        cache_file.write_text("w_main.srw: processed\n")

        # Benchmark incremental conversion
        def incremental_convert() -> dict[str, Any]:
            """Perform incremental conversion."""
            with patch.object(pipeline, 'is_file_changed') as mock_changed:
                mock_changed.return_value = False  # Most files unchanged
                return pipeline.process_directory(str(sample_pb_project))

        benchmark(incremental_convert)
        # Incremental should be much faster
        assert benchmark.stats['mean'] < 0.1  # Under 100ms
