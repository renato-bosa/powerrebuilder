"""Common utilities for PowerRebuilder.

This package provides shared utility functions used across the codebase.
"""

# Import utilities from specific modules
from .strings import camel_to_snake, snake_to_camel, truncate, pluralize
from .collections import chunk_list, filter_dict, find_duplicates, merge_dicts
from .files import (
    ensure_directory,
    get_file_extension,
    normalize_path,
    read_file_safe,
    safe_cast,
    safe_json_loads,
    to_bool,
    format_timestamp,
)

__all__ = [
    # String utilities
    "camel_to_snake",
    "snake_to_camel",
    "truncate",
    "pluralize",
    # Collection utilities
    "chunk_list",
    "filter_dict",
    "find_duplicates",
    "merge_dicts",
    # File utilities
    "ensure_directory",
    "get_file_extension",
    "normalize_path",
    "read_file_safe",
    "format_timestamp",
    "safe_cast",
    "safe_json_loads",
    "to_bool",
]
