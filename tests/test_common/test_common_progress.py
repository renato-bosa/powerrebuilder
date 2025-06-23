"""Tests for common.progress module."""

import time
from unittest.mock import MagicMock, Mock, patch

import pytest

from common.progress import (
    PipelineProgress,
    TransferSpeedColumn,
    create_simple_progress,
    track_progress,
)


class TestTransferSpeedColumn:
    """Test TransferSpeedColumn class."""

    def test_render_mb_per_second(self):




        """Test rendering speed in MB/s."""
        column = TransferSpeedColumn()
        task = Mock()
        task.fields = {"speed": 5 * 1024 * 1024}  # 5 MB/s

        text = column.render(task)

        assert text.plain == "5.0 MB/s"
        assert text.style == "bright_green"

    def test_render_kb_per_second(self):




        """Test rendering speed in KB/s."""
        column = TransferSpeedColumn()
        task = Mock()
        task.fields = {"speed": 500 * 1024}  # 500 KB/s

        text = column.render(task)

        assert text.plain == "500.0 KB/s"
        assert text.style == "green"

    def test_render_bytes_per_second(self):




        """Test rendering speed in B/s."""
        column = TransferSpeedColumn()
        task = Mock()
        task.fields = {"speed": 500}  # 500 B/s

        text = column.render(task)

        assert text.plain == "500 B/s"
        assert text.style == "yellow"

    def test_render_zero_speed(self):




        """Test rendering zero speed."""
        column = TransferSpeedColumn()
        task = Mock()
        task.fields = {"speed": 0}

        text = column.render(task)

        assert text.plain == ""
        assert text.style == "dim"

    def test_render_no_speed_field(self):




        """Test rendering when speed field is missing."""
        column = TransferSpeedColumn()
        task = Mock()
        task.fields = {}

        text = column.render(task)

        assert text.plain == ""
        assert text.style == "dim"


