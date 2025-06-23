#!/usr/bin/env python3
"""List all objects in the PBD."""

from pathlib import Path

from extract.pbd.structures.header import extract_pbl_header
from extract.pbd.structures.node import extract_nods
from extract.pbd_io.utils import BLOCK_SIZE

pbd_path = Path("input/pbd_files/dcm_accounting.pbd")

with open(pbd_path, "rb") as f:
    header = extract_pbl_header(f, BLOCK_SIZE, str(pbd_path))
    nodes = extract_nods(f, header.is_unicode, header.first_nod_offset, BLOCK_SIZE)

    for node in nodes:
        if node and hasattr(node, "entry_defs"):
            for _i, entry in enumerate(node.entry_defs):
                if entry:
                    pass
