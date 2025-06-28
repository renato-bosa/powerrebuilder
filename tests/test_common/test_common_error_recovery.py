"""Tests for common.error_recovery module."""

import json
import logging
import tempfile
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from common.utils.error_recovery import (
    FileErrorCollector,
    PipelineCheckpoint,
    ResourceChecker,
    ResourceError,
    RetryError,
    retry,
)
from common.exceptions import ExtractError, ParseError


class TestExceptions:
    """Test custom exception classes."""

    def test_resource_error(self):




        """Test ResourceError exception."""
        error = ResourceError("Not enough disk space")
        assert str(error) == "Not enough disk space"
        assert isinstance(error, Exception)

    def test_retry_error(self):




        """Test RetryError exception."""
        error = RetryError("All retries failed")
        assert str(error) == "All retries failed"
        assert isinstance(error, Exception)


class TestRetryDecorator:
    """Test retry decorator functionality."""

    def test_successful_call_no_retry(self):




        """Test that successful calls don't retry."""
        call_count = 0

        @retry(max_attempts=3)
        def successful_func():

            nonlocal call_count
            call_count += 1
            return "success"

        result = successful_func()
        assert result == "success"
        assert call_count == 1

    def test_retry_on_exception(self):




        """Test retry on exception."""
        call_count = 0

        @retry(max_attempts=3, backoff_factor=0.1)  # Small backoff for fast tests
        def failing_func():

            nonlocal call_count
            call_count += 1
            if call_count < 3:
                raise ValueError("Temporary failure")
            return "success"

        result = failing_func()
        assert result == "success"
        assert call_count == 3

    def test_retry_exhausted(self):




        """Test when all retries are exhausted."""
        call_count = 0

        @retry(max_attempts=3, backoff_factor=0.1)
        def always_failing_func():

            nonlocal call_count
            call_count += 1
            raise ValueError("Always fails")

        with pytest.raises(RetryError) as exc_info:
            always_failing_func()

        assert "Failed after 3 attempts" in str(exc_info.value)
        assert call_count == 3

    def test_retry_specific_exceptions(self):




        """Test retry only catches specified exceptions."""
        @retry(max_attempts=3, exceptions=(ValueError,))
        def specific_exception_func():

            raise TypeError("Not retried")

        with pytest.raises(TypeError):
            specific_exception_func()

    def test_retry_with_custom_logger(self):




        """Test retry with custom logger."""
        mock_logger = MagicMock()
        call_count = 0

        @retry(max_attempts=2, backoff_factor=0.1, logger=mock_logger)
        def func_with_logger():

            nonlocal call_count
            call_count += 1
            if call_count == 1:
                raise ValueError("First failure")
            return "success"

        result = func_with_logger()
        assert result == "success"
        assert mock_logger.warning.called

    def test_retry_preserves_function_metadata(self):




        """Test that retry decorator preserves function metadata."""
        @retry(max_attempts=3)
        def documented_func():


            """This is a documented function."""
            return "result"

        assert documented_func.__name__ == "documented_func"
        assert documented_func.__doc__ == "This is a documented function."