class TestPipelineProgress:
    """Test PipelineProgress class."""

    @patch("common.progress.Console")
    def test_initialization_with_console(self, mock_console_class):


        """Test initialization with provided console."""
        mock_console = MagicMock()
        progress = PipelineProgress(console=mock_console)

        assert progress.console == mock_console
        assert progress.start_time > 0
        assert progress.main_task_id is None
        assert progress.file_task_id is None
        assert progress.current_operation_id is None

    @patch("common.progress.Console")
    def test_initialization_without_console(self, mock_console_class):


        """Test initialization without console (creates new)."""
        progress = PipelineProgress()

        mock_console_class.assert_called_once()
        assert progress.console == mock_console_class.return_value

    @patch("common.progress.Live")
    @patch("common.progress.Layout")
    def test_pipeline_context(self, mock_layout_class, mock_live_class):


        """Test pipeline context manager."""
        progress = PipelineProgress()
        mock_layout = MagicMock()
        mock_layout_class.return_value = mock_layout

        with progress.pipeline_context(total_steps=3) as ctx:
            assert ctx == progress
            assert progress.main_task_id is not None

        # Verify layout setup
        mock_layout.split_column.assert_called_once()
        mock_live_class.assert_called_once()

    def test_create_footer(self):




        """Test footer creation."""
        progress = PipelineProgress()

        # Test running footer
        footer = progress._create_footer(final=False)
        # Access the renderable content from the Panel
        assert hasattr(footer, "renderable")
        assert "Running" in str(footer.renderable)

        # Test final footer
        footer = progress._create_footer(final=True)
        assert hasattr(footer, "renderable")
        assert "Complete" in str(footer.renderable)

    def test_create_footer_time_formatting(self):




        """Test footer time formatting."""
        progress = PipelineProgress()

        # Test seconds only
        progress.start_time = time.time() - 30
        footer = progress._create_footer()
        footer_text = str(footer.renderable)
        # Should show approximately 30 seconds (allow for small timing differences)
        assert "30" in footer_text or "29" in footer_text or "31" in footer_text

        # Test minutes and seconds
        progress.start_time = time.time() - 90
        footer = progress._create_footer()
        footer_text = str(footer.renderable)
        assert "1m" in footer_text
        # Should show approximately 30 seconds (allow for small timing differences)
        assert ("30s" in footer_text or "29s" in footer_text or 
                "31s" in footer_text)

    def test_start_step(self):




        """Test starting a pipeline step."""
        progress = PipelineProgress()
        progress.main_task_id = 1
        progress.pipeline_progress = MagicMock()

        progress.start_step("Test Step", 2)

        progress.pipeline_progress.update.assert_called_once_with(
            1,
            description="Step 2: Test Step",
            completed=1,
        )

    def test_complete_step(self):




        """Test completing a pipeline step."""
        progress = PipelineProgress()
        progress.main_task_id = 1
        progress.pipeline_progress = MagicMock()

        progress.complete_step(3)

        progress.pipeline_progress.update.assert_called_once_with(
            1,
            completed=3,
        )

    def test_file_extraction_context(self):




        """Test file extraction context manager."""
        progress = PipelineProgress()
        progress.file_progress = MagicMock()
        mock_task_id = 42
        progress.file_progress.add_task.return_value = mock_task_id

        with progress.file_extraction_context(total_files=10) as task_id:
            assert task_id == mock_task_id
            assert progress.file_task_id == mock_task_id

        # Verify task creation and completion
        progress.file_progress.add_task.assert_called_once_with(
            "Extracting files", total=10, speed=0,
        )
        progress.file_progress.update.assert_called_once_with(
            mock_task_id, description="Extraction complete",
        )

    def test_update_file_progress_with_file(self):




        """Test updating file progress with current file."""
        progress = PipelineProgress()
        progress.file_task_id = 1
        progress.file_progress = MagicMock()

        progress.update_file_progress(5, "/path/to/file.pbd", 1024000)

        progress.file_progress.update.assert_called_once_with(
            1,
            completed=5,
            description="Extracting: file.pbd",
            speed=1024000,
        )

    def test_update_file_progress_without_file(self):




        """Test updating file progress without current file."""
        progress = PipelineProgress()
        progress.file_task_id = 1
        progress.file_progress = MagicMock()

        progress.update_file_progress(5, "", 0)

        progress.file_progress.update.assert_called_once_with(
            1,
            completed=5,
            description="Extracting files",
            speed=0,
        )

    def test_update_file_progress_no_task(self):




        """Test updating file progress when no task exists."""
        progress = PipelineProgress()
        progress.file_task_id = None
        progress.file_progress = MagicMock()

        # Should not raise error
        progress.update_file_progress(5, "file.pbd", 1000)

        # Should not call update
        progress.file_progress.update.assert_not_called()

    def test_operation_context(self):




        """Test operation context manager."""
        progress = PipelineProgress()
        progress.operation_progress = MagicMock()
        mock_task_id = 99
        progress.operation_progress.add_task.return_value = mock_task_id

        with progress.operation_context("Test Operation", total=50) as task_id:
            assert task_id == mock_task_id
            assert progress.current_operation_id == mock_task_id

        # Verify task creation and removal
        progress.operation_progress.add_task.assert_called_once_with(
            "Test Operation", total=50,
        )
        progress.operation_progress.remove_task.assert_called_once_with(
            mock_task_id,
        )
        assert progress.current_operation_id is None

    def test_update_operation_with_all_params(self):




        """Test updating operation with all parameters."""
        progress = PipelineProgress()
        progress.current_operation_id = 1
        progress.operation_progress = MagicMock()

        progress.update_operation(completed=25, description="New Description")

        progress.operation_progress.update.assert_called_once_with(
            1,
            completed=25,
            description="New Description",
        )

    def test_update_operation_partial_params(self):




        """Test updating operation with partial parameters."""
        progress = PipelineProgress()
        progress.current_operation_id = 1
        progress.operation_progress = MagicMock()

        # Only completed
        progress.update_operation(completed=10)
        progress.operation_progress.update.assert_called_with(1, completed=10)

        # Only description
        progress.update_operation(description="Updated")
        progress.operation_progress.update.assert_called_with(1, description="Updated")

    def test_update_operation_no_task(self):




        """Test updating operation when no task exists."""
        progress = PipelineProgress()
        progress.current_operation_id = None
        progress.operation_progress = MagicMock()

        # Should not raise error
        progress.update_operation(completed=5, description="Test")

        # Should not call update
        progress.operation_progress.update.assert_not_called()


