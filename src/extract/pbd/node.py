"""Node structures for PowerBuilder extraction."""

import logging
import struct
from dataclasses import dataclass, field
from typing import Any, BinaryIO

from src.extract.pbd.constants import SIGNATURES, UNICODE_SIGNATURES
from src.extract.pbd.recovery import extract_entry_with_recovery
from src.extract.utils.binary import safe_unpack

logger = logging.getLogger(__name__)


@dataclass
class PbNodeDefinition:
    """PowerBuilder node definition structure.

    Nodes contain references to entries (objects) in the PBD file.
    Each node can contain multiple entry definitions.
    """

    offset: int
    """Offset of this node in the file"""

    signature: bytes
    """Node signature (NOD*)"""

    is_unicode: bool
    """Whether this node uses Unicode encoding"""

    next_node_offset: int
    """Offset to the next node (0 if last)"""

    entry_count: int
    """Number of entries in this node"""

    entry_defs: list[Any] = field(default_factory=list)
    """List of entry definitions in this node"""

    metadata: dict[str, Any] = field(default_factory=dict)
    """Additional metadata for debugging"""


def extract_nods(
    arr: bytes | BinaryIO,
    is_unicode: bool,
    first_nod_offset: int,
    block_size: int = 512,
) -> list[PbNodeDefinition]:
    """Extract all nodes from a PBD file.

    Args:
        arr: File bytes or file-like object
        is_unicode: Whether the file uses Unicode encoding
        first_nod_offset: Offset to the first node
        block_size: Block size for alignment

    Returns:
        List of node definitions

    Raises:
        NodeError: If node extraction fails
    """
    # Handle both bytes and file-like objects
    if hasattr(arr, "read"):
        # It's a file-like object, read it
        arr.seek(0)
        file_bytes = arr.read()
    else:
        # It's already bytes
        file_bytes = arr

    nodes: list[Any] = []
    current_offset = first_nod_offset

    # Validate first node offset
    if current_offset < 0 or current_offset >= len(file_bytes):
        logger.warning(
            "Invalid first node offset %d (file size: %d)",
            current_offset,
            len(file_bytes),
        )
        return nodes

    # Maximum nodes to prevent infinite loops
    max_nodes = 10000
    node_count = 0

    while current_offset > 0 and node_count < max_nodes:
        try:
            # Extract node at current offset
            node = _extract_single_node(
                file_bytes, current_offset, is_unicode, block_size
            )

            if not node:
                logger.debug("No node found at offset %d", current_offset)
                break

            nodes.append(node)
            node_count += 1

            # Move to next node
            current_offset = node.next_node_offset

            # Validate next offset
            if current_offset > 0 and current_offset >= len(file_bytes):
                logger.warning(
                    "Next node offset %d exceeds file size %d",
                    current_offset,
                    len(file_bytes),
                )
                break

        except Exception as e:
            logger.warning(
                "Failed to extract node at offset %d: %s",
                current_offset,
                e,
            )
            break

    logger.info("Extracted %d nodes from PBD", len(nodes))
    return nodes


def _extract_single_node(
    file_bytes: bytes,
    offset: int,
    is_unicode: bool,
    block_size: int,
) -> PbNodeDefinition | None:
    """Extract a single node from the file.

    Args:
        file_bytes: Complete file bytes
        offset: Offset to the node
        is_unicode: Whether to expect Unicode encoding
        block_size: Block size for alignment

    Returns:
        Node definition or None if not found
    """
    # Check signature
    if offset + 4 > len(file_bytes):
        return None

    signature = file_bytes[offset : offset + 4]

    # Verify it's a NOD block
    expected_sig = UNICODE_SIGNATURES["NOD"] if is_unicode else SIGNATURES["NOD"]
    if signature != expected_sig[:4]:
        # Try the other encoding
        alt_sig = SIGNATURES["NOD"] if is_unicode else UNICODE_SIGNATURES["NOD"]
        if signature != alt_sig[:4]:
            logger.debug(
                "Invalid node signature at offset %d: %s",
                offset,
                signature.hex(),
            )
            return None

    # Create node structure
    node = PbNodeDefinition(
        offset=offset,
        signature=signature,
        is_unicode=is_unicode,
        next_node_offset=0,
        entry_count=0,
    )

    # Parse node header
    try:
        header_offset = offset + 4  # Skip signature

        if is_unicode:
            # Unicode node structure
            node_data = _parse_unicode_node_header(file_bytes, header_offset)
        else:
            # ASCII node structure
            node_data = _parse_ascii_node_header(file_bytes, header_offset)

        if not node_data:
            return None

        node.next_node_offset = node_data["next_offset"]
        node.entry_count = node_data["entry_count"]

        # Extract entries
        entries_offset = node_data["entries_offset"]
        node.entry_defs = _extract_node_entries(
            file_bytes,
            entries_offset,
            node.entry_count,
            is_unicode,
            offset,
        )

        # Store metadata
        node.metadata.update(node_data)

    except Exception as e:
        logger.warning("Failed to parse node at offset %d: %s", offset, e)
        return None

    return node


