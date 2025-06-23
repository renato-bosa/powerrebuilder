#!/usr/bin/env python3
"""Final debug script to understand P-code extraction issue."""

import os
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))


def extract_entries_manual(pbd_path: str) -> None:








    """Extract entries from PBD using the actual extraction logic."""
    # Import here to avoid the type annotation issue
    try:
        from extract.pbd.structures.entry import (
            extract_entry_def,
            extract_entry_def_unicode,
        )
        from extract.pbd.structures.header import extract_pbl_header
        from extract.pbd.structures.node import extract_nods
        from extract.pbd_io.utils import retrieve_bytes_from_file

        # Read the file
        with open(pbd_path, "rb") as f:
            data = f.read()

        # Parse header
        header = extract_pbl_header(data)
        if not header:
            return

        # Extract NODs
        nodes = extract_nods(
            pbd_path,
            header.is_unicode,
            header.first_nod_offset,
            getattr(header, "effective_block_size", 0x200),
        )

        total_entries = 0
        source_files = []

        for _i, node in enumerate(nodes):
            if not node:
                continue

            # Extract entries from this NOD
            for j in range(node.numberofentries):
                entry_offset = node.entriesoffset[j]

                # Read entry data
                entry_data = retrieve_bytes_from_file(pbd_path, entry_offset, 200)

                # Parse entry based on Unicode flag
                if header.is_unicode:
                    entry = extract_entry_def_unicode(entry_data)
                else:
                    entry = extract_entry_def(entry_data)

                if entry:
                    total_entries += 1

                    # Check if it's a source file
                    ext = Path(entry.objectname).suffix.lower()
                    if ext in {
                        ".sru",
                        ".srw",
                        ".srd",
                        ".srm",
                        ".sra",
                        ".srq",
                        ".srs",
                        ".srf",
                        ".srj",
                    }:
                        source_files.append(entry)

                        # Check P-code detection logic
                        entry.version.lower()

        if source_files:
            for entry in source_files:
                pass

    except Exception:
        import traceback

        traceback.print_exc()


if __name__ == "__main__":
    # Try multiple PBD files
    test_pbds = [
        "input/pbd_files/pfcmain.pbd",  # PFC files often have source code
        "input/pbd_files/dcm_email.pbd",
        "tests/fixtures/pbd_files/dcm_email.pbd",
    ]

    for test_pbd in test_pbds:
        if os.path.exists(test_pbd):
            extract_entries_manual(test_pbd)
            break
    else:
        pass
