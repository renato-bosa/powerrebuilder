import logging
from dataclasses import dataclass, field
from typing import BinaryIO

from extract.pbd_core.entry import (
    PbEntryDefinition,
    extract_entry_def,
    extract_entry_def_ascii_sig_unicode_data,
    extract_entry_def_unicode,
    get_entry_size_ascii_sig_unicode,
)
from extract.pbd_io.utils import (
    bin2int,
    decode,
    extract_bytes_2_lst,
    retrieve_bytes_from_file,
)

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
NODE_BLOCK_SIZES_UNICODE = [4, 4, 4, 4, 2, 2, 4, 4, 4]  # NOD blocks use same structure in Unicode files


def extract_entry_definitions_from_node_block(block: bytes, is_unicode: bool, entry_count: int) -> list[PbEntryDefinition]:
    """Extract all entry definitions from a node block.

    Args:
        block: The data containing entries (after NOD header)
        is_unicode: Whether the file uses Unicode encoding
        entry_count: Number of entries to extract (from NOD header)
    """
    entries = []
    offset = 0

    # Extract exactly entry_count entries
    for i in range(entry_count):
        if offset >= len(block):
            logger.warning(f"Reached end of block after {i} entries, expected {entry_count}")
            break

        # Check if this is ASCII ENT* with Unicode data format
        if len(block[offset:]) >= 4 and block[offset:offset+4] == b'ENT*':
            # This is the mixed format - ASCII signature with Unicode data
            entry = extract_entry_def_ascii_sig_unicode_data(block[offset:])
            if entry:
                entries.append(entry)
                # Get the aligned entry size
                entry_size = get_entry_size_ascii_sig_unicode(block[offset:])
                if entry_size == 0:
                    logger.error(f"Failed to calculate entry size at offset {offset}")
                    break
                offset += entry_size
            else:
                logger.error(f"Failed to parse entry {i} at offset {offset}")
                break
        else:
            # Try standard Unicode or ASCII entry format
            if is_unicode:
                entry = extract_entry_def_unicode(block[offset:])
            else:
                entry = extract_entry_def(block[offset:])

            if entry:
                entries.append(entry)
                # Estimate entry size for standard formats
                name_bytes = entry.objnamelen * (2 if is_unicode else 1)
                entry_size = (48 if is_unicode else 24) + name_bytes
                # Align to 2-byte boundary
                entry_size = (entry_size + 1) & ~1
                offset += entry_size
            else:
                logger.error(f"Failed to parse entry {i} at offset {offset}")
                break

    if len(entries) != entry_count:
        logger.warning(f"Extracted {len(entries)} entries, expected {entry_count}")

    return entries


NODE_FUNCTORS_NON_UNICODE = [
    lambda x: decode(x, unicode=False, is_terminated=False),  # Signature
    bin2int,  # next_nod_offset
    bin2int,  # unknown field 1 (4 bytes)
    bin2int,  # unknown field 2 (4 bytes)
    bin2int,  # numberofentries (2 bytes as int)
    bin2int,  # unknown field 3 (2 bytes)
    bin2int,  # offsetleft
    bin2int,  # offsetright
    bin2int,  # spaceleft
]

NODE_FUNCTORS_UNICODE = [
    lambda x: decode(x, unicode=False, is_terminated=False),  # Signature - still ASCII even in Unicode files
    bin2int,  # next_nod_offset
    bin2int,  # unknown field 1 (4 bytes)
    bin2int,  # unknown field 2 (4 bytes)
    bin2int,  # numberofentries (2 bytes as int)
    bin2int,  # unknown field 3 (2 bytes)
    bin2int,  # offsetleft
    bin2int,  # offsetright
    bin2int,  # spaceleft
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
    file_handle: BinaryIO,
    is_unicode: bool,
    first_nod_offset: int,
    block_size: int,  # Added block_size
) -> list[NodeClass]:
    """Extract all NOD blocks starting from the first_nod_offset."""
    all_nodes: list[NodeClass] = []
    processed_offsets: set[int] = set()
    current_nod_offset = first_nod_offset

    while current_nod_offset != 0 and current_nod_offset not in processed_offsets:
        # Pass block_size to extract_nod
        node = extract_nod(file_handle, is_unicode, current_nod_offset, block_size, processed_offsets)
        if node:
            all_nodes.append(node)
            processed_offsets.add(current_nod_offset)  # Ensure this offset is marked here too
            current_nod_offset = node.next_nod_offset  # Move to the next node in the primary chain
        else:
            logger.warning(f"Failed to extract a valid NOD block at offset {current_nod_offset} or it was a duplicate. Stopping NOD chain processing.")
            break

    if not all_nodes:
        logger.warning(f"No NOD blocks were extracted. Started at offset {first_nod_offset}. Unicode mode: {is_unicode}")

    return all_nodes