def _parse_ascii_node_header(file_bytes: bytes, offset: int) -> dict[str, Any] | None:
    """Parse ASCII node header.

    Args:
        file_bytes: Complete file bytes
        offset: Offset after signature

    Returns:
        Node header data or None
    """
    # Minimum header size
    if offset + 16 > len(file_bytes):
        return None

    try:
        # Common node structure:
        # - Next node offset (4 bytes)
        # - Entry count (4 bytes)
        # - Additional fields vary by version

        # Parse next offset and entry count safely
        next_result = safe_unpack("<I", file_bytes, offset)
        entry_result = safe_unpack("<I", file_bytes, offset + 4)
        
        if not next_result or not entry_result:
            logger.debug("Failed to parse ASCII node header at offset %d", offset)
            return None
            
        next_offset = next_result[0]
        entry_count = entry_result[0]

        # Sanity checks
        if entry_count > 10000:  # Unreasonable number of entries
            logger.warning("Suspicious entry count: %d", entry_count)
            return None

        # Entries typically start after the header
        # The exact offset depends on the PB version
        entries_offset = offset + 16  # Basic header size

        return {
            "next_offset": next_offset,
            "entry_count": entry_count,
            "entries_offset": entries_offset,
            "header_size": 16,
        }

    except struct.error as e:
        logger.debug("Failed to unpack ASCII node header: %s", e)
        return None


def _parse_unicode_node_header(file_bytes: bytes, offset: int) -> dict[str, Any] | None:
    """Parse Unicode node header.

    Args:
        file_bytes: Complete file bytes
        offset: Offset after signature

    Returns:
        Node header data or None
    """
    # Unicode headers may be larger
    if offset + 20 > len(file_bytes):
        return None

    try:
        # Unicode node structure is similar but may have different alignment
        # Parse next offset and entry count safely
        next_result = safe_unpack("<I", file_bytes, offset)
        entry_result = safe_unpack("<I", file_bytes, offset + 4)
        
        if not next_result or not entry_result:
            logger.debug("Failed to parse Unicode node header at offset %d", offset)
            return None
            
        next_offset = next_result[0]
        entry_count = entry_result[0]

        # Sanity checks
        if entry_count > 10000:
            logger.warning("Suspicious entry count: %d", entry_count)
            return None

        # Unicode entries may start at different offset
        entries_offset = offset + 20

        return {
            "next_offset": next_offset,
            "entry_count": entry_count,
            "entries_offset": entries_offset,
            "header_size": 20,
        }

    except struct.error as e:
        logger.debug("Failed to unpack Unicode node header: %s", e)
        return None


def _extract_node_entries(
    file_bytes: bytes,
    offset: int,
    entry_count: int,
    is_unicode: bool,
    node_offset: int,
) -> list[Any]:
    """Extract entries from a node.

    Args:
        file_bytes: Complete file bytes
        offset: Offset to first entry
        entry_count: Number of entries to extract
        is_unicode: Whether to use Unicode parsing
        node_offset: Offset of the containing node (for context)

    Returns:
        List of entry definitions
    """
    entries = []
    current_offset = offset

    for i in range(entry_count):
        try:
            # Each entry reference in the node typically contains:
            # - Entry offset (4 bytes)
            # - Entry size or other metadata

            if current_offset + 8 > len(file_bytes):
                logger.debug(
                    "Insufficient data for entry %d at offset %d",
                    i,
                    current_offset,
                )
                break

            # Read entry reference safely
            entry_result = safe_unpack("<I", file_bytes, current_offset)
            if not entry_result:
                logger.debug(
                    "Insufficient data for entry offset %d at current_offset %d",
                    i,
                    current_offset,
                )
                break
            entry_offset = entry_result[0]

            # Skip to actual entry data
            if entry_offset > 0 and entry_offset < len(file_bytes):
                # Extract the actual entry definition
                entry_data = file_bytes[
                    entry_offset : entry_offset + 1024
                ]  # Read enough for header

                context = f"entry {i} in node at offset {node_offset}"
                entry_def = extract_entry_with_recovery(entry_data, is_unicode, context)

                if entry_def:
                    entries.append(entry_def)
                else:
                    logger.debug(
                        "Failed to extract entry %d at offset %d",
                        i,
                        entry_offset,
                    )

            # Move to next entry reference
            current_offset += 8  # Typical entry reference size

        except Exception as e:
            logger.debug(
                "Failed to extract entry %d: %s",
                i,
                e,
            )
            # Continue with next entry
            current_offset += 8

    return entries
