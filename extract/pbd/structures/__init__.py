"""PowerBuilder data structures package.

This package defines the core data structures used in PowerBuilder files:
- HeaderClass: PBD/PBL file header
- NodeClass: Node (NOD) blocks containing file entries
- PbEntryDefinition: Entry definitions within nodes
- DataClass: Data (DAT) blocks containing actual content
- PbdObject: High-level object representation
"""

from .header import HeaderClass, extract_pbl_header
from .node import NodeClass, extract_nods, extract_nod
from .entry import (
    PbEntryDefinition,
    extract_entry_def,
    extract_entry_def_unicode,
    extract_entry_def_mixed_mode,
    extract_entry_def_ascii_sig_unicode_data,
    read_and_parse_entry_def,
)
from .data_block import (
    DataClass,
    extract_data_from_entry,
    get_text_from_data,
    get_binary_from_data,
)
from .pbd_object import PbdObject

__all__ = [
    # Header
    'HeaderClass',
    'extract_pbl_header',
    # Node
    'NodeClass', 
    'extract_nods',
    'extract_nod',
    # Entry
    'PbEntryDefinition',
    'extract_entry_def',
    'extract_entry_def_unicode',
    'extract_entry_def_mixed_mode',
    'extract_entry_def_ascii_sig_unicode_data',
    'read_and_parse_entry_def',
    # Data block
    'DataClass',
    'extract_data_from_entry',
    'get_text_from_data',
    'get_binary_from_data',
    # Object
    'PbdObject',
]