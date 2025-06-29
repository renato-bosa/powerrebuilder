import logging
from dataclasses import dataclass, field
from typing import BinaryIO

from src.common.constants import BUFFER_SIZE, HEADER_SIZE, STRING_TABLE_OFFSET
from src.extract.utils.binary import (
    binary_to_int,
    decode,
    extract_bytes_2_lst,
    retrieve_bytes_from_file,
)

from .entry import (
    PbEntryDefinition,
    get_entry_size_ascii_sig_unicode,
)
from .entry_recovery import extract_entry_with_recovery

logger = logging.getLogger(__name__)

# NOD header is 32 bytes total:
# 4 bytes: signature "NOD*"
# 4 bytes: next NOD offset
# 8 bytes: unknown fields
# 2 bytes: entry count
# 2 bytes: unknown
# 4 bytes: offset left
# 4 bytes: offset right
# 4 bytes: space left
NODE_BLOCK_SIZES_NON_UNICODE = [4, 4, 4, 4, 2, 2, 4, 4, 4]
NODE_BLOCK_SIZES_UNICODE = [
    4, 4, 4, 4, 2, 2, 4, 4, 4, ]  # NOD blocks use same structure in Unicode files


def _parse_mixed_format_entry(block: bytes, offset: int, i: int, file_context: str = None) -> tuple[PbEntryDefinition | None , int]:








    """Parse a mixed format entry (ASCII ENT* with Unicode data)."""
    context = f"entry {i} at offset {offset}"
    if file_context:
        context = f"{context} in {file_context}"

    # Use enhanced parser with recovery
    entry = extract_entry_with_recovery(block[offset:], is_unicode=False, entry_context=context)
    if not entry:
        logger.error("Failed to parse entry %s at offset %s", i, offset)
        return None, offset

    # Get the aligned entry size
    entry_size = get_entry_size_ascii_sig_unicode(block[offset:])
    if entry_size == 0:
        logger.error("Failed to calculate entry size at offset %s", offset)
        return None, offset

    return entry, offset + entry_size

def _parse_standard_format_entry(block: bytes, offset: int, i: int, is_unicode: bool, file_context: str = None) -> tuple[PbEntryDefinition | None , int]:






    """Parse a standard format entry (Unicode or ASCII)."""
    context = f"entry {i} at offset {offset}"
    if file_context:
        context = f"{context} in {file_context}"

    # Use enhanced parser with recovery
    entry = extract_entry_with_recovery(block[offset:], is_unicode=is_unicode, entry_context=context)

    if not entry:
        logger.error("Failed to parse entry %s at offset %s", i, offset)
        return None, offset

    # Estimate entry size for standard formats
    name_bytes = entry.objnamelen * (2 if is_unicode else 1)

    # Add comment length if present
    comment_bytes = entry.commentlen * (2 if is_unicode else 1)

    entry_size = (48 if is_unicode else 24) + comment_bytes + name_bytes
    # Align to 2-byte boundary
    entry_size = (entry_size + 1) & ~1

    # Validate entry size is reasonable (entries should typically be < 2KB)
    MAX_ENTRY_SIZE = 2048
    if entry_size > MAX_ENTRY_SIZE:
        logger.warning(
            f"Calculated entry size ({entry_size}) exceeds reasonable maximum ({MAX_ENTRY_SIZE}). "
            f"Entry appears corrupted: name_len={entry.objnamelen}, comment_len={entry.commentlen}",
        )
        # Return offset + fixed header size to skip this entry
        return entry, offset + (48 if is_unicode else 24)

    return entry, offset + entry_size

def _find_next_ent_signature(block: bytes, start_offset: int) -> int | None:






    """Find the next ENT* signature in the block."""
    search_offset = start_offset + 2
    while search_offset < len(block) - 4:
        if block[search_offset : search_offset + 4] == b"ENT*":
            logger.info("Found next ENT* at offset %s, resuming", search_offset)
            return search_offset
        search_offset += 2  # Search on 2-byte boundaries
    return None

