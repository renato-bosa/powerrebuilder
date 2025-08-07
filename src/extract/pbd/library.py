"""PBD Library extraction module."""

import logging
from pathlib import Path
from typing import Any

from src.extract.pbd.version_detection import PBVersionDetector, PowerBuilderVersion

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
        self._version = None  # PowerBuilder version detection

    def __enter__(self) -> "Library":
        """Context manager entry."""
        # Detect PowerBuilder version first
        self._detect_version()
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

    def _detect_version(self) -> PowerBuilderVersion | None:
        """Detect PowerBuilder version of this file."""
        try:
            with open(self.file_path, "rb") as f:
                self._version = PBVersionDetector.detect_from_file(f)
                if self._version:
                    logger.info(
                        "Detected %s for %s", self._version, self.file_path.name
                    )
                else:
                    logger.warning(
                        "Could not detect PowerBuilder version for %s",
                        self.file_path.name,
                    )
                    # Default to PB 10.5 Unicode as fallback
                    self._version = PowerBuilderVersion(10, 5, True)
                    logger.info("Using default version: %s", self._version)
        # Processing: catch specific exceptions when possible
        except (ValueError, TypeError, OSError, ImportError) as e:
            logger.error("Error detecting version for %s: %s", self.file_path.name, e)
            # Default fallback
            self._version = PowerBuilderVersion(10, 5, True)
        return self._version

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
                        f,
                        header.is_unicode,
                        header.first_nod_offset,
                        512,
                        pb_version=self._version,
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
                    # Extract all nodes with version information
                    nodes = extract_nods(
                        f,
                        header.is_unicode,
                        header.first_nod_offset,
                        512,
                        pb_version=self._version,
                    )

                    # Process each node and extract entries
                    for node in nodes:
                        if hasattr(node, "entry_defs"):
                            for entry in node.entry_defs:
                                # Extract each entry to a file (pass version for proper parsing)
                                self._extract_entry(
                                    f, entry, output_path, self._version
                                )
                                self._processed_count += 1
                else:
                    logger.warning(
                        "No valid node offset found in %s", self.file_path.name
                    )

                # If no entries were extracted through nodes, or if we got decode errors, try direct scanning
                # Check if any extracted files have DECODE_ERROR in their names
                extracted_files = list(output_path.rglob("*DECODE_ERROR*"))
                if self._processed_count == 0 or len(extracted_files) > 0:
                    logger.info(
                        "Attempting direct ENT* block scanning for %s",
                        self.file_path.name,
                    )

                    # Clean up any decode error files first
                    for bad_file in extracted_files:
                        bad_file.unlink()
                        logger.debug("Removed decode error file: %s", bad_file.name)

                    from src.extract.pbd.direct_scanner import scan_for_entries

                    # Reopen file for scanning
                    f.seek(0)
                    direct_entries = scan_for_entries(f)

                    if direct_entries:
                        logger.info(
                            "Found %d entries through direct scanning",
                            len(direct_entries),
                        )
                        self._processed_count = 0  # Reset count
                        for entry in direct_entries:
                            self._extract_entry(f, entry, output_path, self._version)
                            self._processed_count += 1

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

    def _extract_entry(
        self,
        file_handle: Any,
        entry: Any,
        output_dir: Path,
        pb_version: PowerBuilderVersion | None = None,
    ) -> None:
        """Extract a single entry from the PBD file.

        Args:
            file_handle: Open file handle
            entry: Entry definition to extract
            output_dir: Output directory for extracted files
            pb_version: PowerBuilder version for format-specific handling
        """
        try:
            logger.debug(
                "Extracting entry: %s at offset %s",
                getattr(entry, "object_name", "unknown"),
                getattr(entry, "offset", 0),
            )
            # Check if entry has the necessary attributes (object_name, data_offset, size)
            if (
                hasattr(entry, "object_name")
                and hasattr(entry, "data_offset")
                and hasattr(entry, "size")
            ):
                # Create output file with appropriate extension
                object_name = entry.object_name
                object_type = getattr(entry, "object_type", "unknown")

                # Determine file extension based on object type
                extension_map = {
                    "window": ".srw",
                    "userobject": ".sru",
                    "menu": ".srm",
                    "datawindow": ".srd",
                    "function": ".srf",
                    "structure": ".srs",
                    "application": ".sra",
                }
                extension = extension_map.get(object_type.lower(), ".fun")

                output_file = output_dir / f"{object_name}{extension}"
                output_file.parent.mkdir(parents=True, exist_ok=True)

                # Extract data using proper DAT block parsing
                try:
                    from src.extract.pbd.structures import extract_data_from_entry

                    # Get file size
                    current_pos = file_handle.tell()
                    file_handle.seek(0, 2)  # Seek to end
                    file_size = file_handle.tell()
                    file_handle.seek(current_pos)  # Restore position

                    # Extract DAT blocks
                    data_blocks, is_partial = extract_data_from_entry(
                        file_handle, entry, False, 512, file_size
                    )

                    if not data_blocks:
                        logger.warning(
                            "No data blocks found for entry %s, attempting simple extraction from data_offset",
                            object_name,
                        )
                        # Fallback to simple extraction using data_offset
                        file_handle.seek(entry.data_offset)
                        # Read available data up to file end or entry size, whichever is smaller
                        available_size = min(entry.size, file_size - entry.data_offset)
                        if available_size <= 0:
                            logger.error("No data available for entry %s", object_name)
                            return
                        entry_data = file_handle.read(available_size)
                    else:
                        # Concatenate all data blocks
                        entry_data = b"".join(block.data for block in data_blocks)

                        if is_partial:
                            logger.warning(
                                "Partial data extraction for entry %s (some DAT blocks missing)",
                                object_name,
                            )

                except ImportError as e:
                    logger.warning(
                        "DAT extraction not available (%s), using simple extraction for entry %s",
                        e,
                        object_name,
                    )
                    # Fallback to simple extraction using data_offset
                    file_handle.seek(entry.data_offset)
                    # Read available data up to file end or entry size, whichever is smaller
                    current_pos = file_handle.tell()
                    file_handle.seek(0, 2)  # Seek to end
                    file_size = file_handle.tell()
                    file_handle.seek(current_pos)  # Restore position

                    available_size = min(entry.size, file_size - entry.data_offset)
                    if available_size <= 0:
                        logger.error("No data available for entry %s", object_name)
                        return
                    entry_data = file_handle.read(available_size)

                # Write entry data
                with output_file.open("wb") as f:
                    f.write(entry_data)

                logger.debug(
                    "Extracted entry: %s (%s) - %d bytes",
                    object_name,
                    object_type,
                    len(entry_data),
                )

            # Legacy support for old-style entries with name and data attributes
            elif hasattr(entry, "name") and hasattr(entry, "data"):
                # Create output file
                output_file = output_dir / entry.name
                output_file.parent.mkdir(parents=True, exist_ok=True)

                # Write entry data
                with output_file.open("wb") as f:
                    f.write(entry.data)

                logger.debug("Extracted entry: %s", entry.name)

            # Support entries with object_name and offset (legacy compatibility)
            elif (
                hasattr(entry, "object_name")
                and hasattr(entry, "offset")
                and hasattr(entry, "size")
            ):
                logger.warning(
                    "Entry %s uses legacy offset field instead of data_offset, this may be incorrect",
                    entry.object_name,
                )
                # Keep the old behavior for backward compatibility but warn
                object_name = entry.object_name
                object_type = getattr(entry, "object_type", "unknown")

                extension_map = {
                    "window": ".srw",
                    "userobject": ".sru",
                    "menu": ".srm",
                    "datawindow": ".srd",
                    "function": ".srf",
                    "structure": ".srs",
                    "application": ".sra",
                }
                extension = extension_map.get(object_type.lower(), ".fun")

                output_file = output_dir / f"{object_name}{extension}"
                output_file.parent.mkdir(parents=True, exist_ok=True)

                file_handle.seek(entry.offset)
                entry_data = file_handle.read(entry.size)

                with output_file.open("wb") as f:
                    f.write(entry_data)

                logger.debug(
                    "Extracted entry (legacy): %s (%s)", object_name, object_type
                )
            else:
                logger.warning(
                    "Entry missing required attributes (object_name/data_offset/size or name/data): %s",
                    type(entry).__name__,
                )

        except Exception as e:
            logger.warning("Failed to extract entry: %s", e)
