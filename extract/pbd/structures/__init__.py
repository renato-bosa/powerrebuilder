"""PowerBuilder data structures package.

This package defines the core data structures used in PowerBuilder files:
- HeaderClass: PBD/PBL file header
- NodeClass: Node (NOD) blocks containing file entries
- PbEntryDefinition: Entry definitions within nodes
- DataClass: Data (DAT) blocks containing actual content
- PbdObject: High-level object representation
"""

from .data_block import (
    DataClass,
    extract_data_from_entry,
    get_binary_from_data,
    get_text_from_data,
)
from .entry import (
    PbEntryDefinition,
    extract_entry_def,
    extract_entry_def_ascii_sig_unicode_data,
    extract_entry_def_mixed_mode,
    extract_entry_def_unicode,
    read_and_parse_entry_def,
)
from .header import HeaderClass, extract_pbl_header
from .node import NodeClass, extract_nod, extract_nods
from .pbd_object import PbdObject

__all__ = [
    # Data block
    "DataClass",
    # Header
    "HeaderClass",
    # Node
    "NodeClass",
    # Entry
    "PbEntryDefinition",
    # Object
    "PbdObject",
    "extract_data_from_entry",
    "extract_entry_def",
    "extract_entry_def_ascii_sig_unicode_data",
    "extract_entry_def_mixed_mode",
    "extract_entry_def_unicode",
    "extract_nod",
    "extract_nods",
    "extract_pbl_header",
    "get_binary_from_data",
    "get_text_from_data",
    "read_and_parse_entry_def",
]