def extract_entry_definitions_from_node_block(
    block: bytes, is_unicode: bool, entry_count: int, file_context: str = None,
) -> list[PbEntryDefinition]:






    """Extract all entry definitions from a node block.

    Args:
        block: The data containing entries (after NOD header)
        is_unicode: Whether the file uses Unicode encoding
        entry_count: Number of entries to extract (from NOD header)
        file_context: Optional file context for better error messages
    """
    entries = []
    offset = 0

    # Extract up to entry_count entries, but stop if we can't find valid entries
    for i in range(entry_count):
        if offset >= len(block):
            logger.warning("Reached end of block after %s entries, expected %s", i, entry_count)
            break

        # First check if we've hit a DAT* block or other non-entry data
        if len(block[offset:]) >= 4:
            sig = block[offset:offset + 4]
            if sig == b"DAT*" or sig == b"D\x00A\x00":  # ASCII or Unicode DAT
                logger.info("Found DAT* block at offset %s after %s entries, expected %s entries", offset, i, entry_count)
                break

        # Check if this is ASCII ENT* signature (could be pure ASCII or mixed with Unicode data)
        if len(block[offset:]) >= 4 and block[offset : offset + 4] == b"ENT*":
            entry, new_offset = _parse_mixed_format_entry(block, offset, i, file_context)
        elif is_unicode and len(block[offset:]) >= 8 and block[offset:offset + 8] == b"E\x00N\x00T\x00*\x00":
            # This is a pure Unicode entry
            entry, new_offset = _parse_standard_format_entry(block, offset, i, is_unicode, file_context)
        else:
            # No valid entry signature found
            if is_unicode:
                logger.warning("No valid Unicode ENT* signature at offset %s, stopping at %s entries", offset, len(entries))
            else:
                logger.warning("No valid ASCII ENT* signature at offset %s, stopping at %s entries", offset, len(entries))
            break

        if entry:
            entries.append(entry)
            offset = new_offset
            continue

        # Handle parsing failure - try to find next valid entry
        logger.warning("Failed to parse entry %s at offset %s, searching for next valid entry", i, offset)

        # Check if we're at the end of meaningful data
        if offset >= len(block) - 4:
            logger.warning("Reached end of block data at offset %s, stopping at %s entries", offset, len(entries))
            break

        # Try to find the next ENT* signature to resync
        next_offset = _find_next_ent_signature(block, offset)
        if next_offset:
            logger.info("Found next ENT* signature at offset %s, skipping %s bytes", next_offset, next_offset - offset)
            offset = next_offset
            continue
        else:
            # No more ENT* signatures found, check if we have DAT* block
            dat_offset = block[offset:].find(b"DAT*")
            if dat_offset >= 0:
                logger.info("Found DAT* block at offset %s, ending entry parsing", offset + dat_offset)
            else:
                logger.warning("No more ENT* signatures found, stopping at %s entries", len(entries))
            break

    if len(entries) != entry_count:
        logger.warning("Extracted %s entries, expected %s", len(entries), entry_count)

    return entries


NODE_FUNCTORS_NON_UNICODE = [
    lambda x: decode(x, unicode=False, is_terminated=False), # Signature
    binary_to_int, # next_nod_offset
    binary_to_int, # unknown field 1 (4 bytes)
    binary_to_int, # unknown field 2 (4 bytes)
    binary_to_int, # numberofentries (2 bytes as int)
    binary_to_int, # unknown field 3 (2 bytes)
    binary_to_int, # offsetleft
    binary_to_int, # offsetright
    binary_to_int, # spaceleft
]

NODE_FUNCTORS_UNICODE = [
    lambda x: decode(
        x, unicode=False, is_terminated=False,
    ), # Signature - still ASCII even in Unicode files
    binary_to_int, # next_nod_offset
    binary_to_int, # unknown field 1 (4 bytes)
    binary_to_int, # unknown field 2 (4 bytes)
    binary_to_int, # numberofentries (2 bytes as int)
    binary_to_int, # unknown field 3 (2 bytes)
    binary_to_int, # offsetleft
    binary_to_int, # offsetright
    binary_to_int, # spaceleft
]


@dataclass(slots=True)
class NodeClass:
    nodetype: str
    next_nod_offset: int  # Next NOD offset
    address: int  # Where this NOD was found
    numberofentries: int  # This is the count of entries in the NOD
    offsetleft: int
    offsetright: int
    spaceleft: int
    entry_defs: list[PbEntryDefinition] = field(default_factory=list)


def extract_nods(
    file_handle: BinaryIO, is_unicode: bool, first_nod_offset: int, block_size: int, # Added block_size
) -> list[NodeClass]:








    """Extract all NOD blocks starting from the first_nod_offset."""
    all_nodes: list[NodeClass] = []
    processed_offsets: set[int] = set()
    current_nod_offset = first_nod_offset

    while current_nod_offset != 0 and current_nod_offset not in processed_offsets:
        # Pass block_size to extract_nod
        node = extract_nod(
            file_handle, is_unicode, current_nod_offset, block_size, processed_offsets,
        )
        if node:
            all_nodes.append(node)
            processed_offsets.add(
                current_nod_offset,
            )  # Ensure this offset is marked here too
            current_nod_offset = (
                node.next_nod_offset
            )  # Move to the next node in the primary chain
        else:
            logger.warning(
                f"Failed to extract a valid NOD block at offset {current_nod_offset} or it was a duplicate. Stopping NOD chain processing.",
            )
            break

    if not all_nodes:
        logger.warning(
            f"No NOD blocks were extracted. Started at offset {first_nod_offset}. Unicode mode: {is_unicode}",
        )

    return all_nodes


def _read_node_header(file_handle: BinaryIO, nod_offset: int, node_header_size: int, block_size: int) -> bytes | None:








    """Read and validate NOD header data."""
    header_data = retrieve_bytes_from_file(
        file_handle, nod_offset, node_header_size, block_size_override=block_size,
    )

    if not header_data or len(header_data) < node_header_size:
        logger.error(
            f"NOD block at offset {nod_offset}: Failed to read header. Expected {node_header_size} bytes, got {len(header_data) if header_data else 0}.",
        )
        return None

    return header_data

