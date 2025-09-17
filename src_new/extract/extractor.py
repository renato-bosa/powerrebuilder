"""Extract Feature - PowerBuilder PBL/PBD file extraction.

This module handles extraction of objects from PowerBuilder Library files.
Consolidates the extraction logic into a clean, maintainable implementation.
"""

import logging
import struct
from pathlib import Path
from typing import Dict, List, Optional, Tuple

from _core import (
    ExtractedObject,
    ObjectType,
    PBLEntry,
    PBLFile,
)
from _patterns import (
    BaseCoordinator,
    BinaryReader,
    CoordinatorResult,
    FileHandler,
)

logger = logging.getLogger(__name__)


# ============================================================================
# PBL/PBD FORMAT CONSTANTS
# ============================================================================

# File signatures
PBL_SIGNATURE = b"PBL\x06"  # PowerBuilder Library
PBD_SIGNATURE = b"PBD\x06"  # PowerBuilder Dynamic Library

# Block signatures
HDR_SIGNATURE = b"HDR*"  # Header block
NOD_SIGNATURE = b"NOD*"  # Node block
ENT_SIGNATURE = b"ENT*"  # Entry block
DAT_SIGNATURE = b"DAT*"  # Data block
FRE_SIGNATURE = b"FRE*"  # Free block

# PowerBuilder object extensions
OBJECT_EXTENSIONS = {
    ".sra": ObjectType.APPLICATION,
    ".srw": ObjectType.WINDOW,
    ".sru": ObjectType.USER_OBJECT,
    ".srm": ObjectType.MENU,
    ".srf": ObjectType.FUNCTION,
    ".srd": ObjectType.DATAWINDOW,
    ".srs": ObjectType.STRUCTURE,
    ".srq": ObjectType.QUERY,
    ".fun": ObjectType.FUNCTION,  # P-code function
}


# ============================================================================
# PBL PARSER
# ============================================================================


class PBLParser:
    """Parser for PowerBuilder Library files.

    Handles both PBL (source) and PBD (compiled) formats.
    """

    def __init__(self, file_path: Path):
        """Initialize parser with file path.

        Args:
            file_path: Path to PBL/PBD file
        """
        self.file_path = file_path
        self.reader = None
        self.header = None
        self.entries = []

    def parse(self) -> PBLFile:
        """Parse the PBL/PBD file.

        Returns:
            Parsed PBL file object
        """
        with BinaryReader(self.file_path) as self.reader:
            # Parse header
            self.header = self._parse_header()

            # Parse node directory
            nodes = self._parse_nodes()

            # Parse entries from nodes
            self.entries = self._parse_entries(nodes)

            return PBLFile(
                path=self.file_path,
                version=self._detect_version(),
                entries=self.entries,
                size=self.reader.size,
                checksum=self.reader.calculate_checksum(),
            )

    def _parse_header(self) -> Dict:
        """Parse file header.

        Returns:
            Header information
        """
        # Check signature
        signature = self.reader.read(4)
        if signature not in [PBL_SIGNATURE, PBD_SIGNATURE]:
            raise ValueError(f"Invalid file signature: {signature}")

        # Read header fields
        header = {
            "signature": signature,
            "format_version": self.reader.read_uint32(),
            "creation_time": self.reader.read_uint32(),
            "modification_time": self.reader.read_uint32(),
            "comment_size": self.reader.read_uint32(),
        }

        # Skip comment if present
        if header["comment_size"] > 0:
            header["comment"] = self.reader.read_string(
                header["comment_size"]
            )

        # Read directory info
        header["first_node_offset"] = self.reader.read_uint32()
        header["node_count"] = self.reader.read_uint32()

        return header

    def _parse_nodes(self) -> List[Dict]:
        """Parse node directory.

        Returns:
            List of node entries
        """
        nodes = []

        # Seek to first node
        self.reader.seek(self.header["first_node_offset"])

        for _ in range(self.header["node_count"]):
            # Check for node signature
            sig = self.reader.read(4)
            if sig != NOD_SIGNATURE:
                logger.warning(f"Invalid node signature: {sig}")
                continue

            node = {
                "signature": sig,
                "next_offset": self.reader.read_uint32(),
                "prev_offset": self.reader.read_uint32(),
                "parent_offset": self.reader.read_uint32(),
                "entry_count": self.reader.read_uint16(),
                "level": self.reader.read_uint16(),
            }

            # Read entry offsets
            node["entries"] = []
            for _ in range(node["entry_count"]):
                node["entries"].append(self.reader.read_uint32())

            nodes.append(node)

            # Move to next node if exists
            if node["next_offset"] > 0:
                self.reader.seek(node["next_offset"])

        return nodes

    def _parse_entries(self, nodes: List[Dict]) -> List[PBLEntry]:
        """Parse entries from nodes.

        Args:
            nodes: List of parsed nodes

        Returns:
            List of PBL entries
        """
        entries = []

        for node in nodes:
            for entry_offset in node["entries"]:
                if entry_offset == 0:
                    continue

                self.reader.seek(entry_offset)

                # Check entry signature
                sig = self.reader.read(4)
                if sig != ENT_SIGNATURE:
                    logger.warning(f"Invalid entry signature at {entry_offset}")
                    continue

                # Parse entry
                entry_data = {
                    "signature": sig,
                    "data_offset": self.reader.read_uint32(),
                    "data_size": self.reader.read_uint32(),
                    "timestamp": self.reader.read_uint32(),
                    "name_size": self.reader.read_uint16(),
                    "comment_size": self.reader.read_uint16(),
                }

                # Read name
                name = self.reader.read_string(entry_data["name_size"])

                # Skip comment
                if entry_data["comment_size"] > 0:
                    self.reader.read(entry_data["comment_size"])

                # Determine object type
                obj_type = self._determine_type(name)

                entries.append(
                    PBLEntry(
                        name=name,
                        type=obj_type,
                        size=entry_data["data_size"],
                        offset=entry_data["data_offset"],
                        timestamp=entry_data["timestamp"],
                    )
                )

        return entries

    def _determine_type(self, name: str) -> ObjectType:
        """Determine object type from name.

        Args:
            name: Object name

        Returns:
            Object type
        """
        # Check extension
        for ext, obj_type in OBJECT_EXTENSIONS.items():
            if name.lower().endswith(ext):
                return obj_type

        # Default to user object
        return ObjectType.USER_OBJECT

    def _detect_version(self) -> str:
        """Detect PowerBuilder version.

        Returns:
            Version string
        """
        # Simple version detection based on format version
        format_ver = self.header.get("format_version", 0)

        if format_ver >= 0x0600:
            return "PB12.5"
        elif format_ver >= 0x0500:
            return "PB11"
        elif format_ver >= 0x0400:
            return "PB10"
        else:
            return "PB9"

    def extract_data(self, entry: PBLEntry) -> bytes:
        """Extract data for an entry.

        Args:
            entry: PBL entry to extract

        Returns:
            Raw data bytes
        """
        with BinaryReader(self.file_path) as reader:
            reader.seek(entry.offset)

            # Check for data block signature
            sig = reader.read(4)
            if sig != DAT_SIGNATURE:
                # Try reading raw data
                reader.seek(entry.offset)
                return reader.read(entry.size)

            # Skip block header
            reader.read(12)  # Skip block metadata

            # Read actual data
            return reader.read(entry.size)


