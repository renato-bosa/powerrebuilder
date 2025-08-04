"""Security utilities for the extract module.

This module consolidates security-related functionality including:
- Path validation to prevent directory traversal attacks
- Resource limiting for memory and processing constraints
- Security coordinator for safe extraction operations
"""

from pathlib import Path
from typing import Any

# Import core security functionality
from src.core.resource_limits import ResourceLimits
from src.core.resource_limits import ResourceMonitor as ResourceLimiter
from src.core.security import (
    PathTraversalError,
    SecurityError,
)
from src.core.security import (
    PathValidator as BasePathValidator,
)

# Import extraction functions for the coordinator
from src.extract.coordinator import extract_pbls, extract_with_recovery


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


class ExtractCoordinator:
    """Coordinator for extraction operations."""

    def __init__(self, base_path: Path | None = None) -> None:
        """Initialize the coordinator.

        Args:
            base_path: Base path for extraction operations
        """
        self.base_path = base_path or Path.cwd()

    def extract(self, input_path: str, output_path: str, **kwargs) -> None:
        """Extract files from PBL/PBD.

        Args:
            input_path: Path to input file or directory
            output_path: Path to output directory
            **kwargs: Additional extraction options
        """
        extract_pbls(input_path, output_path, **kwargs)

    def extract_with_recovery(self, *args: Any, **kwargs: Any) -> Any:
        """Extract with recovery enabled."""
        return extract_with_recovery(*args, **kwargs)


__all__ = [
    # Extraction coordination
    "ExtractCoordinator",
    # Exceptions
    "PathTraversalError",
    # Path validation
    "PathValidator",
    # Resource limiting
    "ResourceLimiter",
    "ResourceLimits",
    "SecurityError",
]