def _validate_nod_signature(parsed_header: list, nod_offset: int, header_data: bytes) -> bool:






    """Validate NOD signature."""
    expected_sig = "NOD*"
    if not parsed_header or parsed_header[0] != expected_sig:
        logger.error(
            f"NOD block at offset {nod_offset}: Invalid signature. Expected '{expected_sig}', got '{parsed_header[0] if parsed_header else None}'.",
        )
        if header_data and len(header_data) >= 8:
            logger.error("NOD block raw bytes at offset %s: %s", nod_offset, header_data[:8].hex())
        return False
    return True

def _read_node_entries(file_handle: BinaryIO, nod_offset: int, entry_count: int, node_header_size: int, block_size: int) -> bytes | None:






    """Read the full NOD data including entries."""
    # Estimate: each entry is roughly 60-100 bytes (28 byte header + name)
    estimated_entry_size = 100
    estimated_total_size = node_header_size + (entry_count * estimated_entry_size)
    blocks_needed = (estimated_total_size + block_size - 1) // block_size
    bytes_to_read = blocks_needed * block_size

    node_data = retrieve_bytes_from_file(
        file_handle, nod_offset, bytes_to_read, block_size_override=block_size,
    )

    if not node_data or len(node_data) < node_header_size:
        logger.error("NOD block at offset %s: Failed to read full data.", nod_offset)
        return None

    return node_data

def _create_node_class(parsed_values: list, nod_offset: int) -> NodeClass | None:






    """Create NodeClass instance from parsed values."""
    try:
        if len(parsed_values) >= 10:
            return NodeClass(
                nodetype=parsed_values[0], # 'NOD*'
                next_nod_offset=parsed_values[1], address=nod_offset, numberofentries=parsed_values[4], offsetleft=parsed_values[6], offsetright=parsed_values[7], spaceleft=parsed_values[8], entry_defs=parsed_values[9] if isinstance(parsed_values[9], list) else [], )
        else:
            logger.error(
                f"Not enough parsed values for NOD at offset {nod_offset}. Got {len(parsed_values)} values, expected 10.",
            )
            return None
    except TypeError as e:
        logger.exception(
            f"Error creating NodeClass instance for NOD at offset {nod_offset}: {e}. Parsed values: {parsed_values}",
        )
        return None

def extract_nod(
    file_handle: BinaryIO, is_unicode: bool, nod_offset: int, block_size: int, processed_nod_offsets: set[int] | None = None, ) -> NodeClass | None:






    """Extract a single NOD block and its linked NOD blocks recursively."""
    if processed_nod_offsets is None:
        processed_nod_offsets = set()

    if nod_offset == 0 or nod_offset in processed_nod_offsets:
        return None

    processed_nod_offsets.add(nod_offset)

    # Determine header size and parsing functions
    node_header_size = sum(NODE_BLOCK_SIZES_UNICODE if is_unicode else NODE_BLOCK_SIZES_NON_UNICODE)
    node_block_sizes = NODE_BLOCK_SIZES_UNICODE if is_unicode else NODE_BLOCK_SIZES_NON_UNICODE
    node_functors = NODE_FUNCTORS_UNICODE if is_unicode else NODE_FUNCTORS_NON_UNICODE

    # Read and parse header
    header_data = _read_node_header(file_handle, nod_offset, node_header_size, block_size)
    if not header_data:
        return None

    parsed_header = extract_bytes_2_lst(header_data, node_block_sizes, node_functors)
    if not _validate_nod_signature(parsed_header, nod_offset, header_data):
        return None

    # Read full node data with entries
    entry_count = parsed_header[4]
    node_data = _read_node_entries(file_handle, nod_offset, entry_count, node_header_size, block_size)
    if not node_data:
        return None

    # Extract entries
    entry_data = node_data[node_header_size:]
    if entry_data:
        # Debug logging
        if entry_data[:4] == b"ENT*":
            logger.debug("Found ENT* signature at start of entry data")
        else:
            logger.debug("Entry data first 32 bytes (hex): %s", entry_data[:32].hex())

        # Get file context for better error messages
        file_context = None
        if hasattr(file_handle, "name"):
            import os
            file_context = os.path.basename(file_handle.name)

        entries = extract_entry_definitions_from_node_block(entry_data, is_unicode, entry_count, file_context)
    else:
        entries = []

    # Create NodeClass instance
    parsed_values = [*parsed_header, entries]
    return _create_node_class(parsed_values, nod_offset)
    # If implementing a more robust bi-directional scan, this might be useful.
    # For now, primarily relying on next_nod_offset chain from the initial entry point.
    # if current_node.prev_nod_offset != 0:
    #    current_node.prev_node = extract_nod(file_handle, is_unicode, current_node.prev_nod_offset, processed_nod_offsets)

    return current_node
