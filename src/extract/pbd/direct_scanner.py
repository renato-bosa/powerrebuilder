"""Direct scanner for finding ENT* blocks in PBD files."""

import logging
import re
from typing import BinaryIO

from src.extract.pbd.entry import extract_entry_def

logger = logging.getLogger(__name__)


def scan_for_entries(file_handle: BinaryIO) -> list:
    """Scan PBD file for ENT* blocks directly.

    This bypasses the node structure and finds entry definitions directly.

    Args:
        file_handle: Open file handle

    Returns:
        List of entry definitions
    """
    file_handle.seek(0)
    data = file_handle.read()

    entries = []

    # Search for ENT* signatures
    ent_pattern = re.compile(b"ENT\\*")
    matches = list(ent_pattern.finditer(data))

    logger.info(f"Found {len(matches)} ENT* signatures")

    for match in matches:
        offset = match.start()

        # Extract enough data for the entry definition
        entry_data = data[offset : offset + 1024]

        # Parse the entry definition
        entry_def = extract_entry_def(entry_data)

        if entry_def:
            # Set the actual file offset
            entry_def.offset = offset
            entries.append(entry_def)
            logger.debug(f"Found entry: {entry_def.object_name} at offset {offset}")
        else:
            logger.debug(f"Failed to parse entry at offset {offset}")

    return entries
