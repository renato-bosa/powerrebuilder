"""Extract coordinator wrapper for compatibility."""

from pathlib import Path
from typing import Any

from src.extract.coordinator import extract_pbls, extract_with_recovery


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
