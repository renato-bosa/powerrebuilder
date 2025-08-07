"""Output directory handling utilities for PowerRebuilder.

This module provides utilities for checking and managing output directories,
including overwrite confirmation and safe directory creation.
"""

import logging
import sys
from pathlib import Path

import click

logger = logging.getLogger(__name__)


class OutputDirectoryHandler:
    """Handles output directory creation and overwrite logic."""

    def __init__(self, allow_overwrite: bool = True, interactive: bool = True) -> None:
        """Initialize the output directory handler.

        Args:
            allow_overwrite: Whether to allow overwriting existing files
            interactive: Whether to prompt user for confirmation
        """
        self.allow_overwrite = allow_overwrite
        self.interactive = interactive

    def prepare_output_directory(
        self,
        output_path: Path,
        force_overwrite: bool = False,
        stage_name: str = "operation",
    ) -> bool:
        """Prepare an output directory, handling existing files appropriately.

        Args:
            output_path: Path to the output directory
            force_overwrite: If True, skip confirmation and overwrite
            stage_name: Name of the operation (for user messages)

        Returns:
            True if directory is ready to use, False if operation should be cancelled
        """
        if not output_path.exists():
            # Directory doesn't exist, create it
            logger.info("Creating output directory: %s", output_path)
            output_path.mkdir(parents=True, exist_ok=True)
            return True

        # Directory exists, check if it has files
        existing_files = self._get_existing_files(output_path)

        if not existing_files:
            # Directory exists but is empty
            logger.info("Using existing empty directory: %s", output_path)
            return True

        # Directory has files - handle overwrite logic
        return self._handle_existing_files(
            output_path, existing_files, force_overwrite, stage_name
        )

    def _get_existing_files(self, directory: Path) -> list[Path]:
        """Get list of existing files in directory (recursively).

        Args:
            directory: Directory to check

        Returns:
            List of existing file paths
        """
        if not directory.exists():
            return []

        existing_files = []
        try:
            for item in directory.rglob("*"):
                if item.is_file():
                    existing_files.append(item)
        except (OSError, PermissionError) as e:
            logger.warning("Could not fully scan directory {directory}: %s", e)
            # Still return what we found

        return existing_files

    def _handle_existing_files(
        self,
        output_path: Path,
        existing_files: list[Path],
        force_overwrite: bool,
        stage_name: str,
    ) -> bool:
        """Handle the case where output directory has existing files.

        Args:
            output_path: Output directory path
            existing_files: List of existing files
            force_overwrite: Whether to force overwrite without prompting
            stage_name: Name of the operation

        Returns:
            True if should proceed, False if should cancel
        """
        file_count = len(existing_files)

        if not self.allow_overwrite:
            logger.error(
                "Output directory %s contains %s files, but overwrite is disabled (--no-overwrite flag was used).",
                output_path,
                file_count,
            )
            self._suggest_alternative_path(output_path, stage_name)
            return False

        if force_overwrite:
            logger.warning(
                "Force overwrite enabled. Will overwrite %s existing files in %s",
                file_count,
                output_path,
            )
            return True

        # Interactive confirmation
        if self.interactive and sys.stdin.isatty():
            return self._prompt_user_confirmation(
                output_path, existing_files, stage_name
            )
        # Non-interactive mode - default to overwrite with warning
        logger.warning(
            "Output directory %s contains %s files. Non-interactive mode: will overwrite existing files.",
            output_path,
            file_count,
        )
        return True

    def _prompt_user_confirmation(
        self, output_path: Path, existing_files: list[Path], stage_name: str
    ) -> bool:
        """Prompt user for confirmation about overwriting files.

        Args:
            output_path: Output directory path
            existing_files: List of existing files
            stage_name: Name of the operation

        Returns:
            True if user confirms, False otherwise
        """
        file_count = len(existing_files)

        click.echo()
        click.echo(
            click.style(
                "⚠️  Output directory already contains files:", fg="yellow", bold=True
            )
        )
        click.echo(f"   Directory: {output_path}")
        click.echo(f"   Files: {file_count}")

        # Show a few example files
        if existing_files:
            click.echo("   Examples:")
            for _i, file_path in enumerate(existing_files[:5]):
                rel_path = file_path.relative_to(output_path)
                click.echo(f"     - {rel_path}")
            if len(existing_files) > 5:
                click.echo(f"     ... and {len(existing_files) - 5} more files")

        click.echo()
        click.echo("Options:")
        click.echo("  [o] Overwrite existing files (default)")
        click.echo("  [n] Cancel and choose different directory")
        click.echo("  [a] Show alternative directory suggestions")
        click.echo()

        while True:
            choice = click.prompt(
                "How would you like to proceed?",
                type=click.Choice(["o", "n", "a"], case_sensitive=False),
                default="o",
                show_default=True,
            )

            if choice.lower() == "o":
                logger.info("User confirmed overwrite of %s files", file_count)
                return True
            if choice.lower() == "n":
                logger.info("User cancelled operation")
                return False
            if choice.lower() == "a":
                self._suggest_alternative_path(output_path, stage_name)
                continue  # Ask again

    def _suggest_alternative_path(self, original_path: Path, stage_name: str) -> None:
        """Suggest alternative output paths to the user.

        Args:
            original_path: The original output path that has conflicts
            stage_name: Name of the operation
        """
        from datetime import datetime

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

        suggestions = [
            original_path.parent / f"{original_path.name}_{timestamp}",
            original_path.parent / f"{original_path.name}_new",
            original_path.parent / f"{stage_name}_output_{timestamp}",
        ]

        click.echo()
        click.echo(click.style("Alternative output directories:", fg="blue", bold=True))
        for i, suggestion in enumerate(suggestions, 1):
            exists_marker = " (exists)" if suggestion.exists() else " (new)"
            click.echo(f"  {i}. {suggestion}{exists_marker}")

        click.echo()
        click.echo("You can restart the command with one of these directories:")
        click.echo(f"  Example: ... --output-dir {suggestions[0]}")

    def get_safe_output_path(self, base_path: Path, prefix: str = "output") -> Path:
        """Generate a safe output path that doesn't conflict with existing files.

        Args:
            base_path: Base directory to create output in
            prefix: Prefix for the output directory name

        Returns:
            Path that is safe to use for output
        """
        from datetime import datetime

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        counter = 1

        while True:
            if counter == 1:
                candidate = base_path / f"{prefix}_{timestamp}"
            else:
                candidate = base_path / f"{prefix}_{timestamp}_{counter}"

            if not candidate.exists():
                return candidate

            counter += 1
            if counter > 100:  # Safety limit
                # Fall back to a unique name
                import uuid

                unique_id = str(uuid.uuid4())[:8]
                return base_path / f"{prefix}_{unique_id}"


def check_and_prepare_output_directory(
    output_path: str | Path,
    allow_overwrite: bool = True,
    force_overwrite: bool = False,
    interactive: bool = True,
    stage_name: str = "operation",
) -> tuple[Path, bool]:
    """Convenience function to check and prepare an output directory.

    Args:
        output_path: Output directory path
        allow_overwrite: Whether overwriting is allowed
        force_overwrite: Whether to force overwrite without prompting
        interactive: Whether to use interactive prompts
        stage_name: Name of the operation (for messages)

    Returns:
        Tuple of (prepared_path, should_proceed)
    """
    path = Path(output_path)
    handler = OutputDirectoryHandler(allow_overwrite, interactive)

    should_proceed = handler.prepare_output_directory(path, force_overwrite, stage_name)

    return path, should_proceed