def extract_nod(
    file_handle: BinaryIO,
    is_unicode: bool,
    nod_offset: int,
    block_size: int,  # Added block_size
    processed_nod_offsets: set[int] | None = None,
) -> NodeClass | None:
    """Extract a single NOD block and its linked NOD blocks recursively."""
    if processed_nod_offsets is None:
        processed_nod_offsets = set()

    if nod_offset == 0 or nod_offset in processed_nod_offsets:
        return None  # End of chain or already processed

    processed_nod_offsets.add(nod_offset)

    # The entry definitions are within this structure, not in separate blocks generally.
    node_header_size = sum(NODE_BLOCK_SIZES_UNICODE if is_unicode else NODE_BLOCK_SIZES_NON_UNICODE)

    # First read just the header to get the entry count
    header_data = retrieve_bytes_from_file(file_handle, nod_offset, node_header_size, block_size_override=block_size)

    if not header_data or len(header_data) < node_header_size:
        logger.error(f"NOD block at offset {nod_offset}: Failed to read header. Expected {node_header_size} bytes, got {len(header_data) if header_data else 0}.")
        return None

    node_block_sizes = NODE_BLOCK_SIZES_UNICODE if is_unicode else NODE_BLOCK_SIZES_NON_UNICODE
    node_functors = NODE_FUNCTORS_UNICODE if is_unicode else NODE_FUNCTORS_NON_UNICODE

    # Parse header to get entry count
    parsed_header = extract_bytes_2_lst(header_data, node_block_sizes, node_functors)

    # Validate signature
    expected_sig = "NOD*"
    if not parsed_header or parsed_header[0] != expected_sig:
        logger.error(f"NOD block at offset {nod_offset}: Invalid signature. Expected '{expected_sig}', got '{parsed_header[0] if parsed_header else None}'.")
        if header_data and len(header_data) >= 8:
            logger.error(f"NOD block raw bytes at offset {nod_offset}: {header_data[:8].hex()}")
        return None

    # Now calculate how much data we need for entries
    entry_count = parsed_header[4]  # numberofentries
    # Estimate: each entry is roughly 60-100 bytes (28 byte header + name)
    estimated_entry_size = 100  # Conservative estimate
    estimated_total_size = node_header_size + (entry_count * estimated_entry_size)
    # Round up to next block size
    blocks_needed = (estimated_total_size + block_size - 1) // block_size
    bytes_to_read = blocks_needed * block_size

    # Read the full NOD data including entries
    node_data = retrieve_bytes_from_file(file_handle, nod_offset, bytes_to_read, block_size_override=block_size)

    if not node_data or len(node_data) < node_header_size:
        logger.error(f"NOD block at offset {nod_offset}: Failed to read full data.")
        return None

    # Extract entry definitions from the remaining data
    entry_data = node_data[node_header_size:]
    if entry_data:
        # Debug logging
        if entry_data[:4] == b'ENT*':
            logger.debug("Found ENT* signature at start of entry data")
        else:
            logger.debug(f"Entry data first 32 bytes (hex): {entry_data[:32].hex()}")
        entries = extract_entry_definitions_from_node_block(entry_data, is_unicode, entry_count)
    else:
        entries = []

    # Combine header fields and entries
    parsed_values = parsed_header + [entries]

    # Create NodeClass instance, handling potential parsing issues
    try:
        # parsed_values contains 10 items: 9 header fields + entry_defs
        # [0] signature, [1] next_nod_offset, [2] unknown1, [3] unknown2, [4] numberofentries,
        # [5] unknown3, [6] offsetleft, [7] offsetright, [8] spaceleft, [9] entry_defs
        if len(parsed_values) >= 10:
            current_node = NodeClass(
                nodetype=parsed_values[0],  # 'NOD*'
                next_nod_offset=parsed_values[1],
                address=nod_offset,  # Use the offset where this NOD was found
                numberofentries=parsed_values[4],
                offsetleft=parsed_values[6],
                offsetright=parsed_values[7],
                spaceleft=parsed_values[8],
                entry_defs=parsed_values[9] if isinstance(parsed_values[9], list) else [],
            )
        else:
            logger.error(f"Not enough parsed values for NOD at offset {nod_offset}. Got {len(parsed_values)} values, expected 10.")
            return None
    except TypeError as e:
        logger.error(f"Error creating NodeClass instance for NOD at offset {nod_offset}: {e}. Parsed values: {parsed_values}")
        return None

    # Recursively extract next_nod_offset and prev_nod_offset
    # These are within the current node's data structure so they are already parsed into current_node.
    # We just need to call extract_nod for them if they exist.

    # Note: We don't need to recursively extract nodes here since extract_nods()
    # already follows the chain iteratively via next_nod_offset

    # prev_nod_offset is often 0 or points to already processed nodes in a linear scan from header.
    # If implementing a more robust bi-directional scan, this might be useful.
    # For now, primarily relying on next_nod_offset chain from the initial entry point.
    # if current_node.prev_nod_offset != 0:
    #    current_node.prev_node = extract_nod(file_handle, is_unicode, current_node.prev_nod_offset, processed_nod_offsets)

    return current_node
