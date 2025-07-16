"""Tests for the main CLI interface."""

import logging
import sys
from pathlib import Path
from unittest.mock import patch

import pytest
from click.testing import CliRunner

# Add the parent directory to the path to import main
sys.path.insert(0, str(Path(__file__).parent.parent))
from main import cli


class TestCLI:
    """Test the main CLI interface."""

    @pytest.fixture
    def runner(self):


        """Create a CLI runner for testing."""
        return CliRunner()

    def test_cli_help(self, runner):




        """Test CLI help message."""
        result = runner.invoke(cli, ["--help"])
        assert result.exit_code == 0
        assert "SIME Finch: PowerBuilder Reverse Engineering Toolkit" in result.output
        assert "Commands:" in result.output
        assert "extract" in result.output
        assert "parse" in result.output
        assert "generate" in result.output
        assert "all" in result.output
        assert "clean-output" in result.output

    def test_cli_version(self, runner):




        """Test CLI version option."""
        with patch("main.metadata.version", return_value="0.1.0"):
            result = runner.invoke(cli, ["--version"])
            assert result.exit_code == 0
            assert "sime-finch, version 0.1.0" in result.output

    def test_cli_loglevel_option(self, runner):




        """Test CLI loglevel option."""
        with patch("main.logging.basicConfig") as mock_config:
            result = runner.invoke(cli, ["--loglevel", "DEBUG", "extract", "--help"])
            assert result.exit_code == 0
            # Check that logging was configured with DEBUG level
            mock_config.assert_called()
            call_args = mock_config.call_args
            assert call_args[1]["level"] == logging.DEBUG

    @patch("main.extract_pbls")
    def test_extract_command(self, mock_extract, runner):


        """Test extract command."""
        # Create a temporary directory for testing
        with runner.isolated_filesystem():
            input_dir = Path("input")
            output_dir = Path("output")
            input_dir.mkdir()

            result = runner.invoke(cli, ["extract", str(input_dir), str(output_dir)])

            assert result.exit_code == 0
            mock_extract.assert_called_once_with(
                str(input_dir),
                str(output_dir),
                enable_byte_recovery=False,
            )

    @patch("main.extract_pbls")
    def test_extract_command_with_options(self, mock_extract, runner):


        """Test extract command with options."""
        with runner.isolated_filesystem():
            input_dir = Path("input")
            output_dir = Path("output")
            input_dir.mkdir()

            result = runner.invoke(
                cli,
                [
                    "extract",
                    str(input_dir),
                    str(output_dir),
                    "--debug",
                    "--enable-byte-recovery",
                ],
            )

            assert result.exit_code == 0
            mock_extract.assert_called_once_with(
                str(input_dir),
                str(output_dir),
                enable_byte_recovery=True,
            )

    @patch("main.extract_pbls", side_effect=Exception("Test error"))
    def test_extract_command_error_handling(self, mock_extract, runner):


        """Test extract command error handling."""
        with runner.isolated_filesystem():
            input_dir = Path("input")
            output_dir = Path("output")
            input_dir.mkdir()

            result = runner.invoke(cli, ["extract", str(input_dir), str(output_dir)])

            assert result.exit_code == 1
            assert "Failed to extract: Test error" in result.output

    @patch("main.parse_powerbuilder_files")
    @patch("main.parse_database_schema")
    def test_parse_command(self, mock_parse_schema, mock_parse_files, runner):


        """Test parse command."""
        with runner.isolated_filesystem():
            input_dir = Path("input")
            output_dir = Path("output")
            input_dir.mkdir()

            result = runner.invoke(cli, ["parse", str(input_dir), str(output_dir)])

            assert result.exit_code == 0
            mock_parse_files.assert_called_once_with(str(input_dir), str(output_dir))
            mock_parse_schema.assert_called_once_with(str(input_dir), str(output_dir))

    @patch("main.parse_powerbuilder_files", side_effect=ImportError("Missing module"))
    def test_parse_command_import_error(self, mock_parse_files, runner):


        """Test parse command with import error."""
        with runner.isolated_filesystem():
            input_dir = Path("input")
            output_dir = Path("output")
            input_dir.mkdir()

            result = runner.invoke(cli, ["parse", str(input_dir), str(output_dir)])

            assert result.exit_code == 1
            assert "Failed to import parsing modules" in result.output

    @patch("main.generate_models")
    @patch("main.generate_services")
    @patch("main.generate_frontend")
    def test_generate_command(self, mock_frontend, mock_services, mock_models, runner):


        """Test generate command."""
        result = runner.invoke(cli, ["generate"])

        assert result.exit_code == 0
        mock_models.assert_called_once()
        mock_services.assert_called_once()
        mock_frontend.assert_called_once()

    @patch("main.generate_models", side_effect=Exception("Generation failed"))
    def test_generate_command_error(self, mock_models, runner):


        """Test generate command error handling."""
        result = runner.invoke(cli, ["generate"])

        assert result.exit_code == 1
        assert "Failed to generate code: Generation failed" in result.output

    @patch("main.extract_pbls")
    @patch("main.parse_powerbuilder_files")
    @patch("main.parse_database_schema")
    @patch("main.decompile_directory")
    @patch("main.generate_models")
    @patch("main.generate_services")
    @patch("main.generate_frontend")
    def test_all_command(
        self,
        mock_frontend,
        mock_services,
        mock_models,
        mock_decompile,
        mock_parse_schema,
        mock_parse_files,
        mock_extract,
        runner,
    ):


        """Test all command (full pipeline)."""
        with runner.isolated_filesystem():
            input_dir = Path("input")
            output_dir = Path("output")
            input_dir.mkdir()

            result = runner.invoke(
                cli,
                [
                    "all",
                    "--pbl-input-dir",
                    str(input_dir),
                    "--base-output-dir",
                    str(output_dir),
                ],
            )

            assert result.exit_code == 0
            # Check that all pipeline steps were called
            mock_extract.assert_called_once()
            mock_parse_files.assert_called_once()
            mock_parse_schema.assert_called_once()
            mock_decompile.assert_called_once()
            mock_models.assert_called_once()
            mock_services.assert_called_once()
            mock_frontend.assert_called_once()

    def test_clean_output_dry_run(self, runner):




        """Test clean_output command in dry run mode."""
        with runner.isolated_filesystem():
            # Create test directory structure
            output_dir = Path("data/output/current/extracted/recovery")
            output_dir.mkdir(parents=True)
            (output_dir / "test_file.txt").touch()

            result = runner.invoke(cli, ["clean_output", "data/output/current/extracted/recovery"])

            assert result.exit_code == 0
            assert "Listing contents" in result.output
            assert "dry run" in result.output
            assert "test_file.txt" in result.output
            # Directory should still exist
            assert output_dir.exists()

    @patch("main.shutil.rmtree")
    def test_clean_output_force(self, mock_rmtree, runner):


        """Test clean_output command with force flag."""
        with runner.isolated_filesystem():
            # Create test directory
            output_dir = Path("data/output/current/extracted/recovery")
            output_dir.mkdir(parents=True)

            result = runner.invoke(
                cli, ["clean_output", "data/output/current/extracted/recovery", "--force"],
            )

            assert result.exit_code == 0
            assert "Deleting" in result.output
            mock_rmtree.assert_called_once()

    def test_clean_output_no_target(self, runner):




        """Test clean_output command with no target."""
        result = runner.invoke(cli, ["clean_output"])

        assert result.exit_code == 0
        assert "No target directory specified" in result.output
        assert "Common large directories" in result.output

    def test_clean_output_full_flags(self, runner):




        """Test clean_output command with full flags."""
        with runner.isolated_filesystem():
            # Create test directories
            recovery_dir = Path("data/output/current/extracted/recovery")
            Path("data/output/current/extracted")
            decompiled_dir = Path("data/output/current/decompiled")
            parsed_dir = Path("data/output/current/parsed")

            for d in [recovery_dir, decompiled_dir, parsed_dir]:
                d.mkdir(parents=True)

            result = runner.invoke(
                cli,
                [
                    "clean_output",
                    "--full-recovery",
                    "--full-decompiled",
                    "--full-parsed",
                ],
            )

            assert result.exit_code == 0
            assert "data/output/current/extracted/recovery" in result.output
            assert "data/output/current/decompiled" in result.output
            assert "data/output/current/parsed" in result.output

    def test_clean_output_nonexistent_directory(self, runner):




        """Test clean_output with nonexistent directory."""
        result = runner.invoke(cli, ["clean_output", "nonexistent/directory"])

        assert result.exit_code == 0
        assert "Directory not found" in result.output

    def test_cli_traceback_option(self, runner):




        """Test CLI traceback option."""
        with patch("main.extract_pbls", side_effect=Exception("Test error")):
            with runner.isolated_filesystem():
                input_dir = Path("input")
                input_dir.mkdir()

                # Without traceback option
                result = runner.invoke(cli, ["extract", str(input_dir), "output"])
                assert result.exit_code == 1
                assert "Test error" in result.output

                # With traceback option
                result = runner.invoke(
                    cli, ["--traceback", "extract", str(input_dir), "output"],
                )
                assert result.exit_code == 1
                # The traceback should be shown (this will raise the exception)
                assert result.exception is not None


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
