"""Tests for common.pipeline module."""

import json
from datetime import datetime
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from src.common.pipeline.pipeline import NoOpProgressTracker, PipelineStage, PipelineSummary


class ConcretePipelineStage(PipelineStage):
    """Concrete implementation of PipelineStage for testing."""

    def process_file(self, input_file: Path, output_dir: Path) -> dict[str, any]:




        """Mock implementation of process_file."""
        return {"processed": str(input_file), "output": str(output_dir)}


class TestPipelineStage:
    """Test PipelineStage base class."""

    def test_initialization(self):




        """Test PipelineStage initialization."""
        stage = ConcretePipelineStage("test_stage")

        assert stage.stage_name == "test_stage"
        assert stage.logger.name == "common.pipeline.pipeline.test_stage"

    def test_ensure_directory_creates_new(self, tmp_path):




        """Test ensure_directory creates new directory."""
        stage = ConcretePipelineStage("test")
        new_dir = tmp_path / "new" / "nested" / "dir"

        result = stage.ensure_directory(new_dir)

        assert new_dir.exists()
        assert new_dir.is_dir()
        assert result == new_dir

    def test_ensure_directory_existing(self, tmp_path):




        """Test ensure_directory with existing directory."""
        stage = ConcretePipelineStage("test")
        existing_dir = tmp_path / "existing"
        existing_dir.mkdir()

        result = stage.ensure_directory(existing_dir)

        assert existing_dir.exists()
        assert result == existing_dir

    def test_process_directory_empty(self, tmp_path):




        """Test processing empty directory."""
        stage = ConcretePipelineStage("test")
        input_dir = tmp_path / "input"
        output_dir = tmp_path / "output"
        input_dir.mkdir()

        summary = stage.process_directory(input_dir, output_dir, pattern="*.txt")

        assert summary["stage"] == "test"
        assert summary["statistics"]["total_files"] == 0
        assert summary["statistics"]["successful"] == 0
        assert summary["statistics"]["failed"] == 0
        assert summary["statistics"]["success_rate"] == 0.0
        assert output_dir.exists()

    def test_process_directory_with_files(self, tmp_path):




        """Test processing directory with matching files."""
        stage = ConcretePipelineStage("test")
        input_dir = tmp_path / "input"
        output_dir = tmp_path / "output"
        input_dir.mkdir()

        # Create test files
        (input_dir / "file1.txt").write_text("content1")
        (input_dir / "file2.txt").write_text("content2")
        (input_dir / "file3.log").write_text("log content")

        summary = stage.process_directory(input_dir, output_dir, pattern="*.txt")

        assert summary["statistics"]["total_files"] == 2
        assert summary["statistics"]["successful"] == 2
        assert summary["statistics"]["failed"] == 0
        assert summary["statistics"]["success_rate"] == 1.0
        assert len(summary["results"]) == 2

    def test_process_directory_recursive(self, tmp_path):




        """Test recursive directory processing."""
        stage = ConcretePipelineStage("test")
        input_dir = tmp_path / "input"
        output_dir = tmp_path / "output"
        sub_dir = input_dir / "subdir"
        sub_dir.mkdir(parents=True)

        # Create files at different levels
        (input_dir / "file1.txt").write_text("content1")
        (sub_dir / "file2.txt").write_text("content2")

        # Test recursive
        summary = stage.process_directory(
            input_dir, output_dir, pattern="*.txt", recursive=True,
        )
        assert summary["statistics"]["total_files"] == 2

        # Test non-recursive
        summary = stage.process_directory(
            input_dir, output_dir, pattern="*.txt", recursive=False,
        )
        assert summary["statistics"]["total_files"] == 1

    def test_process_directory_with_failures(self, tmp_path):




        """Test processing with some failures."""
        class FailingStage(PipelineStage):
            def process_file(self, input_file: Path, output_dir: Path) -> dict[str, any]:

                if "fail" in input_file.name:
                    raise ValueError(f"Simulated failure for {input_file}")
                return {"processed": str(input_file)}

        stage = FailingStage("test")
        input_dir = tmp_path / "input"
        output_dir = tmp_path / "output"
        input_dir.mkdir()

        # Create test files
        (input_dir / "success.txt").write_text("ok")
        (input_dir / "fail.txt").write_text("will fail")

        summary = stage.process_directory(input_dir, output_dir, pattern="*.txt")

        assert summary["statistics"]["total_files"] == 2
        assert summary["statistics"]["successful"] == 1
        assert summary["statistics"]["failed"] == 1
        assert summary["statistics"]["success_rate"] == 0.5
        assert len(summary["errors"]) == 1
        assert "fail.txt" in summary["errors"][0]["file"]

    @patch("extract.pbd.io.progress.TqdmProgressTracker")
    def test_get_progress_tracker_enabled(self, mock_tqdm):


        """Test progress tracker when enabled."""
        stage = ConcretePipelineStage("test")
        mock_tracker = MagicMock()
        mock_tqdm.return_value = mock_tracker

        tracker = stage._get_progress_tracker(10, enabled=True)

        assert tracker == mock_tracker
        mock_tqdm.assert_called_once_with(
            total=10,
            description="Test progress",
        )

    @patch("extract.pbd.io.progress.SilentProgressTracker")
    def test_get_progress_tracker_disabled(self, mock_silent):


        """Test progress tracker when disabled."""
        stage = ConcretePipelineStage("test")
        mock_tracker = MagicMock()
        mock_silent.return_value = mock_tracker

        tracker = stage._get_progress_tracker(10, enabled=False)

        assert tracker == mock_tracker
        mock_silent.assert_called_once_with(
            total=10,
            description="Test progress",
        )

    def test_get_progress_tracker_import_error(self):




        """Test progress tracker fallback on import error."""
        stage = ConcretePipelineStage("test")

        # Patch the entire module import to raise ImportError
        with patch.dict("sys.modules", {"extract.pbd.io.progress": None}):
            tracker = stage._get_progress_tracker(10, enabled=True)

        assert isinstance(tracker, NoOpProgressTracker)

    def test_save_summary(self, tmp_path):




        """Test saving summary to JSON file."""
        stage = ConcretePipelineStage("test")
        output_dir = tmp_path / "output"
        output_dir.mkdir()

        summary = {
            "stage": "test",
            "statistics": {
                "total_files": 5,
                "successful": 4,
                "failed": 1,
            },
        }

        summary_file = stage.save_summary(summary, output_dir)

        assert summary_file == output_dir / "test_summary.json"
        assert summary_file.exists()

        # Verify content
        with open(summary_file) as f:
            loaded = json.load(f)
        assert loaded == summary