# ============================================================================
# EXTRACTION COORDINATOR
# ============================================================================


class ExtractCoordinator(BaseCoordinator):
    """Coordinator for extraction stage.

    Extracts objects from PowerBuilder Library files.
    """

    @property
    def stage_name(self) -> str:
        """Get stage name."""
        return "extract"

    def discover_files(self) -> List[Path]:
        """Discover PBL/PBD files to process.

        Returns:
            List of library files
        """
        if self.input_path.is_file():
            # Single file
            if self.input_path.suffix.lower() in [".pbl", ".pbd"]:
                return [self.input_path]
            else:
                raise ValueError(f"Not a PBL/PBD file: {self.input_path}")
        else:
            # Directory - find all PBL/PBD files
            files = []
            for pattern in ["*.pbl", "*.pbd", "*.PBL", "*.PBD"]:
                files.extend(self.input_path.rglob(pattern))
            return files

    def process_file(self, input_file: Path, output_dir: Path) -> bool:
        """Process a single PBL/PBD file.

        Args:
            input_file: Path to PBL/PBD file
            output_dir: Output directory

        Returns:
            True if successful
        """
        try:
            self.logger.info(f"Extracting: {input_file}")

            # Parse the library file
            parser = PBLParser(input_file)
            pbl_file = parser.parse()

            self.logger.info(
                f"Found {len(pbl_file.entries)} entries in {input_file.name}"
            )

            # Create output subdirectory for this library
            lib_output = output_dir / input_file.stem
            lib_output.mkdir(parents=True, exist_ok=True)

            # Extract each entry
            file_handler = FileHandler()
            extracted_count = 0

            for entry in pbl_file.entries:
                try:
                    # Extract data
                    data = parser.extract_data(entry)

                    # Determine output file name
                    output_name = entry.name
                    if not any(output_name.endswith(ext) for ext in OBJECT_EXTENSIONS):
                        # Add extension based on type
                        ext_map = {
                            ObjectType.WINDOW: ".srw",
                            ObjectType.USER_OBJECT: ".sru",
                            ObjectType.MENU: ".srm",
                            ObjectType.DATAWINDOW: ".srd",
                            ObjectType.FUNCTION: ".srf",
                            ObjectType.STRUCTURE: ".srs",
                            ObjectType.APPLICATION: ".sra",
                        }
                        output_name += ext_map.get(entry.type, ".sru")

                    # Write to file
                    output_file = lib_output / output_name

                    # Check if it's text or binary
                    if self._is_text_data(data):
                        # Decode and write as text
                        text = data.decode("utf-8", errors="replace")
                        file_handler.write_text(output_file, text)
                    else:
                        # Write as binary (P-code)
                        output_file = output_file.with_suffix(".fun")
                        file_handler.write_binary(output_file, data)

                    extracted_count += 1

                except Exception as e:
                    self.logger.warning(f"Failed to extract {entry.name}: {e}")

            self.logger.info(
                f"Extracted {extracted_count}/{len(pbl_file.entries)} objects"
            )

            return extracted_count > 0

        except Exception as e:
            self.logger.error(f"Failed to process {input_file}: {e}")
            return False

    def _is_text_data(self, data: bytes) -> bool:
        """Check if data appears to be text.

        Args:
            data: Data bytes

        Returns:
            True if likely text
        """
        # Check for common text patterns
        if not data:
            return False

        # Check for UTF-8 BOM
        if data.startswith(b"\xef\xbb\xbf"):
            return True

        # Check for UTF-16 BOM
        if data.startswith(b"\xff\xfe") or data.startswith(b"\xfe\xff"):
            return True

        # Sample first 1000 bytes
        sample = data[:1000]

        # Try to decode as text
        try:
            sample.decode("utf-8")
            # Check for reasonable text characters
            text_chars = sum(
                1 for b in sample
                if b in range(32, 127) or b in [9, 10, 13]
            )
            return text_chars > len(sample) * 0.7
        except:
            return False