class TestFileErrorCollector:
    """Test FileErrorCollector class."""

    def test_initialization(self):




        """Test collector initialization."""
        collector = FileErrorCollector()
        assert collector.errors == {
            "extract": [],
            "parse": [],
            "decompile": [],
            "generate": [],
        }
        assert collector.warnings == {
            "extract": [],
            "parse": [],
            "decompile": [],
            "generate": [],
        }

    def test_add_error(self):




        """Test adding errors."""
        collector = FileErrorCollector()
        error = ExtractError("Failed to extract")

        collector.add_error("extract", "file1.pbd", error)
        assert len(collector.errors["extract"]) == 1
        assert collector.errors["extract"][0] == ("file1.pbd", error)

    def test_add_warning(self):




        """Test adding warnings."""
        collector = FileErrorCollector()

        collector.add_warning("parse", "file2.pb", "Deprecated syntax")
        assert len(collector.warnings["parse"]) == 1
        assert collector.warnings["parse"][0] == ("file2.pb", "Deprecated syntax")

    def test_has_errors(self):




        """Test checking for errors."""
        collector = FileErrorCollector()
        assert not collector.has_errors()
        assert not collector.has_errors("extract")

        collector.add_error("extract", "file.pbd", Exception("Error"))
        assert collector.has_errors()
        assert collector.has_errors("extract")
        assert not collector.has_errors("parse")

    def test_get_error_summary(self):




        """Test getting error summary."""
        collector = FileErrorCollector()
        collector.add_error("extract", "file1.pbd", ExtractError("Error 1"))
        collector.add_error("extract", "file2.pbd", ExtractError("Error 2"))
        collector.add_error("parse", "file3.pb", ParseError("Error 3"))
        collector.add_warning("generate", "file4.dart", "Warning 1")

        summary = collector.get_error_summary()
        assert summary["errors"]["extract"] == 2
        assert summary["errors"]["parse"] == 1
        assert summary["errors"]["decompile"] == 0
        assert summary["errors"]["generate"] == 0
        assert summary["warnings"]["generate"] == 1
        assert summary["total_errors"] == 3
        assert summary["total_warnings"] == 1

    def test_log_summary(self, caplog):




        """Test logging summary."""
        collector = FileErrorCollector()
        # Add multiple errors to test truncation
        for i in range(5):
            collector.add_error("extract", f"file{i}.pbd", ExtractError(f"Error {i}"))
        collector.add_warning("parse", "file.pb", "Warning")

        with caplog.at_level(logging.ERROR):
            collector.log_summary()

        assert "Pipeline completed with 5 errors" in caplog.text
        assert "extract: 5 errors" in caplog.text
        assert "... and 2 more" in caplog.text  # Only shows first 3 errors


class TestResourceChecker:
    """Test ResourceChecker class."""

    def test_check_disk_space_sufficient(self):




        """Test disk space check with sufficient space."""
        with patch("shutil.disk_usage") as mock_disk_usage:
            # Mock 10GB free space
            mock_disk_usage.return_value = MagicMock(free=10 * 1024**3)

            # Should not raise
            ResourceChecker.check_disk_space(Path("/tmp"))

    def test_check_disk_space_insufficient(self):




        """Test disk space check with insufficient space."""
        with patch("shutil.disk_usage") as mock_disk_usage:
            # Mock 0.5GB free space
            mock_disk_usage.return_value = MagicMock(free=0.5 * 1024**3)

            with pytest.raises(ResourceError) as exc_info:
                ResourceChecker.check_disk_space(Path("/tmp"))

            assert "Insufficient disk space" in str(exc_info.value)
            assert "0.50GB free" in str(exc_info.value)

    def test_check_disk_space_error_handling(self, caplog):




        """Test disk space check error handling."""
        with patch("shutil.disk_usage", side_effect=OSError("Disk error")):
            with caplog.at_level(logging.WARNING):
                ResourceChecker.check_disk_space(Path("/tmp"))

            assert "Could not check disk space" in caplog.text

    def test_check_memory_sufficient(self):




        """Test memory check with sufficient memory."""
        with patch("psutil.virtual_memory") as mock_memory:
            # Mock 2GB available memory
            mock_memory.return_value = MagicMock(available=2 * 1024**3)

            # Should not raise
            ResourceChecker.check_memory()

    def test_check_memory_insufficient(self):




        """Test memory check with insufficient memory."""
        with patch("psutil.virtual_memory") as mock_memory:
            # Mock 0.3GB available memory
            mock_memory.return_value = MagicMock(available=0.3 * 1024**3)

            with pytest.raises(ResourceError) as exc_info:
                ResourceChecker.check_memory()

            assert "Insufficient memory" in str(exc_info.value)
            assert "0.30GB available" in str(exc_info.value)

    def test_check_memory_error_handling(self, caplog):




        """Test memory check error handling."""
        with patch("psutil.virtual_memory", side_effect=OSError("Memory error")):
            with caplog.at_level(logging.WARNING):
                ResourceChecker.check_memory()

            assert "Could not check memory" in caplog.text

    def test_check_all(self):




        """Test checking all resources."""
        with patch.object(ResourceChecker, "check_disk_space") as mock_disk:
            with patch.object(ResourceChecker, "check_memory") as mock_memory:
                ResourceChecker.check_all(Path("/tmp"))

                mock_disk.assert_called_once_with(Path("/tmp"))
                mock_memory.assert_called_once()