class TestUtilityFunctions:
    """Test utility functions."""

    @patch("common.progress.Console")
    @patch("common.progress.Progress")
    def test_create_simple_progress(self, mock_progress_class, mock_console_class):


        """Test creating simple progress bar."""
        result = create_simple_progress()

        mock_progress_class.assert_called_once()
        mock_console_class.assert_called_once()
        assert result == mock_progress_class.return_value

    @patch("common.progress.create_simple_progress")
    def test_track_progress_determinate(self, mock_create_progress):


        """Test track_progress context manager with determinate progress."""
        mock_progress = MagicMock()
        mock_create_progress.return_value = mock_progress
        mock_task_id = 123
        mock_progress.add_task.return_value = mock_task_id

        with track_progress("Test Task", total=100) as task:
            # Test update method
            task.update(advance=10, extra_field="value")
            mock_progress.update.assert_called_with(
                mock_task_id, advance=10, extra_field="value",
            )

            # Test set_description method
            task.set_description("New Description")
            mock_progress.update.assert_called_with(
                mock_task_id, description="New Description",
            )

        # Verify task creation
        mock_progress.add_task.assert_called_once_with("Test Task", total=100)

    @patch("common.progress.create_simple_progress")
    def test_track_progress_indeterminate(self, mock_create_progress):


        """Test track_progress context manager with indeterminate progress."""
        mock_progress = MagicMock()
        mock_create_progress.return_value = mock_progress
        mock_task_id = 456
        mock_progress.add_task.return_value = mock_task_id

        with track_progress("Test Task") as task:
            task.update()  # Default advance=1
            mock_progress.update.assert_called_with(
                mock_task_id, advance=1,
            )

        # Verify task creation with None total
        mock_progress.add_task.assert_called_once_with("Test Task", total=None)


class TestExampleUsage:
    """Test the example usage function."""

    @patch("time.sleep")
    @patch("common.progress.PipelineProgress")
    def test_example_usage_runs(self, mock_pipeline_class, mock_sleep):


        """Test that example_usage runs without errors."""
        # This mainly ensures the example code is valid
        from common.progress import example_usage

        # Mock the pipeline instance and its methods
        mock_pipeline = MagicMock()
        mock_pipeline_class.return_value = mock_pipeline

        # Create a mock context that returns the pipeline
        mock_context = MagicMock()
        mock_context.__enter__ = MagicMock(return_value=mock_pipeline)
        mock_context.__exit__ = MagicMock(return_value=None)
        mock_pipeline.pipeline_context.return_value = mock_context

        # Mock file extraction context
        mock_file_context = MagicMock()
        mock_file_context.__enter__ = MagicMock(return_value=1)
        mock_file_context.__exit__ = MagicMock(return_value=None)
        mock_pipeline.file_extraction_context.return_value = mock_file_context

        # Mock operation context
        mock_op_context = MagicMock()
        mock_op_context.__enter__ = MagicMock(return_value=2)
        mock_op_context.__exit__ = MagicMock(return_value=None)
        mock_pipeline.operation_context.return_value = mock_op_context

        # Run the example
        example_usage()

        # Verify some key method calls
        assert mock_pipeline.start_step.call_count >= 5
        assert mock_pipeline.complete_step.call_count >= 5
        assert mock_pipeline.update_file_progress.call_count == 54
        assert mock_pipeline.update_operation.call_count == 500


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
