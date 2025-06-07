"""PowerBuilder parser package.

This package provides functionality for parsing PowerBuilder source code.

TODO: Missing Features
    - Complete SQL query parsing and optimization - Basic support exists, needs enhancement
    - Enhanced error recovery during parsing - Missing
    - Custom type and enum handling - Missing
    - Library import resolution - Missing
"""

from __future__ import annotations

from .base_parser import PowerBuilderBaseParser
from .constants import (
    FILE_EXTENSIONS,
    PB_BASIC_TYPES,
    PB_CONTROL_TYPES,
    PB_EVENT_TYPES,
    PB_KEYWORDS,
    PB_SYSTEM_TYPES,
    SQL_KEYWORDS,
    FileType,
)
from .parse_coordinator import PowerBuilderParser, PowerBuilderDataWindowParser, parse_file, parse_string
from .transaction_parser import TransactionParser

__all__ = [
    # Parsers
    "PowerBuilderBaseParser",
    "PowerBuilderParser",
    "TransactionParser",
    "parse_file",
    "parse_string",
    # Constants
    "FileType",
    "FILE_EXTENSIONS",
    "PB_BASIC_TYPES",
    "PB_SYSTEM_TYPES",
    "PB_CONTROL_TYPES",
    "PB_EVENT_TYPES",
    "PB_KEYWORDS",
    "SQL_KEYWORDS",
]