class TestPipelineCheckpoint:
    """Test PipelineCheckpoint class."""

    def test_initialization(self):




        """Test checkpoint initialization."""
        with tempfile.TemporaryDirectory() as tmpdir:
            checkpoint_dir = Path(tmpdir) / "checkpoints"
            checkpoint = PipelineCheckpoint(checkpoint_dir)

            assert checkpoint_dir.exists()
            assert checkpoint.checkpoint_file == checkpoint_dir / "pipeline_checkpoint.json"

    def test_save_checkpoint(self):




        """Test saving checkpoint."""
        with tempfile.TemporaryDirectory() as tmpdir:
            checkpoint = PipelineCheckpoint(Path(tmpdir))

            processed = ["file1.pb", "file2.pb"]
            failed = ["file3.pb"]
            state = {"current_index": 3, "total": 10}

            checkpoint.save("extract", processed, failed, state)

            # Verify file was created
            assert checkpoint.checkpoint_file.exists()

            # Verify content
            with open(checkpoint.checkpoint_file, "r") as f:
                data = json.load(f)

            assert data["stage"] == "extract"
            assert data["processed_files"] == processed
            assert data["failed_files"] == failed
            assert data["state"] == state
            assert "timestamp" in data

    def test_load_checkpoint(self):




        """Test loading checkpoint."""
        with tempfile.TemporaryDirectory() as tmpdir:
            checkpoint = PipelineCheckpoint(Path(tmpdir))

            # Save checkpoint
            checkpoint.save("parse", ["file1.pb"], [], {"index": 1})

            # Load checkpoint
            data = checkpoint.load()
            assert data is not None
            assert data["stage"] == "parse"
            assert data["processed_files"] == ["file1.pb"]

    def test_load_nonexistent_checkpoint(self):




        """Test loading when no checkpoint exists."""
        with tempfile.TemporaryDirectory() as tmpdir:
            checkpoint = PipelineCheckpoint(Path(tmpdir))

            data = checkpoint.load()
            assert data is None

    def test_load_corrupted_checkpoint(self, caplog):




        """Test loading corrupted checkpoint."""
        with tempfile.TemporaryDirectory() as tmpdir:
            checkpoint = PipelineCheckpoint(Path(tmpdir))

            # Write corrupted JSON
            with open(checkpoint.checkpoint_file, "w") as f:
                f.write("{ corrupted json")

            with caplog.at_level(logging.WARNING):
                data = checkpoint.load()

            assert data is None
            assert "Could not load checkpoint" in caplog.text

    def test_clear_checkpoint(self):




        """Test clearing checkpoint."""
        with tempfile.TemporaryDirectory() as tmpdir:
            checkpoint = PipelineCheckpoint(Path(tmpdir))

            # Save checkpoint
            checkpoint.save("generate", [], [], {})
            assert checkpoint.checkpoint_file.exists()

            # Clear checkpoint
            checkpoint.clear()
            assert not checkpoint.checkpoint_file.exists()

    def test_clear_nonexistent_checkpoint(self):




        """Test clearing when no checkpoint exists."""
        with tempfile.TemporaryDirectory() as tmpdir:
            checkpoint = PipelineCheckpoint(Path(tmpdir))

            # Should not raise
            checkpoint.clear()

    def test_save_checkpoint_error_handling(self, caplog):




        """Test save checkpoint error handling."""
        with tempfile.TemporaryDirectory() as tmpdir:
            checkpoint = PipelineCheckpoint(Path(tmpdir))

            # Make directory read-only to cause save error
            import os
            os.chmod(tmpdir, 0o444)

            try:
                with caplog.at_level(logging.WARNING):
                    checkpoint.save("test", [], [], {})

                assert "Could not save checkpoint" in caplog.text
            finally:
                # Restore permissions
                os.chmod(tmpdir, 0o755)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
