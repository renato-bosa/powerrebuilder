"""PowerBuilder analysis package.

This package provides analysis tools for PowerBuilder files:
- DataWindow detection and extraction
- Symbol table analysis
- Cross-reference analysis
"""

from .datawindow import (
    detect_datawindow_blob,
    analyze_datawindow_content,
    parse_datawindow_header,
    extract_datawindow_metadata,
)
from .symbol_table import build_symbol_table
from .cross_reference import build_cross_references

__all__ = [
    # DataWindow analysis
    'detect_datawindow_blob',
    'analyze_datawindow_content',
    'parse_datawindow_header',
    'extract_datawindow_metadata',
    # Symbol table
    'build_symbol_table',
    # Cross references
    'build_cross_references',
]