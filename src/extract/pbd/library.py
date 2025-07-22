"""PBD Library extraction module."""

import logging
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)


class Library:
    """Library class for extracting PBD/PBL files."""

    def __init__(self, file_path: str | Path) -> None:
        """Initialize library with file path.

        Args:
            file_path: Path to PBD/PBL file
        """
        self.file_path = Path(file_path)
        self._entries = None
        self._entry_count = 0
        self._processed_count = 0

    def __enter__(self) -> "Library":
        """Context manager entry."""
        # Initialize entry count by scanning the file
        self._scan_entries()
        return self

    def __exit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        """Context manager exit."""
        if exc_type is None:
            # Log statistics on successful completion
            logger.info(
                "Library extraction completed: %d/%d entries processed from %s",
                self._processed_count,
                self._entry_count,
                self.file_path.name,
            )
        else:
            # Log error information
            logger.error(
                "Library extraction failed: %d/%d entries processed from %s before error: %s",
                self._processed_count,
                self._entry_count,
                self.file_path.name,
                exc_val,
            )

    def __len__(self) -> int:
        """Return number of entries in library."""
        if self._entry_count == 0:
            self._scan_entries()
        return self._entry_count

    def _scan_entries(self) -> None:
        """Scan the library file to count entries."""
        try:
            from src.extract.pbd.header import extract_pbl_header
            from src.extract.pbd.node import extract_nods

            with self.file_path.open("rb") as f:
                # Extract header to get initial information
                header = extract_pbl_header(f, 512)  # Common block size

                if hasattr(header, "node_offset") and header.node_offset > 0:
                    # Extract node information to count entries
                    f.seek(header.node_offset)
                    nodes = extract_nods(f, header.node_offset, header.node_count)

                    # Count total entries across all nodes
                    self._entry_count = sum(
                        len(node.entry_defs)
                        for node in nodes
                        if hasattr(node, "entry_defs")
                    )
                else:
                    # Fallback: estimate from file size
                    file_size = self.file_path.stat().st_size
                    # Rough estimate: average entry size ~5KB
                    self._entry_count = max(1, file_size // 5000)

                logger.debug(
                    "Found %d entries in %s", self._entry_count, self.file_path.name
                )

        except Exception as e:
            logger.warning("Failed to scan entries in %s: %s", self.file_path.name, e)
            self._entry_count = 0

    def extract_all(
        self, output_dir: str | Path, silent_progress: bool = False
    ) -> None:
        """Extract all entries to output directory.

        Args:
            output_dir: Directory to extract files to
            silent_progress: Whether to suppress progress output
        """
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)

        try:
            # Use the simple extraction function from extract module
            from src.extract.extract import extract_pbl_file

            # Track progress through a custom callback if needed
            extract_pbl_file(self.file_path, output_path)

            # Count extracted files as processed entries
            extracted_files = list(output_path.rglob("*"))
            self._processed_count = len([f for f in extracted_files if f.is_file()])

            logger.info(
                "Successfully extracted %d entries from %s",
                self._processed_count,
                self.file_path.name,
            )
        except Exception as e:
            logger.error("Failed to extract from %s: %s", self.file_path.name, e)
            raise
