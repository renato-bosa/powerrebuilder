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
            from src.extract.pbd.structures import extract_nods, extract_pbl_header

            with self.file_path.open("rb") as f:
                # Extract header to get initial information
                header = extract_pbl_header(f, 512)  # Common block size

                if hasattr(header, "first_nod_offset") and header.first_nod_offset > 0:
                    # Extract node information to count entries
                    nodes = extract_nods(
                        f, header.is_unicode, header.first_nod_offset, 512
                    )

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

    def extract_all(self, output_dir: str | Path) -> None:
        """Extract all entries to output directory.

        Args:
            output_dir: Directory to extract files to
        """
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)

        try:
            # Use structures module directly to avoid circular dependency
            from src.extract.pbd.structures import extract_nods, extract_pbl_header

            with self.file_path.open("rb") as f:
                # Extract header to get initial information
                header = extract_pbl_header(f, 512)

                if hasattr(header, "first_nod_offset") and header.first_nod_offset > 0:
                    # Extract all nodes
                    nodes = extract_nods(
                        f, header.is_unicode, header.first_nod_offset, 512
                    )

                    # Process each node and extract entries
                    for node in nodes:
                        if hasattr(node, "entry_defs"):
                            for entry in node.entry_defs:
                                # Extract each entry to a file
                                self._extract_entry(f, entry, output_path)
                                self._processed_count += 1
                else:
                    logger.warning("No valid node offset found in %s", self.file_path.name)

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

    def _extract_entry(self, file_handle: Any, entry: Any, output_dir: Path) -> None:
        """Extract a single entry from the PBD file.

        Args:
            file_handle: Open file handle
            entry: Entry definition to extract
            output_dir: Output directory for extracted files
        """
        try:
            # Basic entry extraction - write entry data to file
            if hasattr(entry, "name") and hasattr(entry, "data"):
                # Create output file
                output_file = output_dir / entry.name
                output_file.parent.mkdir(parents=True, exist_ok=True)

                # Write entry data
                with output_file.open("wb") as f:
                    f.write(entry.data)

                logger.debug("Extracted entry: %s", entry.name)

        except Exception as e:
            logger.warning("Failed to extract entry: %s", e)
