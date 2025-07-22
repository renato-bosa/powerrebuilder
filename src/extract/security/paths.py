"""Path validation utilities for extract module."""

from pathlib import Path

from src.core.security import PathValidator as BasePathValidator


class PathValidator:
    """Instance-based wrapper for path validation."""

    def __init__(self, base_dir: str | Path) -> None:
        """Initialize with a base directory.

        Args:
            base_dir: The base directory for validation
        """
        self.base_dir = Path(base_dir).resolve()

    def validate_path(self, path: str | Path) -> Path:
        """Validate a path is safe and within the base directory.

        Args:
            path: The path to validate

        Returns:
            The validated absolute path

        Raises:
            ValueError: If the path is unsafe
        """
        return BasePathValidator.validate_path(path, self.base_dir)

    @classmethod
    def validate_filename(cls, filename: str) -> str:
        """Validate a filename is safe.

        Args:
            filename: The filename to validate

        Returns:
            The validated filename

        Raises:
            ValueError: If the filename is unsafe
        """
        return BasePathValidator.validate_filename(filename)


__all__ = ["PathValidator"]
