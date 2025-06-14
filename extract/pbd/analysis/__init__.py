"""PowerBuilder analysis package.

This package provides analysis tools for PowerBuilder files:
- DataWindow detection and extraction
- Symbol table analysis
- Cross-reference analysis
"""

from .cross_reference import build_cross_references
from .datawindow import (
    analyze_datawindow_content,
    detect_datawindow_blob,
    extract_datawindow_metadata,
    parse_datawindow_header,
)
from .symbol_table import build_symbol_table

__all__ = [
    "analyze_datawindow_content",
    # Cross references
    "build_cross_references",
    # Symbol table
    "build_symbol_table",
    # DataWindow analysis
    "detect_datawindow_blob",
    "extract_datawindow_metadata",
    "parse_datawindow_header",
]
