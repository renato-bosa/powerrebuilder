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
from .parser import PowerBuilderParser, parse_file, parse_string
from .powerbuilder import Parser
from .pseudocode_parser import PowerBuilderPseudocodeParser
from .visitors import (
    visit_function_definition,
    visit_param,
    visit_param_list,
    visit_statement_list,
    visit_type_spec,
)

__all__ = [
    # Parsers
    'PowerBuilderBaseParser',
    'PowerBuilderParser',
    'PowerBuilderPseudocodeParser',
    'Parser',
    'parse_file',
    'parse_string',
    # Visitors
    'visit_function_definition',
    'visit_param_list',
    'visit_param',
    'visit_type_spec',
    'visit_statement_list',
    # Constants
    'FileType',
    'FILE_EXTENSIONS',
    'PB_BASIC_TYPES',
    'PB_SYSTEM_TYPES',
    'PB_CONTROL_TYPES',
    'PB_EVENT_TYPES',
    'PB_KEYWORDS',
    'SQL_KEYWORDS',
]
