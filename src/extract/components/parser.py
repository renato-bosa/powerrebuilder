"""Binary file parser component for PowerBuilder files.

This component handles parsing of PowerBuilder binary file formats (PBL/PBD),
including header parsing, structure analysis, and entry extraction.
"""

import logging
import struct
from pathlib import Path
from typing import Any

from src.contracts.extractors import IBinaryFileParser
from src.core.exceptions import ExtractError, HeaderError, NodeError
from src.core.resource_limits import safe_read_file
from src.extract.pbd.header import extract_pbl_header
from src.extract.pbd.node import extract_nods as extract_nodes

logger = logging.getLogger(__name__)


class BinaryFileParser(IBinaryFileParser):
    """Parser for PowerBuilder binary files.

    This component is responsible for understanding the binary structure
    of PBL/PBD files and extracting their contents.
    """

    def __init__(self, block_size: int = 512) -> None:
        """Initialize the binary parser.

        Args:
            block_size: Default block size for reading (default: 512)
        """
        self.block_size = block_size
        self._file_cache: dict[Path, bytes] = {}

    def parse_header(self, file_path: Path) -> dict[str, Any]:
        """Parse file header to determine format and metadata.

        Args:
            file_path: Path to binary file

        Returns:
            Dictionary with header information

        Raises:
            HeaderError: If header parsing fails
        """
        try:
            # Read file bytes
            file_bytes = self._read_file_cached(file_path)

            # Extract header
            header = extract_pbl_header(
                file_bytes,
                block_size=self.block_size,
                file_path_for_error_log=str(file_path),
            )

            # Convert to dictionary
            return {
                "signature": header.signature.decode("ascii", errors="ignore"),
                "format_version": header.format_version,
                "is_unicode": header.is_unicode,
                "first_nod_offset": header.first_nod_offset,
                "entry_count": header.entry_count
                if hasattr(header, "entry_count")
                else None,
                "file_size": len(file_bytes),
                "block_size": self.block_size,
            }

        except struct.error as e:
            logger.error("Binary format error parsing header for %s: %s", file_path, e)
            raise HeaderError(f"Invalid binary format in header: {e}") from e
        except OSError as e:
            logger.error("File access error for %s: %s", file_path, e)
            raise HeaderError(f"Cannot read file header: {e}") from e
        except Exception as e:
            logger.error("Unexpected error parsing header for %s: %s", file_path, e)
            raise HeaderError(f"Failed to parse header: {e}") from e

    def parse_structure(self, file_path: Path) -> list[dict[str, Any]]:
        """Parse the complete file structure.

        Args:
            file_path: Path to binary file

        Returns:
            List of file entries with metadata

        Raises:
            ExtractError: If structure parsing fails
        """
        try:
            # Read file bytes
            file_bytes = self._read_file_cached(file_path)

            # Parse header first
            header = extract_pbl_header(
                file_bytes,
                block_size=self.block_size,
                file_path_for_error_log=str(file_path),
            )

            # Extract nodes
            nodes = extract_nodes(
                file_bytes, header.is_unicode, header.first_nod_offset, self.block_size
            )

            # Extract entries from nodes
            all_entries = []
            for node in nodes:
                # Entries are already in the node's entry_defs attribute
                if hasattr(node, "entry_defs") and node.entry_defs:
                    entries = node.entry_defs

                    for entry in entries:
                        # Convert entry to dictionary
                        entry_dict = {
                            "name": entry.object_name,
                            "type": self._determine_entry_type(entry),
                            "size": entry.size,
                            "offset": entry.data_offset,
                            "comment": entry.comment,
                            "creation_time": entry.creation_datetime,
                            "modification_time": entry.modification_datetime,
                            "node_offset": node.offset,
                            "entry_offset": entry.offset,
                        }
                        all_entries.append(entry_dict)

            logger.info("Parsed %d entries from %s", len(all_entries), file_path.name)
            return all_entries

        except HeaderError:
            # Re-raise header errors as-is
            raise
        except struct.error as e:
            logger.error(
                "Binary format error parsing structure for %s: %s", file_path, e
            )
            raise NodeError(f"Invalid node structure: {e}") from e
        except OSError as e:
            logger.error("File access error for %s: %s", file_path, e)
            raise ExtractError(f"Cannot read file: {e}") from e
        except Exception as e:
            logger.error("Unexpected error parsing structure for %s: %s", file_path, e)
            raise ExtractError(f"Failed to parse file structure: {e}") from e

    def extract_entry(
        self, file_path: Path, entry_info: dict[str, Any], output_path: Path
    ) -> bool:
        """Extract a single entry from the binary file.

        Args:
            file_path: Path to binary file
            entry_info: Entry metadata from parse_structure
            output_path: Output file path

        Returns:
            True if successful, False otherwise
        """
        try:
            # Read file bytes
            file_bytes = self._read_file_cached(file_path)

            # Get entry data
            offset = entry_info["offset"]
            size = entry_info["size"]

            # Validate offset and size
            if offset < 0 or offset + size > len(file_bytes):
                logger.error(
                    "Invalid offset/size for entry %s: offset=%d, size=%d, file_size=%d",
                    entry_info["name"],
                    offset,
                    size,
                    len(file_bytes),
                )
                return False

            # Extract data
            entry_data = file_bytes[offset : offset + size]

            # Check if data looks like P-code (starts with specific signatures)
            if self._is_pcode_data(entry_data):
                # Write as .fun file for P-code
                output_path = output_path.with_suffix(".fun")

            # Ensure output directory exists
            output_path.parent.mkdir(parents=True, exist_ok=True)

            # Write to file
            with output_path.open("wb") as f:
                f.write(entry_data)

            logger.debug(
                "Extracted entry %s (%d bytes) to %s",
                entry_info["name"],
                size,
                output_path,
            )

            return True

        except OSError as e:
            logger.error(
                "File I/O error extracting entry %s: %s",
                entry_info.get("name", "unknown"),
                e,
            )
            return False
        except struct.error as e:
            logger.error(
                "Binary format error extracting entry %s: %s",
                entry_info.get("name", "unknown"),
                e,
            )
            return False
        except Exception as e:
            logger.error(
                "Unexpected error extracting entry %s: %s",
                entry_info.get("name", "unknown"),
                e,
            )
            return False

    def _read_file_cached(self, file_path: Path) -> bytes:
        """Read file with caching.

        Args:
            file_path: Path to file

        Returns:
            File contents as bytes
        """
        if file_path not in self._file_cache:
            # Use safe_read_file for size limits
            self._file_cache[file_path] = safe_read_file(str(file_path))
        return self._file_cache[file_path]

    def _determine_entry_type(self, entry: Any) -> str:
        """Determine the type of an entry.

        Args:
            entry: Entry object

        Returns:
            Entry type string
        """
        # Check object name for common extensions
        name = entry.object_name.lower()

        if name.endswith(".win"):
            return "window"
        if name.endswith(".men"):
            return "menu"
        if name.endswith(".dwo"):
            return "datawindow"
        if name.endswith(".fun"):
            return "function"
        if name.endswith(".str"):
            return "structure"
        if name.endswith(".uo"):
            return "userobject"
        if name.endswith(".app"):
            return "application"
        # Default to fun for P-code
        return "fun"

    def _is_pcode_data(self, data: bytes) -> bool:
        """Check if data appears to be P-code.

        Args:
            data: Data bytes to check

        Returns:
            True if data looks like P-code
        """
        if len(data) < 4:
            return False

        # Check for common P-code signatures
        # P-code often starts with specific byte patterns
        signatures = [
            b"\x00\x00\x00\x00",  # Null header
            b"PBVM",  # PowerBuilder VM marker
            b"\x01\x00\x00\x00",  # Version marker
        ]

        for sig in signatures:
            if data.startswith(sig):
                return True

        # Check for high density of null bytes (common in P-code)
        null_count = data[:100].count(b"\x00")
        if null_count > 50:  # More than 50% nulls in first 100 bytes
            return True

        return False

    def clear_cache(self) -> None:
        """Clear the file cache to free memory."""
        self._file_cache.clear()