class TestPipelineSummary:
    """Test PipelineSummary class."""

    def test_initialization(self, tmp_path):




        """Test PipelineSummary initialization."""
        input_dir = tmp_path / "input"
        output_dir = tmp_path / "output"

        summary = PipelineSummary("test", input_dir, output_dir)

        assert summary.stage_name == "test"
        assert summary.input_dir == input_dir
        assert summary.output_dir == output_dir
        assert summary.success_count == 0
        assert summary.failure_count == 0
        assert summary.results == []
        assert summary.errors == []
        assert isinstance(summary.start_time, datetime)

    def test_add_success_without_result(self, tmp_path):




        """Test adding success without result data."""
        summary = PipelineSummary("test", tmp_path, tmp_path)
        file_path = tmp_path / "file.txt"

        summary.add_success(file_path)

        assert summary.success_count == 1
        assert summary.failure_count == 0
        assert len(summary.results) == 0  # No result data provided

    def test_add_success_with_result(self, tmp_path):




        """Test adding success with result data."""
        summary = PipelineSummary("test", tmp_path, tmp_path)
        file_path = tmp_path / "file.txt"
        result = {"lines": 100, "size": 1024}

        summary.add_success(file_path, result)

        assert summary.success_count == 1
        assert len(summary.results) == 1
        assert summary.results[0]["file"] == str(file_path)
        assert summary.results[0]["status"] == "success"
        assert summary.results[0]["lines"] == 100
        assert summary.results[0]["size"] == 1024

    def test_add_failure(self, tmp_path):




        """Test adding failure."""
        summary = PipelineSummary("test", tmp_path, tmp_path)
        file_path = tmp_path / "file.txt"
        error = "Permission denied"

        summary.add_failure(file_path, error)

        assert summary.failure_count == 1
        assert summary.success_count == 0
        assert len(summary.errors) == 1
        assert summary.errors[0]["file"] == str(file_path)
        assert summary.errors[0]["error"] == error

    def test_generate_empty_summary(self, tmp_path):




        """Test generating summary with no files processed."""
        input_dir = tmp_path / "input"
        output_dir = tmp_path / "output"
        summary = PipelineSummary("test", input_dir, output_dir)

        result = summary.generate()

        assert result["stage"] == "test"
        assert result["input_directory"] == str(input_dir)
        assert result["output_directory"] == str(output_dir)
        assert result["statistics"]["total_files"] == 0
        assert result["statistics"]["successful"] == 0
        assert result["statistics"]["failed"] == 0
        assert result["statistics"]["success_rate"] == 0.0
        assert result["results"] is None
        assert result["errors"] is None
        assert "processed_at" in result
        assert "duration_seconds" in result

    def test_generate_mixed_summary(self, tmp_path):




        """Test generating summary with mixed results."""
        summary = PipelineSummary("test", tmp_path, tmp_path)

        # Add some successes
        summary.add_success(tmp_path / "file1.txt", {"size": 100})
        summary.add_success(tmp_path / "file2.txt", {"size": 200})
        summary.add_success(tmp_path / "file3.txt")  # No result data

        # Add some failures
        summary.add_failure(tmp_path / "file4.txt", "Error 1")
        summary.add_failure(tmp_path / "file5.txt", "Error 2")

        result = summary.generate()

        assert result["statistics"]["total_files"] == 5
        assert result["statistics"]["successful"] == 3
        assert result["statistics"]["failed"] == 2
        assert result["statistics"]["success_rate"] == 0.6
        assert len(result["results"]) == 2  # Only files with result data
        assert len(result["errors"]) == 2

    def test_generate_duration_calculation(self, tmp_path):




        """Test duration calculation in summary."""
        summary = PipelineSummary("test", tmp_path, tmp_path)

        # Mock start time to be 5 seconds ago
        from datetime import UTC
        with patch.object(summary, "start_time", datetime.now(UTC)):
            import time
            time.sleep(0.1)  # Small delay to ensure duration > 0
            result = summary.generate()

        assert result["duration_seconds"] > 0
        assert isinstance(result["duration_seconds"], float)


class TestNoOpProgressTracker:
    """Test NoOpProgressTracker class."""

    def test_context_manager(self):




        """Test NoOpProgressTracker as context manager."""
        tracker = NoOpProgressTracker()

        with tracker as t:
            assert t is tracker
            t.update()  # Should not raise
            t.update(5)  # Should not raise

    def test_methods_do_nothing(self):




        """Test that all methods complete without error."""
        tracker = NoOpProgressTracker()

        # These should all complete without error
        tracker.update()
        tracker.update(10)
        tracker.finish()

        # Context manager methods
        assert tracker.__enter__() is tracker
        tracker.__exit__(None, None, None)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
