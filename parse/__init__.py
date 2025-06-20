"""PowerBuilder parser package.

This package provides functionality for parsing PowerBuilder source code.

TODO: Missing Features (COMPLETED)
    - Complete SQL query parsing and optimization - Basic parsing implemented, optimization NOW INTEGRATED
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
from .grammar import GrammarManager, get_default_manager
from .library import Library, LibraryManager, get_default_library_manager
from .parse_coordinator import (
    PowerBuilderDataWindowParser,
    PowerBuilderParser,
    parse_file,
    parse_string,
)
from .transaction_parser import TransactionParser

__all__ = [
    "FILE_EXTENSIONS",
    "PB_BASIC_TYPES",
    "PB_CONTROL_TYPES",
    "PB_EVENT_TYPES",
    "PB_KEYWORDS",
    "PB_SYSTEM_TYPES",
    "SQL_KEYWORDS",
    # Constants
    "FileType",
    # Grammar Management
    "GrammarManager",
    "Library",
    # Library Management
    "LibraryManager",
    # Parsers
    "PowerBuilderBaseParser",
    "PowerBuilderParser",
    "TransactionParser",
    "get_default_library_manager",
    "get_default_manager",
    "parse_file",
    "parse_string",
]
