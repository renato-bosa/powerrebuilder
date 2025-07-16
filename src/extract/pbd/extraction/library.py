"""PBD Library extraction module."""

import logging
from pathlib import Path
from typing import Union

from src.extract.pbd.extractors.base import extract_pbl

logger = logging.getLogger(__name__)


class Library:
    """Library class for extracting PBD/PBL files."""

    def __init__(self, file_path: Union[str, Path]):
        """Initialize library with file path.

        Args:
            file_path: Path to PBD/PBL file
        """
        self.file_path = Path(file_path)
        self._entries = None

    def __enter__(self):
        """Context manager entry."""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        pass

    def __len__(self):
        """Return number of entries in library."""
        # TODO: Implement proper entry counting
        return 0

    def extract_all(self, output_dir: Union[str, Path], silent_progress: bool = False):
        """Extract all entries to output directory.

        Args:
            output_dir: Directory to extract files to
            silent_progress: Whether to suppress progress output
        """
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)

        try:
            # Use the existing extraction logic
            extract_pbl(
                self.file_path, 
                str(output_path), 
                show_progress=not silent_progress,
                extract_resources=True
            )
            logger.info(f"Successfully extracted entries from {self.file_path.name}")
        except Exception as e:
            logger.error(f"Failed to extract from {self.file_path.name}: {e}")
            raise