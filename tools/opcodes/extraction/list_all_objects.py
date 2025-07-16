#!/usr/bin/env python3
"""List all objects in the PBD."""

from pathlib import Path

from src.extract.pbd.structures.header import extract_pbl_header
from src.extract.pbd.structures.node import extract_nods
from src.extract.pbd_io.utils import BLOCK_SIZE

pbd_path = Path("data/input/pbd_files/dcm_accounting.pbd")

with open(pbd_path, "rb") as f:
    header = extract_pbl_header(f, BLOCK_SIZE, str(pbd_path))
    nodes = extract_nods(f, header.is_unicode, header.first_nod_offset, BLOCK_SIZE)

    for node in nodes:
        if node and hasattr(node, "entry_defs"):
            for _i, entry in enumerate(node.entry_defs):
                if entry:
                    pass
